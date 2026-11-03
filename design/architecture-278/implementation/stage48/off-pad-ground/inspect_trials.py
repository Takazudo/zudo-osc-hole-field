"""Audit rejected native trials without promoting either to accepted hardware."""
from pathlib import Path
from collections import Counter
import hashlib, importlib.util, json, sys
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
sys.path.insert(0,str(ROOT/'design/architecture-278/implementation/stage41/native-pilot'))
from identity_guard import inventory,compare,structure_matches,top_level_spans,value,kind,digest,copper_contract
sys.path.insert(0,str(ROOT/'design/architecture-278/implementation/stage44/b2-specific'))
from drc_run import validate,dependencies
BASE='d1f79d02ac20ecca28591a1332fd217603ac53ce114bcd4aa1290f78ba3d2b73'
RETIRED={'f3c671af-83ca-560f-8614-5a530082d051','a8007baf-45fa-5fc8-be0d-a0a22bae8b43'}
LED='XA23B6CC73603CD7235D3';TARGET='a6b5c1e1-3b03-53c1-aff3-69160966559d';DANGLING='a63a488c-d65e-5563-90b3-e28bf3a61872'
def require(ok,message):
 if not ok:raise ValueError(message)
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'))
def validate_snapshot(s):
 seen=Counter()
 for net,groups in s['groups'].items():
  for g in groups:
   require(bool(g),'empty group')
   for k in g:
    require(k in s['objects'] and s['objects'][k]['net']==net,'group net')
    seen[k]+=1
 require(seen==Counter({k:1 for k in s['objects']}),'partition inventory')
 require(sum(len(g)-1 for g in s['groups'].values())==s['native_open_edges'],'open count')
def partitions(old,new,proposal,merge):
 validate_snapshot(old);validate_snapshot(new)
 removed={k for k,v in old['objects'].items() if v.get('uuid') in RETIRED}
 require(len(removed)==2,'native retirement')
 retained=set(old['objects'])-removed
 require(retained<=set(new['objects']) and all(old['objects'][k]==new['objects'][k] for k in retained),'retained objects')
 added=set(new['objects'])-retained
 require(len(added)==len(proposal['copper']) and {new['objects'][k]['uuid'] for k in added}=={r['uuid'] for r in proposal['copper']},'addition set')
 source=next(k for k,v in old['objects'].items() if v.get('ref')=='R8270' and v.get('pin')=='2')
 target=next(k for k,v in old['objects'].items() if v.get('uuid')==TARGET)
 sg=next(set(g) for g in old['groups']['AGND'] if source in g);tg=next(set(g) for g in old['groups']['AGND'] if target in g)
 expected={net:[set(g)&retained for g in groups if set(g)&retained] for net,groups in old['groups'].items()}
 require(sg!=tg,'baseline already merged')
 if merge:expected['AGND']=[g for g in expected['AGND'] if g not in [sg,tg]]+[sg|tg]
 require(set(new['groups'])==set(expected),'net set')
 for net,groups in new['groups'].items():
  projected=[set(g)&retained for g in groups]
  require(all(projected) and {frozenset(g) for g in projected}=={frozenset(g) for g in expected[net]},'partition change '+net)
 signal=next(set(g)&retained for g in old['groups'][LED] if next(iter(removed)) in g)
 require(all(any(k in g and set(g)&retained==signal for g in old['groups'][LED]) for k in removed),'retirements in different components')
 for k in added:
  require(new['objects'][k]['net']==LED and any(k in g and set(g)&retained==signal for g in new['groups'][LED]),'addition component')
 require(old['native_open_edges']==117 and new['native_open_edges']==(116 if merge else 117),'expected opens')
 return dict(retained_objects=len(retained),added_objects=len(added),only_intended_ground_merge=merge,all_other_partitions_preserved=True)
def warning_rows(d):
 return Counter((v['type'],tuple(sorted(i['uuid'] for i in v['items']))) for v in d['violations'] if v['severity']=='warning' and v['type'] not in ['silk_overlap','silk_over_copper'])
def drc_gate(old,new,trial):
 require(new['kicad_version']=='10.0.6' and not new['schematic_parity'] and not any(v['severity']=='error' for v in new['violations']),'native rule/parity')
 added=warning_rows(new)-warning_rows(old);removed=warning_rows(old)-warning_rows(new)
 expected=Counter({('via_dangling',(DANGLING,)):1}) if trial==1 else Counter()
 require(added==expected and not removed,'unexpected uncapped warning delta')
 require(len(new['unconnected_items'])==(116 if trial==1 else 117),'DRC opens')
 require(len(new['violations'])==(477 if trial==1 else 476),'violation count')
 return dict(opens=len(new['unconnected_items']),rule_errors=0,parity=0,warnings=len(new['violations']),new_uncapped_warnings=[[k[0],list(k[1])] for k in added],capped_silkscreen_identity_nonregression='UNRESOLVED',accepted=False,reason='new dangling via' if trial==1 else 'intended ground closure absent')
def inspect(trial):
 base=ROOT/'.circuit-cache/stage44-b2-fresh';candidate=ROOT/f'.circuit-cache/stage48-trial{trial}'
 proposal=read(HERE/f'evidence/trial{trial}-proposal.json');before=base/'osc-jack-left.kicad_pcb';after=candidate/'osc-jack-left.kicad_pcb'
 require(sha(before)==BASE==proposal['board_sha256'] and set(proposal['removed_uuids'])==RETIRED and len(proposal['removed_uuids'])==2,'baseline/scope')
 raw=before.read_text();retired=[]
 for a,b in top_level_spans(raw):
  block=raw[a:b]
  if kind(block)=='segment' and value(block,'uuid') in RETIRED:
   require(kind(block)=='segment' and value(block,'net')==LED,'retirement contract');retired.append(digest(block))
 old_inv,new_inv=inventory(raw),inventory(after.read_text());newids={r['uuid'] for r in proposal['copper']}
 def contract(r):
  g=[r['start_nm'],r['end_nm'],[r['width_nm']],r['layer']] if r['kind']=='segment' else [r['at_nm'],[r['diameter_nm']],[r['drill_nm']],['F.Cu','B.Cu']]
  return [r['kind'],r['uuid'],g,r['net']]
 actual=Counter(canonical(k) for k,n in new_inv['native_contract'].items() if k[1] in newids for _ in range(n))
 require(actual==Counter(canonical(contract(r)) for r in proposal['copper']),'new copper geometry')
 allowed=[list(k) for k,n in new_inv['copper'].items() if k[1] in newids for _ in range(n)]
 identity=compare(old_inv,new_inv,retired,allowed);identity['checks']['all_footprints_unchanged']=structure_matches(old_inv,new_inv,{})
 require(all(identity['checks'].values()),'identity preservation')
 old=read(base/'connectivity-passfresh.json');new=read(candidate/'connectivity-pass1.json')
 require(old['board_sha256']==sha(before) and new['board_sha256']==sha(after) and new['version']=='10.0.6','snapshot binding')
 part=partitions(old,new,proposal,trial==1)
 report=candidate/'drc-pass1.json';execution=read(Path(str(report)+'.execution.json'))
 # The execution used repository-relative paths; preserve those exact receipt bindings.
 relative=report.relative_to(ROOT)
 validate(relative,execution,sha(after),dependencies(after))
 require(dependencies(before)==dependencies(after),'dependency preservation')
 drc=drc_gate(read(base/'drc-passfresh.json'),read(report),trial)
 bindings={str(p.relative_to(ROOT)):sha(p) for p in [before,after,base/'connectivity-passfresh.json',candidate/'connectivity-pass1.json',report,Path(str(report)+'.execution.json'),HERE/f'evidence/trial{trial}-proposal.json']}
 return dict(trial=trial,identity=identity,partitions=part,drc=drc,bindings=bindings)
if __name__=='__main__':
 for trial in [1,2]:
  result=inspect(trial);out=HERE/f'evidence/trial{trial}-audit.json'
  if '--write' in sys.argv:out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
  else:require(read(out)==result,'audit replay')
  print(json.dumps({'trial':trial,**result['drc']}))
