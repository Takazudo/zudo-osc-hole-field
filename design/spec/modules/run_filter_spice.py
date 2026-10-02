"""Manufacturer OTA macromodel response checks; ideal op-amps and bias sources.

The vendor model warns of over-optimistic bandwidth/phase margin. Bias-current
sources replace the unqualified exponential converter and command servos here.
"""
import json,math,re,subprocess
from pathlib import Path
from design.spec.modules.filter import ROOT,family
from design.spec.modules.run_oscillator_spice import primitives,net,name
from design.spec.modules.spice_trace import check_oracle_result
DIR=ROOT/'design/spec/modules/spice'
SCRATCH=ROOT/'.circuit-cache/filter-spice'
OUT=ROOT/'design/reports/spice/filter.json'
ATTEN=200/100200
CAP=150e-12
RF_RES=573000


def common():
    f=family();selected=[]
    amps={'HP_SUM','BP_BUFFER','LP_BUFFER','RESONANCE_TIA','DRY_TIA'}
    for p in f.parts:
        role=p.attributes.get('Role','')
        passive=role.startswith('filter:R_HP_') or role.startswith('filter:C_BP_INTEGRATOR') or role.startswith('filter:C_LP_INTEGRATOR')
        passive |= any(role.startswith('filter:R_'+k+s) for k in ('BP','LP','RES','DRY') for s in ('_ATTEN_','_OFFSET_'))
        passive |= role in ('filter:R_RESONANCE_FIXED','filter:R_RESONANCE_LIMIT_R','filter:R_DRY_GAIN')
        if passive or role.removeprefix('filter:') in amps or role.startswith('general_output:'):selected.append(p)
    lines=['* Derived from filter.py; OTA bias and offset settings are model test fixtures.', '.include "design/spec/modules/spice/filter-model/LM13700.MOD"','VP P_12V 0 12','VN N_12V 0 -12','VIN IN_BUFFER 0 DC 0 AC 1']+primitives(selected)
    lines+=['RRES_TRIM RESONANCE_TRIM RES_INT 243k']
    for k in ('BP','LP','RES','DRY'):
        offset=-.3 if k=='DRY' else .3
        lines.append(f'VOFF_{k} {k}_OFFSET_TRIM 0 {offset}')
    pins={}
    for p in f.parts:
        if p.symbol.endswith('LM13700M_NOPB'):
            pins.setdefault(p.key.rsplit('.',1)[0],{}).update(p.pins)
    n=0
    for group,pinmap in pins.items():
        for pin_numbers in [('1','2','3','4','5','6','7','8','11'),('16','15','14','13','12','6','10','9','11')]:
            n+=1;nodes=[net(pinmap[p]) if pinmap[p] is not None else f'NC_{n}_{p}' for p in pin_numbers]
            lines.append(f'XOTA{n} '+ ' '.join(nodes)+' LM13700/NS')
    for k in ('BP','LP'):lines.append(f'I{k} P_12V {k}_IABC {{ibfreq}}')
    lines+=['IRES P_12V RES_IABC {ibres}','IDRY P_12V DRY_IABC {ibdry}']
    for p in f.parts:
        if p.attributes.get('Role','').startswith('filter:RES_LIMIT_'):
            lines.append(f'D{name(p.key)} {net(p.pins["2"])} {net(p.pins["1"])} LIMIT_DIODE')
    lines+=['.model LIMIT_DIODE D(IS=1n N=1.8 RS=1)']
    for k in ('LP','BP','HP','OUT'):lines.append(f'RLOAD_{k} {k}_TIP 0 100k')
    return '\n'.join(lines)+'\n'


def main():
    SCRATCH.mkdir(parents=True,exist_ok=True)
    (DIR/'filter-core-vendor.inc').write_text(common())
    results=[]
    cases=[(fc,g,1) for fc in (100,1000,10000) for g in (0,1.7)]+[(1000,g,0) for g in (0,1.7)]
    for fc,g,gain in cases:
        stem=f'filter-{fc}-{("low" if g==0 else "high")}-gain{gain}'
        ibfreq=2*math.pi*fc*CAP/(19.2*ATTEN);ibres=g/(19.2*ATTEN*RF_RES);ibdry=gain*5/12400
        data=f'.circuit-cache/filter-spice/{stem}.txt'
        (ROOT/data).unlink(missing_ok=True)  # Do not consume a previous AC trace.
        lines=[f'Filter response: vendor OTA, ideal opamps; fc command {fc}, damping feedback {g}',f'.param ibfreq={ibfreq:.12g} ibres={ibres:.12g} ibdry={ibdry:.12g}','.include "design/spec/modules/spice/filter-core-vendor.inc"','.control','set wr_singlescale','set wr_vecnames','op','print v(BP_INT) v(LP_INT) v(HP_CORE)','ac dec 100 2 200k',f'wrdata {data} db(v(LP_TIP)) db(v(BP_TIP)) db(v(HP_TIP)) db(v(OUT_TIP))','quit','.endc','.end']
        deck=DIR/(stem+'.cir');deck.write_text('\n'.join(lines)+'\n')
        run=subprocess.run(['bash','scripts/kicad/run.sh','ngspice','-b',str(deck.relative_to(ROOT))],cwd=ROOT,text=True,capture_output=True)
        text=run.stdout+'\n'+run.stderr
        check_oracle_result(run,ROOT/data)
        table=[]
        for line in (ROOT/data).read_text().splitlines()[1:]:
            row=[float(x) for x in line.split()];assert len(row)==5,row;table.append(row)
        at=min(table,key=lambda r:abs(math.log(r[0]/fc)));peak=max(table,key=lambda r:r[2])
        low=min(table,key=lambda r:abs(math.log(r[0]/(fc/10))))
        high=min(table,key=lambda r:abs(math.log(r[0]/(fc*10))))
        assert abs(peak[0]/fc-1)<.35,(stem,peak)
        assert low[1]>high[1]+25,(stem,low,high)
        assert high[3]>low[3]+25,(stem,low,high)
        assert all(math.isfinite(x) for row in table for x in row),(stem,table[:5])
        results.append({'deck':str(deck.relative_to(ROOT)),'status':'PASS - model only','cutoff_command_Hz':fc,'resonance_feedback_g':g,'dry_gain_command':gain,'bias_currents_A':{'integrator_each':ibfreq,'resonance':ibres,'dry':ibdry},'near_command_frequency_Hz':at[0],'gain_dB_at_command':dict(zip(('LP','BP','HP','OUT'),at[1:])),'BP_peak_Hz':peak[0],'BP_peak_dB':peak[2],'model_boundary':'Vendor single-OTA macromodel, ideal op-amps, externally imposed bias currents, generic clamp diodes and chosen offset trim voltages.'})
        print(stem,'BP peak',peak[0],peak[2],'gains',at[1:])
    for g in (0,1.7):
        rows=[r for r in results if r['cutoff_command_Hz']==1000 and r['resonance_feedback_g']==g]
        a,b=rows
        for out in ('LP','BP','HP'):assert abs(a['gain_dB_at_command'][out]-b['gain_dB_at_command'][out])<.01,(g,out,a,b)
        assert abs(a['gain_dB_at_command']['OUT'])<.5,a
        assert a['gain_dB_at_command']['OUT']>b['gain_dB_at_command']['OUT']+20,(a,b)
    # A bounded transient at maximum resonance checks this model's limiter,
    # not hardware amplitude or the vendor model's optimistic stability margin.
    bias=2*math.pi*1000*CAP/(19.2*ATTEN)
    transient=common().replace('VIN IN_BUFFER 0 DC 0 AC 1','VIN IN_BUFFER 0 PWL(0 0 1m 0 1.001m .01 1.01m 0 50m 0)')
    deck=DIR/'filter-self-oscillation-vendor.cir'
    deck.write_text('Model-only self-oscillation with generic limiter diodes\n'+f'.param ibfreq={bias:.12g} ibres={5/49900:.12g} ibdry=0\n'+transient+'.tran 1u 50m\n.measure tran bp_max MAX v(BP_CORE) FROM=30m TO=50m\n.measure tran bp_min MIN v(BP_CORE) FROM=30m TO=50m\n.measure tran lp_max MAX v(LP_CORE) FROM=30m TO=50m\n.measure tran lp_min MIN v(LP_CORE) FROM=30m TO=50m\n.end\n')
    run=subprocess.run(['bash','scripts/kicad/run.sh','ngspice','-b',str(deck.relative_to(ROOT))],cwd=ROOT,text=True,capture_output=True)
    text=run.stdout+'\n'+run.stderr
    check_oracle_result(run)
    measures={k:float(v) for k,v in re.findall(r'^((?:bp|lp)_(?:max|min))\s*=\s*([-+\d.eE]+)',text,re.M)}
    assert len(measures)==4,text
    assert .5<measures['bp_max']-measures['bp_min']<12,measures
    assert all(abs(v)<10 for v in measures.values()),measures
    results.append({'deck':str(deck.relative_to(ROOT)),'status':'PASS - model only','test':'Self-oscillation after small input kick, 30..50ms observation window','measures_V':measures,'limitations':'Ideal amplifiers, imposed bias currents and generic diode model; no hardware amplitude/stability claim.'})
    print('Self-oscillation model:',measures)
    report={'schema_version':1,'module':'filter','authority':'PROPOSAL (planning, owner-delegated)','oracle':'pinned KiCad 10.0.6 ngspice through scripts/kicad/run.sh','status':'PASS - bounded vendor-macromodel small-signal response; not hardware','runs':results,'G06_model_result':'Changing ideal dry bias current leaves LP/BP/HP response unchanged within 0.01 dB; OUT changes by >20 dB.','limitations':['Vendor explicitly warns bandwidth and phase-margin optimism greater than twofold.','Real exponential converter, PNP current servos, amplifier dynamics, tolerance/temperature, rail startup and power-off protection are NOT RUN by these AC decks.','Offset trimmer fixtures are +0.3 V for BP/LP/RES and -0.3 V for DRY; they are not hardware calibration values.','The single transient fixture only establishes bounded oscillation in this model; hardware amplitude, overload and recovery remain unverified.']}
    OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(json.dumps(report,indent=2)+'\n')
if __name__=='__main__':main()
