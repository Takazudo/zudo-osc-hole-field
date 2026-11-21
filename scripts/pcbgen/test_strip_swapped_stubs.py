"""Pure tests of the swapped-package stub walk (no KiCad)."""
import unittest

from scripts.pcbgen.strip_swapped_stubs import accepted, trace_chains


def seg(a, b, layer='F.Cu', net='N'):
    return {'a': a, 'b': b, 'layer': layer, 'net': net, 'length': abs(a[0] - b[0]) + abs(a[1] - b[1])}


class StubWalk(unittest.TestCase):
    def test_chain_stops_at_the_first_via(self):
        segs = {'s1': seg((0, 0), (1, 0)), 's2': seg((1, 0), (2, 0)), 's3': seg((2, 0), (3, 0))}
        stop = lambda p, layer, sid: 'via' if p == (2, 0) else None  # noqa: E731
        c, = trace_chains(segs, [('s1', 'a')], stop)
        self.assertEqual((c['segments'], c['stop']), (['s1', 's2'], 'via'))  # s3 beyond the via stays

    def test_chain_stops_before_a_t_junction(self):
        segs = {'s1': seg((0, 0), (1, 0)), 's2': seg((1, 0), (2, 0)), 's3': seg((1, 0), (1, 1))}
        c, = trace_chains(segs, [('s1', 'a')], lambda *a: None)
        self.assertEqual((c['segments'], c['stop']), (['s1'], 'T-junction'))

    def test_other_layers_and_unconnected_tracks_are_not_followed(self):
        segs = {'s1': seg((0, 0), (1, 0)), 's2': seg((1, 0), (2, 0), layer='B.Cu'), 's3': seg((5, 5), (6, 5))}
        c, = trace_chains(segs, [('s1', 'b')], lambda *a: None)
        self.assertEqual((c['segments'], c['stop']), (['s1'], 'open end'))

    def test_start_from_either_end_and_stop_at_another_part(self):
        segs = {'s1': seg((0, 0), (1, 0)), 's2': seg((2, 0), (1, 0))}
        stop = lambda p, layer, sid: 'pad of another part' if p == (2, 0) else None  # noqa: E731
        c, = trace_chains(segs, [('s1', 'a')], stop)
        self.assertEqual((c['segments'], c['stop'], c['stop_point']), (['s1', 's2'], 'pad of another part', [2, 0]))

    def test_long_or_zone_touching_chains_are_rejected(self):
        chains = [{'segments': ['a'], 'length': 5.0, 'stop': 'via'},
                  {'segments': ['b'], 'length': 25.0, 'stop': 'via'},
                  {'segments': ['c'], 'length': 1.0, 'stop': 'zone'}]
        ok, bad = accepted(chains, 20.0)
        self.assertEqual([c['segments'] for c in ok], [['a']])
        self.assertEqual(sorted(c['reason'] for c in bad), ['longer than 20 mm', 'touches a zone'])


if __name__ == '__main__':
    unittest.main()
