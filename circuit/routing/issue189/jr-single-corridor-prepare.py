"""Prepare the complete D7504.1 transaction and one diagnosed dangling-tail cut.

This is a candidate only: original return membership and every native gate still apply.
"""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
cache=ROOT/'.circuit-cache/issue189-downloaded/jr-six-corridors'
base=json.loads((cache/'osc-jack-right-grid-189-local-base/dump.json').read_text())
after=json.loads((cache/'osc-jack-right-grid-189-jr-six-corridors-verify/dump.json').read_text())
sha='cf8cabf2e115e294a7a67253eae290ecd02a57419b5996a54e8755fcf79196cf'
assert base['board_sha256']==sha==hashlib.sha256((ROOT/'boards/osc-jack-right/osc-jack-right.kicad_pcb').read_bytes()).hexdigest()
assert after['board_sha256']=='c88b0582e6e112a8618f4ecfe92a69306985c3c623417eff8d07c06df5543626'
replay=HERE/'jr-six-corridors-copper.json'
assert hashlib.sha256(replay.read_bytes()).hexdigest()=='5c4e776f1f7cb1afa57af8ae1d677b25855cb95ce64513d2b28029fc197ec8a9'
delta=json.loads(replay.read_text())
selection=next(e for e in json.loads((HERE/'jr-six-corridors-selection.json').read_text()) if e['target']=='X3307A17C148FAA8F7A4D')
nets={selection['target'],*selection['victims']}
receipt=json.loads((HERE/'jr-six-corridors-result.json').read_text())
assert not nets&{g['net'] for g in receipt['gate']['split_pad_groups']}
stub='464b5771-fcf1-5ef3-9331-4894362f895a'
assert ['track_dangling',[stub]] in receipt['gate']['new_warning_identities']
t=next(t for t in base['tracks'] if t['uuid']==stub)
assert t==next(t for t in after['tracks'] if t['uuid']==stub)
assert t['net']=='X117A9D03425A2C3FC85C' and t['a']==[409200000,178800000] and t['b']==[409750000,178800000]
assert t['width']==200000 and t['layer']=='In2.Cu'
added={x['uuid'] for x in delta['added'] if x['net'] in nets};rows=[]
for t in after['tracks']:
    if t['uuid'] in added:rows.append({'kind':'segment','uuid':t['uuid'],'net':t['net'],'start_nm':t['a'],'end_nm':t['b'],'width_nm':t['width'],'layer':t['layer']})
for v in after['vias']:
    if v['uuid'] in added:rows.append({'kind':'via','uuid':v['uuid'],'net':v['net'],'at_nm':v['xy'],'diameter_nm':v['diameter'],'drill_nm':v['drill']})
assert len(rows)==len(added)
proposal={'board_sha256':sha,'removed_uuids':sorted(selection['removed_source_uuids']+[stub]),'copper':rows}
p=HERE/'jr-single-corridor-proposal.json';p.write_text(json.dumps(proposal,indent=2)+'\n')
plan={'board':'osc-jack-right','input_board_sha256':sha,'name':'189-jr-single-corridor','proposal':str(p.relative_to(ROOT)),'proposal_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'rail_method':'rail-links','restore_connectivity':True,'scope':'D7504.1 with complete victim repair plus one diagnosed0.55mm tail cut. No signal pad group split in donor, but actual isolated return/fill connectivity is unknown. Full native coupled restoration, warning, original membership and independent reload gates mandatory; no canonical promotion by pilot.'}
(HERE/'jr-coupled-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
print('Prepared',len(rows),'additions;',len(proposal['removed_uuids']),'cuts; native isolated gate NOT RUN')
