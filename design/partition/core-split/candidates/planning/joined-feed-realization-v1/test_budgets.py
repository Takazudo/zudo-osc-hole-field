import importlib.util,unittest
from pathlib import Path
p=Path(__file__).with_name('compare-budgets.py');sp=importlib.util.spec_from_file_location('budget',p);b=importlib.util.module_from_spec(sp);sp.loader.exec_module(b)
class BudgetTests(unittest.TestCase):
 def test_latest_analog_drop(self):
  self.assertAlmostEqual(b.drop(2.1,4.6,104,85,.013,.0002,.0001,.0001,1),19.8119,places=9)
 def test_old_copper_cannot_inherit_short_cut_pass(self):
  self.assertAlmostEqual(b.drop(2.1,4.6,104,85,.013,.0002,.001,.0005,1),23.5419,places=9)
 def test_three_return_conditional_conductance(self):
  self.assertAlmostEqual(b.drop(2.1,4.6,104,85,.013,.0002,.001,.0005,3),14.780433333333333,places=9)
 def test_two_return_conditional_conductance(self):
  self.assertAlmostEqual(b.drop(2.1,4.6,104,85,.013,.0002,.001,.0005,2),16.9708,places=9)
 def test_common_copper_is_not_divided(self):
  a=b.drop(2.1,4.6,104,85,.013,.0002,.001,.0005,3);z=b.drop(2.1,4.6,104,85,.013,.0002,.001,0,3)
  self.assertAlmostEqual(a-z,2.3,places=9)
 def test_rail_path_is_not_divided(self):
  self.assertEqual(b.drop(2.1,0,104,85,.013,.0002,.001,.0005,3),b.drop(2.1,0,104,85,.013,.0002,.001,.0005,1))
 def test_invalid_return_count_or_nonfinite_rejects(self):
  for n in (0,4):
   with self.assertRaises(ValueError):b.drop(2.1,4.6,104,85,.013,.0002,.001,.0005,n)
  with self.assertRaises(ValueError):b.drop(float('nan'),4.6,104,85,.013,.0002,.001,.0005,3)
 def test_latest_effective_caps_and_no_readiness_credit(self):
  x=b.calculate();rows=x['alternatives'][1:]
  self.assertTrue(all(r['main_cut_ceiling_mm']==104 and r['new_cut_ceiling_mm']==85 for r in rows))
  self.assertTrue(all(r['physical_candidate_ready'] is False for r in x['alternatives']))
if __name__=='__main__':unittest.main()
