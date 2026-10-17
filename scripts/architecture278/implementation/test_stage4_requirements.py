import unittest
import stage4_requirements as r

class RequirementsTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.report=r.build()
    def test_every_crossing_classified(self):
        self.assertEqual(225,self.report['row_count']);self.assertEqual(225,sum(self.report['class_counts'].values()))
        self.assertTrue(all(x['live_endpoint_evidence'] for x in self.report['rows']))
    def test_gate_reference_is_not_logic(self):
        rows=[x for x in self.report['rows'] if x['actual_identity']['actual_net']=='OSC_GATE_REF']
        self.assertEqual(5,len(rows));self.assertTrue(all(x['signal_class']=='gate_threshold_reference_DC' for x in rows))
    def test_analog_and_conditioned_gate_distinct(self):
        for row in self.report['rows']:
            name=row['actual_identity']['actual_net'].split('/')[-1]
            if name=='SYNC_BUFFER':self.assertEqual('buffered_analog_gate_input',row['signal_class'])
            if name in ('SYNC_GATE','SOFT_DRIVE','HARD_DRIVE'):self.assertEqual('conditioned_logic_and_sync_command',row['signal_class'])
    def test_unknown_net_rejected(self):
        with self.assertRaises(ValueError):r.classify({'actual_identity':{'actual_net':'/O1/UNKNOWN','actual_panel_uid':''}})
    def test_initial_envelope_not_guarantee(self):
        old=self.report['initial_source'];self.assertIn('PROPOSAL',old['authority']);self.assertIn('Unvalidated',old['status'])
        self.assertEqual(.3,old['remote_controls']['max_harness_length_m']);self.assertEqual(1e-9,old['remote_controls']['max_harness_capacitance_F'])
        self.assertEqual('NEEDS BENCH',self.report['relevant_cells']['remote_buffer']['verification_status'])
    def test_all_endpoint_nets_match(self):
        for row in self.report['rows']:
            for p in row['live_endpoint_evidence']:self.assertEqual(p['net'],row['actual_identity']['actual_net'])
if __name__=='__main__':unittest.main()
