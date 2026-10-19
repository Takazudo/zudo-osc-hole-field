"""Audit rejected experiments without promoting them to accepted routing."""
from pathlib import Path
from collections import Counter
import json,sys
import accept as a

def projected(old,new):
 a.validate_snapshot(old);a.validate_snapshot(new)
 retained=set(old['objects'])
 if not retained<=set(new['objects']) or any(new['objects'][k]!=v for k,v in old['objects'].items()):raise ValueError('retained objects changed')
 changes={}
 for net,groups in old['groups'].items():
  before={frozenset(g) for g in groups};after={frozenset(set(g)&retained) for g in new['groups'][net]}
  if before!=after:
   changes[net]={'before_sizes':sorted(map(len,before)),'after_sizes':sorted(map(len,after)), 'after_components':[{'size':len(g),'sha256':a.signature(sorted(g)),'pads':sorted(v['ref']+':'+v['pin'] for k in g if (v:=old['objects'][k]).get('kind')=='pad')} for g in sorted(after,key=lambda g:(len(g),sorted(g)))]}
 return changes

def run():
 root=a.ROOT;cache=root/'.circuit-cache';baseline=cache/'stage49-fresh';old=a.read(baseline/'connectivity-passfresh.json');p=a.read(a.HERE/'proposal.json');out={'accepted_repair':False,'baseline_head':'8b204afe0e97d45fc3417ef2782ab005994698e1','baseline_board_sha256':a.BASE,'trials':{}}
 sys.path.insert(0,str(root/'design/architecture-278/implementation/stage44/b2-specific'))
 from drc_run import validate,dependencies
 before_board=baseline/'osc-jack-left.kicad_pcb'
 if a.sha(before_board)!=a.BASE or old['board_sha256']!=a.BASE:raise ValueError('baseline snapshot binding')
 base_report=baseline/'drc-passfresh.json'
 validate(base_report.relative_to(root),a.read(baseline/'drc-passfresh.json.execution.json'),a.BASE,dependencies(before_board))
 for name,label in [('trial1','pass1'),('seed','seed')]:
  folder=cache/('stage51-'+name);board=folder/'osc-jack-left.kicad_pcb';snapshot=folder/f'connectivity-{label}.json';report=folder/f'drc-{label}.json';receipt=folder/f'drc-{label}.json.execution.json'
  new=a.read(snapshot);d=a.read(report)
  if new['board_sha256']!=a.sha(board):raise ValueError('snapshot binding')
  validate(report.relative_to(root),a.read(receipt),a.sha(board),dependencies(board))
  if dependencies(board)!=dependencies(baseline/'osc-jack-left.kicad_pcb'):raise ValueError('dependency drift')
  q=p if name=='trial1' else {**p,'copper':p['copper'][:2]}
  raw=board.read_text();a.exact_added_properties(raw,q)
  before,after=a.inventory((baseline/'osc-jack-left.kicad_pcb').read_text()),a.inventory(raw)
  ids={r['uuid'] for r in q['copper']};allowed=[list(k) for k,n in after['copper'].items() if k[1] in ids for _ in range(n)]
  identity=a.compare(before,after,[],allowed)
  if not all(identity['checks'].values()) or not a.structure_matches(before,after,{}):raise ValueError('identity drift')
  changes=projected(old,new)
  if name=='trial1':
   if set(changes)!={a.NET,'-12V'} or new['native_open_edges']!=117:raise ValueError('unexpected trial failure')
   try:a.connectivity(old,new,p)
   except ValueError as e:rejection=str(e)
   else:raise ValueError('false acceptance')
   if rejection!='unexpected partition: -12V':raise ValueError(rejection)
  else:
   if changes or new['native_open_edges']!=116:raise ValueError('seed partition drift')
   rejection='incomplete seed; no target closure'
  out['trials'][name]={'accepted':False,'rejection':rejection,'identity':identity,'all_footprints_unchanged':True,'retained_partition_changes':changes,'objects':len(new['objects']),'opens':new['native_open_edges'],'rule_errors':sum(v['severity']=='error' for v in d['violations']),'parity':len(d['schematic_parity']),'warnings':dict(Counter(v['type'] for v in d['violations'] if v['severity']=='warning')),'bindings':{str(f.relative_to(root)):a.sha(f) for f in [board,snapshot,report,receipt]}}
  for f in [report,receipt]:
   retained=a.HERE/'evidence'/f'{name}-{f.name}'
   if '--check' in sys.argv:
    if retained.read_bytes()!=f.read_bytes():raise ValueError('retained native report drift')
   else:retained.write_bytes(f.read_bytes())
 return out
if __name__=='__main__':
 result=run();text=json.dumps(result,indent=2,sort_keys=True)+'\n'
 if '--check' in sys.argv:
  if text!=(a.HERE/'audit.json').read_text():raise ValueError('audit replay drift')
 else:(a.HERE/'audit.json').write_text(text)
 print('PASS rejected-trial audit; no accepted repair')
