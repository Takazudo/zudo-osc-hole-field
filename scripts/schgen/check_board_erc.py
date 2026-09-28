#!/usr/bin/env python3
"""Native ERC receipt for every active manifest board; warnings remain visible."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.checks.partition35_json import dumps


def inspect(board):
    identity = board['id']
    directory = ROOT/'boards'/identity
    target = ROOT/'.circuit-cache/board-erc'/f'{identity}.json'
    target.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(['bash', 'scripts/kicad/run.sh', 'kicad-cli', 'sch', 'erc',
                    '--format', 'json', '--severity-all', '-o', str(target.relative_to(ROOT)),
                    f'boards/{identity}/{identity}.kicad_sch'], cwd=ROOT, check=True,
                   stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    native = json.loads(target.read_text())
    violations = [item for sheet in native['sheets'] for item in sheet['violations']]
    warnings = sorted(({'type': v['type'], 'description': v['description'],
                        'items': sorted(i['description'] for i in v.get('items', []))}
                       for v in violations if v['severity'] == 'warning'), key=dumps)
    errors = [v for v in violations if v['severity'] == 'error']
    digest = hashlib.sha256()
    for path in sorted(directory.rglob('*.kicad_sch')):
        digest.update(str(path.relative_to(directory)).encode())
        digest.update(path.read_bytes())
    return {'board_id': identity, 'kicad_version': native['kicad_version'],
            'schematic_tree_sha256': digest.hexdigest(), 'errors': errors,
            'warning_count': len(warnings),
            'warning_types': dict(sorted(Counter(w['type'] for w in warnings).items())),
            'warnings': warnings}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    manifest = json.loads((ROOT/'design/partition/partition.json').read_text())
    with ThreadPoolExecutor(max_workers=2) as pool:
        rows = list(pool.map(inspect, manifest['boards']))
    errors = sum(len(r['errors']) for r in rows)
    baseline=json.loads((ROOT/'design/reports/master-erc-warning-baseline.json').read_text())
    identity=lambda w:json.dumps({k:w[k] for k in ('type','description','items')},sort_keys=True)
    actual=Counter(identity(w) for r in rows for w in r['warnings'] if w['type']=='pin_to_pin')
    expected=Counter(identity(w) for w in baseline['warnings'])
    if actual!=expected:raise SystemExit('projected pin-to-pin warnings differ from master baseline identities')

    report = {'schema_version': 1, 'status': 'FAIL' if errors else 'PASS - native ERC errors zero; warnings retained; unvalidated drafts',
              'oracle': 'Pinned KiCad 10.0.6 via scripts/kicad/run.sh', 'boards': rows,
              'pin_to_pin_master_identity_parity':'PASS;228 original warning identities preserved, sheet paths projected',
              'errors': errors, 'warnings': sum(r['warning_count'] for r in rows),
              'scope': 'Active manifest schematics only. No routed PCB or physical qualification.'}
    target = ROOT/'design/reports/board-erc.json'
    text = dumps(report)+'\n'
    if args.check:
        if not target.exists() or target.read_text() != text:
            raise SystemExit('native board ERC receipt drift')
    else:
        target.write_text(text)
    print(f"Native board ERC: {len(rows)} boards, {errors} errors, {report['warnings']} retained warnings")
    if errors:
        raise SystemExit('native board ERC errors')


if __name__ == '__main__':
    main()
