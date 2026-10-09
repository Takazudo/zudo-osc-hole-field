"""Prepare one additive JR ground link from the pinned canonical155 dump."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
probe_path=HERE/'jr-original-ground-probe.json'
assert hashlib.sha256(probe_path.read_bytes()).hexdigest()=='28c7045945b1d1b1ed5ff8f13bc2db24169589face0540f83790e61801c75481'
probe=json.loads(probe_path.read_text())
proposal=probe['proposal'];sha='cf8cabf2e115e294a7a67253eae290ecd02a57419b5996a54e8755fcf79196cf'
assert proposal['board_sha256']==sha==hashlib.sha256((ROOT/'boards/osc-jack-right/osc-jack-right.kicad_pcb').read_bytes()).hexdigest()
assert not proposal['removed_uuids'] and len(proposal['copper'])==24
assert all(row['net']=='AGND' for row in proposal['copper'])
assert sum(bool(r['path']) for r in probe['results'])==1
p=HERE/'jr-original-ground-proposal.json';p.write_text(json.dumps(proposal,indent=2)+'\n')
plan={'board':'osc-jack-right','input_board_sha256':sha,'name':'189-jr-original-ground','proposal':str(p.relative_to(ROOT)),'proposal_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'rail_method':'rail-links','restore_connectivity':True,'scope':'One additive original AGND group connection;24objects,zero removals. Dedicated ground layer allowed for ground only. Full original membership/warning/DRC/parity/fresh gates mandatory. Raster only until native pilot passes.'}
(HERE/'jr-coupled-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
print('Prepared24 additive ground objects; native NOT RUN')
