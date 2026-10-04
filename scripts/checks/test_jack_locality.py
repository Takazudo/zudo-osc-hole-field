import copy
import random
import unittest

import hashlib
import json

from scripts.checks.jack_locality import improve_by_swaps,stable_sum


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


    def test_swap_pass_matches_its_golden_digest(self):
        # Pins the exact output across Python versions (regen-all --check runs on more than one).
        rng=random.Random(11)
        rows=[row(f'R{i}',round(rng.uniform(0,150),2),round(rng.uniform(0,150),2),rotation=rng.choice((0,90)),side=rng.choice(('B.Cu','F.Cu'))) for i in range(60)]
        pin_nets={f'R{i}':{'1':f'N{i%23}','2':f'N{(i*7)%23}'} for i in range(60)}
        anchors={f'N{i}':[(round(rng.uniform(0,150),2),round(rng.uniform(0,150),2))] for i in range(0,23,2)}
        out=improve_by_swaps(rows,{f'R{i}':('R_0603' if i%3 else 'R_0805') for i in range(60)},pin_nets,anchors)
        digest=hashlib.sha256(json.dumps(sorted(out,key=lambda r:r['ref']),sort_keys=True).encode()).hexdigest()
        self.assertEqual(digest,GOLDEN_SWAP_DIGEST)


    def test_swap_pass_never_uses_builtin_float_sum(self):
        # Builtin sum() rounds differently on Python 3.10/3.11 and 3.12+.
        import scripts.checks.jack_locality as module
        def forbidden(*args,**kwargs):raise AssertionError('builtin sum() in the swap pass')
        module.sum=forbidden
        try:
            rows=[row('R1',100,0),row('R2',0,0)]
            improve_by_swaps(rows,{'R1':'R_0603','R2':'R_0603'},{'R1':{'1':'A'},'R2':{'1':'B'}},{'A':[(0.0,0.0)],'B':[(100.0,0.0)]})
        finally:del module.sum


class StableSumTests(unittest.TestCase):
    def test_compensated_on_every_python_version(self):
        # Naive left-to-right addition (Python 3.10/3.11 sum) loses the 1.0 entirely.
        self.assertEqual(stable_sum([1e16,1.0,-1e16]),1.0)
        self.assertEqual(stable_sum([0.1]*10),1.0)


GOLDEN_SWAP_DIGEST='308fd6691cbb638b1deca5f83fbaa8130b5a159e50a0429ec1fda881886035f7'

if __name__=='__main__':
    unittest.main()
