#!/usr/bin/env python3
"""Check the complete retained 148-edge cut against the candidate gate; no search."""
import argparse
import json
from pathlib import Path
from unittest.mock import patch

import f3_adapter as a
import analyze_f3_breakout_region as region
import exact_transition_candidate as method

HERE=Path(__file__).resolve().parent


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args=p.parse_args();a.require(not args.output.exists(),'fresh output file required')
    original,card,packet,pool,_,binding=region.authenticate(args.candidate)
    target=packet['demand_and_preservation_contract']['targets']['signal']
    groups,records,_=a.portals(original,target,pool['signal'],packet['budget'],packet['bounds_mm'])
    saved=region.capture(original,groups,records,packet)
    gate=method.ExactTransitions(original,saved,packet)
    previous=HERE/'local-breakout/region-stop/exact-boundary.json'
    evidence=json.loads(previous.read_text());rows=[]
    with patch.object(method,'solve',side_effect=AssertionError('feasibility search forbidden')):
        for old in evidence['boundary']:
            li=gate.r.layers.index(old['layer']);nodes=[]
            for key in ('start_mm','end_mm'):
                y,x=gate.r.cell(*[round(v*1e6) for v in old[key]])
                nodes.append((li,y-gate.y0,x-gate.x0))
            a.require(not gate.foreign[nodes[1]] and gate.hard[nodes[0]] and gate.hard[nodes[1]],'retained foreign-only boundary drift')
            passed=gate.edge(*nodes)
            a.require(passed==old['validation']['pass'],'complete exact gate disagrees with retained full geometry')
            rows.append({'layer':old['layer'],'start_mm':old['start_mm'],'end_mm':old['end_mm'],
                'candidate_gate_pass':passed,'exact_validation':old['validation']})
    result={'status':'PASS: 130 exact-clear exits admitted; 18 real collisions still refused',
        'scope':'Complete retained boundary edge check only; no new feasibility search, native, copper or pair success',
        'current_method_sha256':region.sha(HERE/'exact_transition_candidate.py'),'producer_sha256':region.sha(Path(__file__)),
        'candidate_input_source_binding_sha256':region.sha(args.candidate/'source-binding.json'),
        'complete_original_dump_sha256':binding['input_dump_sha256'],'retained_boundary_sha256':region.sha(previous),
        'pass_count':sum(x['candidate_gate_pass'] for x in rows),'refuse_count':sum(not x['candidate_gate_pass'] for x in rows),
        'exact_checks':gate.exact_checks,'edges':rows,'feasibility_search_executed':False,'native_executed':False}
    a.require(result['pass_count']==130 and result['refuse_count']==18,'retained complete boundary census drift')
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('status','pass_count','refuse_count','exact_checks','feasibility_search_executed','native_executed')}))


if __name__=='__main__':main()
