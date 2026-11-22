#!/usr/bin/env python3
"""MC04-S7 Revision 10: the retained link-cluster baseline of the link gate.

Writes design/stack/geometry/links/link-cluster-baseline.json from the link gate record of the source commit: for each
joint and front board, every top-level cluster's ID and member pairs (a split link's records, such as P-K-P-L01.01.01,
belong to their top-level cluster P-K-P-L01). links_gate.stable_clusters keeps these clusters; only pairs that no
baseline cluster holds are clustered. The record is retained, not recomputed; --check verifies it against the commit."""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'design/stack/geometry/links/link-cluster-baseline.json'
SOURCE_COMMIT = '93197a3e'  # the last link gate generated before the stage 7 move (MC04-S7 Revision 2)
SOURCE = 'design/stack/geometry/links/link-gate.json'
TOP = re.compile(r'^(.*-L\d+)(\..*)?$')


def build():
    raw = subprocess.run(['git', '-C', str(ROOT), 'show', f'{SOURCE_COMMIT}:{SOURCE}'], capture_output=True, check=True).stdout
    doc = json.loads(raw)
    clusters = {}
    for link in doc['links']:
        if link['joint'] == 'O-K':
            continue
        m = TOP.match(link['id'])
        if not m:
            raise ValueError('unexpected link id ' + link['id'])
        top = m.group(1)
        c = clusters.setdefault(top, {'id': top, 'joint': link['joint'], 'front_board': link['front_board'], 'members': set()})
        if (c['joint'], c['front_board']) != (link['joint'], link['front_board']):
            raise ValueError('cluster spans joints: ' + top)
        c['members'] |= set(link['members'])
    rows = [dict(c, members=sorted(c['members'])) for _, c in sorted(clusters.items())]
    return {'schema_version': 1,
            'status': 'RETAINED SOURCE INPUT (MC04-S7 Revision 10): link clusters before the stage 7 move',
            'source': {'commit': SOURCE_COMMIT, 'path': SOURCE, 'sha256': hashlib.sha256(raw).hexdigest()},
            'generator': 'scripts/stack/geometry/link_cluster_baseline.py', 'clusters': rows}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    text = json.dumps(build(), indent=1) + '\n'
    if a.check:
        if not OUT.exists() or OUT.read_text() != text:
            raise SystemExit('link cluster baseline drift')
    else:
        OUT.write_text(text)
    print('link cluster baseline', len(json.loads(text)['clusters']), 'clusters')


if __name__ == '__main__':
    main()
