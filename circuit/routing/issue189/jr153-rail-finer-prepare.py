"""Prepare five full-width supply escapes from the pinned accepted JR153 input."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
p=HERE/'jr153-rail-finer-probe.json';assert hashlib.sha256(p.read_bytes()).hexdigest()=='e980dc2db6adb8209c8e43e5b00b962ce7b96451b6bb0ef386a27b1f4d47ac09'
probe=json.loads(p.read_text());proposal=probe['proposal'];sha='05a8d4beff64f5dee1356f679eb7d24842996d7a6b125047b8f48467e41bac26'
assert proposal['board_sha256']==sha==hashlib.sha256((ROOT/'boards/osc-jack-right/osc-jack-right.kicad_pcb').read_bytes()).hexdigest()
assert not proposal['removed_uuids'] and len(proposal['copper'])==10
assert all(r['kind']=='segment' and r['net']=='-12V' and r['width_nm']==250000 and r['layer']=='F.Cu' for r in proposal['copper'])
assert sum(bool(r['path']) for r in probe['results'])==5
p=HERE/'jr153-rail-finer-proposal.json';p.write_text(json.dumps(proposal,indent=2)+'\n')
plan={'board':'osc-jack-right','input_board_sha256':sha,'name':'189-jr153-rail-finer','proposal':str(p.relative_to(ROOT)),'proposal_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'rail_method':'rail-links','restore_connectivity':True,'scope':'Five existing minus-twelve groups;10full-width250000nm F.Cu segments,zero vias/removals. Existing rail-escape dimensions,0.025mm raster. No signal neckdown. Full native groups/warnings/DRC/parity/fresh acceptance mandatory; no canonical change by pilot.'}
(HERE/'jr-coupled-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
print('Prepared10full-width segments/5supply paths; native NOT RUN')
