import collections,hashlib,json,zipfile
from pathlib import Path
from scripts.pcbgen.netlist import read_netlist
root=Path('/workspace/zudo-osc-hole-field/.circuit-cache/issue189-downloaded');outputs={}
for bid,folder in [('osc-jack-left','jl117-full'),('osc-jack-right','jr129-full'),('osc-core',None)]:
 netlist=Path('schematic/boards')/(bid+'.net');components,_=read_netlist(netlist);refs={c.ref:dict(c.fields) for c in components}
 if folder:raw=(root/folder/'fresh/dump.json').read_bytes()
 else:
  with zipfile.ZipFile('/tmp/issue189-core-supply-terminal.zip') as z:raw=z.read(next(n for n in z.namelist() if n.endswith('osc-core-grid-shards-start/dump.json')))
 d=json.loads(raw);pads={p['uuid']:p for p in d['pads']};buckets=collections.defaultdict(lambda:{'nets':0,'edges':0,'single_pad_components':0,'net_ids':[]})
 for net,groups in d['islands'].items():
  if net in ['AGND','+12V','-12V','+5V']:continue
  ps=[pads[u] for g in groups for u in g if u in pads];blocks=sorted({refs[p['ref']].get('Block','UNKNOWN') for p in ps if not refs[p['ref']].get('Block','UNKNOWN').startswith('INTERFACES_')});label=' + '.join(blocks) or 'INTERFACES_ONLY';b=buckets[label];b['nets']+=1;b['edges']+=len(groups)-1;b['single_pad_components']+=sum(sum(u in pads for u in g)==1 for g in groups);b['net_ids'].append(net)
 rows=[dict(blocks=k,**v) for k,v in buckets.items()];rows.sort(key=lambda r:(-r['edges'],r['blocks']));outputs[bid]={'board_sha256':d['board_sha256'],'dump_sha256':hashlib.sha256(raw).hexdigest(),'netlist_sha256':hashlib.sha256(netlist.read_bytes()).hexdigest(),'status':'ELECTRICAL OWNERSHIP PRIORITIZATION ONLY; ROUTABILITY AND BATCH COMPATIBILITY UNPROVEN','signal_groups':rows}
Path('/tmp/issue189-circuit-batch-assessment.json').write_text(json.dumps(outputs,indent=2)+'\n')
for bid,d in outputs.items():print(bid,[{k:v for k,v in r.items() if k!='net_ids'} for r in d['signal_groups'][:10]])
