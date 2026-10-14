"""Independent analytic accounting fixtures; no production artifact loads/solves."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import numpy as np
import scipy.sparse as sp

import resistance_attribution as R


def branch(n, a, b, ohm, identity, kind='barrel', weights=None):
    nodes = [a, b] if weights is None else a
    weights = [1., -1.] if weights is None else weights
    return {'id': identity, 'kind': kind, 'board': 'KA', 'net': '+12V',
            'object_ids': [identity], 'layer_interval': ['F.Cu', 'In4.Cu'],
            'region': {'length_mm': 1.},
            'branch': {'nodes': nodes, 'weights': weights, 'resistance_ohm': ohm},
            'matrix': R.matrix_record(R.rank_one(n, nodes, weights, ohm))}


def packet(components, voltage, injection, held=(0,), observation=(2,), weights=(1.,), current=1.):
    n = len(voltage)
    matrix = sum((R.matrix_read(c['matrix']) for c in components), sp.csr_matrix((n,n)))
    energies = {}
    for c in components:
        energies[c['kind']] = energies.get(c['kind'], 0.) + float(np.dot(voltage, R.matrix_read(c['matrix']) @ voltage))
    return {'schema': 'e16-attribution-detail-v1',
            'identity': {'board': 'KA', 'net': '+12V', 'ref': 'Utest', 'pin': '1',
                         'pad_uuid': 'synthetic-pad', 'process_case': 'nominal-average',
                         'depth_case': 'uniform-dielectric', 'return_state': 'all-present',
                         'observation_support': {'nodes': list(observation), 'weights': list(weights)},
                         'source_support': {'mode': 'equipotential_patches', 'potential_V': 0,
                                            'pads': [{'ref': f'TP{i}', 'pin': '1', 'pad_uuid': f'source-{i}',
                                                      'board': 'KA', 'nodes': [i]} for i in held]}},
            'network': {'matrix': R.matrix_record(matrix)}, 'components': components,
            'solution': {'potential_V': list(voltage), 'injection_A': list(injection),
                         'original_node_current_A': list(map(float, matrix @ voltage)),
                         'original_energy_W': float(np.dot(voltage, injection)), 'original_class_energy_W': energies,
                         'normalization': {'mode': 'unit_current', 'current_A': current}},
            'scope': {'complete_modeled_network': True, 'omitted_components': [],
                      'physical_omissions': ['synthetic fixture, no instrument qualification'],
                      'expected_component_ids': [c['id'] for c in components]},
            'provenance': {'source_sha256': hashlib.sha256(b'synthetic source').hexdigest(),
                           'operator_sha256': R.digest(R.matrix_record(matrix)),
                           'extractor_sha256': hashlib.sha256(Path(R.__file__).read_bytes()).hexdigest(),
                           'config_sha256': hashlib.sha256(R.CONFIG.read_bytes()).hexdigest(),
                           'quantity_origin': 'synthetic'}}


def series(current=1.):
    return packet([branch(3,0,1,.002,'via'),branch(3,1,2,.003,'sheet')],
                  [0.,.002*current,.005*current],[0.,0.,current],current=current)


class Attribution(unittest.TestCase):
    def result(self, p):
        return R.attribute(p, R.bindings(p))

    def passed(self, p):
        r = self.result(p)
        self.assertEqual(r['failures'], [])
        self.assertFalse(r['whole_board_acceptance'])
        self.assertFalse(r['electrical_acceptance'])
        self.assertFalse(r['adopted'])
        return r

    def blocked(self, p, message=None):
        r = self.result(p)
        self.assertEqual(r['status'], 'BLOCKED')
        self.assertFalse(r['whole_board_acceptance'])
        self.assertTrue(r['failures'])
        if message:
            self.assertIn(message, r['failures'][0])

    def test_api_sparse_order_is_not_limited_by_tiny_json_cli(self):
        matrix=R.matrix_read({'n':100001,'row':[0,1],'col':[0,1],'siemens':[1.,1.]})
        self.assertEqual(matrix.shape,(100001,100001))
        self.assertEqual(matrix.nnz,2)

    def test_cli_rejects_large_network_or_component_before_allocation(self):
        for field in ('network','component'):
            p=series()
            if field=='network':p['network']['matrix']['n']=3000000
            else:p['components'][0]['matrix']['n']=3000000
            with tempfile.TemporaryDirectory() as directory:
                base=Path(directory);detail=base/'detail.json';expected=base/'expected.json'
                detail.write_text(json.dumps(p));expected.write_text(json.dumps(R.bindings(p)))
                with patch('sys.argv',['report','--detail',str(detail),'--expected',str(expected),
                                       '--output',str(base/'out.json')]),patch.object(R,'matrix_read') as reader:
                    with self.assertRaisesRegex(ValueError,'CLI limited'):
                        R.main()
                    reader.assert_not_called()

    def test_known_series(self):
        r = self.passed(series())
        self.assertAlmostEqual(r['effective_resistance_ohm'], .005)
        self.assertEqual([c['effective_resistance_mohm'] for c in r['components']], [2.,3.])

    def test_known_parallel(self):
        p = packet([branch(2,0,1,.002,'a'),branch(2,0,1,.003,'b')],
                   [0.,.0012],[0.,1.],observation=(1,))
        r = self.passed(p)
        self.assertAlmostEqual(r['effective_resistance_ohm'], .0012)
        self.assertAlmostEqual(r['components'][0]['joule_energy_W'], .00072)
        self.assertAlmostEqual(r['components'][1]['joule_energy_W'], .00048)

    def test_shared_transfer_two_source_supports(self):
        # Two 2 mOhm feeds in parallel, then one shared 3 mOhm interval.
        p = packet([branch(4,0,2,.002,'s0'),branch(4,1,2,.002,'s1'),branch(4,2,3,.003,'shared')],
                   [0.,0.,.001,.004],[0.,0.,0.,1.],held=(0,1),observation=(3,))
        r = self.passed(p)
        self.assertAlmostEqual(r['effective_resistance_ohm'],.004)
        self.assertEqual([s['current_A'] for s in r['source_currents_A']],[-.5,-.5])
        self.assertAlmostEqual(r['components'][2]['effective_resistance_mohm'],3.)

    def test_distributed_termination_rank_one_once(self):
        # Potentials on two support nodes differ: NOT two independent resistors.
        c = branch(4,[1,2,3],None,.002,'term','termination',[.25,.75,-1.])
        cs = [branch(4,0,1,.001,'a'),branch(4,0,2,.003,'b'),c]
        # Current flows from terminal through .25/.75 distributed support.
        p = packet(cs,[0.,.00025,.00225,.00375],[0.,0.,0.,1.],observation=(3,))
        r = self.passed(p)
        self.assertAlmostEqual(r['components'][-1]['joule_energy_W'],.002)
        self.assertAlmostEqual(r['effective_resistance_ohm'],.00375)

    def test_wire_and_terminations_once(self):
        cs=[branch(5,i,i+1,r,k,kind) for i,(r,k,kind) in enumerate([
            (.001,'copper','barrel'),(.002,'KA-term','termination'),
            (.003,'bulk','wire_bulk'),(.004,'KB-term','termination')])]
        p=packet(cs,[0.,.001,.003,.006,.01],[0.,0.,0.,0.,1.],observation=(4,))
        self.assertAlmostEqual(self.passed(p)['effective_resistance_ohm'],.01)

    def test_normalization_and_milliohm_conversion(self):
        for i in (.001,2.,-3.):
            r=self.passed(series(i))
            self.assertAlmostEqual(r['effective_resistance_ohm'],.005)
            self.assertAlmostEqual(r['components'][0]['effective_resistance_mohm'],2.)

    def test_loaded_energy_never_becomes_resistance(self):
        p=series(.002)
        p['solution']['normalization']={'mode':'simultaneous_load','current_A':None}
        r=self.passed(p)
        self.assertIsNone(r['effective_resistance_ohm'])
        self.assertTrue(all(c['effective_resistance_ohm'] is None for c in r['components']))
        p['solution']['normalization']['current_A']=.002
        self.blocked(p,'cannot be normalized')

    def test_stale_hashes(self):
        for key in ('identity','network','components','solution','scope','provenance'):
            p=series(); expected=R.bindings(p); expected[key]='a'*64
            self.assertIn('hashes',R.attribute(p,expected)['failures'][0])

    def test_missing_identities(self):
        for key in ('board','net','ref','pin','pad_uuid','process_case','return_state'):
            p=series(); p['identity'][key]=''; self.blocked(p,'identity')
        p=series();p['components'][0]['object_ids']=[];self.blocked(p,'physical identities')

    def test_nonfinite_data(self):
        for value in ('nan','inf','-inf'):
            p=series();p['solution']['potential_V'][1]=value;self.blocked(p,'nonfinite')
        p=series();p['solution']['original_energy_W']='nan';self.blocked(p,'nonfinite')

    def test_incomplete_or_local_cannot_accept(self):
        for key,value in [('complete_modeled_network',False),('omitted_components',['unmapped'])]:
            p=series();p['scope'][key]=value;self.blocked(p,'incomplete')
        r=self.passed(series());self.assertFalse(r['whole_board_acceptance'])

    def test_duplicate_and_missing_interface(self):
        p=series();p['components'].append(copy.deepcopy(p['components'][0]));self.blocked(p,'duplicate')
        p=series();p['components'].pop();self.blocked(p,'ownership')

    def test_operator_mismatch_even_same_solution_energy(self):
        p=packet([branch(3,0,1,.001,'a'),branch(3,0,2,.001,'b')],
                 [0.,.001,.001],[0.,.5,.5],observation=(1,2),weights=(.5,.5))
        # Above potentials deliberately corrected to .0005 for half-current supports.
        p['solution']['potential_V']=[0.,.0005,.0005]
        p['solution']['original_node_current_A']=[-1.,.5,.5]
        p['solution']['original_energy_W']=.0005
        p['solution']['original_class_energy_W']={'barrel':.0005}
        extra=branch(3,1,2,.001,'hidden')  # zero energy for equal potentials
        p['components'].append(extra);p['scope']['expected_component_ids'].append('hidden')
        self.blocked(p,'operator_partition')

    def test_bad_current_energy_and_solution(self):
        for field in ('original_node_current_A','potential_V'):
            p=series();p['solution'][field][-1]+=1;self.blocked(p,'reconciliation')
        p=series();p['solution']['original_energy_W']*=2;self.blocked(p,'energy_original')
        p=series();del p['solution']['potential_V'];self.blocked(p)

    def test_wrong_unit_rhs_and_support(self):
        p=series();p['identity']['observation_support']['weights']=[.9];self.blocked(p,'normalization')
        p=series();p['solution']['injection_A']=[0.,.5,.5];self.blocked(p,'RHS')
        p=series();p['identity']['observation_support']['nodes']=[0];self.blocked(p,'held source')

    def test_all_three_open_is_unconditionally_floating(self):
        p=series();p['identity'].update(net='AGND',return_state='all-three-open')
        p['solution']['injection_A']=[0.,0.,0.]
        self.blocked(p,'STRUCTURALLY_FLOATING')

    def test_unreported_island_rejected(self):
        p=packet([branch(3,0,1,.001,'a')],[0.,.001,0.],[0.,1.,0.],observation=(1,))
        self.blocked(p,'floating')

    def test_unsupported_mapping(self):
        p=series();p['components'][0]['kind']='invented-series-path';self.blocked(p,'unsupported')

    def test_config_hash_and_normalization_fail_closed(self):
        p=series();p['provenance']['config_sha256']='a'*64;self.blocked(p,'configuration')
        p=series();p['solution']['normalization']['current_A']=0;self.blocked(p,'normalization')

    def test_json_roundtrip_and_decimal_precision(self):
        p=series();p['solution']['potential_V']=['0','0.002','0.005']
        r=self.passed(json.loads(json.dumps(p)))
        self.assertEqual(json.loads(json.dumps(r,allow_nan=False)),r)
        self.assertIn('Utest.1',R.summary(r))

    def test_aggregation_does_not_duplicate_shared_members(self):
        p=packet([branch(2,0,1,.002,'tile1'),branch(2,0,1,.002,'tile2')],
                 [0.,.001],[0.,1.],observation=(1,))
        for c in p['components']:
            c.update(kind='sheet_union',object_ids=['pad-frag','track-frag'],layer_interval=['F.Cu'])
            c.pop('branch')
            c['region']={'tile':c['id']}
        p['solution']['original_class_energy_W']={'sheet_union':.001}
        r=self.passed(p)
        self.assertEqual(len(r['physical_aggregates']),1)
        self.assertAlmostEqual(r['physical_aggregates'][0]['joule_energy_W'],.001)

    def test_source_identity_cannot_be_relabelled_onto_free_nodes(self):
        p=series();p['identity']['pad_uuid']='source-0'
        self.blocked(p,'held source pad')

    def test_underflow_overflow_current_normalization(self):
        for current in (1e-200, 1e200):
            p=series();p['solution']['normalization']['current_A']=current
            self.blocked(p,'normalization scale')

    def test_singular_distributed_stamp_is_not_saved_by_connectivity(self):
        p=packet([branch(3,[0,1,2],None,.001,'term','termination',[-1.,.5,.5])],
                 [0.,.001,.001],[0.,.5,.5],observation=(1,2),weights=(.5,.5))
        self.blocked(p,'singular')

    def test_duplicate_source_nodes_rejected(self):
        p=series();p['identity']['source_support']['pads'][0]['nodes']=[0,0]
        self.blocked(p,'duplicate held nodes')

    def test_large_operator_needs_exact_external_uniqueness_receipt(self):
        n=258
        cs=[branch(n,0,i,1.,f'v{i}') for i in range(1,n)]
        p=packet(cs,[0.]+[1.]*(n-1),[0.]+[1.]*(n-1),observation=(1,))
        p['solution']['normalization']={'mode':'simultaneous_load','current_A':None}
        self.blocked(p,'UNIQUENESS_NOT_VERIFIED')
        p['provenance']['uniqueness_receipt_sha256']='a'*64
        proof={'network_sha256':R.digest(p['network']),'held_nodes_sha256':R.digest([0]),
               'return_state':'all-present','status':'POSITIVE_DEFINITE_FREE_OPERATOR',
               'receipt_sha256':'a'*64,'method':'synthetic identity free-block independent check'}
        p['solution']['uniqueness_evidence']=proof
        self.assertEqual(self.passed(p)['uniqueness'],'EXTERNAL_RECEIPT_BOUND_NOT_RECOMPUTED')
        for key in ('network_sha256','held_nodes_sha256','return_state','receipt_sha256'):
            bad=copy.deepcopy(p);bad['solution']['uniqueness_evidence'][key]='bad'
            self.blocked(bad,'UNIQUENESS_NOT_VERIFIED')
        for digest in ('0'*64,'g'*64):
            bad=copy.deepcopy(p);bad['provenance']['uniqueness_receipt_sha256']=digest
            bad['solution']['uniqueness_evidence']['receipt_sha256']=digest
            self.blocked(bad,'UNIQUENESS_NOT_VERIFIED')

    def test_original_class_energy_is_independently_reconciled(self):
        p=series();p['solution']['original_class_energy_W']['barrel']*=2
        self.blocked(p,'energy_classes')

    def test_interface_extractor_matches_existing_stamp_convention(self):
        cfg=json.loads(R.CONFIG.read_text())
        operators={b:{'N':2,'terminals':[f'CS247-{b}-W1'],
                      'supports':{f'CS247-{b}-W1':(np.array([0,1]),np.array([.25,.75]))}}
                   for b in ('KA','KB')}
        cs,offsets=R.interface_components(operators,cfg,'+12V')
        self.assertEqual(offsets,{'KA':0,'KB':3})
        self.assertEqual([c['kind'] for c in cs],['termination','termination','wire_bulk'])
        v=np.array([.001,.003,.005,.002,.004,.006])
        observed=sum(float(v@(R.matrix_read(c['matrix'])@v)) for c in cs)
        expected=((.25*.001+.75*.003-.005)**2+(.25*.002+.75*.004-.006)**2)/cfg['wires']['termination_per_end_ohm']+(.005-.006)**2/cfg['wires']['bulk_ohm']
        self.assertAlmostEqual(observed,expected)
        removed,_=R.interface_components(operators,cfg,'+12V',(1,))
        self.assertEqual(len(removed),2)

    def test_renamed_duplicate_physical_interval_rejected(self):
        p=series();p['components'][1]['object_ids']=p['components'][0]['object_ids']
        self.blocked(p,'duplicate physical')

    def test_retained_packet_must_preserve_configured_supports(self):
        p=series();p['provenance']['quantity_origin']='retained_solution'
        p['identity']['source_support']['board']='KA'
        self.blocked(p,'source identities')

    def test_tiled_union_partition_in_real_assembly(self):
        import shapely
        from shapely.geometry import box
        desc={'groups':[{'group':0,'layer':'F.Cu','fragments':['overlap-pad','overlap-track'],
                         'wkb':shapely.to_wkb(box(0,0,3,1),hex=True)}],
              'supports':{},'barrels':{},'terminals':[]}
        items=[R.adapter.mesh_item(desc,g,t,.5,.5) for g,t in R.adapter.tiles(desc,.5,1.)]
        asm=R.adapter.Assembly(desc,items)
        case={'rho_ohm_mm':2e-5,'outer_copper_mm':.07,'inner_copper_mm':.07,'barrel_plating_mm':.018}
        depth={'foil_mm':.07,'dielectric_mm':[.236]*5,'board_mm':1.6}
        cs=R.copper_components(asm,items,case,depth,'KA','+12V')
        self.assertEqual(len(cs),3)
        actual=sum((R.matrix_read(c['matrix']) for c in cs),sp.csr_matrix((asm.N,asm.N)))
        K,_,_=asm.matrix(case,depth)
        self.assertLess(R._max((actual-K).data)/R._max(K.data),1e-12)

    def test_real_tiny_assembly_partition_and_ring_mapping(self):
        # Reuse actual mesh/Assembly machinery, not a new resistor solver.
        from test_finite_adapter import operator,pad,via,sheet,rect,CASE,UNIFORM
        objs=[pad('CS247-KA-W1','+12V',rect(-.5,-.5,.5,.5)),via('v1','+12V',0,0),
              pad('L','+12V',rect(1.5,-.5,2.5,.5)),via('v2','+12V',2,0)]
        _,desc,assembly=operator(objs,[sheet('plane',rect(-1,-1,3,1))],'+12V')
        items=[R.adapter.mesh_item(desc,g,t,1.,.25) for g,t in R.adapter.tiles(desc,1.,20.)]
        components=R.copper_components(assembly,items,CASE,UNIFORM,'KA','+12V')
        K,_,records=assembly.matrix(CASE,UNIFORM)
        actual=sum((R.matrix_read(c['matrix']) for c in components),sp.csr_matrix(K.shape))
        self.assertLess(R._max((actual-K).data)/R._max(K.data),1e-12)
        self.assertEqual(len([c for c in components if c['kind']=='barrel']),len(records))
        self.assertTrue(any(len(c['object_ids'])>1 for c in components))


if __name__=='__main__':
    unittest.main()
