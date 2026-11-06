"""Source-only reservation audit. Unknown instrument volumes never become free.

Reads canonical sources without changing them; no KiCad, network or campaign.
"""
import argparse
from collections import Counter,defaultdict
import hashlib
import itertools
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'design/architecture-278/implementation/stage3'

def overlap(a,b):return a[0]<b[2] and b[0]<a[2] and a[1]<b[3] and b[1]<a[3]

def intersection(a,b):
    if not overlap(a,b):return None
    return[max(a[0],b[0]),max(a[1],b[1]),min(a[2],b[2]),min(a[3],b[3])]

def area(b):return (b[2]-b[0])*(b[3]-b[1])

def polygon_rectangles(points):
    """Exact decomposition of the committed orthogonal board outline."""
    ys=sorted({y for x,y in points});rects=[]
    for y0,y1 in zip(ys,ys[1:]):
        mid=(y0+y1)/2;xs=[]
        for (x,y),(xx,yy) in zip(points,points[1:]+points[:1]):
            if x==xx and min(y,yy)<mid<max(y,yy):xs.append(x)
        xs.sort();assert len(xs)%2==0
        rects += [[x0,y0,x1,y1] for x0,x1 in zip(xs[::2],xs[1::2])]
    return rects

def classify_query(q,config,k_rects,k_z):
    b=q['xy_mm'];z=q['z_mm'];panel=config['panel_projection_mm']
    assert len(b)==4 and b[0]<b[2] and b[1]<b[3]
    assert len(z)==2 and 0<=z[0]<z[1]
    inside=panel[0]<=b[0] and panel[1]<=b[1] and b[2]<=panel[2] and b[3]<=panel[3]
    limit=config['depths_mm']['cover']+(config['depths_mm']['external_workspace'] if q.get('phase')=='service_cover_removed' else 0)
    if not inside or z[1]>limit:status='OUTSIDE_CURRENT_ENVELOPE: revised geometry or a declared cover-removed service phase needed'
    else:status='UNKNOWN: other-function candidate volumes not assigned'
    hits=[intersection(b,r) for r in k_rects] if z[0]<k_z[1] and k_z[0]<z[1] else []
    hits=[x for x in hits if x]
    return dict(q,space_status=status,qualified_free=False,
                historical_retained_K_board_intersections_mm=hits,
                historical_K_conflict_if_retained=bool(hits),
                scope='Historical K overlap is conditional on retaining that board; never silently adopt/move/delete it to clear candidate space.')

def validate_input(config):
    assert config['qualified_free_regions']==[], 'No free-space certificate is supported by these sources'
    assert config['depths_mm']=={'middle':50,'core':69.2,'cover':105,'rear_package_allowance':5,'handle_projection':18,'withdrawal':40,'external_workspace':100}, 'baseline depth/service changed'

def build():
    source_names=['design/architecture-278/implementation/stage3/reservations-input.json','design/architecture-278/source-ledger.json','design/partition/floorplan-candidate.json','design/partition/mechanical-candidate.json','design/boards/osc-core.json','design/mechanical/core-rear-allowance.json','design/architecture-278/implementation/assembly-report.json','design/architecture-278/implementation/assembly-mechanical-review.json','design/architecture-278/interface-contract.json','design/architecture-278/implementation/compact-rear.json']
    raw={n:(ROOT/n).read_bytes() for n in source_names};v={n:json.loads(data) for n,data in raw.items()}
    config=v[source_names[0]];ledger=v[source_names[1]];floor=v[source_names[2]];mech=v[source_names[3]];board=v[source_names[4]];rear_allowance=v[source_names[5]];assembly=v[source_names[6]];review=v[source_names[7]];contract=v[source_names[8]];compact=v[source_names[9]]
    validate_input(config)
    mods={f['id']:f for f in ledger['functions'] if f['family']!='OSC'};assert len(mods)==28
    packages={p['ref']:p for p in ledger['packages']};placements={p['ref']:p for p in floor['placements']}
    rows=[]
    for name,f in mods.items():
        pp=[p for p in packages.values() if p['instance']==name];kp=[placements[p['ref']] for p in pp if p['current_board']=='K']
        envelopes={}
        for side in sorted({p['side'] for p in kp}):
            bb=[p['courtyard_mm'] for p in kp if p['side']==side]
            envelopes[side]=[min(b[0] for b in bb),min(b[1] for b in bb),max(b[2] for b in bb),max(b[3] for b in bb)]
        rows.append({'function':name,'family':f['family'],'retained_package_count':len(pp),'retained_board_counts':dict(Counter(p['current_board'] for p in pp)),
                     'retained_K_package_count':len(kp),'retained_K_refs':[p['ref'] for p in kp],
                     'historical_K_courtyard_envelopes_mm':envelopes,
                     'new_stack_occupied_volume':None,'new_stack_status':'UNKNOWN' if kp else 'NO_SOURCE_K_PACKAGES; front/carrier/harness volumes still require reconciliation',
                     'scope':'Historical projected source placement, not installed solids or a transferred candidate reservation'})
    k=[p for p in floor['placements'] if p['board']=='K'];krect=polygon_rectangles(board['outline']);kz=[-mech['K_rear']['face_z_mm'],-mech['K_rear']['back_face_z_mm']]
    kmax=kz[1]+rear_allowance['component_height_ceiling_mm']
    hw={p['id']:p for p in review['all_438_hardware_proxies']}
    projection_counts=dict(Counter(hw[p['b']]['kind'] for p in review['all_hardware_projection_findings']))
    # Derive supply-pin distances rather than reusing package-origin proximity.
    endpoints=defaultdict(list)
    for e in assembly['endpoint_inventory']:
        if e['physical']:
            for xy in e['xy_mm']:endpoints[e['ref']].append(dict(e,xy=xy))
    locality=[]
    for a in assembly['bypass_associations']:
        if a['owner']!='rear-core':continue
        cap=a['capacitor'];ic=a['package']
        pairs=[(math.dist(p['xy'],q['xy']),p,q) for p in endpoints[cap] for q in endpoints[ic] if p['net']==q['net'] and p['net']!='AGND']
        if not pairs:continue
        d,p,q=min(pairs,key=lambda x:x[0])
        locality.append({'capacitor':cap,'target_package':ic,'rail_net':p['net'],'capacitor_pin':p['pin'],'target_pin':q['pin'],'capacitor_pad_mm':p['xy'],'target_pad_mm':q['xy'],'direct_pad_distance_mm':d,
                         'refinement':'Move whole capacitor next to its exact supply pad while retaining source cluster, all package units, six trim/tool reservations and short return to the same local plane. Do not treat the straight-line distance as a routed loop.',
                         'return_loop_status':'OPEN: ground vias/plane spreading/shared impedance not extracted'})
    sensitive=[]
    tokens=('TIMING_CAP','EXPO_SUM','SCALE_PIN','HF_PIN','LINEAR_REF','SINE_GAIN_SUM','VEE5')
    for net in sorted({e['net'] for e in assembly['endpoint_inventory'] if e['net'] and any(x in e['net'] for x in tokens)}):
        ee=[e for values in endpoints.values() for e in values if e['net']==net and e['owner']=='rear-core']
        pairs=[(math.dist(a['xy'],b['xy']),a,b) for a,b in itertools.combinations(ee,2)]
        if pairs:
            d,a,b=max(pairs,key=lambda x:x[0]);sensitive.append({'net':net,'endpoint_count':len(ee),'largest_direct_span_mm':d,'extreme_endpoints':[a['ref']+':'+a['pin'],b['ref']+':'+b['pin']], 'refinement':'Place actual local timing/summing/feedback endpoints around the relevant IC pins, not around harness entry. Preserve entire source package and local bypass; no remote feedback.'})
    # Package boxes are actually known in a source snapshot; no exact new Z
    # distribution for the non-OSC population is available in that snapshot.
    hashes={n:hashlib.sha256(data).hexdigest() for n,data in raw.items()};hashes[str(Path(__file__).relative_to(ROOT))]=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    return {'status':'RESERVATION SOURCE AUDIT; WHOLE-INSTRUMENT SPACE QUALIFICATION BLOCKED','source_sha256':hashes,'input':config,
            'knowledge_classes':{'known_source':'Fixed438centres,33functions,retainedpackage/board assignments and footprint XY are source declarations, not measured solids.',
                'conditional':'Candidate50/69.2/105mm stack,5mm package procurement allowance,existing fixture boxes and depth comparisons.',
                'unknown':'Other28 new-stack package/carrier/harness/service solids and unresolved installed hardware Z; no zero-area substitution.',
                'qualified_free':'None identified; lack of modeled objects does not certify empty space.'},
            'other_functions':rows,'other_function_count':len(rows),'other_K_function_count':sum(r['retained_K_package_count']>0 for r in rows),
            'other_K_package_count':sum(r['retained_K_package_count'] for r in rows),'all_K_package_count':len(k),
            'K_package_instance_counts':dict(Counter(packages[p['ref']]['instance'] for p in k)),
            'historical_K_board':{'xy_polygon_mm':board['outline'],'xy_rectangles_mm':krect,'board_depth_mm':kz,'conditional_rear_extent_mm':kmax,'candidate_cover_mm':105,'conditional_excess_mm':kmax-105,'keepouts':board['keepouts'],'scope':'Oldstack comparison only; sourceproposal100mmK/120mmcase is not candidate50/69.2/105mapping'},
            'depth_projection_review':{'unresolved_hardware_pairs':len(review['all_hardware_projection_findings']),'by_hardware_kind':projection_counts,'middle_opposite_face_pairs':review['middle_shared_projection_findings'],
                'known_conditional_selector_intervals_mm':{'O1/O3/O5':[8.5,20],'O2/O4':[21.5,33]},
                'missing_evidence':'Each pair needs occupied body/lead/latch/cable/tool geometry in a common PCB-face datum, tolerances, and sourced or explicitly provisional height bounds. Opposite PCB face alone does not qualify through-tail/connector/optical clearance.'},
            'geometry_queries':[classify_query(q,config,krect,kz) for q in config['evaluation_queries']],
            'rear_bypass_actual_pad_ranking':sorted(locality,key=lambda x:-x['direct_pad_distance_mm']),
            'sensitive_local_net_spans':sorted(sensitive,key=lambda x:-x['largest_direct_span_mm']),
            'next_bounded_source_work':['Join all28 retained function/package/units/NC/bypass assignments to candidate boards and exactnew-stackreservations, keeping13POWER/sharedservices independently accounted.',
                'Propose whole-package placements/carriers/through-board volumes and disjoint extraction/trim/probe corridors before classifying any region as free; samepanelXY may be reused only with explicitnonintersectingZ envelopes.',
                'For a one-zone testpiece, explicitly inventory the absent neighboring circuit surrogates and reserve their conservative volumes; do not infer wholeinstrumentfit from an isolated coupon.',
                'Repack worst local bypass and sensitive-pin clusters with actual pads and all existingtrim/fixture obstacles; recalculate full remote paths andreturnbudgets aftermovingconnectorbanks.',
                'Owner clarification is needed only for a genuine product tradeoff beyond delegatedengineering (functionremoval, fixedpanelmoves, adoption/hardware); missingcandidategeometry is engineeringwork, not a freshpermission gate.'],
            'native':'NOT RUN; no genuine exact-run admission','physical':'NOT RUN'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args();r=build();data=json.dumps(r,indent=2,sort_keys=True)+'\n';p=OUT/'reservations-report.json'
    if args.check:assert p.read_text()==data,'stale reservationstudy'
    else:p.write_text(data)
    print(f'SOURCE audit reproduced: {r["other_function_count"]} otherfunctions; {r["other_K_function_count"]} with{r["other_K_package_count"]} retainedKpackages; qualifiedfree0; wholeinstrumentSPACE UNKNOWN')
if __name__=='__main__':main()
