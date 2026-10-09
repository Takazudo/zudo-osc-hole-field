"""Prepare seven full-width supply escapes from the pinned accepted JL134 input."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];HERE=Path(__file__).resolve().parent
p=HERE/'jl134-rail-finer-probe.json';assert hashlib.sha256(p.read_bytes()).hexdigest()=='701ad4a39c80737986af0eae6621f538f08b36dc1255bface6a57c4e8e9161ba'
probe=json.loads(p.read_text());proposal=probe['proposal'];sha='892c31f6d97081723864996d601ece6ecf272c25140fd1169f9e534b1adcda6a'
assert proposal['board_sha256']==sha==hashlib.sha256((ROOT/'boards/osc-jack-left/osc-jack-left.kicad_pcb').read_bytes()).hexdigest()
assert not proposal['removed_uuids'] and len(proposal['copper'])==10
assert all(r['kind']=='segment' and r['net'] in ('+12V','-12V') and r['width_nm']==250000 and r['layer'] in ('F.Cu','B.Cu') for r in proposal['copper'])
assert sum(bool(r['path']) for r in probe['results'])==7
p=HERE/'jl134-rail-finer-proposal.json';p.write_text(json.dumps(proposal,indent=2)+'\n')
plan={'board':'osc-jack-left','input_board_sha256':sha,'name':'189-jl134-rail-finer','proposal':str(p.relative_to(ROOT)),'proposal_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'rail_method':'rail-links','restore_connectivity':True,'scope':'Seven existing plus/minus-twelve groups;10full-width250000nm outer-layer segments,zero vias/removals. Existing rail-escape dimensions,0.025mm raster. No signal neckdown. Full native groups/warnings/DRC/parity/fresh acceptance mandatory; no canonical change by pilot.'}
(HERE/'jl-coupled-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
print('Prepared10full-width segments/7supply paths; native NOT RUN')
