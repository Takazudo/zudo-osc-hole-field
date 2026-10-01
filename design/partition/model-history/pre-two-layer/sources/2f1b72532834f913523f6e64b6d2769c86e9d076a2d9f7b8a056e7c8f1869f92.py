"""Verify copied KiCad companions against retained source digests.

The expected mapping is immutable authority supplied by the caller. Current
destination bytes are never substituted as a new expected value.
"""
import hashlib
from pathlib import Path


def verify(expected):
    if len(expected) != 3 or {Path(name).suffix for name in expected} != {'.kicad_pro', '.kicad_sch', '.kicad_dru'}:
        raise ValueError('Exact project, schematic and rule companion bindings required')
    if len({str(Path(name).with_suffix('')) for name in expected}) != 1:
        raise ValueError('Copied companions must belong to the same candidate stem')
    for name, retained_digest in expected.items():
        if hashlib.sha256(Path(name).read_bytes()).hexdigest() != retained_digest:
            raise ValueError('Candidate companion changed from retained source authority: '+name)
