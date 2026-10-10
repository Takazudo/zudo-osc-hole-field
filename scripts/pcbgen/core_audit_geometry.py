"""Pinned-native read-only geometry bootstrap. No refill, save or DRC tasks."""
import argparse,json,subprocess,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.pcbgen import audit_fixture_tasks as a
TARGET=('e389d344-872d-538e-9bfc-39577adb1686','B.Cu',1)
def references(m):
 refs={}
 for t in m['tasks']:
  key=(t['zone_uuid'],t['layer'],t['stage']);refs[key]=t['expected_geometry']
 if len(refs)!=4 or TARGET not in refs:raise ValueError('exact four native geometry references required')
 return refs
def snapshot(m,before,after,kernel,native=None):
 a.validate_manifest(m,before,after,kernel)
 version=subprocess.check_output(['kicad-cli','version'],text=True).strip()
 if version!=a.VERSION:raise ValueError('requires pinned native10.0.6')
 if native is None:import pcbnew as native
 if native.GetBuildVersion()!=a.VERSION:raise ValueError('native Python version changed')
 paths,raw,texts,ctx=a.sources(before,after);boards={};rows=[];blocks=[a.zone_blocks(t) for t in texts]
 for (uid,layer,stage),ref in sorted(references(m).items()):
  if ref['source_board_sha256']!=a.SHA(raw[stage]) or ref['source_zone_bytes_sha256']!=a.SHA(blocks[stage][uid].encode()):raise ValueError('native source/reference bytes changed')
  if stage not in boards:boards[stage]=native.LoadBoard(str(paths[stage]))
  board=boards[stage];zones=[z for z in board.Zones() if z.m_Uuid.AsString()==uid]
  lid=native.F_Cu if layer=='F.Cu' else native.B_Cu
  if len(zones)!=1 or zones[0].GetIsRuleArea() or list(zones[0].GetLayerSet().Seq())!=[lid] or zones[0].GetNetname()!='AGND':raise ValueError('zone UUID/layer/net identity changed')
  signature=a.native_zone_signature(zones[0].GetFilledPolysList(lid))
  rows.append(dict(geometry_reference=ref,reference_sha256=a.identity(ref),stage=stage,zone_uuid=uid,layer=layer,net='AGND',signature=signature))
 # Read-only mounts are enforced by the host; additionally prove no bytes
 # changed during native LoadBoard. There is no fill/save API in this module.
 if any(p.read_bytes()!=b for p,b in zip(paths,raw)) or any(p.with_suffix(s).read_bytes()!=v for p in paths for s,v in ctx.items()):raise ValueError('native read changed source/context')
 return dict(manifest_sha256=a.identity(m),policy=kernel,source_sha256=m['source_sha256'],context_sha256=m['context_sha256'],native_version=version,native_python_version=native.GetBuildVersion(),rows=rows)
def validate_receipt(m,kernel,bindings,receipt):
 if type(receipt.get('completed_drc_tasks')) is not int or receipt.get('completed_drc_tasks')!=0 or receipt.get('refilled') is not False or receipt.get('saved') is not False or receipt.get('rerouted') is not False:raise ValueError('bootstrap is not read-only/non-task evidence')
 first,second=receipt['independent_reloads']
 if first!=second:raise ValueError('independent native reload disagrees')
 if first['manifest_sha256']!=a.identity(m) or first['policy']!=kernel or first['source_sha256']!=m['source_sha256'] or first['context_sha256']!=m['context_sha256'] or first['native_version']!=a.VERSION or first['native_python_version']!=a.VERSION:raise ValueError('bootstrap manifest/kernel/source/context/version changed')
 refs=references(m);rows=first['rows'];expected={a.identity(v) for v in refs.values()}
 if len(rows)!=4 or {r['reference_sha256'] for r in rows}!=expected:raise ValueError('bootstrap reference coverage changed')
 signatures={}
 for r in rows:
  key=(r['zone_uuid'],r['layer'],r['stage'])
  if key not in refs or r['geometry_reference']!=refs[key] or r['reference_sha256']!=a.identity(refs[key]) or r['net']!='AGND' or not __import__('re').fullmatch('[0-9a-f]{64}',r['signature']):raise ValueError('bootstrap zone/source identity altered')
  signatures[r['reference_sha256']]=r['signature']
 target=a.identity(refs[TARGET])
 if len(bindings)!=3 or set(bindings)!=expected-{target} or any(signatures[k]!=v for k,v in bindings.items()):raise ValueError('three existing native controls disagree')
 return dict(reference=refs[TARGET],reference_sha256=target,signature=signatures[target],native_version=a.VERSION,completed_drc_tasks=0,requires_stage_review=True)
def bootstrap(m,before,after,bindings,output,kernel):
 output=Path(output)
 if output.exists():raise ValueError('bootstrap output must be disjoint/new')
 output.mkdir(parents=True);manifest=output/'manifest-input.json';a.atomic(manifest,m);snapshots=[]
 for i in range(2):
  path=output/('independent-reload-'+str(i)+'.json')
  subprocess.run([sys.executable,__file__,'--manifest',str(manifest),'--before',str(before),'--after',str(after),'--output',str(path)],check=True)
  snapshots.append(json.loads(path.read_bytes()))
 receipt=dict(independent_reloads=snapshots,completed_drc_tasks=0,refilled=False,saved=False,rerouted=False)
 validate_receipt(m,kernel,bindings,receipt);a.atomic(output/'geometry-receipt.json',receipt)
if __name__=='__main__':
 parser=argparse.ArgumentParser();parser.add_argument('--manifest',required=True);parser.add_argument('--before',required=True);parser.add_argument('--after',required=True);parser.add_argument('--output',required=True);args=parser.parse_args()
 a.atomic(args.output,snapshot(json.loads(Path(args.manifest).read_bytes()),args.before,args.after,a.policy(Path(__file__).resolve().parents[2])))
