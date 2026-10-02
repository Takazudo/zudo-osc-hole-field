"""Retained review evidence must follow actual source and native output bytes."""
import hashlib
import json
from pathlib import Path
import shutil
from tempfile import TemporaryDirectory
import unittest
from scripts.panel.check_review_receipt import ROOT, RECEIPT, INPUTS, OUTPUTS, ABSENT_INPUTS, verify


class PanelReviewReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temp = TemporaryDirectory(); self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        for path in (*INPUTS, *OUTPUTS, RECEIPT):
            target = self.root / path; target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / path, target)

    def receipt(self, mutate):
        path = self.root / RECEIPT; value = json.loads(path.read_text())
        mutate(value); path.write_text(json.dumps(value))

    def update_output_hash(self, path):
        data = (self.root / path).read_bytes()
        self.receipt(lambda r: r['outputs'].__setitem__(path, {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}))

    def test_current_retained_evidence_passes(self):
        verify(self.root)

    def test_every_input_and_output_byte_change_is_rejected(self):
        for path in (*INPUTS, *OUTPUTS):
            with self.subTest(path=path):
                target = self.root / path; before = target.read_bytes()
                target.write_bytes(before + b'\n')
                with self.assertRaisesRegex(ValueError, 'stale native panel'):
                    verify(self.root)
                target.write_bytes(before)

    def test_missing_identity_and_invalid_hash_metadata_are_rejected(self):
        original = (self.root / RECEIPT).read_bytes()
        for mutate in (lambda r: r.update(schema_version=True),
                       lambda r: r['inputs'].pop(INPUTS[0]),
                       lambda r: r['outputs'].pop(OUTPUTS[0]),
                       lambda r: r['inputs'][INPUTS[0]].update(bytes=True),
                       lambda r: r['inputs'][INPUTS[0]].update(sha256='bad')):
            self.receipt(mutate)
            with self.assertRaises(ValueError): verify(self.root)
            (self.root / RECEIPT).write_bytes(original)

    def test_native_drc_schema_and_findings_cannot_be_rehashed_into_success(self):
        path = self.root / OUTPUTS[0]; original = path.read_bytes()
        for mutate in (lambda r: r.pop('$schema'),
                       lambda r: r.pop('violations'),
                       lambda r: r.update(unconnected_items=None),
                       lambda r: r.update(violations=[{'severity': 'error'}]),
                       lambda r: r.update(included_severities=['warning']),
                       lambda r: r.update(included_severities=['error', 'warning']),
                       lambda r: r.update(source='another.kicad_pcb'),
                       lambda r: r.update(kicad_version='10.0.5')):
            value = json.loads(original); mutate(value); path.write_text(json.dumps(value))
            self.update_output_hash(OUTPUTS[0])
            with self.assertRaisesRegex(ValueError, 'native panel DRC'): verify(self.root)

    def test_command_and_oracle_changes_are_rejected(self):
        original = (self.root / RECEIPT).read_bytes()
        for mutate in (lambda r: r['commands']['drc'].remove('--severity-all'),
                       lambda r: r['oracle'].update(kicad_version='10.0.5'),
                       lambda r: r['oracle'].update(image='unrelated')):
            self.receipt(mutate)
            with self.assertRaises(ValueError): verify(self.root)
            (self.root / RECEIPT).write_bytes(original)

    def test_new_custom_rule_file_cannot_hide_outside_hashed_inputs(self):
        path = self.root / ABSENT_INPUTS[0]
        path.write_text('(version 1)\n(rule "new clearance" (constraint clearance (min 0mm)))\n')
        with self.assertRaisesRegex(ValueError, 'custom-rule absence changed'):
            verify(self.root)
        path.unlink()
        self.receipt(lambda r: r.update(absent_inputs=[]))
        with self.assertRaisesRegex(ValueError, 'absence declaration'):
            verify(self.root)

    def test_weakened_project_rules_cannot_be_rehashed_into_success(self):
        path = self.root / INPUTS[1]; original = path.read_bytes()
        for mutate in (lambda d: d['rules'].update(min_hole_clearance=.1),
                       lambda d: d['rules'].update(min_copper_edge_clearance=.1),
                       lambda d: d['rule_severities'].update(hole_clearance='ignore'),
                       lambda d: d.update(drc_exclusions=['waiver'])):
            value = json.loads(original); mutate(value['board']['design_settings'])
            path.write_text(json.dumps(value)); data = path.read_bytes()
            self.receipt(lambda r: r['inputs'].__setitem__(INPUTS[1],
                {'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}))
            with self.assertRaisesRegex(ValueError, 'source rule floor'):
                verify(self.root)

    def test_receipt_summary_must_match_native_table_and_command(self):
        original = (self.root / RECEIPT).read_bytes()
        for mutate in (lambda r: r['feature_summary'].update(features=1),
                       lambda r: r.update(render_requested_pixels=[1, 1])):
            self.receipt(mutate)
            with self.assertRaisesRegex(ValueError, 'summary differs'):
                verify(self.root)
            (self.root / RECEIPT).write_bytes(original)

    def test_published_image_must_remain_the_same_native_output(self):
        path = OUTPUTS[3]; target = self.root / path
        target.write_bytes(target.read_bytes() + b'other copy')
        self.update_output_hash(path)
        with self.assertRaisesRegex(ValueError, 'published panel image differs'):
            verify(self.root)


if __name__ == '__main__':
    unittest.main()
