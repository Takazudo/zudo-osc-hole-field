import unittest,tempfile,json,importlib.util
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('installer',ROOT/'install_resources.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class InstallerTests(unittest.TestCase):
 def setUp(self):
  self.t=tempfile.TemporaryDirectory();self.addCleanup(self.t.cleanup);self.root=Path(self.t.name);self.host=self.root/'host';self.payload=self.root/'payload'
  for rel,content in {'circuit.config.ts':'export default {}','circuit/WORKFLOW.md':'Official workflow placeholder for TEST ONLY','package.json':json.dumps({'dependencies':{'@takazudo/zudo-circuit-doc':'0.1.0'}}),'circuit/publication/assets.json':json.dumps({'schema_version':1,'assets':[{'path':'favicon.svg','reason':'original'}]}),'doc/src/content/docs/project/index.mdx':'---\ntitle: Project\n---\n\nOriginal brief','doc/src/content/docs/project/next-actions.mdx':'---\ntitle: Next\n---\n\nOriginal next'}.items():
   p=self.host/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(content)
  for rel in ['project/osc-hole-field/test.json','doc/public/assets/osc-hole-field/x.svg','doc/src/content/docs/project/osc-overview.mdx']:
   p=self.payload/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_text('test')
 def snapshot(self):return {str(p.relative_to(self.host)):p.read_bytes() for p in self.host.rglob('*') if p.is_file()}
 def test_dry_run_is_read_only(self):
  before=self.snapshot();p=m.plan(self.host,self.payload);self.assertEqual(before,self.snapshot());self.assertGreater(len(p['writes']),0)
 def test_install_preserves_authored_text_and_allowlist(self):
  m.apply(m.plan(self.host,self.payload));brief=(self.host/'doc/src/content/docs/project/index.mdx').read_text();self.assertIn('Original brief',brief);self.assertIn('{/* osc-hole-field-r21-handoff:start */}',brief);a=json.loads((self.host/'circuit/publication/assets.json').read_text());self.assertEqual(a['assets'][0]['path'],'favicon.svg');self.assertEqual(len(a['assets']),2)
 def test_idempotent(self):
  m.apply(m.plan(self.host,self.payload));p=m.plan(self.host,self.payload);self.assertEqual(p['writes'],[])
 def test_collision_aborts_without_writes(self):
  p=self.host/'project/osc-hole-field/test.json';p.parent.mkdir(parents=True);p.write_text('different');before=self.snapshot()
  with self.assertRaises(ValueError):m.plan(self.host,self.payload)
  self.assertEqual(before,self.snapshot())
 def test_unknown_host_rejected(self):
  (self.host/'circuit.config.ts').unlink()
  with self.assertRaises(ValueError):m.plan(self.host,self.payload)
 def test_generated_path_rejected(self):
  p=self.payload/'doc/src/content/docs/components/no.mdx';p.parent.mkdir(parents=True);p.write_text('no')
  with self.assertRaises(ValueError):m.plan(self.host,self.payload)
 def test_symlink_escape_rejected(self):
  (self.host/'project').symlink_to(self.root/'outside',target_is_directory=True)
  with self.assertRaises(ValueError):m.plan(self.host,self.payload)
 def test_concurrent_change_rejected(self):
  p=m.plan(self.host,self.payload);(self.host/'doc/src/content/docs/project/index.mdx').write_text('changed')
  with self.assertRaises(ValueError):m.apply(p)
  self.assertFalse((self.host/'project/osc-hole-field/test.json').exists())
 def test_modified_managed_block_rejected(self):
  m.apply(m.plan(self.host,self.payload));p=self.host/'doc/src/content/docs/project/index.mdx';p.write_text(p.read_text().replace('zudo-osc-hole-field handoff','Other'))
  with self.assertRaises(ValueError):m.plan(self.host,self.payload)
 def test_never_changes_workflow_or_package(self):
  a=(self.host/'circuit/WORKFLOW.md').read_bytes();b=(self.host/'package.json').read_bytes();m.apply(m.plan(self.host,self.payload));self.assertEqual(a,(self.host/'circuit/WORKFLOW.md').read_bytes());self.assertEqual(b,(self.host/'package.json').read_bytes())
if __name__=='__main__':unittest.main()
