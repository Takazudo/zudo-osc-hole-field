"""Independent assembly geometry screen; no native/aggregate execution or source edits.

Projected overlap is not a physical collision verdict without installed Z solids.
"""
import argparse
from collections import Counter
import hashlib
import itertools
import json
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT/'scripts/architecture278'))
from populated_mechanics import courtyard, sexpr, field
OUT=ROOT/'design/architecture-278/implementation'

def intersects(a,b):return a[0]<b[2]-1e-9 and b[0]<a[2]-1e-9 and a[1]<b[3]-1e-9 and b[1]<a[3]-1e-9

def shift(b,dx,dy=0):return[b[0]+dx,b[1]+dy,b[2]+dx,b[3]+dy]

def rotated(b,x,y,degrees):
    points=list(itertools.product((b[0],b[2]),(b[1],b[3])))
    for _ in range((degrees//90)%4):points=[(-yy,xx) for xx,yy in points]
    return[min(xx for xx,yy in points)+x,min(yy for xx,yy in points)+y,max(xx for xx,yy in points)+x,max(yy for xx,yy in points)+y]

def pair(a,b,scope):return {'a':a['id'],'b':b['id'],'a_box_mm':a['box_mm'],'b_box_mm':b['box_mm'],'scope':scope}

def build():
    paths=[OUT/'assembly-report.json',OUT/'compact-rear.json',OUT/'candidate-report.json',ROOT/'design/grid/placements.lock.json',Path(__file__),ROOT/'scripts/architecture278/implementation/assembly.py',ROOT/'scripts/architecture278/populated_mechanics.py']
    r=json.loads(paths[0].read_text());rear=json.loads(paths[1].read_text());baseline=json.loads(paths[2].read_text());lock=json.loads(paths[3].read_text())['placements']
    locked={p['uid']:p for p in lock};links={h['id']:h for h in baseline['front_links']}
    footprint_names={'jack':'Jack_3.5mm_QingPu_WQP518MA','pot':'PTV09A-4020F','switch':'Toggle_Dailywell_2MS_T1B1M2','button':'Button_Omron_B3F_6x6_P6.5x4.5','octave':'SRBV160803'}
    hardware=[]
    for p in lock:
        name=('LED0402-Kingbright-Red' if p['led_type']=='clip' else 'LED0402-Kingbright-White') if p['kind']=='led' else footprint_names[p['kind']]
        path=ROOT/f'footprints/kicad/zudo-osc-hole-field.pretty/{name}.kicad_mod';paths.append(path)
        box=rotated(courtyard(str(path.relative_to(ROOT))),p['x_mm'],p['y_mm'],p['rot_deg'])
        holes=[]
        for node in sexpr(path.read_text()):
            if isinstance(node,list) and node[0]=='pad' and node[2] in ('thru_hole','np_thru_hole'):
                xx,yy=map(float,field(node,'at')[:2]);w,h=map(float,field(node,'size')[:2])
                holes.append(rotated([xx-w/2,yy-h/2,xx+w/2,yy+h/2],p['x_mm'],p['y_mm'],p['rot_deg']))
        hardware.append({'through_pad_keepouts_mm':holes,'id':p['uid'],'kind':p['kind'],'box_mm':box,'source':str(path.relative_to(ROOT)),
                         'conditional_pcb_depth_mm':-p['assembly_pcb_z_mm'] if 'assembly_pcb_z_mm' in p else None,
                         'scope':'footprint proxy at locked datum; installed solid/depth not established'})
    front=[];middle=[];panel_mismatches=[]
    for i in range(1,6):
        inst=f'O{i}';dx=17*(i-1)
        actual_instances=r.get('front_instances',{})
        placed=actual_instances.get(inst,r['front_placements'])
        delta=0 if inst in actual_instances else dx
        for p in placed:
            q=dict(p,id=inst+':'+p['ref'],box_mm=shift(p['box_mm'],delta),instance=inst)
            q['through_pad_keepouts_mm']=[shift(b,delta) for b in p['through_pad_keepouts_mm']]
            if p.get('uid'):
                uid=p['uid'].replace('O1',inst);q['uid']=uid;datum=locked[uid]
                if [p['origin_mm'][0]+delta,p['origin_mm'][1]]!=[datum['x_mm'],datum['y_mm']] or p['quarter_turn']*90!=datum['rot_deg']:panel_mismatches.append(q['id'])
                q['plane_mm']=-datum.get('assembly_pcb_z_mm',-r['config']['front_depth_mm'])
            elif p['board']=='selector':q['plane_mm']=-locked[f'C:{inst}.OCT']['assembly_pcb_z_mm']
            else:q['plane_mm']=r['config']['front_depth_mm']
            front.append(q)
        for p in r['middle_header_placements']:
            middle.append(dict(p,id=inst+':'+p['ref'],box_mm=shift(p['box_mm'],dx),instance=inst))
    definite=[]
    for a,b in itertools.combinations(front,2):
        if a['side']==b['side'] and a['plane_mm']==b['plane_mm'] and intersects(a['box_mm'],b['box_mm']):definite.append(pair(a,b,'same candidate front PCB plane/face courtyard overlap'))
    for a,b in itertools.combinations(middle,2):
        if a['side']==b['side'] and intersects(a['box_mm'],b['box_mm']):definite.append(pair(a,b,'same middle PCB plane/face header courtyard overlap'))
    # Through pads occupy both PCB faces on the same plane, including neighbors.
    through=[]
    for p in front:
        if p.get('uid'):continue
        for h in hardware:
            # Ordinary panel PCB depths remain conditional; use the same20mm
            # assumption as the candidate and preserve selector16/29mm datums.
            plane=h['conditional_pcb_depth_mm'] or r['config']['front_depth_mm']
            if p['plane_mm']!=plane:continue
            for b in h['through_pad_keepouts_mm']:
                if intersects(p['box_mm'],b):through.append({'placement':p['id'],'through_pad_owner':h['id'],'placement_box_mm':p['box_mm'],'pad_box_mm':b,'scope':'same conditional PCB depth; exact installed datum remains OPEN'})
    shared=[dict(p,id=p['ref']) for p in r['shared_middle_placements']]
    middle_shared=[pair(a,b,'opposite or unspecified middle faces; inspect actual installed heights and through-vias') for a in middle for b in shared if intersects(a['box_mm'],b['box_mm'])]
    din={};card_checks={}
    for name,a in r['alternatives'].items():
        din[name]=[]
        width,height=baseline['config']['tile_mm'] if name=='retained_150_recomputed' else rear['tile_mm']
        cards={n:{'id':n,'box_mm':[xy[0],xy[1],xy[0]+width,xy[1]+height]} for n,xy in a['origins_mm'].items()}
        for n,b in rear['mechanical']['other_reservations_mm'].items():
            if n not in cards:cards[n]={'id':n+':retained_reservation','box_mm':b}
        collisions=[pair(aa,bb,'candidate card versus retained full-five rear reservation') for aa,bb in itertools.combinations(cards.values(),2) if intersects(aa['box_mm'],bb['box_mm'])]
        card_checks[name]={'cards':cards,'overlaps':collisions,'scope':'Retained unpopulated reservations added where alternative contains onlyO1/O2; not an assertion of full replication.'}
        for inst,(x,y) in a['origins_mm'].items():
            connector=baseline['config']['connector'] if name=='retained_150_recomputed' else rear['connector']
            d={'id':inst+':DIN','box_mm':shift(connector['body_reservation_mm'],x,y)}
            for p in middle+shared:
                if intersects(d['box_mm'],p['box_mm']):din[name].append(pair(d,p,'DIN body reservation projection; opposite-face body may clear but actual THT pads/tails require checking'))
    # This list is intentionally not called collisions: many different Z planes
    # have common XY projection. It makes omitted occupied hardware auditable.
    projected=[]
    for p in front:
        if p.get('uid'):continue
        for h in hardware:
            if intersects(p['box_mm'],h['box_mm']):projected.append(pair(p,h,'projected hardware overlap only; reconcile per-part installed solid and Z interval'))
    for p in middle+shared:
        for h in hardware:
            if intersects(p['box_mm'],h['box_mm']):projected.append(pair(p,h,'middle/front projected hardware overlap only; reconcile per-part installed solid and Z interval'))
    sources={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(paths))}
    return {'status':'INDEPENDENT GEOMETRY SCREEN; physical fit NOT ACCEPTED','source_sha256':sources,
            'locked_hardware_count':len(hardware),'locked_hardware_by_kind':dict(Counter(p['kind'] for p in hardware)),
            'all_438_hardware_proxies':hardware,'fixed_panel_transform_mismatches':panel_mismatches,
            'same_plane_face_courtyard_conflicts':definite,'same_plane_through_pad_conflicts':through,
            'alternative_full_five_card_checks':card_checks,'middle_shared_projection_findings':middle_shared,'DIN_middle_projection_findings':din,
            'all_hardware_projection_findings':projected,
            'counts':{'same_plane_face':len(definite),'through_pad':len(through),'middle_shared_projection':len(middle_shared),'DIN_projection_by_alternative':{k:len(v) for k,v in din.items()},'all_hardware_projection':len(projected),'card_overlap_by_alternative':{k:len(v['overlaps']) for k,v in card_checks.items()}},
            'limits':['Actual front_instances consumed when present; otherwise O1 copy comparison only. Locked datum/rotation equality checked; selector PCB depth16/29mm retained.',
                      'No exact installed Z body/lead/tail/plug/latch/optical/screw/tool solid exists for every438hardware item. Footprint proxies are not full occupied volumes.',
                      'Panel-side versus rear-side SMT placement and reflection must be reconciled with eventual native footprint pad/face transforms.',
                      'Middle DIN female/male footprint drill/tail rows, flange fixings and connector keying are not substituted by body reservations.',
                      'Middle shared-reference rear face may project below rear card; actual component heights/supports/straps/extraction remain unqualified.',
                      'Carrier/supportPCB outlines, holes, barriers, cable bend/strainrelief and power/source infrastructure remain absent.',
                      'NativeKiCad10.0.6/ERC/DRC/physicalNOTRUN; no exact-run admission.']}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args();r=build()
    data=json.dumps(r,indent=2,sort_keys=True)+'\n';out=OUT/'assembly-mechanical-review.json'
    if args.check:assert out.read_text()==data,'stale independent mechanical review'
    else:out.write_text(data)
    print(json.dumps(r['counts'],sort_keys=True));print('438hardware footprint proxies covered; physical/native NOT RUN')
if __name__=='__main__':main()
