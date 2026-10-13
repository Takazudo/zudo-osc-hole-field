#!/usr/bin/env python3
"""The single sealed post-t2 pilot construction for one board (separate candidate record P1).

Refuses unless the preflight file matches its seal (SHA-256 recorded with an independent
geometry-review verdict of PASS) and the t2 inputs match the preflight's bound hashes.
Adds only the sealed face segments (no drill, move, removal, layer change or relaxed
clearance), then re-runs the complete caps -> clipped sheets -> graph -> census chain.
Credit is the census difference alone: newly closed pads, with zero newly disconnected.
"""
import argparse,hashlib,json,subprocess,sys,time,uuid
from pathlib import Path
HERE=Path(__file__).resolve().parent
NS=uuid.UUID('e16acce5-0000-5000-8000-000000000242')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def need(c,m):
 if not c:raise SystemExit('pilot: '+m)
def main():
 p=argparse.ArgumentParser()
 for k in ['preflight','seal','source','graph','census','python','output']:p.add_argument('--'+k,required=True)
 a=p.parse_args();out=Path(a.output);need(out.is_absolute() and not out.exists(),'fresh absolute OUTDIR');start=time.monotonic()
 seal=json.loads(Path(a.seal).read_text());pre=json.loads(Path(a.preflight).read_text())
 need(seal['preflight_sha256']==sha(a.preflight),'preflight differs from its seal')
 need(seal.get('geometry_review',{}).get('verdict')=='PASS','no independent geometry review PASS recorded in the seal')
 need(pre['legal'] and pre['proposal'],'sealed preflight has no legal corridor')
 need(pre['input_sha256']['graph']==sha(a.graph) and pre['input_sha256']['census']==sha(a.census),'t2 graph/census differ from the preflight')
 source=json.loads(Path(a.source).read_text());need(source['board']==pre['board'],'board')
 pr=pre['proposal'];L=pre['limits'];pts=pr['path_mm']
 need(pr['length_mm']<=L['max_length_mm'] and pr['segments']<=L['max_segments'] and pr['width_mm'] in L['widths_mm'],'proposal outside its sealed limits')
 key=f'pilot-p1:{pre["board"]}:{pre["target"]["pad_id"]}'
 new=[{'id':str(uuid.uuid5(NS,f'{key}:{n}')),'kind':'segment','net':pre['net'],'layers':[pr['face']],'path_mm':[list(u),list(v)],'width_mm':pr['width_mm'],
       'access_for_pad':pre['target']['pad_id'],'epoch':'E16-P1','method':'pilot_orphan_component_feed','pilot_start_object':pr['start_object'],'pilot_end_object':pr['end_object']}
      for n,(u,v) in enumerate(zip(pts,pts[1:]))]
 ids=[o['id'] for o in source['objects']]+[o['id'] for o in new];need(len(ids)==len(set(ids)),'pilot ids collide')
 out.mkdir(parents=True);cand=dict(source,objects=source['objects']+new,parent_sha256=sha(a.source),pilot={'seal_sha256':sha(a.seal),'preflight_sha256':sha(a.preflight)})
 src=out/f'{pre["board"]}-p1-source.json';src.write_text(json.dumps(cand,indent=1)+'\n')
 ev=out/'eval';r=subprocess.run([a.python,str(HERE/'evaluate_access.py'),'--source',str(src),'--clip-helper',str(HERE/'clip_sheets.py'),'--design',str(HERE/'evidence/board-access-design.json'),
                                 '--python',a.python,'--output',str(ev)],cwd=HERE,capture_output=True,text=True)
 need(r.returncode==0,'re-evaluation failed: '+r.stderr[-800:])
 before={u['pad_id']:u for u in json.loads(Path(a.census).read_text())['unresolved']};after={u['pad_id'] for u in json.loads((ev/'port-obligations.json').read_text())['unresolved']}
 closed=sorted(set(before)-after);broken=sorted(after-set(before))
 res={'schema':'e16-pilot-p1-v1','board':pre['board'],'net':pre['net'],'target':pre['target'],'added_objects':new,'parent_t2_source_sha256':sha(a.source),'p1_source_sha256':sha(src),
      'seal_sha256':sha(a.seal),'evaluation':json.loads((ev/'evaluation.json').read_text()),'closed_pads':[{'pad_id':x,'ref':before[x]['ref'],'pad':before[x]['pad'],'net':before[x]['net'],'direct_load':before[x]['direct_load']} for x in closed],
      'newly_disconnected':broken,'credited':bool(closed) and not broken,'direct_loads_closed':sum(before[x]['direct_load'] for x in closed),
      'unresolved_before':len(before),'unresolved_after':len(after),'elapsed_seconds':round(time.monotonic()-start,2),'native_calls':0,'accepted':False,
      'note':'Separate post-t2 candidate record; t2 receipts and models are unchanged.'}
 (out/'pilot-result.json').write_text(json.dumps(res,indent=1)+'\n');print(json.dumps({k:res[k] for k in ['board','net','credited','direct_loads_closed','unresolved_before','unresolved_after']}|{'closed':len(closed),'newly_disconnected':len(broken)}))
 sys.exit(0 if not broken else 1)
if __name__=='__main__':main()
