"""Finite five-card slot/whole-card-turn/common-pin source allocation search.

No CAD, native tool, fabricated geometry or canonical mutation is performed.
"""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'design/architecture-278/implementation'
INSTANCES=['O1','O2','O3','O4','O5']
SLOTS=[(2,122),(107,122),(2,5),(107,5),(212,5)]
SHARED={'OSC_REF5','OSC_REFN5','OSC_GATE_REF'}

def matching(costs,threshold):
    adjacency=[[p for p,c in sorted(enumerate(row),key=lambda x:(x[1],x[0])) if c<=threshold] for row in costs]
    if any(not row for row in adjacency):return None
    used={}
    def visit(net,seen):
        for pin in adjacency[net]:
            if pin in seen:continue
            seen.add(pin)
            if pin not in used or visit(used[pin],seen):
                used[pin]=net;return True
        return False
    if not all(visit(n,set()) for n in sorted(range(len(costs)),key=lambda n:(len(adjacency[n]),n))):return None
    return {n:p for p,n in used.items()}

def build():
    report=json.loads((OUT/'assembly-report.json').read_text())
    config=report['config'];base=report['alternatives']['five_card_two_rows']
    compact=json.loads((OUT/'compact-rear.json').read_text())
    assert compact['tile_mm']==[103,115]
    assert base['origins_mm']==dict(zip(INSTANCES,map(list,SLOTS)))
    assert config['route_factor']==1.15 and config['route_extra_mm']==5 and config['endpoint_tolerance_mm']==1
    assert config['wire_nominal_mm']+config['wire_cut_tolerance_mm']==63
    assert config['GH_pair_developed_mm']==15 and config['DIN_developed_mm']==25
    nets=sorted(base['DIN_signal_labels']);assert len(nets)==26
    nindex={n:i for i,n in enumerate(nets)}
    rows=base['paths'];fixed=[r for r in rows if r['net'].startswith('OSC_OCT')]
    moving=[r for r in rows if not r['net'].startswith('OSC_OCT')]
    assert len(fixed)==30 and {r['net'] for r in moving}==set(nets)
    def segment(a,b):
        dx,dy=abs(a[0]-b[0]),abs(a[1]-b[1])
        return 1.15*(max(dx,dy)+(math.sqrt(2)-1)*min(dx,dy))+7
    def locate(local,slot,turn):
        x,y=local
        if turn:x,y=103-x,115-y
        return [slot[0]+x,slot[1]+y]
    def evaluate(row,slot,turn,pin):
        old=base['origins_mm'][row['instance']]
        local=[row['other_pad_mm'][i]-old[i] for i in range(2)]
        rear=locate(local,slot,turn)
        centre=compact['connector']['centre_mm']
        din=locate([centre[0]+2.54,centre[1]-39.37+pin*2.54],slot,turn)
        anchor=row['front_pad_mm'] if row['net'] in SHARED else row['middle_header_pad_mm']
        terms={'middle_trace_mm':segment(anchor,din),'DIN_mm':25,'rear_trace_mm':segment(din,rear)}
        if row['net'] not in SHARED:
            terms.update(front_trace_mm=row['segments']['front_trace_mm'],GH_pair_mm=15,wire_max_mm=63)
        return sum(terms.values()),rear,din,terms
    # Independent round-trip against every original row, before any search.
    for r in moving:
        total,*_=evaluate(r,base['origins_mm'][r['instance']],0,int(base['DIN_signal_labels'][r['net']][1:])-1)
        assert math.isclose(total,r['total_mm'],rel_tol=0,abs_tol=1e-9),(r['instance'],r['net'])
    buckets={(instance,n):[r for r in moving if r['instance']==instance and r['net']==n] for instance in INSTANCES for n in nets}
    assert all(buckets.values()),'missing instance/net endpoint coverage'
    costs={}
    for instance in INSTANCES:
        for slot_index,slot in enumerate(SLOTS):
            for turn in (0,1):
                costs[instance,slot_index,turn]=[
                    [max(evaluate(r,slot,turn,pin)[0] for r in buckets[instance,n]) for pin in range(32)] for n in nets]
    fixed_max=max(r['total_mm'] for r in fixed)
    best=float('inf');winner=None;counts={'enumerated':0,'lower_bound_pruned':0,'matching_pruned':0,'optimized':0}
    for assignment in itertools.permutations(range(5)):
        for turns in itertools.product((0,1),repeat=5):
            counts['enumerated']+=1
            matrices=[costs[instance,assignment[i],turns[i]] for i,instance in enumerate(INSTANCES)]
            combined=[[max(m[n][p] for m in matrices) for p in range(32)] for n in range(26)]
            lower=max(fixed_max,max(min(row) for row in combined))
            if lower>=best:counts['lower_bound_pruned']+=1;continue
            values=sorted({v for row in combined for v in row if v<best})
            if not values or matching(combined,values[-1]) is None:
                counts['matching_pruned']+=1;continue
            lo,hi=0,len(values)-1
            while lo<hi:
                mid=(lo+hi)//2
                if matching(combined,values[mid]) is None:lo=mid+1
                else:hi=mid
            selected=matching(combined,values[lo]);value=max(fixed_max,values[lo]);counts['optimized']+=1
            if value<best:
                best=value;winner=(assignment,turns,selected)
    assert counts['enumerated']==3840 and winner is not None
    assignment,turns,selected=winner
    origins={instance:list(SLOTS[assignment[i]]) for i,instance in enumerate(INSTANCES)}
    angles={instance:180*turns[i] for i,instance in enumerate(INSTANCES)}
    pinmap={n:'c'+str(selected[nindex[n]]+1) for n in nets}
    result_rows=[]
    for r in moving:
        total,rear,din,terms=evaluate(r,origins[r['instance']],angles[r['instance']]//180,selected[nindex[r['net']]])
        result_rows.append({**{k:r[k] for k in ('instance','net','front_endpoint','other_endpoint')},
            **{k:r[k] for k in ('link','link_pin') if k in r},'front_pad_mm':r['front_pad_mm'],
            'other_pad_mm':rear,'DIN_pad_mm':din,'DIN_signal_pin':pinmap[r['net']],
            'segments':terms,'total_mm':total,'margin_mm':300-total,
            'pad_separation_lower_bound_mm':math.dist(r['front_pad_mm'],rear)})
    result_rows+=fixed
    assert len(result_rows)==len(rows) and math.isclose(max(r['total_mm'] for r in result_rows),best,abs_tol=1e-9)
    hashes={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
        [Path(__file__),OUT/'assembly-report.json',OUT/'compact-rear.json',ROOT/'scripts/architecture278/implementation/assembly.py',ROOT/'scripts/architecture278/implementation/candidate.py',ROOT/'scripts/architecture278/populated_mechanics.py']}
    return {'status':'FINITE SOURCE ALLOCATION FAMILY SEARCH; Stage1 OPEN; native/physical NOT RUN',
        'source_sha256':hashes,'inherited_assembly_source_sha256':report['source_sha256'],
        'family':{'slots_mm':SLOTS,'card_mm':[103,115],'whole_card_turns_deg':[0,180],
            'assignments':120,'turn_masks':32,'total_combinations':3840,'signal_pins':'c1..c32; common injective26-net assignment',
            'adjacent_return_pins':'b with same index for every selected c signal;26 returns',
            'transform_180':'local[x,y] -> [103-x,115-y]; all rear endpoints, DIN, functional clusters and card reservations rotate together'},
        'search_counts':counts,'best_origins_mm':origins,'best_turns_deg':angles,'best_common_DIN_signal_labels':pinmap,
        'best_common_DIN_return_labels':{'b'+p[1:]:'AGND' for p in pinmap.values()},
        'maximum_mm':best,'minimum_margin_mm':300-best,'overlength_endpoint_count':sum(r['total_mm']>300 for r in result_rows),
        'actual_XY_pad_separation_over300_count':sum(r['pad_separation_lower_bound_mm']>300 for r in result_rows),
        'unchanged_octave_path_count':len(fixed),'unchanged_octave_maximum_mm':fixed_max,
        'original_endpoint_path_count':len(rows),'original_path_roundtrip':'PASS within1e-9mm for all195 DIN endpoint rows',
        'paths':result_rows,'limitations':[
            'Global minimum only within these3840assignments/turn masks, fixed front/shared geometry, fixed103x115 rear geometry and32c-row signal positions.',
            'Routing reservations are the inherited1.15octile+7mm per segment,63mm wire,15mm GH pair and25mm DIN; these are not extracted routes or proven worst-case obstacle bounds.',
            'Rotated supports, straps, keying, guides, insertion sweeps and board-to-world mating face must be rechecked before adopting a candidate.',
            'No change to passive identities, source/rail/return acceptance, capacitance, unknown load maxima, source stability or five-receiver electrical obligations.',
            'Unknown intermediate planes/returns remain OPEN. Failure of this finite family is not universal architecture infeasibility.']}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args()
    r=build();data=json.dumps(r,indent=2,sort_keys=True)+'\n';path=OUT/'placement-search-report.json'
    if args.check:assert path.read_text()==data,'stale placement search'
    else:path.write_text(data)
    print(json.dumps({k:r[k] for k in ('search_counts','maximum_mm','minimum_margin_mm','overlength_endpoint_count','actual_XY_pad_separation_over300_count','best_origins_mm','best_turns_deg')}))
