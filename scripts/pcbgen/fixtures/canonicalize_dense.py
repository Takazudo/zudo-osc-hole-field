#!/usr/bin/env python3
"""Sort only retained fixture copper slots; preserve owner objects and item bytes.

KiCad orders vias by transient in-memory net codes. Those codes can change after
reload even when every item is identical. Use retained UUID order for this fixture.
"""
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.pcbgen.uuid_tools import top_level_spans, UUID_RE


def canonicalize(path):
    source = ROOT/'scripts/pcbgen/fixtures/dense-evidence'
    owned = {t['uuid'] for name in ('copper', 'stitching')
             for t in json.loads((source/f'{name}.json').read_text())['items']}
    text = path.read_text()
    slots = {}
    for start, end in top_level_spans(text):
        block = text[start:end]
        kind = block.split()[0]
        match = UUID_RE.search(block)
        if kind in ('(segment', '(via') and match and match[1] in owned:
            slots.setdefault('copper', []).append((start, end, kind+match[1], block))
    edits = []
    for group in slots.values():
        ordered = sorted(group, key=lambda item: item[2])
        edits.extend((start, end, target[3])
                     for (start, end, _, _), target in zip(group, ordered))
    for start, end, block in sorted(edits, reverse=True):
        text = text[:start] + block + text[end:]
    if path.read_text() != text:
        path.write_text(text)


if __name__ == '__main__':
    canonicalize(Path(sys.argv[1]))
