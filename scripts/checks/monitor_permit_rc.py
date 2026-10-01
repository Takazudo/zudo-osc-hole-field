#!/usr/bin/env python3
"""Fresh pinned ngspice diagnostics of the candidate's passive timing chain."""
import argparse
import hashlib
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.checks import monitor_permit_behavior as behavior
from scripts.checks import monitor_rc_math as reference
SPEC=ROOT/'design/power/monitor-permit-draft.json'
CATALOG=ROOT/'design/power/monitor-permit-parts.json'
REPORT=ROOT/'design/power/monitor-permit-rc-report.json'
VOLTAGE_TOLERANCE=0.00005
CHARGE_TOLERANCE=2e-12
CROSSING_REFINEMENT_TOLERANCE=5e-9
STEPS=(5e-7,1.25e-7)


def source_parameters():
    spec=json.loads(SPEC.read_text());behavior.build(spec)
    parts={p['ref']:p for p in spec['components']}
    catalog={p['mpn']:p for p in json.loads(CATALOG.read_text())['parts']}
    for ref in ('R120','R121'):
        if parts[ref]['value']!=catalog[parts[ref]['mpn']]['resistance_ohm']:
            raise ValueError('timing resistance differs from exact MPN')
    bundles=[ROOT/'.claude/skills/component-passives-family',ROOT/'.claude/skills/component-ti-sn74hc14dr']
    requested=[('rec-c-hold','fact-c-hold-capacitance','C109'),('rec-schmitt','fact-schmitt-input-capacitance','U104')]
    facts=[];paths={SPEC,CATALOG,Path(behavior.__file__).resolve(),Path(reference.__file__).resolve(),Path(__file__).resolve(),ROOT/'scripts/kicad/run.sh',ROOT/'scripts/kicad/pin.env'}
    for bundle,(rid,fid,ref) in zip(bundles,requested):
        paths.update(bundle/name for name in ('facts.json','manifest.json','sources.json'))
        record=next(r for r in json.loads((bundle/'manifest.json').read_text())['records'] if r['record_id']==rid)
        fact=next(f for f in json.loads((bundle/'facts.json').read_text())['facts'] if f['fact_id']==fid)
        source=next(s for s in json.loads((bundle/'sources.json').read_text())['sources'] if s['source_id']==fact['source_id'])
        if (record['mpn']!=parts[ref]['mpn'] or fact['record_id']!=rid or source['record_id']!=rid
                or fid not in record['fact_ids'] or fact['source_id'] not in record['source_ids']
                or fact['verdict']!='PASS - primary-source confirmed' or fact['provenance']!='PRIMARY-SPEC'
                or fact['class']!='GUARANTEED_ELECTRICAL'
                or source['availability']!='AVAILABLE' or source['authority_class']!='MANUFACTURER_PRIMARY'
                or not re.fullmatch('[0-9a-f]{64}',source['sha256']) or set(source['sha256'])=={'0'}):
            raise ValueError('timing-capacitance source closure failed')
        facts.append(fact)
    if facts[0]['unit']!='nF and VDC' or facts[1]['unit']!='pF':
        raise ValueError('capacitance source units changed')
    cap=facts[0]['value']['nominal']*1e-9;pin_cap=facts[1]['value']*1e-12
    if not math.isclose(cap,parts['C109']['value'],rel_tol=1e-14,abs_tol=0):
        raise ValueError('timing capacitance differs from exact MPN')
    reference.parameters(parts['R120']['value'],parts['R121']['value'],cap,pin_cap)
    return {'r1':parts['R120']['value'],'r2':parts['R121']['value'],'cap':cap,'pin_cap':pin_cap,
            'supply_V':5.0,'high_V':5*spec['model_conditions']['schmitt_high_fraction'],
            'low_V':5*spec['model_conditions']['schmitt_low_fraction'],
            'observer_scope':spec['model_conditions']['schmitt_scope'],'source_facts':facts},paths


def cases(parameters):
    v=parameters['supply_V'];crossing=-parameters['r1']*parameters['cap']*math.log(parameters['low_V']/v)
    edge=1e-9;start=1e-6;stop=0.001
    waves={'startup':([[0,0],[start,0],[start+edge,v],[stop,v]],(0,0),False)}
    for name,duration in [('short_good_fast_pulse',.8*crossing),('long_good_fast_pulse',1.2*crossing)]:
        duration=round(duration,12)  # Deterministic picosecond stimulus grid.
        waves[name]=([[0,v],[start,v],[start+edge,0],[start+duration,0],[start+duration+edge,v],[stop,v]],(v,v),True)
    result=[]
    for name,(points,initial,observer_initial) in waves.items():
        for label,pin_cap in [('zero_pin_c',0),('source_pin_c',parameters['pin_cap'])]:
            result.append({'name':name+'_'+label,'mode':'timing','points':points,'initial':initial,
                           'observer_initial':observer_initial,'pin_cap':pin_cap,'expected_observer_crossings':1 if name=='startup' else 0 if name.startswith('short') else 2})
    result.append({'name':'forced_zero_endpoints','mode':'forced_clamp','initial':(v,0),'pin_cap':0,'stop':stop})
    return result


def deck(case,p,step):
    lines=['* UNSELECTED PASSIVE MODEL: no buffer, Schmitt, latch, transistor or die-clamp model',
           f"R120 good delay_cap {p['r1']:.17g}",f"R121 delay_cap delay_in {p['r2']:.17g}",
           f"C109 delay_cap 0 {p['cap']:.17g}"]
    if case['mode']=='timing':
        points=' '.join(f'{t:.17g} {v:.17g}' for t,v in case['points'])
        lines.append('Vdrive good 0 PWL('+points+')')
        if case['pin_cap']>0:lines.append(f"Cpin delay_in 0 {case['pin_cap']:.17g}")
        stop=case['points'][-1][0];vectors='v(delay_cap) v(delay_in) i(vdrive)'
    else:
        lines+=['Vdrive good 0 0','Vclamp delay_in 0 0'];stop=case['stop']
        vectors='v(delay_cap) v(delay_in) i(vdrive) i(vclamp)'
    lines += [f".ic v(delay_cap)={case['initial'][0]:.17g} v(delay_in)={case['initial'][1]:.17g}",
              '.options reltol=1e-9 abstol=1e-13 vntol=1e-10 method=gear',
              '.control','set wr_singlescale','set wr_vecnames','set numdgt=15',
              f'tran {step:.17g} {stop:.17g} 0 {step:.17g} uic',
              'wrdata waveform.dat '+vectors,'quit','.endc','.end']
    return '\n'.join(lines)+'\n'


def native_worker(directory):
    directory=(ROOT/directory).resolve()
    if ROOT/'.circuit-cache' not in directory.parents:raise ValueError('native output directory outside cache')
    version=subprocess.run(['ngspice','--version'],capture_output=True,text=True,check=True).stdout
    if not re.search(r'ngspice-44\.2\s',version):raise ValueError('required ngspice44.2 unavailable')
    manifest=json.loads((directory/'manifest.json').read_text())
    for name in manifest:
        if not re.fullmatch('[a-z0-9_]+',name):raise ValueError('invalid native case name')
        case_dir=directory/name
        output=subprocess.run(['ngspice','-b','model.cir'],cwd=case_dir,capture_output=True,text=True)
        (case_dir/'native.log').write_text(output.stdout+output.stderr)
        if output.returncode:raise ValueError('native simulator failed: '+name)
        if not (case_dir/'waveform.dat').is_file():raise ValueError('native waveform missing: '+name)
    (directory/'native-version.txt').write_text('ngspice44.2\n')


def read_waveform(path,columns):
    lines=path.read_text().splitlines()
    expected=['time','v(delay_cap)','v(delay_in)','i(vdrive)']+(['i(vclamp)'] if columns==5 else [])
    if columns not in (4,5) or not lines or lines[0].split()!=expected:
        raise ValueError('unexpected waveform header')
    rows=[tuple(float(v) for v in line.split()) for line in lines[1:]]
    if len(rows)<10 or any(len(row)!=columns or not all(math.isfinite(v) for v in row) for row in rows):
        raise ValueError('invalid native waveform')
    if any(b[0]<=a[0] for a,b in zip(rows,rows[1:])):raise ValueError('native time is not strictly increasing')
    return rows


def inspect(case,p,rows,step):
    stop=case['points'][-1][0] if case['mode']=='timing' else case['stop']
    if rows[0][0]>step/10 or abs(rows[-1][0]-stop)>1e-12:
        raise ValueError('native waveform coverage incomplete')
    first_expected=case['initial']
    if case['mode']=='forced_clamp':
        tau=p['cap']/(1/p['r1']+1/p['r2'])
        first_expected=(case['initial'][0]*math.exp(-rows[0][0]/tau),0)
    if max(abs(rows[0][i+1]-first_expected[i]) for i in range(2))>VOLTAGE_TOLERANCE:
        raise ValueError('charged initial condition was not retained')
    errors=[0.0,0.0]
    if case['mode']=='timing':
        trajectory=reference.Trajectory(case['points'],case['initial'],p['r1'],p['r2'],p['cap'],case['pin_cap'])
        for row in rows:
            expected=trajectory.value(row[0])
            errors=[max(errors[i],abs(row[i+1]-expected[i])) for i in range(2)]
        observed=reference.observer(rows,p['high_V'],p['low_V'],case['observer_initial'])
        if len(observed['crossings'])!=case['expected_observer_crossings']:
            raise ValueError('ideal observer crossing inventory differs: '+case['name'])
        # Compare the independent analytic voltage at each native bracket;
        # allow only the already-declared voltage-comparison tolerance.
        for event in observed['crossings']:
            threshold=p['low_V'] if event['transition']=='fall_low' else p['high_V']
            lo,hi=[trajectory.value(t)[1] for t in event['bracket_s']]
            if not min(lo,hi)-VOLTAGE_TOLERANCE <= threshold <= max(lo,hi)+VOLTAGE_TOLERANCE:
                raise ValueError('native crossing bracket disagrees with RC reference')
        change=p['cap']*(rows[-1][1]-rows[0][1])+case['pin_cap']*(rows[-1][2]-rows[0][2])
        delivered=-reference.integrate(rows,3)
        charge_error=abs(change-delivered)
        result={'ideal_observer':observed,'charge_balance_error_C':charge_error}
        if charge_error>CHARGE_TOLERANCE:raise ValueError('RC charge conservation failed')
    else:
        tau=p['cap']/(1/p['r1']+1/p['r2'])
        for row in rows:
            expected=case['initial'][0]*math.exp(-row[0]/tau)
            errors[0]=max(errors[0],abs(row[1]-expected));errors[1]=max(errors[1],abs(row[2]))
        available=p['cap']*case['initial'][0]
        left=reference.integrate(rows,3);right=reference.integrate(rows,4)
        residual=p['cap']*rows[-1][1]
        sampled_available=p['cap']*rows[0][1]
        if abs(left+right+residual-sampled_available)>CHARGE_TOLERANCE:raise ValueError('forced discharge charge conservation failed')
        result={'forced_C109_only_tau_s':tau,'left_charge_C':left,'right_charge_C':right,
                'first_sample_branch_current_A':[rows[0][3],rows[0][4]],
                'ideal_t0_branch_current_A':[case['initial'][0]/p['r1'],case['initial'][0]/p['r2']],
                'integration_start_s':rows[0][0],'available_t0_charge_C':available,
                'available_first_sample_charge_C':sampled_available,
                'scope':'Both resistor endpoints forced to0V; pin capacitance omitted. Not a die-clamp or floating-supply model.'}
    if max(errors)>VOLTAGE_TOLERANCE:raise ValueError('native RC waveform differs from independent equations: '+str(errors))
    result.update(maximum_voltage_difference_V=errors,sample_count=len(rows),step_limit_s=step)
    return result


def run(check=False):
    p,paths=source_parameters()
    before={str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(paths)}
    cache=ROOT/'.circuit-cache';cache.mkdir(exist_ok=True)
    directory=Path(tempfile.mkdtemp(prefix='monitor-rc-',dir=cache))
    manifest=[];definitions=cases(p);hashes={}
    for case in definitions:
        for i,step in enumerate(STEPS):
            name=case['name']+'_'+str(i);manifest.append(name)
            case_dir=directory/name;case_dir.mkdir()
            text=deck(case,p,step);(case_dir/'model.cir').write_text(text)
            hashes[name]=hashlib.sha256(text.encode()).hexdigest()
    (directory/'manifest.json').write_text(json.dumps(manifest)+'\n')
    subprocess.run(['bash',str(ROOT/'scripts/kicad/run.sh'),'python3',str(Path(__file__).relative_to(ROOT)),
                    '--native-worker',str(directory.relative_to(ROOT))],cwd=ROOT,check=True)
    results={}
    for case in definitions:
        resolutions=[]
        for i,step in enumerate(STEPS):
            rows=read_waveform(directory/(case['name']+'_'+str(i))/'waveform.dat',4 if case['mode']=='timing' else 5)
            resolutions.append(inspect(case,p,rows,step))
        if case['mode']=='timing':
            a,b=[row['ideal_observer']['crossings'] for row in resolutions]
            if [e['transition'] for e in a]!=[e['transition'] for e in b]:raise ValueError('observer changed with timestep refinement')
            if any(abs(x['linear_interpolation_s']-y['linear_interpolation_s'])>CROSSING_REFINEMENT_TOLERANCE for x,y in zip(a,b)):
                raise ValueError('crossing time fails timestep refinement')
        results[case['name']]=resolutions
    after={str(path.relative_to(ROOT)):hashlib.sha256(path.read_bytes()).hexdigest() for path in sorted(paths)}
    if before!=after:raise ValueError('model source changed during native run')
    data={'status':'CONDITIONAL PASSIVE RC DIAGNOSTICS; NOT IC OR PHYSICAL QUALIFICATION',
          'qualification_accepted':False,'physical_permit_release_bound_s':None,
          'oracle':'ngspice44.2 through pinned KiCad10.0.6 scripts/kicad/run.sh',
          'parameters':p,'voltage_comparison_tolerance_V':VOLTAGE_TOLERANCE,
          'charge_balance_tolerance_C':CHARGE_TOLERANCE,
          'crossing_refinement_tolerance_s':CROSSING_REFINEMENT_TOLERANCE,
          'cases':definitions,'results':results,'input_sha256':before,'deck_sha256':hashes,
          'limitations':['GOOD_FAST is a prescribed ideal source, not an external rail fault or an actual HC14 output.',
             '10pF is a5V owner-table sensitivity, not an unpowered nonlinear pin-network bound.',
             'Nominal C109 uses its retained capacitance test conditions; this does not qualify installed transient capacitance.',
             'Observer fractions are illustrative; no HC74 pulse capture, reset-removal, NPN release or startup guarantee.',
             'Forced zero endpoints do not model die clamps, surviving control power, other stored capacitors or a charged pin-capacitance impulse.']}
    # Round display-only metrics to prevent insignificant host math-library
    # differences; acceptance uses unrounded native/analytic values above.
    def rounded(value):
        if isinstance(value,float):return float(f'{value:.10g}')
        if isinstance(value,list):return [rounded(v) for v in value]
        if isinstance(value,dict):return {k:rounded(v) for k,v in value.items()}
        return value
    data['results']=rounded(results)
    text=json.dumps(data,indent=2)+'\n'
    if check:
        if not REPORT.exists() or REPORT.read_text()!=text:raise ValueError('native RC report drift')
    else:REPORT.write_text(text)
    print('PASS: fresh passive RC waveforms and independent equations; physical permit OPEN')
    print('Raw native evidence retained locally at '+str(directory.relative_to(ROOT)))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');parser.add_argument('--native-worker')
    args=parser.parse_args()
    if args.native_worker:native_worker(args.native_worker)
    else:run(args.check)
