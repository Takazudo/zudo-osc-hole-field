#!/usr/bin/env python3
"""MC04-S7 Revision 9: the retained GH header baseline of commit 6093081c.

Writes design/partition/gh-baseline-6093081c.json from the connector packing and the partition at the source commit:
for each harness its id, pair, index, contact count and signal slots (the net on each signal position, null where the
position was unwired), each header end's site, and every header's reference designator. The packer keeps these
headers stable (scripts/checks/connector_packing35.py). The record is retained, not recomputed from the current
netlist; --check verifies it against the source commit."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'design/partition/gh-baseline-6093081c.json'
SOURCE_COMMIT = '6093081c'
SOURCES = ('design/partition/connector-packing-candidate.json', 'design/partition/partition.json')


def git_bytes(path):
    return subprocess.run(['git', '-C', str(ROOT), 'show', f'{SOURCE_COMMIT}:{path}'], capture_output=True, check=True).stdout


def build():
    raw = {p: git_bytes(p) for p in SOURCES}
    pack = json.loads(raw[SOURCES[0]])
    part = json.loads(raw[SOURCES[1]])
    heads = {h['id']: h for h in pack['headers']}
    harnesses = []
    for h in pack['harnesses']:
        if 'EL' in h['boards']:
            continue  # the stage-optical ports are fixed by stage-optical-input.json, not chunked
        first = heads[h['header_ids'][0]]
        n = first['contacts']
        pins = [first['pin_map'][str(i + 1)] for i in range(n)]
        count = (n + 1) // 2
        slots = [None if pins[2 * i] in ('NC', 'AGND') else pins[2 * i] for i in range(count) if 2 * i < n]
        harnesses.append({'id': h['id'], 'boards': h['boards'], 'index': int(h['id'].rsplit('-', 1)[1]),
                          'contacts': n, 'signal_slots': slots,
                          'sites': {heads[i]['board']: heads[i]['center_mm'] for i in h['header_ids']}})
    refdes = {c['id']: c['pcb_reference'] for c in part['connectors']}
    return {'schema_version': 1,
            'status': 'RETAINED SOURCE INPUT (MC04-S7 Revision 9): GH header baseline before the stage 7 move',
            'source': {'commit': SOURCE_COMMIT,
                       'sha256': {p: hashlib.sha256(b).hexdigest() for p, b in raw.items()}},
            'generator': 'scripts/partition/gh_baseline.py',
            'harnesses': harnesses, 'header_refdes': dict(sorted(refdes.items()))}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    text = json.dumps(build(), indent=1) + '\n'
    if a.check:
        if not OUT.exists() or OUT.read_text() != text:
            raise SystemExit('GH baseline drift')
    else:
        OUT.write_text(text)
    d = json.loads(text)
    print('GH baseline', len(d['harnesses']), 'harnesses', len(d['header_refdes']), 'headers')


if __name__ == '__main__':
    main()
