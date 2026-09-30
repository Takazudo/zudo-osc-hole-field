"""Wavefolder DC/transient fixtures: retained OTA plus generic devices/ideal amps.

The source signal path/control servo is translated from physical pin maps.
No actual amplifier bandwidth, diode spread, harness or fault qualification.
"""
import hashlib,json,math,re,subprocess
from pathlib import Path
from design.spec.modules.wavefolder import ROOT,family
from design.spec.modules.run_oscillator_spice import net,name,number,MAPS
DIR=ROOT/'design/spec/modules/spice';CACHE=ROOT/'.circuit-cache/wavefolder-spice'
OUT=ROOT/'design/reports/spice/wavefolder.json'
MODEL=ROOT/'design/spec/modules/spice/filter-model/LM13700.MOD'


def common(fold=5,bias=0,*,depth=0,bias_cv=0,offset=-.3,mismatch=False,sine=False):
 f=family();lines=['* Spec-derived signal path and bias servo; ideal limited amplifiers.', '.include "design/spec/modules/spice/filter-model/LM13700.MOD"','VP P_12V 0 12','VN N_12V 0 -12','VREF5 REF5 0 5','VREFN5 REFN5 0 -5',f'VIN IN_BUFFER 0 '+('SIN(0 5 100)' if sine else '0'),f'VMANUAL FOLD_MANUAL 0 {fold}',f'VDEPTH FOLD_DEPTH 0 {depth}',f'VBIAS BIAS_MANUAL 0 {bias}',f'VBIASCV BIAS_BUFFER 0 {bias_cv}',f'VOFFSET OFFSET_TRIM 0 {offset}']
 selected=[]
 for p in f.parts:
  role=p.attributes.get('Role','');key=p.attributes.get('LogicalCellKey',p.key)
  own=role.startswith('wavefolder:') and '_DEC_' not in p.key
  level=('remote_buffer:' in role or 'level_attenuator:' in role) and '_LEVEL__' in key
  if own or level or role.startswith('general_output:'):selected.append(p)
 for p in selected:
  role=p.attributes.get('Role','')
  if p.prefix in ('R','RB','C'):
   lines.append(f'{p.prefix[0]}{name(p.key)} {net(p.pins["1"])} {net(p.pins["2"])} {number(p.value):g}')
  elif p.symbol.endswith(('OPA4196IDR','OPA4197IPWR')) and p.unit in MAPS:
   out,minus,plus=MAPS[p.unit]
   if role=='wavefolder:CURRENT_SERVO':lines.append(f'B{name(p.key)} {net(p.pins[out])} 0 V=10.5*tanh(1e5*(v({net(p.pins[plus])})-v({net(p.pins[minus])}))/10.5)')
   else:lines.append(f'E{name(p.key)} {net(p.pins[out])} 0 {net(p.pins[plus])} {net(p.pins[minus])} 1e6')
  elif role.startswith('wavefolder:F') and '_D_' in role:
   model='FOLD_POS' if '_D_POS' in role else 'FOLD_NEG'
   lines.append(f'D{name(p.key)} {net(p.pins["2"])} {net(p.pins["1"])} {model}')
  elif role=='wavefolder:BIAS_REVERSE_BE':lines.append(f'DREVERSE {net(p.pins["2"])} {net(p.pins["1"])} FOLD_NEG')
  elif role=='wavefolder:CONTROL_CLAMP':lines+=['DCLOW 0 CONTROL_CLAMP SCHOTTKY','DCHIGH CONTROL_CLAMP REF5 SCHOTTKY']
  elif role=='wavefolder:BIAS_PNP':lines.append('QBIAS CURRENT_SOURCE BASE EMITTER GENERIC_PNP')
  elif role=='wavefolder:PRE_GAIN_MAX':lines.append('RGAIN_TRIM PRE_GAIN_TRIM PRE_GAIN_SUM 5k')
  elif role=='level_attenuator:RV':
   lines+=['RLEVEL_TOP '+net(p.pins['3'])+' '+net(p.pins['2'])+' 1u','RLEVEL_BOTTOM '+net(p.pins['2'])+' '+net(p.pins['1'])+' 10k']
 pins={}
 for p in f.parts:
  if p.symbol.endswith('LM13700M_NOPB'):pins.update(p.pins)
 for i,numbers in enumerate([('1','2','3','4','5','6','7','8','11'),('16','15','14','13','12','6','10','9','11')]):
  nodes=[net(pins[n]) if pins[n] is not None else f'NC_{i}_{n}' for n in numbers]
  lines.append(f'XOTA{i} '+' '.join(nodes)+' LM13700/NS')
 lines+=['.model GENERIC_PNP PNP(IS=1e-14 BF=200 VAF=100)',f'.model FOLD_POS D(IS={2e-9 if mismatch else 1e-9} N=1.8 RS=1 CJO=2p TT=4n)','.model FOLD_NEG D(IS=1n N=1.8 RS=1 CJO=2p TT=4n)','.model SCHOTTKY D(IS=1u N=1.1 RS=1 CJO=10p)','RLOAD OUT_TIP 0 100k','.options reltol=1e-5 abstol=1e-11']
 return '\n'.join(lines)+'\n'


def invoke(stem,body,analysis):
 deck=DIR/(stem+'.cir');data=CACHE/(stem+'.txt')
 data.unlink(missing_ok=True)  # A failed oracle must never reuse an old trace.
 deck.write_text('Unvalidated wavefolder model: '+stem+'\n'+body+'.control\nset wr_singlescale\nset wr_vecnames\n'+analysis+f'\nwrdata {data.relative_to(ROOT)} v(PRE_AC) v(PRE_GAIN) v(FOLDER_DRIVE) v(COMMAND) v(OUT_TIP) v(F1_OUT) v(F2_OUT) v(F3_OUT) v(F4_OUT) v(CONTROL_NEG) v(CONTROL_RAW) v(BASE_DRIVE)\nquit\n.endc\n.end\n')
 r=subprocess.run(['bash','scripts/kicad/run.sh','ngspice','-b',str(deck.relative_to(ROOT))],cwd=ROOT,text=True,capture_output=True)
 (CACHE/(stem+'.log')).write_text(r.stdout+'\n'+r.stderr)
 if r.returncode or not data.exists() or 'simulation(s) aborted' in r.stderr:raise RuntimeError(r.stdout+'\n'+r.stderr)
 rows=[[float(x) for x in line.split()] for line in data.read_text().splitlines()[1:]]
 assert rows and all(math.isfinite(x) for row in rows for x in row),stem
 return rows,deck


def extrema(rows):
 slopes=[(b[1]-a[1])/(b[0]-a[0]) for a,b in zip(rows,rows[1:])]
 turns=[]
 for i in range(1,len(slopes)):
  if slopes[i]*slopes[i-1]<0:turns.append({'input_V':rows[i][0],'pre_AC_V':rows[i][1]})
 return turns


def run_dc(stem,fold,bias,offset,**kw):
 rows,deck=invoke(stem,common(fold,bias,offset=offset,**kw),'dc VIN -5 5 .01')
 assert max(abs(r[1]) for r in rows)<9,(stem,max(abs(r[1]) for r in rows))
 assert max(abs(r[5]) for r in rows)<.001,(stem,'DC coupling path should block static output')
 centre=min(rows,key=lambda r:abs(r[0]))
 headroom=max(abs(v) for r in rows for v in [r[2],r[3],*r[6:]])
 assert headroom<=10.5001,(stem,headroom)
 result={'deck':str(deck.relative_to(ROOT)),'status':'PASS - model only','fold_manual_V':fold,'bias_manual_V':bias,'fold_depth_V':kw.get('depth',0),'bias_CV_V':kw.get('bias_cv',0),'diode_mismatch':kw.get('mismatch',False),'pre_AC_min_V':min(r[1] for r in rows),'pre_AC_max_V':max(r[1] for r in rows),'pre_AC_at_zero_input_V':centre[1],'maximum_static_jack_DC_V':max(abs(r[5]) for r in rows),'command_V':centre[4],'maximum_monitored_internal_voltage_V':headroom,'odd_symmetry_error_V':max(abs(a[1]+b[1]) for a,b in zip(rows,reversed(rows))),'turning_points':extrema(rows)}
 print(stem,result['pre_AC_min_V'],result['pre_AC_max_V'],'turns',len(result['turning_points']))
 return result


def main():
 CACHE.mkdir(parents=True,exist_ok=True)
 calibration,_=invoke('wavefolder-offset-calibration',common(5,0,offset=0),'dc VOFFSET -.8 .8 .002')
 offset=min(calibration,key=lambda r:abs(r[2]))[0]
 print('Model-only offset wiper',offset)
 runs=[run_dc(f'wavefolder-dc-f{str(f).replace(".","p")}-b{str(b).replace("-","n")}',f,b,offset) for b in (-5,0,5) for f in (.25,1.5,3,5)]
 for bias in (-5,5):runs.append(run_dc('wavefolder-control-limit-'+str(bias).replace('-','n'),5,bias,offset,depth=5,bias_cv=bias))
 runs.append(run_dc('wavefolder-fold-mute',0,0,offset,depth=-5))
 assert max(abs(runs[-1][k]) for k in ('pre_AC_min_V','pre_AC_max_V'))<.05,runs[-1]
 runs.append(run_dc('wavefolder-diode-mismatch',5,0,offset,mismatch=True))
 standard=next(r for r in runs if r['fold_manual_V']==5 and r['bias_manual_V']==0 and not r['diode_mismatch'])
 assert len(standard['turning_points'])>=8,standard
 rows,deck=invoke('wavefolder-sine-transient',common(5,2.5,offset=offset,sine=True),'tran 5u 800m')
 window=[r for r in rows if r[0]>=.7];out=[r[5] for r in window]
 # Time-weighted DC mean; ngspice adaptive steps must not bias the average.
 mean=sum((b[0]-a[0])*(a[5]+b[5])/2 for a,b in zip(window,window[1:]))/(window[-1][0]-window[0][0])
 assert abs(mean)<.05,mean
 assert max(out)-min(out)>2 and max(abs(v) for v in out)<8,(min(out),max(out))
 report={'schema_version':1,'module':'wavefolder','authority':'PROPOSAL (planning, owner-delegated)','status':'PASS - bounded model only','oracle':'KiCad10.0.6 pinned wrapper ngspice','model_offset_calibration_V':offset,'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [ROOT/'design/spec/modules/wavefolder.py',ROOT/'design/spec/modules/io_partition.py',Path(__file__).resolve(),MODEL]},'dc_runs':runs,'transient':{'deck':str(deck.relative_to(ROOT)),'status':'PASS - model only','input':'5V peak,100Hz sine; FOLD manual5V,BIAS manual2.5V,full LEVEL,100k load','window_s':[.7,.8],'min_V':min(out),'max_V':max(out),'time_weighted_mean_V':mean},'limitations':['TI retained single-OTA macromodel; its header warns AC bandwidth/phase margin can be overestimated by more than2x.','Ideal amplifiers have no bandwidth/current/slew/phase model; only the bias-servo amplifier has a smooth +/-10.5V output bound. Normal-case internal headroom is checked separately; overload is not qualified.','Diode, Schottky and PNP parameters are generic fixtures, not vendor BAS16/BAT54/MMBT3906 models.','Control servo is connected from source parts but its real compensation/stability/offset/corner operation is unqualified.','DC curves refer to PRE_AC; steady jack DC is blocked by the1uF/100k highpass.','Protection, harness/cable stability, noise, temperature, actual current bounds and hardware behavior NOT RUN.']}
 OUT.write_text(json.dumps(report,indent=2)+'\n')
 print('Transient',report['transient'])
if __name__=='__main__':main()
