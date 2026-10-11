"""Source authentication, no-search mask semantics and native fail-closed tests."""
import copy
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np

from prepare_diagnostic import (HERE, ROOT, authenticate, encoded, first_via_mask,
                                prepare, read, target_members, validate_dump)
from native_diagnostic import require_admission

ARCHIVE = Path(sys.argv.pop(1)) if len(sys.argv) > 1 and not sys.argv[1].startswith('-') else None


class MaskSemantics(unittest.TestCase):
    def masks(self):
        free = np.zeros((2, 5, 5), bool)
        free[0, 2, 1:4] = True
        src = np.zeros_like(free)
        src[0, 2, 1] = True
        via = np.zeros((5, 5), bool)
        return free, via, src

    def test_legal_via_in_disconnected_component_is_negative(self):
        free, via, src = self.masks()
        free[:, 0, 0] = True
        via[0, 0] = True
        result = first_via_mask(free, via, src, np.zeros_like(src))
        self.assertEqual(result['legal_via_cells'], 1)
        self.assertTrue(result['negative'])

    def test_first_reachable_via_is_not_negative_or_routing_acceptance(self):
        free, via, src = self.masks()
        via[2, 3] = True
        result = first_via_mask(free, via, src, np.zeros_like(src))
        self.assertFalse(result['negative'])
        self.assertFalse(result['search_executed'])
        self.assertFalse(result['native_executed'])

    def test_other_layer_cannot_be_reached_before_first_via(self):
        free, via, src = self.masks()
        free[1, :, :] = True
        via[0, 0] = True
        result = first_via_mask(free, via, src, np.zeros_like(src))
        self.assertTrue(result['negative'])
        self.assertEqual(result['layers'][1]['optimistic_reachable_cells'], 0)

    def test_no_direct_native_execution_even_with_slot_text(self):
        with patch.dict('os.environ', {}, clear=True):
            with self.assertRaisesRegex(ValueError, 'bounded guard'):
                require_admission('not-an-admission', '250-test')
        with self.assertRaises(ValueError):
            require_admission(None, '250-test')

    def test_guard_environment_cannot_substitute_for_cgroup_membership(self):
        env = {'EPIC242_NATIVE_WORKER': 'jl250-test',
               'EPIC242_NATIVE_SLICE': 'epic242-jl250-test.slice',
               'EPIC242_NATIVE_DEADLINE': '9999999999'}
        with patch.dict('os.environ', env, clear=True), patch.object(
                Path, 'read_text', return_value='0::/unbounded.service\n'):
            with self.assertRaisesRegex(ValueError, 'outside'):
                require_admission('parent-slot', '250-test')

    def test_cgroup_name_cannot_substitute_for_memory_cap(self):
        env = {'EPIC242_NATIVE_WORKER': 'jl250-test',
               'EPIC242_NATIVE_SLICE': 'epic242-jl250-test.slice',
               'EPIC242_NATIVE_DEADLINE': '9999999999'}

        def unbounded(path):
            return '0::/epic242-jl250-test.slice/checks.service\n' if str(path) == '/proc/self/cgroup' else 'max\n'

        with patch.dict('os.environ', env, clear=True), patch.object(Path, 'read_text', unbounded):
            with self.assertRaisesRegex(ValueError, 'cap'):
                require_admission('parent-slot', '250-test')


@unittest.skipUnless(ARCHIVE, 'exact retained JL117 ZIP required for artifact tests')
class RetainedInput(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.dump, cls.endpoints, cls.artifact = authenticate(ARCHIVE)

    def test_equal_edge_count_wrong_group_is_rejected(self):
        dump = copy.deepcopy(self.dump)
        groups = dump['islands']['AGND']
        groups[1], groups[2] = [groups[1][0], groups[2][0]], []
        self.assertEqual(sum(len(g)-1 for g in dump['islands'].values()), 117)
        with self.assertRaisesRegex(ValueError, 'membership'):
            validate_dump(dump, self.endpoints)

    def test_pose_drift_rejected(self):
        dump = copy.deepcopy(self.dump)
        uid = target_members(dump)[0]
        next(p for p in dump['pads'] if p['uuid'] == uid)['xy'][0] += 1
        with self.assertRaisesRegex(ValueError, 'pose'):
            validate_dump(dump, self.endpoints)

    def test_target_with_unannounced_copper_source_rejected(self):
        dump = copy.deepcopy(self.dump)
        group = target_members(dump)
        group.append(dump['tracks'][0]['uuid'])
        with self.assertRaisesRegex(ValueError, 'three-pad'):
            target_members(dump)

    def test_corrupt_archive_rejected_before_reading_members(self):
        with tempfile.TemporaryDirectory() as tmp:
            bad = Path(tmp) / 'bad.zip'
            bad.write_bytes(b'not the retained archive')
            with self.assertRaisesRegex(ValueError, 'size/digest'):
                authenticate(bad)

    def test_stale_published_input_rejected(self):
        original = Path.read_bytes

        def stale(path):
            if str(path).endswith('/boards/osc-jack-left/osc-jack-left.kicad_pcb'):
                return b'stale JL118'
            return original(path)

        with patch.object(Path, 'read_bytes', stale):
            with self.assertRaisesRegex(ValueError, 'published JL'):
                authenticate(ARCHIVE)

    def test_context_drift_rejected(self):
        original = Path.read_bytes

        def stale(path):
            if str(path).endswith('/boards/osc-jack-left/fp-lib-table'):
                return b'wrong relative library context'
            return original(path)

        with patch.object(Path, 'read_bytes', stale):
            with self.assertRaisesRegex(ValueError, 'context'):
                authenticate(ARCHIVE)

    def test_deterministic_source_replay_without_native_or_subprocess(self):
        with tempfile.TemporaryDirectory() as tmp, patch.object(
                subprocess, 'run', side_effect=AssertionError('no subprocess/native permitted')):
            generated = prepare(ARCHIVE, Path(tmp))
            for name, value in generated.items():
                self.assertEqual((HERE / name).read_bytes(), encoded(value))
            diagnostic = generated['diagnostic-plan.json']['diagnostic']
            self.assertTrue(all(r['negative'] for r in diagnostic['observations']))
            self.assertEqual([r['legal_via_cells'] for r in diagnostic['observations']], [1, 958])
            proposal = generated['no-copper-proposal.json']
            self.assertEqual(proposal['removed_uuids'], [])
            self.assertEqual(proposal['copper'], [])

    def test_all_unresolved_edges_and_endpoints_retained(self):
        cases = read(HERE / 'cases.json')['cases']
        self.assertEqual(sum(c['open_edges'] for c in cases), 117)
        self.assertEqual({c['net']: c['groups'] for c in cases}, self.endpoints['disconnected_nets'])
        self.assertEqual(len(self.endpoints['context_files']), 26)


if __name__ == '__main__':
    unittest.main()
