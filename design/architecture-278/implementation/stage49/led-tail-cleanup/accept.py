"""Exact authorized LED tail cleanup and one specified AGND component merge gate."""
from pathlib import Path
from collections import Counter
import hashlib,json,sys,re
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
sys.path.insert(0,str(HERE));sys.path.insert(0,str(ROOT/'design/architecture-278/implementation/stage41/native-pilot'))
from identity_guard import inventory,compare,structure_matches,top_level_spans,kind,value,digest,copper_contract
import importlib.util
_spec=importlib.util.spec_from_file_location('stage49_propose',HERE/'propose.py');_p=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(_p)
BASE,RETIRED,NET=_p.BASE,_p.RETIRED,_p.NET
SOURCE='b9d402b4-b8c4-5ab2-a8c0-3fd450c4809c'
TARGET='a6b5c1e1-3b03-53c1-aff3-69160966559d'

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
 if canonical(proposal)!=canonical(_p.build(before_raw)):raise ValueError('exact authorized proposal')
 exact_added_properties(after_raw,proposal)
 expected_retired=proposal['retirements']
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
 old_objects,new_objects=old['objects'],new['objects']
 retired=[k for k,v in old_objects.items() if v.get('uuid') in RETIRED]
 if len(retired)!=10 or any(old_objects[k]['net']!=NET for k in retired):raise ValueError('native retirement')
 retained=set(old_objects)-set(retired)
 if not retained<=set(new_objects) or any(new_objects[k]!=old_objects[k] for k in retained):raise ValueError('retained native objects')
 added=set(new_objects)-retained
 if {new_objects[k].get('uuid') for k in added}!={r['uuid'] for r in proposal['copper']} or len(added)!=len(proposal['copper']):raise ValueError('native additions')
 source=next(k for k,v in old_objects.items() if v.get('kind')=='pad' and v.get('ref')=='R8270' and v.get('pin')=='2')
 target=next(k for k,v in old_objects.items() if v.get('uuid')==TARGET)
 sg=next(set(g) for g in old['groups']['AGND'] if source in g);tg=next(set(g) for g in old['groups']['AGND'] if target in g)
 if sg==tg:raise ValueError('already connected')
 expected={}
 for net,groups in old['groups'].items():
  expected[net]=[set(g)&retained for g in groups if set(g)&retained]
 expected['AGND']=[g for g in expected['AGND'] if g not in [sg,tg]]+[sg|tg]
 if set(new['groups'])!=set(expected):raise ValueError('native net set')
 for net,groups in new['groups'].items():
  projected=[set(g)&retained for g in groups]
  if any(not g for g in projected):raise ValueError('new-only island')
  if {frozenset(g) for g in projected}!={frozenset(g) for g in expected[net]}:raise ValueError('unexpected partition: '+net)
 if old['native_open_edges']!=117 or new['native_open_edges']!=116:raise ValueError('open count')
 signal_expected=next(set(g)&retained for g in old['groups'][NET] if retired[0] in g)
 if any(next(set(g)&retained for g in old['groups'][NET] if k in g)!=signal_expected for k in retired):raise ValueError('retired objects in different LED components')
 for key in added:
  net=new_objects[key]['net'];g=next(set(g)&retained for g in new['groups'][net] if key in g)
  if net!=NET or g!=signal_expected:raise ValueError('replacement attached to wrong baseline component')
 changes=[]
 for key in retired:
  group=next(g for g in old['groups'][NET] if key in g)
  changes.append(dict(operation='retire',uuid=old_objects[key]['uuid'],net=NET,baseline_component_hash=signature(group),baseline_component_size=len(group),retained_neighbors=len(set(group)&retained)))
 for key in sorted(added):
  net=new_objects[key]['net'];g=next(g for g in new['groups'][net] if key in g)
  changes.append(dict(operation='add',uuid=new_objects[key]['uuid'],net=net,component_hash=signature(g),component_size=len(g),retained_members=len(set(g)&retained)))
 return dict(accepted=True,old_opens=117,new_opens=116,source_component_size=len(sg),main_component_size=len(tg),source_component_hash=signature(sorted(sg)),main_component_hash=signature(sorted(tg)),exact_retained_partition_merge=True,objects=changes)

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
 if drc['kicad_version']!='10.0.6' or new['version']!='10.0.6' or drc['schematic_parity'] or any(v['severity']=='error' for v in drc['violations']) or len(drc['unconnected_items'])!=116:raise ValueError('native DRC/parity/open gate')
 old_report=baseline/'drc-passfresh.json'
 validate(old_report,read(baseline/'drc-passfresh.json.execution.json'),sha(before),dependencies(before))
 old_drc=read(old_report)
 if baseline.parent.resolve()!=candidate.parent.resolve():raise ValueError('relative library root depth changed')
 result['warning_comparison']=warning_gate(old_drc,drc)
 result['drc']=dict(rule_errors=0,parity=0,opens=116,warning_counts=dict(Counter(v['type'] for v in drc['violations'] if v['severity']=='warning')))
 result['accepted_bounded_native_repair']=True
 return result

def run(baseline,candidate,proposal_path,label):
 result=evaluate(baseline,candidate,proposal_path,label)
 output=candidate/f'acceptance-{label}.json'
 if output.exists():raise ValueError('do not overwrite acceptance')
 output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps(result))
if __name__=='__main__':run(Path(sys.argv[1]),Path(sys.argv[2]),Path(sys.argv[3]),sys.argv[4])
