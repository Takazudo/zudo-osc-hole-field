"""Reassemble exact retained core evidence; never extract or alter board content."""
import hashlib,json,sys,zipfile
from pathlib import Path
root=Path(sys.argv[1]);output=Path(sys.argv[2]);receipt=Path(sys.argv[3])
expected=['218c4088052df6d606d9996fd12f2fb9b4bf08eec3b650104a6690e81c63c803','c3c23b394334010b40b847ad7fa0be8dc5c1b9ced6a6c450884f3705aa24d2cf','2dce95a2e45b958570757e24180c56a3aa265744d18ee2db88ee4eedaa2a6ae6']
manifest=None;paths=[]
for index,digest in enumerate(expected):
 path=root/f'issue189-core-part{index}.zip'
 with path.open('rb') as stream:assert hashlib.file_digest(stream,'sha256').hexdigest()==digest
 with zipfile.ZipFile(path) as z:
  current=json.loads(z.read('manifest.json'))
  if manifest is None:manifest=current
  assert current==manifest
  part=manifest['parts'][index]
  assert part['index']==index and part['name']==f'part-{index:03d}.bin'
  assert set(z.namelist())=={'manifest.json',part['name']}
  assert z.getinfo(part['name']).file_size==part['size']<=256*1024*1024
 paths.append(path)
assert manifest['original_artifact']==11650664778 and manifest['original_run']==37984573591
assert manifest['original_sha256']=='b5c112a5c9336a27cb08369ec42a11b7cc51a39bb569215d24075ccd3ab11567'
assert manifest['original_size']==724422573 and len(manifest['parts'])==3
whole=hashlib.sha256();total=0
with output.open('xb') as target:
 for index,path in enumerate(paths):
  part=manifest['parts'][index];part_hash=hashlib.sha256();size=0
  with zipfile.ZipFile(path) as z,z.open(part['name']) as stream:
   while data:=stream.read(8*1024*1024):
    target.write(data);whole.update(data);part_hash.update(data);size+=len(data)
  assert size==part['size'] and part_hash.hexdigest()==part['sha256'];total+=size
assert total==manifest['original_size'] and whole.hexdigest()==manifest['original_sha256']
result=dict(status='ORIGINAL ARCHIVE REASSEMBLED AND SHA VERIFIED; NOT ADOPTED',export_run=38006210148,
 export_source='ac7bd3005af84264444bfb1de64d23be5f2c8766',parts_artifacts=[11651401938,11651436723,11651900419],
 parts_zip_sha256=expected,manifest=manifest,output=str(output),extracted=False,adopted=False)
receipt.write_text(json.dumps(result,indent=2)+'\n');print('PASS exact724422573byte original archive SHA256',whole.hexdigest())
