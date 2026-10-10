"""Verify retained failed audit ZIP and export diagnostics; no native execution."""
import hashlib,json,pathlib,sys,zipfile
archive=pathlib.Path(sys.argv[1]);output=pathlib.Path(sys.argv[2]);output.mkdir(parents=True,exist_ok=False)
expected='2cd2463554fdd63a672bf3b59dae5e3473a960017f51c142f9fc0fd7e4ebeaf4'
with archive.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==expected
with zipfile.ZipFile(archive) as z:
 names=z.namelist();assert len(names)==len(set(names))
 inventory=[]
 with zipfile.ZipFile(output/'diagnostics.zip','w',zipfile.ZIP_DEFLATED) as small:
  for n in names:
   if n.endswith('/'):continue
   p=pathlib.PurePosixPath(n);assert not p.is_absolute() and '..' not in p.parts
   with z.open(n) as f:sha=hashlib.file_digest(f,'sha256').hexdigest()
   inventory.append(dict(path=n,bytes=z.getinfo(n).file_size,sha256=sha))
   if not n.endswith(('.kicad_pcb','.kicad_prl','.kicad_pro','.kicad_dru')):small.writestr(n,z.read(n))
 manifest=dict(status='FAILED AUDIT ARCHIVE HASH/INVENTORY VERIFIED; NO NATIVE REPLAY',run=38058774479,source='617082dc9b7a7f457fd3363b6999d6bb2f341dc5',artifact=11673646039,archive_sha256=expected,archive_bytes=archive.stat().st_size,inventory=inventory,diagnostics_sha256=hashlib.sha256((output/'diagnostics.zip').read_bytes()).hexdigest())
 (output/'failure-inventory.json').write_text(json.dumps(manifest,indent=2)+'\n')
 print(json.dumps({k:v for k,v in manifest.items() if k!='inventory'}))
