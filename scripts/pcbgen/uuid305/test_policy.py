import tempfile,unittest,json
from pathlib import Path
from policy import check_policy,HERE
class Policy(unittest.TestCase):
 def test_exact_actual_sources(self):self.assertEqual(check_policy(Path.cwd())['pcbnew_version'],'10.0.6')
 def test_each_producer_and_oracle_change_rejected(self):
  policy=json.loads((HERE/'oracle-policy.json').read_text())
  for changed in policy['source_sha256']:
   with self.subTest(path=changed),tempfile.TemporaryDirectory() as d:
    root=Path(d)
    for path in policy['source_sha256']:
     dest=root/path;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((Path.cwd()/path).read_bytes())
    dest=root/changed;dest.write_bytes(dest.read_bytes()+b'\nchanged')
    with self.assertRaisesRegex(ValueError,'reviewed producer/oracle bytes changed'):check_policy(root)
if __name__=='__main__':unittest.main()
