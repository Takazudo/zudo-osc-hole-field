#!/usr/bin/env python3
"""Bounded source geometry audit; no native calls, placement/copper adoption or fit claim."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[3]
INPUTS=['design/partition/core-split/candidates/two.json','design/partition/core-split/power/input.json','design/partition/core-split/power/contract.json','design/partition/core-split/decision.json','design/partition/partition-input.json','design/partition/partition.json','design/partition/core-split/mechanical/generated/comparison.json','boards/osc-core/osc-core.kicad_pcb']

def read(p):return json.loads((ROOT/p).read_text())
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def box(poly):
    points=[p for ring in poly for p in ring]
    if len(poly)!=1 or len({p[0] for p in points})!=2 or len({p[1] for p in points})!=2:
        raise ValueError('nonrectangular source courtyard requires polygon screen')
    return [min(p[0] for p in points),min(p[1] for p in points),max(p[0] for p in points),max(p[1] for p in points)]
def nm(q):return [round(v*1000000) for v in q]
def gap2(a,b):
    dx=max(0,a[0]-b[2],b[0]-a[2]);dy=max(0,a[1]-b[3],b[1]-a[3])
    return dx*dx+dy*dy
def overlap(a,b):return min(a[2],b[2])>max(a[0],b[0]) and min(a[3],b[3])>max(a[1],b[1])
def inside(q):return q[0]>=4.3 and q[1]>=8.3 and q[2]<=313.7 and q[3]<=291.7 and not(q[2]>257.7 and q[3]>245.7)

def gap_corrections(candidate):
    rows=[]
    for board in candidate['boards'].values():
        parts={p['ref']:p for p in board['placements']}
        boxes={r:nm(box(p['courtyard_polygons_mm'])) for r,p in parts.items()}
        changes={}
        for face,metrics in board['measurement']['faces'].items():
            for v in metrics['courtyard_gap_violations']:
                moving,fixed=v['refs'];a,b=boxes[moving],boxes[fixed]
                if not moving.startswith('C'):raise ValueError('review non-capacitor correction')
                # 1 micrometre proposal, 1000 times the 1 nm deficit; no tolerance relaxation.
                dx=1000 if a[0]>=b[2] else -1000 if a[2]<=b[0] else 0
                dy=1000 if a[1]>=b[3] else -1000 if a[3]<=b[1] else 0
                if bool(dx)==bool(dy):raise ValueError('expected one-axis strict gap')
                shifted=[a[0]+dx,a[1]+dy,a[2]+dx,a[3]+dy]
                changes[moving]=shifted
                rows.append({'board':board['id'],'side':face,'moving_ref':moving,'fixed_ref':fixed,
                    'source_boxes_mm':[[x/1e6 for x in a],[x/1e6 for x in b]],
                    'before_gap_mm':math.sqrt(gap2(a,b))/1e6,'delta_xy_mm':[dx/1e6,dy/1e6],
                    'after_gap_mm':math.sqrt(gap2(shifted,b))/1e6,
                    'proposed_origin_mm':[round(parts[moving]['x_mm']+dx/1e6,6),round(parts[moving]['y_mm']+dy/1e6,6)],
                    'affected_pad_identities':parts[moving]['pad_identity'],
                    'adoption':'NOT APPLIED; assigned placement owner must preserve/replay connected copper and recheck native identity/groups'})
        corrected=boxes|changes
        for row in rows:
            if row['board']!=board['id']:continue
            ref=row['moving_ref'];q=corrected[ref]
            neighbors=[(gap2(q,other),r) for r,other in corrected.items() if r!=ref and parts[r]['side']==row['side']]
            d,r=min(neighbors)
            row['minimum_same_face_gap_after_mm']=math.sqrt(d)/1e6
            row['nearest_ref_after']=r
            row['new_strict_conflicts']=[r for d,r in neighbors if d<350000**2]
            row['outline_pass']=inside([x/1e6 for x in q])
    return rows

def obstacles(board,mechanical,source,partition):
    rows=[(p['ref'],box(p['courtyard_polygons_mm'])) for p in board['placements'] if p['side']=='F.Cu']
    # Pad/land footprints occur in placements. Separate support/tool/loom and KA-only reserve masks.
    rows += [('support', [x-1.6,y-1.6,x+1.6,y+1.6]) for x,y in board['supports_mm']]
    rows += [(a['header_id']+'-tool',a['box_mm']) for a in partition['K_service_apertures']]
    key=board['provisional_board_key']
    rows += [(p['id']+'-loom',p['box_mm']) for p in mechanical['through_loom_passages'] if p['board']==key]
    if key=='KA':rows += [('protection',[180,220,256,290])]
    return [(r,[q[0]-.35,q[1]-.35,q[2]+.35,q[3]+.35]) for r,q in rows]

def continuous_origins(w,h,rows):
    """Complete axis-aligned translation screen for rectangular obstacle model.

    Feasibility changes only at obstacle/domain x events. For each event, merge
    forbidden open y intervals; touching expanded boxes preserves the 0.35 gap.
    """
    found=[];tested=0
    for xmin,xmax,ymin,ymax in [(4.3,313.7-w,8.3,245.7-h),(4.3,257.7-w,8.3,291.7-h)]:
        if xmax<xmin or ymax<ymin:continue
        events=sorted({xmin,xmax}|{v for _,q in rows for v in (q[0]-w,q[2]) if xmin<=v<=xmax})
        for x in events:
            tested+=1;y=ymin
            intervals=sorted((q[1]-h,q[3]) for _,q in rows if x<q[2] and x+w>q[0])
            for lo,hi in intervals:
                if y<=lo:break
                if y<hi:y=hi
            if y<=ymax:
                q=[x,y,x+w,y+h]
                if any(overlap(q,o) for _,o in rows):raise ValueError('event sweep contradiction')
                found.append([round(x,6),round(y,6)])
    return {'event_count':tested,'feasible_event_origins_mm':found,
            'scope':'Complete continuous translation for this cardinal rectangular envelope and inflated axis-aligned obstacle model only; no copper/3D proof.'}


def row_search(board,obstacle_rows):
    # Conservative 1 mm occupancy grid. Zero occupancy is rechecked against exact rectangles.
    n=322;m=302;grid=[[0]*n for _ in range(m)]
    for _,q in obstacle_rows:
        for y in range(max(0,math.floor(q[1])),min(m,math.ceil(q[3]))):
            for x in range(max(0,math.floor(q[0])),min(n,math.ceil(q[2]))):grid[y][x]=1
    sums=[[0]*(n+1) for _ in range(m+1)]
    for y in range(m):
        accum=0
        for x in range(n):accum+=grid[y][x];sums[y+1][x+1]=sums[y][x+1]+accum
    output=[]
    for rotation,w,h in [(0,91,34),(90,34,91)]:
        best=None;zeros=[];tested=0
        for y in range(9,292-h):
            for x in range(5,314-w):
                q=[x,y,x+w,y+h]
                if not inside(q):continue
                tested+=1
                area=sums[y+h][x+w]-sums[y][x+w]-sums[y+h][x]+sums[y][x]
                score=(area,y,x)
                if best is None or score<best[0]:best=(score,q)
                if area==0:zeros.append(q)
        q=best[1]
        output.append({'rotation_deg':rotation,'searched_origins':tested,'grid_step_mm':1,
            'zero_obstacle_candidates':zeros,'continuous_translation_screen':continuous_origins(w,h,obstacle_rows),'best_box_mm':q,'occupied_grid_area_mm2':best[0][0],
            'best_conflicting_refs_or_reservations':[r for r,o in obstacle_rows if overlap(q,o)],
            'best_exact_overlaps':[{'id':r,'inflated_obstacle_mm':o,'overlap_area_mm2':round((min(q[2],o[2])-max(q[0],o[0]))*(min(q[3],o[3])-max(q[1],o[1])),6)} for r,o in obstacle_rows if overlap(q,o)],
            'scope':'Whole 91x34 row+corridor projection; conservative actual courtyard rectangles plus 0.35 gap. Grid failure is not continuous impossibility; exact-zero candidates still need copper/3D/service checks.'})
    return output

def build():
    candidate=read(INPUTS[0]);power=read(INPUTS[1]);source=read(INPUTS[4]);partition=read(INPUTS[5]);comparison=read(INPUTS[6])
    if power['new_feed']['wire_service_corridor_height_mm']!=28:raise ValueError('power envelope changed')
    mech=next(a for a in comparison['alternatives'] if a['id']=='two-deep')
    gaps=gap_corrections(candidate)
    searches={b:row_search(board,obstacles(board,mech,source,partition)) for b,board in candidate['boards'].items()}
    # Continuous cardinal-oriented escape: enumerate all maximal boundary-coordinate rectangles.
    enclosure=source['enclosure']['internal_xy_mm'];xs=[enclosure[0],4,258,314,enclosure[2]];ys=[enclosure[1],8,246,292,enclosure[3]]
    board_rects=[[4,8,314,246],[4,246,258,292]]
    empty=[]
    for i,x0 in enumerate(xs):
        for x1 in xs[i+1:]:
            for j,y0 in enumerate(ys):
                for y1 in ys[j+1:]:
                    q=[x0,y0,x1,y1]
                    if not any(overlap(q,b) for b in board_rects):empty.append(q)
    fitting=[q for q in empty if (q[2]-q[0]>=91 and q[3]-q[1]>=28) or(q[2]-q[0]>=28 and q[3]-q[1]>=91)]
    return {'input_sha':'9e0aceda2f1d55052a8c9c03f958e8d93271a81c','status':'SOURCE GEOMETRY BLOCKER; architecture NOT SELECTED; retain accepted K1402',
        'source_sha256':{p:digest(ROOT/p) for p in INPUTS},'tool_sha256':digest(Path(__file__)),
        'strict_gap_proposals':gaps,'strict_gap_summary':{'count':len(gaps),'remaining_after_local_proposal':sum(bool(r['new_strict_conflicts']) for r in gaps),'canonical_edits':0},
        'cardinal_edge_escape':{'enclosure_xy_mm':enclosure,'empty_boundary_rectangles_mm':empty,'fitting_91x28_rectangles_mm':fitting,
            'status':'BLOCKED for cardinal row/corridor orientations inside retained XY and identical uncut KA/KB outlines; arbitrary-angle/changed-envelope alternatives NOT CHECKED. EXT, walls/supports only reduce available space.'},
        'stack_options':{'unchanged':{'pitch_mm':26,'bare_gap_mm':24.4,'corridor_deficit_mm':3.6,'including_opposing_5mm_allowance_deficit_mm':8.6},
            'bare_only':{'required_pitch_mm':29.6,'status':'Insufficient against 5 mm opposing body allowance'},
            'body_allowance_clear':{'required_pitch_mm':34.6,'KA_front_z_mm':-100,'KB_front_z_mm':-134.6,'required_inside_depth_mm':154.6,'increase_vs_two_deep_mm':8.6,'contact_margin_mm':0,'status':'Z-only mathematical boundary; no manufacturing margin or accepted case; XY/copper/service unresolved'}},
        'endpoint_placement_search':searches,
        'service_wire_boundary':{'maximum_cut_mm':110,'bend_radius_mm':source['load_distribution']['minimum_bend_radius_mm'],'max_OD_mm':source['load_distribution']['diameter_max_mm'],'qualified_loop_length_mm':None,'status':'No complete endpoint pair/route, extraction stroke or strain-relief geometry accepted; 110 cannot be represented as available service slack.'},
        'remaining':['Uncut retained outline plus 26 pitch excludes cardinal edge escape for unchanged 91x28x28 corridor.','Aperture would remove accepted board material/copper and needs precise owner/native review; no aperture adopted.','Continuous event sweep closes cardinal translation under the stated rectangular masks; arbitrary tilts, altered tool obligations and redesigned power corridors remain untested.','All 40 strict-gap corrections are proposed only, with pad identities for replay; no accepted copper moved.','No native, opposing-body exact solids, installed access, manufacturing margin, physical fit or architecture selection.']}

def svg(report):
    candidate=read(INPUTS[0]);out=['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1080 640">', '<rect width="1080" height="640" fill="white"/>', '<style>text{font:14px sans-serif} .small{font-size:11px}</style>', '<text x="20" y="25">Two-core feed screen — BLOCKED source proposal, no physical fit or copper adoption</text>']
    for i,(name,b) in enumerate(candidate['boards'].items()):
        ox=20+i*535;oy=70;scale=1.5
        def rectangle(q,fill,opacity=1):
            return f'<rect x="{ox+q[0]*scale}" y="{oy+q[1]*scale}" width="{(q[2]-q[0])*scale}" height="{(q[3]-q[1])*scale}" fill="{fill}" opacity="{opacity}"/>'
        out.append(f'<text x="{ox}" y="55">{name} F-side projected source courtyards</text>')
        out.append(f'<polygon points="'+ ' '.join(f'{ox+x*scale},{oy+y*scale}' for x,y in b['outline_mm'])+'" fill="#edf5f0" stroke="#28735c"/>')
        for part in b['placements']:
            if part['side']=='F.Cu':out.append(rectangle(box(part['courtyard_polygons_mm']),'#7b8b99',.55))
        row=report['endpoint_placement_search'][name][0]
        q=row['best_box_mm'] if name=='two-A' else [8.45,134.52,99.45,168.52]
        out.append(rectangle(q,'#efb159',.45));out.append(rectangle([q[0],q[1],q[2],q[1]+6],'#3482a6',.75))
        for conflict in row['best_exact_overlaps'] if name=='two-A' else []:out.append(rectangle(conflict['inflated_obstacle_mm'],'#d33',.8))
        out.append(f'<text x="{ox}" y="535">91 × 6 terminal row + 91 × 28 corridor projection</text>')
        out.append(f'<text x="{ox}" y="557" class="small">Origin {q[0]:g}, {q[1]:g} mm; orientation 0°; examples are NOT a wired pair</text>')
        out.append(f'<text x="{ox}" y="579" class="small">'+('KA: best 1 mm grid attempt hits JR-K-2/3/4 tool reserves' if name=='two-A' else 'KB: source XY opening only; at 26 pitch corridor still hits KA plane')+'</text>')
    out.append('<text x="20" y="615">Pitch: 26 current / 29.6 bare boundary / 34.6 with 5 mm opposing body allowance; zero margin, no adoption.</text></svg>')
    return '\n'.join(out)+'\n'


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    report=build();outputs={'two-core-feasibility.json':json.dumps(report,sort_keys=True,indent=2)+'\n','two-core-feasibility.svg':svg(report)}
    for name,content in outputs.items():
        out=HERE/'generated'/name
        if args.check:
            if not out.exists() or out.read_text()!=content:raise SystemExit('DRIFT '+name)
        else:out.write_text(content)
    print('PASS source feasibility artifacts; no native/physical acceptance')
if __name__=='__main__':main()
