"""Source-only native fixture gate tests; pcbnew is never imported."""
import importlib.util
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import Mock, patch

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('annulus_fixture', HERE / 'fixtures/selective-annulus/native_roundtrip_characterization.py')
f = importlib.util.module_from_spec(spec)
spec.loader.exec_module(f)


class FixtureGateTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(); self.addCleanup(self.tmp.cleanup)
        self.base = Path(self.tmp.name)
        self.worker = 'local-' + 'a' * 32 + '-1-annulus'
        self.env = {'EPIC242_NATIVE_WORKER': self.worker, 'EPIC242_NATIVE_SLICE': 'epic242-w' + self.worker.encode().hex() + '.slice', 'EPIC242_NATIVE_DEADLINE': '2000000000'}
        self.gate = self.base / 'gate'; self.gate.mkdir()
        self.mounts = self.base / 'mountinfo'
        self.mounts.write_text('1 0 0:1 / /epic242-gate ro - bind none ro\n2 0 0:1 / /epic242-start.sh ro - bind none ro\n')
        self.cg = self.base / 'cgroup'; self.cg.mkdir()
        (self.cg / 'memory.max').write_text('6442450944'); (self.cg / 'memory.swap.max').write_text('0')
        self.expected = ['env', 'EXACT=fixture', 'python3', f.SCRIPT, 'native', '--output', '.circuit-cache/unique']
        pin = re.search(r"^KICAD_IMAGE='([^']+)'$", (f.ROOT / 'scripts/kicad/pin.env').read_text(), re.M).group(1)
        self.record = {'container_id': 'b' * 64, 'token': 'gate.abcdefghijkl', 'worker': self.worker, 'deadline': 2000000000, 'image': pin, 'command': self.expected}
        (self.gate / 'container-id').write_text('b' * 64)
        (self.gate / 'ack').write_text('gate.abcdefghijkl:' + 'b' * 64 + '\n')
        self.save()

    def save(self):
        (self.gate / 'request.json').write_text(json.dumps(self.record))

    def verify(self):
        f.verify_native_gate(self.env, self.expected, self.gate, self.mounts, self.cg)

    def test_exact_gate_control(self):
        self.verify()

    def test_command_image_identity_ack_drift_refused(self):
        for key, changed in [('command', ['wrong']), ('image', 'wrong'), ('worker', 'wrong'), ('deadline', 2000000001), ('container_id', 'c' * 64)]:
            original = self.record[key]; self.record[key] = changed; self.save()
            with self.subTest(key=key), self.assertRaises(ValueError): self.verify()
            self.record[key] = original; self.save()
        (self.gate / 'ack').write_text('wrong')
        with self.assertRaisesRegex(ValueError, 'acknowledgement'): self.verify()

    def test_actual_mounts_and_memory_zero_swap_required(self):
        for path, value in [(self.mounts, '1 0 0:1 / /epic242-gate rw - bind none rw\n'), (self.cg / 'memory.max', 'max'), (self.cg / 'memory.swap.max', '1')]:
            original = path.read_text(); path.write_text(value)
            with self.subTest(path=path), self.assertRaises(ValueError): self.verify()
            path.write_text(original)

    def test_host_membership_required(self):
        proc = self.base / 'membership'
        proc.write_text('0::/epic242.slice/' + self.env['EPIC242_NATIVE_SLICE'] + '/epic242-' + self.worker + '-checks.service\n')
        aggregate = self.cg / 'epic242.slice'; aggregate.mkdir()
        individual = aggregate / self.env['EPIC242_NATIVE_SLICE']; individual.mkdir()
        for path, cap in [(aggregate, '12884901888'), (individual, '6442450944')]:
            (path / 'memory.max').write_text(cap); (path / 'memory.swap.max').write_text('0')
        f.verify_host_resources(self.env, proc, self.cg)
        proc.write_text('0::/user.slice\n')
        with self.assertRaisesRegex(ValueError, 'actual host'): f.verify_host_resources(self.env, proc, self.cg)
        proc.write_text('0::/epic242.slice/' + self.env['EPIC242_NATIVE_SLICE'] + '/epic242-' + self.worker + '-checks.service\n')
        (aggregate / 'memory.max').write_text('max')
        with self.assertRaisesRegex(ValueError, 'caps'): f.verify_host_resources(self.env, proc, self.cg)

    def test_native_import_waits_for_authority_and_gate(self):
        with patch.object(f, 'context', side_effect=ValueError('missing authority')), patch.dict('sys.modules', {'pcbnew': None}), self.assertRaisesRegex(ValueError, 'authority'):
            f.native({}, '.circuit-cache/unique')
        with patch.object(f, 'context', return_value=(object(), {}, self.base)), patch.object(f, 'native_command', return_value=[]), patch.object(f, 'verify_native_gate', side_effect=ValueError('missing real gate')), patch.dict('sys.modules', {'pcbnew': None}), self.assertRaisesRegex(ValueError, 'real gate'):
            f.native({}, '.circuit-cache/unique')

    def test_worker_no_launch_before_actual_membership(self):
        output = self.base / 'not-created'
        with patch.object(f, 'context', return_value=(object(), {}, output)), patch.object(f, 'verify_host_resources', side_effect=ValueError('wrong cgroup')), patch.object(f.subprocess, 'run') as launch, self.assertRaisesRegex(ValueError, 'cgroup'):
            f.worker({}, '.circuit-cache/unique')
        self.assertFalse(output.exists()); launch.assert_not_called()

    def test_unavailable_layer_api_fails_explicitly_without_native_library(self):
        board, pcb = Mock(), Mock()
        pcb.GetBuildVersion.return_value = '10.0.6'; pcb.LoadBoard.return_value = board
        pcb.PCB_VIA_T = 7
        board.GetLayerID.side_effect = lambda name: {'F.Cu': 0, 'B.Cu': 2}.get(name, 4)
        tracks = [Mock() for _ in range(5)]
        for i, track in enumerate(tracks):
            track.Type.return_value = 7 if i < 2 else 9
            track.m_Uuid.AsString.return_value = f'e16a0000-0000-4000-8000-{i+1:012d}'
            track.GetDrillValue.return_value = 300000; track.GetNetname.return_value = 'AGND'
            track.TopLayer.return_value = 0; track.BottomLayer.return_value = 2
        board.GetTracks.return_value = tracks
        tracks[0].GetWidth.side_effect = TypeError('layer overload not exported')
        with self.assertRaisesRegex(ValueError, 'UNSUPPORTED_NATIVE_API'):
            f.characterize(pcb, f.FIXTURE, self.base / 'fresh.kicad_pcb')
        pcb.SaveBoard.assert_not_called()


if __name__ == '__main__':
    unittest.main()
