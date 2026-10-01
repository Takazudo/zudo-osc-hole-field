"""Exact capture order and physical reduced-trace reconstruction fixtures."""
from fractions import Fraction as F
from types import SimpleNamespace
import unittest
import numpy as np
from scipy.sparse import csc_matrix,csr_matrix
from scipy.sparse.linalg import splu
from shapely.geometry import box
from scripts.pcbgen.potential_pair_probe import RecordingFactor,reduced_port_indices,reconstruct_nodal_traces,potential_rhs,snapshot_capture_inputs,require_same_restriction
from scripts.pcbgen.potential_refinement import refine
from scripts.pcbgen.potential_trial_matrix import potential_matrix
from scripts.pcbgen.contact_constraints import restrict_wetted_terminals
from scripts.pcbgen.test_sheet_volume import assembly


class PotentialPairTests(unittest.TestCase):
    def test_initial_copy_and_sequential_refinement_increment(self):
        matrix=csc_matrix([[1.,-1.,0.],[-1.,2.,-1.],[0.,-1.,1.]])
        rhs=np.array([[-1.,-1.],[0.,1.],[1.,0.]])
        real=splu(matrix[1:,1:])
        class Perturbed:
            def __init__(self):self.calls=0
            def solve(self,r):
                result=real.solve(r);self.calls+=1
                if self.calls==1:result[0,0]+=1e-7
                return result
        proxy=RecordingFactor(Perturbed(),matrix,rhs)
        field,receipt=refine(matrix,rhs,proxy)
        self.assertGreater(receipt['corrections'],0)
        np.testing.assert_array_equal(field,proxy.field)
        result={'potential_refinement':[{'start':0,'stop':2,**receipt}],
                'field_maximum_by_profile_ohm':np.max(abs(field),axis=0).tolist()}
        proof=proxy.verify(result)
        self.assertEqual(len(proof['calls']),1+receipt['corrections'])
        self.assertEqual(field[0].tolist(),[0,0])
        with self.assertRaises(ValueError):proxy.solve(rhs[1:])

    def test_manifest_and_code_are_bound_before_work(self):
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from scripts.pcbgen.regional_probe import verify_hashes
        with TemporaryDirectory() as td:
            manifest=Path(td)/'manifest.json';code=Path(td)/'code.py'
            manifest.write_text('{"epoch":1}');code.write_text('old code')
            parsed,own=snapshot_capture_inputs(manifest,code)
            self.assertEqual(parsed,{'epoch':1})
            manifest.write_text('{"epoch":2}')
            with self.assertRaisesRegex(ValueError,'changed diagnostic input'):verify_hashes(own)
            manifest.write_text('{"epoch":1}');code.write_text('new code')
            with self.assertRaisesRegex(ValueError,'changed diagnostic input'):verify_hashes(own)

    def test_restriction_json_roundtrip_preserves_exact_semantics(self):
        import json
        from shapely.geometry import mapping
        actual={'terminals':[{'ref':'fixture','tied_barrels':[0,1],
                             'maximum_wetting_geojson':mapping(box(0,0,1,1))}],
                'original_dofs':100,'restricted_dofs':90,'allowance':.123}
        retained=json.loads(json.dumps(actual))
        self.assertNotEqual(actual,retained) # tuple/list containers differ
        require_same_restriction(actual,retained)
        retained['terminals'][0]['tied_barrels']=[0,2]
        with self.assertRaisesRegex(ValueError,'terminals'):require_same_restriction(actual,retained)
        retained=json.loads(json.dumps(actual));retained['allowance']+=1e-15
        with self.assertRaisesRegex(ValueError,'allowance'):require_same_restriction(actual,retained)

    def test_factor_operand_mutation_is_rejected(self):
        matrix=csc_matrix([[1.,-1.],[-1.,1.]])
        rhs=np.array([[-1.,-2.],[1.,2.]])
        proxy=RecordingFactor(splu(matrix[1:,1:]),matrix,rhs)
        with self.assertRaisesRegex(ValueError,'RHS differs'):proxy.solve(rhs[1:]+1)

    def test_original_ports_are_mapped_through_restricted_unit_rows(self):
        P=csr_matrix(([1.,1.,1.,1.],([0,1,2,3],[1,0,1,0])),shape=(4,2))
        v=SimpleNamespace(port_offsets=np.array([0,4]),vertex_maps=[{i:{i:1} for i in range(4)}],projections=[P])
        np.testing.assert_array_equal(reduced_port_indices(v),[1,0,1,0])
        P.data[0]=.5
        with self.assertRaisesRegex(ValueError,'unit reduced'):reduced_port_indices(v)

    def test_real_canonical_traces_before_and_after_restriction(self):
        source=box(.4,.4,.65,.65);sink=box(-.7,-.5,-.45,-.25)
        v=assembly([(0,0)],(-1,-1,1,1),source,sink,1)
        field=np.arange(v.potential_matrix.shape[0]*2,dtype=float).reshape(-1,2)*1e-7;field[0]=0
        ports=reduced_port_indices(v)
        nodes,errors,indices,proof=reconstruct_nodal_traces(v,field,ports)
        self.assertEqual(len(nodes),4)
        self.assertGreaterEqual(proof['maximum_projected_vs_canonical_trace_difference'],0)
        self.assertTrue(all(np.isfinite(x).all() for x in nodes+errors))
        restriction=restrict_wetted_terminals(v,[{'ref':'fixture','layer':3,'maximum_wetting':box(-.35,-.35,.35,.35)}])
        self.assertLess(restriction['restricted_dofs'],restriction['original_dofs'])
        ports=reduced_port_indices(v)
        self.assertEqual(len(set(ports.tolist())),1)
        profiles=[[(3,source,1.),(1,sink,-1.)],[(0,source,1.),(1,sink,-1.)]]
        rhs=potential_rhs(v,profiles);proxy=RecordingFactor(v.potential_factor,v.potential_matrix,rhs);v.potential_factor=proxy
        result=potential_matrix(v,profiles,batch_size=2);proxy.verify(result)
        nodes,errors,indices,_=reconstruct_nodal_traces(v,proxy.field,ports)
        for layer,mapping in enumerate(v.vertex_maps):
            for vertex in mapping:
                np.testing.assert_array_equal(nodes[layer][vertex],proxy.field[ports[0]])
                self.assertEqual(errors[layer][vertex].tolist(),[0,0])


if __name__=='__main__':unittest.main()
