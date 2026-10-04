import copy
import math
import unittest
from scripts.checks.core_locality import prove_core_locality_transition,spread_module_homes,without_core_locality


class CoreLocalityTests(unittest.TestCase):
    def test_spread_separates_crowded_homes_inside_bounds_and_out_of_holes(self):
        homes={'A':(50,50),'B':(51,50),'C':(50,51)};areas={'A':800,'B':800,'C':200}
        spread=spread_module_homes(homes,areas,(0,0,100,100),holes=[(60,0,100,40)],fill=.5)
        r={k:math.sqrt(areas[k]/(2*.5)/math.pi) for k in homes}
        for a in homes:
            x,y=spread[a];self.assertTrue(r[a]-1e-6<=x<=100-r[a]+1e-6 and r[a]-1e-6<=y<=100-r[a]+1e-6)
            self.assertFalse(60<x<100 and 0<y<40)
            for b in homes:
                # The weak pull toward the header home leaves at most a small residual overlap.
                if a<b:self.assertGreater(math.dist(spread[a],spread[b]),r[a]+r[b]-1.0)

    def test_transition_accepts_only_core_faces_and_stack(self):
        old={'boards':[{'id':'osc-core','board_key':'K','layers':4,'layer_reason':'four'},{'id':'osc-jack-left','board_key':'JL','layers':6,'layer_reason':'six'}],
             'assignment':{'components':[{'ref':'R1','board':'K','side':'B.Cu'},{'ref':'R2','board':'JL','side':'B.Cu'}]}}
        new=copy.deepcopy(old);new['boards'][0].update(layers=6,layer_reason='six');new['assignment']['components'][0]['side']='F.Cu'
        prove_core_locality_transition(old,new)
        self.assertEqual(without_core_locality(new,old),old)
        bad=copy.deepcopy(new);bad['assignment']['components'][1]['side']='F.Cu'
        with self.assertRaisesRegex(ValueError,'beyond the core locality'):prove_core_locality_transition(old,bad)


if __name__=='__main__':unittest.main()
