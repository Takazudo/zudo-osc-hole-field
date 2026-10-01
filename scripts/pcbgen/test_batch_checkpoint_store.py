"""Mutation tests for the local finite-profile checkpoint primitive."""

import copy
import hashlib
import io
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
from scipy.sparse import csc_matrix, csr_matrix

from scripts.pcbgen.batch_checkpoint_store import (
    Batch, BatchCheckpointStore, CheckpointError, digest_dense_operand,
    digest_run_material, digest_sparse_operand,
)


def fixture(start=0, stop=8, count=10, mode="current"):
    width = stop - start
    receipts = {
        "refinement": {"start": start, "stop": stop, "iterations": 1},
        "residual_work": {"start": start, "stop": stop,
                          "full_equation_residual_A": 2e-9},
    }
    if mode == "current":
        receipts.update({
            "physical_gate": {"start": start, "stop": stop,
                              "operator_residual_A": 2e-9,
                              "sheet_source_balance_A": 3e-9,
                              "barrel_balance_A": 4e-9,
                              "shared_face_continuity_A": 5e-9},
            "conservation_correction": {"total": 0.1},
        })
    return Batch(start, stop, np.ones((count, width), dtype=np.float64),
                 np.ones(width, dtype=np.float64),
                 np.ones(width, dtype=np.float64),
                 np.ones(width, dtype=np.float64) if mode == "current" else None,
                 receipts)


class BatchCheckpointStoreTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)
        self.key = digest_run_material({"native_sha256": "a" * 64,
                                        "operator_sha256": "b" * 64})
        self.store = BatchCheckpointStore(self.path, run_key=self.key,
                                          mode="current", profile_count=10)

    def test_contiguous_prefix_and_short_last_batch(self):
        self.store.save(fixture())
        self.store.save(fixture(8, 10))
        restored = self.store.load_prefix()
        self.assertEqual([(b.start, b.stop) for b in restored], [(0, 8), (8, 10)])
        np.testing.assert_array_equal(restored[0].energy, fixture().energy)
        self.assertEqual(restored[1].receipts, fixture(8, 10).receipts)
        with self.assertRaisesRegex(CheckpointError, "duplicate"):
            self.store.save(fixture())

    def test_changed_source_or_operand_key_rejected(self):
        self.store.save(fixture())
        for field in ("native_sha256", "operator_sha256"):
            material = {"native_sha256": "a" * 64, "operator_sha256": "b" * 64}
            material[field] = "c" * 64
            changed = BatchCheckpointStore(self.path, run_key=digest_run_material(material),
                                           mode="current", profile_count=10)
            with self.subTest(field=field), self.assertRaisesRegex(CheckpointError, "run_key"):
                changed.load_prefix()

    def test_mode_count_and_batch_size_rejected(self):
        self.store.save(fixture())
        for kwargs in ({"mode": "potential"}, {"profile_count": 11}, {"batch_size": 4}):
            config = {"run_key": self.key, "mode": "current", "profile_count": 10}
            config.update(kwargs)
            with self.subTest(kwargs=kwargs), self.assertRaises(CheckpointError):
                BatchCheckpointStore(self.path, **config).load_prefix()

    def test_payload_mutation_and_uncommitted_tail_recovered(self):
        self.store.save(fixture())
        payload = self.path / "batch-00000000-00000008.npz"
        original = payload.read_bytes()
        payload.write_bytes(original + b"damage")
        with self.assertRaisesRegex(CheckpointError, "payload hash"):
            self.store.load_prefix()
        payload.write_bytes(original)
        (self.path / "batch-00000000-00000008.json").unlink()
        self.assertEqual(self.store.load_prefix(), [])
        self.assertFalse(payload.exists())
        self.store.save(fixture())
        (self.path / "batch-00000000-00000008.npz").unlink()
        with self.assertRaisesRegex(CheckpointError, "incomplete"):
            self.store.load_prefix()

    def test_payload_only_tail_after_committed_prefix_recomputes(self):
        self.store.save(fixture())
        orphan = self.path / "batch-00000008-00000010.npz"
        orphan.write_bytes(b"uncommitted")
        self.assertEqual([(b.start, b.stop) for b in self.store.load_prefix()], [(0, 8)])
        self.assertFalse(orphan.exists())
        self.store.save(fixture(8, 10))
        self.assertEqual([(b.start, b.stop) for b in self.store.load_prefix()],
                         [(0, 8), (8, 10)])

    def test_manifest_mutation_rejected(self):
        self.store.save(fixture())
        manifest_path = self.path / "batch-00000000-00000008.json"
        raw = json.loads(manifest_path.read_text())
        for field, value in (("start", 1), ("payload_bytes", 1),
                             ("payload_sha256", "0" * 64)):
            mutated = dict(raw)
            mutated[field] = value
            manifest_path.write_text(json.dumps(mutated, sort_keys=True,
                                                separators=(",", ":")))
            with self.subTest(field=field), self.assertRaises(CheckpointError):
                self.store.load_prefix()
        manifest_path.write_text(json.dumps(raw, sort_keys=True, separators=(",", ":")))
        manifest_path.write_text('{"start":0,"start":0}')
        with self.assertRaisesRegex(CheckpointError, "duplicate JSON"):
            self.store.load_prefix()

    def test_rehashed_malformed_payload_still_rejected(self):
        self.store.save(fixture())
        payload_path = self.path / "batch-00000000-00000008.npz"
        manifest_path = self.path / "batch-00000000-00000008.json"
        original_payload = payload_path.read_bytes()
        original_manifest = json.loads(manifest_path.read_text())
        with np.load(io.BytesIO(original_payload), allow_pickle=False) as source:
            arrays = {key: source[key] for key in source.files}

        def replace(**changes):
            modified = dict(arrays)
            modified.update(changes)
            output = io.BytesIO()
            np.savez(output, **modified)
            raw = output.getvalue()
            manifest = dict(original_manifest)
            manifest["payload_bytes"] = len(raw)
            manifest["payload_sha256"] = hashlib.sha256(raw).hexdigest()
            payload_path.write_bytes(raw)
            manifest_path.write_text(json.dumps(manifest, sort_keys=True,
                                                separators=(",", ":")))

        mutations = (
            {"energy": arrays["energy"].astype(np.float32)},
            {"field_max": np.full(8, np.inf)},
            {"energy": np.zeros((10, 7))},
            {"receipts_json": np.frombuffer(b"{}", dtype=np.uint8)},
            {"receipts_json": np.asarray([None], dtype=object)},
        )
        for changes in mutations:
            replace(**changes)
            with self.subTest(changes=list(changes)), self.assertRaises(CheckpointError):
                self.store.load_prefix()

    def test_receipt_range_and_nonfinite_json_rejected(self):
        base = fixture()
        for defect in ("range", "nonfinite"):
            receipts = copy.deepcopy(base.receipts)
            if defect == "range":
                receipts["refinement"]["stop"] = 7
            else:
                receipts["conservation_correction"]["total"] = float("nan")
            invalid = Batch(0, 8, base.energy, base.field_max,
                            base.residual_work_one_norm, base.correction_energy,
                            receipts)
            with self.subTest(defect=defect), self.assertRaises(CheckpointError):
                self.store.save(invalid)

    def test_shape_dtype_finite_and_numerical_gate_rejected_before_write(self):
        base = fixture()
        cases = [
            Batch(0, 8, np.ones((9, 8)), base.field_max,
                  base.residual_work_one_norm, base.correction_energy, base.receipts),
            Batch(0, 8, np.ones((10, 8), dtype=np.float32), base.field_max,
                  base.residual_work_one_norm, base.correction_energy, base.receipts),
            Batch(0, 8, np.full((10, 8), np.nan), base.field_max,
                  base.residual_work_one_norm, base.correction_energy, base.receipts),
        ]
        bad_receipt = copy.deepcopy(base.receipts)
        bad_receipt["physical_gate"]["shared_face_continuity_A"] = 2e-8
        cases.append(Batch(0, 8, base.energy, base.field_max,
                           base.residual_work_one_norm, base.correction_energy,
                           bad_receipt))
        for case in cases:
            with self.subTest(case=case.energy.shape), self.assertRaises(CheckpointError):
                self.store.save(case)
        self.assertEqual(list(self.path.glob("batch-*")), [])

    def test_gap_overlap_and_duplicate_artifacts_rejected(self):
        with self.assertRaisesRegex(CheckpointError, "gapped"):
            self.store.save(fixture(8, 10))
        self.store.save(fixture())
        for extra in ("batch-00000008-00000009.json",
                      "batch-00000004-00000010.json"):
            (self.path / extra).write_text("{}")
            with self.subTest(extra=extra), self.assertRaises(CheckpointError):
                self.store.load_prefix()
            (self.path / extra).unlink()
        complete = BatchCheckpointStore(self.path / "complete", run_key=self.key,
                                        mode="current", profile_count=8)
        complete.save(fixture(count=8))
        with self.assertRaises(CheckpointError):
            complete.save(fixture(8, 8, count=8))

    def test_potential_gate_and_no_correction(self):
        store = BatchCheckpointStore(self.path, run_key=self.key,
                                     mode="potential", profile_count=10)
        bad = fixture(mode="potential")
        bad.receipts["residual_work"]["full_equation_residual_A"] = 2e-8
        with self.assertRaisesRegex(CheckpointError, "numerical gate"):
            store.save(bad)
        good = fixture(mode="potential")
        store.save(good)
        self.assertIsNone(store.load_prefix()[0].correction_energy)

    def test_operand_hashes_bind_values_shape_dtype_and_format(self):
        dense = np.asarray([[1., 0.], [0., 2.]])
        baseline = digest_dense_operand(dense)
        self.assertNotEqual(baseline, digest_dense_operand(dense.astype(np.float32)))
        self.assertNotEqual(baseline, digest_dense_operand(dense.reshape(4)))
        changed = dense.copy()
        changed[0, 0] = 3.
        self.assertNotEqual(baseline, digest_dense_operand(changed))
        csr = csr_matrix(dense)
        sparse_key = digest_sparse_operand(csr)
        self.assertNotEqual(sparse_key, digest_sparse_operand(csc_matrix(dense)))
        self.assertNotEqual(sparse_key, digest_sparse_operand(csr_matrix(changed)))
        with self.assertRaises(CheckpointError):
            digest_sparse_operand(csr_matrix(np.asarray([[np.inf]])))

    def test_run_material_rejects_nonstring_nested_keys(self):
        for material in ({1: "a"}, {"source": {1: "a"}},
                         {"sources": [{1: "a"}]}):
            with self.subTest(material=material), self.assertRaisesRegex(
                    CheckpointError, "keys must be strings"):
                digest_run_material(material)


if __name__ == "__main__":
    unittest.main()
