"""Pinned OPAx197 nominal macro-model with bounded fanout/passive corners."""
import json, subprocess,sys,itertools
from .oscillator import ROOT
from .check_oscillator_reference import build
from design.spec.cells.sweep_precision_vendor import model, deck, measure, LIB_SHA256
OUT=ROOT/'design/reports/spice/oscillator-reference-vendor.json'


def refresh_load_bound(out,report):
    """Refresh arithmetic metadata only; retain unchanged nominal model runs.

    The SPICE decks use fixed 3k/open loads, rails and passive corners, not the
    input-bias scalar. Prove that the new conditional fanout still lies inside
    that retained load envelope, without claiming a full-temperature run.
    """
    assert out['model_library_sha256']==LIB_SHA256
    expected=set(itertools.product((11.4,12.6),(-1,0,1),(0.,1e-9),(3000.,1e12)))
    actual={(r['rail_abs_V'],r['R_tolerance_percent'],r['load_cap_F'],r['load_ohm']) for r in out['runs']}
    assert len(out['runs'])==24 and actual==expected,'retained model corner coverage differs'
    for r in out['runs']:
        assert r['C_tolerance_percent']==5*r['R_tolerance_percent']
        assert r['settling_error_mV_at_400us']<=1 and r['late_ripple_mV']<=1 and r['overshoot_percent_of_step']<=10
    c=report['conditions']
    assert (c['supply_abs_min_V'],c['supply_abs_max_V'],c['reference_abs_max_V'])==(11.4,12.6,5.025)
    assert (out['nominal_feedback_ohm'],out['nominal_isolation_ohm'],out['nominal_compensation_F'])==(c['feedback_ohm'],c['isolation_ohm'],c['compensation_F'])
    maximum=max(x['maximum_mA'] for x in report['local_outputs_per_oscillator'])
    assert maximum<=out['load_current_at_5_025V_mA']==5.025/3000*1000,'updated fanout exceeds retained SPICE load'
    out['computed_max_branch_mA']=maximum
    out['source_load_bound']={'input_bias_bound_A':c['input_bias_bound_A'],
        'scope':'Conditional full-temperature load arithmetic; retained nominal TI model remains at 27 C. No full-temperature semiconductor performance was simulated.',
        'source':'design/spec/modules/oscillator-reference.json',
        'model_deck_inputs_changed_by_bias_correction':False}
    return out


def main():
    model();report=build();rows=[]
    init=ROOT/'.spiceinit';assert not init.exists();init.write_text('set ngbehavior=ps\n')
    path=ROOT/'.circuit-cache/sources/opa197-model/oscillator-fanout.cir'
    try:
        for rail in (11.4,12.6):
            for tolerance in (-1,0,1):
                for cap,load in ((cap,load) for cap in (None,'1n') for load in ('3000','1e12')):
                    body=deck(load,cap).replace('12\n',f'{rail}\n').replace('-12\n',f'-{rail}\n')
                    body=body.replace('Risoa drive mid 499',f'Risoa drive mid {50*(1+tolerance*.01)}').replace('Risob mid jack 499',f'Risob mid jack {50*(1+tolerance*.01)}')
                    body=body.replace('Rfb jack fb 100',f'Rfb jack fb {100*(1+tolerance*.01)}').replace('Cfast drive fb 1e-09',f'Cfast drive fb {1e-9*(1+tolerance*.05)}')
                    body=body.replace('PULSE(-5 5 ', 'PULSE(-5.025 5.025 ')
                    path.write_text(body)
                    p=subprocess.run(['bash','scripts/kicad/run.sh','ngspice','-b',str(path.relative_to(ROOT))],cwd=ROOT,capture_output=True,text=True,timeout=120)
                    assert p.returncode==0,p.stderr
                    m=measure(p.stdout+p.stderr)
                    error=max(abs(m[k]-v) for k,v in [('pset',5.025),('nset',-5.025),('p2set',5.025),('n2set',-5.025)])*1000
                    ripple=max(m[a]-m[b] for a,b in [('platmax','platmin'),('nlatmax','nlatmin'),('p2latmax','p2latmin'),('n2latmax','n2latmin')])*1000
                    overshoot=max(0,max(m['pmax'],m['p2max'],-m['nmin'],-m['n2min'])-5.025)/10.05*100
                    assert error<=1 and ripple<=1 and overshoot<=10,(m,error,ripple,overshoot)
                    rows.append({'rail_abs_V':rail,'R_tolerance_percent':tolerance,'C_tolerance_percent':5*tolerance,'load_ohm':float(load),'load_cap_F':1e-9 if cap else 0,'settling_error_mV_at_400us':error,'late_ripple_mV':ripple,'overshoot_percent_of_step':overshoot,'status':'PASS - model only'})
    finally:init.unlink()
    out={'schema_version':1,'status':'PASS - 24 macro-model cases; physical performance NOT RUN','model_library_sha256':LIB_SHA256,'oracle':'pinned KiCad 10.0.6 / ngspice via scripts/kicad/run.sh','nominal_feedback_ohm':100,'nominal_isolation_ohm':100,'nominal_compensation_F':1e-9,'load_current_at_5_025V_mA':1.675,'computed_max_branch_mA':max(x['maximum_mA'] for x in report['local_outputs_per_oscillator']),'runs':rows,'limits':'Nominal TI family model at 27 C. Passive/rail corners and load cover the declared powered envelope; temperature, semiconductor process, real harness/PCB, startup/partial-power and physical calibration NOT RUN. No short-circuit-current guarantee used.'}
    OUT.write_text(json.dumps(refresh_load_bound(out,report),indent=2)+'\n')
    print('PASS: 24 local reference model cases')
if __name__=='__main__':
    if '--refresh-load-bound' in sys.argv or '--check-load-bound' in sys.argv:
        body=json.dumps(refresh_load_bound(json.loads(OUT.read_text()),build()),indent=2)+'\n'
        if '--check-load-bound' in sys.argv:assert OUT.read_text()==body,'reference model load metadata drift'
        else:OUT.write_text(body)
        print('PASS: reference load arithmetic remains inside retained 24-case nominal model envelope; no new SPICE run')
    else:main()
