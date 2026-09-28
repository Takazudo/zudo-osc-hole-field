#!/usr/bin/env python3
"""Check real oracle pads/DRC, fixed coordinates, indexing and conservative envelopes."""
from collections import Counter
import hashlib
import itertools
import json
import math
import re
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts/libgen'))
from gen_courtyards import courtyard_box
A=json.loads((ROOT/'design/mechanical/selector-assembly.json').read_text())
LOCK=json.loads((ROOT/'design/grid/placements.lock.json').read_text())
P={p['uid']:p for p in LOCK['placements']}
OUT=ROOT/'.circuit-cache/selector-fixture'
fixed=hashlib.sha256(json.dumps(sorted((p['uid'],p['x_mm'],p['y_mm']) for p in P.values()),separators=(',',':')).encode()).hexdigest()
assert fixed==A['fixed_uid_xy_sha256'] and len(P)==438,'fixed UID/x/y changed'
grid=json.loads((ROOT/'project/osc-hole-field/workbench/layout/grid.json').read_text())
assert len(grid['blocks'])==33
assert len(A['instances'])==5 and len({i['uid'] for i in A['instances']})==5
assert {i['uid'] for i in A['instances']}=={p['uid'] for p in P.values() if p['kind']=='octave'}
assert A['panel']['aperture_diameter_mm']==7.0
clearance=A['panel']['shaft_clearance_budget']
assert abs((clearance['minimum_front_bore_mm']-clearance['shaft_or_extension_max_allowed_mm'])/2-clearance['relative_axis_error_max_mm']-clearance['radial_wobble_allocation_mm']-clearance['remaining_radial_clearance_mm'])<1e-8
assert A['carrier']['bushing_hole_diameter_mm']-A['carrier']['hole_diameter_tolerance_mm']>9
assert A['electrical']['clockwise_terminals']==[2,3,4,5,6,7]
assert A['electrical']['clockwise_octaves']==[-2,-1,0,1,2,3]
# A rigid rotation preserves angular order. A 180-degree pointer correction restores common panel indexing.
for i in A['instances']:
    assert i['rotation_deg'] in (0,180)
    assert (i['rotation_deg']+i['knob_index_correction_deg'])%360==0
    assert all(((j*30+i['rotation_deg']+i['knob_index_correction_deg'])%360)==j*30 for j in range(6))
    assert P[i['uid']]['rot_deg']==i['rotation_deg']
    assert P[i['uid']]['assembly_pcb_z_mm']==i['pcb_z_mm']
    assert P[i['uid']]['hole_d_mm']==A['panel']['aperture_diameter_mm']

def counters(name):
    j=json.loads((OUT/f'{name}-drc.json').read_text())
    assert j['kicad_version']=='10.0.6'
    return dict(sorted(Counter(v['type'] for v in j['violations']).items()))
report={'status':'CONDITIONAL UNVALIDATED DRAFT','physical_qualification_issue':A['physical_qualification_issue'],'fixed_features':438,'fixed_modules':33,'fixed_uid_xy_sha256':fixed,'kicad_version':'10.0.6','drc':{}}
for name in ('front','rear','rejected-alternating-coplanar','rejected-same-coplanar'):
    report['drc'][name]=counters(name)
    m=json.loads((OUT/f'{name}-measurements.json').read_text())
    if name in ('front','rear'):
        expected={i['uid'] for i in A['instances'] if i['adapter_group']==name}
        assert len(m['instances'])==len(expected)
        assert {i['uid'] for i in m['instances']}==expected
    for part in m['instances']:
        p=P[part['uid']];assert part['shaft_xy_mm']==[p['x_mm'],p['y_mm']]
        rotation=part['rotation_deg'];sign=1 if rotation==0 else -1
        assert set(part['pads'])==set(map(str,range(1,11)))|{'MP1','MP2'}
        for terminal,xy in {'1':(5,9.15),'2':(2.5,9.15),'3':(0,9.15),'4':(-2.5,9.15),'5':(-5,9.15),'6':(-5,-9.15),'7':(-2.5,-9.15),'8':(0,-9.15),'9':(2.5,-9.15),'10':(5,-9.15),'MP1':(-8,-1.1),'MP2':(8,-1.1)}.items():
            actual=part['pads'][terminal]
            assert all(abs(actual['xy_mm'][n]-(p[key]+sign*xy[n]))<1e-6 for n,key in enumerate(('x_mm','y_mm')))
        for num,pad in part['pads'].items():
            mount=num.startswith('MP')
            assert pad['diameter_mm']==(2.6 if mount else 1.55)
            assert pad['drill_mm']==(2 if mount else .9)
            assert pad['attribute']==0,'PTH must not be silently changed to NPTH'
report['drc']['panel']=counters('panel')
assert not report['drc']['panel'],'panel aperture must not introduce copper or legend violations'
assert not report['drc']['front'] and not report['drc']['rear']
assert report['drc']['rejected-same-coplanar'].get('hole_to_hole')==4
assert not report['drc']['rejected-alternating-coplanar'].get('hole_to_hole')
assert report['drc']['rejected-alternating-coplanar']['clearance']>=4
assert report['drc']['rejected-alternating-coplanar']['courtyards_overlap']==4
bore_distance=math.hypot(17-16,2.2)
report['coplanar_alternating']={'nearest_bore_centers_mm':round(bore_distance,6),'nominal_bore_web_mm':round(bore_distance-2,6),'copper_overlap_mm':round(2.6-bore_distance,6),'solid_clearance':'NOT ESTABLISHED; conservative 18.2 mm support envelope overlaps 1.2 mm in projection'}
# Independent world-space AABBs enclose unknown contours. They are keepouts, not measured solids.
boxes=[]
def add(i,kind,xy,z):
    p=P[i['uid']];x0,y0,x1,y1=xy
    if i['rotation_deg']==180:x0,y0,x1,y1=-x1,-y1,-x0,-y0
    boxes.append({'uid':i['uid'],'kind':kind,'box':[p['x_mm']+x0,p['y_mm']+y0,i['pcb_z_mm']+z[0],p['x_mm']+x1,p['y_mm']+y1,i['pcb_z_mm']+z[1]]})
for i in A['instances']:
    add(i,'body-support-mounting-tail',A['drawing']['conservative_body_support_xy_mm'],A['drawing']['body_support_z_mm'])
    add(i,'terminal-tail',A['drawing']['terminal_tail_xy_mm'],A['drawing']['terminal_tail_z_mm'])
    add(i,'adapter',[-9.9,-10.5,9.9,10.5],[-1.6,0])
    add(i,'bushing',[-4.5,-4.5,4.5,4.5],[7.5,14.5])
    add(i,'carrier-plate',[-7.5,-7.5,7.5,7.5],[7.5,9.5])
    add(i,'washer',[-7,-7,7,7],[9.5,10])
    add(i,'nut',[-6.351,-6.351,6.351,6.351],[10,12])
    add(i,'shaft',[-3,-3,3,3],[14.5,23])
    if i['extension_length_mm']:
        add(i,'extension-socket',[-5,-5,5,5],[16,22.5])
        add(i,'extension-stem',[-3,-3,3,3],[22.5,35.5])
    # Global Z=1..10 for every knob.
    add(i,'knob',[-4,-4,4,4],[1-i['pcb_z_mm'],10-i['pcb_z_mm']])
def intersects(a,b):
    return all(min(a[n+3],b[n+3])-max(a[n],b[n])>1e-8 for n in range(3))
collisions=[(a['uid'],a['kind'],b['uid'],b['kind']) for a,b in itertools.combinations(boxes,2) if a['uid']!=b['uid'] and intersects(a['box'],b['box'])]
assert not collisions,collisions
report['inter_selector_keepout_intersections']=collisions
report['keepout_boxes']=boxes
planes=sorted(set(i['pcb_z_mm'] for i in A['instances']))
assert len(planes)==2
step=planes[1]-planes[0]
span=A['drawing']['body_support_z_mm'][1]-A['drawing']['body_support_z_mm'][0]
budget=A['tolerance_budget']
assert step-span-budget['body_and_tail_z_growth_mm']-budget['relative_adapter_z_error_mm']>=budget['allocated_min_z_gap_mm']
report['clearances_mm']={'complete_envelopes_z':step-span,'allocated_z_after_growth_and_placement':step-span-budget['body_and_tail_z_growth_mm']-budget['relative_adapter_z_error_mm'],'extension_socket_to_neighbor_body_x':17-9.1-5,'knob_to_knob':17-A['knob']['diameter_mm'],'washer_to_washer':17-14,'socket_tool_to_socket_tool':17-15}
# Compare each generated component keepout projection to every other nearby control's existing courtyard.
# This is conservative in depth, and cannot qualify that other component's own envelope.
neighbor_checks=[]
for p in P.values():
    if p['kind'] not in ('pot','switch'):continue
    name='PTV09A-4020F' if p['kind']=='pot' else 'Toggle_Dailywell_2MS_T1B1M2'
    x0,y0,x1,y1=courtyard_box((ROOT/f'footprints/kicad/zudo-osc-hole-field.pretty/{name}.kicad_mod').read_text())
    target=[p['x_mm']+x0,p['y_mm']+y0,p['x_mm']+x1,p['y_mm']+y1]
    for i in A['instances']:
        q=P[i['uid']]
        if math.hypot(q['x_mm']-p['x_mm'],q['y_mm']-p['y_mm'])>22:continue
        for box in [b for b in boxes if b['uid']==i['uid']]:
            b=box['box'];dx=max(target[0]-b[3],b[0]-target[2]);dy=max(target[1]-b[4],b[1]-target[3])
            assert max(dx,dy)>0,(i['uid'],box['kind'],p['uid'],'neighbor envelope intersection')
            neighbor_checks.append({'selector':i['uid'],'feature':box['kind'],'neighbor':p['uid'],'separating_axis_gap_mm':round(max(dx,dy),4)})
report['nearest_neighbor_courtyard_projection_gap_mm']=min(x['separating_axis_gap_mm'] for x in neighbor_checks)
report['neighbor_projection_checks']=neighbor_checks
# Check the actual VRML coordinate units independently of display auto-framing.
wrl=(ROOT/'footprints/kicad/zudo-osc-hole-field.3dshapes/SRBV160803.wrl').read_text()
points=[]
for group in re.findall(r'point \[ (.*?) \]',wrl):
    for triplet in group.split(','):
        points.append([float(v)*2.54 for v in triplet.split()])
assert points
bounds=[min(p[n] for p in points) for n in range(3)]+[max(p[n] for p in points) for n in range(3)]
assert all(abs(a-b)<1e-6 for a,b in zip(bounds,[-9.1,-9.6,-4,9.1,10.5,23])),bounds
report['model_bounds_mm_xyz']=bounds
report['limits']=['Keepout boxes are source-bounded nominal envelopes, not exact solids or guaranteed tolerance maxima.', 'Minimum neighbor courtyard gap 0.25 mm is not a manufacturing acceptance; current toggle body gap is 0.96 mm. Unknown toggle/carrier tolerances remain physical qualification.', 'Carrier rail anchorage, local tongue capture, socket clamp detail, harness/tool paths and structural loads require qualification.', 'DRC fixtures contain no functional circuitry or routed harness; clean DRC proves only local board geometry.', 'Physical fit, clockwise continuity and strength: NOT RUN; no hardware available.']
path=ROOT/'design/mechanical/selector-assembly-check.json';path.write_text(json.dumps(report,indent=2)+'\n')
print('PASS: 438 fixed UID/x/y; 33 modules; six-position mapping and indexing arithmetic; unchanged pads; front/rear KiCad DRC zero; rejected candidates correctly fail; no inter-selector conservative keepout intersections')
print('Physical fit and continuity: NOT RUN; see linked mechanical qualification issue')
