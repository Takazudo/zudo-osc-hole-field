"""Separate wire envelope and historical complete-path allocation, without qualification."""
import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import direct_study as d
ROOT=d.ROOT;OUT=d.OUT/'stage5'

def need(ok,message):
    if not ok:raise ValueError(message)

def metric(row,config):
    segments=row['segments'];wired='link' in row;octave=row['net'].startswith('OSC_OCT')
    expected={'front_trace_mm','GH_pair_mm','wire_max_mm','middle_trace_mm','DIN_mm','rear_trace_mm'} if wired else {'middle_trace_mm','DIN_mm','rear_trace_mm'}
    need(set(segments)==expected,'complete segment decomposition')
    need(all(math.isfinite(x) and x>=0 for x in segments.values()),'finite nonnegative allocations')
    need(row['length_limit_mm']==300 and row['capacitance_limit_pF']==1000,'canonical comparison values unchanged')
    need(row['capacitance_pF'] is None,'unextracted capacitance must remain unknown')
    need(segments['DIN_mm']==(0 if octave else 25),'DIN allowance changed')
    if wired:need(segments['GH_pair_mm']==15 and segments['wire_max_mm']==63,'GH/wire allowance changed')
    total=sum(segments.values());need(math.isclose(total,row['total_mm'],abs_tol=1e-8),'total decomposition mismatch')
    wire={'present':wired,'cut_nominal_mm':60 if wired else None,'cut_tolerance_mm':3 if wired else None,'cut_minimum_mm':57 if wired else None,'cut_maximum_mm':63 if wired else None,'original_harness_limit_mm':300,'length_only_result':'PASS ALLOCATION' if wired else 'NOT APPLICABLE: no wire in this branch','not_qualified':'actual cut length, conductor geometry, assembled capacitance and stability not measured'}
    return {'identity':d.identity(row),'actual_identity':row['actual_identity'],'wire':wire,
        'connector_developed_allocations_mm':{'GH_pair':segments.get('GH_pair_mm',0),'DIN_pair':segments['DIN_mm'],'sum':segments.get('GH_pair_mm',0)+segments['DIN_mm']},
        'PCB_trace_allocations_mm':{'front':segments.get('front_trace_mm',0),'middle':segments['middle_trace_mm'],'rear':segments['rear_trace_mm'],'sum':sum(segments.get(k,0) for k in ('front_trace_mm','middle_trace_mm','rear_trace_mm'))},
        'complete_developed_allocation_mm':total,'historical_strict_complete_path':{'limit_mm':300,'margin_mm':300-total,'result':'EXCEEDS HISTORICAL ALLOCATION' if total>300 else 'WITHIN HISTORICAL ALLOCATION','definition':'Later complete-pad-to-pad planning interpretation, not equivalent to original harness wording or measured failure threshold'},
        'capacitance':{'direct_limit_pF':1000,'assembled_direct_pF':None,'result':'UNKNOWN','scope':'shared nets require unique-segment aggregate; see nine-network table, not sum of duplicated endpoint rows'},
        'electrical_qualification':'UNKNOWN: error, stability, parasitics and dynamics unqualified','combined_acceptance':'NOT QUALIFIED'}

def summarize(name,candidate,config,expected):
    rows=candidate['paths'];need(len(rows)==225 and sorted(map(d.identity,rows))==expected,'exact225 crossing coverage')
    data=[metric(r,config)for r in rows]
    need(len(candidate['returns'])==240 and len(candidate['shared_aggregate_capacitance'])==9,'return/shared scope')
    wirekeys={(r['instance'],r['link'],r['link_pin']) for r in rows if 'link' in r}
    return {'name':name,'row_count':len(data),'rows':data,'summary':{'maximum_complete_allocation_mm':max(r['complete_developed_allocation_mm']for r in data),'historical_complete_over300_count':sum(r['complete_developed_allocation_mm']>300 for r in data),'wired_endpoint_rows':sum(r['wire']['present']for r in data),'unique_signal_wire_conductors':len(wirekeys),'wire_length_only_allocation_failures':0,'no_wire_rows':sum(not r['wire']['present']for r in data),'electrical_UNKNOWN_rows':len(data),'qualified_rows':0},'shared_aggregate_capacitance':candidate['shared_aggregate_capacitance'],'return_record_count':240,'combined_acceptance':'NOT QUALIFIED'}

def build():
    names=['design/architecture-278/implementation/assembly-report.json','design/architecture-278/implementation/candidate-report.json','design/architecture-278/implementation/direct-study-report.json','design/architecture-278/implementation/stage4/candidate-report.json','design/architecture-278/implementation/stage5/candidate-report.json']
    sources={p:(ROOT/p).read_bytes()for p in names};assembly,first,study,current,repair=[json.loads(sources[p])for p in names];config=assembly['config'];need((config['wire_nominal_mm'],config['wire_cut_tolerance_mm'],config['GH_pair_developed_mm'],config['DIN_developed_mm'],config['route_factor'],config['route_extra_mm'],config['endpoint_tolerance_mm'])==(60,3,15,25,1.15,5,1),'unchanged allowances')
    expected=sorted(map(d.identity,current['candidate']['paths']))
    variants={'stage3_baseline':study['best_by_variant']['baseline'],'stage3_bypass_refined':study['best_by_variant']['bypass_refined'],'stage4_shared_repair':current['candidate'],'stage5_header_repair':repair['candidate']}
    results={name:summarize(name,c,config,expected)for name,c in variants.items()}
    need([results[n]['summary']['historical_complete_over300_count'] for n in list(variants)[:3]]==[38,50,38],'historical failure counts drift')
    cuts=[{'instance':f'O{i+1}','template_link':h['id'],'conductors':len(h['pins']),'signal_conductors':sum(n!='AGND'for n in h['pins'].values()),'AGND_conductors':sum(n=='AGND'for n in h['pins'].values()),'cut_range_mm':[57,63]}for i in range(5)for h in first['front_links']]
    need(len(cuts)==85 and sum(h['conductors']for h in cuts)==270,'physical harness coverage')
    hashes={p:hashlib.sha256(b).hexdigest()for p,b in sources.items()}
    for p in [Path(__file__),Path(__file__).with_name('test_stage5_dual_metrics.py')]:hashes[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
    return {'status':'DUAL METRIC SOURCE REPORT; NO ELECTRICAL QUALIFICATION','source_sha256':hashes,'variants':results,'physical_wire_cut_inventory':cuts,'physical_wire_inventory_scope':'85links/270conductors include160signal and110AGND conductors.190wired endpoint rows are not190distinct wires. No wire length is inferred for35directshared-to-rear rows.','retained_trace_allowances':{'route_factor':1.15,'extra_per_segment_mm':5,'endpoint_tolerance_each_mm':1,'status':'reserved source geometry, not routed/extracted copper'},'nine_network_rule':'Aggregate shared directcapacitance over unique electrical segments, connectors, traces and probes once; retain five1k/100nF receiver switching dynamics separately. All extracted values UNKNOWN.','native':'NOT RUN','physical':'NOT RUN'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args();r=build();out=OUT/'dual-metrics-report.json';data=json.dumps(r,separators=(',',':'),sort_keys=True)+'\n'
    if args.check:need(out.read_text()==data,'stale dual metrics')
    else:out.write_text(data)
    print('dual metrics225/variant;historical38/50/38 preserved;160unique signal wires/110returns;qualification UNKNOWN')
if __name__=='__main__':main()
