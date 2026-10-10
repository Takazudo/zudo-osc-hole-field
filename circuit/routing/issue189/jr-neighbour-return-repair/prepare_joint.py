"""Isolate one whole unaccepted signal case with its explicit native-split repair."""
import hashlib,importlib.util,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
spec=importlib.util.spec_from_file_location('guard',HERE.parent/'core-short-no-via/rebase_proposal.py');guard=importlib.util.module_from_spec(spec);spec.loader.exec_module(guard)
original=HERE.parent/'jack-post-adoption-neighbours';native=json.loads((original/'native-rejection.json').read_text());assert native['artifact_sha256']=='89d3b9b245998063c77e031190bd123e5b2abcb868129773626e75e5b57eb2d1' and not native['native_pilot_eligible']
s=json.loads((original/'result.json').read_text());case=next(c for b in s['boards'] if b['board']=='osc-jack-right' for c in b['cases'] if c['net']=='XF80280C65F38E93A154C');assert case['complete_raster_transaction'] and len(case['proposal']['copper'])==77
repair=json.loads((HERE/'result.json').read_text());assert not repair['all_four_have_raster_restoration'];success=[r for r in repair['trials'] if r['complete_raster_transaction']];assert len(success)==1
r=success[0];assert set(r['pad_names'])=={'U7607.5','C7615.2','C7622.2'} and r['net']=='AGND' and len(r['copper'])==2
rows=case['proposal']['copper']+r['copper'];assert len({x['uuid'] for x in rows})==79
minimum=min(guard.gap(x,y) for x in case['proposal']['copper'] for y in r['copper']);assert minimum>=.25
source=ROOT/'boards/osc-jack-right/osc-jack-right.kicad_pcb';assert sha(source)==case['proposal']['board_sha256']
proposal=HERE/'joint-proposal.json';proposal.write_text(json.dumps({**case['proposal'],'copper':rows},indent=2)+'\n')
plan=dict(board='osc-jack-right',input_board_sha256=sha(source),name='189-jr134-d7604-return-joint',proposal=str(proposal.relative_to(ROOT)),proposal_sha256=sha(proposal),rail_method='rail-links',restore_connectivity=False,scope='One whole D7604.1-D7603.1 signal case plus explicit U7607.5/C7615.2/C7622.2 return:74segments/5vias, zero cuts/moves; other two unaccepted cases omitted. Native whole-board original groups, DRC/parity, warnings and settled/fresh gates mandatory; no automatic restoration or publication.')
(HERE/'joint-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
(HERE/'joint-selection.json').write_text(json.dumps(dict(status='CHANGED JOINT PROPOSAL; NATIVE NOT RUN',source_sha256=sha(source),original_screen_sha256=sha(original/'result.json'),native_rejection_sha256=sha(original/'native-rejection.json'),repair_screen_sha256=sha(HERE/'result.json'),proposal_sha256=sha(proposal),minimum_new_ground_signal_gap_mm=minimum,added_segments=74,added_vias=5,removed_copper=0,omitted_whole_unaccepted_nets=['X3307A17C148FAA8F7A4D','XF19CF8B5CE37D561D88A']),indent=2)+'\n')
print('Prepared74segments/5vias, no cuts; native NOT RUN; minimum signal/ground gap',minimum)
