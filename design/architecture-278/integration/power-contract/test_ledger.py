"""Combined power-contract ledger controls."""
from pathlib import Path
import importlib.util, json, unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('power_contract_ledger', HERE / 'ledger.py')
ledger = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ledger)


class LedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = ledger.build()

    def test_committed_ledger_matches_build(self):
        committed = json.loads((HERE / 'ledger.json').read_text())
        self.assertEqual(committed, json.loads(json.dumps(self.data, ensure_ascii=False)))

    def test_requirements_unchanged_by_conditional_cleanup(self):
        s = self.data['states']
        self.assertEqual(s['continuous_requirement']['mA'], {'+12V': 1700, '-12V': 1600, '+5V': 300})
        self.assertEqual(s['normal_planning_stage54_conditional']['continuous_rule_result_mA'],
                         {'+12V': 1700, '-12V': 1600, '+5V': 300})

    def test_unknowns_stay_null(self):
        for key in ('guaranteed_whole_instrument_maximum_mA', 'measured_whole_instrument_mA',
                    'measured_source_capacity_mA', 'supply_capability_mA'):
            self.assertTrue(all(self.data[key][r] is None for r in ledger.RAILS), key)
        self.assertIsNone(self.data['converter_efficiency_booked'])

    def test_power_findings(self):
        p = self.data['power']
        cont = p['continuous_requirement']['infeasible_at_100_percent']
        self.assertTrue(all(v['current_pd_chain'] for v in cont.values()))
        self.assertFalse(cont['nominal_15V_3A']['any_architecture'])
        self.assertTrue(all(v['any_architecture'] for v in p['transient_requirement_20ms']['infeasible_at_100_percent'].values()))
        self.assertGreater(p['normal_planning']['positive_converter_efficiency_needed_with_pd_u4_model']['nominal_15V_3A'], 1)
        self.assertAlmostEqual(p['continuous_requirement']['osc_inlet_W_at_source_band'][1], 41.96, places=6)
        self.assertNotIn('interface_maximum', p)

    def test_ratings_screen(self):
        r = self.data['ratings_screen']
        self.assertTrue(r['+12V']['continuous_exceeds_ptc_hold_25C'] and r['-12V']['continuous_exceeds_ptc_hold_25C'])
        self.assertTrue(r['+12V']['continuous_beyond_ldo_table_rows'] and r['-12V']['continuous_beyond_ldo_table_rows'])
        self.assertFalse(any(v['ptc_enforces_interface_maximum'] for v in r.values()))

    def test_floors_are_pd_screened_minima(self):
        chain = ledger.read(ledger.INPUTS['pd_supply_input'])['chain']
        self.assertEqual({r: round(chain[r]['pre_rail_min_V'], 4) for r in ledger.RAILS},
                         {'+12V': 13.2198, '-12V': 13.4836, '+5V': 6.055})


if __name__ == '__main__':
    unittest.main()
