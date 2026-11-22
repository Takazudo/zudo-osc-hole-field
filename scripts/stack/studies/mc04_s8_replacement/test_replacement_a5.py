"""MC04-S8 Part A5: the joint search is complete (synthetic cases checked against brute force) and its record is current."""
import itertools
import json
import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import replacement as rp  # noqa: E402
import replacement_a5 as a5  # noqa: E402


def overlap(a, b):
    return a[0] < b[1] and b[0] < a[1]


class Completeness(unittest.TestCase):
    """Blocks are intervals on a line; two blocks conflict when they overlap. solve() must find an assignment exactly
    when brute force over every combination finds one, and what it returns must be valid and accepted."""

    def brute(self, vs, doms, accept):
        for combo in itertools.product(*(doms[v] for v in vs)):
            a = dict(zip(vs, combo))
            if all(not overlap(a[x], a[y]) for x, y in itertools.combinations(vs, 2)) and accept(a):
                return a
        return None

    def test_random_cases_agree_with_brute_force(self):
        rng = random.Random(11)
        for case in range(300):
            n = rng.randint(2, 4)
            vs = ['b%d' % i for i in range(n)]
            doms = {}
            for v in vs:
                w = rng.randint(2, 5)
                doms[v] = [(x, x + w) for x in sorted(rng.sample(range(0, 14), rng.randint(1, 5)))]
            forbidden = rng.choice([None, vs[0]])
            accept = (lambda a, f=forbidden, doms=doms: f is None or a[f] != doms[f][0])
            got = a5.solve(vs, doms, lambda a, ca, b, cb: not overlap(ca, cb), accept)
            ref = self.brute(vs, doms, accept)
            self.assertEqual(got is None, ref is None, (case, doms))
            if got is not None:
                self.assertTrue(all(not overlap(got[x], got[y]) for x, y in itertools.combinations(vs, 2)))
                self.assertTrue(accept(got))
                self.assertTrue(all(got[v] in doms[v] for v in vs))

    def test_an_infeasible_case_is_proved(self):
        doms = {'a': [(0, 4)], 'b': [(2, 6), (3, 7)], 'c': [(1, 3)]}
        stats = {}
        self.assertIsNone(a5.solve(['a', 'b', 'c'], doms, lambda a, ca, b, cb: not overlap(ca, cb), stats=stats))
        self.assertGreaterEqual(stats['nodes'], 0)


class Record(unittest.TestCase):
    def test_record_states_the_model_and_is_current(self):
        doc = json.loads(a5.OUT.read_text())
        self.assertEqual(doc['model'], rp.MODEL)
        self.assertEqual(json.dumps(a5.build(), indent=1) + '\n', a5.OUT.read_text())

    def test_found_poses_respect_the_limits(self):
        doc = json.loads(a5.OUT.read_text())
        for r in doc['runs']:
            for ic, c in r.get('poses', {}).items():
                self.assertLessEqual(c['moved_mm'], rp.LIMIT_MM if ic in r['targets'] else r['limit_others_mm'])
            for m in r.get('passives_moved', []):
                self.assertLessEqual(m['moved_mm'], rp.LIMIT_MM)
        for t in doc['placed']:
            self.assertIn(t, a5.TARGETS)


if __name__ == '__main__':
    unittest.main()
