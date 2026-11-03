import copy
import json
import math
import unittest
import stage8_currents as c

class Currents(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.config=json.loads((c.OUT/'current-input.json').read_text())
        # Historical fixture tests topology independently of final Stage8 poses.
        cls.interface=json.loads((c.prior.hosting.a.OUT/'stage7/interfaces-report.json').read_text())
    def test_full_source_capture(self):
        r=c.source_capture(self.interface)
        self.assertEqual(r['counts']['units'],76);self.assertEqual(r['counts']['amplifier_sections'],12)
        self.assertEqual(len(r['LED_polarity_paths']),3);self.assertEqual(len(r['bypasses']),10)
    def test_wrong_pin_and_NC_rejected(self):
        for ref,pin,net in [('U3305','2','/X1/SELECTOR_REMOTE'),('U3301','12','AGND')]:
            r=copy.deepcopy(self.interface);r['packages'][ref]['pins'][pin]=net
            with self.assertRaises(ValueError):c.source_capture(r)
    def test_wrong_host_rejected(self):
        r=copy.deepcopy(self.interface);r['packages']['U3303']['board']='X1-jack'
        with self.assertRaises(ValueError):c.source_capture(r)
    def test_ground_graph(self):
        r=c.topology(self.interface);self.assertEqual(len(r['ground_branches']),4)
        self.assertEqual(r['middle_AGND_star']['pin'],'7')
    def test_duplicate_ground_edge_rejected(self):
        r=copy.deepcopy(self.interface);r['middle_trace_edges'][-1]=copy.deepcopy(r['middle_trace_edges'][-2])
        with self.assertRaises(ValueError):c.topology(r)
    def test_wrong_wire_pad_rejected(self):
        r=copy.deepcopy(self.interface);r['links'][0]['conductors'][0]['front_pad_xyz_mm'][0]+=1
        with self.assertRaises(ValueError):c.topology(r)
    def test_selected_gain_and_ground_derivative(self):
        a=c.selector(5,-5,'A',2200,2200,1e7)
        b=c.selector(5,-5,'A',2200,2200,1e7,.1)
        expected=2200/(1e7+2200)
        self.assertAlmostEqual(a['control_to_jack_ground_coupling'],expected)
        self.assertAlmostEqual((b['common_voltage_relative_J_AGND_V']-a['common_voltage_relative_J_AGND_V'])/.1,expected)
        self.assertAlmostEqual(a['A_signal_current_A'],a['control_bias_ground_current_A'])
    def test_bridge_current_not_ground_current(self):
        r=c.selector(5,-5,'bridge',2200,2200,1e7)
        self.assertEqual(r['common_voltage_relative_J_AGND_V'],0)
        self.assertAlmostEqual(r['A_signal_current_A'],10/4400)
        self.assertAlmostEqual(r['B_signal_current_A'],-10/4400)
        self.assertEqual(r['control_bias_ground_current_A'],0)
    def test_open_ground_unity(self):
        r=c.selector(5,-5,'open',2200,2200,1e7,.001)
        self.assertAlmostEqual(r['common_voltage_relative_J_AGND_V'],.001)
        self.assertEqual(r['control_to_jack_ground_coupling'],1)
        with self.assertRaises(ValueError):c.selector(5,0,'invented',2200,2200,1e7)
    def test_no_cancellation_credit(self):
        s=next(s for s in self.config['states']if s['id']=='opposed_overlap')
        r=c.state_case(self.config,s,self.config['resistance_cases'][1],.0006)
        leds=r['signed_diagnostic_terms_A']['LED_A_B_OUT_to_jack_ground']
        self.assertEqual(sum(leds),0)
        self.assertGreater(r['modeled_current_magnitude_envelopes_A']['jack_AGND'],2*5/5600)
        self.assertGreater(r['ground_voltage_bounds_for_modeled_terms_V']['jack_to_middle'],.0002)
    def test_output_indicator_tracks_loaded_drive(self):
        for voltage in (5,-5):
            state={'A_V':voltage,'B_V':0,'switch':'A'}
            r=c.state_case(self.config,state,self.config['resistance_cases'][1],.0006)
            volt=r['ideal_output_voltages_V'];load=r['signed_diagnostic_terms_A']['external_output_load']
            self.assertAlmostEqual(volt['OUT_BUFFERED']-volt['OUT_TIP'],998*load)
            self.assertAlmostEqual(r['signed_diagnostic_terms_A']['LED_A_B_OUT_to_jack_ground'][2],volt['OUT_BUFFERED']/5600)
            self.assertGreater(abs(volt['OUT_BUFFERED']),abs(volt['OUT_TIP']))
    def test_quiescent_not_added_to_AGND(self):
        s=self.config['states'][0];r=c.state_case(self.config,s,self.config['resistance_cases'][0],.0004)
        self.assertEqual(r['quiescent_between_rails_A']['all12_amplifiers'],.013)
        self.assertAlmostEqual(r['modeled_current_magnitude_envelopes_A']['jack_AGND'],.0008+10/101000+15e-9)
        self.assertIsNone(r['total_guaranteed_current_bound_A']);self.assertFalse(r['qualified'])
    def test_source_conditioned_facts(self):
        r=c.facts(self.config);self.assertIn('16.5',r['ADG_ground_current']['conditions'])
        cfg=copy.deepcopy(self.config);cfg['ADG5412F_primary_ground_evidence']['sha256']='0'*64
        with self.assertRaises(ValueError):c.facts(cfg)
    def test_numeric_source_value_mutation_rejected(self):
        cfg=copy.deepcopy(self.config);cfg['nominal']['indicator_sense_ohm']=1000
        with self.assertRaises(ValueError):c.state_case(cfg,cfg['states'][0],cfg['resistance_cases'][0],.0006)
    def test_negative_resistance_rejected(self):
        resistance=copy.deepcopy(self.config['resistance_cases'][0]);resistance['extra_return_branch_ohm']=-.1
        with self.assertRaises(ValueError):c.state_case(self.config,self.config['states'][0],resistance,.0006)

if __name__=='__main__':unittest.main()
