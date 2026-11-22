"""MC04-S7 Revision 10: the link gate keeps the baseline link clusters (IDs and member pairs) and clusters only the
pairs no baseline link holds, deterministically (no KiCad, no network)."""
import json
import random
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import links_gate as lg  # noqa: E402
import link_cluster_baseline as lcb  # noqa: E402

TOP = re.compile(r'^(.*-L\d+)(\..*)?$')


def site(i, x, y, n=2):
    return {'id': 'S-%d' % i, 'xy': [float(x), float(y)], 'classes': ['ANALOGUE'] * n}


def base(*clusters):
    return [{'id': 'X-L%02d' % k, 'joint': 'J', 'front_board': 'F', 'members': ['S-%d' % i for i in ms]}
            for k, ms in clusters]


def run(sites, b, n=40, jr=35.0):
    return [(c['id'], c['members']) for c in lg.stable_clusters(sites, b, n, jr, 'X-L')]


class StableClusters(unittest.TestCase):
    def test_baseline_clusters_keep_their_ids_and_remaining_members(self):
        b = base((1, (1, 2, 3)), (2, (4, 5)), (3, (6,)))
        sites = [site(1, 0, 0), site(3, 4, 0), site(4, 100, 0), site(5, 104, 0)]  # S-2 and S-6 are gone
        self.assertEqual(run(sites, b), [('X-L01', ['S-1', 'S-3']), ('X-L02', ['S-4', 'S-5'])])

    def test_a_new_pair_joins_the_nearest_kept_cluster_within_the_radius(self):
        b = base((1, (1, 2)), (2, (3, 4)))
        sites = [site(1, 0, 0), site(2, 4, 0), site(3, 60, 0), site(4, 64, 0), site(9, 20, 0)]
        self.assertEqual(run(sites, b), [('X-L01', ['S-1', 'S-2', 'S-9']), ('X-L02', ['S-3', 'S-4'])])

    def test_new_pairs_beyond_the_radius_take_the_next_unused_ids(self):
        b = base((1, (1,)), (2, (2,)), (3, (3,)))  # X-L03's pair is gone; its ID is never reused
        sites = [site(1, 0, 0), site(2, 50, 0), site(8, 200, 0), site(9, 400, 0)]
        self.assertEqual(run(sites, b), [('X-L01', ['S-1']), ('X-L02', ['S-2']), ('X-L04', ['S-8']),
                                         ('X-L05', ['S-9'])])

    def test_a_new_pair_does_not_join_a_cluster_whose_circuits_it_would_exceed(self):
        b = base((1, (1, 2)))
        sites = [site(1, 0, 0, 4), site(2, 2, 0, 4), site(9, 1, 0, 4)]
        n = lg.circuits_needed(['ANALOGUE'] * 8)
        self.assertEqual(run(sites, b, n=n), [('X-L01', ['S-1', 'S-2']), ('X-L02', ['S-9'])])

    def test_two_runs_and_any_input_order_give_the_same_clusters(self):
        rng = random.Random(7)
        sites = [site(i, rng.uniform(0, 300), rng.uniform(0, 200), rng.randint(1, 4)) for i in range(1, 41)]
        b = base((1, (1, 2, 3)), (2, (10, 11)), (3, (20,)))
        first = run(sites, b)
        for _ in range(5):
            rng.shuffle(sites)
            self.assertEqual(run(sites, b), first)


class CommittedGate(unittest.TestCase):
    def test_baseline_record_is_the_source_commit(self):
        self.assertEqual(json.dumps(lcb.build(), indent=1) + '\n', lcb.OUT.read_text())

    def test_every_baseline_link_keeps_its_id_and_its_remaining_members(self):
        clusters = json.loads(lcb.OUT.read_text())['clusters']
        gate = json.loads(lg.LINK_GATE.read_text())
        by_top = {}
        for link in gate['links']:
            if link['joint'] == 'O-K':
                continue
            by_top.setdefault(TOP.match(link['id']).group(1), set()).update(link['members'])
        present = {m for ms in by_top.values() for m in ms}
        for c in clusters:
            kept = set(c['members']) & present
            if kept:
                self.assertIn(c['id'], by_top, c['id'])
                self.assertTrue(kept <= by_top[c['id']], c['id'])
                self.assertEqual(by_top[c['id']] & {m for d in clusters for m in d['members']}, kept, c['id'])

    def test_the_jl_l02_hold_names_its_baseline_cluster(self):
        clusters = {c['id']: c['members'] for c in json.loads(lcb.OUT.read_text())['clusters']}
        gate = json.loads(lg.LINK_GATE.read_text())
        hold = [x for x in gate['links'] if x['id'] == 'JL-K-JL-L02']
        self.assertEqual(len(hold), 1)
        self.assertEqual(sorted(hold[0]['members']), clusters['JL-K-JL-L02'])
        self.assertEqual(lg.hold_errors(json.loads(lg.GATE_OPTIONS.read_text()), gate['links']), [])


if __name__ == '__main__':
    unittest.main()
