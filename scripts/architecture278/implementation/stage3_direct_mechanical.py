"""Independent cross-board screen of the new direct-study best geometry.

Per-card courtyard feasibility does not include the retained middle population.
No native execution, route generation or geometry adoption is performed.
"""
import argparse
import hashlib
import itertools
import json
from pathlib import Path
import stage3_reservations as reserve

ROOT=reserve.ROOT
OUT=ROOT/'design/architecture-278/implementation/stage3'

def shift(b,x,y=0):return[b[0]+x,b[1]+y,b[2]+x,b[3]+y]

def pair(a,b,scope):return{'a':a['id'],'b':b['id'],'a_box_mm':a['box_mm'],'b_box_mm':b['box_mm'],'scope':scope}

def middle_conflict_class(d,p):
    if not reserve.overlap(d['box_mm'],p['box_mm']):return None
    return 'SAME_FACE_RESERVATION' if d['side']==p['side'] else 'OPPOSITE_FACE_PROJECTION'

def build_variant(variant):
    names=['design/architecture-278/implementation/direct-study-report.json','design/architecture-278/implementation/assembly-report.json','design/architecture-278/implementation/assembly-mechanical-review.json','design/architecture-278/implementation/stage3/reservations-report.json']
    raw={n:(ROOT/n).read_bytes() for n in names};study,assembly,review,reservations=[json.loads(raw[n])for n in names];best=study['best_by_variant'][variant];spec=study['spec'];assert best is not None
    assert (spec['middle_depth_mm'],spec['core_depth_mm'],spec['cover_depth_mm'],spec['withdrawal_mm'],spec['external_workspace_mm'])==(50,69.2,105,40,100)
    shared=[dict(p,id=p['ref'])for p in assembly['shared_middle_placements']]
    middle=[]
    for i in range(5):
        for p in assembly['middle_header_placements']:
            middle.append(dict(p,id=f'O{i+1}:'+p['ref'],box_mm=shift(p['box_mm'],17*i),pads_mm={k:[[x+17*i,y]for x,y in points]for k,points in p['pads_mm'].items()}))
    dinlocal=next(p for p in best['fixtures']if p['id']=='DIN')['box_mm']
    dins=[{'id':inst+':DIN-middle','box_mm':shift(dinlocal,*xy),'instance':inst,'origin_mm':xy,'side':'rear'}for inst,xy in best['origins_mm'].items()]
    same_face=[];opposite=[];through=[]
    for d in dins:
        for p in shared:
            kind=middle_conflict_class(d,p)
            if kind:
                dst=same_face if kind=='SAME_FACE_RESERVATION' else opposite
                dst.append(pair(d,p,'same middle rear-face DIN body reservation versus shared package courtyard' if p['side']=='rear' else 'opposite-face projection; full solids unresolved'))
        for p in middle:
            if reserve.overlap(d['box_mm'],p['box_mm']):opposite.append(pair(d,p,'middle rear DIN versus front GH body projection; through-hole/tail/land details required'))
        # All96 contact points, with exact nominal2.54pitch and selected bank
        # rotation. A point inside GH courtyard is a tail/land exclusion finding,
        # not a claimed exact drill-size or final-solid intersection.
        ox,oy=d['origin_mm'];cx,cy=best['connector_centre_mm'];turn=best['connector_turn_deg']//90
        for row,xoff in zip('abc',(-2.54,0,2.54)):
            for n in range(1,33):
                x,y=xoff,-39.37+(n-1)*2.54
                for _ in range(turn):x,y=-y,x
                xy=[ox+cx+x,oy+cy+y]
                for p in middle:
                    b=p['box_mm']
                    if b[0]<xy[0]<b[2] and b[1]<xy[1]<b[3]:through.append({'DIN':d['id'],'contact':row+str(n),'contact_point_mm':xy,'GH':p['id'],'GH_box_mm':b,'scope':'nominalDINthroughcontactinsideGHcourtyard; exact drill/tail/land exclusion still needed'})
    hardware=review['all_438_hardware_proxies'];projections=[pair(d,h,'newmiddleDIN/hardwareXYprojection only; knownconditionalplanes do not establish complete Z solids')for d in dins for h in hardware if reserve.overlap(d['box_mm'],h['box_mm'])]
    k=reservations['historical_K_board'];queries=[]
    for inst,box in best['geometry']['five_card_boxes_mm'].items():
        for phase,z in [('installed',[69.2,74.2]),('service_cover_removed',[69.2,127.2])]:
            q={'id':inst+':'+phase,'xy_mm':box,'z_mm':z,'phase':phase}
            queries.append(reserve.classify_query(q,reservations['input'],k['xy_rectangles_mm'],k['board_depth_mm']))
    handles=[p for p in best['fixtures']if p['id'].startswith('handle')];grips=[]
    for h in handles:
        b=h['box_mm'];cx,cy=(b[0]+b[2])/2,(b[1]+b[3])/2
        grips.append({'id':h['id']+':20mm-finger','box_mm':[cx-10,cy-10,cx+10,cy+10]})
    grip_hits=[pair(a,b,'inherited20mm simultaneousfinger envelopes overlap; revisedgripprocedure/toolgeometry needed')for a,b in itertools.combinations(grips,2)if reserve.overlap(a['box_mm'],b['box_mm'])]
    hashes={n:hashlib.sha256(b).hexdigest()for n,b in raw.items()}
    for p in [Path(__file__),ROOT/'scripts/architecture278/implementation/stage3_reservations.py']:hashes[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
    return {'variant':variant,'status':'INDEPENDENT CROSS-BOARD SCREEN; NEW BEST GEOMETRY NOT ACCEPTED','source_sha256':hashes,
            'direct_study_claimed_best_mm':best['maximum_mm'],'direct_study_overlength_count':best['overlength_count'],
            'card_mm':spec['card_mm'],'origins_mm':best['origins_mm'],'connector_centre_mm':best['connector_centre_mm'],'connector_turn_deg':best['connector_turn_deg'],
            'same_middle_face_reservation_conflicts':same_face,'opposite_face_DIN_header_projections':opposite,
            'DIN_through_contact_inside_GH_courtyard':through,'new_DIN_all438_hardware_projection_findings':projections,
            'other_function_and_historical_K_checks':queries,'handle_finger_envelope_conflicts':grip_hits,
            'counts':{'same_middle_face':len(same_face),'opposite_middle_face':len(opposite),'through_contact_inside_GH':len(through),'new_DIN_hardware_XY':len(projections),'historicalK_service_intersections':sum(q['historical_K_conflict_if_retained']for q in queries),'handle_finger_pairs_per_card':len(grip_hits),'qualified_free_queries':sum(q['qualified_free']for q in queries)},
            'scope':['Allfive newDINbodyreservations checked against retained30sharedpackages and85middleheaders;438hardware proxies remain bound to fixedcentres.',
                'Same-face reservation intersections reject the proposed source arrangement even though individual44x238cardpacking passed; exactnative/physicalsolids remain unavailable.',
                'Opposite-face projections and nominalDINcontactpoints are separate source-exclusion findings, not fabricated exact drill/body measurements.',
                'Other28candidateoccupiedvolumes remain UNKNOWN; retainedK scenario is separately explicit, not automatically adopted.',
                'Inherited20mmgrip envelope is a conservative service assumption; overlapping simultaneousgrips require a revised tool/procedure, not a claim that no possible service solution exists.',
                'No nativeKiCad/ERC/DRC, physicalclearance, stiffness, energizedservice or hardware acceptance.']}

def build():
    return {'status':'INDEPENDENT BOTH-VARIANT CROSS-BOARD SCREEN; NOT ACCEPTED',
            'variants':{variant:build_variant(variant) for variant in ('baseline','bypass_refined')}}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args();r=build();data=json.dumps(r,indent=2,sort_keys=True)+'\n';p=OUT/'direct-mechanical-report.json'
    if args.check:assert p.read_text()==data,'stale direct mechanical review'
    else:p.write_text(data)
    print(json.dumps({k:v['counts']for k,v in r['variants'].items()},sort_keys=True));print('NEW BEST NOT ACCEPTED; native/physicalNOTRUN')
if __name__=='__main__':main()
