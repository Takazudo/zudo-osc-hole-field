#!/usr/bin/env python3
"""Compare an independent E16 replay with the retained receipts by content.

Execution seals bind absolute paths, so byte hashes are run-local. This compares
per-round counts and residual identities, every added source object (and the
exact prefix of each previous round), the final graph and the complete pad
census, excluding only seal fields. Clipped sheets and caps are not retained as
files, so their geometry is compared only through graph/census equality.
"""
import argparse,gzip,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent
SEALS={'input_sha256','parent_sha256','elapsed_seconds','peak_KiB','graph_sha256'}
def load(p):return json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_text())
def strip(d):return {k:v for k,v in d.items() if k not in SEALS}
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def compare(board,run,ev,rounds):
 idx=load(ev/'index.json')['boards'][board];norm=load(run/f'{board}-normalized.json');ids={o['id'] for o in norm['objects']}
 delta=sorted(load(ev/f'{board}-access-delta.json.gz'),key=lambda o:o['id'])
 checks={'normalized_objects':{'objects':len(norm['objects']),'loads':len(norm['loads']),'content_sha256':digest(strip(norm))}}
 prev=None;rows={};before=norm['objects']
 for r in ['base']+rounds:
  e=load(run/f'{board}-eval-{r}/evaluation.json');ret=idx['rounds'][r]
  now={x['pad_id'] for x in load(run/f'{board}-eval-{r}/port-obligations.json')['unresolved']}
  rows[r]={'counts_equal':[e['unresolved_physical_pad_count'],e['unresolved_direct_load_count'],e['unresolved_supplemental_count']]==[ret['unresolved'],ret['direct'],ret['supplemental']],
           'unresolved':e['unresolved_physical_pad_count'],'newly_disconnected':sorted(now-prev) if prev is not None else []}
  if r!='base':
   src=load(run/f'{board}-access-{r}.json');added=[o for o in src['objects'] if o['id'] not in ids]
   rows[r]['source_objects_prefix_preserved']=src['objects'][:len(before)]==before
   rows[r]['object_ids_unique']=len({o['id'] for o in src['objects']})==len(src['objects']);before=src['objects']
   rows[r]['added_objects_subset_of_retained_delta']=all(o in delta for o in added)
   rows[r]['added_objects']=len(added)
  prev=now
 last=rounds[-1];src=load(run/f'{board}-access-{last}.json');added=sorted([o for o in src['objects'] if o['id'] not in ids],key=lambda o:o['id'])
 checks['final_delta_equal']=added==delta
 graph=load(run/f'{board}-eval-{last}/port-graph.json');rgraph=load(ev/f'{board}-{last}-port-graph.json.gz')
 checks['final_graph_equal_excluding_seals']=strip(graph)==strip(rgraph)
 checks['final_physical_ports_equal']=graph['physical_ports']==rgraph['physical_ports']
 census=load(run/f'{board}-eval-{last}/port-obligations.json');rcensus=load(ev/f'{board}-{last}-port-obligations.json')
 checks['final_census_equal_excluding_seals']=strip(census)==strip(rcensus)
 checks['final_pad_identities']=len(census['unresolved'])
 checks['physical_pad_universe']=census['physical_pad_count']
 return {'board':board,'rounds':rows,'checks':checks,'all_equal':all(v for k,v in checks.items() if isinstance(v,bool)) and all(x['counts_equal'] and not x['newly_disconnected'] and x.get('source_objects_prefix_preserved',True) and x.get('object_ids_unique',True) and x.get('added_objects_subset_of_retained_delta',True) for x in rows.values())}
def main():
 p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--board',choices=['KA','KB'],required=True)
 p.add_argument('--rounds',default='r1,r2,r3');p.add_argument('--evidence',type=Path,default=HERE/'evidence/e16');p.add_argument('--output',type=Path);a=p.parse_args()
 out=compare(a.board,a.run.resolve(),a.evidence,a.rounds.split(','))
 out.update(method='content comparison excluding seal fields '+','.join(sorted(SEALS)),native_calls=0)
 text=json.dumps(out,indent=1)+'\n'
 if a.output:a.output.write_text(text)
 print(text)
if __name__=='__main__':main()
