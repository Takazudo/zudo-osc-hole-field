"""MC04-S7 Revision 4: the GH jack header sites."""
import unittest

import scripts.checks.connector_packing35 as cp


class JackSites(unittest.TestCase):
    def test_revision_4_sites(self):
        self.assertEqual(len(cp.JACK_SITES['JL']), 27)
        self.assertEqual(cp.JACK_SITES['JL'][-2:], [(142, 122), (159, 122)])
        self.assertEqual(len(cp.JACK_SITES['JR']), 30)
        self.assertEqual(cp.JACK_SITES['JR'][-3:], [(193, 24), (227, 24), (295, 24)])
        for board, sites in cp.JACK_SITES.items():
            self.assertEqual(len(set(sites)), len(sites), board)

    def test_short_site_list_fails_clearly(self):
        saved = cp.JACK_SITES['JR']
        cp.JACK_SITES['JR'] = saved[:-1]
        try:
            with self.assertRaisesRegex(ValueError, 'JR-K header sites run short: header 30 needs a site but JR has 29'):
                cp.candidate()
        finally:
            cp.JACK_SITES['JR'] = saved

    def test_current_packing_uses_every_site(self):
        report = cp.candidate()
        self.assertEqual(report['errors'], [])
        self.assertEqual(report['jack_sites_used'], {'JL': 27, 'JR': 30})


class Fixings(unittest.TestCase):
    HEADER = {'id': 'JR-K-29-JR', 'board': 'JR', 'land_courtyard_mm': [237.03, 20.95, 250.97, 27.05]}
    SLEEVE = {'id': 'SLV-U2', 'active': True, 'xy': [244.0, 24.0], 'keepout_radius_mm': {'K': 4.05, 'JR': 3.75}}

    def test_header_on_a_sleeve_fails(self):
        self.assertRegex(cp.fixing_errors([self.HEADER], [self.SLEEVE])[0], 'header/fixing overlap JR-K-29-JR SLV-U2')

    def test_inactive_or_other_board_fixings_are_ignored(self):
        self.assertEqual(cp.fixing_errors([self.HEADER], [dict(self.SLEEVE, active=False)]), [])
        self.assertEqual(cp.fixing_errors([self.HEADER], [dict(self.SLEEVE, keepout_radius_mm={'P': 4.0})]), [])

    def test_only_the_recorded_pre_existing_conflict_is_listed(self):
        self.assertEqual(cp.KNOWN_FIXING_CONFLICTS, {('JL-P-4-P', 'SLV-L1')})
        report = cp.candidate()
        heads = [h for h in report['headers'] if h['id'] == 'JL-P-4-P']
        sleeve = {'id': 'SLV-L1', 'active': True, 'xy': [93.0, 276.0], 'keepout_radius_mm': {'K': 4.05, 'P': 3.75}}
        self.assertTrue(cp.fixing_errors(heads, [sleeve], known=set()))
        self.assertEqual(cp.fixing_errors(heads, [sleeve]), [])

    def test_every_current_site_clears_the_fixings(self):
        report = cp.candidate()
        self.assertFalse([e for e in report['errors'] if 'fixing' in e])
        self.assertEqual(report['errors'], [])


if __name__ == '__main__':
    unittest.main()
