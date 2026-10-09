"""Prepare one exact ground escape corridor on accepted JL134, preserving the prior repair."""
import json,hashlib,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.pcbgen.route_jack_grid import repair_selection,repair_search_dump
h=ROOT/'circuit/routing/issue189';p=ROOT/'.circuit-cache/issue189-downloaded/jl-ground-junction/osc-jack-left-grid-189-jl-ground-junction-fresh/dump.json';d=json.loads(p.read_text())
sha='892c31f6d97081723864996d601ece6ecf272c25140fd1169f9e534b1adcda6a';assert d['board_sha256']==sha==hashlib.sha256((ROOT/'boards/osc-jack-left/osc-jack-left.kicad_pcb').read_bytes()).hexdigest();assert d['open_edges']==134
selections=[json.loads((h/f'jl-ground-{ref}-selection.json').read_text()) for ref in ('RB2217',)];objects={}
for kind in ('tracks','vias'):
 for o in d[kind]:objects.setdefault(o['uuid'],[]).append(o)
for s in selections:
 for o in s['selected_objects']:assert objects[o['object']['uuid']]==[o['object']]
ids=sorted({u for s in selections for u in s['removed_source_uuids']});assert len(ids)==7
pads={p['ref']+'.'+p['pad']:p for p in d['pads']};sources=[pads[r+'.2']['uuid'] for r in ('RB2217',)];main=max(d['islands']['AGND'],key=len)
assert pads['R1301.2']['uuid'] in main and not set(sources)&set(main)
plan={'board':'osc-jack-left','input_board_sha256':sha,'scope':'Existing isolated ground group RB2217.2; seven exact signal segments on one victim net. Rebound from135 geometric selection only after all selected object geometry is proven unchanged on accepted134; the prior R1301 ground repair remains in the complete native baseline. No canonical changes by pilot.','stage':{'name':'189-jl-rb2217-ground-corridor','repair':True,'repair_targets':['AGND'],'repair_ground_pad_uuids':sources,'repair_source_uuids':ids,'clearance':.25,'signal_width':.2,'signal_via_diameter':.6,'grow':{n:.05 for n in ('+12V','-12V','+5V','AGND')},'res':.05,'window_mm':8}}
assert repair_selection(d,plan['stage'])==(['AGND'],set(ids));assert len(repair_search_dump(d,plan['stage'])['islands']['AGND'])==2
(h/'jl-local-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
print('Prepared1 source group/7 exact objects/1signal victim on accepted134; native NOT RUN')
