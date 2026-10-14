"""Independent tiny reconstruction fixtures; never open retained production files."""
import copy
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
import tempfile
from unittest.mock import patch

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

import attribution_reconstruction as B
import resistance_attribution as R
import finite_solve as S
from test_finite_adapter import CASE, UNIFORM


def sheet_assembly(n, edges, supports, inside, board):
    K = sp.csr_matrix((n, n))
    for a, b, resistance in edges:
        K += R.rank_one(n, [a, b], [1., -1.], resistance)
    geometric = K / (CASE['outer_copper_mm']/CASE['rho_ohm_mm'])
    xy = np.column_stack((np.arange(n), np.zeros(n)))
    item = {'group': 0, 'tile': None, 'xy': xy, 'row': geometric.tocoo().row,
            'col': geometric.tocoo().col, 'val': geometric.data}
    asm = SimpleNamespace(N=n, group=np.zeros(n, dtype=int), xy=xy, vertex_node=np.arange(n),
                          desc={'groups': [{'group': 0, 'layer': 'F.Cu', 'fragments': ['pad', 'overlapping-track']}], 'barrels': {}},
                          rings={}, supports=supports, support_inside=inside,
                          Kg={'face': geometric, 'inner': sp.csr_matrix((n, n))})
    return asm, [item]


def operators_from(assemblies):
    return {b: {'N': a.N, 'Kg_face': a.Kg['face'], 'Kg_inner': a.Kg['inner'], 'rings': a.rings,
                'barrels': a.desc['barrels'], 'supports': a.supports, 'support_inside': a.support_inside,
                'terminals': [f'CS247-{b}-W1']} for b, a in assemblies.items()}


def reductions_from(ops, cfg):
    reductions = {}
    for b, op in ops.items():
        Af, coupling, D, free, _, _, terms, src, _, _ = S.board_parts(op, CASE, UNIFORM, cfg, b, '+12V')
        lu = spla.splu(Af, permc_spec='MMD_AT_PLUS_A', diag_pivot_thresh=0., options={'SymmetricMode': True})
        Y, residual = S.refined_interface_solve(lu, Af, coupling)
        assert residual <= 1e-9
        reductions[b] = {'N': op['N'], 'free': free, 'terms': terms, 'source_pads': src,
                         'board': b, 'net': '+12V', 'case': 'nominal-average', 'depth': 'uniform-dielectric',
                         'Y': Y, 'S': np.asarray(D-coupling.T @ Y, dtype=float),
                         # Deliberately unrelated loaded field must never become selected excitation.
                         'u0': np.full(len(free), 99.), 'g': np.full(len(terms), 123.)}
    return reductions


def fixture(unequal=False, parallel=False, shared=False):
    cfg = json.loads(R.CONFIG.read_text())
    cfg['wires']['termination_per_end_ohm'] = .002
    cfg['wires']['bulk_ohm'] = .003
    cfg['source_support'] = {'board': 'KA', 'mode': 'equipotential_patches',
                             'pads': {'+12V': [{'ref': 'TPfixture', 'pad_id': 'source'}]}}
    ka_support = {'source': (np.array([0, 1, 2]), np.full(3, 1/3)),
                  'CS247-KA-W1': (np.array([3]), np.array([1.]))}
    edges = [(j, 3, .003) for j in range(3)]
    ka_n = 4
    if parallel:
        edges += [(j, 3, .003) for j in range(3)]
    if unequal:
        ka_n = 5
        edges += [(j, 4, .009) for j in range(3)]
        ka_support['CS247-KA-W1'] = (np.array([3, 4]), np.array([.25, .75]))
    if shared:
        ka_n = 7
        edges += [(j, 3, .003) for j in range(4, 7)]
        cfg['source_support']['pads']['+12V'].append({'ref': 'TPsecond', 'pad_id': 'source2'})
        ka_support['source2'] = (np.array([4, 5, 6]), np.full(3, 1/3))
    ka_inside = {k: np.ones(len(ns), dtype=bool) for k, (ns, _) in ka_support.items()}
    kb_support = {'CS247-KB-W1': (np.array([0]), np.array([1.])), 'load': (np.array([1]), np.array([1.]))}
    kb_inside = {k: np.ones(len(ns), dtype=bool) for k, (ns, _) in kb_support.items()}
    aa, ai = sheet_assembly(ka_n, edges, ka_support, ka_inside, 'KA')
    ba, bi = sheet_assembly(2, [(0, 1, .004)], kb_support, kb_inside, 'KB')
    assemblies, items = {'KA': aa, 'KB': ba}, {'KA': ai, 'KB': bi}
    ops = operators_from(assemblies)
    obs = {'board': 'KB', 'pad_uuid': 'load', 'ref': 'Ufixture', 'pin': '4', 'net': '+12V',
           'process_case': 'nominal-average', 'depth_case': 'uniform-dielectric'}
    return {'operators': ops, 'reductions': reductions_from(ops, cfg), 'assemblies': assemblies, 'items': items,
            'plans': {'KA': [(0, None)], 'KB': [(0, None)]}, 'config': cfg, 'case': CASE, 'depth': UNIFORM, 'observation': obs}


class Reconstruction(unittest.TestCase):
    def passed(self, data, **kw):
        result, packet = B.fixture_report(**data, **kw)
        self.assertEqual(result['status'], 'PASS_MODELED_SOLUTION_ACCOUNTING_ONLY', result['failures'])
        self.assertFalse(result['electrical_acceptance'])
        self.assertFalse(result['whole_board_acceptance'])
        self.assertFalse(result['adopted'])
        self.assertEqual(result['uniqueness'], 'CHECKED_TINY_POSITIVE_DEFINITE_FREE_OPERATOR')
        # Existing reporter gives identical complete accounting from rebuilt detail.
        old = R.attribute(packet, R.bindings(packet))
        self.assertEqual({k: v for k, v in result.items() if k != 'reconstruction'}, old)
        return result, packet

    def test_series_reconstruction_to_existing_reporter(self):
        r, p = self.passed(fixture())
        self.assertAlmostEqual(r['effective_resistance_ohm'], .012)
        self.assertAlmostEqual(r['copper_resistance_ohm'], .005)
        self.assertAlmostEqual(r['source_currents_A'][0]['current_A'], -1.)
        self.assertEqual(r['reconstruction']['selected_rhs_count'], 1)
        # A hand-built voltage packet could hide the old loaded-field error.
        self.assertLess(max(map(float, p['solution']['potential_V'])), .013)

    def test_parallel(self):
        r, _ = self.passed(fixture(parallel=True))
        self.assertAlmostEqual(r['copper_resistance_ohm'], .0045)

    def test_shared_sources(self):
        r, _ = self.passed(fixture(shared=True))
        self.assertAlmostEqual(r['copper_resistance_ohm'], .0045)
        for p in r['source_currents_A']:
            self.assertAlmostEqual(p['current_A'], -.5)

    def test_unequal_distributed_support_potentials(self):
        r, p = self.passed(fixture(unequal=True))
        self.assertNotEqual(p['solution']['potential_V'][3], p['solution']['potential_V'][4])
        self.assertAlmostEqual(r['copper_resistance_ohm'], .001*.25**2+.003*.75**2+.004)
        self.assertAlmostEqual(r['class_energy_W']['termination'], .004)
        self.assertAlmostEqual(r['class_energy_W']['wire_bulk'], .003)

    def test_normalization(self):
        for current in (-3., .001, 2.):
            r, _ = self.passed(fixture(), current=current)
            self.assertAlmostEqual(r['effective_resistance_ohm'], .012)
            self.assertAlmostEqual(r['total_energy_W'], .012*current**2)

    def test_bad_normalization_before_solve(self):
        for current in (0., float('nan'), 1e200, 1e-200):
            with self.assertRaisesRegex(ValueError, 'normalization'):
                B.fixture_report(**fixture(), current=current)

    def test_source_identity_and_mapping_drift(self):
        d = fixture(); d['observation']['pad_uuid'] = 'source'
        with self.assertRaisesRegex(ValueError, 'held source pad'):
            B.fixture_report(**d)
        d = fixture(); d['reductions']['KA']['source_pads'] = ['renamed']
        with self.assertRaisesRegex(ValueError, 'source UUID drift'):
            B.fixture_report(**d)
        d = fixture(); d['operators'] = copy.deepcopy(d['operators'])
        d['operators']['KA']['supports']['source'][0][0] = 3
        with self.assertRaisesRegex(ValueError, 'mapping drift'):
            B.fixture_report(**d)

    def test_basis_and_schur_drift(self):
        for key in ('Y', 'S'):
            d = fixture(); d['reductions']['KA'][key] *= 1.01
            with self.assertRaisesRegex(ValueError, 'basis residual|Schur matrix'):
                B.fixture_report(**d)

    def test_missing_and_duplicate_tiles(self):
        d = fixture(); d['items']['KA'] = []
        with self.assertRaisesRegex(ValueError, 'missing final'):
            B.fixture_report(**d)
        d = fixture(); d['items']['KA'] *= 2; d['plans']['KA'] *= 2
        with self.assertRaisesRegex(ValueError, 'duplicate union'):
            B.fixture_report(**d)

    def test_hidden_operator_entry_even_equal_potential(self):
        d = fixture(); a = d['assemblies']['KA']; item = d['items']['KA'][0]
        # Zero-energy held-to-held edge still must reconcile the whole operator.
        extra = R.rank_one(a.N, [0, 1], [1., -1.], 1.)
        m = sp.csr_matrix((item['val'], (item['row'], item['col'])), shape=(a.N, a.N)) + extra
        item.update(row=m.tocoo().row, col=m.tocoo().col, val=m.data)
        with self.assertRaisesRegex(ValueError, 'absent from original|partition reconciliation'):
            B.fixture_report(**d)

    def test_shared_members_not_duplicated(self):
        r, _ = self.passed(fixture())
        sheets = [c for c in r['components'] if c['kind'] == 'sheet_union']
        self.assertEqual(len(sheets), 2)
        self.assertEqual(sheets[0]['object_ids'], ['overlapping-track', 'pad'])
        self.assertAlmostEqual(sum(c['joule_energy_W'] for c in sheets), .005)

    def test_removed_wire_is_terminal_floating_failure(self):
        with self.assertRaisesRegex(ValueError, 'singular/unresolved'):
            B.fixture_report(**fixture(), removed=(1,))

    def test_connected_removed_wire_keeps_both_end_terminations(self):
        d = fixture()
        d['config']['wires']['pairs']['W2'] = '+12V'
        for board in ('KA', 'KB'):
            asm = d['assemblies'][board]; op = d['operators'][board]
            t1, t2 = f'CS247-{board}-W1', f'CS247-{board}-W2'
            asm.supports[t2] = copy.deepcopy(asm.supports[t1])
            asm.support_inside[t2] = asm.support_inside[t1].copy()
            op['terminals'].append(t2)
        d['reductions'] = reductions_from(d['operators'], d['config'])
        r, packet = self.passed(d, removed=(1,))
        self.assertAlmostEqual(r['effective_resistance_ohm'], .012)
        self.assertEqual(len([c for c in r['components'] if c['kind'] == 'termination']), 4)
        self.assertEqual([c['id'] for c in r['components'] if c['kind'] == 'wire_bulk'], ['W2:bulk'])
        matrix = R.matrix_read(packet['network']['matrix'])
        fixed = packet['identity']['source_support']['pads'][0]['nodes']
        free = np.array([i for i in range(matrix.shape[0]) if i not in fixed])
        direct = np.linalg.solve(matrix[free][:,free].toarray(), np.array(packet['solution']['injection_A'], dtype=float)[free])
        np.testing.assert_allclose(direct, np.array(packet['solution']['potential_V'], dtype=float)[free], rtol=1e-12, atol=1e-15)

    def test_bound_failure_before_factorization(self):
        d = fixture(); d['operators']['KA']['N'] = 1515457
        with patch.object(S, 'board_parts') as parts, patch.object(B.spla, 'splu') as factor:
            with self.assertRaisesRegex(ValueError, 'PRODUCTION_BLOCKED'):
                B.fixture_report(**d)
            parts.assert_not_called(); factor.assert_not_called()

    def test_output_failure_no_partial_result_and_no_input_mutation(self):
        d = fixture(); before = d['reductions']['KB']['Y'].copy()
        with self.assertRaisesRegex(ValueError, 'output resource bound'):
            B.fixture_report(**d, output_limit=1)
        np.testing.assert_array_equal(d['reductions']['KB']['Y'], before)
        # No output directory or process is created by these pure fixture APIs.
        self.passed(d)

    def test_declared_node_count_does_not_hide_large_storage(self):
        for what in ('shape', 'entries', 'vertices', 'items'):
            d = fixture()
            if what == 'shape':
                d['operators']['KA']['Kg_face'] = sp.csr_matrix((1000,1000))
            elif what == 'entries':
                d['operators']['KA']['Kg_face'] = sp.coo_matrix((np.ones(65537), (np.zeros(65537, dtype=int), np.zeros(65537, dtype=int))), shape=(4,4))
            elif what == 'vertices':
                d['items']['KA'][0]['xy'] = np.zeros((4097,2))
            else:
                d['items']['KA'] *= 129
            with patch.object(S, 'full_matrix') as matrix, patch.object(B.spla, 'splu') as factor:
                with self.assertRaisesRegex(ValueError, 'resource bound'):
                    B.fixture_report(**d)
                matrix.assert_not_called(); factor.assert_not_called()

    def test_missing_production_map_cannot_trigger_assembly(self):
        with patch.object(B.A, 'Assembly') as assembly:
            with self.assertRaisesRegex(ValueError, 'PRODUCTION_BLOCKED'):
                B.recover_fixture_assembly({}, [], {'N':1541278})
            assembly.assert_not_called()

    def test_recovery_bounds_actual_geometry_and_sparse_payloads(self):
        for what in ('wkb', 'row', 'boundary', 'supports', 'operator'):
            d = fixture(); desc = d['assemblies']['KA'].desc; items = d['items']['KA']; op = d['operators']['KA']
            if what == 'wkb':
                desc['groups'][0]['wkb'] = 'a'*(1024**2+1)
            elif what in ('row', 'boundary'):
                items[0][what] = np.zeros(65537, dtype=int)
            elif what == 'supports':
                desc['supports'] = {'fake': [None]*65537}
            else:
                op['Kg_face'] = sp.csr_matrix((1000,1000))
            with patch.object(B.A, 'Assembly') as assembly:
                with self.assertRaisesRegex(ValueError, 'resource bound'):
                    B.recover_fixture_assembly(desc, items, op)
                assembly.assert_not_called()

    def test_direct_reconstruction_bounds_reduction_payload_before_work(self):
        d = fixture(); d['reductions']['KA']['S'] = np.zeros(65537)
        args = {k: d[k] for k in ('operators','reductions','config','case','depth','observation')}
        with patch.object(S, 'full_matrix') as matrix:
            with self.assertRaisesRegex(ValueError, 'resource bound'):
                B.reconstruct_fixture(**args)
            matrix.assert_not_called()

    def test_readiness_never_loads_real_artifacts_or_manufactures_request(self):
        with patch.object(S, 'pload', side_effect=AssertionError('real pickle prohibited')):
            report = B.readiness()
            self.assertEqual(report['B1'], 'NOT_EXECUTABLE_NOT_ADMITTED')
            self.assertEqual(report['operator_contract']['missing_original_mapping_fields'], ['group','vertex_node','xy'])
            self.assertIsNone(report['production_request_sha256'])
            self.assertIsNone(report['production_execute_command'])
            with tempfile.TemporaryDirectory() as directory:
                path = Path(directory)/'readiness.json'
                self.assertEqual(B.main(['--readiness','--output',str(path)]), 2)
                before = path.read_bytes()
                with self.assertRaises(FileExistsError):
                    B.main(['--readiness','--output',str(path)])
                self.assertEqual(path.read_bytes(), before)

    def test_local_component_operations_never_use_board_size(self):
        d = fixture(); asm = d['assemblies']['KA']; k, _, _ = B.A.laplacian(asm.Kg['face'], asm.Kg['inner'], {}, {}, CASE, UNIFORM)
        calls = []
        original = S._extended_residual
        def record(matrix, x, rhs):
            calls.append(matrix.shape[0]); return original(matrix, x, rhs)
        # One local two-node component in an otherwise larger reference.
        k = R.rank_one(1000, [9, 990], [1., -1.], 1.)
        v = np.zeros(1000); v[990] = 1.
        meta = {'id': 'tiny', 'board': 'KA', 'kind': 'barrel', 'object_ids': ['via'], 'layer_interval': ['F.Cu', 'B.Cu'], 'region': {}}
        with patch.object(S, '_extended_residual', side_effect=record):
            audit = B.account_copper(k, iter([(meta, np.array([9, 990]), R.rank_one(2, [0, 1], [1., -1.], 1.))]), v)
        self.assertEqual(calls, [2, 1000])  # local per component, original once.
        self.assertEqual(audit['energy_W'], 1.)

    def test_partition_current_uses_nodal_rhs_scale(self):
        matrix = R.rank_one(2, [0,1], [1.,-1.], 1.)
        meta = {'id':'edge','board':'KA','kind':'barrel','object_ids':['via'],
                'layer_interval':['F.Cu','B.Cu'],'region':{}}
        components = [(meta, np.array([0,1]), matrix)]
        original = S._extended_residual; calls = 0
        def perturb_reference(*args):
            nonlocal calls
            result = original(*args); calls += 1
            if calls == 2:
                result[0] += 1e-10  # At zero potential, so energy is unchanged.
            return result
        with patch.object(S, '_extended_residual', side_effect=perturb_reference):
            with self.assertRaisesRegex(ValueError, 'current reconciliation'):
                B.account_copper(matrix, iter(components), np.array([0.,1.]), injection_scale_A=.01)

    def test_real_mesh_assembly_rings_end_to_end(self):
        import shapely
        from shapely.geometry import Point, box
        d = fixture(); assemblies, items = {}, {}
        for board in ('KA', 'KB'):
            term = f'CS247-{board}-W1'
            pid = 'source' if board == 'KA' else 'load'
            copper = box(-1,-1,1,1).difference(Point(0,0).buffer(.15, quad_segs=4))
            desc = {'groups': [{'group': g, 'layer': layer, 'fragments': [f'plane{g}', f'overlap{g}'],
                                 'wkb': shapely.to_wkb(copper, hex=True)}
                                for g, layer in enumerate(('F.Cu', 'In4.Cu'))],
                    'supports': {}, 'terminals': [term],
                    'barrels': {board+'via': {'center_mm': [0,0], 'drill_mm': .3,
                                             'taps': [{'group': 0, 'layer': 'F.Cu'}, {'group': 1, 'layer': 'In4.Cu'}]}}}
            for support, group, patch in ((pid, 0, box(-1,-1,-.3,1)), (term, 1, box(.3,-1,1,1))):
                desc['supports'][support] = [{'fragment': support+'frag', 'group': group,
                                              'wkb': shapely.to_wkb(patch, hex=True), 'copper_area_mm2': patch.area}]
            items[board] = [B.A.mesh_item(desc, g, t, 1., 1.) for g, t in B.A.tiles(desc,1.,6.)]
            assemblies[board] = B.A.Assembly(desc, items[board])
        d.update(assemblies=assemblies, items=items, operators=operators_from(assemblies),
                 plans={b: [(it['group'], None if it['tile'] is None else tuple(it['tile'])) for it in its] for b, its in items.items()})
        # Recover discarded numbering from original mesh, as a future admitted
        # retained driver must, rather than pass the fixture's first Assembly.
        d['assemblies'] = {b: B.recover_fixture_assembly(a.desc, items[b], d['operators'][b])
                           for b, a in assemblies.items()}
        d['reductions'] = reductions_from(d['operators'], d['config'])
        r, _ = self.passed(d)
        barrels = [c for c in r['components'] if c['kind'] == 'barrel']
        self.assertEqual(len(barrels), 2)
        self.assertTrue(all(c['layer_interval'] == ['F.Cu','In4.Cu'] for c in barrels))
        self.assertTrue(any(len(c['object_ids']) > 1 for c in r['components']))


if __name__ == '__main__':
    unittest.main()
