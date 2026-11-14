"""Tests of the fixing list (ST-08 a1 part 1): retained files equal a fresh run, the DS-66 rules, and one
fault-injection test per checker rule. No network and no KiCad: the boards are parsed with plain Python."""
import copy
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import fixings as fx  # noqa: E402
import fixings_check  # noqa: E402
import fixings_readme  # noqa: E402


def setUpModule():
    global DOC, INP, RETAINED
    DOC, INP = fx.generate()
    RETAINED = json.loads(fx.SITES_JSON.read_text())


def rules(errs):
    return [e[0] for e in errs]


def by_id(doc, fid):
    return next(f for f in doc['fixings'] if f['id'] == fid)


def first_added(doc, board):
    return next(f for f in doc['fixings'] if f['kind'] == 'sleeve added' and f['front_board'] == board)


class RetainedFiles(unittest.TestCase):
    def test_retained_json_equals_a_fresh_run(self):
        self.assertEqual(fx.render(DOC), fx.SITES_JSON.read_text(), 'stale; regenerate with: ' + fx.REGEN)

    def test_retained_readme_equals_a_fresh_run(self):
        self.assertEqual(fixings_readme.render(DOC), fx.README.read_text(), 'stale; regenerate with: ' + fx.REGEN)

    def test_provenance_binds_the_geometry_candidate(self):
        self.assertEqual(RETAINED['provenance']['input_sha256'][fx.CANDIDATE],
                         fx.sg.sha256_file(fx.ROOT / fx.CANDIDATE))

    def test_checker_on_the_retained_list_reports_only_the_recorded_findings(self):
        errs = fixings_check.check(RETAINED, INP)
        self.assertEqual([list(e) for e in errs], RETAINED['checker_findings'])
        self.assertEqual(rules(errs), [] if RETAINED['verdict'] == 'DONE' else ['coverage'])


class Ruling(unittest.TestCase):
    def test_named_sites_go_and_at_most_one_of_each_pair_stays(self):
        for sid in fx.NAMED_DROPS:
            self.assertEqual(by_id(RETAINED, sid)['kind'], 'sleeve dropped')
        for pr in fx.PAIRED:
            self.assertLessEqual(sum(by_id(RETAINED, s)['kind'] == 'sleeve kept' for s in pr), 1)

    def test_eighteen_posts_at_the_power_post_lands(self):
        posts = [f for f in RETAINED['fixings'] if f['kind'] == 'post']
        self.assertEqual(len(posts), 18)
        self.assertIn([227.5, 160], [p['xy'] for p in posts])

    def test_verdict_follows_the_coverage(self):
        cov = RETAINED['coverage']
        self.assertEqual(RETAINED['verdict'], 'DONE' if cov['after'][0] <= 90 else 'NEEDS_DESIGN')
        self.assertLess(cov['after'][0], cov['present_30'][0])
        self.assertGreaterEqual(cov['after'][0] + 1e-9, cov['lower_bound_any_selection'][0])

    def test_counts_and_plate(self):
        c = RETAINED['counts']
        active = [f for f in RETAINED['fixings'] if f['kind'] in ('sleeve kept', 'sleeve added')]
        self.assertEqual(c['long_19'] + c['short_17'], len(active))
        self.assertEqual(c['plate'], {'long': 10, 'short': 6})


class FaultInjection(unittest.TestCase):
    def errs(self, doc):
        return fixings_check.check(doc, INP)

    def new(self, doc, rule):
        base = {tuple(e) for e in RETAINED['checker_findings']}
        return [e for e in self.errs(doc) if e[0] == rule and tuple(e) not in base]

    def test_spacing_sleeve_within_70_mm(self):
        d = copy.deepcopy(RETAINED)
        s = first_added(d, 'JL')
        s['xy'] = s['front_xy'] = [s['xy'][0], 110.0]
        self.assertTrue(self.new(d, 'spacing'))

    def test_coverage_point_beyond_90_mm(self):
        d = copy.deepcopy(RETAINED)
        first_added(d, 'JL')['kind'] = 'sleeve dropped'
        found = self.new(d, 'coverage')
        self.assertTrue(found)
        self.assertGreater(float(found[0][1].split(' is ')[1].split(' mm')[0]), 100)

    def test_site_on_panel_hardware(self):
        d = copy.deepcopy(RETAINED)
        s = first_added(d, 'JL')
        s['xy'] = s['front_xy'] = [14.5, 29.0]  # on the locked jack J101
        self.assertTrue(any('panel hardware' in e[1] for e in self.new(d, 'site')))

    def test_site_on_a_tab(self):
        d = copy.deepcopy(RETAINED)
        s = first_added(d, 'P')
        s['xy'] = s['front_xy'] = [31.5, 197.0]
        self.assertTrue(any('tab TAB-CONTROL-O2' in e[1] for e in self.new(d, 'site')))

    def test_site_outside_a_board(self):
        d = copy.deepcopy(RETAINED)
        s = first_added(d, 'JL')
        s['xy'] = s['front_xy'] = [5.0, 100.0]
        self.assertTrue(any('board edge' in e[1] for e in self.new(d, 'site')))

    def test_moves_part_in_keepout_without_listed_move(self):
        d = copy.deepcopy(RETAINED)
        s = next(f for f in d['fixings'] if f['kind'] == 'sleeve added' and f['part_moves'])
        gone = s['part_moves'].pop(0)
        self.assertTrue(any(gone['ref'] in e[1] for e in self.new(d, 'moves')))

    def test_moves_free_position_inside_a_keepout(self):
        d = copy.deepcopy(RETAINED)
        s = next(f for f in d['fixings'] if f['kind'] == 'sleeve added'
                 and any(m['nearest_free_origin'] for m in f['part_moves']))
        m = next(m for m in s['part_moves'] if m['nearest_free_origin'])
        m['nearest_free_origin'] = list(m['origin'])
        self.assertTrue(any('free position of ' + m['ref'] in e[1] for e in self.new(d, 'moves')))

    def test_moves_ceramic_0805_or_larger_within_5_mm(self):
        d = copy.deepcopy(RETAINED)
        f = next(f for f in d['fixings'] if any(m['ceramic_0805_or_larger_within_5mm'] for m in f.get('part_moves', [])))
        ref = next(m['ref'] for m in f['part_moves'] if m['ceramic_0805_or_larger_within_5mm'])
        f['part_moves'] = [m for m in f['part_moves'] if m['ref'] != ref]
        self.assertTrue(any(ref in e[1] for e in self.new(d, 'moves')))

    def test_stale_input_hash(self):
        d = copy.deepcopy(RETAINED)
        d['provenance']['input_sha256'][fx.CANDIDATE] = '0' * 64
        self.assertTrue(any(fx.CANDIDATE in e[1] for e in self.new(d, 'stale')))


if __name__ == '__main__':
    unittest.main()
