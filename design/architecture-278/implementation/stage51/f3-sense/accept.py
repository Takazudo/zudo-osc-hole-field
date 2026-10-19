"""Exact additive F3 proposal and all-net retained partition acceptance."""
from pathlib import Path
from collections import Counter
import hashlib,json,sys,re
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
sys.path.insert(0,str(HERE));sys.path.insert(0,str(ROOT/'design/architecture-278/implementation/stage41/native-pilot'))
from identity_guard import inventory,compare,structure_matches,top_level_spans,kind,value,digest,copper_contract
BASE='05f85d8cb27dcbeec76327065e91526f0112ebc316054a1cec5cae5cbc80c441'
NET='XED7C19D453619667580D'
PROPOSAL_SHA='3e0249197b3ae360353ce0a0b103e8e05e68e001833a582c8afb490820321712'
RETIRED=()

def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'))
def signature(x):return hashlib.sha256(canonical(x).encode()).hexdigest()
def contract(row):
 if row['kind']=='segment':g=[row['start_nm'],row['end_nm'],[row['width_nm']],row['layer']]
 else:g=[row['at_nm'],[row['diameter_nm']],[row['drill_nm']],['F.Cu','B.Cu']]
 return [row['kind'],row['uuid'],g,row['net']]
def exact_added_block(row):
 def mm(n):return format(n/1e6,'.9g')
 def xy(p):return ' '.join(mm(n) for n in p)
 if row['kind']=='segment':
  body=f'(start {xy(row["start_nm"])}) (end {xy(row["end_nm"])}) (width {mm(row["width_nm"])}) (layer "{row["layer"]}")'
 else:
  body=f'(at {xy(row["at_nm"])}) (size {mm(row["diameter_nm"])}) (drill {mm(row["drill_nm"])}) (layers "F.Cu" "B.Cu")'
 return f'({row["kind"]} {body} (net "{row["net"]}") (uuid "{row["uuid"]}"))'
def exact_added_properties(after_raw,proposal):
 expected={r['uuid']:re.sub(r'\s+','',exact_added_block(r)) for r in proposal['copper']};actual={}
 for a,b in top_level_spans(after_raw):
  block=after_raw[a:b]
  if kind(block) in ['segment','via'] and value(block,'uuid') in expected:
   uid=value(block,'uuid')
   if uid in actual:raise ValueError('duplicate new copper')
   actual[uid]=re.sub(r'\s+','',block)
 if actual!=expected:raise ValueError('new copper properties or geometry changed')
def identity(before_raw,after_raw,proposal):
 if digest(before_raw)!=proposal['board_sha256'] or proposal['board_sha256']!=BASE:raise ValueError('baseline binding')
 if signature(proposal)!=signature(read(HERE/'proposal.json')) or sha(HERE/'proposal.json')!=PROPOSAL_SHA:raise ValueError('exact authorized proposal')
 if proposal['removed_uuids']:raise ValueError('retirement forbidden')
 exact_added_properties(after_raw,proposal)
 expected_retired=[]
 before,after=inventory(before_raw),inventory(after_raw)
 newids={r['uuid'] for r in proposal['copper']}
 actual=Counter(canonical(c) for c,n in after['native_contract'].items() if c[1] in newids for _ in range(n))
 expected=Counter(canonical(contract(r)) for r in proposal['copper'])
 if actual!=expected:raise ValueError('proposal geometry/net changed')
 allowed=[list(k) for k,n in after['copper'].items() if k[1] in newids for _ in range(n)]
 result=compare(before,after,[r['sha256'] for r in expected_retired],allowed)
 result['checks']['all_footprints_unchanged']=structure_matches(before,after,{})
 result['accepted']=all(result['checks'].values())
 if not result['accepted']:raise ValueError('identity preservation: '+str(result))
 return result

def validate_snapshot(snapshot):
 seen=Counter()
 for net,groups in snapshot['groups'].items():
  for group in groups:
   if not group:raise ValueError('empty component')
   for key in group:
    if key not in snapshot['objects'] or snapshot['objects'][key]['net']!=net:raise ValueError('component net/object mismatch')
    seen[key]+=1
 if seen!=Counter({k:1 for k in snapshot['objects']}):raise ValueError('component inventory/duplicate')
 if sum(len(groups)-1 for groups in snapshot['groups'].values())!=snapshot['native_open_edges']:raise ValueError('component/open count mismatch')

def connectivity(old,new,proposal):
 validate_snapshot(old);validate_snapshot(new)
 old_objects,new_objects=old['objects'],new['objects'];retained=set(old_objects)
 if not retained<=set(new_objects) or any(new_objects[k]!=old_objects[k] for k in retained):raise ValueError('retained native objects')
 added=set(new_objects)-retained
 if {new_objects[k].get('uuid') for k in added}!={r['uuid'] for r in proposal['copper']} or len(added)!=len(proposal['copper']):raise ValueError('native additions')
 source=next(k for k,v in old_objects.items() if v.get('kind')=='pad' and v.get('ref')=='R2316' and v.get('pin')=='2')
 target=next(k for k,v in old_objects.items() if v.get('kind')=='pad' and v.get('ref')=='U2317' and v.get('pin')=='10')
 sg=next(set(g) for g in old['groups'][NET] if source in g);tg=next(set(g) for g in old['groups'][NET] if target in g)
 if sg==tg or sg!={source} or len(tg)!=50:raise ValueError('baseline target partition')
 expected={net:[set(g) for g in groups] for net,groups in old['groups'].items()}
 expected[NET]=[g for g in expected[NET] if g not in [sg,tg]]+[sg|tg]
 if set(new['groups'])!=set(expected):raise ValueError('native net set')
 for net,groups in new['groups'].items():
  projected=[set(g)&retained for g in groups]
  if any(not g for g in projected):raise ValueError('new-only island')
  if {frozenset(g) for g in projected}!={frozenset(g) for g in expected[net]}:raise ValueError('unexpected partition: '+net)
 if old['native_open_edges']!=116 or new['native_open_edges']!=115:raise ValueError('open count')
 for key in added:
  net=new_objects[key]['net'];g=next(set(g)&retained for g in new['groups'][net] if key in g)
  if net!=NET or g!=sg|tg:raise ValueError('new copper attached to wrong component')
 return dict(accepted=True,old_opens=116,new_opens=115,source_component_size=1,target_component_size=50,merged_retained_members=51,added_objects=len(added),source_component_hash=signature(sorted(sg)),target_component_hash=signature(sorted(tg)),exact_retained_partition_merge=True)

def warning_gate(old_drc,drc):
 def uncapped(d):return Counter((v['type'],tuple(sorted(i['uuid'] for i in v['items']))) for v in d['violations'] if v['severity']=='warning' and v['type'] not in ('silk_overlap','silk_over_copper'))
 added_warnings=uncapped(drc)-uncapped(old_drc);removed_warnings=uncapped(old_drc)-uncapped(drc)
 if added_warnings or any(not set(k[1])<=set(RETIRED) for k in removed_warnings):raise ValueError('uncapped warning regression/change')
 for report in (old_drc,drc):
  counts=Counter(v['type'] for v in report['violations'] if v['severity']=='warning')
  if any(n >= (499 if k in ('clearance','unconnected_items') else 199) for k,n in counts.items() if k not in ('silk_overlap','silk_over_copper')):raise ValueError('unreviewed capped warning category')
 if any(v['type']=='lib_footprint_issues' for v in drc['violations']):raise ValueError('library resolution')
 return dict(no_added_uncapped=True,removed_uncapped=[[k[0],list(k[1])] for k in removed_warnings],capped_silkscreen_identity_nonregression='UNRESOLVED')

def evaluate(baseline,candidate,proposal_path,label):
 proposal=read(proposal_path);before=baseline/'osc-jack-left.kicad_pcb';after=candidate/'osc-jack-left.kicad_pcb'
 old=read(baseline/'connectivity-passfresh.json');new=read(candidate/f'connectivity-{label}.json')
 if old['board_sha256']!=sha(before) or new['board_sha256']!=sha(after):raise ValueError('snapshot bytes')
 result=dict(identity=identity(before.read_text(),after.read_text(),proposal),connectivity=connectivity(old,new,proposal),baseline_sha256=sha(before),candidate_sha256=sha(after),proposal_sha256=sha(proposal_path))
 drc=read(candidate/f'drc-{label}.json')
 sys.path.insert(0,str(ROOT/'design/architecture-278/implementation/stage44/b2-specific'))
 from drc_run import validate,dependencies
 execution=read(candidate/f'drc-{label}.json.execution.json')
 validate(candidate/f'drc-{label}.json',execution,sha(after),dependencies(after))
 if dependencies(before)!=dependencies(after):raise ValueError('dependency drift')
 if drc['kicad_version']!='10.0.6' or new['version']!='10.0.6' or drc['schematic_parity'] or any(v['severity']=='error' for v in drc['violations']) or len(drc['unconnected_items'])!=115:raise ValueError('native DRC/parity/open gate')
 old_report=baseline/'drc-passfresh.json'
 validate(old_report,read(baseline/'drc-passfresh.json.execution.json'),sha(before),dependencies(before))
 old_drc=read(old_report)
 if baseline.parent.resolve()!=candidate.parent.resolve():raise ValueError('relative library root depth changed')
 result['warning_comparison']=warning_gate(old_drc,drc)
 result['drc']=dict(rule_errors=0,parity=0,opens=115,warning_counts=dict(Counter(v['type'] for v in drc['violations'] if v['severity']=='warning')))
 result['accepted_bounded_native_repair']=True
 return result

def run(baseline,candidate,proposal_path,label):
 result=evaluate(baseline,candidate,proposal_path,label)
 output=candidate/f'acceptance-{label}.json'
 if output.exists():raise ValueError('do not overwrite acceptance')
 output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result))
if __name__=='__main__':run(Path(sys.argv[1]),Path(sys.argv[2]),Path(sys.argv[3]),sys.argv[4])
