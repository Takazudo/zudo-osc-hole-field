"""Check exact saved JR/core scopes without running or substituting native acceptance."""
import argparse,hashlib,json,sys,zipfile
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.audit_added_mask import added_copper_scope
p=argparse.ArgumentParser();p.add_argument('jr_archive',type=Path);p.add_argument('core_archive',type=Path);p.add_argument('output',type=Path);args=p.parse_args()
sha=lambda b:hashlib.sha256(b).hexdigest()
result=[]
for archive,bid,digest,count,vias,before_sha,after_sha in (
 (args.jr_archive,'osc-jack-right','eea30c08925c060754a521868ef8f8b3766864bb2237d1efcd2212b8e7ca3dfd',79,5,'35b52972dd70b4186cf3f3b7ee2ac3d70432f3476c2f56c9fcf9c1c4d7d4d445','22189b127579271b2f2c219da5e4b7e2af59673cb04e002b0dc4966afe2170dd'),
 (args.core_archive,'osc-core','b5c112a5c9336a27cb08369ec42a11b7cc51a39bb569215d24075ccd3ab11567',382,38,'95c815b2178511621f97cd7021938023b96d4ee19c9282ae99b35fb387ba10c5','b9f5ca13f83c7ffdbe5836fd271e7c1099e04b901ca1798a7be06f025bd02d66')):
 with archive.open('rb') as f:assert hashlib.file_digest(f,'sha256').hexdigest()==digest
 with zipfile.ZipFile(archive) as z:
  def read(stage):
   paths=[n for n in z.namelist() if n.endswith(f'{bid}-grid-shards-{stage}/{bid}.kicad_pcb')];assert len(paths)==1
   return z.read(paths[0])
  before,after=read('start'),read('fresh')
  assert sha(before)==before_sha and sha(after)==after_sha
  scope=added_copper_scope(before.decode(),after.decode(),count,vias)
  result.append(dict(board=bid,archive_sha256=digest,before_sha256=before_sha,after_sha256=after_sha,added_copper=count,added_vias=vias,source_scope=scope))
args.output.write_text(json.dumps(dict(status='EXACT SAVED SOURCE SCOPE REGRESSION; NO NEW NATIVE ACCEPTANCE',scopes=result),indent=2)+'\n')
print(json.dumps([{k:v for k,v in r.items() if k!='source_scope'} for r in result],indent=2))
