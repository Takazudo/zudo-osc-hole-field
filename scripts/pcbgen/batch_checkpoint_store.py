"""Local, hash-bound storage for completed finite-profile matrix batches.

This module only stores and restores columns. The caller must construct and
verify the run key from frozen sources, native/prerequisite bytes, profiles,
parameters, library versions, and the assembled numerical operands. The caller
must recheck those inputs before each save and final publication, and must run
all full-matrix certificate gates after loading a prefix.
"""

from __future__ import annotations

import fcntl
import hashlib
import io
import json
import os
import re
import tempfile
import zipfile
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from scipy import sparse


SCHEMA_VERSION = 1
GATE_A = 1e-8
_HEX = re.compile(r"[0-9a-f]{64}\Z")
_NAME = re.compile(r"batch-(\d{8})-(\d{8})\.(npz|json)\Z")
_CURRENT_KEYS = ("operator_residual_A", "sheet_source_balance_A",
                 "barrel_balance_A", "shared_face_continuity_A")
_ARRAY_KEYS = ("energy", "field_max", "residual_work_one_norm", "correction_energy")


class CheckpointError(ValueError):
    """A batch is missing, stale, malformed, or numerically inadmissible."""


def _require_string_keys(value: object) -> None:
    if isinstance(value, dict):
        if any(not isinstance(key, str) for key in value):
            raise CheckpointError("JSON object keys must be strings")
        for item in value.values():
            _require_string_keys(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _require_string_keys(item)


def _json_bytes(value: object) -> bytes:
    _require_string_keys(value)
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"),
                          allow_nan=False).encode("utf-8")
    except (TypeError, ValueError) as exc:
        raise CheckpointError("receipt is not finite canonical JSON") from exc


def _object(raw: bytes) -> dict:
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise CheckpointError("duplicate JSON key")
            result[key] = value
        return result
    try:
        value = json.loads(raw, object_pairs_hook=pairs,
                           parse_constant=lambda value: (_ for _ in ()).throw(
                               CheckpointError(f"nonfinite JSON constant {value}")))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise CheckpointError("malformed JSON") from exc
    if not isinstance(value, dict) or _json_bytes(value) != raw:
        raise CheckpointError("noncanonical JSON object")
    return value


def digest_run_material(material: dict) -> str:
    """Digest a caller-complete, explicit run-material record.

    The caller owns the material recipe; this helper refuses an empty or
    noncanonical record but cannot infer omitted source or operand hashes.
    """
    if not isinstance(material, dict) or not material:
        raise CheckpointError("run material must be a nonempty object")
    return hashlib.sha256(_json_bytes(material)).hexdigest()


def digest_dense_operand(value: np.ndarray) -> str:
    """Hash the exact dtype, shape, and C-order bytes of a finite dense array."""
    if (not isinstance(value, np.ndarray) or value.dtype.kind not in "biufc"
            or not np.all(np.isfinite(value))):
        raise CheckpointError("dense operand must be a finite numeric ndarray")
    contiguous = np.ascontiguousarray(value)
    header = _json_bytes({"kind": "dense", "shape": list(value.shape),
                          "dtype": value.dtype.str})
    return hashlib.sha256(len(header).to_bytes(8, "big") + header +
                          contiguous.tobytes(order="C")).hexdigest()


def digest_sparse_operand(value: sparse.spmatrix) -> str:
    """Hash canonical CSR/CSC shape, dtypes, indptr, indices, and data."""
    if sparse.isspmatrix_csr(value):
        kind = "csr"
    elif sparse.isspmatrix_csc(value):
        kind = "csc"
    else:
        raise CheckpointError("sparse operand must be CSR or CSC")
    normalized = value.copy()
    normalized.sum_duplicates()
    normalized.sort_indices()
    if normalized.dtype.kind not in "biufc" or not np.all(np.isfinite(normalized.data)):
        raise CheckpointError("sparse operand must contain finite numeric data")
    header = _json_bytes({"kind": kind, "shape": list(normalized.shape),
                          "indptr_dtype": normalized.indptr.dtype.str,
                          "indices_dtype": normalized.indices.dtype.str,
                          "data_dtype": normalized.data.dtype.str})
    digest = hashlib.sha256(len(header).to_bytes(8, "big") + header)
    for part in (normalized.indptr, normalized.indices, normalized.data):
        raw = np.ascontiguousarray(part).tobytes(order="C")
        digest.update(len(raw).to_bytes(8, "big"))
        digest.update(raw)
    return digest.hexdigest()


def _number(value: object, label: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise CheckpointError(f"{label} must be a finite number")
    result = float(value)
    if not np.isfinite(result) or result < 0 or result > GATE_A:
        raise CheckpointError(f"{label} exceeds numerical gate")
    return result


def _receipts(mode: str, start: int, stop: int, receipts: object) -> dict:
    if not isinstance(receipts, dict):
        raise CheckpointError("receipts must be an object")
    required = {"refinement", "residual_work", "physical_gate",
                "conservation_correction"} if mode == "current" else {
                    "refinement", "residual_work"}
    if set(receipts) != required:
        raise CheckpointError("receipt field set mismatch")
    for name in ("refinement", "residual_work", "physical_gate"):
        if name not in receipts:
            continue
        row = receipts[name]
        if not isinstance(row, dict) or row.get("start") != start or row.get("stop") != stop:
            raise CheckpointError(f"{name} range mismatch")
    if mode == "current":
        if not isinstance(receipts["conservation_correction"], dict):
            raise CheckpointError("conservation correction must be an object")
        for key in _CURRENT_KEYS:
            _number(receipts["physical_gate"].get(key), key)
    else:
        _number(receipts["residual_work"].get("full_equation_residual_A"),
                "full_equation_residual_A")
    _json_bytes(receipts)
    return receipts


@dataclass(frozen=True)
class Batch:
    start: int
    stop: int
    energy: np.ndarray
    field_max: np.ndarray
    residual_work_one_norm: np.ndarray
    correction_energy: np.ndarray | None
    receipts: dict


class BatchCheckpointStore:
    """A strict contiguous-prefix store for one exact numerical run."""

    def __init__(self, directory: Path, *, run_key: str, mode: str,
                 profile_count: int, batch_size: int = 8):
        if not isinstance(run_key, str) or not _HEX.fullmatch(run_key):
            raise CheckpointError("run key must be a lowercase SHA-256 digest")
        if mode not in ("current", "potential"):
            raise CheckpointError("unsupported checkpoint mode")
        if type(profile_count) is not int or profile_count < 1:
            raise CheckpointError("profile count must be positive")
        if type(batch_size) is not int or batch_size < 1:
            raise CheckpointError("batch size must be positive")
        self.directory = Path(directory)
        self.run_key = run_key
        self.mode = mode
        self.profile_count = profile_count
        self.batch_size = batch_size

    @contextmanager
    def _locked(self):
        self.directory.mkdir(parents=True, exist_ok=True)
        with (self.directory / ".lock").open("a+b") as lock:
            fcntl.flock(lock, fcntl.LOCK_EX)
            try:
                yield
            finally:
                fcntl.flock(lock, fcntl.LOCK_UN)

    def _paths(self, start: int, stop: int) -> tuple[Path, Path]:
        stem = f"batch-{start:08d}-{stop:08d}"
        return self.directory / f"{stem}.npz", self.directory / f"{stem}.json"

    def _range(self, start: int, stop: int) -> None:
        if (type(start) is not int or type(stop) is not int or start < 0
                or start >= self.profile_count or stop <= start
                or stop > self.profile_count):
            raise CheckpointError("batch range outside profile count")
        if start % self.batch_size or stop != min(start + self.batch_size, self.profile_count):
            raise CheckpointError("batch range is not the next exact batch")

    def _arrays(self, batch: Batch) -> dict[str, np.ndarray]:
        self._range(batch.start, batch.stop)
        width = batch.stop - batch.start
        values = {"energy": batch.energy, "field_max": batch.field_max,
                  "residual_work_one_norm": batch.residual_work_one_norm}
        if self.mode == "current":
            values["correction_energy"] = batch.correction_energy
        elif batch.correction_energy is not None:
            raise CheckpointError("potential batch cannot have correction energy")
        for key, value in values.items():
            expected = (self.profile_count, width) if key == "energy" else (width,)
            if not isinstance(value, np.ndarray) or value.dtype != np.dtype("float64") or value.shape != expected:
                raise CheckpointError(f"{key} dtype or shape mismatch")
            if not np.all(np.isfinite(value)):
                raise CheckpointError(f"{key} contains nonfinite data")
        _receipts(self.mode, batch.start, batch.stop, batch.receipts)
        return values

    @staticmethod
    def _atomic(path: Path, payload: bytes) -> None:
        descriptor, name = tempfile.mkstemp(prefix=".batch-tmp-", dir=path.parent)
        try:
            with os.fdopen(descriptor, "wb") as stream:
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(name, path)
            directory_fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
            try:
                os.fsync(directory_fd)
            finally:
                os.close(directory_fd)
        finally:
            if os.path.exists(name):
                os.unlink(name)

    def _read_unlocked(self) -> list[Batch]:
        names = set()
        for path in self.directory.iterdir():
            if path.name == ".lock" or path.name.startswith(".batch-tmp-"):
                continue
            match = _NAME.fullmatch(path.name)
            if not match:
                raise CheckpointError(f"unexpected checkpoint entry: {path.name}")
            names.add((int(match[1]), int(match[2]), match[3]))
        pairs = {(start, stop) for start, stop, _ in names}
        prefix = []
        expected = 0
        ordered = sorted(pairs)
        for index, (start, stop) in enumerate(ordered):
            self._range(start, stop)
            if start != expected:
                raise CheckpointError("checkpoint prefix has a gap or overlap")
            has_payload = (start, stop, "npz") in names
            has_manifest = (start, stop, "json") in names
            if has_payload and not has_manifest and index == len(ordered) - 1:
                # The manifest is the commit marker. A crash after the atomic
                # payload rename may leave one uncommitted tail; discard only
                # that exact next batch and recompute it on restart.
                self._paths(start, stop)[0].unlink()
                directory_fd = os.open(self.directory, os.O_RDONLY | os.O_DIRECTORY)
                try:
                    os.fsync(directory_fd)
                finally:
                    os.close(directory_fd)
                break
            if not has_payload or not has_manifest:
                raise CheckpointError("incomplete checkpoint pair")
            prefix.append(self._read_pair(start, stop))
            expected = stop
        return prefix

    def _read_pair(self, start: int, stop: int) -> Batch:
        payload_path, manifest_path = self._paths(start, stop)
        manifest = _object(manifest_path.read_bytes())
        expected = {"schema_version": SCHEMA_VERSION, "run_key": self.run_key,
                    "mode": self.mode, "profile_count": self.profile_count,
                    "batch_size": self.batch_size, "start": start, "stop": stop}
        for key, value in expected.items():
            if type(manifest.get(key)) is not type(value) or manifest[key] != value:
                raise CheckpointError(f"checkpoint {key} mismatch")
        if set(manifest) != set(expected) | {"payload_bytes", "payload_sha256"}:
            raise CheckpointError("manifest field set mismatch")
        if type(manifest["payload_bytes"]) is not int or manifest["payload_bytes"] < 1:
            raise CheckpointError("invalid payload length")
        if not isinstance(manifest["payload_sha256"], str) or not _HEX.fullmatch(manifest["payload_sha256"]):
            raise CheckpointError("invalid payload digest")
        payload = payload_path.read_bytes()
        if len(payload) != manifest["payload_bytes"] or hashlib.sha256(payload).hexdigest() != manifest["payload_sha256"]:
            raise CheckpointError("payload hash or length mismatch")
        try:
            with zipfile.ZipFile(io.BytesIO(payload)) as archive:
                names = archive.namelist()
                keys = {"energy", "field_max", "residual_work_one_norm", "receipts_json"}
                if self.mode == "current":
                    keys.add("correction_energy")
                if len(names) != len(keys) or set(names) != {f"{key}.npy" for key in keys}:
                    raise CheckpointError("payload member set mismatch")
            with np.load(io.BytesIO(payload), allow_pickle=False) as loaded:
                raw = loaded["receipts_json"]
                if raw.dtype != np.dtype("uint8") or raw.ndim != 1:
                    raise CheckpointError("receipt bytes dtype or shape mismatch")
                receipts = _object(raw.tobytes())
                batch = Batch(start, stop, loaded["energy"], loaded["field_max"],
                              loaded["residual_work_one_norm"],
                              loaded["correction_energy"] if self.mode == "current" else None,
                              receipts)
        except (OSError, ValueError, zipfile.BadZipFile) as exc:
            if isinstance(exc, CheckpointError):
                raise
            raise CheckpointError("invalid non-pickle batch payload") from exc
        self._arrays(batch)
        return batch

    def load_prefix(self) -> list[Batch]:
        """Read only a fully verified contiguous prefix; fail closed otherwise."""
        with self._locked():
            return self._read_unlocked()

    def save(self, batch: Batch) -> None:
        """Commit one gated batch, payload first and manifest last."""
        arrays = self._arrays(batch)
        with self._locked():
            prefix = self._read_unlocked()
            expected = prefix[-1].stop if prefix else 0
            if batch.start != expected:
                raise CheckpointError("duplicate, overlapping, or gapped checkpoint")
            payload_path, manifest_path = self._paths(batch.start, batch.stop)
            output = io.BytesIO()
            np.savez(output, **arrays,
                     receipts_json=np.frombuffer(_json_bytes(batch.receipts), dtype=np.uint8))
            payload = output.getvalue()
            manifest = {"schema_version": SCHEMA_VERSION, "run_key": self.run_key,
                        "mode": self.mode, "profile_count": self.profile_count,
                        "batch_size": self.batch_size, "start": batch.start,
                        "stop": batch.stop, "payload_bytes": len(payload),
                        "payload_sha256": hashlib.sha256(payload).hexdigest()}
            self._atomic(payload_path, payload)
            self._atomic(manifest_path, _json_bytes(manifest))
