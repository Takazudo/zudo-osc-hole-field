"""MC04-S7 Revision 11: check.py's fixing_reach misses are exactly the 108 baseline pairs plus the four ruled
interim-GH exceptions, with the reach limits, the fixing list and the declared flags unchanged (no KiCad, no network)."""
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import check  # noqa: E402
import fixing_reach_exceptions as fre  # noqa: E402
import stackgeom as sg  # noqa: E402

RULED = ['JL-K-26', 'JL-K-27', 'JR-K-28', 'JR-K-29']


def setUpModule():
    global CI, CTX, DOC, REC, DETAIL
    raw = sg.load_raw()
    CI = sg.canonical_inputs(raw, sg.load_boards(raw))
    CTX = check.Context(CI)
    DOC = json.loads(sg.CANDIDATE.read_text())
    REC = json.loads(fre.OUT.read_text())
    res = check.Result()
    check.check_fixing_reach(DOC['candidate'], CTX, res)
    DETAIL = res.checks['fixing_reach']['detail']


class FixingReachPin(unittest.TestCase):
    def test_record_is_current(self):
        self.assertEqual(json.dumps(fre.build(), indent=1) + '\n', fre.OUT.read_text())

    def test_the_ruled_exceptions_are_exactly_the_four(self):
        self.assertEqual([r['pair'] for r in REC['interim_gh_exceptions']], RULED)
        self.assertEqual(REC['baseline']['misses'], 108)
        self.assertEqual(len(set(REC['baseline']['pairs'])), 108)
        self.assertFalse(set(RULED) & set(REC['baseline']['pairs']))

    def test_misses_are_the_baseline_plus_the_four_by_pair_id(self):
        missed = sorted(m['pair'] for m in DETAIL['runs']['declared']['missed_pairs'])
        self.assertEqual(missed, sorted(REC['baseline']['pairs'] + RULED))

    def test_each_exception_keeps_its_recorded_distance_and_fixing(self):
        by = {m['pair']: m for m in DETAIL['runs']['declared']['missed_pairs']}
        for r in REC['interim_gh_exceptions']:
            m = by[r['pair']]
            self.assertEqual((m['xy'], m['worst_mm'], m['K_side_nearest'], m['front_side_nearest']),
                             (r['xy'], r['worst_mm'], r['K_side_nearest'], r['front_side_nearest']), r['pair'])

    def test_limits_fixing_list_and_declared_flags_are_unchanged(self):
        fx = CI['parameters']['fixings']
        self.assertEqual((fx['reach_mm'], fx['exception_reach_mm']), (40, 50))
        self.assertEqual((DETAIL['reach_mm'], DETAIL['exception_reach_mm']), (40, 50))
        self.assertEqual(DOC['candidate']['fixings'], CTX.reference['fixings'])
        declared = sorted(f['id'] for f in DOC['candidate']['fixings'] if f['declared'])
        self.assertEqual(len(declared), REC['limits']['declared_fixings'])
        self.assertFalse([d for d in declared if d.startswith('SLV-')], 'option (b) is not applied')

    def test_option_b_is_recorded_not_applied(self):
        b = REC['option_b_gate_a_candidate']
        self.assertIn('NOT APPLIED', b['status'])
        self.assertEqual(b['figure']['distances_mm'], {'JR-K-28': 51.0, 'JR-K-29': 17.0})


if __name__ == '__main__':
    unittest.main()
