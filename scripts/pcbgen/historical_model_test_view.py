"""Explicit read-only archived source-byte view for historical gate TESTS.

This is never imported by a solver or native authority gate. It does not make
old receipts valid for the current source epoch. Non-source artifacts remain
actual retained files, with every original digest checked by the real gate.
"""
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[2]


@contextmanager
def archived_source_bytes(scope):
    reader=Path.read_bytes
    manifest=ROOT/'design/partition/model-history/pre-two-layer/manifest.json'
    rows=json.loads(reader(manifest))['entries'];view={}
    for row in rows:
        if row['scope']!=scope:continue
        original=(ROOT/row['original_path']).resolve()
        retained=(ROOT/row['retained_path']).resolve()
        if not original.is_relative_to(ROOT/'scripts') or not retained.is_relative_to(manifest.parent):
            raise ValueError('historical test view must contain only retained source scripts')
        data=reader(retained)
        if hashlib.sha256(data).hexdigest()!=row['sha256']:
            raise ValueError('retained historical test source changed')
        if original in view and view[original]!=data:raise ValueError('historical source scope is ambiguous')
        view[original]=data
    if not view:raise ValueError('historical source test scope is absent')
    def read(path):
        data=view.get(path.resolve())
        return reader(path) if data is None else data
    with patch.object(Path,'read_bytes',read):yield
