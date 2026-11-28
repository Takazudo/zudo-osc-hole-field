"""MC04-S15 unit tests: the brief's fixtures F to F9 and mutations M1 to M26, written before the recorded run.

Each mutation states its full expected vector over NG1 to NG7 (P pass, F fail, – not evaluated); a differing vector is
STOP 3. Further tests cover the derived S12 functions' switch and the C4 pad poses (hand values written here).
"""
import copy
import math
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import no_growth as ng  # noqa: E402

K = 'K'


def part(ref, pad1, origin, pad2, net='N', board=K, protected=True, other='GND', pin_record=True, side='B'):
    pads = [(0, '1', pad1)] + ([(1, '2', pad2)] if pad2 is not None else [])
    pins = {'1': net, '2': other} if pin_record else {}
    xs = [p[0] for _, _, p in pads] + [origin[0]]
    ys = [p[1] for _, _, p in pads] + [origin[1]]
    return (board, ref), {'origin': tuple(origin), 'side': side, 'pads': pads, 'pins': pins, 'pin_record': pin_record,
                          'protected': protected,
                          'courtyard': [min(xs) - 0.4, min(ys) - 0.4, max(xs) + 0.4, max(ys) + 0.4]}


U1 = part('U1', (0, 0), (0, 0), None)
R2 = part('R2', (3, 0), (3, 0.75), (3, 1.5))
R4 = part('R4', (5, 2), (5, 1.25), (5, 0.5))
R1 = part('R1', (10, 0), (10.75, 0), (11.5, 0))
R3 = part('R3', (0, 4), (0.75, 4), (1.5, 4))
R5 = part('R5', (0, 1), (0.75, 1), (1.5, 1))
C9 = part('C9', (6, 0), (6.75, 0), (7.5, 0), protected=False)
C7 = part('C7', (20, 20), (20.75, 20), (21.5, 20), net='X', protected=False)
J1 = part('J1', (30, 30), (30, 30), (31, 30), protected=False, pin_record=False)
R9 = part('R9', (4, 0), (4.75, 0), (5.5, 0), board='P', protected=False)


def geo_at(kxy, fxy=(50.0, 50.0)):
    return {'K_connector': [kxy[0] - 1, kxy[1] - 1, kxy[0] + 1, kxy[1] + 1],
            'front_connector': [fxy[0] - 1, fxy[1] - 1, fxy[0] + 1, fxy[1] + 1]}


class Fx:
    """One fixture: footprints, links, paper and base scenes (base equal to paper unless stated)."""

    def __init__(self, parts, links=None, open_ics=(), paper_override=None, base_override=None, rename=None):
        fps = dict(copy.deepcopy(p) for p in parts)
        if rename:
            for fp in fps.values():
                fp['pins'] = {k: rename.get(v, v) for k, v in fp['pins'].items()}
        self.fps = fps
        self.links = links or {}
        nets = {lid: set(x['nets']) for lid, x in self.links.items()}
        front = {lid: x['front'] for lid, x in self.links.items()}
        self.model = ng.Model(fps, nets, front, open_ics=open_ics)
        self.paper_poses = {k: (fp['origin'], fp['side']) for k, fp in fps.items()}
        self.paper_poses.update(paper_override or {})
        self.base_poses = dict(self.paper_poses)
        self.base_poses.update(base_override or {})
        self.paper = self.scene(self.paper_poses, name='paper')
        self.base = self.scene(self.base_poses, name='base')

    def courtyards(self, poses):
        out = {}
        for k, fp in self.fps.items():
            pos = poses.get(k, (None, None))[0]
            if pos is None:
                continue
            c = fp['courtyard']
            dx, dy = pos[0] - fp['origin'][0], pos[1] - fp['origin'][1]
            out[k] = [c[0] + dx, c[1] + dy, c[2] + dx, c[3] + dy]
        return out

    def scene(self, poses, turns=None, links=None, rects=None, name='scene'):
        L = {lid: x['geo'] for lid, x in self.links.items()} if links is None else links
        R = rects if rects is not None else {lid: x.get('rects', []) for lid, x in self.links.items()}
        return ng.Scene(poses, turns or {}, L, R, self.courtyards(poses), name)

    def shift_pad_to(self, ref, xy, board=K, pad=0):
        """Scene poses with `ref` shifted so that its pad `pad` lands at `xy`."""
        k = (board, ref)
        fp = self.fps[k]
        p0 = fp['pads'][pad][2]
        bpos = self.base_poses[k][0]
        bpad = (p0[0] - fp['origin'][0] + bpos[0], p0[1] - fp['origin'][1] + bpos[1])
        poses = dict(self.base_poses)
        poses[k] = ((bpos[0] + xy[0] - bpad[0], bpos[1] + xy[1] - bpad[1]), self.base_poses[k][1])
        return poses

    def run(self, scene):
        return self.model.evaluate(self.paper, self.base, scene)


def F(**kw):
    return Fx([U1, R2, R4, R1], **kw)


def F2():
    return Fx([U1, R1, R3, R5])


def F3(**kw):
    return Fx([U1, R2, R1], **kw)


def F4(**kw):
    return Fx([U1, R2, R1, C9], **kw)


def vec(s):
    return [c if c != '-' else '–' for c in s.replace(' ', '')]


class Fixtures(unittest.TestCase):
    def fig(self, fx, scene, net='N', board=K):
        f = fx.model.figures(scene, net, board, cache=False)
        return f['extent'], f['tree']

    def test_base_figures(self):
        self.assertEqual(self.fig(F(), F().base), (12, 14))
        self.assertEqual(self.fig(F2(), F2().base), (14, 14))
        self.assertEqual(self.fig(F3(), F3().base), (10, 10))
        self.assertEqual(self.fig(F4(), F4().base), (10, 10))
        f5 = F3(links={'L': {'nets': ['N'], 'front': 'P', 'geo': geo_at((6, 0))}})
        self.assertEqual(self.fig(f5, f5.base), (10, 10))
        f6 = F6()
        self.assertEqual(self.fig(f6, f6.base), (10, 10))
        self.assertEqual(self.fig(f6, f6.base, board='P'), (4, 4))
        f7 = F7()
        self.assertEqual(self.fig(f7, f7.paper), (10, 10))
        self.assertEqual(self.fig(f7, f7.base), (12, 12))
        f8 = F8()
        self.assertEqual(self.fig(f8, f8.base), (8, 8))
        f9 = F9()
        self.assertEqual(self.fig(f9, f9.paper), (10, 10))
        self.assertEqual(self.fig(f9, f9.base), (12, 12))


def F5():
    return F3(links={'L': {'nets': ['N'], 'front': 'P', 'geo': geo_at((6, 0))}})


def F6():
    return Fx([U1, R2, R9], links={'L': {'nets': ['N'], 'front': 'P', 'geo': geo_at((10, 0), (0, 0))}})


def F7():
    k = (K, 'R1')
    return F3(base_override={k: ((12.75, 0), 'B')})


def F8():
    k = (K, 'R1')
    return F3(base_override={k: ((8.75, 0), 'B')})


def F9():
    k = (K, 'C9')
    return F4(base_override={k: ((12.75, 0), 'B')})


class Mutations(unittest.TestCase):
    def check(self, res, expected):
        self.assertEqual(res['vector'], vec(expected), res)

    def fig(self, fx, scene, board=K):
        f = fx.model.figures(scene, 'N', board, cache=False)
        return f

    def test_m1(self):
        fx = F()
        sc = fx.scene(fx.shift_pad_to('R1', (10.25, 0)))
        self.check(fx.run(sc), 'FFFPPPP')
        f = self.fig(fx, sc)
        self.assertAlmostEqual(f['extent'], 12.25)
        self.assertAlmostEqual(f['tree'], 14.25)
        self.assertAlmostEqual(max(f['pairs'].values()), 10.25)

    def test_m2(self):
        fx = F()
        sc = fx.scene(fx.shift_pad_to('R2', (7, 0)))
        self.check(fx.run(sc), 'PPFPPPP')
        f = self.fig(fx, sc)
        self.assertEqual((f['extent'], f['tree']), (12, 14))
        self.assertAlmostEqual(f['pairs'][(('pad', K, 'U1', 0), ('pad', K, 'R2', 0))], 7)

    def test_m3(self):
        fx = F2()
        sc = fx.scene(fx.shift_pad_to('R5', (0.5, 0.5)))
        self.check(fx.run(sc), 'PFPPPPP')
        f = self.fig(fx, sc)
        self.assertEqual((f['extent'], f['tree']), (14, 15))
        self.assertAlmostEqual(f['pairs'][(('pad', K, 'U1', 0), ('pad', K, 'R5', 0))], math.sqrt(0.5))

    def test_m4(self):
        fx = F()
        sc = fx.scene(fx.shift_pad_to('R1', (9, 0)))
        self.check(fx.run(sc), 'PPPPPPP')
        f = self.fig(fx, sc)
        self.assertEqual((f['extent'], f['tree']), (11, 13))

    def test_m5_tie(self):
        fx = F()
        self.check(fx.run(fx.scene(fx.shift_pad_to('R4', (5, -2)))), 'PPPPPPP')

    def test_m6(self):
        fx = F()
        self.check(fx.run(fx.scene(fx.shift_pad_to('R4', (5, -2.000001)))), 'FFFPPPP')

    def test_m7_face(self):
        fx = F()
        poses = dict(fx.base_poses)
        poses[(K, 'R4')] = (fx.base_poses[(K, 'R4')][0], 'F')
        self.check(fx.run(fx.scene(poses)), 'PPPFPPP')

    def test_m8_turn(self):
        fx = F3()
        sc = fx.scene(dict(fx.base_poses), turns={(K, 'R1'): 90})
        self.check(fx.run(sc), 'FFFPPPP')
        f = self.fig(fx, sc)
        self.assertAlmostEqual(f['extent'], 11.5)
        self.assertAlmostEqual(f['tree'], 11.5)

    def tail_link(self, rect):
        return {'T': {'nets': [], 'front': 'P', 'geo': geo_at((80, 80)), 'rects': [(K, 'B', rect, 'K tail')]}}

    def test_m9_cover(self):
        fx = Fx([U1, R2, R4, R1], links=self.tail_link([8.0, -1.0, 9.2, 1.0]))
        self.check(fx.run(fx.scene(fx.shift_pad_to('R1', (9, 0)))), 'PPPPFPP')

    def test_m10_cover_exemption(self):
        fx = Fx([U1, R2, R4, R1], links=self.tail_link([8.0, -1.0, 10.5, 1.0]))
        self.check(fx.run(fx.scene(fx.shift_pad_to('R1', (9, 0)))), 'PPPPPPP')

    def test_m11(self):
        fx = F4()
        r = fx.run(fx.scene(fx.shift_pad_to('C9', (12, 0))))
        self.check(r, 'FFFPPPP')
        self.assertEqual(r['evaluated']['N']['class'], 'Other')

    def test_m12(self):
        fx = Fx([U1, R2, R4, R1, C7])
        r = fx.run(fx.scene(fx.shift_pad_to('C7', (25, 20))))
        self.check(r, '–––PPPP')
        self.assertEqual(r['evaluated'], {})
        self.assertTrue(r['pass'])

    def test_m13_link_end(self):
        fx = F5()
        r = fx.run(fx.scene(dict(fx.base_poses), links={'L': geo_at((12, 0))}))
        self.check(r, 'FFFPPPP')
        self.assertTrue(r['tallies']['link_end_alone'])

    def test_m14_direction_flip(self):
        fx = F5()
        r = fx.run(fx.scene(dict(fx.base_poses), links={'L': geo_at((6, -19))}))
        self.check(r, 'FFFPPPP')
        self.assertIn('N', r['evaluated'])

    def test_m15_k_and_p(self):
        fx = F6()
        sc = fx.scene(dict(fx.base_poses), links={'L': geo_at((9, 0), (-1, 0))})
        r = fx.run(sc)
        self.check(r, 'FFPPPPP')
        bk, bp = r['evaluated']['N']['boards']['K'], r['evaluated']['N']['boards']['P']
        self.assertEqual((bk['scene']['extent'], bk['scene']['tree'], bk['fails']), (9, 9, []))
        self.assertEqual((bp['scene']['extent'], bp['scene']['tree']), (5, 5))
        self.assertEqual(bk['base']['extent'] + bp['base']['extent'], 14)
        self.assertEqual(bk['scene']['extent'] + bp['scene']['extent'], 14)

    def test_m16(self):
        fx = F7()
        r = fx.run(fx.scene(fx.shift_pad_to('R1', (11, 0))))
        self.check(r, 'FFFPPPP')
        self.assertEqual(r['evaluated']['N']['class'], 'P-moved')
        self.assertTrue(r['tallies']['stricter_limit_alone'])
        self.assertTrue(r['tallies']['inherited_excess_alone'])

    def test_m17(self):
        fx = F7()
        self.check(fx.run(fx.scene(fx.shift_pad_to('R1', (10, 0)))), 'PPPPPPP')

    def test_m18(self):
        fx = F8()
        r = fx.run(fx.scene(fx.shift_pad_to('R1', (9, 0))))
        self.check(r, 'FFFPPPP')
        self.assertTrue(r['tallies']['stricter_limit_alone'])

    def test_m19_return_to_paper_lengthens(self):
        fx = F8()
        self.check(fx.run(fx.scene(fx.shift_pad_to('R1', (10, 0)))), 'FFFPPPP')

    def test_m20(self):
        fx = F9()
        self.check(fx.run(fx.scene(fx.shift_pad_to('C9', (11, 0)))), 'PPPPPPP')
        r = fx.run(fx.scene(fx.shift_pad_to('C9', (12.01, 0))))
        self.check(r, 'FFFPPPP')
        self.assertEqual(r['evaluated']['N']['class'], 'Other')

    def test_m21_open_ic(self):
        fx = F(open_ics={(K, 'U1')}, base_override={(K, 'U1'): (None, None)})
        poses = dict(fx.base_poses)
        poses.pop((K, 'U1'))  # claimed: no row, so the scene has no pose of its own
        r = fx.run(fx.scene(poses))
        self.check(r, '–––PPPP')
        self.assertEqual((r['moved'], r['evaluated']), ([], {}))

    def test_m22_open_ic_convention_off(self):
        fx = F(paper_override={(K, 'U1'): (None, None)}, base_override={(K, 'U1'): (None, None)})
        poses = dict(fx.base_poses)
        poses[(K, 'U1')] = ((0, 0), 'B')
        sc = fx.scene(poses)
        r = fx.run(sc)
        self.check(r, 'FFFPPPP')
        b = r['evaluated']['N']['boards']['K']
        self.assertEqual((b['scene']['extent'], b['scene']['tree']), (12, 14))
        self.assertEqual((b['base']['extent'], b['base']['tree']), (9, 11))

    def test_m23_lost_position(self):
        fx = F()
        poses = dict(fx.base_poses)
        poses[(K, 'R2')] = (None, None)
        self.check(fx.run(fx.scene(poses)), 'FFFPPFP')

    def test_m24_no_pin_record(self):
        fx = Fx([U1, R2, R4, R1, J1])
        self.check(fx.run(fx.scene(fx.shift_pad_to('J1', (33, 30)))), '–––PPPF')

    def test_m25_rail_renamed(self):
        fx = Fx([U1, R2, R4, R1], rename={'GND': 'AGND2'})
        r = fx.run(fx.scene(fx.shift_pad_to('R1', (10.25, 0))))
        self.check(r, 'FFFPPPP')
        self.assertEqual(sorted(r['evaluated']), ['AGND2', 'N'])

    def test_m26_scene_digest(self):
        body = {'slots': [{'link': 'L', 'slot_centre': [1.0, 2.0]}], 'rows': [{'board': K, 'ref': 'R1', 'new': [1, 2]}]}
        d = ng.scene_digest(body['slots'], body['rows'])
        bad = copy.deepcopy(body)
        bad['rows'][0]['new'] = [1, 2.5]
        self.assertNotEqual(ng.scene_digest(bad['slots'], bad['rows']), d)
        self.assertEqual(ng.scene_digest(body['slots'], body['rows']), d)


class Geometry(unittest.TestCase):
    def test_rmst_brute_force(self):
        import itertools
        import random
        rnd = random.Random(7)
        for n in range(2, 7):
            for _ in range(20):
                pts = [(rnd.uniform(0, 10), rnd.uniform(0, 10)) for _ in range(n)]
                self.assertAlmostEqual(ng.rmst(pts), ng.brute_rmst(pts))
                self.assertGreaterEqual(ng.rmst(pts) + 1e-9, ng.hpwl(pts))
        self.assertEqual(len(list(itertools.islice(range(3), 3))), 3)

    def test_c4_hand_values(self):
        """C4: three synthetic poses of R8356 (paper origin (205.66, 208.14), face B, pad 1 at (205.66, 208.89),
        pad 2 at (205.66, 207.39)); hand values written before the run."""
        fp = {'origin': (205.66, 208.14), 'side': 'B'}
        p1, p2 = (205.66, 208.89), (205.66, 207.39)
        # shift by (+2.0, -1.0)
        for xy, want in ((p1, (207.66, 207.89)), (p2, (207.66, 206.39))):
            got = ng.pad_xy(fp, xy, ((207.66, 207.14), 'B'), 0)
            self.assertAlmostEqual(got[0], want[0])
            self.assertAlmostEqual(got[1], want[1])
        # 90 degree turn in place: (0, +0.75) -> (-0.75, 0); (0, -0.75) -> (+0.75, 0)
        for xy, want in ((p1, (204.91, 208.14)), (p2, (206.41, 208.14))):
            got = ng.pad_xy(fp, xy, ((205.66, 208.14), 'B'), 90)
            self.assertAlmostEqual(got[0], want[0])
            self.assertAlmostEqual(got[1], want[1])
        # face flip in place: the pads lie on the mirror axis, so they do not move
        for xy in (p1, p2):
            got = ng.pad_xy(fp, xy, ((205.66, 208.14), 'F'), 0)
            self.assertAlmostEqual(got[0], xy[0])
            self.assertAlmostEqual(got[1], xy[1])


class C7Hand(unittest.TestCase):
    def test_c7_hand_values(self):
        """C7 hand values for P-K-P-L03.01 at the base (from the record's geometry, written before the run): K connector
        [205.3667, 179.8333, 223.9667, 185.9333], front connector [205.3667, 204.7333, 223.9667, 210.8333]."""
        self.assertEqual(ng.C7_K, (214.6667, 182.8833))
        self.assertEqual(ng.C7_FRONT, (214.6667, 207.7833))


if __name__ == '__main__':
    unittest.main()
