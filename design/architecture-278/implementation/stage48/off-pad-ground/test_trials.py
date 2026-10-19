"""Rejected evidence must never be promoted to an accepted candidate."""
import copy,importlib.util,unittest
from pathlib import Path
HERE=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('stage48_inspect',HERE/'inspect_trials.py');a=importlib.util.module_from_spec(spec);spec.loader.exec_module(a)
class TrialTests(unittest.TestCase):
 def setUp(self):
  self.one=a.read(HERE/'evidence/trial1-drc-pass1.json');self.two=a.read(HERE/'evidence/trial2-drc-pass1.json')
  self.base=copy.deepcopy(self.two)
 def test_exact_trial1_rejection(self):self.assertEqual(a.drc_gate(self.base,self.one,1)['reason'],'new dangling via')
 def test_exact_trial2_rejection(self):self.assertEqual(a.drc_gate(self.base,self.two,2)['reason'],'intended ground closure absent')
 def test_no_false_acceptance(self):
  for t in [1,2]:self.assertFalse(a.read(HERE/f'evidence/trial{t}-audit.json')['drc']['accepted'])
 def test_missing_first_failure_rejected(self):
  self.one['violations']=[v for v in self.one['violations'] if not(v['type']=='via_dangling' and any(i['uuid']==a.DANGLING for i in v['items']))]
  with self.assertRaises(ValueError):a.drc_gate(self.base,self.one,1)
 def test_added_rule_error_rejected(self):
  self.two['violations'].append(dict(type='clearance',severity='error',items=[]))
  with self.assertRaises(ValueError):a.drc_gate(self.base,self.two,2)
 def test_added_unrelated_warning_rejected(self):
  self.two['violations'].append(dict(type='track_dangling',severity='warning',items=[dict(uuid='foreign')]))
  with self.assertRaises(ValueError):a.drc_gate(self.base,self.two,2)
 def test_wrong_open_count_rejected(self):
  self.two['unconnected_items'].pop()
  with self.assertRaises(ValueError):a.drc_gate(self.base,self.two,2)
 def test_parity_error_rejected(self):
  self.two['schematic_parity']=[dict(type='mismatch')]
  with self.assertRaises(ValueError):a.drc_gate(self.base,self.two,2)
 def test_wrong_native_version_rejected(self):
  self.two['kicad_version']='9.0'
  with self.assertRaises(ValueError):a.drc_gate(self.base,self.two,2)
 def test_retained_evidence_hashes(self):
  for t in [1,2]:
   bindings=a.read(HERE/f'evidence/trial{t}-audit.json')['bindings']
   for suffix in ['drc-pass1.json','drc-pass1.json.execution.json']:
    self.assertEqual(a.sha(HERE/f'evidence/trial{t}-{suffix}'),bindings[f'.circuit-cache/stage48-trial{t}/{suffix}'])
   proposal=HERE/f'evidence/trial{t}-proposal.json'
   self.assertEqual(a.sha(proposal),bindings[str(proposal.relative_to(a.ROOT))])
 def test_local_native_replay(self):
  needed=[a.ROOT/'.circuit-cache/stage44-b2-fresh/connectivity-passfresh.json']+[a.ROOT/f'.circuit-cache/stage48-trial{t}/connectivity-pass1.json' for t in [1,2]]
  if not all(p.exists() for p in needed):self.skipTest('ignored full native artifacts unavailable')
  for t in [1,2]:self.assertEqual(a.inspect(t),a.read(HERE/f'evidence/trial{t}-audit.json'))
if __name__=='__main__':unittest.main()
