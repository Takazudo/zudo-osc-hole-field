"""Select two additive whole-net path transactions on accepted JR153."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
probe_path=HERE/'jr153-fine-probe.json'
assert hashlib.sha256(probe_path.read_bytes()).hexdigest()=='36deff16237f8c59e2d9dbe01a3392ec47a764ade2c1a902e435798e28ba281b'
probe=json.loads(probe_path.read_text());proposal=probe['proposal']
sha='05a8d4beff64f5dee1356f679eb7d24842996d7a6b125047b8f48467e41bac26'
assert proposal['board_sha256']==sha==hashlib.sha256((ROOT/'boards/osc-jack-right/osc-jack-right.kicad_pcb').read_bytes()).hexdigest()
assert not proposal['removed_uuids']
diagnosis_path=HERE/'jr153-three-additive-diagnosis.json'
assert hashlib.sha256(diagnosis_path.read_bytes()).hexdigest()=='aa6ad64ade77e33407703272f6a9e81d67cf06a1e7459718cbeda0c330ea745b'
diagnosis=json.loads(diagnosis_path.read_text());assert diagnosis['input_board_sha256']==sha
assert diagnosis['excluded_whole_net_within2mm']==['XFA0270EBB537DA86D487']
nets={'XCCFC73EB45D48FD86BED','X25A978F2114D0833EE1B'}
rows=[r for r in proposal['copper'] if r['net'] in nets]
assert len(rows)==33 and sum(bool(r['path']) for r in probe['results'] if r['net'] in nets)==2
p=HERE/'jr153-two-filtered-proposal.json';p.write_text(json.dumps({**proposal,'copper':rows},indent=2)+'\n')
plan={'board':'osc-jack-right','input_board_sha256':sha,'name':'189-jr153-two-filtered','proposal':str(p.relative_to(ROOT)),'proposal_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'rail_method':'rail-links','restore_connectivity':True,'scope':'Two additive paths on two complete selected net transactions;33objects; exclude the whole D7208 transaction whose new geometry is within2mm of the natively detached C7221.1,zero removals. Native original groups/warning identities/DRC/parity/fresh gates mandatory. No canonical changes by pilot.'}
(HERE/'jr-coupled-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
print('Prepared33 additive objects/2paths; native NOT RUN')
