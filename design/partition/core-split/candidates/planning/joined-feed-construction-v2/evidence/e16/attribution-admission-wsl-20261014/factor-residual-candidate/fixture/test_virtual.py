"""Virtual whole-operator access equivalence; no original data."""
import test_coercivity as C
from test_coercivity import W,T,P,np,csr,CONTEXT
import unittest
import json
from pathlib import Path

RESULTS={}


def view_case(kwargs):
    blocks,d,exact=T.separated_fixture(**kwargs)
    meter=P.Meter();view=P.JoinedRows([(a,b,tuple(range(2))) for a,b in blocks],d,meter)
    return blocks,d,exact,meter,view


class VirtualTests(unittest.TestCase):
    def test_exact_rows_reverse_and_coupled(self):
        for name,kwargs in [('strong',{}),('weak',{'ground':2.**-30}),('nonsymmetric',{'nonsymmetric':True})]:
            blocks,d,exact,meter,view=view_case(kwargs)
            reference=C.joined_stored(blocks,np.array(view.midpoint))
            for i in range(reference.shape[0]):
                row=dict(view.row(i))
                self.assertEqual(list(row),sorted(row))
                for j in range(reference.shape[1]):
                    self.assertEqual(T.F(row.get(j,0.)),T.F(float(reference[i,j])))
                    self.assertEqual(T.F(view.lookup(i,j)),T.F(float(reference[i,j])))
            access_before=dict(view.access)
            result=W.measured(lambda:P.coercivity_interval_certificate(view,view.interval_entries(),CONTEXT,meter),meter)
            self.assertEqual(result['status'],'CERTIFIED')
            result.update(W.physical_result(result,blocks,exact))
            result['view_access']=dict(view.access)
            result['view_access_baseline']=access_before
            result['view_access_certificate_delta']={k:v-access_before[k] for k,v in view.access.items()}
            result['integer_units']=meter.integer_operations
            result['integer_bit_work_envelope']=meter.integer_bit_work_envelope
            result['input_array_bytes']=sum(a.indptr.nbytes+a.indices.nbytes+a.data.nbytes+b.nbytes for a,b in blocks)
            result['input_scope']='nonowning existing board CSR and dense B; no joined CSR or transpose in certificate'
            RESULTS[name]=result
            self.assertGreater(result['view_access']['B_entries'],0)

    def test_packed_path_only_equivalence(self):
        import array
        for side in [4,8,9]:
            a=T.grid(side);m=P.Meter();packet,h=P.produce_coercivity_tree(a,CONTEXT,m,packed=True)
            self.assertIsInstance(packet['parent'],array.array)
            result=P.verify_coercivity_tree(a,CONTEXT,packet,h,m,path_only=True)
            self.assertGreaterEqual(result['inverse_infinity_upper'],side*side*(1+2*(side-1)))
            self.assertLess(result['inverse_infinity_upper'],side*side*(1+2*(side-1))*1.000001)
            self.assertNotIn('coercivity_subtree',m.phases)
            self.assertNotIn('coercivity_trace',m.phases)
            result['tree_buffer_payload_bytes']=25*a.shape[0]
            RESULTS[f'packed_path_grid_{side}']=result
            old=packet['edge'][1];packet['edge'][1]=old+.01
            with self.assertRaises(ValueError):P.verify_coercivity_tree(a,CONTEXT,packet,h,P.Meter(),path_only=True)
        for name,kwargs in [('strong',{}),('weak',{'ground':2.**-30})]:
            blocks,d,exact,meter,view=view_case(kwargs)
            access_before=dict(view.access)
            result=W.measured(lambda:P.coercivity_interval_certificate(view,view.interval_entries(),CONTEXT,meter,
                               bound_mode='path-only',packed=True),meter)
            self.assertEqual(result['status'],'CERTIFIED')
            result.update(W.physical_result(result,blocks,exact))
            result['view_access']=dict(view.access)
            result['view_access_baseline']=access_before
            result['view_access_certificate_delta']={k:v-access_before[k] for k,v in view.access.items()}
            result['integer_units']=meter.integer_operations
            result['integer_bit_work_envelope']=meter.integer_bit_work_envelope
            RESULTS[name+'_packed_path']=result

    def test_mutation_and_one_sided_refusal(self):
        blocks,d,exact,meter,view=view_case({})
        packet,h=P.produce_coercivity_tree(view,CONTEXT,meter)
        old=float(blocks[0][1][0,0]);blocks[0][1][0,0]=old+.01
        with self.assertRaises(ValueError):P.verify_coercivity_tree(view,CONTEXT,packet,h,meter)
        blocks[0][1][0,0]=old
        view.offsets[1]+=1
        with self.assertRaises(ValueError):view.validate()
        _,_,_,m,invalid=view_case({})
        invalid.intervals[0].pop()
        with self.assertRaises(ValueError):invalid.interval_entries()
        _,_,_,m,v=view_case({})
        v.blocks[0][0][0,1]=0.;v.blocks[0][0].eliminate_zeros()
        with self.assertRaises(ValueError):P.produce_coercivity_tree(v,CONTEXT,m)

    def test_sparse_terminal_mapping_and_shared_terminal(self):
        a=csr([[3.,-1.],[-1.,3.]])
        blocks=[(a,np.array([[-.25],[0.]]),(1,)),(a.copy(),np.array([[-.5],[0.]]),(1,))]
        d=[[(1.,1.),(-.1,-.1)],[(-.1,-.1),(2.,2.)]]
        m=P.Meter();view=P.JoinedRows(blocks,d,m)
        self.assertEqual(dict(view.row(0)),{0:3.,1:-1.,5:-.25})
        self.assertEqual(dict(view.row(5)),{0:-.25,2:-.5,4:-.1,5:2.})
        r=P.coercivity_interval_certificate(view,view.interval_entries(),CONTEXT,m)
        self.assertEqual(r['status'],'CERTIFIED')
        self.assertFalse(hasattr(view,'indptr'))
        self.assertFalse(hasattr(view,'transpose'))

if __name__=='__main__':
    import sys
    result=unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(VirtualTests))
    if len(sys.argv)>1:Path(sys.argv[1]).write_text(json.dumps(RESULTS,indent=2,sort_keys=True)+'\n')
    raise SystemExit(not result.wasSuccessful())
