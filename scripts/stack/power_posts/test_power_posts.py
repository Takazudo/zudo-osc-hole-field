"""Unit tests for the ST-04 power-post calculator: no network, no KiCad."""
import copy
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import power_posts as pp  # noqa: E402


class Reproduction(unittest.TestCase):
    def setUp(self):
        self.d = pp.load()

    def test_present_drop_matches_partition(self):
        drop, rwire = pp.present_drop_mV(self.d)
        part = json.loads((pp.ROOT / 'design/partition/partition.json').read_text())['power']['worst_load_distribution_drop_mV']
        for rail in pp.RAILS:
            self.assertAlmostEqual(drop[rail], part[rail], places=6)
        self.assertAlmostEqual(rwire, 0.00163, places=9)
        self.assertEqual([round(drop[r], 3) for r in pp.RAILS], [15.321, 15.058, 11.113])

    def test_present_shares_match_partition(self):
        part = json.loads((pp.ROOT / 'design/partition/partition.json').read_text())['power']['GH_normal_return_bounds']
        for b, a in pp.present_shares(self.d).items():
            self.assertAlmostEqual(a, part[b]['worst_single_contact_A'], places=9)

    def test_present_budget_matches_supply(self):
        sup = json.loads((pp.ROOT / 'design/power/supply-architecture.json').read_text())
        text = json.dumps(sup)
        for rail, val in pp.present_budget_V(self.d).items():
            self.assertAlmostEqual(val, v := self.d['terms']['present_budget_V']['value'][rail], places=9, msg=v)
        self.assertIn('"worst_rail_plus_return_loss_V": {"+12V": 0.194', text)


class StackScreens(unittest.TestCase):
    def setUp(self):
        self.d = pp.load()
        self.r = pp.results(self.d)

    def test_limits_met_on_paper(self):
        self.assertTrue(all(x < 20 for x in self.r['worst_drop_mV'].values()))
        self.assertTrue(all(x < 0.20 for x in self.r['budget_V'].values()))
        self.assertTrue(all(x < 20 for x in self.r['el_total_mV'].values()))
        for b in pp.BRANCHES:
            self.assertLess(self.r['joint_ohm'][b], min(self.r['requirement_ohm'].values()))
            self.assertLess(self.r['shares'][b], self.d['terms']['header_contact_limit_A']['value'])

    def test_gh_limit_is_exceeded_and_reported(self):
        for b in pp.BRANCHES:
            self.assertGreater(self.r['shares'][b], 0.5)
        floor = 4.6 * 0.0005 / (0.00436 + 0.0005)
        for b in pp.BRANCHES:
            self.assertGreater(self.r['shares'][b], floor)

    def test_requirement_formula_hits_20mV(self):
        for rail, rj in self.r['requirement_ohm'].items():
            self.assertAlmostEqual(pp.stack_drop_mV(self.d, rj)[rail], 20.0, places=9)

    def test_face_term_moves_joint(self):
        d = copy.deepcopy(self.d)
        d['terms']['face_ohm']['value'] *= 2
        self.assertAlmostEqual(pp.joint_ohm(d, 18.8) - pp.joint_ohm(self.d, 18.8), 2 * self.d['terms']['face_ohm']['value'], places=12)

    def test_fault_shares_rise_as_posts_go(self):
        for row in pp.fault_shares(self.d).values():
            self.assertLess(row[3], row[2])
            self.assertLess(row[2], row[1])
            self.assertLess(row[1], row[0])
            self.assertLess(row[0], 1.6)

    def test_every_term_has_status_and_source(self):
        for k, t in self.d['terms'].items():
            self.assertIn(t['status'], ('SOURCED', 'DERIVED', 'ASSUMED'), k)
            self.assertTrue(t['source'], k)
            self.assertIn('unit', t, k)

    def test_joints(self):
        js = self.d['joints']
        self.assertEqual(len(js), 18)
        self.assertEqual(sum(j['net'] == 'AGND' for j in js), 9)
        for j in js:
            if j['front_board'] == 'P' and j['carried_by']:
                self.assertEqual(j['front_xy'], j['K_xy'])
            self.assertEqual(j['gap_mm'], 17.0 if j['front_board'] == 'P' else 19.0)
            self.assertEqual(j['post_code'], 'R30-1011702' if j['front_board'] == 'P' else 'R30-1011902')
        by = {j['id']: j for j in js}
        self.assertEqual(by['POWER-P-AGND2']['K_xy'], [98.5, 175.0])
        self.assertEqual(by["POWER-JR-AGND3"]["K_xy"], [278.5, 160])
        counts = self.d['terms']['header_agnd_positions']['value']
        self.assertEqual(sum(counts.values()), 274)  # 2026-11-27 refresh: MC04-S7 rev 13 adds JL-K-26/27 and JR-K-28..30


class Continuation(unittest.TestCase):
    def setUp(self):
        self.d = pp.load()

    def test_body_at_19mm(self):
        self.assertAlmostEqual(pp.body_ohm(self.d, 19.0) / pp.body_ohm(self.d, 18.8), 19.0 / 18.8, places=12)
        self.assertAlmostEqual(pp.joint_ohm(self.d, 19.0) * 1000, 0.4045, places=3)

    def test_working_limit_covers_normal_and_post_loss(self):
        lim = self.d['terms']['header_contact_working_limit_A']['value']
        self.assertEqual(lim, 1.0)
        for row in pp.fault_shares(self.d).values():
            self.assertLess(max(row.values()), lim)
        self.assertEqual(self.d['terms']['header_contact_limit_A']['value'], 1.6)

    def test_spreading_rises_but_stays_under_ceiling(self):
        old, new = pp.spreading(self.d, True), pp.spreading(self.d, False)
        for k in old:
            self.assertGreater(new[k]['parallel_ohm'], old[k]['parallel_ohm'])
            self.assertLess(new[k]['parallel_ohm'], self.d['terms']['return_plane_ohm']['value'])
        s = pp.p_share_with_spreading(self.d)
        self.assertLess(s['old'], s['new'])
        self.assertLess(s['new'], 1.0)

    def test_cover_worsens(self):
        rows, nprov = pp.p_pair_cover(self.d)
        self.assertEqual(nprov, 2)
        self.assertEqual(len(rows), 10)
        self.assertEqual(sum(r['old_mm'] > 40 for r in rows), 4)
        self.assertEqual(sum(r['new_mm'] > 40 for r in rows), 8)
        self.assertEqual(sum(r['new_mm'] > 50 for r in rows), 5)
        self.assertTrue(all(r['new_mm'] >= r['old_mm'] - 1e-9 for r in rows))


class AttemptA2(unittest.TestCase):
    def test_ds44_jr_lands_at_half_millimetre(self):
        d = pp.load()
        for j in d['joints']:
            if j['front_board'] == 'JR' and j['carried_by']:
                self.assertAlmostEqual(j['K_xy'][0] - j['present_front_xy'][0], 0.5, places=9)
                self.assertEqual(j['K_xy'], j['front_xy'])

    def test_decision_rows_pin(self):
        src = pp.load()['sources']['S-DEC']
        text = (pp.ROOT / src['path']).read_text().splitlines(True)
        rows = [next(line for line in text if line.startswith(f'| {r} |')) for r in src['rows']]
        self.assertEqual(hashlib.sha256(''.join(rows).encode()).hexdigest(), src['rows_sha256'])

    def test_repository_sources_are_current(self):
        """Every repository source is pinned by its file, its cited rows or its cited object, and the pin holds."""
        for sid, src in pp.load()['sources'].items():
            if not sid.startswith('S-'):
                continue
            with self.subTest(source=sid):
                data = (pp.ROOT / src['path']).read_bytes()
                if 'sha256' in src:
                    self.assertEqual(hashlib.sha256(data).hexdigest(), src['sha256'])
                elif 'locator_sha256' in src:
                    cited = json.loads(data)
                    for key in src['locator'].split('.'):
                        cited = cited[key]
                    canonical = json.dumps(cited, sort_keys=True, separators=(',', ':'))
                    self.assertEqual(hashlib.sha256(canonical.encode()).hexdigest(), src['locator_sha256'])
                else:
                    self.assertIn('rows_sha256', src)

class Readme(unittest.TestCase):
    def test_readme_tables_are_current(self):
        d = pp.load()
        env = json.loads(pp.ENVELOPES.read_text())
        current = pp.README.read_text()
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'README.md'
            p.write_text(current)
            pp.write_readme(d, env, p)
            self.assertEqual(p.read_text(), current, 'run power_posts.py --write-readme')

    def test_locked_hardware_is_never_proposed_to_move(self):
        lock = json.loads((pp.ROOT / 'design/grid/placements.lock.json').read_text())['placements']
        locked = {r['ref'] for r in lock}
        env = json.loads(pp.ENVELOPES.read_text())
        text = pp.README.read_text()
        hits = {m['ref'] for b in env['boards'].values() for m in b['hits']} & locked
        # At the DS-44 positions the jack courtyards enter only the K-facing keep-out (through-hole, both faces); see README.
        self.assertEqual(hits, {'J1410', 'J1510', 'J1610', 'J1710'})
        for ref in sorted(hits):
            self.assertIn(ref, text)
        self.assertIn('NEEDS_DESIGN', text)
        self.assertIn('No jack or LED moves', text)


if __name__ == '__main__':
    unittest.main()
