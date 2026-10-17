import copy
import math
import unittest
import stage5_electrical as e

class ElectricalTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.ctx=e.source_context()
    def test_capture_matches(self):self.assertEqual(28,len(e.assert_capture(self.ctx)))
    def test_changed_capture_rejected(self):
        ctx=copy.deepcopy(self.ctx);ctx['bypin']['R1135','1'][0]['value']='100 ohm'
        with self.assertRaises(ValueError):e.assert_capture(ctx)
    def test_rc_and_bias_units(self):
        b=e.budgets();self.assertAlmostEqual(.00026,b['control_wiper']['nominal_filter']['tau_s'])
        self.assertAlmostEqual(.00015,b['pitch_input']['input_limit_15nA_bias_sensitivity_V'])
        self.assertAlmostEqual(.025,b['octave_five_receivers']['five5V_step_initial_current_A'])
        self.assertAlmostEqual(2.5e-6,b['octave_five_receivers']['five5V_step_charge_C'])
    def test_gate_source_arithmetic(self):
        b=e.budgets()['SYNC_BUFFER'];self.assertAlmostEqual(1.471965,e.gate_threshold('high'),places=5);self.assertAlmostEqual(.971509,e.gate_threshold('low'),places=5)
        self.assertGreater(b['two_50nA_bias_worst_sign_input_referred_sensitivity_V'],0)
    def test_return_budget_does_not_pass200uV(self):
        self.assertGreater(e.budgets()['return_error']['at_0_5mohm_V'],200e-6)
    def test_pitch_proposal_conserves_existing_total(self):
        p=e.characterization()['experiments'][0]['proposed_targets']
        self.assertAlmostEqual(5/1200,p['collective_pitch_interconnect_error_V']+p['remaining_chain_error_V'])
        self.assertAlmostEqual(p['collective_pitch_interconnect_error_V'],p['return_suballocation_V']+p['remaining_interconnect_error_V'])
        self.assertIn('NOT APPROVED',p['approval'])
    def test_gate_proposal_does_not_promise_minimum_pulse(self):
        p=e.characterization()['experiments'][2]['proposed_targets']
        self.assertEqual((0,0,100),(p['false_edges'],p['missed_edges'],p['pulses_per_grid_case']))
        self.assertIsNone(p['minimum_supported_pulse_s']);self.assertIn('NOT APPROVED',p['approval'])
    def test_no_unknowns_promoted(self):
        b=e.budgets();self.assertIsNone(b['remote_buffer']['phase_margin_deg']);self.assertIsNone(b['SYNC_GATE']['VOH_min_V']);self.assertIsNone(b['HARD_SOFT_DRIVE']['minimum_sync_pulse_s'])
    def test_trace_past_switch_to_real_logic_driver(self):
        t=e.trace_net('/O1/HARD_DRIVE',self.ctx);ends={p['endpoint'] for p in t['active_terminals'] if p['pin_type']=='output' and not p['AC_only']}
        self.assertIn('U1107:2',ends)
    def test_trace_past_reference_resistor(self):
        t=e.trace_net('/O1/LOCAL_REF5',self.ctx);ends={p['endpoint'] for p in t['active_terminals'] if p['pin_type']=='output' and not p['AC_only']}
        self.assertIn('U1110:1',ends)
    def test_trace_wiper_receiver(self):
        t=e.trace_net('/O1/C1eb779_W',self.ctx);ends={p['endpoint'] for p in t['active_terminals'] if p['pin_type']=='input' and not p['AC_only']}
        self.assertIn('U1112:5',ends)
if __name__=='__main__':unittest.main()
