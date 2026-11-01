#!/usr/bin/env python3
"""Offline consistency check of the UNADOPTED S2b TMUX7412F + TMUX6112 candidate record (decision E13).

Without --tree: the patch hash and every predecessor hash are checked against the
predecessor commit's Git objects. With --tree DIR: every successor hash is checked
against a rebuilt tree (see reproduce.sh). PASS here is file identity only; it is
not an electrical, layout, assembly or sourcing validation.
"""
import argparse, hashlib, json, subprocess, sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
REPO = HERE.parents[2]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--tree', type=Path)
    args = parser.parse_args()
    receipt = json.loads((HERE / 'receipts/application-receipt.json').read_text())
    errors = []
    if sha((HERE / 'patches/source.patch').read_bytes()) != receipt['source_patch_sha256']:
        errors.append('source.patch hash differs from receipt')
    predecessor = receipt['predecessor_commit']
    for path, row in receipt['files'].items():
        blob = subprocess.run(['git', '-C', str(REPO), 'show', f'{predecessor}:{path}'], capture_output=True)
        before = sha(blob.stdout) if blob.returncode == 0 else None
        if before != row['before_sha256']:
            errors.append(f'predecessor hash differs: {path}')
        if args.tree is not None:
            target = args.tree / path
            after = sha(target.read_bytes()) if target.exists() else None
            if after != row['after_sha256']:
                errors.append(f'successor hash differs: {path}')
    source = [p for p, r in receipt['files'].items() if r['kind'] == 'source']
    if len(source) != receipt['source_file_count'] or {p for p, r in receipt['files'].items() if r['kind'] == 'retained-source'} != set(receipt['retained_source_files']) or len(receipt['files']) != receipt['changed_file_count']:
        errors.append('file counts differ from receipt')
    for error in errors:
        print('FAIL:', error)
    if errors:
        return 1
    print('PASS: record consistency;', len(receipt['files']), 'files,', len(source), 'source',
          '; successor tree checked' if args.tree else '; successor tree NOT RUN (no --tree)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
