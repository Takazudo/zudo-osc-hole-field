import json,uuid,hashlib
from pathlib import Path
from shapely.geometry import Polygon,LineString,Point
root=Path('.circuit-cache/issue189-downloaded/jr-rb4413-move');d=json.loads((root/'osc-jack-right-grid-189-jr-rb4413-candidate/dump.json').read_text());net='X34EC684E00B004F73024';line=LineString([(385.7,92.7),(385.7,92.4)]).buffer(.1);rows=[]
for p in d['pads']:
 if p['net']!=net and 'B.Cu' in p['layers'] and p['poly']:rows.append((p['uuid'],line.distance(Polygon([(x/1e6,y/1e6) for x,y in p['poly']]))))
for t in d['tracks']:
 if t['net']!=net and t['layer']=='B.Cu':rows.append((t['uuid'],line.distance(LineString([[v/1e6 for v in t[k]] for k in ['a','b']]).buffer(t['width']/2e6))))
for v in d['vias']:
 if v['net']!=net:rows.append((v['uuid'],line.distance(Point([x/1e6 for x in v['xy']]).buffer(v['diameter']/2e6))))
minimum=min(rows,key=lambda p:p[1]);assert minimum[1]>=.25-1e-8;print('minimum foreign copper gap',minimum)
source=Path('circuit/routing/issue189/jr-rb4413-move');out=Path('circuit/routing/issue189/jr-rb4413-edge-bridge');out.mkdir(exist_ok=True)
p=json.loads((source/'proposal.json').read_text());row=dict(kind='segment',uuid=str(uuid.uuid5(uuid.NAMESPACE_URL,'issue189-rb4413-old-edge-bridge')),net=net,layer='B.Cu',start_nm=[385700000,92700000],end_nm=[385700000,92400000],width_nm=200000);p['copper'].append(row);(out/'proposal.json').write_text(json.dumps(p,indent=2)+'\n')
plan=json.loads((source/'plan.json').read_text());plan['proposal_sha256']=hashlib.sha256((out/'proposal.json').read_bytes()).hexdigest();plan['changed_method']='Restore actual existing pad-edge landing 34f3b8b3 at385.7,92.7, not only old pad centre';(out/'plan.json').write_text(json.dumps(plan,indent=2)+'\n');(out/'static-clearance.json').write_text(json.dumps(dict(status='STATIC ONLY; NATIVE NOT RUN',rejected_candidate_sha256=d['board_sha256'],old_landing_uuid='34f3b8b3-14db-5078-9909-c5d7b4d35488',added_segment=row,minimum_foreign_copper=minimum),indent=2)+'\n')
