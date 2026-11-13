import copy,hashlib,json,tempfile,unittest
from pathlib import Path
from run_protocol import canonical_checkpoint
CHECKPOINT='circuit/routing/osc-pcb-current-checkpoint.json'
def sha(data):return hashlib.sha256(data).hexdigest()
class Checkpoint(unittest.TestCase):
 def setUp(self):self.root=Path.cwd();self.record=json.loads((self.root/CHECKPOINT).read_text())
 def fake(self,board_bytes,entry):
  d=tempfile.TemporaryDirectory();self.addCleanup(d.cleanup);root=Path(d.name)
  (root/'b.kicad_pcb').write_bytes(board_bytes);(root/CHECKPOINT).parent.mkdir(parents=True)
  (root/CHECKPOINT).write_text(json.dumps({'boards':{'osc-core':{**entry,'board':'b.kicad_pcb'}}}));return root
 def test_current_canonical_board_is_bound_exactly(self):
  entry=self.record['boards']['osc-core'];current,extra=canonical_checkpoint(self.root)
  self.assertEqual(current,sha((self.root/entry['board']).read_bytes()))
  if current!=entry['board_sha256']:
   # A metadata-only successor binds its receipt and verifier as mandatory admission inputs.
   self.assertEqual(current,entry['metadata_successor']['successor_board_sha256'])
   self.assertEqual(extra,[self.root/entry['metadata_successor']['path'],self.root/'scripts/checks/metadata_successor.py'])
 def test_exact_adopted_bytes_need_no_successor(self):
  self.assertEqual(canonical_checkpoint(self.fake(b'k',{'board_sha256':sha(b'k')})),(sha(b'k'),[]))
 def test_other_bytes_refused(self):
  entry=copy.deepcopy(self.record['boards']['osc-core']);entry.pop('metadata_successor',None)
  with self.assertRaisesRegex(ValueError,'neither the adopted'):canonical_checkpoint(self.fake(b'edited',entry))
  entry=copy.deepcopy(self.record['boards']['osc-core'])
  with self.assertRaisesRegex(ValueError,'neither the adopted'):canonical_checkpoint(self.fake(b'edited',entry))
 def test_recorded_successor_hash_without_verified_receipt_refused(self):
  entry={'board_sha256':sha(b'k'),'metadata_successor':{'path':'r.json','sha256':'0'*64,'successor_board_sha256':sha(b'edited')}}
  with self.assertRaisesRegex(ValueError,'receipt does not bind'):canonical_checkpoint(self.fake(b'edited',entry))
 def test_verified_receipt_must_match_checkpoint_binding(self):
  from unittest import mock
  entry={'board_sha256':sha(b'k'),'metadata_successor':{'path':'r.json','sha256':'1'*64,'successor_board_sha256':sha(b'edited')}}
  good={'path':'r.json','receipt_sha256':'1'*64,'adopted':{'sha256':sha(b'k')}}
  for field,bad in (('path',{**good,'path':'other.json'}),('sha',{**good,'receipt_sha256':'2'*64}),('adopted',{**good,'adopted':{'sha256':'3'*64}})):
   with self.subTest(field),mock.patch('scripts.checks.metadata_successor.successor_for',return_value=bad):
    with self.assertRaisesRegex(ValueError,'receipt does not bind'):canonical_checkpoint(self.fake(b'edited',entry))
  with mock.patch('scripts.checks.metadata_successor.successor_for',return_value=good):
   root=self.fake(b'edited',entry);self.assertEqual(canonical_checkpoint(root),(sha(b'edited'),[root/'r.json',root/'scripts/checks/metadata_successor.py']))
if __name__=='__main__':unittest.main()
