#!/usr/bin/env python3
"""Compare an independent E16 replay with the retained receipts by content; fail closed.

Execution seals bind absolute paths, so byte hashes are run-local. Only the
documented seal fields (SEALS) are excluded. For every requested round this checks:

- exact unresolved pad identities (not only counts) against the retained
  per-round evidence: each round's retained access report lists exactly the
  residuals of its input census, r3/t2 retain full obligations, and r4+ retain
  cumulative closed identities;
- zero newly disconnected identities;
- the previous round's objects as an exact prefix, unique ids, and an append-only delta;
- the round's added objects against the retained delta bundle of its span
  (r1-r3: K?-access-delta.json.gz, r4-t2: K?-access-delta-r4-t2.json.gz), each
  span composed exactly once, and the round's access report against the retained one;
- the final round's full graph, physical ports and complete census.

Clipped sheets and caps are not retained as files, so their geometry is compared
only through graph/census equality. Any mismatch or missing evidence exits nonzero.
"""
import argparse,gzip,hashlib,json,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent
SEALS={'input_sha256','parent_sha256','output_sha256','elapsed_seconds','peak_KiB','graph_sha256'}
ROUNDS=['r1','r2','r3','r4','t1','t2']
SPANS={'K-access-delta.json.gz':['r1','r2','r3'],'K-access-delta-r4-t2.json.gz':['r4','t1','t2']}
SUCCESS={'PLACED','ROUTED','ROUTED_FED_TRANSITION'}
# Retained r1/r2 reports predate later construct_access.py report fields (index.json method_note).
# Only these exact replay-side additions, with these exact values, are removed before comparison.
LEGACY_REPORT_ADDITIONS={'r1':{'top':{'method':'via'},'parameters_mm':{'route_widths':[0.25,0.2],'route_pitch':0.05,'route_half_window':3.0},'result':{}},
                         'r2':{'top':{},'parameters_mm':{},'result':{'new_via':False}}}
class Mismatch(Exception):pass
def need(c,m):
 if not c:raise Mismatch(m)
def load(p):
 need(p.exists(),f'missing evidence: {p}')
 return json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_text())
def strip(d):return {k:v for k,v in d.items() if k not in SEALS}
def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def legacy_normalized(r,rep,rrep):
 """Remove the documented later-revision additions; return (report, removed-field record)."""
 add=LEGACY_REPORT_ADDITIONS.get(r)
 if not add:return rep,[]
 rep=dict(rep);removed=[]
 for k,v in add['top'].items():
  if k not in rrep and rep.get(k)==v:rep.pop(k);removed.append(k)
 if add['parameters_mm']:
  pm=dict(rep['parameters_mm'])
  for k,v in add['parameters_mm'].items():
   if k not in rrep['parameters_mm'] and pm.get(k)==v:pm.pop(k);removed.append('parameters_mm.'+k)
  rep['parameters_mm']=pm
 if add['result']:
  out=[]
  for x in rep['results']:
   x=dict(x)
   for k,v in add['result'].items():
    if k in x and x[k]==v:x.pop(k);removed.append('results[].'+k)
   out.append(x)
  rep['results']=out
 return rep,sorted(set(removed))
def span_of(r):return next(f for f,rs in SPANS.items() if r in rs)
def retained_deltas(board,ev,rounds,normalized_ids):
 """Each span's retained bundle, validated and composed once."""
 out={};seen=set(normalized_ids)
 for f,rs in SPANS.items():
  if not set(rs)&set(rounds):continue
  objs=load(ev/f.replace('K-',board+'-',1));ids=[o['id'] for o in objs]
  need(isinstance(objs,list) and objs,f'{f}: empty or malformed delta bundle')
  need(len(ids)==len(set(ids)),f'{f}: duplicate object ids in retained delta')
  need(not set(ids)&seen,f'{f}: retained delta reuses an existing or earlier-span id')
  seen|=set(ids);out[f]={o['id']:o for o in objs}
 return out
def expected_residuals(board,ev,idx,rounds):
 """Retained residual identity set per round, each derived from that round's own evidence."""
 rep=lambda r:{x['pad_id'] for x in load(ev/f'{board}-access-{r}-report.json.gz')['results']}
 obl=lambda r:{x['pad_id'] for x in load(ev/f'{board}-{r}-port-obligations.json')['unresolved']}
 closed=lambda r:{x['pad_id'] for x in idx['rounds'][r]['closed_identities']}
 exp={'base':rep('r1')}
 if 'r1' in rounds:exp['r1']=rep('r2')
 if 'r2' in rounds:exp['r2']=rep('r3')
 if 'r3' in rounds:
  exp['r3']=obl('r3');need(exp['r3']==rep('r4'),'retained r3 obligations differ from the r4 input residuals')
 if 'r4' in rounds:exp['r4']=obl('r3')-closed('r4')
 if 't1' in rounds:
  exp['t1']=exp.get('r4',obl('r3')-closed('r4'))-closed('t1');need(exp['t1']==rep('t2'),'retained t1 residuals differ from the t2 input residuals')
 if 't2' in rounds:
  exp['t2']=obl('t2');need(exp['t2']==exp.get('t1',rep('t2'))-closed('t2'),'retained t2 obligations differ from t1 minus t2 closures')
 return exp
def compare(board,run,ev,rounds):
 need(rounds and rounds==ROUNDS[:len(rounds)],'rounds must be a prefix of '+','.join(ROUNDS))
 idx=load(ev/'index.json')['boards'][board];norm=load(run/f'{board}-normalized.json');base_ids=[o['id'] for o in norm['objects']]
 need(len(base_ids)==len(set(base_ids)),'normalized object ids are not unique')
 deltas=retained_deltas(board,ev,rounds,base_ids);exp=expected_residuals(board,ev,idx,rounds)
 checks={'normalized_objects':{'objects':len(norm['objects']),'loads':len(norm['loads']),'content_sha256':digest(strip(norm))},
         'retained_delta_spans':{f:len(d) for f,d in deltas.items()}}
 rows={};prev=None;before=norm['objects'];added_by_span={f:{} for f in deltas}
 for r in ['base']+rounds:
  e=load(run/f'{board}-eval-{r}/evaluation.json');ret=idx['rounds'][r]
  now={x['pad_id'] for x in load(run/f'{board}-eval-{r}/port-obligations.json')['unresolved']}
  row={'counts_equal':[e['unresolved_physical_pad_count'],e['unresolved_direct_load_count'],e['unresolved_supplemental_count']]==[ret['unresolved'],ret['direct'],ret['supplemental']],
       'unresolved':len(now),'residual_identities_equal':now==exp[r],
       'identities_missing_from_replay':sorted(exp[r]-now),'identities_extra_in_replay':sorted(now-exp[r]),
       'newly_disconnected':sorted(now-prev) if prev is not None else []}
  if r!='base':
   src=load(run/f'{board}-access-{r}.json');ids=[o['id'] for o in src['objects']];added=src['objects'][len(before):]
   row['source_objects_prefix_preserved']=src['objects'][:len(before)]==before
   row['object_ids_unique']=len(ids)==len(set(ids))
   f=span_of(r);span=deltas[f]
   row['added_objects']=len(added)
   row['added_objects_in_own_span_delta']=all(span.get(o['id'])==o for o in added)
   row['added_ids_new_in_span']=not any(o['id'] in added_by_span[f] for o in added)
   added_by_span[f].update((o['id'],o) for o in added)
   placed={x['pad_id'] for x in load(ev/f'{board}-access-{r}-report.json.gz')['results'] if x['status'] in SUCCESS}
   row['added_objects_serve_round_successes']={o.get('access_for_pad') for o in added}<=placed
   rep,rrep=load(run/f'{board}-access-{r}-report.json'),load(ev/f'{board}-access-{r}-report.json.gz')
   rep,legacy=legacy_normalized(r,rep,rrep)
   row['access_report_equal_excluding_seals']=strip(rep)==strip(rrep)
   if legacy:row['documented_legacy_report_fields_removed']=legacy
   before=src['objects']
  rows[r]=row;prev=now
 # Every requested span is composed exactly: the added objects across its rounds equal the retained bundle.
 for f,rs in SPANS.items():
  if f in deltas and set(rs)<=set(rounds):checks[f'span_{f}_equal']=added_by_span[f]==deltas[f]
 last=rounds[-1];rg=ev/f'{board}-{last}-port-graph.json.gz'
 need(rg.exists(),f'final round {last} has no retained graph; compare through r3 or t2')
 graph=load(run/f'{board}-eval-{last}/port-graph.json');rgraph=load(rg)
 checks['final_graph_equal_excluding_seals']=strip(graph)==strip(rgraph)
 checks['final_physical_ports_equal']=graph['physical_ports']==rgraph['physical_ports']
 census=load(run/f'{board}-eval-{last}/port-obligations.json');rcensus=load(ev/f'{board}-{last}-port-obligations.json')
 checks['final_census_equal_excluding_seals']=strip(census)==strip(rcensus)
 checks['final_pad_identities']=len(census['unresolved'])
 checks['physical_pad_universe']=census['physical_pad_count']
 flags=[k for k in ('counts_equal','residual_identities_equal','source_objects_prefix_preserved','object_ids_unique','added_objects_in_own_span_delta',
                    'added_ids_new_in_span','added_objects_serve_round_successes','access_report_equal_excluding_seals')]
 failed=[f'{r}.{k}' for r,x in rows.items() for k in flags if x.get(k,True) is not True]+[f'{r}.newly_disconnected' for r,x in rows.items() if x['newly_disconnected']]
 failed+=[k for k,v in checks.items() if isinstance(v,bool) and not v]
 return {'board':board,'rounds_compared':rounds,'rounds':rows,'checks':checks,'failed':failed,'all_equal':not failed}
def main(argv=None):
 p=argparse.ArgumentParser();p.add_argument('--run',type=Path,required=True);p.add_argument('--board',choices=['KA','KB'],required=True)
 p.add_argument('--rounds',default=','.join(ROUNDS));p.add_argument('--evidence',type=Path,default=HERE/'evidence/e16');p.add_argument('--output',type=Path);a=p.parse_args(argv)
 try:out=compare(a.board,a.run.resolve(),a.evidence,a.rounds.split(','))
 except Mismatch as e:out={'board':a.board,'error':str(e),'all_equal':False,'failed':['evidence']}
 out.update(method='content comparison excluding seal fields '+','.join(sorted(SEALS)),native_calls=0)
 text=json.dumps(out,indent=1)+'\n'
 if a.output:a.output.write_text(text)
 print(json.dumps({k:out.get(k) for k in ('board','all_equal','failed','error') if k in out}))
 return 0 if out['all_equal'] else 1
if __name__=='__main__':sys.exit(main())
