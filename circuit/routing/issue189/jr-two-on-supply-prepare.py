"""Rebase eligible signal copper onto the exact independently eligible additive supply board.

This prepares a reviewed replay only. The merger must validate the combined board
against the newly accepted canonical input; no old board is copied over it.
"""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from scripts.pcbgen.route_shards import copper_block_groups,delta,merge_text
cache=ROOT/'.circuit-cache/issue189-downloaded/jr-rail-finer'
base=(cache/'osc-jack-right-grid-189-local-base/osc-jack-right.kicad_pcb').read_text()
supply=(cache/'osc-jack-right-grid-189-jr153-rail-finer-fresh/osc-jack-right.kicad_pcb').read_text()
old_sha='05a8d4beff64f5dee1356f679eb7d24842996d7a6b125047b8f48467e41bac26';new_sha='ea5f09c78cd1146ad5c4f8a1f9e573bb644e9e96cd3ee0d02ab5c8a64b3cf6e2'
assert hashlib.sha256(base.encode()).hexdigest()==old_sha and hashlib.sha256(supply.encode()).hexdigest()==new_sha
assert hashlib.sha256((ROOT/'boards/osc-jack-right/osc-jack-right.kicad_pcb').read_bytes()).hexdigest()==new_sha
r=json.loads((HERE/'jr153-two-filtered-result.json').read_text());assert r['gate']['adopted'] and not r['gate']['native_errors'] and not r['gate']['split_pad_groups'] and not r['gate']['new_warning_identities']
p=HERE/'jr153-two-filtered-copper.json';assert hashlib.sha256(p.read_bytes()).hexdigest()==r['replay_sha256'];tail=json.loads(p.read_text());assert tail['base_sha256']==old_sha and not set(tail['nets'])&{'AGND','+12V','-12V','+5V'}
supply_delta=delta(base,supply);assert not supply_delta['removed'] and len(supply_delta['added'])==10 and supply_delta['nets']==['-12V']
before,current=copper_block_groups(base),copper_block_groups(supply)
assert all(rows==current[u] for u,rows in before.items())
assert all(len(before[x['uuid']])==1 and before[x['uuid']]==current[x['uuid']] for x in tail['removed'])
assert all(x['uuid'] not in current for x in tail['added'])
rebased={**tail,'base_sha256':new_sha};candidate=merge_text(supply,[rebased]);actual=delta(supply,candidate);assert actual==rebased
assert len(rebased['removed'])==0 and len(rebased['added'])==33
remaining=copper_block_groups(candidate)
assert all(current[x['uuid']]==remaining[x['uuid']] for x in supply_delta['added'])
(HERE/'jr-two-on-supply-copper.json').write_text(json.dumps(rebased,sort_keys=True)+'\n')
proof={'status':'REVIEWED REBASE; COMBINED NATIVE GATE NOT RUN','old_input_sha256':old_sha,'new_input_sha256':new_sha,'signal_donor_candidate_sha256':r['candidate_sha256'],'signal_donor_replay_sha256':r['replay_sha256'],'supply_objects_preserved':10,'supply_objects_removed':0,'removed_signal_objects':0,'added_signal_objects':33,'retained_current_objects':sum(len(v) for u,v in current.items() if u not in {x['uuid'] for x in tail['removed']}),'scope':'Every old copper block is unchanged on the additive supply input; all signal removal identities and geometry match, additions do not collide, all10new supply blocks survive exactly. Canonical merger must require this exact new board hash and all native original membership/warning/fresh gates.'}
(HERE/'jr-two-on-supply-rebase.json').write_text(json.dumps(proof,indent=2)+'\n');print('Prepared signal replay on exact supply input;',proof['retained_current_objects'],'supply-input objects retained; combined native NOT RUN')
