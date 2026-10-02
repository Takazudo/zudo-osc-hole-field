"""TI OPAx197 model screening of the new selected-signal harness path (#60).

Includes selected contact 2.2k/10M loading, local-feedback isolated harness driver,
0/1 nF internal harness, and local precision jack output. No contact bounce,
make-before-break, component tolerance, faults or hardware qualification.
"""
import hashlib
import json
import subprocess
import sys
from design.spec.cells.sweep_precision_vendor import model, measure, LIB_SHA256, deck
from design.spec.modules.manual_ab import ROOT, family
from design.spec.modules.io_partition import AMP_MAPS

CACHE=ROOT/'.circuit-cache/manual-ab-spice'
OUT=ROOT/'design/reports/spice/manual_ab.json'


def make_deck(load, cable, harness):
    f=family()
    remote=[p for p in f.parts if p.attributes.get('Role')=='internal_selector_buffer:A']
    assert len(remote)==1 and remote[0].symbol.endswith('OPA4197IPWR')
    out,minus,plus=AMP_MAPS[remote[0].unit-1]
    assert remote[0].pins[plus]=='SELECTOR_COMMON' and remote[0].attributes['BoardRegion']=='control'
    precision=next(p for p in f.parts if p.attributes.get('Role')=='precision_output:A')
    assert precision.pins[AMP_MAPS[precision.unit-1][2]]=='SELECTOR_REMOTE'
    from design.spec.modules.run_oscillator_spice import number
    cell={p.attributes['Role'].split(':')[1]:number(p.value) for p in f.parts if p.attributes.get('Role') in ('internal_selector_buffer:R_ISO_A','internal_selector_buffer:R_ISO_B')}
    assert remote[0].pins[minus] == remote[0].pins[out]
    roles={p.attributes.get('Role'):p for p in f.parts}
    assert roles['manual_ab:R_SELECT_A_SERIES'].value=='2.2 kΩ'
    assert roles['manual_ab:R_SELECT_COMMON_BIAS'].value=='10 MΩ'
    body=deck(load,cable).replace('Xamp sig fb vp vn drive OPAx197','Xamp remote fb vp vn drive OPAx197')
    extra=['Rselected sig selected 2200','Rbias selected 0 10Meg',
           'Xremote selected rdrive vp vn rdrive OPAx197',
           f"Rremote_a rdrive rmid {cell['R_ISO_A']:g}",
           f"Rremote_b rmid remote {cell['R_ISO_B']:g}"]
    if '--diagnostic-original' in sys.argv:
        extra=['Rselected sig selected 2200','Rbias selected 0 10Meg',
               'Xremote selected rfb vp vn rdrive OPAx197',
               'Rremote rdrive remote 100','Rremote_fb remote rfb 10k','Cremote_fast rdrive rfb 100p']
    if harness:extra.append(f'Charness remote 0 {harness}')
    return body.replace('.control','\n'.join(extra)+'\n.control')


def main():
    model();CACHE.mkdir(parents=True,exist_ok=True)
    init=ROOT/'.spiceinit'
    if init.exists():raise RuntimeError('refusing to overwrite .spiceinit')
    init.write_text('set ngbehavior=ps\n')
    rows=[]
    try:
        for load in ('1e12','100k','10k'):
            for cable in (None,'100p','1n','5n'):
                for harness in (None,'1n'):
                    if ('--probe' in sys.argv or '--diagnostic-original' in sys.argv) and (load,cable,harness)!=('100k','1n','1n'):continue
                    name=f'{load}-{cable or "0"}-{harness or "0"}'
                    source=make_deck(load,cable,harness);path=CACHE/(name+'.cir');path.write_text(source)
                    result=subprocess.run(['bash','scripts/kicad/run.sh','ngspice','-b',str(path.relative_to(ROOT))],cwd=ROOT,capture_output=True,text=True)
                    (CACHE/(name+'.log')).write_text(result.stdout+result.stderr)
                    if result.returncode:raise RuntimeError(result.stderr)
                    m=measure(result.stdout)
                    error=max(abs(m[k]-(5 if k.startswith('p') else -5))*1000 for k in ('pset','nset','p2set','n2set'))
                    expected=5*1e7/(1e7+2200)
                    settling=max(abs(m[k]-(expected if k.startswith('p') else -expected))*1000 for k in ('pset','nset','p2set','n2set'))
                    ripple=max((m[a]-m[b])*1000 for a,b in [('platmax','platmin'),('nlatmax','nlatmin'),('p2latmax','p2latmin'),('n2latmax','n2latmin')])
                    over=max(0,max(m['pmax'],m['p2max'])-5,-5-min(m['nmin'],m['n2min']))/10*100
                    rows.append({'load':load,'output_capacitance':cable or '0','internal_harness_capacitance':harness or '0',
                                 'deck_sha256':hashlib.sha256(source.encode()).hexdigest(),'total_error_mV_by_400us':error,
                                 'settling_error_mV_by_400us':settling,'late_ripple_mV':ripple,'overshoot_percent':over,
                                 'pass':error<=2 and settling<=1 and ripple<=1 and over<=10})
    finally:init.unlink()
    report={'schema_version':1,'status':'PASS - TI MODEL ONLY' if all(r['pass'] for r in rows) else 'FAIL - TI MODEL',
            'oracle':'pinned KiCad 10.0.6 wrapper / ngspice','model_library_sha256':LIB_SHA256,'cases':rows,
            'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in ['design/spec/modules/manual_ab.py','design/spec/modules/io_partition.py','design/spec/modules/run_manual_ab_spice.py']},
            'limits':'27 C nominal model; ideal +/-5V source represents A_BUFFER/B_BUFFER, followed by 2.2k series/10M bias, local harness follower and precision jack-output cell. Source-facing protection and the input amplifier are excluded. <=2mV selected-buffered-source-to-jack error at the sampled settling times; <=1mV settling error from the resistor-loaded nominal by 400us, <=1mV late ripple, <=10% overshoot. Internal harness <=1nF; external <=5nF. Contact transition/bounce, overload, tolerance, partial power, protection #59 and bench NOT RUN.'}
    report['circuit']='REJECTED diagnostic: 100ohm isolation, 10k feedback, 100pF local compensation; not fitted' if '--diagnostic-original' in sys.argv else 'FITTED DRAFT: local unity feedback plus two 499ohm resistors; high-impedance receiver'
    target=ROOT/'design/reports/spice/manual-ab-rejected-remote.json' if '--diagnostic-original' in sys.argv else CACHE/'probe.json' if '--probe' in sys.argv else OUT
    target.write_text(json.dumps(report,indent=2)+'\n');print(report['status'],len(rows),'cases')
    if not all(r['pass'] for r in rows):raise SystemExit(1)

if __name__=='__main__':main()
