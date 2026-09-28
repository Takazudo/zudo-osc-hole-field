"""Rail subtotal accounting tests; planning values stay distinct from maxima."""
import json,unittest
from scripts.schgen.build_master_budget import ROOT,RAILS,build


class MasterBudget(unittest.TestCase):
    def test_bleeder_basis_and_missing_maxima(self):
        report=build()
        source=json.loads((ROOT/'design/power/rail-budget-input.json').read_text())
        self.assertEqual(len(report['instances']),34)
        for rail in RAILS:
            typical=sum(x['reported_typical_subtotal_mA'][rail] for x in report['instances'])
            upper=sum(x['planning_upper_subtotal_mA'][rail] for x in report['instances'])
            self.assertAlmostEqual(report['reported_assumed_typical_subtotal_mA'][rail]-typical,
                                   source['synth_inlet']['nominal_bleeder_current_mA'][rail],places=5)
            self.assertAlmostEqual(report['reported_planning_upper_subtotal_mA'][rail]-upper,
                                   source['synth_inlet']['worst_voltage_and_resistance_bleeder_current_mA'][rail],places=5)
            self.assertIsNone(report['complete_typical_mA'][rail])
            self.assertIsNone(report['guaranteed_maximum_mA'][rail])
        self.assertGreater(report['planning_subtotal_overshoot_mA']['+12V'],0)
        self.assertGreater(report['planning_subtotal_overshoot_mA']['-12V'],0)

if __name__=='__main__':unittest.main()
