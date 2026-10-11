"""Project retained exact-board native endpoints; never run or substitute native gates.

Usage: python3 recover_endpoints.py /path/to/full-artifacts
Directory contains jl117.zip, jr129.zip, k1402.zip and metadata paths described below.
GitHub artifact IDs/digests in accepted-artifacts.json are the durable inputs.
"""
import hashlib,json,pathlib,sys,zipfile
O=pathlib.Path(__file__).resolve().parent
sha=lambda b:hashlib.sha256(b).hexdigest()
canonical=lambda d:json.dumps(d,sort_keys=True,separators=(',',':')).encode()
def write(p,d):p.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
def main(root):
 baseline=json.loads((O/'baseline.json').read_text()); artifacts=json.loads((O/'accepted-artifacts.json').read_text())
 for key,label,board in [('JL','jl117','osc-jack-left'),('JR','jr129','osc-jack-right'),('K','k1402','osc-core')]:
  metadata=artifacts[key]; path=root/(label+'.zip'); raw=path.read_bytes(); assert len(raw)==metadata['size_in_bytes'];assert sha(raw)==metadata['digest'].removeprefix('sha256:'); del raw
  with zipfile.ZipFile(path) as z:
   prefix=f'.circuit-cache/{board}-grid-shards-fresh/'; raw=z.read(prefix+'dump.json');d=json.loads(raw); b=baseline['boards'][key];assert sha(raw)==b['dump_sha256'];assert d['board_sha256']==b['settled_sha256'];assert sha(z.read(prefix+board+'.kicad_pcb'))==b['settled_sha256'];assert d['open_edges']==b['open_edges']
   pads={p['uuid']:p for p in d['pads']}; nets={}
   for net,groups in d['islands'].items():
    if len(groups)<2:continue
    rows=[]
    for group in groups:
     rows.append({'all_member_count':len(group),'all_sorted_members_sha256':sha(canonical(sorted(group))),'pads':[{k:pads[u][k] for k in ['uuid','ref','pad','net','xy','layers']} for u in group if u in pads]})
    nets[net]=rows
   assert {n:len(gs)-1 for n,gs in nets.items()}==b['open_by_net']
   context={n[len(prefix):]:sha(z.read(n)) for n in z.namelist() if n.startswith(prefix) and (n.endswith(('.kicad_sch','.kicad_dru','.kicad_pro')) or n.rsplit('/',1)[-1] in ['sym-lib-table','fp-lib-table'])}
   result={'status':'RECOVERED retained native topology; no fresh native execution','artifact_id':metadata['id'],'run_id':metadata['workflow_run']['id'],'source_sha':metadata['workflow_run']['head_sha'],'archive_digest':metadata['digest'],'member':prefix+'dump.json','dump_sha256':b['dump_sha256'],'settled_board_sha256':b['settled_sha256'],'native_open_edges':d['open_edges'],'disconnected_nets':nets,'context_files':context,'context_file_manifest_sha256':sha(canonical(context)),'context_digest_definition':'SHA256 of sorted-key compact JSON mapping artifact workspace-relative context file paths to byte SHA256; not a substitute for native validator context authentication','group_digest_definition':'SHA256 of compact JSON sorted complete member UUID list. Full lists remain in exact retained ZIP dump; pads above preserve all unresolved pad endpoints.'}
   name=f'{key.lower()}-endpoints.json';write(O/name,result);b['endpoint_memberships']={'status':'RECOVERED from digest-verified exact settled native artifact','path':name,'sha256':sha((O/name).read_bytes())};b['dump_status']='Full retained fresh dump downloaded; digest and exact settled board binding verified';b['native_context_files']=context;b['native_context_digest']=result['context_file_manifest_sha256'];b['context_status']=result['context_digest_definition'];b['native_artifact_id']=metadata['id'];print(key,d['open_edges'],len(nets),'disconnected nets',sum(len(g['pads']) for gs in nets.values() for g in gs),'pad endpoints')
 write(O/'baseline.json',baseline)
if __name__=='__main__':main(pathlib.Path(sys.argv[1]))
