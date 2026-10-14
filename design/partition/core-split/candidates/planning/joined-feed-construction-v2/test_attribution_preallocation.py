"""Bounded metadata/constructor fixtures; never load retained original data."""
import os
os.environ.update(OPENBLAS_NUM_THREADS='1', OMP_NUM_THREADS='1', MKL_NUM_THREADS='1')
import resource
resource.setrlimit(resource.RLIMIT_AS, (512 * 1024**2, 512 * 1024**2))
resource.setrlimit(resource.RLIMIT_CPU, (20, 20))
import copy
import unittest
from unittest.mock import patch

import numpy as np
import scipy.sparse as sp
import attribution_preallocation as G
import attribution_executor as E
import finite_solve as S
from test_finite_adapter import CASE, UNIFORM


class DescriptorArray:
    def __init__(self, size, dtype):
        self.size = size
        self.shape = (size,)
        self.ndim = 1
        self.dtype = np.dtype(dtype)

    def __getitem__(self, key):
        raise AssertionError('numeric/index value read during metadata preflight')

    def __array__(self, *args, **kwargs):
        raise AssertionError('array conversion during metadata preflight')

    def __iter__(self):
        raise AssertionError('array value iteration during metadata preflight')


class DescriptorCSR:
    format = 'csr'
    dtype = np.dtype('float64')

    def __init__(self, n, count):
        self.shape = (n, n)
        self.data = DescriptorArray(count, 'float64')
        self.indices = DescriptorArray(count, 'int32')
        self.indptr = DescriptorArray(n + 1, 'int32')

    @property
    def nnz(self):
        raise AssertionError('logical nnz may index indptr; use stored size metadata')


def descriptors(n=5, face=7, inner=3, sizes=(2, 3), taps=(0, 1, 3)):
    terms = ['terminal-' + str(i) for i in range(len(sizes))]
    return {'N': n, 'Kg_face': DescriptorCSR(n, face), 'Kg_inner': DescriptorCSR(n, inner),
            'barrels': {str(i): {'taps': [{}] * count} for i, count in enumerate(taps)},
            'terminals': terms,
            'supports': {term: (DescriptorArray(size, 'int64'), DescriptorArray(size, 'float64'))
                         for term, size in zip(terms, sizes)}}


def policy(raw=1000):
    return {'max_raw_entries': raw, 'memory_envelope': {
        'live_baseline_bytes_upper': 1024**2,
        'other_constructor_bytes_upper': 16 * 1024**2,
        'native_workspace_bytes_upper': 16 * 1024**2,
        'allocator_and_tail_bytes_upper': 16 * 1024**2,
        'evidence_reference': 'synthetic-only declared test envelope; not production qualification',
    }}


class Budget:
    def __init__(self):
        self.calls = 0
        self.started = 1
        self.deadline = 2

    def check(self):
        self.calls += 1


class PreallocationTests(unittest.TestCase):
    def test_exact_count_without_value_reads(self):
        budget = Budget()
        report = G.preflight(descriptors(), policy(31), budget.check)
        self.assertEqual(report['barrel_raw_triples'], 8)
        self.assertEqual(report['K_stored_upper'], 18)
        self.assertEqual(report['termination_raw_triples'], 13)
        self.assertEqual(report['raw_coordinate_upper'], 31)
        self.assertEqual(report['largest_outer_entries'], 9)
        self.assertEqual(report['metadata_visits'], 7)
        self.assertEqual(report['named_array_bytes']['coordinate_conversion_arrays_upper'], 80 * 31 + 8 * 6)
        self.assertEqual(report['full_pipeline_qualification'], 'NOT_QUALIFIED')
        self.assertEqual(report['declared_envelope_gate'], 'PASS')
        self.assertEqual((budget.started, budget.deadline), (1, 2))
        self.assertGreater(budget.calls, report['metadata_visits'])
        with self.assertRaisesRegex(ValueError, 'raw coordinate ceiling'):
            G.preflight(descriptors(), policy(30), budget.check)

    def test_raw_outer_bound_does_not_assume_distinct_or_free_nodes(self):
        # Descriptors contain no node or weight values. Overlap, held filtering,
        # duplicates and zero weights therefore cannot incorrectly reduce s^2.
        op = descriptors(n=1, face=1, inner=0, sizes=(4, 4), taps=())
        result = G.preflight(op, policy(), Budget().check)
        self.assertEqual(result['termination_raw_triples'], 32)
        huge = descriptors(n=1, face=0, inner=0, sizes=(G.MAX_RAW_ENTRIES,), taps=())
        with self.assertRaisesRegex(ValueError, 'raw coordinate ceiling'):
            G.preflight(huge, policy(G.MAX_RAW_ENTRIES), Budget().check)
        empty = G.preflight(descriptors(sizes=(0,), taps=()), policy(), Budget().check)
        self.assertEqual(empty['termination_raw_triples'], 0)

    def test_malformed_and_cap_inputs(self):
        mutations = [
            lambda o: o.update(N=True),
            lambda o: setattr(o['Kg_face'], 'shape', (5, 6)),
            lambda o: setattr(o['Kg_face'].data, 'dtype', np.dtype('float32')),
            lambda o: setattr(o['Kg_face'].indices, 'size', 3),
            lambda o: setattr(o['Kg_inner'].indptr, 'shape', (5,)),
            lambda o: o['terminals'].append(o['terminals'][0]),
            lambda o: setattr(o['supports'][o['terminals'][0]][1], 'shape', (1,)),
        ]
        for mutate in mutations:
            op = descriptors()
            mutate(op)
            with self.assertRaises(ValueError):
                G.preflight(op, policy(), Budget().check)
        for limit in (True, 0, -1, G.MAX_RAW_ENTRIES + 1):
            with self.assertRaises(ValueError):
                G.preflight(descriptors(), policy(limit), Budget().check)

    def test_missing_or_excess_envelope_precedes_any_numerical_constructor(self):
        for change in (lambda p: p.update(memory_envelope=None),
                       lambda p: p['memory_envelope'].pop('native_workspace_bytes_upper'),
                       lambda p: p['memory_envelope'].update(live_baseline_bytes_upper=G.WORKER_BYTES)):
            declared = policy()
            change(declared)
            with patch.object(E.S, 'board_parts') as constructor, patch.object(E.S, 'held_nodes') as held:
                with self.assertRaises(ValueError):
                    E._board_selected(descriptors(), None, None, None, None, 'KB', None, None,
                                      Budget(), preallocation_policy=declared)
                constructor.assert_not_called()
                held.assert_not_called()
            with patch.object(E.S, 'board_parts') as constructor:
                with self.assertRaises(ValueError):
                    E._guarded_board_parts(descriptors(), None, None, None, 'KB', Budget(), policy=declared)
                constructor.assert_not_called()

    def test_shared_deadline_and_legacy_path_unchanged(self):
        with patch.object(E.S, 'board_parts') as constructor:
            budget = Budget()
            budget.check = lambda: (_ for _ in ()).throw(ValueError('TIMEOUT'))
            with self.assertRaisesRegex(ValueError, 'TIMEOUT'):
                E._guarded_board_parts(descriptors(), None, None, None, 'KB', budget, policy=policy())
            constructor.assert_not_called()
        with patch.object(E, '_construction_preflight', side_effect=AssertionError('legacy opt-in')) as guard:
            with patch.object(E.S, 'held_nodes', side_effect=RuntimeError('legacy held entry')):
                with self.assertRaisesRegex(RuntimeError, 'legacy held entry'):
                    E._board_selected({}, None, None, None, None, 'KB', None, None, Budget())
            guard.assert_not_called()

    def test_guarded_constructor_preserves_exact_original_output(self):
        term = 'CS247-KB-W1'
        op = {'N': 3,
              'Kg_face': sp.csr_matrix(np.array([[1., -1., 0.], [-1., 2., -1.], [0., -1., 1.]])),
              'Kg_inner': sp.csr_matrix((3, 3), dtype=np.float64), 'barrels': {}, 'rings': {},
              'terminals': [term],
              'supports': {term: (np.array([1, 2], dtype=np.int64), np.array([.25, .75]))}}
        cfg = {'source_support': {'board': 'KA'}, 'wires': {'termination_per_end_ohm': .7}}
        before = copy.deepcopy(op)
        expected = S.board_parts(op, CASE, UNIFORM, cfg, 'KB', E.NET)
        actual, report = E._guarded_board_parts(op, CASE, UNIFORM, cfg, 'KB', Budget(), policy=policy())
        for left, right in zip(expected, actual):
            if sp.issparse(left):
                self.assertEqual((left.format, left.shape), (right.format, right.shape))
                for name in ('data', 'indices', 'indptr'):
                    self.assertEqual(getattr(left, name).dtype, getattr(right, name).dtype)
                    self.assertEqual(getattr(left, name).tobytes(), getattr(right, name).tobytes())
            elif isinstance(left, np.ndarray):
                self.assertEqual((left.shape, left.dtype, left.tobytes()), (right.shape, right.dtype, right.tobytes()))
            else:
                self.assertEqual(left, right)
        self.assertEqual(op['Kg_face'].data.tobytes(), before['Kg_face'].data.tobytes())
        self.assertEqual(report['raw_coordinate_upper'], 11)
        self.assertEqual(report['full_pipeline_qualification'], 'NOT_QUALIFIED')


if __name__ == '__main__':
    unittest.main(verbosity=2)
