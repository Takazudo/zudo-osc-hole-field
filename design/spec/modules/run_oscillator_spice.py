"""Generate/run bounded ideal-reference and generic-BJT waveform models.

AS3340 core, sync, tracking and rail sequencing have no retained vendor model.
"""
import json, re, subprocess
from pathlib import Path
from .oscillator import ROOT, family, octave_family
DIR=ROOT/'design/spec/modules/spice'
REPORT=ROOT/'design/reports/spice/oscillator.json'
MAPS={1:('1','2','3'),2:('7','6','5'),3:('8','9','10'),4:('14','13','12')}

def net(v):return '0' if v=='AGND' else re.sub('[^A-Za-z0-9_]','_',v.replace('+','P_').replace('-','N_'))
def name(v):return re.sub('[^A-Za-z0-9_]','_',v)
def number(s):
    x=re.match(r'([\d.eE+-]+)\s*([kMmunpµ]?)',s)
    return float(x[1])*{'':1,'k':1e3,'M':1e6,'m':1e-3,'u':1e-6,'µ':1e-6,'n':1e-9,'p':1e-12}[x[2]]

def primitives(parts):
    rows=[]
    for p in parts:
        if p.prefix in ('R','RB','C'):
            rows.append(f'{p.prefix[0]}{name(p.key)} {net(p.pins["1"])} {net(p.pins["2"])} {number(p.value):g}')
        elif p.symbol.endswith(('OPA4196IDR','OPA4197IPWR')) and p.unit in MAPS:
            out,minus,plus=MAPS[p.unit]
            rows.append(f'E{name(p.key)} {net(p.pins[out])} 0 {net(p.pins[plus])} {net(p.pins[minus])} 1e6')
    return rows


def decks():
    ref=octave_family();parts=list(ref.parts)
    raw=next(p for p in parts if p.symbol.endswith('REF5050AIDR')).pins['6']
    lines=['Shared octave reference: ideal opamps/reference; no real precision claim',f'Vref {net(raw)} 0 5','Vp P_12V 0 12','Vn N_12V 0 -12']+primitives(parts)
    trim=next(p for p in parts if p.prefix=='RV')
    lines += [f'Rspan {net(trim.pins["1"])} {net(trim.pins["2"])} 900','.control','op','print '+' '.join('v(osc_oct'+str(i)+')' for i in range(6)),'quit','.endc','.end']
    out={'oscillator-reference-ideal.cir':'\n'.join(lines)+'\n'}
    f=family();sp=[p for p in f.parts if p.key.startswith('R_SINE_') or p.attributes.get('LogicalCellKey','').startswith(('SINE_DIFF.','SINE_GAIN.'))]
    lines=['Sine shaper: generic matched BJT pair, ideal amplifiers; no AS3340 model','Vp P_12V 0 12','Vn N_12V 0 -12','Vtri TRI_SCALED 0 PWL('+' '.join(f'{i*.0005:g} {(-5 if i%2==0 else 5)}' for i in range(21))+')','Voffset SINE_OFFSET 0 1.5']
    generated=primitives(sp)
    lines+=generated+['Q1 SINE_C1 SINE_BASE SINE_TAIL GENERIC_PAIR','Q2 SINE_C2 0 SINE_TAIL GENERIC_PAIR','.model GENERIC_PAIR NPN(IS=1e-14 BF=300 VAF=100)','Rlevel SINE_GAIN_TRIM SINE_GAIN_SUM 5500','.tran 2u 10m','.measure tran sine_max MAX v(SIN_SCALED) FROM=5m TO=10m','.measure tran sine_min MIN v(SIN_SCALED) FROM=5m TO=10m','.measure tran sine_mean AVG v(SIN_SCALED) FROM=5m TO=10m','.four 1k v(SIN_SCALED)','.end']
    out['oscillator-sine-generic.cir']='\n'.join(lines)+'\n'
    sp=[p for p in f.parts if p.key.startswith(('R_TRI_','R_SAW_')) or p.attributes.get('LogicalCellKey','').startswith(('TRI_SCALE.','SAW_SCALE.'))]
    lines=['Raw-output scaling: ideal 12 V core amplitudes assumed','Vref OSC_REF5 0 5','Vtri TRI_RAW 0 PWL('+' '.join(f'{i*.0005:g} {(0 if i%2==0 else 4)}' for i in range(7))+')','Vsaw SAW_RAW 0 PWL(0 0 .000999 8 .001 0 .001999 8 .002 0 .002999 8 .003 0)']+primitives(sp)+['.tran 1u 3m','.measure tran tri_max MAX v(TRI_SCALED) FROM=1m TO=3m','.measure tran tri_min MIN v(TRI_SCALED) FROM=1m TO=3m','.measure tran saw_max MAX v(SAW_SCALED) FROM=1m TO=3m','.measure tran saw_min MIN v(SAW_SCALED) FROM=1m TO=3m','.end']
    out['oscillator-levels-ideal.cir']='\n'.join(lines)+'\n'
    return out


def main():
    DIR.mkdir(exist_ok=True);results=[]
    for file,body in decks().items():
        p=DIR/file;p.write_text(body)
        run=subprocess.run(['bash','scripts/kicad/run.sh','ngspice','-b',str(p.relative_to(ROOT))],cwd=ROOT,text=True,capture_output=True)
        text=run.stdout+'\n'+run.stderr
        if run.returncode:raise RuntimeError(text)
        measures={k:float(v) for k,v in re.findall(r'^([a-z_]+)\s*=\s*([-+\d.eE]+)',text,re.M)}
        if 'reference' in file:
            measures={k:float(v) for k,v in re.findall(r'v\((osc_oct\d)\)\s*=\s*([-+\d.eE]+)',text,re.I)}
            assert len(measures)==6,text
            assert all(abs(measures['osc_oct'+str(i)]-(i-2))<.002 for i in range(6)),measures
        elif 'sine' in file:
            assert 4<measures['sine_max']<6 and -6<measures['sine_min']<-4,measures
            assert abs(measures['sine_mean'])<.1,measures
            thd=re.search(r'THD:\s*([\d.eE+-]+)\s*%',text)
            assert thd,text
            measures['generic_model_thd_percent']=float(thd[1])
            assert measures['generic_model_thd_percent']<5,measures
        else:
            assert all(abs(measures[k]-v)<.02 for k,v in [('tri_max',5),('tri_min',-5),('saw_max',5),('saw_min',-5)]),measures
        results.append({'deck':str(p.relative_to(ROOT)),'status':'PASS - model only','measures':measures,'model_limit':'Ideal op-amps/reference; generic matched BJT pair if present. Not a manufacturer oscillator model or hardware result.'})
        print(file,measures)
    report={'schema_version':1,'oracle':'scripts/kicad/run.sh ngspice -b, pinned KiCad 10.0.6 image','status':'Model-limited checks only','model_calibration':{'generic_pair_temperature_C':27,'sine_symmetry_wiper_V':1.5,'sine_level_rheostat_ohm':5500,'octave_span_rheostat_ohm':900,'meaning':'Chosen model settings, not measured factory trim positions'},'runs':results,'not_run':[{'subject':'AS3340 exponential core, tracking, sync, PWM transients, startup and temperature','status':'NOT RUN','reason':'No retained vendor macro-model; ALFA data sheet gives reference topology and typical conditions, not a SPICE model.'},{'subject':'Cable stability, protection and buffered -5 V supply sequencing','status':'NOT RUN','reason':'Ideal amplifier models here do not establish device stability, rail behavior or fault survival.'}]}
    REPORT.parent.mkdir(parents=True,exist_ok=True);REPORT.write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
