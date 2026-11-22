"""MC04-S7 Revision 4: the GH jack header sites."""
import unittest

import scripts.checks.connector_packing35 as cp


class JackSites(unittest.TestCase):
    def test_revision_4_sites(self):
        self.assertEqual(len(cp.JACK_SITES['JL']), 27)
        self.assertEqual(cp.JACK_SITES['JL'][-2:], [(142, 122), (159, 122)])
        self.assertEqual(len(cp.JACK_SITES['JR']), 30)
        self.assertEqual(cp.JACK_SITES['JR'][-3:], [(193, 24), (244, 24), (295, 24)])
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


if __name__ == '__main__':
    unittest.main()
