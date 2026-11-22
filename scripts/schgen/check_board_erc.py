#!/usr/bin/env python3
"""Native ERC receipt for every active manifest board; warnings remain visible."""
import argparse
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import hashlib
import json
import re
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.checks.partition35_json import dumps
from scripts.pcbgen.netlist import TOKEN, parse, many


def schematic_tree_digest(root):
    """Hash only the active root and referenced sheets, not local experiments."""
    root = Path(root).resolve()
    directory = root.parent
    visited, active = set(), set()

    def visit(path):
        path = path.resolve()
        if not path.is_relative_to(directory):
            raise ValueError('schematic sheet escapes board directory')
        if path in active:
            raise ValueError('cyclic schematic hierarchy')
        if path in visited:
            return
        active.add(path)
        tokens = TOKEN.findall(path.read_text())
        node, end = parse(tokens)
        if end != len(tokens) or node[0] != 'kicad_sch':
            raise ValueError('malformed schematic sheet')
        for sheet in many(node, 'sheet'):
            files = [p[2] for p in many(sheet, 'property') if p[1] == 'Sheetfile']
            if len(files) != 1:
                raise ValueError('schematic child requires one Sheetfile')
            visit(path.parent / files[0])
        active.remove(path)
        visited.add(path)

    visit(root)
    digest = hashlib.sha256()
    for path in sorted(visited):
        digest.update(str(path.relative_to(directory)).encode())
        digest.update(path.read_bytes())
    return digest.hexdigest()


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
    tree_hash = schematic_tree_digest(directory/f'{identity}.kicad_sch')
    return {'board_id': identity, 'kicad_version': native['kicad_version'],
            'schematic_tree_sha256': tree_hash, 'errors': errors,
            'warning_count': len(warnings),
            'warning_types': dict(sorted(Counter(w['type'] for w in warnings).items())),
            'warnings': warnings}


HEADER_REF=re.compile(r'^J9\d{5}$')


def item_ref(item):
    return item.split()[1]


def projected_identities(projected,baseline,board_of,identity):
    """Multisets of warning identities, projected and master. A master warning whose two pins now sit on different
    boards (a net that crosses, such as a moved indicator bridge, MC04-S7) is projected on the board of each pin
    with a GH header pin as the other item; both sides compare with the off-board item replaced by one marker.
    Same-board warnings keep their exact identity."""
    marker='Symbol <GH header pin on the cross-board net>'
    def norm(w,keep):
        return identity({**w,'items':sorted(i if i==keep else marker for i in w['items'])})
    actual=Counter();expected=Counter();split=0
    for w in projected:
        heads=[i for i in w['items'] if HEADER_REF.match(item_ref(i))]
        others=[i for i in w['items'] if i not in heads]
        actual[norm(w,others[0]) if len(heads)==1 and len(others)==1 else identity(w)]+=1
    for w in baseline:
        boards={board_of.get(item_ref(i)) for i in w['items']}
        if len(w['items'])==2 and len(boards)==2:
            split+=1
            expected['split:'+identity(w)]+=1
        else:
            expected[identity(w)]+=1
    # resolve split master warnings against the projected ones: each must match one of its two projections
    for key in [k for k in expected if k.startswith('split:')]:
        w=json.loads(key[len('split:'):]);n=expected.pop(key)
        options=[norm(w,keep) for keep in w['items']]
        for _ in range(n):
            hit=next((o for o in options if actual[o]-expected[o]>0),options[0])
            expected[hit]+=1
    expected=+expected
    return actual,expected,split


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
    board_of={c['ref']:c['board'] for c in manifest['assignment']['components']}
    actual,expected,split=projected_identities([w for r in rows for w in r['warnings'] if w['type']=='pin_to_pin'],
                                               baseline['warnings'],board_of,identity)
    if actual!=expected:raise SystemExit('projected pin-to-pin warnings differ from master baseline identities')

    report = {'schema_version': 1, 'status': 'FAIL' if errors else 'PASS - native ERC errors zero; warnings retained; unvalidated drafts',
              'oracle': 'Pinned KiCad 10.0.6 via scripts/kicad/run.sh', 'boards': rows,
              'pin_to_pin_master_identity_parity':'PASS;%d original warning identities preserved, sheet paths projected; '
                                                  '%d of them split across boards, where the off-board pin is a GH header pin'
                                                  %(sum(expected.values()),split),
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
