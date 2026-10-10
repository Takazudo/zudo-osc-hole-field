"""Read-only reconstruction of reviewed core audit packets; never dispatches."""
import sys,json,zipfile,io,argparse
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen import audit_fixture_tasks as a
parser=argparse.ArgumentParser();parser.add_argument('--source-zip',required=True);parser.add_argument('--compact',required=True);parser.add_argument('--metadata',required=True);parser.add_argument('--scratch',required=True);parser.add_argument('--output',required=True);args=parser.parse_args()
root=Path(args.scratch);root.mkdir(exist_ok=True)
if a.SHA(Path(args.source_zip).read_bytes())!='4211d6ae2ebe9861e17ae45f133c8e6318fcbaa74998740aa10ba879d70bd9ef':raise ValueError('saved input ZIP changed')
with zipfile.ZipFile(args.source_zip) as z:
 for label,stage in [('before','start'),('after','fresh')]:
  p=root/label;p.mkdir(exist_ok=True)
  for suffix in ('.kicad_pcb','.kicad_pro','.kicad_dru'):
   name=next(n for n in z.namelist() if n.endswith('osc-core-grid-shards-'+stage+'/osc-core'+suffix));(p/('osc-core'+suffix)).write_bytes(z.read(name))
before=root/'before/osc-core.kicad_pcb';after=root/'after/osc-core.kicad_pcb'
compact=Path(args.compact)
with zipfile.ZipFile(compact) as z:
 d=zipfile.ZipFile(io.BytesIO(z.read(next(n for n in z.namelist() if n.endswith('diagnostics.zip')))));required=json.loads(d.read('zones/required-scope.json'))
kernel=a.policy(Path.cwd());m=a.build_manifest(required,before,after,kernel)
anchor=a.reviewed_legacy_anchor(compact,json.loads(Path(args.metadata).read_text()),Path.cwd(),kernel)
leaves,bindings=a.import_legacy(compact,anchor,m,before,after,kernel)
missing=[t for t in m['tasks'] if t['task_id'] not in leaves]
packets=[[t['task_id'] for t in missing if t['stage']==0][i:i+8] for i in (0,8)]
a.selection(m,leaves,packets)
assert len(m['tasks'])==426 and len(leaves)==235 and len(missing)==191 and len(bindings)==3
out=Path(args.output);out.mkdir(parents=True,exist_ok=True)
a.atomic(out/'manifest.json',m);a.atomic(out/'prior-proof-anchor.json',anchor);a.atomic(out/'native-geometry-bindings.json',bindings)
a.atomic(out/'completed-receipts.json',{k:v['receipt'] for k,v in leaves.items()})
a.atomic(out/'missing-task-ids.json',[t['task_id'] for t in missing])
a.atomic(out/'pilot-plan.json',dict(status='REVIEW REQUIRED; NOT DISPATCHED',packets=packets,max_workers=2,command_seconds=2400,job_minutes=50,maximum_aggregate_rss_kib=12582912,minimum_available_kib=2097152,partial_upload_required=True,output_directories=['shard-0','shard-1'],expected_new_reports=16,expected_total_if_all_pass=251,required_total=426))
print(json.dumps(dict(tasks=len(m['tasks']),completed=len(leaves),missing=len(missing),geometry_bindings=len(bindings),pilot_batches=[[t['batch_index'] for t in m['tasks'] if t['task_id'] in p] for p in packets],manifest_sha256=a.SHA((out/'manifest.json').read_bytes()))))
