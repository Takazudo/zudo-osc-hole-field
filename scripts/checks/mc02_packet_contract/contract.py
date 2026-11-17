#!/usr/bin/env python3
"""Offline MC02 source reconciliation, never a gate or model validation."""
import argparse
import ast
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
GATE = 'design/stack/geometry/links/link-gate.json'
THREADING = 'design/stack/fixings/threading-procedure.json'
ELECTRICAL = 'design/stack/link-electrical/link-ratios.json'
INPUTS = 'design/stack/link-electrical/inputs.json'
KERNEL = 'scripts/stack/link_electrical/link_ratios.py'


def require(condition, message):
    if not condition:
        raise ValueError(message)


def git(root, *args):
    return subprocess.check_output(['git', '-C', str(root), *args], stderr=subprocess.PIPE)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def projection_function(kernel):
    """Reuse only the two hash-projection definitions from verified source bytes.

    No numerical imports, coupling solver, native command or generation runs.
    """
    tree = ast.parse(kernel)
    selected = [n for n in tree.body if isinstance(n, ast.FunctionDef)
                and n.name in ('projection', 'projection_sha256')]
    require(len(selected) == 2, 'projection definitions missing')
    namespace = {'hashlib': hashlib, 'json': json}
    exec(compile(ast.Module(body=selected, type_ignores=[]), KERNEL, 'exec'), namespace)
    return namespace['projection_sha256']


def reconcile(manifest, historical_revision, historical, candidate, projection):
    require(historical_revision == manifest['historical_revision'], 'wrong historical revision')
    cases = {}
    for label, data in (('historical', historical), ('candidate', candidate)):
        gate, threading, electrical = (data[p] for p in (GATE, THREADING, ELECTRICAL))
        unplaced = sorted([[r['board'], r['ref']] for r in gate['replacement']['footprints']
                           if r['step'] == 'no position'])
        latches = sorted(r['link'] for r in threading['latch']['not_shown'])
        require(unplaced == manifest['unplaced'], f'{label}: unplaced set changed')
        require(latches == manifest['latches'], f'{label}: latch set changed')
        links = [r for r in gate['links'] if not r.get('gone')]
        require(len({r['id'] for r in links}) == len(links) == 61, f'{label}: link identity changed')
        require(projection[label](links) == electrical['record_projection_sha256'] == data[INPUTS]['link_record']['projection_sha256'],
                f'{label}: consumed projection mismatch')
        by_id = {r['id']: r for r in electrical['links']}
        require(len(by_id) == len(electrical['links']) == 61, f'{label}: duplicate/missing electrical links')
        require(set(by_id) == {r['id'] for r in links}, f'{label}: electrical link set mismatch')
        nulls = {}
        for link in links:
            row = by_id[link['id']]
            classes = dict(Counter(p['class'] for p in link['positions'] if p['kind'] == 'signal'))
            require(classes == row['signals_by_class'], f'{label}: class mismatch')
            if row['ratio'] is None:
                require(row['pairs_evaluated'] == 0 and row['largest_pair'] is None
                        and not row['pairs_without_reference'], f'{label}: unexplained null')
                nulls[row['id']] = classes
            else:
                require(type(row['ratio']) in (int, float) and math.isfinite(row['ratio']),
                        f'{label}: invalid numeric ratio')
        require(nulls == manifest['intentional_nulls'], f'{label}: intentional null classification changed')
        currents = {r['branch']: r['worst_contact_A'] for r in electrical['ground_share']['branches']}
        require(len(currents) == len(electrical['ground_share']['branches']), f'{label}: duplicate current branch')
        require(currents == manifest['current_cases'][label], f'{label}: current-case conflation or drift')
        rated = [r['ratio'] for r in electrical['links'] if r['ratio'] is not None]
        summary = gate['summary']
        expected_allocation = (511, 322, 339) if label == 'historical' else (511, 340, 321)
        require(tuple(summary[k] for k in ('signals_on_links', 'grounds', 'unused_positions')) == expected_allocation,
                f'{label}: allocation changed')
        require(len(rated) == 56, f'{label}: numeric ratio count changed')
        require(sum(x > 1 for x in rated) == (5 if label == 'historical' else 0), f'{label}: exceedance changed')
        if label == 'candidate':
            require(max(rated) == 0.978101, 'candidate: stored maximum changed')
        cases[label] = {'source_revision': manifest[label + '_revision'],
                        'allocation': dict(zip(('signals', 'grounds', 'unused'), expected_allocation)),
                        'current_cases_A': currents, 'numeric_ratios': len(rated),
                        'intentional_nulls': nulls, 'maximum_stored_ratio': max(rated),
                        'projection_sha256': projection[label](links)}
    return {'schema_version': 1, 'scope': 'SOURCE RECONCILIATION ONLY; NOT INTEGRATED OR GATE APPROVAL',
            'model_recalculated': False, 'native_run': False, 'projection_recomputed': True,
            'cases': cases, 'unplaced': manifest['unplaced'], 'not_shown_latches': manifest['latches'],
            'formal_gate_status': 'NOT ASSESSED'}


def load(root):
    manifest = json.loads((HERE / 'manifest.json').read_text())
    packet = git(root, 'show', manifest['packet_revision'] + ':' + manifest['packet_path'])
    require(sha(packet) == manifest['packet_sha256'], 'packet drift')
    historical, candidate, matrix = {}, {}, []
    for path, expected in manifest['historical_blobs'].items():
        data = git(root, 'show', manifest['historical_revision'] + ':' + path)
        oid = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        require(oid == expected, f'historical source drift: {path}')
        if path in (GATE, THREADING, ELECTRICAL, INPUTS):
            historical[path] = json.loads(data)
        current = (root / path).read_bytes()
        matrix.append({'path': path, 'historical_blob': oid, 'bytes_changed': current != data})
    verified = {}
    for path, expected in manifest['candidate_pins'].items():
        verified[path] = (root / path).read_bytes()
        require(sha(verified[path]) == expected, f'candidate source drift: {path}')
        if path in (GATE, THREADING, ELECTRICAL, INPUTS):
            candidate[path] = json.loads(verified[path])
    historical_kernel = git(root, 'show', manifest['historical_revision'] + ':' + KERNEL)
    require(sha(historical_kernel) == manifest['historical_kernel_sha256'], 'historical kernel drift')
    projection = {'historical': projection_function(historical_kernel),
                  'candidate': projection_function(verified[KERNEL])}
    return manifest, historical, candidate, projection, matrix


def run(root):
    manifest, historical, candidate, projection, matrix = load(root)
    report = reconcile(manifest, manifest['historical_revision'], historical, candidate, projection)
    report['historical_blob_comparison'] = matrix
    report['candidate_source_sha256'] = manifest['candidate_pins']
    report['packet_revision'] = manifest['packet_revision']
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=ROOT)
    args = parser.parse_args()
    try:
        print(json.dumps(run(args.root), indent=2))
    except (OSError, ValueError, KeyError, TypeError, IndexError, subprocess.CalledProcessError) as exc:
        parser.exit(1, f'MC02 packet contract refused: {exc}\n')


if __name__ == '__main__':
    main()
