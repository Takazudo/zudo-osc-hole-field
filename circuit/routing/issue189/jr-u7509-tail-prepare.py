"""Trim the natively warned terminal chain only as far as its first real junction."""
import hashlib,json,uuid
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
cache=ROOT/'.circuit-cache/issue189-downloaded/jr-u7509-corridor'
base=json.loads((cache/'osc-jack-right-grid-189-local-base/dump.json').read_text())
d=json.loads((cache/'osc-jack-right-grid-189-jr-u7509-corridor-fresh/dump.json').read_text())
assert d['board_sha256']=='40936b28005c8dc3837975937f685975816542e35f088e5fa77aac008ba4593b'
sha='cf8cabf2e115e294a7a67253eae290ecd02a57419b5996a54e8755fcf79196cf'
assert base['board_sha256']==sha==hashlib.sha256((ROOT/'boards/osc-jack-right/osc-jack-right.kicad_pcb').read_bytes()).hexdigest()
receipt=json.loads((HERE/'jr-u7509-corridor-result.json').read_text());assert not receipt['gate']['split_pad_groups']
assert receipt['gate']['new_warning_identities']==[['track_dangling',['a8da143b-4322-575b-a928-c80d1621b6bf']]]
screen=json.loads((HERE/'jr-u7509-tail-screen.json').read_text());assert len(screen['removed_tracks'])==5
assert screen['input_dump_sha256']==hashlib.sha256((cache/'osc-jack-right-grid-189-jr-u7509-corridor-fresh/dump.json').read_bytes()).hexdigest()
original={t['uuid']:t for t in base['tracks']};current={t['uuid']:t for t in d['tracks']}
for t in screen['removed_tracks']:assert t==original[t['uuid']]==current[t['uuid']]
old=current['dba0a1b8-52e4-5196-9963-ef7821fae7cb'];assert old==original[old['uuid']]
assert old['a']==[391900000,189300000] and old['b']==[391900000,191650000]
assert old['net']=='XC8DB0BC9B43634A2B597' and old['width']==200000 and old['layer']=='In2.Cu'
# The independently checked new victim track joins this retained branch here.
junction=[391900000,190250000];joining=current['89abda1b-73f9-5a30-ab4d-9263197aa189']
assert joining['net']==old['net'] and joining['layer']==old['layer'] and junction in (joining['a'],joining['b'])
replacement={'kind':'segment','net':old['net'],'start_nm':junction,'end_nm':old['b'],'width_nm':old['width'],'layer':old['layer']}
replacement['uuid']=str(uuid.uuid5(uuid.NAMESPACE_URL,'issue189-u7509-tail/'+json.dumps(replacement,sort_keys=True)))
proposal=json.loads((HERE/'jr-u7509-corridor-proposal.json').read_text());assert proposal['board_sha256']==sha
proposal['removed_uuids']=sorted(set(proposal['removed_uuids'])|{t['uuid'] for t in screen['removed_tracks']}|{old['uuid']})
proposal['copper'].append(replacement);assert len(proposal['removed_uuids'])==13 and len(proposal['copper'])==33
p=HERE/'jr-u7509-tail-proposal.json';p.write_text(json.dumps(proposal,indent=2)+'\n')
plan={'board':'osc-jack-right','input_board_sha256':sha,'name':'189-jr-u7509-tail','proposal':str(p.relative_to(ROOT)),'proposal_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'rail_method':'rail-links','restore_connectivity':True,'scope':'Native U7509 candidate preserves every original pad group and closes one edge, rejected only for a remaining dangling tail. Remove its five short centerline segments and trim the next original segment to the first verified junction; preserve the remaining1.4mm. Full original native gates mandatory; no warning waiver.'}
(HERE/'jr-coupled-plan.json').write_text(json.dumps(plan,indent=2)+'\n');print('Prepared33 additions/13 removals; native NOT RUN')
