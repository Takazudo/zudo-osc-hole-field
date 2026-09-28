#!/usr/bin/env python3
"""Check native per-board exports against the master and declared mate graph."""
from __future__ import annotations
import argparse
from collections import defaultdict, Counter
import json
import re
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.schgen.core import children, parse, tokens
from scripts.schgen.project_boards import load_partition, net_token
from scripts.schgen.verify_netlist import exported_pin_nets


def export_netlist(board_id):
    out = ROOT/'schematic/boards'/f'{board_id}.net'
    out.parent.mkdir(parents=True, exist_ok=True)
    source = ROOT/'boards'/board_id/f'{board_id}.kicad_sch'
    subprocess.run(['bash', str(ROOT/'scripts/kicad/run.sh'), 'kicad-cli', 'sch', 'export', 'netlist',
                    '--format', 'kicadsexpr', '-o', str(out.relative_to(ROOT)), str(source.relative_to(ROOT))],
                   cwd=ROOT, check=True)
    body = out.read_text()
    normalized, count = re.subn(r'(?m)^(\s*\(date ")\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}("\))$',
                                r'\g<1>2000-01-01T00:00:00\2', body)
    if count != 1:
        raise ValueError(f'{board_id}: expected one export timestamp, found {count}')
    out.write_text(normalized)
    copy = ROOT/'schematic/boards'/f'{board_id}.kicad_sch'
    copy.write_text(source.read_text().replace('(property "Sheetfile" "sheets/', f'(property "Sheetfile" "../../boards/{board_id}/sheets/'))
    return out


def components(netlist):
    tree, end = parse(tokens(netlist))
    if end != len(tokens(netlist)) or tree[0] != 'export':
        raise ValueError('incomplete KiCad netlist')
    result = {}
    for comp in children(children(tree, 'components')[0], 'comp'):
        ref = children(comp, 'ref')[0][1]
        if ref in result: raise ValueError(f'duplicate export component {ref}')
        result[ref] = comp
    return result


def assert_partition(partition, assignment):
    connectors = {c['id']: c for c in partition['connectors']}
    if len(connectors) != len(partition['connectors']): raise ValueError('duplicate connector id')
    seen = set()
    edges = defaultdict(set)
    for h in partition['harnesses']:
        if seen.intersection(h['header_ids']):
            raise ValueError(f'{h["id"]}: header used by multiple harnesses')
        a, b = (connectors[x] for x in h['header_ids'])
        if a['board'] == b['board']: raise ValueError(f'{h["id"]}: same-board harness')
        if a['contacts'] != b['contacts']: raise ValueError(f'{h["id"]}: contact mismatch')
        for pin in range(1, a['contacts'] + 1):
            key = str(pin)
            na, nb = a['pin_map'].get(key), b['pin_map'].get(key)
            if na != nb: raise ValueError(f'{h["id"]}: swapped/mismatched pin {pin}: {na} / {nb}')
            if na not in (None, 'NC'):
                edges[na].add(frozenset((a['board'], b['board'])))
        seen.update(h['header_ids'])
    if seen != set(connectors): raise ValueError('orphan/duplicated header in harness list')
    terminals = {t['reference']: t for t in partition['load_side_terminals']}
    if len(terminals) != 24: raise ValueError('load terminal count differs from 24')
    for w in partition['load_side_wires']:
        a, b = (terminals[r] for r in w['terminal_refs'])
        if a['net'] != b['net'] or a['net'] != w['net']:
            raise ValueError(f'{w["id"]}: wire net mismatch')
        edges[w['net']].add(frozenset((a['board'], b['board'])))
    if len(partition['load_side_wires']) != 12: raise ValueError('load wire count differs from 12')
    sensitive = {x['net'] for x in json.loads((ROOT/'design/reports/master-audit.json').read_text())['sensitive_nets']}
    for c in connectors.values():
        for net in c['pin_map'].values():
            if net in sensitive: raise ValueError(f'{c["id"]}: Sensitive net on connector: {net}')
            if net and any(x in net.upper() for x in ('RAW_TIP', 'SLEW_STORAGE', 'HOLD_CAP', 'SUMMING')):
                raise ValueError(f'{c["id"]}: raw/storage/summing net on connector: {net}')
    islands = json.loads((ROOT/'design/reports/master-audit.json').read_text())['islands']
    for island, refs in islands.items():
        boards = {assignment[ref]['board'] for ref in refs if ref in assignment}
        if len(boards) > 1: raise ValueError(f'split island {island}: {sorted(boards)}')
    return edges


def verify(partition, board_netlists, master_netlist):
    assignment = {x['ref']: x for x in partition['assignment']['components']}
    if len(assignment) != len(partition['assignment']['components']): raise ValueError('duplicate component assignment')
    edges = assert_partition(partition, assignment)
    master = exported_pin_nets(master_netlist)
    master = {key: net for key, net in master.items() if key[0] in assignment}
    master_components = components(master_netlist)
    projected = {}
    net_boards = defaultdict(set)
    refs = Counter()
    board_by_id = {b['id']: short for short, b in [('J', {'id':'osc-jack'}),('P', {'id':'osc-control'}),('K', {'id':'osc-core'}),('EL', {'id':'osc-stage-optical'}),*((f'O{i}', {'id':f'osc-octave-{i}'}) for i in range(1,6))]}
    for board_id, data in board_netlists.items():
        board = board_by_id[board_id]
        comp = components(data)
        actual = exported_pin_nets(data)
        expected_refs = {r for r, a in assignment.items() if a['board'] == board}
        physical = set(comp) & set(assignment)
        if physical != expected_refs: raise ValueError(f'{board_id}: component set mismatch: missing={sorted(expected_refs-physical)[:8]} extra={sorted(physical-expected_refs)[:8]}')
        for ref in physical: refs[ref] += 1
        expected_interfaces = {c['pcb_reference'] for c in partition['connectors'] if c['board'] == board}
        expected_interfaces |= {t['reference'] for t in partition['load_side_terminals'] if t['board'] == board}
        if set(comp) != physical | expected_interfaces:
            raise ValueError(f'{board_id}: interface component set mismatch')
        for ref in physical:
            for field in ('value', 'footprint'):
                if children(comp[ref], field) != children(master_components[ref], field):
                    raise ValueError(f'{ref}: {field} differs from master')
            def identity(node):
                fields = children(node, 'fields')
                if not fields: return {}
                return {children(x, 'name')[0][1]: (x[-1] if len(x) > 2 else '')
                        for x in children(fields[0], 'field') if children(x, 'name')}
            old, new = identity(master_components[ref]), identity(comp[ref])
            for field in ('MPN', 'Manufacturer', 'LCSC', 'PanelUid'):
                if old.get(field) != new.get(field):
                    raise ValueError(f'{ref}: {field} differs from master')
        for key, token in actual.items():
            ref, pin = key
            if ref in assignment:
                if key in projected: raise ValueError(f'duplicate physical pin {key}')
                projected[key] = token
                if token is not None: net_boards[master[key]].add(board)
            elif ref in expected_interfaces:
                declared = next((c['pin_map'].get(pin) for c in partition['connectors'] if c['pcb_reference'] == ref), None)
                if ref.startswith('TP'):
                    declared = next(t['net'] for t in partition['load_side_terminals'] if t['reference'] == ref)
                if token != (net_token(declared) if declared not in (None, 'NC') else None):
                    raise ValueError(f'{ref}.{pin}: connector/terminal pin map mismatch {token} / {declared}')
    if set(refs) != set(assignment) or any(v != 1 for v in refs.values()):
        raise ValueError('missing/duplicate physical package')
    if set(projected) != set(master):
        raise ValueError(f'physical pin set differs: missing={sorted(set(master)-set(projected))[:8]} extra={sorted(set(projected)-set(master))[:8]}')
    for key, net in master.items():
        if projected[key] != (net_token(net) if net is not None else None):
            raise ValueError(f'{key}: master={net}, board={projected[key]}')
    for net, boards in net_boards.items():
        if len(boards) < 2: continue
        reached = {next(iter(boards))}
        while True:
            new = {b for pair in edges.get(net, ()) if pair & reached for b in pair}
            if new <= reached: break
            reached |= new
        if not boards <= reached:
            raise ValueError(f'{net}: declared harness/wire graph disconnects {sorted(boards-reached)}')
    return {'status': 'PASS - native joined pin/net and declared interface graph only; unvalidated draft',
            'physical_components': len(refs), 'physical_pins': len(projected),
            'fitted_components': sum(x['fitted'] for x in assignment.values()),
            'dnp_components': sum(not x['fitted'] for x in assignment.values()),
            'fitted_ICs': sum(x['fitted'] and ref.startswith('U') for ref, x in assignment.items()),
            'master_nets': len(set(n for n in master.values() if n is not None)),
            'cross_board_nets': sum(len(v)>1 for v in net_boards.values()),
            'headers': len(partition['connectors']), 'harnesses': len(partition['harnesses']),
            'load_side_terminals': len(partition['load_side_terminals']), 'load_side_wires': len(partition['load_side_wires'])}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--export', action='store_true')
    args = parser.parse_args()
    partition = load_partition()
    data = {}
    for b in partition['boards']:
        path = export_netlist(b['id']) if args.export else ROOT/'schematic/boards'/f'{b["id"]}.net'
        data[b['id']] = path.read_text()
    master = (ROOT/'.circuit-cache/partition/master.net').read_text()
    result = verify(partition, data, master)
    report = ROOT/'design/reports/board-projection.json'
    report.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__': main()
