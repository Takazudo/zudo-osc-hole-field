"""Combine whole, mutually separated raster transactions; native pilot mandatory."""
import hashlib,importlib.util,json,math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
p=HERE.parent/'core-short-no-via/rebase_proposal.py';spec=importlib.util.spec_from_file_location('guard',p);guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
s=json.loads((HERE/'result.json').read_text());b=next(b for b in s['boards'] if b['board']=='osc-jack-right');board=ROOT/'boards/osc-jack-right/osc-jack-right.kicad_pcb';assert sha(board)==b['board_sha256']=='35b52972dd70b4186cf3f3b7ee2ac3d70432f3476c2f56c9fcf9c1c4d7d4d445'
cases=[c for c in b['cases'] if c['complete_raster_transaction']];assert len(cases)==3
rows=[r for c in cases for r in c['proposal']['copper']];assert len(rows)==len({r['uuid'] for r in rows})==118
assert all(not c['proposal']['removed_uuids'] and c['proposal']['board_sha256']==b['board_sha256'] for c in cases)
assert sum(r['kind']=='via' for r in rows)==8
minimum=min(guard.gap(x,y) for i,a in enumerate(cases) for other in cases[:i] for x in a['proposal']['copper'] for y in other['proposal']['copper']);assert minimum>=.25
vias=[r for r in rows if r['kind']=='via'];drill_gap=min((math.dist(a['at_nm'],b['at_nm'])-(a['drill_nm']+b['drill_nm'])/2)/1e6 for i,a in enumerate(vias) for b in vias[:i]);assert drill_gap>=.25
p=HERE/'proposal.json';p.write_text(json.dumps(dict(board_sha256=b['board_sha256'],removed_uuids=[],copper=rows),indent=2)+'\n')
plan=dict(board=b['board'],input_board_sha256=b['board_sha256'],name='189-jr134-post-adoption-neighbours',proposal=str(p.relative_to(ROOT)),proposal_sha256=sha(p),rail_method='rail-links',restore_connectivity=False,scope='Three additive signal component joins near the last accepted repair:110segments/8vias, zero cuts or source changes. All original group, DRC/parity, warning, settled/fresh and retention gates mandatory. Read-only pilot, never canonical promotion.')
(HERE/'plan.json').write_text(json.dumps(plan,indent=2)+'\n')
(HERE/'selection.json').write_text(json.dumps(dict(status='PREPARED RASTER PROPOSAL; NATIVE NOT RUN',result_sha256=sha(HERE/'result.json'),proposal_sha256=sha(p),nets=[c['net'] for c in cases],added_segments=110,added_vias=8,removed_copper=0,minimum_cross_transaction_gap_mm=minimum,minimum_new_drill_gap_mm=drill_gap),indent=2)+'\n')
print('Prepared118additions, zero cuts; native NOT RUN')
