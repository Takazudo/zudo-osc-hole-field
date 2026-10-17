import copy
import json
import unittest
import stage5_hosting_options as h

class HostingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=h.build();cls.ledger=json.loads((h.ROOT/'design/architecture-278/source-ledger.json').read_text());cls.packages={p['ref']:p for p in cls.ledger['packages']}
    def test_whole_source_and_bypass_conservation(self):
        for mode,option in self.report['options'].items():
            h.validate_assignment(option['assignments'],self.packages,mode)
            self.assertEqual((5904,8226),(option['package_count'],option['unit_count']))
        for ref,p in self.report['package_index'].items():
            rows=[self.ledger['package_units'][i] for i in p['unit_pin_record_indices']]
            self.assertTrue(all(x['ref']==ref for x in rows));self.assertEqual(sorted(p['units']),sorted(x['unit'] for x in rows))
    def test_missing_power_rejected(self):
        mode='candidate_front_redesign';m=copy.deepcopy(self.report['options'][mode]['assignments']);del m[self.report['POWER_refs'][0]]
        with self.assertRaises(ValueError):h.validate_assignment(m,self.packages,mode)
    def test_split_bypass_rejected(self):
        mode='candidate_front_redesign';m=copy.deepcopy(self.report['options'][mode]['assignments']);ref=next(r for r,p in self.packages.items() if p['decouples_ref']);m[ref]='some-other-host'
        with self.assertRaises(ValueError):h.validate_assignment(m,self.packages,mode)
    def test_mixed_front_counts(self):
        b=self.report['front_board_ownership_matrix'];self.assertEqual({'OSC':285,'other28':775},b['JL']);self.assertEqual({'OSC':35,'other28':250},b['P'])
        self.assertEqual(2519,self.report['counts']['front_packages']);self.assertEqual(2572,self.report['counts']['other_K_packages'])
    def test_no_partial_front_reuse(self):
        mode='core_only_front_reuse';m=copy.deepcopy(self.report['options'][mode]['assignments']);r=next(r for r,p in self.packages.items() if p['current_board']=='JL' and p['instance']=='O1');m[r]='newOSCfront'
        with self.assertRaises(ValueError):h.validate_assignment(m,self.packages,mode)
    def test_no_silent_mixed_board_retention(self):
        mode='candidate_front_redesign';m=copy.deepcopy(self.report['options'][mode]['assignments']);r=next(r for r,p in self.packages.items() if p['current_board']=='JL' and p['instance'] not in h.OSC);m[r]='historical:JL'
        with self.assertRaises(ValueError):h.validate_assignment(m,self.packages,mode)
    def test_historical_K_depth_and_sweep(self):
        k=self.report['historical_K_consequences'];self.assertEqual(3385,k['K_package_count']);self.assertAlmostEqual(106.6,k['conditional_rear_extent_mm']);self.assertAlmostEqual(1.6,k['candidate_cover_excess_mm'])
        self.assertEqual(5,len(k['service_checks']));self.assertTrue(all(x['conditional_straight_withdrawal_conflict'] for x in k['service_checks']))
    def test_unknown_carriers_not_fit(self):
        self.assertEqual(28,len(self.report['nonOSC_source_groups']))
        for g in self.report['nonOSC_source_groups']:self.assertIsNone(g['new_carrier_geometry']);self.assertIsNone(g['new_carrier_service_volume'])
        for o in self.report['options'].values():self.assertFalse(o['adopted']);self.assertFalse(o['implemented']);self.assertEqual([],o['qualified_free_regions'])

if __name__=='__main__':unittest.main()
