"""Reproduce all21 SHA-bound native sample fixture bytes without native execution."""
import hashlib,json,re,sys,zipfile
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.audit_zone_silk_scope import zone_fixture_parts,zone_fixture_batch_text
from scripts.pcbgen.uuid_tools import top_level_spans,UUID_RE
source=Path(sys.argv[1])
archive=Path(sys.argv[2]);sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(archive.read_bytes())=='e925baf46b0941e35354f89edb9737ceb00b65fca0dab7f3246276d008837724'
assert sha(source.read_bytes())=='95c815b2178511621f97cd7021938023b96d4ee19c9282ae99b35fb387ba10c5'
text=source.read_text();artwork=set()
for a,b in top_level_spans(text):
 block=text[a:b];kind=block[1:].split(None,1)[0].rstrip(')')
 if kind=='footprint' or ((kind.startswith('gr_') or kind in ('dimension','image')) and not re.search(r'\(layer "Edge.Cuts"\)',block)):
  artwork.add(UUID_RE.search(block)[1])
parts=zone_fixture_parts(text,'601e02b2-8ccb-5c28-83e5-03789d47fbbd',artwork);rows=[]
with zipfile.ZipFile(archive) as z:
 name=next(n for n in z.namelist() if n.endswith('/result.json'));prefix=name[:-len('result.json')];result=json.loads(z.read(name))
 for trial in result['trials']:
  size=trial['batch_size']
  for start,f in zip(range(0,16,size),trial['fixtures']):
   native=z.read(prefix+f'batch-{size}/{start:04d}/osc-core.kicad_pcb')
   assert zone_fixture_batch_text(parts,f['item_uuids']).encode()==native
   rows.append(dict(size=size,start=start,fixture_sha256=sha(native)))
Path(sys.argv[3]).write_text(json.dumps(dict(status='21 EXISTING NATIVE SAMPLE FIXTURES RECONSTRUCT EXACTLY; FULL PAIRED NATIVE NOT RUN',artifact_sha256=sha(archive.read_bytes()),source_sha256=sha(source.read_bytes()),rows=rows),indent=2)+'\n')
print('PASS21 saved native fixture byte comparisons; no native tool invoked')
