"""Read-only source extraction; writes only the design packet, never CAD."""
from pathlib import Path
import argparse
from collections import defaultdict
import hashlib
import json
import sys
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from design.spec.instrument import specification
from scripts.schgen.core import designator
from design.spec.cells._builder import load_symbol

OUTPUT = ROOT / 'design/architecture-278/interface-contract.json'
OWNERS = {'jack': 'front-jack', 'control': 'front-control', 'selector': 'octave-selector', 'core': 'rear-core'}
SERVICES = ['+12V', '-12V', '+5V', 'AGND', 'OSC_REF5', 'OSC_REFN5', 'OSC_GATE_REF'] + [f'OSC_OCT{i}' for i in range(6)]

def scoped(net, instance, family):
    return net if net is None or net in family.global_nets else f'/{instance.name}/{net}'

def validate(data):
    rows = data['parts']
    ids = [(p['instance'],p['ref'],p['unit']) for p in rows]
    assert len(ids) == len(set(ids)), 'duplicate package unit'
    endpoints = [(p['ref'],p['unit'],pin) for p in rows for pin in p['pins']]
    recorded = [(e['ref'],e['unit'],e['pin']) for n in data['nets'] for e in n['endpoints']] + [(e['ref'],e['unit'],e['pin']) for e in data['no_connects']]
    assert sorted(endpoints) == sorted(recorded), 'endpoint coverage drift'
    for p in rows:
        assert sorted(p['pins']) == p['expected_pins'], 'symbol pin coverage drift'
    for pack in data['packages']:
        matching=[p for p in rows if p['ref']==pack['ref']]
        assert len({p['proposed_owner'] for p in matching})==1, 'split package'
        assert sorted(p['unit'] for p in matching)==pack['units'], 'missing package unit'
    by_part = {(p['ref'], p['unit']): p for p in rows}
    for n in data['nets']:
        assert n['owners'] == sorted({e['owner'] for e in n['endpoints']}), 'net owner summary drift'
        for e in n['endpoints']:
            part = by_part[e['ref'], e['unit']]
            assert part['pins'][e['pin']] == n['net'], 'endpoint net drift'
            assert part['proposed_owner'] == e['owner'], 'endpoint owner drift'
        if n['net'] in SERVICES:
            expected = 'shared power/return' if n['net'] in SERVICES[:4] else 'shared reference'
            assert n['classification'] == expected, 'shared service classification drift'
    for e in data['no_connects']:
        part = by_part[e['ref'], e['unit']]
        assert part['pins'][e['pin']] is None, 'no-connect net drift'
        assert part['proposed_owner'] == e['owner'], 'endpoint owner drift'
    assert len(data['controls'])==8 and len(data['trims'])==6
    assert len(data['harnesses'])==11
    assert sum(h['conductors'] for h in data['harnesses'])==51
    for h in data['harnesses']:
        a,b=h['faces']; assert a['pin_map']==b['pin_map'], 'harness polarity mismatch'
        assert len([n for n in a['pin_map'].values() if n])==h['conductors']
    assert len(data['shared_services'])==13
    for n in data['nets']:
        if n['restriction']=='local-only':
            assert len(n['owners'])==1, 'forbidden sensitive crossing'

def build():
    families, instances=specification()
    families={f.name:f for f in families}; instances={i.name:i for i in instances}
    partition=json.loads((ROOT/'design/partition/partition.json').read_text())
    assignment={p['ref']:p for p in partition['assignment']['components']}
    io=json.loads((ROOT/'design/reports/io-partition.json').read_text())
    crossings={n['net']:n for n in io['allowed_crossings']}
    parts=[]; mapping=[]; bynet=defaultdict(list); nc=[]; packages=defaultdict(list)
    for name in ('O1','OCTAVE_REF'):
        inst=instances[name]; family=families[inst.family]
        for p in family.parts:
            ref=designator(p,inst); attrs={k:v.replace('${SHEETNAME}',name) for k,v in p.attributes.items()}
            region=attrs.get('BoardRegion','core')
            owner=OWNERS[region] if name=='O1' else 'shared-reference'
            row={'expected_pins':sorted(pin.number for pin in load_symbol(p.symbol.split(':')[-1]).units[p.unit]) if p.symbol.startswith('zudo-osc-hole-field:') else sorted(p.pins),'instance':name,'ref':ref,'unit':p.unit,'key':p.key,'symbol':p.symbol,'value':p.value,'pins':{pin:scoped(net,inst,family) for pin,net in p.pins.items()},'attributes':attrs,'current_board':assignment.get(ref,{}).get('board','nonphysical declaration' if not p.footprint else 'UNKNOWN'),'proposed_owner':owner,'core_only_owner':assignment.get(ref,{}).get('board') if region!='core' else owner,'footprint':p.footprint,'dnp':p.dnp,'on_board':p.on_board,'in_bom':p.in_bom}
            parts.append(row); packages[ref].append(row)
            for pin,net in row['pins'].items():
                endpoint={'ref':ref,'unit':p.unit,'pin':pin,'owner':owner,'role':attrs.get('Role','')}
                (nc if net is None else bynet[net]).append(endpoint)
            if name=='O1':
                mapping.append({'key':p.key,'unit':p.unit,'refs':{n:designator(p,instances[n]) for n in ('O1','O2','O5')},'pins':{n:{pin:scoped(net,instances[n],family) for pin,net in p.pins.items()} for n in ('O1','O2','O5')}})
    retained={(p['ref'],p['unit']):p for p in io['package_units']}
    for p in parts:
        if p['symbol'].startswith('Fixture:'):
            continue  # Nonphysical PWR_FLAG has no retained physical package row.
        key=(p['ref'],p['unit'])
        assert key in retained, f'retained unit missing: {key}'
        assert p['pins']==retained[key]['pins'], f'retained endpoint/net mismatch: {key}'
        assert p['attributes'].get('BoardRegion','core')==retained[key]['region'].replace('selector_front','selector').replace('selector_rear','selector'), f'retained owner mismatch: {key}'
    selected_refs={p['ref'] for p in io['physical_packages'] if p['instance'] in ('O1','OCTAVE_REF')}
    live_keys={(p['ref'],p['unit']) for p in parts if not p['symbol'].startswith('Fixture:')}
    assert live_keys=={key for key in retained if key[0] in selected_refs}, 'retained package-unit coverage mismatch'
    nets=[]
    sensitive=set(families['oscillator'].sensitive_nets)|{'VEE5','VEE_FB','VEE_DRIVE','TRI_RAW','SAW_RAW','PULSE_RAW'}
    for net,ends in sorted(bynet.items()):
        owners=sorted({e['owner'] for e in ends}); cross=crossings.get(net)
        if cross:
            cross={**cross,'members':[m for m in cross.get('members',[]) if m['ref'] in packages]}
        restriction='local-only' if net.split('/')[-1] in sensitive else 'defined-crossing-only' if len(owners)>1 else 'local'
        nets.append({'net':net,'owners':owners,'endpoints':ends,'restriction':restriction,'classification': ('shared power/return' if net in SERVICES[:4] else 'shared reference') if net in SERVICES else cross.get('kind','source-local') if cross else 'source-local','source_crossing':cross,'return':'AGND continuous local return; dedicated crossing returns retained; shared impedance not qualified','protection':'Front jack raw input fault switch and high impedance input; output driver/protection/feedback local to front-jack. Other crossings fault isolation OPEN #59.'})
    connectors={c['id']:c for c in partition['connectors']}
    harnesses=[]
    for h in partition['harnesses']:
        if 'O1' not in h['boards'] and not any(s['net'].startswith('/O1/') for s in h['signals']):continue
        faces=[connectors[x] for x in h['header_ids']]
        n=h['signal_count']+h['return_contacts']
        harnesses.append({**h,'faces':faces,'conductors':n,'crimps':2*n,'mating_contacts':2*n,'candidate_disposition':'Retain endpoint net and explicit return; replace centre span with zone traces plus two short keyed links. Adds middle-facing mates, no net deletion. Exact connector/contact count OPEN.','core_only_disposition':'Retain front harness; rear core disconnect replaces K-side termination; exact mating geometry OPEN.'})
    controls=[]
    for p in parts:
        if p['instance']!='O1' or not p['attributes'].get('PanelUid','').startswith('C:'):continue
        pot=p['ref'].startswith('RV')
        controls.append({'uid':p['attributes']['PanelUid'],'ref':p['ref'],'pins':p['pins'],'type':'unbuffered wiper' if pot else 'mechanical selector','wiper_pin':'2' if pot else None,'source_resistance_upper_ohm':2500 if pot and p['value'].endswith('B103') else 25000 if pot else None,'resistance_basis':'nominal Rpot/4; tolerance and source/contact impedance additional' if pot else 'selected source and switch contact; OPEN bound','load':'Existing local receiver endpoints in nets; leakage/bias/capacitance and settling allocation OPEN','length_limit_mm':300,'total_capacitance_limit_pF':1000,'limit_scope':'complete remote path including cable, connector, trace and probe; octave fanout limit aggregate across all five branches','buffer_assumed':False})
    trims=[{'ref':p['ref'],'key':p['key'],'value':p['value'],'pins':p['pins'],'mpn':p['attributes'].get('MPN'),'access':'rear powered calibration only under separately authorized safe bench procedure; replacement power-off/discharged','owner':p['proposed_owner']} for p in parts if p['instance']=='O1' and p['ref'].startswith('RVO')]
    sources=set(['design/partition/partition.json','design/reports/io-partition.json','design/grid/placements.lock.json'])
    for folder,glob in [('design/spec','*.py'),('scripts/schgen','*.py'),('design/standard','*.json'),('scripts/schgen/fixtures','*'),('symbols/src','*.kicad_sym'),('scripts/libgen','*.py')]:
        sources.update(str(p.relative_to(ROOT)) for p in (ROOT/folder).rglob(glob) if p.is_file())
    # Capture every local file read by the pure source compiler, including symbols.
    sources.update(str(p.relative_to(ROOT)) for p in (ROOT/'design').rglob('*.kicad_sym'))
    sources.update(['scripts/architecture278/extract.py','scripts/checks/io_partition60.py'])
    data={'schema_version':1,'retained_report_parity':'PASS exact physical unit/pin/net/region equality; nonphysical flags explicitly excluded','status':'SOURCE MAPPING ONLY; candidate NOT ADOPTED; physical/electrical qualification NOT RUN','source_sha256':{s:hashlib.sha256((ROOT/s).read_bytes()).hexdigest() for s in sorted(sources)},'parts':parts,'packages':[{'ref':ref,'units':sorted(u for u,pins in load_symbol(rows[0]['symbol'].split(':')[-1]).units.items() if pins) if rows[0]['symbol'].startswith('zudo-osc-hole-field:') else sorted(p['unit'] for p in rows),'owner':rows[0]['proposed_owner'],'repartition_required':False,'basis':'Existing refined region packages retained whole; changed front buffer ownership would require repacking and new parity proof'} for ref,rows in sorted(packages.items())],'nets':nets,'no_connects':nc,'controls':controls,'trims':trims,'shared_services':SERVICES,'harnesses':harnesses,'instance_mapping':mapping,'rear_terminals':[dict(t,function='existing shared rail/return terminal',protection='upstream source protection unresolved #59/#247',support_load_path='factory strain relief/support required; solder land not structural support',service='retain factory termination; removable card must disconnect without owner soldering; connector conversion OPEN') for t in partition['load_side_terminals']],'existing_headers_on_K':[c for h in harnesses for c in h['faces'] if c['board']=='K'],'additional_performance_io':'NONE authorized; any new terminal/output requires owner decision','proposed_connector_contract':{'mpn':None,'pin_assignment':None,'keying':'unique polarized keyed circuit-specific groups; prevent reversal and cross-family mating; exact coding OPEN','partial_power':'No hot swap; discharge before removal. Missing rail/off-state injection and fault recovery OPEN #59/#247','middle_faces':'Both front and rear middle faces require counted mating pairs, explicit returns and mounting clearance; 13 services do not define connector pin count','test_adapters':'Separate non-final fixture bill required; count presently OPEN'},'blockers':['Exact final connector pinout and return multiplicity','Worst-case receiver loading, source impedance across frequency and partial-power protection','Shared reference five-receiver capacitance/noise/drift allocation and bench verification','Rear terminal support/strain relief and removable interface conversion','HF trim exact orderable identity absent in source']}
    validate(data)
    return data

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    text=json.dumps(build(),indent=2,ensure_ascii=False,sort_keys=True)+'\n'
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text()!=text:raise SystemExit('interface extraction drift')
        print('PASS source extraction parity; NOT RUN electrical/physical qualification')
    else:OUTPUT.write_text(text);print(OUTPUT.relative_to(ROOT))
if __name__=='__main__':main()
