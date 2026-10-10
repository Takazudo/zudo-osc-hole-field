"""Package exact optional owner-pilot inputs; never modify source boards."""
import argparse,hashlib,json,subprocess,zipfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];HERE=Path(__file__).parent
p=argparse.ArgumentParser();p.add_argument('saved_root',type=Path);p.add_argument('output',type=Path);a=p.parse_args();sha=lambda b:hashlib.sha256(b).hexdigest()
result=json.loads((HERE/'result.json').read_text());assert len(result['boards'])==2 and sum(len(b['cases']) for b in result['boards'])==20
files={};endpoints=[]
def add(name,data):
 assert name not in files;files[name]=data
for b in result['boards']:
 bid=b['board'];folder={'osc-jack-left':'jl-r8276-adoption','osc-jack-right':'jr-c7413-adoption'}[bid];saved=a.saved_root/folder/'.circuit-cache'/f'{bid}-grid-shards-fresh'
 board=ROOT/'boards'/bid/(bid+'.kicad_pcb');assert sha(board.read_bytes())==b['board_sha256'];assert sha((saved/'dump.json').read_bytes())==b['dump_sha256']
 for path in (ROOT/'boards'/bid).rglob('*'):
  if not path.is_file() or not(path.suffix in ('.kicad_pcb','.kicad_sch','.kicad_pro','.kicad_dru') or path.name in ('fp-lib-table','sym-lib-table')):continue
  if 'reports' in path.relative_to(ROOT/'boards'/bid).parts:continue
  add(str(path.relative_to(ROOT)),path.read_bytes())
 for suffix in ('.kicad_pro','.kicad_dru'):
  assert files[f'boards/{bid}/{bid}{suffix}']==(saved/(bid+suffix)).read_bytes(),'current context differs from accepted native input'
 for name in ('drc.json','dump.json'):add(f'evidence/{bid}/{name}',(saved/name).read_bytes())
 for index,c in enumerate(b['cases']):
  endpoints.append(dict(case_id=f'{bid}-{index:02d}',board=bid,board_sha256=b['board_sha256'],net=c['net'],endpoints=c['endpoints'],native_groups=c['native_groups'],bounds_mm=c['bounds_mm'],nearest_last_accepted_cut_mm=c['nearest_last_cut_mm'],raster_complete=c['complete_raster_transaction'],failure_diagnostics=c['diagnostics']))
for directory in ('footprints/kicad/zudo-osc-hole-field.pretty','symbols'):
 for path in sorted((ROOT/directory).rglob('*')):
  if path.is_file() and path.suffix in ('.kicad_mod','.kicad_sym'):add(str(path.relative_to(ROOT)),path.read_bytes())
for name in ('scripts/schgen/fixtures/fixture.kicad_sym','circuit/WORKFLOW.md','design/partition/floorplan-candidate.json','design/partition/partition-input.json','design/partition/connector-packing-candidate.json'):
 add(name,(ROOT/name).read_bytes())
add('evidence/route-result.json',(HERE/'result.json').read_bytes())
add('endpoints.json',(json.dumps(endpoints,indent=2)+'\n').encode())
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip()
readme=f'''# Optional issue189 owner routing pilot — no human pilot performed

Exact repository source: Takazudo/zudo-osc-hole-field at {commit}. Open the two projects under boards/ in KiCad10.0.6. Their sibling custom libraries retain the original relative paths. System KiCad10 libraries are required. No board, footprint, rule, component or copper is edited by this bundle.

This is a local, optional20-connection reproduction bundle, not an adoption or fabrication deliverable. Selection is ten currently open signal-component pairs per jack board nearest the last accepted cuts, with restored copper present. It does not represent all classes or prove physical impossibility. endpoints.json contains persistent net/pad UUIDs, native memberships, coordinates in nanometres and local search frames. evidence/ contains exact accepted native dumps/DRC and bounded failure traces. Read complete native groups; a connection is not necessarily a single missing trace. Raster proposals are unaccepted until all native gates pass.

Preserve318x298mm panel,33modules,180jacks,144controls,114indicators and438locked centres, fixed headers/board outlines/parts, original electrical nets and constraints. Preserve existing successful copper and native group connectivity. No home jumper workaround. Six layers retain In1 AGND, In4+12V and In3 signal use only while -12V fill remains connected. Board project/rules are authoritative; do not reduce clearances, widths, via dimensions or broaden scoped signal neckdown rules. No footprint/source movement is part of this pilot. Do not place orders, contact services, fabricate or energize.

If manually routing in a disposable copy, retain original files and every reviewed cut UUID/boundary anchor. Return modified board plus a change log identifying targeted endpoints and cuts; convert the actual copper into the repository source/replay mechanism. Before adoption require zero native DRC/parity errors, preserved original groups/warning identities, retained uncut copper, at least three settled refills and an independent fresh repeat, and any source/regeneration/full project gates. This bundle does not waive or claim those checks. Fully connected is still not hardware qualification. Keep issue189 open until its full criteria pass.

Canonical accepted counts at bundle creation: JL118 / JR134, zero native DRC/parity errors; warnings remain. The separate sole core writer must not be duplicated or altered by this optional pilot. Verify every manifest SHA256 before use; never overwrite a newer accepted board with these inputs.
'''
add('README.md',readme.encode())
manifest=dict(status='OPTIONAL REPRODUCTION BUNDLE; HUMAN PILOT NOT PERFORMED; NO ADOPTION',source_commit=commit,connection_count=20,files=[dict(path=n,size=len(data),sha256=sha(data)) for n,data in sorted(files.items())])
add('manifest.json',(json.dumps(manifest,indent=2)+'\n').encode())
a.output.parent.mkdir(parents=True,exist_ok=True)
with zipfile.ZipFile(a.output,'x',compression=zipfile.ZIP_DEFLATED,compresslevel=6) as z:
 for name,data in sorted(files.items()):
  info=zipfile.ZipInfo(name,date_time=(2026,10,10,0,0,0));info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o100644<<16;z.writestr(info,data)
with zipfile.ZipFile(a.output) as z:
 assert z.testzip() is None and len(z.namelist())==len(files)
 for f in manifest['files']:assert sha(z.read(f['path']))==f['sha256']
receipt=dict(status=manifest['status'],source_commit=commit,connections=20,archive=str(a.output),archive_sha256=sha(a.output.read_bytes()),bytes=a.output.stat().st_size,manifest_sha256=sha(files['manifest.json']),files=len(files))
(HERE/'bundle-receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt,indent=2))
