import ast
import copy
import json
import math
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

import study as s


def fixtures():
    links=[{'id':str(i),'cable':'C29534' if i<28 else 'fixed','cable_length_mm':50.0,
            'positions':[{'kind':'ground'}], 'geometry':{'fixed':i}} for i in range(61)]
    manifest={'overrides':[str(i) for i in range(28)],'intentional_nulls':sorted(str(i) for i in range(56,61))}
    return links,manifest


class Kernel:
    def __init__(self):
        self.le=SimpleNamespace(rnd=lambda x:x)
        self.pair_calls=[];self.ground_calls=[]
    def link_pairs(self,inp,link,base):
        self.pair_calls.append((link['id'],link['cable_length_mm']))
        return ([] if int(link['id'])>=56 else [{'ratio':link['cable_length_mm']/100,'witness':link['id']}]),[]
    def ground_share(self,inp,links):
        self.ground_calls.append(copy.deepcopy(links))
        conductance=sum(1/r['cable_length_mm'] for r in links)
        return {'alternative_conductance':conductance,'lengths':[r['cable_length_mm'] for r in links]}


def expected(kernel,links):
    return {'links':[s.pair_summary(kernel,{},r,{}) for r in links],'ground_share':kernel.ground_share({},links)}


class SensitivityTests(unittest.TestCase):
    def test_exact_overrides_without_record_mutation(self):
        links,m=fixtures();before=copy.deepcopy(links)
        changed=s.override_lengths(links,m['overrides'])
        self.assertEqual(links,before)
        self.assertEqual(sum(r['cable_length_mm']==51 for r in changed),28)
        for a,b in zip(links,changed):
            b=dict(b);b['cable_length_mm']=a['cable_length_mm'];self.assertEqual(a,b)

    def test_wrong_missing_duplicate_or_extra_override(self):
        links,m=fixtures()
        for ids in (m['overrides'][:-1],m['overrides']+['28'],m['overrides'][:-1]+['28'],m['overrides'][:-1]+['0']):
            with self.assertRaises(ValueError):s.override_lengths(links,ids)

    def test_wrong_baseline_length(self):
        links,m=fixtures();links[0]['cable_length_mm']=49
        with self.assertRaises(ValueError):s.override_lengths(links,m['overrides'])

    def test_baseline_mismatch_prevents_any_variation(self):
        links,m=fixtures();kernel=Kernel();retained=expected(kernel,links)
        retained['links'][0]['ratio']=.7;kernel.pair_calls=[];kernel.ground_calls=[]
        with self.assertRaisesRegex(ValueError,'baseline reproduction'):
            s.experiment(kernel,{},links,{},retained,m)
        self.assertEqual(len(kernel.pair_calls),61)
        self.assertTrue(all(length==50 for ident,length in kernel.pair_calls))
        self.assertEqual(len(kernel.ground_calls),1)

    def test_pair_kernel_only28_new_lengths_ground_all61_recomputed(self):
        links,m=fixtures();kernel=Kernel();retained=expected(kernel,links)
        kernel.pair_calls=[];kernel.ground_calls=[]
        result=s.experiment(kernel,{},links,{},retained,m)
        self.assertEqual(len(kernel.pair_calls),61+28)
        self.assertEqual([len(rows) for rows in kernel.ground_calls],[61,61])
        self.assertEqual(sum(r['cable_length_mm']==51 for r in kernel.ground_calls[1]),28)
        self.assertNotEqual(result['baseline']['ground_share'],result['length_51_only']['ground_share'])
        self.assertEqual(result['numeric_ratio_count'],56)
        self.assertEqual(len(result['intentional_nulls']),5)

    def test_model_pin_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);(root/'model.py').write_text('changed')
            with self.assertRaisesRegex(ValueError,'model pin changed'):
                s.verify_pins(root,{'sha256':{'model.py':'0'*64}})

    def test_missing_null_cannot_be_hidden(self):
        links,m=fixtures();kernel=Kernel();retained=expected(kernel,links);m['intentional_nulls']=[]
        with self.assertRaisesRegex(ValueError,'intentional null'):
            s.experiment(kernel,{},links,{},retained,m)

    def test_retained_mixed_ground_kernel_responds_to_other_path(self):
        # Execute only these stdlib numerical functions from the pinned source,
        # with a two-contact synthetic fixture. No numpy/full model/native run.
        source=(s.ROOT/'scripts/stack/link_electrical/link_ratios.py').read_text()
        tree=ast.parse(source)
        names={'ground_paths_at','worst_contact_mixed_at'}
        nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
        pp=SimpleNamespace(joint_ohm=lambda d,g:1,branch_gap=lambda b,d:1,v=lambda d,k:d[k])
        ns={'math':math,'le':SimpleNamespace(pp=pp)}
        exec(compile(ast.Module(body=nodes,type_ignores=[]),'retained-ground-kernel','exec'),ns)
        inp={'ds62':{'pitch':'p'},'conductor_resistance_mohm':{'p':{'min':10,'max':20}},
             'contact':{'p':{'resistance_max_ohm':{'value':.1}},'resistance_min_ohm':{'value':.01}}}
        terms={'return_plane_ohm':.01,'single_return_A':1}
        base=ns['worst_contact_mixed_at'](inp,'P',[50,50],0,terms)
        mixed=ns['worst_contact_mixed_at'](inp,'P',[50,51],0,terms)
        # Unchanged 50mm candidate sees the other 51mm path's higher maximum.
        self.assertAlmostEqual(base,.23/(.03+.23))
        self.assertAlmostEqual(mixed,.2304/(.03+.2304))
        self.assertGreater(mixed,base)


if __name__=='__main__':unittest.main()
