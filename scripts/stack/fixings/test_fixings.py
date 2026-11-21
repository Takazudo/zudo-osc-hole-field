"""Tests of the ruled fixing list (ST-08 a2 part 1): a fresh run equals the retained files, the ruled list passes
the screens, and the checker fails on planted findings. No network and no KiCad."""
import copy
import itertools
import json
import math
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


def by_id(doc, fid):
    return next(f for f in doc['fixings'] if f['id'] == fid)


def rules(errs):
    return sorted({e[0] for e in errs})


class Staleness(unittest.TestCase):
    def test_regenerated_json_equals_the_retained_file(self):
        self.assertEqual(fx.render(DOC), fx.SITES_JSON.read_text(), 'stale; regenerate with: ' + fx.REGEN)

    def test_regenerated_readme_equals_the_retained_file(self):
        self.assertEqual(fixings_readme.render(DOC), fx.README.read_text(), 'stale; regenerate with: ' + fx.REGEN)

    def test_pins_cover_rows_sections_and_objects_not_whole_campaign_files(self):
        pins = RETAINED['provenance']['pins']
        self.assertEqual(sorted(pins['decision_rows_sha256']), sorted(fx.PINNED_ROWS))
        self.assertNotIn('MISSING', pins['decision_rows_sha256'].values())
        self.assertNotIn('MISSING', pins['review_sections_sha256'].values())
        self.assertFalse([p for p in pins['files_sha256'] if p.startswith(fx.CAMPAIGN) or p.endswith('README.md')])
        self.assertIn(fx.CANDIDATE + ' candidate.planes', pins['objects_sha256'])


class RuledList(unittest.TestCase):
    def test_the_ruled_list_passes_the_checker(self):
        self.assertEqual(fixings_check.check(RETAINED, INP), [])
        self.assertEqual(RETAINED['verdict'], 'DONE')
        self.assertEqual(RETAINED['ruled_findings'], [])

    def test_seventy_mm_for_every_sleeve_against_every_other_fixing(self):
        active = [f for f in RETAINED['fixings'] if f['active']]
        for s, o in itertools.product([f for f in active if f['kind'] != 'post'], active):
            if s['id'] != o['id']:
                self.assertGreaterEqual(math.dist(s['xy'], o['xy']), 70.0 - fx.EPS, (s['id'], o['id']))

    def test_schema_of_fixings_and_counts(self):
        keys = {'id', 'kind', 'xy', 'front_xy', 'front_board', 'boards', 'gap_mm', 'keepout_radius_mm', 'length_class', 'active'}
        for f in RETAINED['fixings']:
            self.assertTrue(keys <= set(f), f['id'])
        sleeves = [f for f in RETAINED['fixings'] if f['active'] and f['kind'] != 'post']
        self.assertEqual({f['kind'] for f in sleeves}, {'sleeve added'})
        self.assertEqual(sorted(f['id'] for f in sleeves), ['SLV-L1', 'SLV-L2', 'SLV-U1', 'SLV-U2'])
        self.assertEqual(RETAINED['counts']['fixings'], 22)
        self.assertEqual(RETAINED['counts']['fastener_operations']['total'], 44)
        self.assertFalse({'reserve', 'alternative'} & {f['kind'] for f in RETAINED['fixings']})

    def test_access_hole_inside_the_applied_keepout(self):
        self.assertTrue(all(h['inside_applied_keepout'] for h in RETAINED['access_holes']))

    def test_reproduced_scans_that_match_the_authority(self):
        sc, au = RETAINED['region_scans'], RETAINED['authority']['scans']
        # MC04-S6 (JL/JR synced to the floorplan, rev 4 link rebind) frees two more JL nodes than DA-03's scratch
        # runs; the authority record is historical and is not relabelled.
        self.assertEqual(au['JL']['all_parts_free'], 125)
        self.assertEqual(sc['JL']['all_parts_free'], 127)
        self.assertEqual(sc['JR']['clear'], au['JR']['clear'])
        self.assertEqual(sc['JR']['all_parts_free_nodes'], [[244.0, 24.0], [244.0, 25.0]])
        self.assertTrue(all(c['fails'] for c in sc['corners']))


class PlantedFindings(unittest.TestCase):
    def found(self, doc, rule):
        return [e for e in fixings_check.check(doc, INP) if e[0] == rule]

    def test_ruled_site_moved_onto_a_pad_fails(self):
        d = copy.deepcopy(RETAINED)
        s = by_id(d, 'SLV-U1')
        jack = next(f for f, c in fx.footprint_classes(INP)['JL'] if f['ref'] == 'J401')
        s['xy'] = s['front_xy'] = list(jack['pads'][0]['center'])
        self.assertTrue(any('panel hardware' in e[1] for e in self.found(d, 'site')))
        self.assertTrue(self.found(d, 'ruled'))

    def test_spacing(self):
        d = copy.deepcopy(RETAINED)
        s = by_id(d, 'SLV-L1')
        s['xy'] = s['front_xy'] = [s['xy'][0] + 10, 230.0]
        self.assertTrue(self.found(d, 'spacing'))

    def test_dropped_site_made_active(self):
        d = copy.deepcopy(RETAINED)
        by_id(d, 'JL-SUP-2')['active'] = True
        self.assertTrue(self.found(d, 'ruled'))

    def test_part_without_listed_move(self):
        d = copy.deepcopy(RETAINED)
        by_id(d, 'SLV-U2')['part_moves'].pop(0)
        self.assertTrue(self.found(d, 'moves'))

    def test_free_position_inside_a_keepout(self):
        d = copy.deepcopy(RETAINED)
        m = by_id(d, 'SLV-U2')['part_moves'][0]
        m['nearest_free_origin'] = list(m['origin'])
        self.assertTrue(any('free position of ' + m['ref'] in e[1] for e in self.found(d, 'moves')))

    def test_part_without_free_position_and_no_decision(self):
        d = copy.deepcopy(RETAINED)
        by_id(d, 'SLV-U2')['part_moves'][0]['nearest_free_origin'] = None
        self.assertTrue(any('no decision assigns it' in e[1] for e in self.found(d, 'moves')))

    def test_ceramic_without_listed_move(self):
        d = copy.deepcopy(RETAINED)
        by_id(d, 'POWER-P-+5V')['part_moves'] = []
        self.assertTrue(any('C4513' in e[1] for e in self.found(d, 'moves')))

    def test_stale_pin(self):
        d = copy.deepcopy(RETAINED)
        d['provenance']['pins']['decision_rows_sha256']['DS-73'] = '0' * 64
        self.assertTrue(any('DS-73' in e[1] for e in self.found(d, 'stale')))


if __name__ == '__main__':
    unittest.main()
