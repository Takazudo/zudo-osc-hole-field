"""MC04-S12 tests: the pinned outcomes and the mutations M1 to M12 of the brief. They read result.json and run the
mutations; they do not re-run the search. Run: python -m unittest test_s12 (from this directory)."""
import copy
import json
import sys
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import s12  # noqa: E402
import joint_search as js  # noqa: E402
from s12 import lg  # noqa: E402

W = None


def world():
    global W
    if W is None:
        W = s12.World()
    return W


def geometry(w, lid, sx, sy, dname):
    """The geometry links_gate.candidate returns at a slot (every searched link out of `placed`), else the plain gate
    geometry with no tail extension."""
    rec = w.byid[lid]
    z = w.size_of(rec)
    d = [k for k, v in lg.DIR_NAMES.items() if v == dname][0]
    placed = w.placed_index({}, skip=s12.SEARCHED)
    c = rec['centre']
    import math
    dist = math.hypot(sx - c[0], sy - c[1])
    w.ctx.model.memo_for(None)
    why, cand = lg.candidate(w.ctx, placed, rec['front_board'], z, lg.rec_own(rec), sx, sy, d, dist, w.ctx.spare(rec['front_board'], z))
    if cand:
        return cand[1]
    return lg.gate_geometry(sx, sy, d, z, w.ctx.opts, hard=w.ctx.hard)


class Result(unittest.TestCase):
    def test_result_recorded(self):
        r = json.loads((HERE / 'result.json').read_text())
        self.assertIsNone(r['stop'])
        self.assertTrue(all(v in (True, None) for v in r['arm0'].values()), r['arm0'])
        self.assertEqual(sorted(r['verdicts']), sorted(s12.FIVE))
        for c in r['candidates']:
            body = json.loads((HERE / 'candidates' / ('scene-%d.json' % c['scene'])).read_text())
            self.assertEqual(body['status'], s12.STATUS)
            self.assertEqual(body['digest'], c['digest'])

    def test_protected_counts(self):
        pc = s12.protected_counts(world())
        self.assertEqual((pc['total'], pc['by_board'], pc['with_base_row']), (1734, {'JL': 287, 'JR': 265, 'K': 1182}, 131))
        self.assertEqual(pc['positionless_base_rows'], ['U1318', 'U1415', 'U4647', 'U5110', 'U5209', 'U5210', 'U8409'])


class Mutations(unittest.TestCase):
    L0102 = 'P-K-P-L13.01.01.02'
    L0101 = 'P-K-P-L13.01.01.01'

    def t1_refs(self, lid, sx, sy, d):
        w = world()
        bad, _ = w.t1(lid, geometry(w, lid, sx, sy, d))
        return [r for r, _ in bad]

    def test_m1(self):
        self.assertIn('R5256', self.t1_refs(self.L0102, 176.0, 196.25, '-y'))

    def test_m2(self):
        self.assertIn('R5257', self.t1_refs(self.L0102, 176.0, 198.25, '-y'))

    def test_m3a(self):
        self.assertIn('R5259', self.t1_refs(self.L0102, 176.0, 194.0, '-y'))

    def test_m3b(self):
        w = world()
        geo = geometry(w, self.L0102, 176.0, 196.25, '-y')
        saved = set(w.protected)
        try:
            w.protected.discard(('K', 'R5256'))
            bad, _ = w.t1(self.L0102, geo)
            tails = w.tails(self.L0102, geo)
        finally:
            w.protected.clear()
            w.protected.update(saved)
        self.assertNotIn('R5259', [r for r, _ in bad])
        self.assertIn(('K', 'R5259', 'K tail'), tails)

    def test_m4(self):
        self.assertIn('R8356', self.t1_refs(self.L0101, 201.1667, 197.4167, '+y'))

    def test_m5(self):
        w = world()
        geo = geometry(w, self.L0101, 202.1667, 195.6667, '+y')
        self.assertEqual(w.rule4(self.L0101, geo), 'covers the recorded courtyard of U8409')

    def test_m6(self):
        w = world()
        ic = next(k[1] for k in sorted(w.protected) if k[0] == 'K' and k[1].startswith('U') and k not in w.base_rows)
        fp = w.s.fps[('K', ic)]
        block = {'board': 'K', 'ic': ic, 'members': [ic], 'passives_moved': [],
                 'pose': {'face': fp['side'], 'turn_deg': 180, 'origin': fp['origin'], 'moved_mm': 0.0, 'shift_mm': [0.0, 0.0]}}
        j = s12.judge(w, {}, w.base_rows_list, overlay_blocks=[block])
        self.assertIn('A10', j['fails'])
        self.assertTrue(any(ic in x for x in j['fails']['A10']))

    def test_m7a(self):
        w = world()
        rows = copy.deepcopy(w.base_rows_list)
        r = next(x for x in rows if x['ref'] == 'R8431')
        r['new'] = [r['new'][0] + 0.25, r['new'][1]]
        f, _ = s12.check_rows(w, rows)
        self.assertTrue(any('R8431' in x for x in f.get('A2', [])))

    def test_m7b(self):
        w = world()
        rows = [x for x in copy.deepcopy(w.base_rows_list) if x['ref'] != 'R5251']
        f, info = s12.check_rows(w, rows)
        self.assertNotIn('A2', f)
        self.assertIn('K R5251', info['protected']['returned'])

    def test_m8(self):
        w = world()
        ovl = s12.gjson(s12.RETURNED, 'scripts/stack/studies/mc04_s10_l13/overlay.json')
        block = [b for b in ovl['blocks'] if b['ic'] == 'U4537']
        self.assertEqual(block[0]['pose']['origin'], [149.97, 182.68])
        j = s12.judge(w, {}, w.base_rows_list, overlay_blocks=block)
        a11 = ' '.join(j['fails'].get('A11', []))
        self.assertIn('/E5/HOLD_N', a11)
        self.assertIn('/E5/READY', a11)

    def test_m9(self):
        w = world()
        lid = 'P-K-P-L15.02.01.01'
        geo = w.byid[lid]['geometry']
        rule, why, _ = w.check_rules(lid, geo, 35.25)
        self.assertEqual(rule, 3, why)

    def test_m10_rider(self):
        """A hosted rider beyond its class distance: the rider's class limit is set below its recorded distance."""
        w = world()
        lid = self.L0102
        rec = copy.deepcopy(w.s.byid[lid])
        rec['riders_in'][0]['class'] = 'TEST'
        lim = w.s.limits
        saved = w.s.byid[lid]
        try:
            lim['TEST'] = 1.0
            w.s.byid[lid] = rec
            why = w.arm1.accept_for(lid, ())(rec['geometry'])
        finally:
            lim.pop('TEST', None)
            w.s.byid[lid] = saved
        self.assertTrue(why and why.startswith('rider'), why)

    def test_m10_trimmer(self):
        w = world()
        k = next(k for k, f in sorted(w.s.fps.items()) if k[0] == 'K' and k[1].startswith('RV') and f['side'] == 'B'
                 and k not in w.base_rows)
        fp = w.s.fps[k]
        rows = copy.deepcopy(w.base_rows_list) + [{
            'board': 'K', 'ref': k[1], 'package': fp['lib'], 'face': 'B', 'why': ['test'], 'old': fp['origin'],
            'courtyard': fp['courtyard'], 'new': [fp['origin'][0] + 1.0, fp['origin'][1]], 'new_face': 'F',
            'shift_mm': [1.0, 0.0], 'moved_mm': 1.0, 'step': 2, 'turned': False, 'new_courtyard': fp['courtyard']}]
        f, _ = s12.check_rows(w, rows)
        self.assertTrue(any(k[1] in x for x in f.get('A4', [])))

    def test_m11(self):
        r = json.loads((HERE / 'result.json').read_text())
        scenes = [json.loads((HERE / 'candidates' / ('scene-%d.json' % c['scene'])).read_text()) for c in r['candidates']]
        w = world()
        if not scenes:  # no candidate written: the digest rule is shown on the all-stay scene
            slots = [s12.hold_entry(w, lid, {'stay': True}, 'x') for lid in s12.SEARCHED]
            scenes = [{'slots': slots, 'digest': s12.digest({'slots': slots, 'rows': w.base_rows_list}), '_rows': w.base_rows_list}]
        for body in scenes:
            slots = copy.deepcopy(body['slots'])
            slots[0]['slot_centre'] = [slots[0]['slot_centre'][0] + 0.25, slots[0]['slot_centre'][1]]
            rows = body.get('_rows') or w.rows_only(w.scene_links(js.moves_from_scene(w, body)))
            self.assertNotEqual(s12.digest({'slots': slots, 'rows': rows}), body['digest'])

    def test_m12(self):
        w = world()
        rows = copy.deepcopy(w.base_rows_list)
        r = next(x for x in rows if x['ref'] == 'R8431')
        r.update({'new': None, 'new_face': None, 'shift_mm': None, 'moved_mm': None, 'step': 'no position', 'turned': False})
        r.pop('new_courtyard', None)
        f, _ = s12.check_rows(w, rows)
        self.assertEqual([x for x in f.get('A2', [])], ['K R8431: protected footprint loses its base position'])


if __name__ == '__main__':
    unittest.main()
