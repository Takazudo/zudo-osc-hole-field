"""MC04-S7 Revision 2: reviewed slot holds of the link gate (no KiCad, no network)."""
import copy
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))

import links_gate as lg  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]
GOPTS = json.loads((ROOT / 'design/stack/geometry/links/link-gate-options.json').read_text())
HOLD = {'link': 'JL-K-JL-L02', 'front_board': 'JL', 'centre': [133.5, 80.0], 'slot_centre': [121.5, 80.0],
        'direction': '+x', 'reason': 'r', 'ruling': 'Revision 2 item 1'}


def gopts(*holds):
    return {'slot_holds': {'value': list(holds)}}


def link(**kw):
    base = {'id': 'JL-K-JL-L02', 'front_board': 'JL', 'centre': [133.5, 80.0], 'placed': True,
            'slot_centre': [121.5, 80.0], 'direction': '+x'}
    base.update(kw)
    return base


class Holds(unittest.TestCase):
    def test_the_retained_hold_is_the_ruled_one(self):
        holds = lg.slot_holds(GOPTS)
        self.assertEqual(len(holds), 1)
        h = holds[0]
        self.assertEqual((h['link'], h['front_board'], h['centre'], h['slot_centre'], h['direction']),
                         ('JL-K-JL-L02', 'JL', [133.5, 80.0], [121.5, 80.0], '+x'))
        self.assertIn('Revision 2', h['ruling'])
        self.assertTrue(h['reason'])

    def test_a_hold_needs_its_reason_and_ruling(self):
        for key in ('reason', 'ruling', 'slot_centre'):
            bad = dict(HOLD)
            del bad[key]
            with self.assertRaisesRegex(ValueError, key):
                lg.slot_holds(gopts(bad))
        with self.assertRaisesRegex(ValueError, 'direction'):
            lg.slot_holds(gopts(dict(HOLD, direction='+z')))

    def test_held_slot_matches_front_and_centre_only(self):
        ctx = SimpleNamespace(gopts=gopts(HOLD))
        self.assertEqual(lg.held_slot(ctx, 'JL', (133.5, 80.0)), HOLD)
        self.assertIsNone(lg.held_slot(ctx, 'JR', (133.5, 80.0)))
        self.assertIsNone(lg.held_slot(ctx, 'JL', (133.5, 80.25)))
        self.assertIsNone(lg.held_slot(SimpleNamespace(gopts={}), 'JL', (133.5, 80.0)))

    def test_stale_or_unmatched_holds_fail(self):
        g = gopts(HOLD)
        self.assertEqual(lg.hold_errors(g, [link()]), [])
        self.assertRegex(lg.hold_errors(g, [link(id='JL-K-JL-L03')])[0], 'no such link')
        self.assertRegex(lg.hold_errors(g, [link(placed=False)])[0], 'not placed')
        self.assertRegex(lg.hold_errors(g, [link(centre=[134.0, 80.0])])[0], 'stale')
        self.assertRegex(lg.hold_errors(g, [link(slot_centre=[133.5, 70.0])])[0], 'not the held slot')

    def test_committed_gate_honours_the_hold(self):
        doc = json.loads(lg.LINK_GATE.read_text())
        self.assertEqual(lg.hold_errors(GOPTS, doc['links']), [])
        unresolved = {r['board'] + ':' + r['ref'] for r in doc['replacement']['footprints'] if r['new'] is None}
        self.assertTrue({'JL:U2119', 'JL:D2243'} <= unresolved)
        self.assertFalse({'JL:U2217', 'JL:U2219'} & unresolved)

    def test_search_takes_only_the_held_slot(self):
        seen = []
        real = lg.candidate

        def fake(ctx, placed, front, size, own, sx, sy, d, dist, spare, lengthen=True, gm=None):
            seen.append((sx, sy, lg.DIR_NAMES[d]))
            return ('probe', None), None
        ctx = SimpleNamespace(gopts=gopts(HOLD), step0=0.5, w=1.0, spare=lambda f, s: 0.0, opts={}, hard=4.0,
                              grid=lambda step: [(0.0, 0.0), (0.5, 0.0)])
        lg.candidate = fake
        real_gm = lg.GeoMaker
        lg.GeoMaker = lambda *a, **k: None
        try:
            best, _ = lg.search(ctx, None, 'JL', (133.5, 80.0), None, None)
        finally:
            lg.candidate, lg.GeoMaker = real, real_gm
        self.assertIsNone(best)
        self.assertEqual(seen, [(121.5, 80.0, '+x')])


if __name__ == '__main__':
    unittest.main()
