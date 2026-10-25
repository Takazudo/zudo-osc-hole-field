#!/usr/bin/env python3
"""Finite-coverage ledger of the E16 adapter over the complete t2 rail-pad census (source-only).

Checks the census invariants against the retained t2 graph/obligations, lists every
obligated source-connected pad (and every feed terminal) with its fragments and finite
component, keeps all structural residuals visible, and cross-checks each port the
2026-10-13 partial model left without a finite path.
"""
import argparse,gzip,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;NETS=['+12V','-12V','+5V','AGND']
def jl(p):
 p=Path(p);return json.loads(gzip.decompress(p.read_bytes()) if p.suffix=='.gz' else p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 p=argparse.ArgumentParser();p.add_argument('--finite',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--ledger',type=Path,required=True);a=p.parse_args()
 old=jl(HERE/'evidence/e16/finite-network-t2-ports.json.gz');rows=[];per={};census={'physical_pads':0,'terminals':0,'originals':0,'structurally_unresolved':0,'source_connected_originals':0}
 for b in ('KA','KB'):
  g=jl(HERE/f'evidence/e16/{b}-t2-port-graph.json.gz');ob=jl(HERE/f'evidence/e16/{b}-t2-port-obligations.json');un={u['pad_id'] for u in ob['unresolved']}
  census['physical_pads']+=len(g['physical_ports']);census['terminals']+=sum(x['id'].startswith('CS247-') for x in g['physical_ports'])
  census['structurally_unresolved']+=len(un)
  for net in NETS:
   c=jl(a.finite/b/f'coverage-{net}.json.gz');solved=old[f'{b}|{net}|all']
   orig=[r for r in c['rows'] if not r['terminal']];conn=[r for r in orig if r['obligated']]
   need_ids={x['id'] for x in g['physical_ports'] if x['net']==net};mine={r['pad_id'] for r in c['rows']}
   assert need_ids==mine,f'{b} {net}: coverage rows differ from the t2 graph census'
   assert {r['pad_id'] for r in orig if r['structurally_unresolved']}=={x for x in un if x in need_ids},'residuals differ'
   old_missing=sorted(r['pad_id'] for r in conn if r['pad_id'] not in solved)
   per[f'{b}|{net}']={'rail_pads':len(c['rows']),'originals':len(orig),'structurally_unresolved':len(orig)-len(conn),'source_connected':len(conn),
                      'terminals':sum(r['terminal'] for r in c['rows']),'terminals_with_finite_path':sum(r['terminal'] and r['finite_path_to_feed'] for r in c['rows']),
                      'obligated_without_finite_path':c['obligated_without_finite_path'],'partial_model_omissions':len(old_missing),
                      'partial_model_omissions_now_covered':sum(1 for x in old_missing if x not in c['obligated_without_finite_path']),
                      'finite_components':c['finite_components'],'mesh':c['mesh'],'operator_desc_sha256':c['desc_sha256'],'coverage_sha256':sha(a.finite/b/f'coverage-{net}.json.gz')}
   census['originals']+=len(orig);census['source_connected_originals']+=len(conn)
   for r in c['rows']:rows.append(dict(r,board=b,net=net,partial_model_omission=r['pad_id'] in old_missing))
 missing=[(k,x) for k,v in per.items() for x in v['obligated_without_finite_path']]
 out={'schema':'e16-finite-coverage-v1','round':'t2','census':census,'per_board_net':per,
      'obligated_without_finite_path':missing,'status':'COMPLETE: every obligated source-connected pad and every feed terminal has a finite path' if not missing else 'INCOMPLETE',
      'partial_model_omissions':sum(v['partial_model_omissions'] for v in per.values()),'partial_model_omissions_now_covered':sum(v['partial_model_omissions_now_covered'] for v in per.values()),
      'criterion':'A pad is covered when its whole finite support (uniform current over every fed face fragment, or every fed fragment if it has none on a face) lies in a finite component holding a feed terminal support; reaching one node of a split pad is not enough.',
      'residuals_visible':'Structurally unresolved pads stay listed with their fed/unfed fragments; their fed fragments are meshed, their unfed fragments are not and carry no current.',
      'load_ledger_sha256':jl(a.ledger)['ledger_sha256'],'rows_file':a.output.name.replace('.json','-rows.json.gz')}
 a.output.write_text(json.dumps(out,indent=1)+'\n')
 (a.output.parent/out['rows_file']).write_bytes(gzip.compress(json.dumps(rows,sort_keys=True).encode(),mtime=0))
 print(json.dumps({k:out[k] for k in ['census','status','partial_model_omissions','partial_model_omissions_now_covered']}))
if __name__=='__main__':main()
