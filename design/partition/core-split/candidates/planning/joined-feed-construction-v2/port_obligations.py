#!/usr/bin/env python3
"""Reconcile every actual four-rail pad, independent of the IC current roster."""
import argparse,hashlib,json
from collections import Counter
from pathlib import Path
NETS={'AGND','+12V','-12V','+5V'}
def need(c,m):
 if not c:raise ValueError(m)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--board',type=Path,required=True);p.add_argument('--planes',type=Path,required=True);p.add_argument('--graph',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 need(not a.output.exists(),'fresh output required')
 seals={str(q):sha(q) for q in [a.board,a.planes,a.graph,Path(__file__)]}
 source,planes,graph=[json.loads(q.read_text()) for q in [a.board,a.planes,a.graph]]
 need(graph['board']==source['board']==planes['board'],'one board epoch')
 need(all(graph['input_sha256'].get(str(q))==sha(q) for q in [a.board,a.planes]),'graph binds exact normalized and clipped inputs')
 objects=[o for o in source['objects']+planes['new_objects'] if o['kind']=='pad' and o.get('net') in NETS]
 byid={o['id']:o for o in objects};ports={r['id']:r for r in graph['physical_ports']}
 need(len(byid)==len(objects) and len(ports)==len(graph['physical_ports']) and set(byid)==set(ports),'complete unique physical pad census')
 direct={r['pad_id'] for r in source['loads']};rows=[]
 for identity,pad in sorted(byid.items()):
  r=ports[identity];need(all(r.get(k)==pad.get(k) for k in ['ref','pad','net']),'graph/source pad identity mismatch')
  if not r['all_port_fragments_connected_to_feed']:
   rows.append({'pad_id':identity,'ref':r['ref'],'pad':r['pad'],'net':r['net'],'direct_load':identity in direct,'component_ids':r['component_ids']})
 out={'status':'ALL_EXISTING_FOUR_RAIL_PHYSICAL_PAD_OBLIGATIONS','board':source['board'],'input_sha256':seals,'graph_sha256':sha(a.graph),'physical_pad_count':len(objects),'unresolved':rows,'counts_by_net':dict(Counter(r['net'] for r in rows)),'direct_loads':sum(r['direct_load'] for r in rows),'supplemental':sum(not r['direct_load'] for r in rows),'current_allocation':'Unassigned by this structural census. DNP copper remains a passive connectivity obligation, with no invented active injection.','accepted':False,'native_calls':0}
 need(all(sha(Path(q))==h for q,h in seals.items()),'source changed')
 a.output.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:out[k] for k in ['board','physical_pad_count','counts_by_net','direct_loads','supplemental']}))
if __name__=='__main__':main()
