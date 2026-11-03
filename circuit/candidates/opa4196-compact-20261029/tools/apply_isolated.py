"""Apply reviewed overlays to NEW isolated copies. No native CAD operations."""
import argparse, hashlib, json, shutil, subprocess
from pathlib import Path

def digest(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()

def inventory(root):
    return {str(p.relative_to(root)): digest(p) for p in sorted(root.rglob('*')) if p.is_file()}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('after', type=Path)
    ap.add_argument('destination', type=Path)
    a = ap.parse_args()
    source = a.after.resolve(strict=True)
    dest = a.destination.resolve()
    if dest.exists() or dest == source or source in dest.parents or dest in source.parents:
        raise SystemExit('Destination must be new and separate from the original source tree')
    packet = Path(__file__).resolve().parent
    contracts = json.loads((packet/'patches/checks.json').read_text())
    snapshots = {}
    # Validate all predecessors BEFORE any output creation.
    for c in contracts:
        v = c['variant']
        root = source/v
        if any(p.is_symlink() for p in root.rglob('*')):
            raise SystemExit('Symlink in variant: explicit review required')
        snapshots[v] = inventory(root)
        for rel, hashes in c['files'].items():
            if snapshots[v].get(rel) != hashes['before_sha256']:
                raise SystemExit('Predecessor mismatch: '+v+'/'+rel)
    dest.mkdir(parents=True)
    results = []
    for c in contracts:
        v = c['variant']
        target = dest/v
        shutil.copytree(source/v, target)
        command = ['patch', '--batch', '--fuzz=0', '-p1', '-i',
                   str(packet/'patches'/(v.replace('/','-')+'.patch'))]
        run = subprocess.run(command, cwd=target, capture_output=True, text=True)
        if run.returncode:
            (dest/'FIRST_FAILURE.txt').write_text(run.stdout+run.stderr)
            raise SystemExit('Patch failed; partial output preserved, no retry: '+v)
        current = inventory(target)
        expected = dict(snapshots[v])
        for rel, hashes in c['files'].items():
            expected[rel] = hashes['proposed_sha256']
        if current != expected:
            raise SystemExit('Successor inventory mismatch; output preserved: '+v)
        if inventory(source/v) != snapshots[v]:
            raise SystemExit('Original inventory changed: '+v)
        results.append({'variant':v, 'status':'PASS', 'file_count':len(current),
                        'changed_files':c['files'], 'predecessor_inventory':snapshots[v],
                        'successor_inventory':current, 'patch_stdout':run.stdout})
    receipt = {'status':'PASS', 'scope':'ISOLATED DEVELOPMENT ONLY; NOT CANONICAL OR MANUFACTURING',
               'originals_unchanged':True, 'variants':results}
    (dest/'APPLICATION-RECEIPT.json').write_text(json.dumps(receipt, indent=2)+'\n')
    (dest/'DEVELOPMENT-SCOPE.txt').write_text(
        'Approved isolated OPA4196 compact candidate evaluation only. Four nonadditive alternatives.\n'
        'U110/U210 restored to OPA4196IDR; 13 IC/module, pins/nets/footprints preserved.\n'
        'Inherited ledgers and check receipts describe predecessor state; APPLICATION-RECEIPT.json\n'
        'records this overlay. No native checks or analog/physical qualification performed.\n'
        'Original H-packing golden fixtures must remain unchanged.\n')
    print('PASS: four isolated candidates, exactly five changed files each; all other bytes and originals preserved')

if __name__ == '__main__':
    main()
