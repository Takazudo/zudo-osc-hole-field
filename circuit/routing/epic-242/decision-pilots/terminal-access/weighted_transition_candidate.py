#!/usr/bin/env python3
"""One fixed weighted source experiment; unchanged exact graph, no native calls."""
import argparse
from datetime import datetime, timezone
import heapq
import json
import math
from pathlib import Path
import subprocess
import time

import numpy as np
from scipy import ndimage
import f3_adapter as a
import analyze_f3_breakout_region as region
from exact_transition_candidate import ExactTransitions, validate_candidate, BudgetStop

HERE=Path(__file__).resolve().parent
GATE_SHA256='f0c87c62c12b7353511c0d3c9e6f34d9485a6c469288a4ce75b8cb2d45639457'
ORDER={'heuristic_weight':2,'priority':['g + 2*h','-g','deterministic node'],
       'planar_cost':'Euclidean lattice step times 3 on F.Cu/B.Cu, otherwise 1',
       'via_cost':30,'reopen':'strictly smaller positive g',
       'variants':0,'automatic_retries':0,'optimality_claim':False}


def priority(cost, heuristic, node):
    return (cost+2*heuristic,-cost,node)


def solve_weighted(gate, source, goal, max_expansions):
    """One fixed weight-2/higher-g search; graph, costs and caps are unchanged."""
    a.require(source.shape==goal.shape==gate.shape, 'terminal shape drift')
    a.require(source.any() and goal.any(), 'original terminals required')
    distance=ndimage.distance_transform_edt(~goal.any(0));best={};previous={};heap=[];expanded=0
    for row in np.argwhere(source):
        node=tuple(map(int,row));a.require(gate.hard[node], 'source violates unchanged nonforeign gate')
        best[node]=0.;heapq.heappush(heap,priority(0.,float(distance[node[1:]]),node))
    steps=((-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1))
    status='GRAPH_EXHAUSTED'
    try:
        while heap:
            gate.limits();_,negative_cost,node=heapq.heappop(heap);cost=-negative_cost
            if cost!=best[node]:continue
            if expanded>=max_expansions:status='EXPANSION_LIMIT';break
            expanded+=1
            if goal[node]:
                path=[node]
                while path[-1] in previous:path.append(previous[path[-1]])
                return list(reversed(path)),{'status':'COMPLETE_SOURCE_GRAPH_PATH','expanded':expanded,'visited':len(best),'exact_checks':gate.exact_checks}
            l,y,x=node;neighbors=[]
            for dy,dx in steps:
                q=(l,y+dy,x+dx)
                if gate.edge(node,q):neighbors.append((q,math.hypot(dy,dx)*(3 if gate.r.layers[l] in ('F.Cu','B.Cu') else 1)))
            for layer in range(gate.shape[0]):
                if gate.via(node,layer):neighbors.append(((layer,y,x),30.))
            for q,increment in neighbors:
                value=cost+increment
                if value<best.get(q,float('inf')):
                    best[q]=value;previous[q]=node;heapq.heappush(heap,priority(value,float(distance[q[1:]]),q))
    except BudgetStop as error:status=str(error)
    return None,{'status':status,'expanded':expanded,'visited':len(best),'exact_checks':gate.exact_checks,
                 'negative_scope':'One bounded method attempt; exhaustion of a cap is not physical impossibility'}


def method_binding():
    a.require(region.sha(HERE/'exact_transition_candidate.py')==GATE_SHA256,'exact graph/validation source drift')
    paths=[Path(__file__),HERE/'test_weighted_transition_candidate.py',HERE/'exact_transition_candidate.py',HERE/'analyze_f3_breakout_region.py']
    return {str(path.relative_to(a.ROOT)):region.sha(path) for path in paths}


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();a.require(not args.output.exists(),'fresh one-attempt output required; never overwrite or resume by rerunning')
    sources=method_binding();args.output.mkdir(parents=True)
    write=lambda name,value:(args.output/name).write_text(json.dumps(value,indent=2)+'\n')
    binding={'status':'PREPARING; one authorized source attempt only','ordering':ORDER,'source_sha256':sources,
             'source_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=a.ROOT,text=True).strip(),
             'started_utc':datetime.now(timezone.utc).isoformat(),'native_admitted':False}
    write('execution-source.json',binding)
    original,card,packet,pool,receipt,input_binding=region.authenticate(args.candidate)
    domain=packet['demand_and_preservation_contract'];target=domain['targets']['signal'];original_digest=a.digest(original)
    a.require(packet['budget']['max_expansions_per_search']==50000,'expansion cap drift')
    groups,records,_=a.portals(original,target,pool['signal'],packet['budget'],domain['common_bounds_mm'])
    saved=region.capture(original,groups,records,packet);gate=ExactTransitions(original,saved,packet)
    a.require(saved['window']==[99,343,37,420] and gate.max_edges==250000,'domain or exact-check cap drift')
    a.require(method_binding()==sources,'source changed during preparation')
    binding.update(status='SEARCH_STARTED; do not retry if interrupted',input_dump_sha256=input_binding['input_dump_sha256'],
        candidate_input_source_binding_sha256=region.sha(args.candidate/'source-binding.json'),window_cells=saved['window'],budget=packet['budget'],exact_check_cap=gate.max_edges)
    write('execution-source.json',binding)
    print('One fixed weight-2/higher-g source search started; all graph/geometry/goals/caps unchanged',flush=True)
    path,diagnostic=solve_weighted(gate,saved['src'],saved['goal'],50000)
    candidate=None;selected=[]
    if path:
        raw=[[gate.r.layers[l],*gate.r.point(y+gate.y0,x+gate.x0),0] for l,y,x in path]
        for left,right in zip(path,path[1:]):
            key=tuple(sorted((left,right)))
            if key in gate.exceptions:selected.append(gate.exceptions[key])
        # Retain a diagnostic chain separately even if atomic physical validation refuses it.
        write('graph-path.json',{'status':'UNVALIDATED GRAPH PATH; NOT COPPER OR NATIVE CREDIT','path':raw})
        try:candidate=validate_candidate(original,raw,groups,records,target,packet)
        except ValueError as error:diagnostic.update(status='STOPPED_AT_COMPLETE_CHAIN_GATE',rejection=str(error),failure=getattr(error,'receipt',None))
    a.require(a.digest(original)==original_digest,'physical input mutated')
    a.require(method_binding()==sources,'executed source drift')
    result={'status':'COMPLETE STITCHED EXACT-VALIDATED SOURCE CANDIDATE' if candidate else 'RETIRE UNCHANGED-PLACEMENT CASE; STOPPED NEGATIVE',
        'ordering':ORDER,'source_sha256':sources,'execution_source_sha256':region.sha(args.output/'execution-source.json'),
        'input_dump_sha256':input_binding['input_dump_sha256'],'candidate_input_source_binding_sha256':binding['candidate_input_source_binding_sha256'],
        'window_cells':saved['window'],'bounds_mm':domain['common_bounds_mm'],'budget':packet['budget'],'exact_check_cap':gate.max_edges,
        'diagnostic':diagnostic,'method_interval_seconds':time.monotonic()-gate.started,'new_exact_overrides_considered':len(gate.exceptions),
        'selected_exact_overrides':selected,'failure_counts':dict(gate.failures),'candidate_created':candidate is not None,
        'physical_input_unchanged':True,'native_executed':False,'adopted':False,'native_admission':'NONE; all slots free',
        'original_demands':'All four retained; rails and AGND unchanged; no all-demand success',
        'next':'Retain complete source candidate for review; native gates still unadmitted' if candidate else 'No rolling heuristic variants or budget increases; recommend a separately scoped candidate placement under the epic',
        'negative_scope':'A capped or rejected source attempt is not placement impossibility'}
    write('result.json',result)
    if candidate:write('source-candidate.json',candidate)
    print(json.dumps({k:result[k] for k in ('status','diagnostic','method_interval_seconds','candidate_created','native_executed')}),flush=True)


if __name__=='__main__':main()
