"""Bounded historical/review verification; no historical suite or native process."""
from pathlib import Path
import hashlib
import json
import sys
ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))
from scripts.checks.architecture_history import CHECKPOINTS, verify_binding


def main():
    for commit, modules in CHECKPOINTS.items():
        verify_binding(ROOT, commit, modules)
    count = 0
    for path in sorted((ROOT / 'design/architecture-278/implementation').glob('stage4[1-4]/**/review-bindings.json')):
        data = json.loads(path.read_text())
        hashes = data.get('sha256', data)
        for name, expected in hashes.items():
            if hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != expected:
                raise ValueError('historical review binding: ' + name)
        count += 1
    if count != 4:
        raise ValueError('missing reviewed stage')
    print(f'PASS: {len(CHECKPOINTS)} checkpoint bindings; {count} Stage41–44 review manifests')


if __name__ == '__main__': main()
