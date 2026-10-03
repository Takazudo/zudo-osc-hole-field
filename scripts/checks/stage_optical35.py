#!/usr/bin/env python3
"""Build a bounded optical-plane candidate; never report installed fit as passed."""
from __future__ import annotations
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.checks.partition35_json import dumps
from scripts.checks.partition35_diagnostic import footprint_geometry
OUT = ROOT/'design/partition/stage-optical-candidate.json'
SVG = ROOT/'design/partition/stage-optical-candidate.svg'


def build():
    source=json.loads((ROOT/'design/partition/stage-optical-input.json').read_text())
    lock=json.loads((ROOT/'design/grid/placements.lock.json').read_text())['placements']
    io=json.loads((ROOT/'design/reports/io-partition.json').read_text())
    selected=[p for p in io['physical_packages'] if p['regions']==['stage_optical']]
    refs={p['ref'] for p in selected}
    stage_uids={p['panel_uid'] for p in selected if p['panel_uid']}
    wanted={p['uid'] for p in lock if p.get('led_type')=='stage'}
    if stage_uids!=wanted or len(stage_uids)!=12:raise ValueError('stage LED roster mismatch')
    for p in selected:
        if p['decouples_ref'] and p['decouples_ref'] not in refs:raise ValueError('stage bypass left its package')
    for island in io['islands']:
        if set(island['refs'])&refs and not set(island['refs'])<=refs:raise ValueError('stage island split')
    for row in io['local_raw_sensitive_nets']:
        if set(row['refs'])&refs and not set(row['refs'])<=refs:raise ValueError('stage sensitive net split')
    crossings=[]
    for row in io['allowed_crossings']:
        if 'stage_optical' in row['regions']:crossings.append({'net':row['net'],'kind':row['kind']})
    if {r['net'] for r in crossings}!={net for port in source['ports'] for net in port['pins'].values()}:
        raise ValueError('stage harness pin map differs from actual crossing nets')
    holes=[]
    for p in lock:
        included=p['block'].startswith('E') or p['block'].startswith('A') and p['key']=='ATTEN'
        if p['kind'] not in source['passage_diameters_mm'] or not included:continue
        holes.append({'uid':p['uid'],'kind':p['kind'],'center_mm':[p['x_mm'],p['y_mm']],
                      'diameter_mm':source['passage_diameters_mm'][p['kind']],
                      'status':'PROPOSAL passage; body seated/tolerance qualification NOT RUN'})
    if Counter(h['kind'] for h in holes)!=Counter({'switch':18,'button':6,'pot':18}):raise ValueError('passage roster mismatch')
    support=source['support'];posts=[{'center_mm':[x,y],'hole_mm':support['hole_mm']} for x in support['x_mm'] for y in support['y_mm']]
    left,top=source['outline'][0];right,bottom=source['outline'][2]
    circles=[(h['center_mm'],h['diameter_mm']/2,h['uid']) for h in holes]
    circles +=[(s['center_mm'],s['hole_mm']/2,'post') for s in posts]
    for i,(p,r,identity) in enumerate(circles):
        if not(left<=p[0]-r and p[0]+r<=right and top<=p[1]-r and p[1]+r<=bottom):raise ValueError('passage outside board '+identity)
        for q,s,other in circles[:i]:
            if math.dist(p,q)<r+s:raise ValueError('intersecting passage/support '+identity+' '+other)
    port_boxes=[]
    for port in source['ports']:
        x,y=port['center_mm'];w,h,z=port['body_clearance_envelope_mm']
        box=[x-w/2,y-h/2,x+w/2,y+h/2]
        if not(left<=box[0]<box[2]<=right and top<=box[1]<box[3]<=bottom):raise ValueError('connector outside board')
        if box[1]<=162:raise ValueError('connector projects into J board edge')
        if box[3]>=178:raise ValueError('connector projects into controls field')
        for post in posts:
            px,py=post['center_mm'];r=support['post_diameter_mm']/2
            near=(max(box[0],min(px,box[2])),max(box[1],min(py,box[3])))
            if math.dist((px,py),near)<r:raise ValueError('rear post intersects connector')
        port_boxes.append({'id':port['id'],'xy_mm':box,'z_mm':[source['face_z_mm']-source['thickness_mm']-z,source['face_z_mm']-source['thickness_mm']]})
    panel_gap=source['panel_rear_z_mm']-(source['face_z_mm']+source['component_height_limit_front_mm'])
    rear_gap=source['face_z_mm']-source['thickness_mm']-source['maximum_nonpassing_pot_body_front_z_mm']
    if panel_gap<0 or rear_gap<0:raise ValueError('negative nominal z clearance')
    occupied=sum(p['courtyard']['area_mm2'] for p in selected if not p['dnp'])
    hole_area=sum(math.pi*r*r for _,r,_ in circles)
    # A deterministic conservative rectangle packing proposal, not a KiCad PCB.
    # Every fixed LED stays at its locked XY. Every package gets one location.
    box_by_fp={p['footprint']:footprint_geometry(ROOT/'footprints/kicad/zudo-osc-hole-field.pretty'/(p['footprint'].split(':')[1]+'.kicad_mod'))['courtyard_bbox_mm'] for p in selected}
    locked={p['uid']:p for p in lock}
    proposal=source['placement_proposal'];gap=proposal['courtyard_clearance_mm']
    obstacles=[(h['center_mm'],h['diameter_mm']/2) for h in holes]
    obstacles +=[(p['center_mm'],proposal['support_head_diameter_mm']/2) for p in posts]
    placements=[];boxes=list(source.get("bulk_reservation_rectangles_mm",[]));fixed_boxes=[]
    # Optional extra keep-clear around fixed emitters so their pads stay routable.
    fixed_gap=proposal.get('fixed_part_clearance_mm',gap)
    def intersects(a,b):return a[0]<b[2]+gap and b[0]<a[2]+gap and a[1]<b[3]+gap and b[1]<a[3]+gap
    def legal(box):
        if not(left+.30<=box[0] and box[2]<=right-.30 and top+.30<=box[1] and box[3]<=bottom-.30):return False
        if any(intersects(box,b) for b in boxes):return False
        if any(a[0]<b[2]+fixed_gap and b[0]<a[2]+fixed_gap and a[1]<b[3]+fixed_gap and b[1]<a[3]+fixed_gap for a in (box,) for b in fixed_boxes):return False
        for (x,y),radius in obstacles:
            # Match the current placer's conservative hole/collar bounding boxes.
            if intersects(box,[x-radius,y-radius,x+radius,y+radius]):return False
        return True
    for part in selected:
        if not part['panel_uid']:continue
        p=locked[part['panel_uid']];b=box_by_fp[part['footprint']]
        box=[b[0]+p['x_mm'],b[1]+p['y_mm'],b[2]+p['x_mm'],b[3]+p['y_mm']]
        if p['rot_deg']!=0 or not legal(box):raise ValueError('fixed stage LED collision '+p['uid'])
        placements.append({'ref':part['ref'],'x_mm':p['x_mm'],'y_mm':p['y_mm'],'rotation_deg':0,'courtyard_mm':box,'fixed':True});boxes.append(box);fixed_boxes.append(box)
    for region in proposal['regions']:
        parts=[p for p in selected if p['instance']==region['instance'] and not p['panel_uid']]
        area={p['ref']:p['courtyard']['area_mm2'] for p in parts}
        nearest=proposal.get('decoupling')=='nearest'
        def order(p):
            # Optionally place each bypass capacitor directly after its own IC.
            owner=p['decouples_ref'] if nearest and p['decouples_ref'] in area else None
            return (-area[owner],owner,1,p['ref']) if owner else (-area[p['ref']],p['ref'],0,p['ref'])
        parts.sort(key=order)
        placed_box={}
        for part in parts:
            original=box_by_fp[part['footprint']];found=None
            target=placed_box.get(part['decouples_ref']) if nearest else None
            best=None
            for angle in (0,90):
                local=original if angle==0 else [-original[3],original[0],-original[1],original[2]]
                w=local[2]-local[0];h=local[3]-local[1]
                x0,y0,x1,y1=region['rect']
                rows=range(round(y0*4),math.floor((y1-h)*4)+1)
                # Bottom-up packing keeps drivers beside the wide lower LED/amplifier gaps.
                if proposal.get('scan_from')=='bottom':rows=reversed(rows)
                for yi in rows:
                    for xi in range(round(x0*4),math.floor((x1-w)*4)+1):
                        x=xi/4;y=yi/4;box=[x,y,x+w,y+h]
                        if not legal(box):continue
                        candidate={'ref':part['ref'],'x_mm':round(x-local[0],6),'y_mm':round(y-local[1],6),'rotation_deg':angle,'courtyard_mm':box,'fixed':False}
                        if target is None:found=candidate;break
                        distance=math.dist(((box[0]+box[2])/2,(box[1]+box[3])/2),((target[0]+target[2])/2,(target[1]+target[3])/2))
                        if best is None or distance<best[0]-1e-9:best=(distance,candidate)
                    if found:break
                if found:break
            if best is not None:found=best[1]
            if not found:raise ValueError('optical proposal OVERFLOW '+part['ref'])
            placements.append(found);boxes.append(found['courtyard_mm']);placed_box[part['ref']]=found['courtyard_mm']
    result={'schema_version':1,'status':'CONDITIONAL CANDIDATE; nominal passage/port checks only; installed fit NOT RUN',
            'source':'design/partition/stage-optical-input.json','source_sha256':hashlib.sha256((ROOT/'design/partition/stage-optical-input.json').read_bytes()).hexdigest(),
            'package_count':len(refs),'component_refs':sorted(refs),'stage_uids':sorted(stage_uids),
            'crossings':crossings,'passages':holes,'support_posts':posts,'connector_clearance_boxes':port_boxes,
            'front_gap_mm':round(panel_gap,6),'rear_requirement_gap_mm':round(rear_gap,6),
            'gross_area_mm2':(right-left)*(bottom-top),'holes_area_mm2':round(hole_area,6),
            'fitted_courtyard_sum_mm2':round(occupied,6),
            'usable_area_mm2':None,'packing_status':'PASS - conservative source rectangle proposal only; actual KiCad PCB, soldering and routing NOT RUN',
            'placement_proposal':placements,
            'checks':{'roster_package_island_local_net':'PASS - source manifest','passage_count':{'switch':18,'button':6,'pot':18},
                      'nominal_passage_support_nonintersection':'PASS','rear_ports_vs_J_edge_and_control_field':'PASS - stated XY envelopes',
                      'tolerance_stack':'OPEN / NOT RUN','support_stiffness':'OPEN / NOT RUN','optical_performance':'NOT RUN',
                      'panel_artwork_and_fasteners':'NOT RUN #37','power_signal_pin_loads':'See current partition power/path bounds; partial-power protection OPEN #59'}}
    # Dimensioned top view of proposed solid passages and fixed emitters.
    k=5;ox=35;oy=55
    def xy(x,y):return ox+(x-left)*k,oy+(y-top)*k
    width=(right-left)*k+70;height=(bottom-top)*k+115
    drawing=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
             '<rect width="100%" height="100%" fill="white"/>',
             '<g font-family="sans-serif" font-size="12" fill="#222">',
             '<text x="25" y="23">Stage optical candidate: 107 × 113 mm; F.Cu z = −4.2 mm</text>',
             '<text x="25" y="41">0.4 mm / 2 layers. PROPOSAL — installed fit and stiffness NOT RUN.</text>',
             f'<rect x="{ox}" y="{oy}" width="{(right-left)*k}" height="{(bottom-top)*k}" fill="#e9f3f2" stroke="#146158"/>']
    for hole in holes:
        x,y=xy(*hole['center_mm']);r=hole['diameter_mm']/2*k
        drawing +=[f'<circle cx="{x}" cy="{y}" r="{r}" fill="white" stroke="#627275"/>']
    for post in posts:
        x,y=xy(*post['center_mm']);drawing +=[f'<circle cx="{x}" cy="{y}" r="{post["hole_mm"]*k/2}" fill="#f5cc81" stroke="#865c14"/>']
    for p in lock:
        if p['uid'] not in stage_uids:continue
        x,y=xy(p['x_mm'],p['y_mm']);drawing +=[f'<circle cx="{x}" cy="{y}" r="3" fill="#ac2180"/>']
    for part in placements:
        if part['fixed']:continue
        b=part['courtyard_mm'];x,y=xy(*b[:2]);drawing +=[f'<rect x="{x}" y="{y}" width="{(b[2]-b[0])*k}" height="{(b[3]-b[1])*k}" fill="#b2cbd3" stroke="#56707a" stroke-width="0.5"/>']
    for box in port_boxes:
        x,y=xy(*box['xy_mm'][:2]);w=(box['xy_mm'][2]-box['xy_mm'][0])*k;h=(box['xy_mm'][3]-box['xy_mm'][1])*k
        drawing +=[f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="none" stroke="#2754a2" stroke-dasharray="4 2"/>']
    drawing +=[f'<text x="25" y="{height-35}">White: 42 passages; gold: 35 posts; magenta: 12 fixed LEDs; grey: courtyard proposal.</text>',
               f'<text x="25" y="{height-17}">Blue: 6 rear GH8 envelopes. No routed PCB or physical fit result.</text>','</g></svg>']
    return dumps(result)+'\n','\n'.join(drawing)+'\n'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    report,svg=build()
    for path,text in [(OUT,report),(SVG,svg)]:
        if args.check:
            if not path.exists() or path.read_text()!=text:raise SystemExit('candidate drift: '+str(path))
        else:path.write_text(text)
    print('PASS: stage candidate nominal passage/port/source checks only; full partition and installed fit NOT RUN')


if __name__=='__main__':main()
