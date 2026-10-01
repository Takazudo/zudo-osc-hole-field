"""Portable runner obligations: no fabricated retained-data test passes."""
from fractions import Fraction as F
from pathlib import Path
import json
import tempfile
import unittest
from unittest.mock import patch
import numpy as np
from scripts.pcbgen.partial_cell_energy import CanonicalChart, ConservativeIndex, Budget
from scripts.pcbgen.partial_cell_energy_run import (
    artifact_path, merge_hashes, verify_inputs, fresh_output, rank_excluded,
    integrate_selected, refined_region, sha, snapshot_json, require_capture_bindings, candidate_census, record_failure)
from scripts.pcbgen.test_partial_cell_energy import sheet


class PartialCellRunTests(unittest.TestCase):
    def charts(self):
        potential = sheet([[0, 0], [2, 0], [0, 2], [2, 2]], [[0, 1, 2], [1, 3, 2]])
        current = sheet([[0, 0], [1, 0], [0, 2]], [[0, 1, 2]])
        p, c = CanonicalChart(potential, []), CanonicalChart(current, [])
        p.validate_all_vertices()
        c.validate_all_vertices()
        return p, c, ConservativeIndex(potential), ConservativeIndex(current)

    def test_full_vertex_audit_rejects_otherwise_unseen_bad_coordinate(self):
        # A local target query cannot discover an invalid far-away vertex.
        s = sheet([[0, 0], [1, 0], [0, 1], [500, 500], [501, 500], [500, 501]],
                  [[0, 1, 2], [3, 4, 5]])
        s.metric_xy[3, 0] += np.longdouble('1e-10')
        chart = CanonicalChart(s, [])
        chart.cell(0)  # Lazy local validation alone would succeed.
        index = ConservativeIndex(s)
        self.assertNotIn(1, index.query_box(index.boxes[0]))
        with self.assertRaisesRegex(ValueError, 'eta'):
            chart.validate_all_vertices()

    def test_ranking_is_deterministic_and_included_cells_never_selected(self):
        p, _, _, _ = self.charts()
        values = np.asarray([[0, 0], [2, 4], [0, 0], [2, 4]], dtype=float)
        errors = np.zeros_like(values)
        selected, upper = rank_excluded(p, values, errors, np.array([False, False]), 1, 1, 10)
        self.assertEqual([r['id'] for r in selected], [0])
        self.assertEqual(upper, [4, 16])
        selected, _ = rank_excluded(p, values, errors, np.array([True, False]), 1, 1, 10)
        self.assertEqual([r['id'] for r in selected], [1])
        with self.assertRaisesRegex(ValueError, 'cap'):
            rank_excluded(p, values, errors, np.array([False, False]), 1, 1, 1)

    def test_integration_charges_errors_before_fraction_and_keeps_caps(self):
        p, c, pi, ci = self.charts()
        selected = [{'id': 0, 'full_cell_energy_interval_ohm': [[1., 3.], [4., 12.]]}]
        cap = Budget({'candidates': 100, 'clips': 100, 'overlap_checks': 100})
        rows, added = integrate_selected(selected, np.array([False, True]), p, c, pi, ci, cap)
        fraction = F(rows[0]['fraction_lower_exact'])
        self.assertLess(fraction, F(1, 2))  # Both eta erosion and area upper paid.
        self.assertLessEqual(F(added[0]), fraction)
        self.assertLessEqual(F(added[1]), 4*fraction)
        zero_cap = Budget({'candidates': 0, 'clips': 100, 'overlap_checks': 100})
        rows, added = integrate_selected(selected, np.array([False, True]), p, c, pi, ci, zero_cap)
        self.assertEqual(added, [0, 0])
        self.assertIn('UNPROCESSED', rows[0]['status'])

    def test_duplicate_and_already_counted_target_fail(self):
        p, c, pi, ci = self.charts()
        selected = [{'id': 0, 'full_cell_energy_interval_ohm': [[1, 2], [1, 2]]}]
        for rows, included in ((selected*2, [False, True]), (selected, [True, True])):
            with self.assertRaisesRegex(ValueError, 'already counted'):
                integrate_selected(rows, np.array(included), p, c, pi, ci, Budget({}))

    def test_overlap_is_rejected_without_added_lower(self):
        p, c, pi, ci = self.charts()
        p.sheet.triangles[1] = p.sheet.triangles[0]
        pi = ConservativeIndex(p.sheet)
        selected = [{'id': 0, 'full_cell_energy_interval_ohm': [[1, 2], [1, 2]]}]
        cap = Budget({'candidates': 100, 'clips': 100, 'overlap_checks': 100})
        rows, added = integrate_selected(selected, np.array([False, True]), p, c, pi, ci, cap)
        self.assertEqual(added, [0, 0])
        self.assertIn('REJECTED', rows[0]['status'])
        self.assertIn('potential overlap', rows[0]['reason'])

    def localization(self):
        row = {'id': 'foil:B.Cu', 'potential_energy_interval_ohm': [[0., 2.], [0., 2.]],
            'current_energy_interval_ohm': [[0., 2.], [0., 2.]], 'work_interval_ohm': [[0., 0.], [0., 0.]],
            'mismatch_interval_ohm': [[0., 4.], [0., 4.]]}
        return {'regions': [row], 'global_canonical_mismatch_upper_ohm': [4., 4.]}

    def test_refinement_changes_only_lower_and_preserves_old_receipt(self):
        old = self.localization()
        before = json.dumps(old, sort_keys=True)
        refined = refined_region(old, [1., .5])
        self.assertEqual(refined['potential_energy_interval_ohm'], [[1, 2], [.5, 2]])
        self.assertEqual(refined['current_energy_interval_ohm'], old['regions'][0]['current_energy_interval_ohm'])
        self.assertEqual(json.dumps(old, sort_keys=True), before)
        with self.assertRaisesRegex(ValueError, 'outer upper'):
            refined_region(old, [3., 0.])
        with self.assertRaisesRegex(ValueError, 'negative'):
            refined_region(old, [-1., 0.])

    def test_input_hash_and_source_copy_mutations_fail(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            root, own = Path(a), Path(b)
            (root/'proof').write_text('old')
            (own/'proof').write_text('old')
            mapping = {'proof': sha(root/'proof')}
            with patch('scripts.pcbgen.partial_cell_energy_run.REPO', own):
                verify_inputs(root, mapping, mapping)
                (own/'proof').write_text('changed')
                with self.assertRaisesRegex(ValueError, 'executed source epoch'):
                    verify_inputs(root, mapping, mapping)
                (root/'proof').write_text('changed')
                with self.assertRaisesRegex(ValueError, 'historical input hash'):
                    verify_inputs(root, mapping, {})
        with self.assertRaisesRegex(ValueError, 'conflicting'):
            merge_hashes({'x': 'old'}, {'x': 'new'})

    def test_artifact_root_and_fresh_output_cannot_escape(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            root, own = Path(a), Path(b)
            with self.assertRaises(ValueError):
                artifact_path(root, '../escape')
            with patch('scripts.pcbgen.partial_cell_energy_run.REPO', own):
                path = fresh_output(own/'.circuit-cache/new', root)
                path.mkdir(parents=True)
                with self.assertRaises(ValueError):
                    fresh_output(path, root)
                with self.assertRaises(ValueError):
                    fresh_output(root/'old-cache', root)

    def test_parsed_configuration_is_bound_to_the_same_read_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory)/'config.json'
            path.write_text('{"selected_limit":4096}')
            expected = sha(path)
            parsed, digest = snapshot_json(path, expected)
            self.assertEqual(parsed['selected_limit'], 4096)
            self.assertEqual(digest, expected)
            path.write_text('{"selected_limit":1}')
            self.assertNotEqual(sha(path), digest)  # Entry/exit recheck rejects change.
            with self.assertRaisesRegex(ValueError, 'parsed JSON bytes'):
                snapshot_json(path, expected)
            # Parsing cannot use A while hashing B: the helper reads once.
            with patch.object(Path, 'read_bytes', return_value=b'{"selected_limit":7}') as read:
                parsed, digest = snapshot_json(path)
                self.assertEqual(parsed['selected_limit'], 7)
                self.assertEqual(read.call_count, 1)
                import hashlib
                self.assertEqual(digest, hashlib.sha256(b'{"selected_limit":7}').hexdigest())

    def test_capture_field_path_hash_and_localization_identity_mutations(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = {'capture': 'run/capture.json', 'potential_fields': 'run/potential-fields.npz',
                      'input_sha256': {'run/capture.json': 'capture-hash', 'run/potential-fields.npz': 'field-hash'}}
            capture = {'artifact_sha256': {'potential-fields.npz': 'field-hash'}}
            localization = {'input_sha256': {'run/capture.json': 'capture-hash'}}
            require_capture_bindings(config, capture, localization, root)
            for mutation in ('path', 'field-hash', 'capture-path', 'capture-hash'):
                changed_config = json.loads(json.dumps(config))
                changed_localization = json.loads(json.dumps(localization))
                if mutation == 'path':
                    changed_config['potential_fields'] = 'other/potential-fields.npz'
                    changed_config['input_sha256']['other/potential-fields.npz'] = 'field-hash'
                elif mutation == 'field-hash':
                    changed_config['input_sha256']['run/potential-fields.npz'] = 'unrelated'
                elif mutation == 'capture-path':
                    changed_localization['input_sha256'] = {'other/capture.json': 'capture-hash'}
                else:
                    changed_localization['input_sha256']['run/capture.json'] = 'unrelated'
                with self.assertRaisesRegex(ValueError, 'capture'):
                    require_capture_bindings(changed_config, capture, changed_localization, root)

    def test_census_cap_records_whole_target_without_truncating_candidates(self):
        _, _, pi, ci = self.charts()
        rows, count = candidate_census([{'id': 0}, {'id': 1}], pi, ci, 0)
        self.assertEqual(len(rows), 1)
        self.assertGreater(rows[0]['current_candidates']+rows[0]['potential_neighbors'], 0)
        self.assertFalse(rows[0]['within_census_cap'])
        self.assertEqual(count, 0)

    def test_failed_premise_is_preserved_without_an_energy_result(self):
        with tempfile.TemporaryDirectory() as a, tempfile.TemporaryDirectory() as b:
            root, own = Path(a), Path(b)
            with patch('scripts.pcbgen.partial_cell_energy_run.REPO', own):
                output = own/'.circuit-cache/rejected'
                record = record_failure(output, root, ValueError('canonical eta'), 'core', 'runner')
                self.assertIn('FAILED', record['status'])
                self.assertNotIn('added_potential_energy_lower_ohm', record)
                self.assertEqual(json.loads((output/'failure.json').read_text()), record)
                with self.assertRaises(ValueError):
                    record_failure(output, root, ValueError('new'), 'core', 'runner')

    def test_small_receipt_binds_source_and_outward_summary_without_cache(self):
        # This verifies only the committed summary and code identity. It does
        # not relabel absent ignored native/field artifacts as revalidated.
        root = Path(__file__).resolve().parents[2]
        receipt = json.loads((root/'design/partition/partial-cell-energy-receipt.json').read_text())
        for name, digest in receipt['diagnostic_sha256'].items():
            self.assertEqual(sha(root/name), digest)
        self.assertEqual(receipt['accepted_cells']+receipt['rejected_or_capped_cells'], receipt['selected_cells'])
        for kind, used in receipt['work_used'].items():
            self.assertLessEqual(used, receipt['work_caps'][kind])
        for k in range(2):
            added = F(receipt['added_potential_energy_lower_ohm'][k])
            old = receipt['old_potential_energy_interval_ohm'][k]
            new = receipt['refined_potential_energy_interval_ohm'][k]
            self.assertLessEqual(F(new[0]), F(old[0])+added)
            self.assertEqual(new[1], old[1])
            self.assertGreaterEqual(F(receipt['uncovered_or_unprocessed_energy_upper_ohm'][k]),
                F(receipt['unchanged_excluded_full_cell_upper_ohm'][k])-added)
            mismatch = receipt['refined_mismatch_interval_ohm'][k]
            self.assertLessEqual(mismatch[0], mismatch[1])
            self.assertLessEqual(mismatch[1], receipt['unchanged_global_canonical_mismatch_upper_ohm'][k])
        self.assertIn('NOT RUN', receipt['retained_revalidation_when_artifacts_absent'])


if __name__ == '__main__':
    unittest.main()
