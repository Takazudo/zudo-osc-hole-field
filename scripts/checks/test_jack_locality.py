import copy
import random
import unittest

from scripts.checks.jack_locality import improve_by_swaps


def row(ref,x,y,rotation=0,side='B.Cu'):
    return {'ref':ref,'board':'JL','fixed':False,'x_mm':x,'y_mm':y,'rotation_deg':rotation,'side':side,'courtyard_mm':[x-1,y-1,x+1,y+1]}


class SwapPassTests(unittest.TestCase):
    def test_swap_brings_each_resistor_to_its_own_jack(self):
        # R1 serves the jack at x=0 and R2 the jack at x=100, but legalization left them crossed.
        rows=[row('R1',100,0),row('R2',0,0,rotation=90,side='F.Cu')]
        pin_nets={'R1':{'1':'A','2':'AGND'},'R2':{'1':'B','2':'AGND'}}
        anchors={'A':[(0.0,0.0)],'B':[(100.0,0.0)]}
        out={r['ref']:r for r in improve_by_swaps(rows,{'R1':'R_0603','R2':'R_0603'},pin_nets,anchors)}
        self.assertEqual((out['R1']['x_mm'],out['R1']['rotation_deg'],out['R1']['side']),(0,90,'F.Cu'))
        self.assertEqual(out['R2']['courtyard_mm'],[99,-1,101,1])

    def test_different_footprints_never_swap(self):
        rows=[row('R1',100,0),row('C1',0,0)]
        pin_nets={'R1':{'1':'A'},'C1':{'1':'B'}}
        anchors={'A':[(0.0,0.0)],'B':[(100.0,0.0)]}
        out={r['ref']:r for r in improve_by_swaps(rows,{'R1':'R_0603','C1':'C_0603'},pin_nets,anchors)}
        self.assertEqual(out['R1']['x_mm'],100)

    def test_swap_pass_ignores_input_order(self):
        # regen-all --check needs byte-stable output, whatever order rows and dicts arrive in.
        rng=random.Random(7)
        rows=[row(f'R{i}',rng.uniform(0,150),rng.uniform(0,150),rotation=rng.choice((0,90)),side=rng.choice(('B.Cu','F.Cu'))) for i in range(40)]
        pin_nets={f'R{i}':{'1':f'N{i}','2':f'N{(i*7)%40}'} for i in range(40)}
        anchors={f'N{i}':[(rng.uniform(0,150),rng.uniform(0,150))] for i in range(0,40,3)}
        footprint={f'R{i}':('R_0603' if i%3 else 'R_0805') for i in range(40)}
        first=improve_by_swaps(copy.deepcopy(rows),footprint,pin_nets,anchors)
        shuffled=copy.deepcopy(rows);rng.shuffle(shuffled)
        keys=list(footprint);rng.shuffle(keys)
        second=improve_by_swaps(shuffled,{k:footprint[k] for k in keys},pin_nets,anchors)
        self.assertEqual(sorted(first,key=lambda r:r['ref']),sorted(second,key=lambda r:r['ref']))


if __name__=='__main__':
    unittest.main()
