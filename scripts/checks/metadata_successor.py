#!/usr/bin/env python3
"""Metadata-only successors of adopted OSC PCB bytes.

An adopted board keeps its adoption evidence bound to the adopted bytes. A
successor may differ from those bytes only in footprint-level MPN, Manufacturer
and LCSC property values; every other byte (copper, placement, outlines, zones,
text, the property blocks' own geometry) must be identical. A reviewed receipt
lists each changed (footprint UUID, reference, property, old, new). Verification
re-reads the adopted bytes from Git, re-derives the complete difference and
requires it to equal the listed changes exactly, and requires the successor hash
to equal the working file. This binds identity metadata only; it runs no KiCad,
proves no routing quality and qualifies no hardware.

  python3 scripts/checks/metadata_successor.py check
  python3 scripts/checks/metadata_successor.py write BOARD --commit REV --label L --successor-label S
      --evidence PATH... --netlist PATH --packet NAME --output RECEIPT
"""
from __future__ import annotations
import argparse
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DIRECTORY = 'circuit/reviews/metadata-successors'
SCHEMA = 'osc-metadata-successor-1'
PROPERTIES = ('MPN', 'Manufacturer', 'LCSC')
PROPERTY_LINE = re.compile(r'^\t\t\(property "(MPN|Manufacturer|LCSC)" "((?:[^"\\]|\\.)*)"$')
FOOTPRINT_UUID = re.compile(r'^\t\t\(uuid "([0-9a-f-]+)"\)$')
REFERENCE = re.compile(r'^\t\t\(property "Reference" "((?:[^"\\]|\\.)*)"$')
INVARIANT = ('Only the listed footprint-level MPN, Manufacturer and LCSC property values differ from the adopted '
             'bytes. Copper, placement, outlines, zones, every other property and all non-property lines are '
             'byte-identical; the changed properties stay hidden, so no rendered layer changes.')


class SuccessorError(ValueError):
    pass


def sha(data):
    return hashlib.sha256(data).hexdigest()


def git_blob(git_root, commit, path):
    """Adopted bytes from Git history, never from the working tree."""
    spec = f'{commit}:{path}'
    oid = subprocess.run(['git', 'rev-parse', '--verify', '--quiet', spec], cwd=git_root,
                         capture_output=True, text=True)
    if oid.returncode:
        raise SuccessorError(f'{path}: adopted bytes absent from Git at {commit}')
    data = subprocess.run(['git', 'cat-file', 'blob', oid.stdout.strip()], cwd=git_root,
                          capture_output=True, check=True).stdout
    return oid.stdout.strip(), data


def footprint_context(lines, index):
    """Reference and footprint UUID of the top-level footprint enclosing line `index`."""
    start = index
    while start >= 0 and not lines[start].startswith('\t('):
        start -= 1
    if start < 0 or not lines[start].startswith('\t(footprint '):
        raise SuccessorError(f'line {index + 1}: changed property is outside a footprint')
    reference = uuid = None
    for position in range(start + 1, len(lines)):
        line = lines[position]
        if line == '\t)':
            break
        if reference is None and (m := REFERENCE.match(line)):
            reference = m[1]
        elif uuid is None and (m := FOOTPRINT_UUID.match(line)):
            uuid = m[1]
    if not reference or not uuid:
        raise SuccessorError(f'line {index + 1}: footprint reference or UUID missing')
    return reference, uuid


def hidden(lines, index):
    for line in lines[index + 1:min(index + 8, len(lines))]:
        if line == '\t\t\t(hide yes)':
            return True
        if line.startswith('\t\t\t(effects') or line == '\t\t)':
            return False
    return False


def derive(old_bytes, new_bytes):
    """Every difference, which must be a footprint-level identity property value; anything else raises."""
    old = old_bytes.decode('latin-1').split('\n')
    new = new_bytes.decode('latin-1').split('\n')
    if len(old) != len(new):
        raise SuccessorError(f'line count differs ({len(old)} -> {len(new)}): not a metadata-only successor')
    changes = []
    for index, (a, b) in enumerate(zip(old, new)):
        if a == b:
            continue
        ma, mb = PROPERTY_LINE.match(a), PROPERTY_LINE.match(b)
        if not (ma and mb and ma[1] == mb[1]):
            raise SuccessorError(f'line {index + 1}: non-property difference: {a[:80]!r} -> {b[:80]!r}')
        reference, uuid = footprint_context(old, index)
        if footprint_context(new, index) != (reference, uuid):
            raise SuccessorError(f'line {index + 1}: footprint identity differs')
        if not (hidden(old, index) and hidden(new, index)):
            raise SuccessorError(f'line {index + 1}: changed property {ma[1]} of {reference} is not hidden')
        changes.append({'reference': reference, 'footprint_uuid': uuid, 'property': ma[1],
                        'old': ma[2].encode('latin-1').decode('utf-8'), 'new': mb[2].encode('latin-1').decode('utf-8')})
    keys = [(c['footprint_uuid'], c['property']) for c in changes]
    if len(set(keys)) != len(keys):
        raise SuccessorError('a footprint property changed more than once')
    return sorted(changes, key=lambda c: (c['reference'], c['footprint_uuid'], c['property']))


# Verification is a pure function of the receipt bytes, the working board bytes and Git, so a
# result is reused only for identical (git root, receipt digest, board digest) inputs.
_VERIFIED = {}


def _verified(git_root, root, receipt_digest, current_digest, receipt_path):
    key = (git_root, receipt_digest, current_digest)
    if key not in _VERIFIED:
        _VERIFIED[key] = _verify_uncached(git_root, root, receipt_digest, current_digest, receipt_path)
    return _VERIFIED[key]


def _verify_uncached(git_root, root, receipt_digest, current_digest, receipt_path):
    raw = (Path(root) / receipt_path).read_bytes()
    if sha(raw) != receipt_digest:
        raise SuccessorError(f'{receipt_path}: receipt changed during verification')
    receipt = json.loads(raw)
    if receipt.get('schema') != SCHEMA or receipt.get('allowed_properties') != list(PROPERTIES):
        raise SuccessorError(f'{receipt_path}: not an {SCHEMA} receipt for {list(PROPERTIES)}')
    board = receipt['board']
    if current_digest != receipt['successor']['sha256']:
        raise SuccessorError(f'{board}: working board bytes are not the receipt successor')
    adopted = receipt['adopted']
    oid, data = git_blob(git_root, adopted['git_commit'], board)
    if oid != adopted['git_blob'] or sha(data) != adopted['sha256']:
        raise SuccessorError(f'{board}: Git bytes at {adopted["git_commit"]} are not the adopted board')
    new_bytes = (Path(root) / board).read_bytes()
    if sha(new_bytes) != current_digest:
        raise SuccessorError(f'{board}: board changed during verification')
    derived = derive(data, new_bytes)
    listed = sorted(receipt['changes'], key=lambda c: (c['reference'], c['footprint_uuid'], c['property']))
    if derived != listed:
        missing = [c for c in derived if c not in listed][:3]
        extra = [c for c in listed if c not in derived][:3]
        raise SuccessorError(f'{board}: derived changes differ from the receipt; unlisted {missing} listed-only {extra}')
    if receipt.get('change_count') != len(derived) or receipt.get('invariant') != INVARIANT:
        raise SuccessorError(f'{board}: receipt count or invariant statement differs')
    return json.dumps(receipt)


def verify(receipt_path, root=ROOT, git_root=ROOT):
    """Return the receipt once the working board is proven a metadata-only successor of the adopted bytes."""
    root = Path(root)
    receipt_digest = sha((root / receipt_path).read_bytes())
    board = json.loads((root / receipt_path).read_bytes())['board']
    current = sha((root / board).read_bytes())
    return json.loads(_verified(str(git_root), str(root), receipt_digest, current, str(receipt_path)))


def receipts(root=ROOT):
    folder = Path(root) / DIRECTORY
    return sorted(str(p.relative_to(root)) for p in folder.glob('*.json')) if folder.is_dir() else []


def successor_for(board, current_sha256, root=ROOT, git_root=ROOT):
    """The verified receipt whose successor is these board bytes, or None. Two candidates are refused."""
    found = []
    for path in receipts(root):
        record = json.loads((Path(root) / path).read_bytes())
        if record.get('board') == board and record.get('successor', {}).get('sha256') == current_sha256:
            found.append(path)
    if len(found) > 1:
        raise SuccessorError(f'{board}: more than one metadata successor names these bytes')
    if not found:
        return None
    receipt = verify(found[0], root, git_root)
    return {**receipt, 'path': found[0], 'receipt_sha256': sha((Path(root) / found[0]).read_bytes())}


def write(args):
    board = args.board
    oid, data = git_blob(ROOT, args.commit, board)
    commit = subprocess.run(['git', 'rev-parse', args.commit + '^{commit}'], cwd=ROOT, capture_output=True,
                            text=True, check=True).stdout.strip()
    new_bytes = (ROOT / board).read_bytes()
    changes = derive(data, new_bytes)
    netlist = ROOT / args.netlist
    receipt = {
        'schema': SCHEMA, 'board': board, 'board_id': Path(board).stem,
        'status': 'METADATA-ONLY SUCCESSOR OF AN UNVALIDATED DRAFT; no routing, placement or qualification change',
        'adopted': {'label': args.label, 'sha256': sha(data), 'git_commit': commit, 'git_blob': oid,
                    'evidence': sorted(args.evidence)},
        'successor': {'label': args.successor_label, 'sha256': sha(new_bytes)},
        'source': {'packet': args.packet, 'netlist': args.netlist, 'netlist_sha256': sha(netlist.read_bytes()),
                   'method': args.method},
        'allowed_properties': list(PROPERTIES), 'invariant': INVARIANT,
        'change_count': len(changes),
        'changes_by_property': {p: sum(c['property'] == p for c in changes) for p in PROPERTIES},
        'changes': changes,
        'verification': 'python3 scripts/checks/metadata_successor.py check (re-reads the adopted Git blob)',
        'qualification': 'NOT RUN: electrical, thermal, physical; no fabrication outputs',
    }
    out = ROOT / args.output
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + '\n')
    verify(args.output)
    print(f'WROTE {args.output}: {len(changes)} property changes, {sha(data)[:12]} -> {sha(new_bytes)[:12]}')


def main():
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    sub = parser.add_subparsers(dest='command', required=True)
    sub.add_parser('check')
    w = sub.add_parser('write')
    w.add_argument('board')
    for name in ('--commit', '--label', '--successor-label', '--netlist', '--packet', '--output', '--method'):
        w.add_argument(name, required=True)
    w.add_argument('--evidence', nargs='+', required=True)
    args = parser.parse_args()
    if args.command == 'write':
        return write(args)
    for path in receipts():
        receipt = verify(path)
        print(f"PASS: {path}: {receipt['adopted']['label']} {receipt['adopted']['sha256'][:12]} -> "
              f"{receipt['successor']['label']} {receipt['successor']['sha256'][:12]}, "
              f"{receipt['change_count']} identity property values; qualification NOT RUN")


if __name__ == '__main__':
    main()
