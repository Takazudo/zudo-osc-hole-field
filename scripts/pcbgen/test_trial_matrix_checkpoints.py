"""Restart equivalence and refusal paths for the real small conductor fixture."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
from shapely.geometry import box

from scripts.pcbgen.batch_checkpoint_store import (
    BatchCheckpointStore, CheckpointError, digest_run_material,
)
from scripts.pcbgen.current_trial_matrix import current_matrix
from scripts.pcbgen.potential_trial_matrix import potential_matrix
from scripts.pcbgen.test_sheet_volume import RHO, THICKNESS, assembly


class TrialMatrixCheckpointTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.source = box(.4, .4, .65, .65)
        self.sink = box(-.7, -.5, -.45, -.25)
        self.profiles = [[(3, self.source, 1.), (1, self.sink, -1.)],
                         [(0, self.source, 1.), (1, self.sink, -1.)]]
        self.source_epoch = 'a' * 64
        self.operand_epoch = None
        self.verify_calls = 0

    def conductor(self, mode):
        result = assembly([(0, 0)], (-1, -1, 1, 1), self.source, self.sink, 1)
        result.certificate_mode = mode
        return result

    def factory(self, mode, operands):
        if self.operand_epoch is not None:
            operands = dict(operands)
            operands['solve_matrix'] = self.operand_epoch
        key = digest_run_material({'source': self.source_epoch,
                                   'profile': [p[0][1].wkb_hex for p in self.profiles],
                                   'mode': mode, 'operands': operands})
        return BatchCheckpointStore(self.path / mode, run_key=key,
                                    mode=mode, profile_count=2, batch_size=1)

    def verify(self):
        self.verify_calls += 1
        if self.source_epoch != 'a' * 64:
            raise ValueError('source changed during checkpoint write')

    def run_mode(self, mode, checkpoint=True):
        conductor = self.conductor(mode)
        options = {'batch_size': 1}
        if checkpoint:
            options.update(checkpoint_factory=self.factory,
                           checkpoint_verify=self.verify)
        if mode == 'current':
            return current_matrix(conductor, self.profiles, RHO, THICKNESS, **options)
        return potential_matrix(conductor, self.profiles, **options)

    def test_interrupted_then_resumed_matches_uninterrupted_both_modes(self):
        for mode in ('current', 'potential'):
            with self.subTest(mode=mode):
                baseline = self.run_mode(mode, checkpoint=False)
                module = ('scripts.pcbgen.current_trial_matrix' if mode == 'current'
                          else 'scripts.pcbgen.potential_trial_matrix')
                import importlib
                original = importlib.import_module(module).refine
                calls = 0

                def interrupt(*args):
                    nonlocal calls
                    calls += 1
                    if calls == 2:
                        raise RuntimeError('interrupted after one batch')
                    return original(*args)

                with patch(module + '.refine', side_effect=interrupt):
                    with self.assertRaisesRegex(RuntimeError, 'interrupted'):
                        self.run_mode(mode)
                files = list((self.path / mode).glob('batch-*.json'))
                self.assertEqual(len(files), 1)
                with patch(module + '.refine', wraps=original) as resumed_refine:
                    resumed = self.run_mode(mode)
                self.assertEqual(resumed_refine.call_count, 1)
                np.testing.assert_array_equal(resumed['energy'], baseline['energy'])
                self.assertEqual(resumed['maximum_equation_residual_A'],
                                 baseline['maximum_equation_residual_A'])
                self.assertEqual(resumed['residual_work_allowance_by_profile_ohm'],
                                 baseline['residual_work_allowance_by_profile_ohm'])
                self.assertGreaterEqual(self.verify_calls, 3)

    def test_mutated_source_operand_and_payload_refuse_reuse(self):
        self.run_mode('potential')
        self.source_epoch = 'b' * 64
        with self.assertRaisesRegex(ValueError, 'source changed'):
            self.run_mode('potential')
        self.source_epoch = 'a' * 64
        self.operand_epoch = '0' * 64
        with self.assertRaisesRegex(CheckpointError, 'run_key'):
            self.run_mode('potential')
        self.operand_epoch = None
        payload = self.path / 'potential' / 'batch-00000000-00000001.npz'
        payload.write_bytes(payload.read_bytes() + b'corrupt')
        with self.assertRaisesRegex(CheckpointError, 'payload hash'):
            self.run_mode('potential')

    def test_source_change_during_first_batch_prevents_checkpoint_commit(self):
        import scripts.pcbgen.potential_trial_matrix as potential_module
        original = potential_module.refine

        def mutate_after_solve(*args):
            field, receipt = original(*args)
            self.source_epoch = 'b' * 64
            return field, receipt

        with patch.object(potential_module, 'refine', side_effect=mutate_after_solve):
            with self.assertRaisesRegex(ValueError, 'source changed'):
                self.run_mode('potential')
        self.assertEqual(list((self.path / 'potential').glob('batch-*')), [])


if __name__ == '__main__':
    unittest.main()
