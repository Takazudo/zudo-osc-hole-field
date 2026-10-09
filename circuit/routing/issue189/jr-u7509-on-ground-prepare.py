"""Rebase eligible signal copper onto the exact independently eligible additive ground board.

This prepares a reviewed replay only. The merger must validate the combined board
against the newly accepted canonical input; no old board is copied over it.
"""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from scripts.pcbgen.route_shards import copper_block_groups,delta,merge_text
cache=ROOT/'.circuit-cache/issue189-downloaded/jr-original-ground'
base=(cache/'osc-jack-right-grid-189-local-base/osc-jack-right.kicad_pcb').read_text()
ground=(cache/'osc-jack-right-grid-189-jr-original-ground-fresh/osc-jack-right.kicad_pcb').read_text()
old_sha='cf8cabf2e115e294a7a67253eae290ecd02a57419b5996a54e8755fcf79196cf';new_sha='3e7305df6f30fb66593e767d1c36c148684ae8664e71a82f4a1bf381f77de9f6'
assert hashlib.sha256(base.encode()).hexdigest()==old_sha and hashlib.sha256(ground.encode()).hexdigest()==new_sha
assert hashlib.sha256((ROOT/'boards/osc-jack-right/osc-jack-right.kicad_pcb').read_bytes()).hexdigest()==new_sha
r=json.loads((HERE/'jr-u7509-tail-result.json').read_text());assert r['gate']['adopted'] and not r['gate']['native_errors'] and not r['gate']['split_pad_groups'] and not r['gate']['new_warning_identities']
p=HERE/'jr-u7509-tail-copper.json';assert hashlib.sha256(p.read_bytes()).hexdigest()==r['replay_sha256'];tail=json.loads(p.read_text());assert tail['base_sha256']==old_sha and 'AGND' not in tail['nets']
ground_delta=delta(base,ground);assert not ground_delta['removed'] and len(ground_delta['added'])==24 and ground_delta['nets']==['AGND']
before,current=copper_block_groups(base),copper_block_groups(ground)
assert all(rows==current[u] for u,rows in before.items())
assert all(len(before[x['uuid']])==1 and before[x['uuid']]==current[x['uuid']] for x in tail['removed'])
assert all(x['uuid'] not in current for x in tail['added'])
rebased={**tail,'base_sha256':new_sha};candidate=merge_text(ground,[rebased]);actual=delta(ground,candidate);assert actual==rebased
assert len(rebased['removed'])==13 and len(rebased['added'])==33
remaining=copper_block_groups(candidate)
assert all(current[x['uuid']]==remaining[x['uuid']] for x in ground_delta['added'])
(HERE/'jr-u7509-on-ground-copper.json').write_text(json.dumps(rebased,sort_keys=True)+'\n')
proof={'status':'REVIEWED REBASE; COMBINED NATIVE GATE NOT RUN','old_input_sha256':old_sha,'new_input_sha256':new_sha,'signal_donor_candidate_sha256':r['candidate_sha256'],'signal_donor_replay_sha256':r['replay_sha256'],'ground_objects_preserved':24,'ground_objects_removed':0,'removed_signal_objects':13,'added_signal_objects':33,'retained_current_objects':sum(len(v) for u,v in current.items() if u not in {x['uuid'] for x in tail['removed']}),'scope':'Every old copper block is unchanged on the additive ground input; all signal removal identities and geometry match, additions do not collide, all24newground blocks survive exactly. Canonical merger must require this exact new board hash and all native original membership/warning/fresh gates.'}
(HERE/'jr-u7509-on-ground-rebase.json').write_text(json.dumps(proof,indent=2)+'\n');print('Prepared signal replay on exact ground input;',proof['retained_current_objects'],'ground-input objects retained; combined native NOT RUN')
