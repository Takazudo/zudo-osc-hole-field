import unittest

from scripts.pcbgen.dedupe_stacked_vias import plan


def via(uid,x,y,net='n',size=0.6,locked=False):
    return {'uuid':uid,'net':net,'xy':(x,y),'size':size,'drill':0.3,'layers':'"F.Cu" "B.Cu"','locked':locked}


class DedupeTests(unittest.TestCase):
    def test_stacked_same_net_vias_fold_onto_the_densest_one(self):
        removed=plan([via('a',0,0),via('b',0.2,0),via('c',0.4,0),via('d',1.0,0)])
        self.assertEqual(removed,{'a':'b','c':'b'})

    def test_other_nets_sizes_locks_and_far_vias_are_kept(self):
        self.assertEqual(plan([via('a',0,0),via('b',0.1,0,net='m'),via('c',0.1,0.1,size=0.7),via('d',0,0.1,locked=True),via('e',0.3,0)]),{})


if __name__=='__main__':
    unittest.main()
