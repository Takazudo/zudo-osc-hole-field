"""Fast contract tests only; no board geometry, route search or native execution."""
import copy
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest.mock import patch
import residual_closure as R

class ResidualClosure(unittest.TestCase):
 def inputs(self):
  p=dict(R.TARGET,id=R.TARGET['pad_id'],net='-12V');p.pop('pad_id')
  return {'board':'KA','objects':[p]}, {}, {'board':'KA'}, {'board':'KA','unresolved':[{'pad_id':R.TARGET['pad_id']}]}
 def engine(self,**changes):
  pr={'face':'B.Cu','width_mm':.2,'path_mm':[[0.,0.],[23.5,0.]],'length_mm':23.5,'segments':1};pr.update(changes)
  def run(*args):return {'board':'KA','net':'-12V','target':dict(R.TARGET),'attempts':[{'face':'B.Cu'}],'proposal':pr,'legal':True}
  return SimpleNamespace(FACES=('B.Cu',),LIMITS=copy.deepcopy(R.LIMITS),preflight=run)
 def test_accepts_only_declared_face_and_bounds(self):
  out=R.bounded_preflight(*self.inputs(),engine=self.engine());self.assertTrue(out['legal'])
  for changes in ({'face':'F.Cu'},{'width_mm':.25},{'path_mm':[[0,0],[30.01,0]],'length_mm':30.01},{'segments':21}):
   with self.assertRaises(ValueError):R.bounded_preflight(*self.inputs(),engine=self.engine(**changes))
 def test_wrong_target_and_resolved_pad_are_refused(self):
  inp=self.inputs();inp[0]['objects'][0]['ref']='U2315'
  with self.assertRaises(ValueError):R.bounded_preflight(*inp,engine=self.engine())
  inp=self.inputs();inp[3]['unresolved']=[]
  with self.assertRaises(ValueError):R.bounded_preflight(*inp,engine=self.engine())
 def test_isolated_module_does_not_mutate_common_globals(self):
  # The module loader itself is exercised against a tiny temporary stand-in;
  # production pathfinding is intentionally not imported or called here.
  import tempfile
  with tempfile.TemporaryDirectory() as d:
   Path(d,'pilot_preflight.py').write_text("LIMITS={'window_margin_mm':6}\nFACES=('F.Cu','B.Cu')\n")
   with patch.object(R,'HERE',Path(d)):
    a=R.isolated_engine();b=R.isolated_engine()
   a.LIMITS['max_segments']=999
   self.assertEqual(b.LIMITS,R.LIMITS);self.assertEqual(b.FACES,('B.Cu',))
 def test_negative_preflight_is_not_credited(self):
  e=self.engine();e.preflight=lambda *a:{'board':'KA','net':'-12V','target':dict(R.TARGET),'attempts':[{'face':'B.Cu','reason':'blocked'}],'proposal':None,'legal':False}
  self.assertFalse(R.bounded_preflight(*self.inputs(),engine=e)['legal'])
 def test_changed_declaration_is_refused_before_io(self):
  with self.assertRaises(ValueError):R.validate_declaration({'schema':'bad'})

if __name__=='__main__':unittest.main()
