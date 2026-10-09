"""Rebind the sole fine-grid signal path while preserving every accepted JL supply object."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from scripts.pcbgen.copper_identity import retention,reject_new_uuid_collisions
cache=ROOT/'.circuit-cache/issue189-downloaded/jl-rail-finer'
before=json.loads((cache/'osc-jack-left-grid-189-local-base/dump.json').read_text())
after=json.loads((cache/'osc-jack-left-grid-189-jl134-rail-finer-fresh/dump.json').read_text())
old='892c31f6d97081723864996d601ece6ecf272c25140fd1169f9e534b1adcda6a';new='343add6006f409640372f77cee521f717626c852c9ee8f68066b78c6b91471f7'
assert before['board_sha256']==old and after['board_sha256']==new
assert hashlib.sha256((ROOT/'boards/osc-jack-left/osc-jack-left.kicad_pcb').read_bytes()).hexdigest()==new
kept=retention(before,after);assert kept['identical']==33131 and kept['added_objects']==10 and kept['removed_objects']==0 and not kept['changed_existing_uuids']
p=HERE/'jl134-finer-probe.json';assert hashlib.sha256(p.read_bytes()).hexdigest()=='12a1d1ee291d098308f0773171e8f3158feb409d2e20ce63133cddf77c7ba589'
probe=json.loads(p.read_text());proposal=probe['proposal'];assert proposal['board_sha256']==old and not proposal['removed_uuids']
assert len(proposal['copper'])==8 and {r['net'] for r in proposal['copper']}=={'XAA649996BC6F560931CB'}
assert [r['island'] for r in probe['results'] if r['path']]==[['D2326.1']]
reject_new_uuid_collisions([i['uuid'] for k in ('tracks','vias') for i in after[k]],proposal['copper'])
p=HERE/'jl127-d2326-proposal.json';p.write_text(json.dumps({**proposal,'board_sha256':new},indent=2)+'\n')
plan={'board':'osc-jack-left','input_board_sha256':new,'name':'189-jl127-d2326','proposal':str(p.relative_to(ROOT)),'proposal_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'rail_method':'rail-links','restore_connectivity':True,'scope':'One additive D2326.1 signal path;8objects,zero removals. Rebound onto exact accepted127 only after verifying all33131oldobjects and10new supply objects remain. Full native baseline127 membership/warnings/DRC/parity/fresh gates mandatory. Native NOT RUN for combined proposal.'}
(HERE/'jl-coupled-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
(HERE/'jl127-d2326-rebase.json').write_text(json.dumps({'status':'HASH REBIND ONLY; NATIVE NOT RUN','old_input_sha256':old,'new_input_sha256':new,'supply_adoption_retention':kept,'new_signal_objects':8,'removed_objects':0,'new_uuid_collisions':False},indent=2)+'\n')
print('Prepared8signal additions on accepted127; all10supply objects preserved; native NOT RUN')
