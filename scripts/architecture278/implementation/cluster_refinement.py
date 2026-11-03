"""Candidate rear bypass locality refinement. No CAD/native or netlist mutation.

Place entire bypass packages first against actual supply pads, then relocate only
other small packages within the same cluster. Six trim axes stay fixed; ICs move as whole packages within their clusters.
"""
import argparse
from collections import Counter
import copy
import hashlib
import itertools
import json
import math
from pathlib import Path
import candidate as c

ROOT,OUT=c.ROOT,c.OUT
# Dedicated package supply returns from retained power units/core pin map.
# Op-amp AGND signal inputs are deliberately NOT treated as supply returns.
SUPPLY_RETURN={'U1105':'12','U1106':'4','U1107':'7','U1108':'4'}

def turn(xy,q):
    x,y=xy
    for _ in range(q%4):x,y=-y,x
    return [x,y]

def pose(original,origin,q=0):
    old=original['origin_mm'];p=copy.deepcopy(original)
    def pt(xy):
        x,y=turn([xy[0]-old[0],xy[1]-old[1]],q)
        return [origin[0]+x,origin[1]+y]
    p['origin_mm']=origin;p['quarter_turn']=q
    p['pads_mm']={pin:[pt(xy) for xy in coords] for pin,coords in original['pads_mm'].items()}
    for key in ('box_mm','reserved_box_mm'):
        b=original[key];pts=[pt(x) for x in itertools.product((b[0],b[2]),(b[1],b[3]))]
        p[key]=[min(x for x,y in pts),min(y for x,y in pts),max(x for x,y in pts),max(y for x,y in pts)]
    return p

def associations(contract,physical):
    keys={u['key'].split('.')[0]:u['ref'] for u in contract['parts'] if u['instance']=='O1'}
    result=[]
    for ref,p in physical.items():
        target=p['attributes'].get('Decouples')
        if not target:continue
        target=keys[target]
        rail=[(pin,net) for pin,net in p['pins'].items() if net not in ('AGND',None)]
        ground=[pin for pin,net in p['pins'].items() if net=='AGND']
        c.require(len(rail)==1 and len(ground)==1,'ambiguous bypass '+ref)
        supply=[pin for pin,net in physical[target]['pins'].items() if net==rail[0][1]]
        c.require(len(supply)==1,'ambiguous IC rail '+ref)
        gp=SUPPLY_RETURN.get(target)
        c.require(gp is None or physical[target]['pins'][gp]=='AGND','invalid dedicated return')
        result.append({'capacitor':ref,'IC':target,'rail':rail[0][1],'capacitor_rail_pin':rail[0][0],
                       'capacitor_return_pin':ground[0],'IC_rail_pin':supply[0],'IC_dedicated_return_pin':gp})
    return result

def metrics(a,placed):
    cap,ic=placed[a['capacitor']],placed[a['IC']]
    cp=cap['pads_mm'][a['capacitor_rail_pin']][0];ip=ic['pads_mm'][a['IC_rail_pin']][0]
    cg=cap['pads_mm'][a['capacitor_return_pin']][0]
    ig=ic['pads_mm'][a['IC_dedicated_return_pin']][0] if a['IC_dedicated_return_pin'] else None
    return {'rail_pad_distance_mm':math.dist(cp,ip),'capacitor_rail_pad_mm':cp,'IC_rail_pad_mm':ip,
            'capacitor_return_pad_mm':cg,'IC_dedicated_return_pad_mm':ig,
            'dedicated_return_pad_distance_mm':math.dist(cg,ig) if ig else None,
            'two_external_leg_distance_sum_mm':math.dist(cp,ip)+math.dist(cg,ig) if ig else None,
            'return_status':'dedicated package AGND pad identified; actual plane/via route and loop OPEN' if ig else 'no dedicated package AGND supply pin; actual supply/ground-plane loop OPEN; grounded signal/spare inputs not credited'}

def valid_pose(p,bounds,placed,gap=.5):
    b=p['reserved_box_mm']
    return bounds[0]<=b[0]+1e-9 and bounds[1]<=b[1]+1e-9 and b[2]<=bounds[2]+1e-9 and b[3]<=bounds[3]+1e-9 and not any(c.overlap(b,o['reserved_box_mm'],gap-1e-8) for o in placed)

def place_one(original,bounds,placed,score):
    choices=[]
    for q in range(4):
        local=pose(original,[0,0],q);b=local['reserved_box_mm']
        for xi in range(math.ceil(2*(bounds[0]-b[0])),math.floor(2*(bounds[2]-b[2]))+1):
            for yi in range(math.ceil(2*(bounds[1]-b[1])),math.floor(2*(bounds[3]-b[3]))+1):
                origin=[xi/2,yi/2]
                # Score only inexpensive translated pad coordinates, build complete
                # objects after sorting; objective uses actual rail and return pads.
                pads={pin:[[x+origin[0],y+origin[1]] for x,y in pts] for pin,pts in local['pads_mm'].items()}
                choices.append((score(pads,origin),q,origin))
    for _,q,origin in sorted(choices,key=lambda x:(x[0],x[1],x[2])):
        p=pose(original,origin,q)
        if valid_pose(p,bounds,placed):return p
    raise ValueError('cluster has no capacity for '+original['ref'])

def validate(placed,base,spec,physical):
    c.require(Counter(p['ref'] for p in placed)==Counter(p['ref'] for p in base),'whole package coverage')
    old={p['ref']:p for p in base};clusters={g['id']:g for g in spec['clusters']}
    for p in placed:
        original=old[p['ref']]
        c.require(p['cluster']==original['cluster'],'cluster ownership changed')
        c.require(p['units']==original['units'] and set(p['pads_mm'])==set(physical[p['ref']]['pins']),'units or pad coverage changed')
        expected=pose(original,p['origin_mm'],p.get('quarter_turn',0))
        def close(a,b):return len(a)==len(b) and all(math.isclose(x,y,abs_tol=1e-9,rel_tol=0) for x,y in zip(a,b))
        c.require(all(len(p['pads_mm'][pin])==len(coords) and all(close(x,y) for x,y in zip(p['pads_mm'][pin],coords)) for pin,coords in expected['pads_mm'].items()) and close(p['box_mm'],expected['box_mm']) and close(p['reserved_box_mm'],expected['reserved_box_mm']),'whole package geometry changed')
        c.require(valid_pose(p,clusters[p['cluster']]['box_mm'],[q for q in placed if q['ref']!=p['ref']]),'courtyard/tool clearance '+p['ref'])
        if p['ref'].startswith('RVO'):
            c.require(p['origin_mm']==original['origin_mm'] and p['pads_mm']==original['pads_mm'],'trim axes moved')
    c.require(sum(bool(p['trim_tool_diameter_mm']) for p in placed)==6,'six trims missing')

def build():
    contract=c.read('interface-contract.json');physical={r:p for r,p in c.packages(contract).items() if p['owner']=='rear-core' and p['footprint']}
    spec=c.read('implementation/compact-rear.json');base=c.place(spec,physical);old={p['ref']:p for p in base}
    aa=associations(contract,physical);bycap={a['capacitor']:a for a in aa};placed=[]
    for group in spec['clusters']:
        originals=[old[r] for r in group['refs']]
        fixed=[copy.deepcopy(p) for p in originals if p['ref'].startswith('RVO')]
        ics=[p for p in originals if p['ref'].startswith('U')]
        for ic in sorted(ics,key=lambda p:-(p['box_mm'][2]-p['box_mm'][0])*(p['box_mm'][3]-p['box_mm'][1])):
            bounds=group['box_mm'];target=[(bounds[0]+bounds[2])/2,(bounds[1]+bounds[3])/2]
            if ic['ref']=='U1105':target=[35,47]
            fixed.append(place_one(ic,bounds,fixed,lambda pads,origin:(math.dist(origin,target),)))
        for p in fixed:p.setdefault('quarter_turn',0)
        current=list(fixed)
        caps=sorted([p for p in originals if p['ref'] in bycap],key=lambda p:p['ref'])
        for cap in caps:
            a=bycap[cap['ref']];ic=next(p for p in fixed if p['ref']==a['IC']);ip=ic['pads_mm'][a['IC_rail_pin']][0]
            ig=ic['pads_mm'][a['IC_dedicated_return_pin']][0] if a['IC_dedicated_return_pin'] else None
            def score(pads,origin):
                rail=math.dist(pads[a['capacitor_rail_pin']][0],ip)
                ret=math.dist(pads[a['capacitor_return_pin']][0],ig) if ig else 0
                return (rail+ret,rail,math.dist(origin,cap['origin_mm']))
            current.append(place_one(cap,group['box_mm'],current,score))
        fixed_refs={p['ref'] for p in fixed}
        other=[p for p in originals if p['ref'] not in fixed_refs and p['ref'] not in bycap]
        for p in sorted(other,key=lambda p:(-(p['reserved_box_mm'][2]-p['reserved_box_mm'][0])*(p['reserved_box_mm'][3]-p['reserved_box_mm'][1]),p['ref'])):
            if valid_pose(p,group['box_mm'],current):q=copy.deepcopy(p);q['quarter_turn']=0
            else:q=place_one(p,group['box_mm'],current,lambda pads,origin:(math.dist(origin,p['origin_mm']),))
            current.append(q)
        placed+=current
    validate(placed,base,spec,physical)
    # Includes DIN, supports, guides, probes, handle and power reservations from
    # the compact comparison; rejects local fixture collisions as well.
    mechanical=c.mechanical(spec,placed)
    new={p['ref']:p for p in placed};rows=[]
    for a in aa:
        c.require(new[a['capacitor']]['cluster']==new[a['IC']]['cluster'],'detached bypass')
        rows.append(dict(a,before=metrics(a,old),after=metrics(a,new)))
    # Endpoints remain exact source tuples; only physical XY is transformed.
    endpoints=[{'ref':r,'pin':pin,'net':net,'xy_mm':new[r]['pads_mm'][pin]} for r,p in physical.items() for pin,net in p['pins'].items()]
    net_spans=[]
    nets=sorted({e['net'] for e in endpoints if e['net'] not in (None,'AGND','+12V','-12V','+5V')})
    for net in nets:
        nodes=[(r,pin) for r,p in physical.items() for pin,n in p['pins'].items() if n==net]
        def span(by):
            coords=[xy for ref,pin in nodes for xy in by[ref]['pads_mm'][pin]]
            return max((math.dist(a,b) for a,b in itertools.combinations(coords,2)),default=0)
        before,after=span(old),span(new)
        net_spans.append({'net':net,'endpoints':[ref+':'+pin for ref,pin in nodes],
            'before_max_pair_separation_mm':before,'after_max_pair_separation_mm':after,'change_mm':after-before,
            'scope':'all retained rear endpoints on this net; some nets also have external endpoints; Euclidean extent only, not copper length/loop area'})
    paths=[Path(__file__),Path(c.__file__),ROOT/'scripts/architecture278/populated_mechanics.py',c.PACK/'interface-contract.json',OUT/'compact-rear.json']+[ROOT/p['footprint_source'] for p in placed]
    return {'status':'BOUNDED REAR BYPASS SOURCE REFINEMENT; local routing/loop qualification OPEN; native NOT RUN',
            'source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(paths))},
            'method':'Six trim axes fixed; whole IC packages recentered within cluster boxes. Bypass whole packages scored by supply-pad distance plus dedicated return-pad distance when such a supply pin exists; other small packages displaced only within original whole functional cluster. 0.5mm position grid and 0.5mm courtyard/tool clearance.',
            'cluster_boxes':{g['id']:g['box_mm'] for g in spec['clusters']},'placements':placed,'bypass_associations':rows,
            'endpoint_inventory':endpoints,'local_net_span_comparison':net_spans,'package_count':len(placed),'unit_count':sum(len(p['units']) for p in placed),'cluster_count':len(spec['clusters']),'trim_count':6,
            'rail_leg_regressions':[r['capacitor'] for r in rows if r['after']['rail_pad_distance_mm']>r['before']['rail_pad_distance_mm']+1e-9],
            'dedicated_two_leg_regressions':[r['capacitor'] for r in rows if r['after']['two_external_leg_distance_sum_mm'] is not None and r['after']['two_external_leg_distance_sum_mm']>r['before']['two_external_leg_distance_sum_mm']+1e-9],
            'before_max_rail_distance_mm':max(r['before']['rail_pad_distance_mm'] for r in rows),'after_max_rail_distance_mm':max(r['after']['rail_pad_distance_mm'] for r in rows),
            'mechanical_screen':mechanical,'limitations':['No extracted copper/planes/vias; Euclidean pad distances do not prove loop area, impedance, inductance or stability.','Feedback/timing/summing/spare endpoint sets and full packages retained; altered passive placement requires new local routed review.','No signal path budget shortened or remote allowance modified; all remote path analyses must be recomputed if this comparison is consumed.','No op-amp grounded input or unused amplifier is counted as a dedicated supply-return pin.','No full assembly/native/physical acceptance and no adoption.']}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args();r=build()
    text=json.dumps(r,indent=2,sort_keys=True)+'\n';p=OUT/'cluster-refinement-report.json'
    if args.check:c.require(p.read_text()==text,'stale cluster refinement')
    else:p.write_text(text)
    print(json.dumps({k:r[k] for k in ('package_count','unit_count','cluster_count','trim_count','before_max_rail_distance_mm','after_max_rail_distance_mm')}))
