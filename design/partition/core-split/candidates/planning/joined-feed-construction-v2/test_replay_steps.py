import json,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import replay_steps as rs

STEP='''import sys
from pathlib import Path
src,out=map(Path,sys.argv[1:3])
Path(sys.argv[3]).write_text(Path(sys.argv[3]).read_text()+'x') if len(sys.argv)>3 else None
out.write_text(src.read_text().upper())
'''

class Ledger(unittest.TestCase):
 def setUp(self):
  self.tmp=Path(tempfile.mkdtemp());self.out=self.tmp/'run';self.out.mkdir()
  self.method=self.tmp/'step.py';self.method.write_text(STEP);self.src=self.tmp/'in.txt';self.src.write_text('a')
  self.dst=self.out/'out.txt'
 def ledger(self,resume=True):return rs.Ledger(self.out,resume,sys.executable)
 def run_step(self,L):return L.run('s',[self.method,self.src,self.dst],[self.src],[self.method],[self.dst])
 def test_valid_step_is_reused(self):
  self.run_step(self.ledger());L=self.ledger();self.run_step(L)
  self.assertEqual(L.log,[{'step':'s','reused':True}])
 def test_changed_input_rejects_and_rebuilds(self):
  self.run_step(self.ledger());self.src.write_text('b');L=self.ledger();self.run_step(L)
  self.assertIn('stale: inputs',L.log[0]['rejected']);self.assertEqual(self.dst.read_text(),'B')
  self.assertTrue(list((self.out/'rejected').rglob('out.txt')),'stale output is moved aside, not deleted')
 def test_rejection_keeps_output_and_ledger_when_names_collide(self):
  dst=self.out/'s.json'
  L=self.ledger();L.run('s',[self.method,self.src,dst],[self.src],[self.method],[dst])
  self.src.write_text('b');L=self.ledger();L.run('s',[self.method,self.src,dst],[self.src],[self.method],[dst])
  moved=next((self.out/'rejected').iterdir())
  self.assertEqual((moved/'s.json').read_text(),'A');self.assertIn('inputs',json.loads((moved/'ledger-s.json').read_text()))
 def test_changed_method_rejects(self):
  self.run_step(self.ledger());self.method.write_text(STEP+'\n');L=self.ledger();self.run_step(L)
  self.assertIn('methods',L.log[0]['rejected'])
 def test_partial_output_without_ledger_rejects(self):
  self.dst.write_text('half');L=self.ledger();self.run_step(L)
  self.assertIn('partial',L.log[0]['rejected']);self.assertEqual(self.dst.read_text(),'A')
 def test_tampered_output_rejects(self):
  self.run_step(self.ledger());self.dst.write_text('Z');L=self.ledger();self.run_step(L)
  self.assertIn('output bytes',L.log[0]['rejected'])
 def test_failed_ledger_is_not_reused(self):
  self.run_step(self.ledger());stamp=self.out/'steps/s.json';d=json.loads(stamp.read_text());d['exit_code']=1;stamp.write_text(json.dumps(d))
  L=self.ledger();self.run_step(L);self.assertIn('failed',L.log[0]['rejected'])
 def test_existing_output_needs_resume(self):
  self.run_step(self.ledger())
  with self.assertRaises(SystemExit):self.run_step(self.ledger(resume=False))
 def test_ledger_records_peak_rss_and_hashes(self):
  rec=self.run_step(self.ledger())
  self.assertGreater(rec['peak_rss_KiB'],0)
  self.assertEqual(rec['outputs'],{'out.txt':{'':rs.sha(self.dst)}});self.assertEqual(rec['inputs'],{str(self.src):rs.sha(self.src)})
 def test_round_table_keeps_retained_prefix(self):
  self.assertEqual(rs.ROUND_NAMES[:3],['r1','r2','r3'])

if __name__=='__main__':unittest.main()
