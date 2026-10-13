import json
from pathlib import Path
import tempfile
import unittest
import pilot_construct as p

class Authentication(unittest.TestCase):
 def test_each_geometry_input_and_review_are_bound(self):
  with tempfile.TemporaryDirectory() as tmp:
   d=Path(tmp); paths={k:d/k for k in ('preflight','source','planes_net','graph','census')}
   for path in paths.values():path.write_text('{}')
   record=d/'review.md';record.write_text('independent review')
   seal_path=d/'seal.json'
   pre={'input_sha256':{k:p.sha(v) for k,v in paths.items()}}
   seal={'preflight_sha256':p.sha(paths['preflight']),'geometry_review':{'verdict':'PASS','record':'review.md','record_sha256':p.sha(record)}}
   seal_path.write_text(json.dumps(seal))
   self.assertEqual(len(p.authenticate(pre,seal,paths,seal_path)),7)
   for path in [*paths.values(),record]:
    saved=path.read_bytes();path.write_text('changed')
    with self.assertRaises(SystemExit):p.authenticate(pre,seal,paths,seal_path)
    path.write_bytes(saved)

if __name__=='__main__':unittest.main()
