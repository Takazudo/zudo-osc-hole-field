"""Inexpensive source and byte-ownership checks; native acceptance is separate."""
import json
import tempfile
import unittest
from pathlib import Path

from scripts.pcbgen.trimmer_labels import ROOT, _owned, _strip_owned, apply, digest
from scripts.pcbgen.trimmer_labels_native_regression import prepare_source_evidence, run
from scripts.pcbgen.uuid_tools import stable_uuid

FIXTURE = ROOT/'scripts/pcbgen/fixtures/trimmer-labels/two-face.kicad_pcb'
INVENTORY = ROOT/'design/service/trimmer-inventory.json'


class TrimmerLabelsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.base = self.path/'base.kicad_pcb'
        self.base.write_bytes(FIXTURE.read_bytes())
        rows = {r['ref']: r for r in json.loads(INVENTORY.read_text())['trimmers']}
        self.rows = rows
        self.policy = {
            'schema_version': 1, 'board_id': 'osc-core',
            'input_board_sha256': digest(self.base.read_bytes()),
            'inventory_sha256': digest(INVENTORY.read_bytes()),
            'base_board': 'base.kicad_pcb',
            'labels': [self.entry('RV1601', 141, 265), self.entry('RV2107', 191, 168)],
        }
        self.policy_path = self.path/'policy.json'

    def entry(self, ref, x, y):
        row = self.rows[ref]
        return {'ref': ref, 'block': row['block'], 'role': row['role'],
                'face': row['placement']['side'], 'x_mm': x, 'y_mm': y,
                'angle_deg': 0}

    def run_apply(self, input_path=None, output_name='out.kicad_pcb', check=False):
        self.policy_path.write_text(json.dumps(self.policy))
        out = self.path/output_name
        return apply(input_path or self.base, self.policy_path, out, check=check), out

    def test_both_faces_owner_artwork_and_nonannotation_bytes(self):
        report, out = self.run_apply()
        self.assertEqual(report['label_count'], 2)
        result = out.read_text()
        self.assertIn('(layer "F.SilkS")', result)
        self.assertIn('(layer "B.SilkS")', result)
        self.assertIn('(justify mirror)', result)
        self.assertIn('OWNER ARTWORK', result)
        self.assertEqual(_strip_owned(result, _owned(result, 'osc-core')[0]), self.base.read_text())
        self.run_apply(check=True)

    def test_duplicate_application_is_identical(self):
        _, first = self.run_apply()
        _, second = self.run_apply(first, 'second.kicad_pcb')
        self.assertEqual(first.read_bytes(), second.read_bytes())

    def test_two_line_label_and_replacement(self):
        self.policy['labels'][1]['text'] = self.rows['RV2107']['label'].replace(' FREQ ', '\nFREQ ')
        _, first = self.run_apply()
        self.assertIn('\\n', first.read_text())
        self.policy['labels'] = [self.policy['labels'][0]]
        _, second = self.run_apply(first, 'second.kicad_pcb')
        self.assertNotIn(stable_uuid('osc-core','trimmer-labels-v1','RV2107'), second.read_text())

    def test_unknown_ref_role_pose_and_digest_rejected(self):
        cases = [({'ref': 'RV9999'}, 'unknown'),
                 ({'role': 'filter:WRONG'}, 'Role'),
                 ({'face': 'F.Cu'}, 'face')]
        for update, message in cases:
            with self.subTest(update=update):
                old = self.policy['labels'][1].copy()
                self.policy['labels'][1].update(update)
                with self.assertRaisesRegex(ValueError, message):
                    self.run_apply()
                self.policy['labels'][1] = old
        old_digest = self.policy['input_board_sha256']
        self.policy['input_board_sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'base board'):
            self.run_apply()
        self.policy['input_board_sha256'] = old_digest
        self.base.write_text(self.base.read_text().replace('(at 172.85 168.2 90)', '(at 172.95 168.2 90)'))
        self.policy['input_board_sha256'] = digest(self.base.read_bytes())
        with self.assertRaisesRegex(ValueError, 'stale footprint pose'):
            self.run_apply()

    def test_uuid_collision_and_nonowned_drift(self):
        uid = stable_uuid('osc-core','trimmer-labels-v1','RV1601')
        self.base.write_text(self.base.read_text().replace('33333333-3333-4333-8333-333333333333',uid))
        self.policy['input_board_sha256'] = digest(self.base.read_bytes())
        with self.assertRaisesRegex(ValueError, 'collision'):
            self.run_apply()
        self.base.write_bytes(FIXTURE.read_bytes())
        self.policy['input_board_sha256'] = digest(self.base.read_bytes())
        _, first = self.run_apply()
        drift = self.path/'drift.kicad_pcb'
        drift.write_text(first.read_text().replace('OWNER ARTWORK','CHANGED ARTWORK'))
        with self.assertRaisesRegex(ValueError, 'non-owned input board drift'):
            self.run_apply(drift, 'second.kicad_pcb')

    def test_unreviewed_label_override_rejected(self):
        self.policy['labels'][0]['text'] = 'DIFFERENT FUNCTION'
        with self.assertRaisesRegex(ValueError, 'reviewed function dictionary'):
            self.run_apply()

    def test_retained_source_artifacts_include_both_faces_and_removal(self):
        evidence = self.path/'retained'
        candidate = prepare_source_evidence(evidence)
        self.assertEqual((evidence/'second-apply.kicad_pcb').read_bytes(), candidate.read_bytes())
        self.assertEqual((evidence/'removed.kicad_pcb').read_bytes(), (evidence/'input.kicad_pcb').read_bytes())
        result = candidate.read_text()
        self.assertIn('(layer "F.SilkS")', result)
        self.assertIn('(layer "B.SilkS")', result)
        self.assertIn('(justify mirror)', result)
        self.assertTrue((evidence/'policy.json').is_file())
        self.assertTrue((evidence/'removal-policy.json').is_file())
        with self.assertRaises(FileExistsError):
            prepare_source_evidence(evidence)

    def test_native_preflight_failure_retains_hashes_and_negative_status(self):
        class WrongVersion:
            @staticmethod
            def GetBuildVersion():
                return '0.0.0 (source-test stand-in, not native acceptance)'

        evidence = self.path/'failure-evidence'
        with self.assertRaisesRegex(ValueError, 'pinned KiCad'):
            run(evidence, WrongVersion)
        receipt = json.loads((evidence/'receipt.json').read_text())
        self.assertEqual(receipt['status'], 'FAIL / NATIVE ACCEPTANCE NOT ESTABLISHED')
        self.assertIn('failure.txt', receipt['files_sha256'])
        for name in ('input.kicad_pcb','inventory.json','policy.json','candidate.kicad_pcb',
                     'second-apply.kicad_pcb','removal-policy.json','removed.kicad_pcb'):
            path = evidence/'source'/name
            self.assertEqual(receipt['files_sha256']['source/'+name], digest(path.read_bytes()))
        with self.assertRaises(FileExistsError):
            run(evidence, WrongVersion)

    def test_native_load_failure_keeps_candidate_and_explicit_failure(self):
        class LoadFailure:
            @staticmethod
            def GetBuildVersion():
                return '10.0.6'

            @staticmethod
            def LoadBoard(_path):
                return None

        evidence = self.path/'load-failure'
        with self.assertRaisesRegex(ValueError, 'failed to load candidate'):
            run(evidence, LoadFailure)
        receipt = json.loads((evidence/'receipt.json').read_text())
        self.assertEqual(receipt['status'], 'FAIL / NATIVE ACCEPTANCE NOT ESTABLISHED')
        self.assertEqual(receipt['error'], 'KiCad failed to load candidate')
        self.assertTrue((evidence/'source/candidate.kicad_pcb').is_file())
        self.assertEqual(receipt['files_sha256']['failure.txt'], digest((evidence/'failure.txt').read_bytes()))


if __name__ == '__main__':
    unittest.main()
