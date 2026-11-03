"""Read-only retained identity and pad-datum extraction; no manufacturer requalification."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts/architecture278'))
from populated_mechanics import sexpr, field

def build():
    inputs = set()
    def read(path):
        inputs.add(path)
        return json.loads((ROOT / path).read_text())
    contract = read('design/architecture-278/interface-contract.json')
    inventory = read('.claude/skills/component-spec-audit/references/inventory.json')['lines']
    packages = {}
    for part in contract['parts']:
        if part['proposed_owner'] == 'rear-core':
            continue
        row = packages.setdefault(part['ref'], {'ref':part['ref'], 'owner':part['proposed_owner'],
            'footprint':part['footprint'], 'attributes':part['attributes'], 'units':[], 'pins':{}})
        row['units'].append({'unit':part['unit'], 'key':part['key'], 'role':part['attributes'].get('Role'),
                             'logical_cell':part['attributes'].get('LogicalCellKey')})
        assert not set(row['pins']) & set(part['pins'])
        row['pins'].update(part['pins'])
    identities = {}
    for row in packages.values():
        a = row['attributes']; key = (a.get('Manufacturer',''), a.get('MPN',''))
        if not key[1]:
            row['identity_status'] = 'OPEN: no exact MPN in retained source'
            continue
        if key not in identities:
            matches = [i for i in inventory if (i['manufacturer'],i['mpn']) == key]
            records=[]
            for match in matches:
                base='.claude/skills/'+match['owner_skill']+'/'
                exact=[r for r in read(base+'manifest.json')['records']
                       if (r['manufacturer'],r['mpn'])==key]
                assert len(exact)==1, key
                source_ids=set(exact[0]['source_ids'])
                records.append({'inventory':match, 'record':exact[0],
                    'sources':[s for s in read(base+'sources.json')['sources'] if s['source_id'] in source_ids]})
            identities[key] = {'manufacturer':key[0], 'mpn':key[1], 'owner_matches':records,
                'status':'retained metadata only; read availability/authority/locators separately; no current remote-byte verification'}
        row['identity_key'] = '|'.join(key)
    hardware=[]
    for row in packages.values():
        if not row['attributes'].get('PanelUid'):
            continue
        path='footprints/kicad/zudo-osc-hole-field.pretty/'+row['footprint'].split(':')[1]+'.kicad_mod'
        inputs.add(path); nodes=sexpr((ROOT/path).read_text())
        pads={n[1]:{'local_xy_mm':list(map(float,field(n,'at')[:2])), 'size_mm':field(n,'size'),
                    'drill':field(n,'drill'), 'net':row['pins'].get(n[1])}
              for n in nodes if isinstance(n,list) and n and n[0]=='pad' and n[1]}
        assert set(pads)==set(row['pins']), row['ref']
        hardware.append({'ref':row['ref'],'uid':row['attributes']['PanelUid'],'footprint':path,
            'description':field(nodes,'descr'), 'pads':pads,
            'status':'local unrotated committed CAD coordinates; transform into actual board face/rotation before routing; not installed fit proof'})
    shared=[]
    for net in ['OSC_REF5','OSC_REFN5','OSC_GATE_REF']+[f'OSC_OCT{i}' for i in range(6)]:
        shared.append({'net':net,'shared_source_endpoints':[
            {'ref':p['ref'],'pin':pin,'unit':p['unit']} for p in contract['parts']
            if p['proposed_owner']=='shared-reference' for pin,n in p['pins'].items() if n==net],
            'candidate_nonshared_endpoints':[{'ref':p['ref'],'pin':pin,'owner':p['proposed_owner']}
                for p in contract['parts'] if p['proposed_owner']!='shared-reference'
                for pin,n in p['pins'].items() if n==net]})
    connectors=read('design/connectors/jst-gh.json')
    pdf=connectors['source']['path']; inputs.add(pdf)
    assert hashlib.sha256((ROOT/pdf).read_bytes()).hexdigest()==connectors['source']['sha256']
    derived=[]
    # Exact 2/4 rows read from retained PDF physical page2 (printed3).
    # Top-entry land pattern visually inspected physical page1 (printed2).
    for positions,span,body,housing in [(2,1.25,5.75,3.75),(4,3.75,8.25,6.25)]:
        derived.append({'positions':positions,'header_mpn':f'BM{positions:02d}B-GHS-TBT(LF)(SN)',
            'housing_mpn':f'GHR-{positions:02d}V-S','contact_mpn':'SSHL-002T-P0.2',
            'table_A_mm':span,'header_table_B_mm':body,'housing_table_B_mm':housing,
            'header_depth_mm':4.25,'header_height_mm':4.05,'housing_depth_mm':4.15,'housing_height_mm':5.7,
            'mated_height_reference_mm':7.3,'signal_pad_size_mm':[.6,1.7],
            'signal_pad_centers_mm':[[span/2-i*1.25,0] for i in range(positions)],
            'hold_down_pad_size_mm':[1,2.8],
            'hold_down_pad_centers_mm':[[-(span/2+1.85),3.35],[span/2+1.85,3.35]],
            'candidate_courtyard_mm':[-body/2-.35,-1.1,body/2+.35,5],
            'courtyard_authority':'PROJECT-CHOICE: same margins as retained3/7/8 geometry, not manufacturer courtyard',
            'datum':'connector mounting surface view; pin1 at positive X; signal pad centre row y0; body towards positive Y',
            'source_locator':'physical PDF page2 printed3 exact Housing/Header2/4 rows and LF/SN note; physical page1 printed2 Top entry land pattern and SSHL contact table',
            'source_status':'exact retained PDF hash verified; nominal/reference drawing only; installed mating/derating/strain relief OPEN',
            'land_tolerance_mm':{'signal_width':.05,'pitch_nonaccumulating':.05,'hold_down_width':.1,'hold_down_height':.1},
            'contact_wire_AWG':[30,26],'contact_insulation_OD_mm':[.76,1.0]})
    inputs.add(str(Path(__file__).relative_to(ROOT)))
    inputs.add('scripts/architecture278/populated_mechanics.py')
    return {'status':'SOURCE EVIDENCE MAP; electrical/native/physical acceptance OPEN',
        'packages':list(packages.values()), 'identities':list(identities.values()),'panel_hardware_local_pads':hardware,
        'shared_middle_nets':shared,'retained_JST_sizes':[s['positions'] for s in connectors['sizes']],
        'candidate_JST_2_4_derived':derived,
        'JST_source':connectors['source'],
        'missing_exact_identity_refs':[p['ref'] for p in packages.values() if not p['attributes'].get('MPN')],
        'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(inputs)}}

if __name__=='__main__':
    ap=argparse.ArgumentParser(); ap.add_argument('--check',action='store_true'); args=ap.parse_args()
    output=ROOT/'design/architecture-278/implementation/front-evidence.json'
    data=json.dumps(build(),indent=2,sort_keys=True)+'\n'
    if args.check: assert output.read_text()==data, 'stale front evidence'
    else: output.write_text(data)
    print('PASS retained identity/pad evidence reproduction; manufacturer qualification NOT RUN')
