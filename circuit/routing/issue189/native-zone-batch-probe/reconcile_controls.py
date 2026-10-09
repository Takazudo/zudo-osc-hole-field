"""Reconcile immutable native detection controls; never authorize board adoption."""
import hashlib,json,re,sys,zipfile
from pathlib import Path
sys.path.insert(0,str(Path.cwd()))
from scripts.pcbgen.probe_zone_batch_controls import control_text,selected_identities,IDS,ZONE
from scripts.pcbgen.audit_zone_silk_scope import zone_fixture_parts
from scripts.pcbgen.uuid_tools import top_level_spans,UUID_RE
source=Path(sys.argv[1]);archive=Path(sys.argv[2]);output=Path(sys.argv[3]);sha=lambda b:hashlib.sha256(b).hexdigest()
assert sha(source.read_bytes())=='95c815b2178511621f97cd7021938023b96d4ee19c9282ae99b35fb387ba10c5'
assert sha(archive.read_bytes())=='0335d000cc4d4055455e2e8cac312693b59a9bde59403e133397074899e20f83'
text=source.read_text();artwork=set()
for a,b in top_level_spans(text):
 block=text[a:b];kind=block[1:].split(None,1)[0].rstrip(')')
 if kind=='footprint' or ((kind.startswith('gr_') or kind in ('dimension','image')) and not re.search(r'\(layer "Edge.Cuts"\)',block)):
  artwork.add(UUID_RE.search(block)[1])
parts=zone_fixture_parts(text,ZONE,artwork);unions={};receipts=[]
with zipfile.ZipFile(archive) as z:
 name=next(n for n in z.namelist() if n.endswith('/result.json'));prefix=name[:-len('result.json')];r=json.loads(z.read(name))
 assert r['status']=='NATIVE POSITIVE AND NEGATIVE CONTROLS PASS; NEVER ACCEPTANCE' and r['version']=='10.0.6'
 assert [c['name'] for c in r['controls']]==['covered-copper','positive-a','positive-b','negative','batch']
 for c,selected,layer in zip(r['controls'],[[0,1],[0],[1],[2],[0,1,2]],['F.Cu','F.Mask','F.Mask','F.Mask','F.Mask']):
  assert c['selected']==selected and c['zone_layer']==layer
  folder=prefix+c['name']+'/'
  board=z.read(folder+source.name);report=z.read(folder+'drc.json')
  assert board==control_text(parts,selected,r['point_mm'],layer).encode()
  assert sha(board)==c['fixture_sha256'] and sha(report)==c['report_sha256']
  assert c['native_geometry_sha256']=='7fb92eb72ba53fc4c78534677ace6a449dfb1a65df5633df9a2c7836e1e93073'
  for suffix in ('.kicad_pro','.kicad_dru'):
   assert z.read(folder+source.stem+suffix)==source.with_suffix(suffix).read_bytes()
  actual=selected_identities(json.loads(report))
  expected={('silk_over_copper','warning',tuple(sorted([ZONE,IDS[i]]))) for i in selected if i<2} if layer=='F.Mask' else set()
  assert actual==expected=={(a,b,tuple(ids)) for a,b,ids in c['identities']}
  unions[c['name']]=actual;receipts.append(dict(c,verified_zone_identity_count=len(actual)))
 assert unions['batch']==unions['positive-a']|unions['positive-b']|unions['negative']
 result=dict(status='FIVE NATIVE DETECTION CONTROLS RECONCILED; NEVER ACCEPTANCE',run=38004636645,
  source_commit='3629a72c7824ebdec8db324ce4d224bd168b0a49',artifact=11650254110,
  artifact_sha256=sha(archive.read_bytes()),source_sha256=sha(source.read_bytes()),version='10.0.6',
  controls=receipts,positive_single_batch_identity_equality=True,full_paired_zone_coverage=False,adopted=False)
 output.write_text(json.dumps(result,indent=2)+'\n');print('PASS5 native controls;0/1/1/0/2 exact identities; no adoption')
