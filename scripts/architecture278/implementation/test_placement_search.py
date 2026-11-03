import itertools
import unittest
from placement_search import matching

class MatchingTests(unittest.TestCase):
    def test_exhaustive_small_graphs_against_permutations(self):
        # Every bipartite adjacency graph with3nets/3pins, including Hall failures.
        for flags in itertools.product((0,1),repeat=9):
            costs=[[flags[n*3+p] for p in range(3)] for n in range(3)]
            possible=any(all(costs[n][perm[n]]==0 for n in range(3))
                         for perm in itertools.permutations(range(3)))
            result=matching(costs,0)
            self.assertEqual(possible,result is not None)
            if result is not None:
                self.assertEqual(3,len(set(result.values())))
                self.assertTrue(all(costs[n][p]==0 for n,p in result.items()))
    def test_more_pins_than_nets(self):
        result=matching([[2,1,4,0],[2,0,1,4]],0)
        self.assertEqual({0:3,1:1},result)
    def test_duplicate_preferred_pin_is_not_accepted(self):
        self.assertIsNone(matching([[0,4],[0,4]],0))
        self.assertIsNotNone(matching([[0,4],[0,4]],4))

if __name__=='__main__':unittest.main()
