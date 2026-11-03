"""Bind rejected native replay without mutating evidence in check mode."""
from pathlib import Path
import json,sys,importlib.util
_spec=importlib.util.spec_from_file_location("stage52_audit_accept",Path(__file__).with_name("accept.py"));a=importlib.util.module_from_spec(_spec);_spec.loader.exec_module(a)

def retain(source,target,check):
 if check:
  if source.read_bytes()!=target.read_bytes():raise ValueError('retained evidence drift')
 else:target.write_bytes(source.read_bytes())
def changes(old,new):
 a.validate_snapshot(old);a.validate_snapshot(new);retained=set(old['objects'])
 if not retained<=set(new['objects']) or any(new['objects'][k]!=v for k,v in old['objects'].items()):raise ValueError('retained objects')
 result={}
 for net,groups in old['groups'].items():
  before={frozenset(g) for g in groups};after={frozenset(set(g)&retained) for g in new['groups'][net]}
  if before!=after:result[net]={'before_sizes':sorted(map(len,before)),'after_sizes':sorted(map(len,after)),'after_hashes':sorted(a.signature(sorted(g)) for g in after),'small_after_pad_groups':[sorted(old['objects'][k]['ref']+':'+old['objects'][k]['pin'] for k in g if old['objects'][k]['kind']=='pad') for g in sorted(after,key=lambda g:(len(g),sorted(g))) if len(g)<100]}
 return result

def run(check=False):
 root=a.ROOT;base=root/'.circuit-cache/stage49-fresh';before=base/'osc-jack-left.kicad_pcb';old=a.read(base/'connectivity-passfresh.json');proposal=a.read(a.HERE/'trial1-proposal.json')
 if a.sha(before)!=a.BASE or old['board_sha256']!=a.BASE:raise ValueError('baseline binding')
 sys.path.insert(0,str(root/'design/architecture-278/implementation/stage44/b2-specific'))
 from drc_run import validate,dependencies
 validate((base/'drc-passfresh.json').relative_to(root),a.read(base/'drc-passfresh.json.execution.json'),a.BASE,dependencies(before))
 out={'accepted_repair':False,'baseline_sha256':a.BASE,'proposal_sha256':a.sha(a.HERE/'trial1-proposal.json'),'trials':{}}
 for name,label in [('trial1','pass1'),('replay','passfresh')]:
  folder=root/('.circuit-cache/stage52-'+name);board=folder/'osc-jack-left.kicad_pcb';snapshot=folder/f'connectivity-{label}.json';report=folder/f'drc-{label}.json';receipt=folder/f'drc-{label}.json.execution.json';new=a.read(snapshot);drc=a.read(report)
  if new['board_sha256']!=a.sha(board):raise ValueError('snapshot binding')
  validate(report.relative_to(root),a.read(receipt),a.sha(board),dependencies(board))
  if dependencies(before)!=dependencies(board):raise ValueError('dependency drift')
  identity=a.identity(before.read_text(),board.read_text(),proposal)
  diff=changes(old,new)
  if set(diff)!={'-12V','AGND',a.NET} or diff['-12V']['after_sizes']!=[38,977] or diff[a.NET]['after_sizes']!=[51]:raise ValueError('unexpected failure partitions')
  if new['native_open_edges']!=117 or len(drc['unconnected_items'])!=117 or drc['schematic_parity'] or any(v['severity']=='error' for v in drc['violations']):raise ValueError('unexpected DRC result')
  try:a.connectivity(old,new,proposal)
  except ValueError as e:rejection=str(e)
  else:raise ValueError('false acceptance')
  if rejection!='unexpected partition: -12V':raise ValueError(rejection)
  out['trials'][name]={'accepted':False,'rejection':rejection,'identity':identity,'changes':diff,'opens':117,'rule_errors':0,'parity':0,'warnings':sum(v['severity']=='warning' for v in drc['violations']),'warning_gate':a.warning_gate(a.read(base/'drc-passfresh.json'),drc),'bindings':{str(p.relative_to(root)):a.sha(p) for p in [board,snapshot,report,receipt]}}
  for p in [report,receipt]:retain(p,a.HERE/'evidence'/(name+'-'+p.name),check)
 first=root/'.circuit-cache/stage52-trial1';fresh=root/'.circuit-cache/stage52-replay'
 for left,right in [(first/'osc-jack-left.kicad_pcb',fresh/'osc-jack-left.kicad_pcb'),(first/'connectivity-pass1.json',fresh/'connectivity-passfresh.json')]:
  if left.read_bytes()!=right.read_bytes():raise ValueError('native replay not byte exact')
 out['independent_build_board_and_snapshot_identical']=True
 return out
if __name__=='__main__':
 check='--check' in sys.argv;text=json.dumps(run(check),indent=2,sort_keys=True)+'\n';p=a.HERE/'audit.json'
 if check:
  if p.read_text()!=text:raise ValueError('audit replay drift')
 else:p.write_text(text)
 print('PASS deterministic rejected experiment; no accepted repair')
