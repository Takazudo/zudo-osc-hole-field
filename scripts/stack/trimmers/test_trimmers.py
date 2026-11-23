"""Fault injection for candidate source and geometry claims."""
import copy
import json
import unittest

import check
import generate as gen


class CandidateChecks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.plan = json.loads(gen.OUT.read_text())
        cls.with_proposal = next(r['ref'] for r in cls.plan['records'] if r['proposal'])

    def changed(self):
        p = copy.deepcopy(self.plan)
        return p, next(r for r in p['records'] if r['ref'] == self.with_proposal)

    def test_recorded_candidate(self):
        self.assertEqual(check.validate(self.plan), [])

    def test_counts_follow_the_gate(self):
        # MC04-S10 Revision 1 (DS-148): 62 links and 455 gate rows after the four S10 holds
        gate = json.loads((check.ROOT / check.gen.SOURCES[0]).read_text())
        self.assertEqual(self.plan['source_counts'], {'replacement_footprints': len(gate['replacement']['footprints']),
                                                      'link_count': len([x for x in gate['links'] if x['placed']]),
                                                      'fixing_keepouts': len(gate['fixings']['keepouts'])})
        self.assertEqual(self.plan['source_counts'], {'replacement_footprints': 455, 'link_count': 62, 'fixing_keepouts': 22})

    def test_missing_adjustment(self):
        p, r = self.changed()
        p['records'].remove(r)
        self.assertTrue(any('missing/duplicate' in e for e in check.validate(p)))

    def test_stale_geometry(self):
        p, _ = self.changed()
        p['canonical_geometry_digest'] = '0' * 64
        self.assertTrue(any('stale canonical geometry' in e for e in check.validate(p)))

    def test_outside_board(self):
        p, r = self.changed()
        old = r['proposal']
        old['xy_mm'] = [500.0, 500.0]
        old['courtyard_mm'] = [499.0, 499.0, 501.0, 501.0]
        self.assertTrue(any('outside K outline' in e for e in check.validate(p)))

    def test_fixing_keepout(self):
        p, r = self.changed()
        x, y = 40.0, 160.0  # POWER-JL-+12V, retained fixing site.
        f = r['after_link_projection']
        c = f['courtyard_mm']
        w, h = c[2] - c[0], c[3] - c[1]
        r['proposal']['xy_mm'] = [x, y]
        r['proposal']['courtyard_mm'] = [x - w / 2, y - h / 2, x + w / 2, y + h / 2]
        self.assertTrue(any('fixing keepout' in e for e in check.validate(p)))

    def test_overlap_between_candidates(self):
        p, first = self.changed()
        second = next(r for r in p['records'] if r['proposal'] and r is not first)
        second['proposal'] = copy.deepcopy(first['proposal'])
        self.assertTrue(any('collides with' in e for e in check.validate(p)))

    def test_search_limit(self):
        p, r = self.changed()
        orig = r['after_link_projection']['xy_mm']
        xy = [orig[0] + 31.0, orig[1]]
        dx = xy[0] - r['proposal']['xy_mm'][0]
        r['proposal']['xy_mm'] = xy
        r['proposal']['courtyard_mm'] = [v + (dx if i % 2 == 0 else 0) for i, v in enumerate(r['proposal']['courtyard_mm'])]
        r['proposal']['distance_mm'] = 31.0
        self.assertTrue(any('exceeds assumed search radius' in e for e in check.validate(p)))

    def test_omitted_available_move(self):
        p, r = self.changed()
        r['proposal'] = None
        r['verdict'] = 'NO_COURTYARD_POSITION_WITHIN_30MM_NEEDS_DESIGN'
        self.assertTrue(any('available courtyard position omitted' in e for e in check.validate(p)))

    def test_changed_live_electrical_metadata(self):
        p, r = self.changed()
        r['nets'] = ['FALSE_NET']
        r['role'] = 'false:SAFE'
        r['module'] = 'FALSE_BLOCK'
        self.assertTrue(any('electrical metadata mismatch' in e for e in check.validate(p)))

    def test_stale_metadata_projection(self):
        p, _ = self.changed()
        p['board_metadata_digest'] = '0' * 64
        self.assertTrue(any('stale board metadata projection' in e for e in check.validate(p)))

    def test_nonfinite_recorded_distance(self):
        p, r = self.changed()
        r['proposal']['distance_mm'] = float('nan')
        self.assertTrue(any('nonfinite or invalid distance' in e for e in check.validate(p)))

    def test_false_service_and_guard_claims(self):
        p, r = self.changed()
        r['service_tool_access'] = 'MEASURED'
        r['guard_status'] = 'VERIFIED'
        r['node_sensitivity'] = 'INSENSITIVE'
        r['loop_length_mm'] = 0.0
        r['added_vias'] = 0
        self.assertTrue(any('unsupported electrical/service claim' in e for e in check.validate(p)))

    def test_false_access_verdict(self):
        p, r = self.changed()
        r['verdict'] = 'SAFE_TO_BUILD'
        r['access'] = 'FULLY_ACCESSIBLE'
        self.assertTrue(any('unsupported access verdict' in e for e in check.validate(p)))


if __name__ == '__main__':
    unittest.main()
