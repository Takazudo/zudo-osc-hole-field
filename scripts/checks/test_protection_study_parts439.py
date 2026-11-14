"""The parts-439 protection re-study must reject any change it did not review."""
import copy
import json
import unittest

from scripts.checks import protection_study_parts439 as study


def current(path):
    return (study.ROOT / path).read_bytes()


def base(path):
    return study.at(study.TRANSITION_BASE, path)


def mutate_standard(change):
    data = json.loads(current(study.STANDARD))
    change(data)
    raw = json.dumps(data, indent=2).encode()
    return lambda path: raw if path == study.STANDARD else current(path)


class ProtectionStudyParts439(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.projection = study.model_projection(study.ROOT)

    def derive(self, current_bytes=current, base_projection=None):
        return study.derive(current_bytes=current_bytes, base_bytes=base,
                            base_projection=base_projection or (lambda: self.projection),
                            current_projection=lambda: self.projection)

    def test_record_equals_a_fresh_derivation_including_the_base_worktree(self):
        record = json.loads(study.RECORD.read_text())
        self.assertEqual(record, json.loads(study.body(study.derive())))
        self.assertEqual(record['hardware_protection'], 'OPEN; physical qualification NOT RUN')

    def test_recorded_delta_is_identity_only_and_outside_consumed_cells(self):
        delta = json.loads(study.RECORD.read_text())['changed_bound_inputs'][study.STANDARD]['delta']
        self.assertEqual(len(delta), 11)
        self.assertTrue(all(row['pointer'].endswith('/part_id') for row in delta))
        self.assertFalse({row['cell'] for row in delta} & {'general_output', 'precision_output'})

    def test_consumed_standard_field_change_is_rejected(self):
        def change(data):
            data['signals'][next(iter(data['signals']))] = 'unreviewed'
        with self.assertRaisesRegex(ValueError, 'Electrical standard changed beyond a cell part_id|Consumed standard field changed'):
            self.derive(mutate_standard(change))

    def test_consumed_cell_part_id_change_is_rejected(self):
        def change(data):
            cell = next(c for c in data['cells'] if c['id'] == 'precision_output')
            part = next(p for p in cell['parts'] if 'part_id' in p)
            part['part_id'] = 'unreviewed_identity'
        with self.assertRaisesRegex(ValueError, 'Consumed standard field changed: cells\\[id=precision_output\\]'):
            self.derive(mutate_standard(change))

    def test_non_identity_standard_change_is_rejected(self):
        def change(data):
            cell = next(c for c in data['cells'] if c['id'] == 'stage_indicator')
            cell['parts'][0]['value'] = 1
        with self.assertRaisesRegex(ValueError, 'beyond a cell part_id'):
            self.derive(mutate_standard(change))

    def test_unreviewed_bound_input_change_is_rejected(self):
        name = 'design/power/supply-architecture.json'
        changed = lambda path: current(path) + b' ' if path == name else current(path)
        with self.assertRaisesRegex(ValueError, 'Unreviewed bound input change'):
            self.derive(changed)

    def test_changed_model_projection_is_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Precision model source projection changed'):
            self.derive(base_projection=lambda: '0' * 64)

    def test_obligation_projection_change_is_rejected(self):
        audit = json.loads(current(study.bridge.AUDIT))
        changed_audit = copy.deepcopy(audit)
        changed_audit['outputs'][0]['uid'] = 'unreviewed-output'
        raw = json.dumps(changed_audit).encode()
        with self.assertRaisesRegex(ValueError, 'obligation changed: outputs'):
            self.derive(lambda path: raw if path == study.bridge.AUDIT else current(path))


if __name__ == '__main__':
    unittest.main()
