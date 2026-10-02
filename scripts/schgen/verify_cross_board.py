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
from scripts.pcbgen.netlist import Component, is_abstract_boundary


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
    if len(terminals) != partition['counts']['load_side_copper_terminals']: raise ValueError('load terminal count differs from manifest')
    for w in partition['load_side_wires']:
        a, b = (terminals[r] for r in w['terminal_refs'])
        if a['net'] != b['net'] or a['net'] != w['net']:
            raise ValueError(f'{w["id"]}: wire net mismatch')
        edges[w['net']].add(frozenset((a['board'], b['board'])))
    if len(partition['load_side_wires']) != partition['counts']['factory_load_side_wires']: raise ValueError('load wire count differs from manifest')
    used_terminals=[r for w in partition['load_side_wires'] for r in w['terminal_refs']]
    if Counter(used_terminals)!=Counter(terminals.keys()):raise ValueError('every load terminal must appear in exactly one wire')
    audit=json.loads((ROOT/'design/reports/master-audit.json').read_text())
    sensitive={x['net'] for x in audit['sensitive_nets']}
    def check_interface_net(label,net):
        if net in sensitive:raise ValueError(f'{label}: Sensitive net on interface: {net}')
        # Match the captured raw-TIP naming rule in io_partition60.crossing_kind().
        if net and (net.upper().endswith('_TIP') or any(x in net.upper() for x in ('RAW_TIP','SLEW_STORAGE','HOLD_CAP','SUMMING'))):
            raise ValueError(f'{label}: raw/storage/summing net on interface: {net}')
    for c in connectors.values():
        for net in c['pin_map'].values():check_interface_net(c['id'],net)
    # The independent source contract defines these as regulated main-power
    # and return wires, never a second channel for ordinary or Sensitive signals.
    distribution=json.loads((ROOT/'design/partition/partition-input.json').read_text())['load_distribution']
    net_order=distribution['net_order']
    if not isinstance(net_order,list) or not net_order or any(not isinstance(n,str) or not n for n in net_order):
        raise ValueError('source load-distribution net order must be a nonempty net list')
    allowed_load_nets=set(net_order)
    for terminal in terminals.values():
        net=terminal['net']
        check_interface_net(terminal['reference'],net)
        if net not in allowed_load_nets:
            raise ValueError(f'{terminal["reference"]}: net outside source load-distribution rails: {net}')
    islands=audit['islands']
    for island, refs in islands.items():
        boards = {assignment[ref]['board'] for ref in refs if ref in assignment}
        if len(boards) > 1: raise ValueError(f'split island {island}: {sorted(boards)}')
    return edges


def native_component(ref, node):
    """Adapt the native component to the shared strict boundary policy."""
    def scalar(name, optional=False):
        rows=children(node,name)
        if optional and not rows:return ''
        if len(rows)!=1 or len(rows[0])!=2:
            raise ValueError(f'{ref}: expected one native {name}')
        return rows[0][1]
    properties=[]
    for prop in children(node,'property'):
        names,values=children(prop,'name'),children(prop,'value')
        if len(names)!=1 or len(names[0])!=2 or len(values)>1 or any(len(row)!=2 for row in values):
            raise ValueError(f'{ref}: malformed native property')
        properties.append((names[0][1],values[0][1] if values else ''))
    if len(dict(properties))!=len(properties):
        raise ValueError(f'{ref}: duplicate native property')
    return Component(ref,scalar('value'),scalar('footprint',optional=True),'','','',tuple(properties))


def interface_pin_maps(partition):
    """All declared interface pins, including explicit NC and mechanical pads."""
    board_keys=[b['board_key'] for b in partition['boards']]
    if len(set(board_keys))!=len(board_keys):raise ValueError('duplicate declared board key')
    boards=set(board_keys)
    result={board:{} for board in boards}
    seen=set()
    def add(ref,board,pins):
        if ref in seen:raise ValueError(f'duplicate interface reference {ref}')
        if board not in boards:raise ValueError(f'{ref}: unknown interface board {board}')
        seen.add(ref)
        result[board].update({(ref,pin):net_token(net) if net not in (None,'NC') else None
                              for pin,net in pins.items()})
    for c in partition['connectors']:
        count=c['contacts']
        if type(count) is not int or count<1:raise ValueError('invalid connector contact count')
        electrical={str(pin) for pin in range(1,count+1)}
        if set(c['pin_map'])!=electrical:
            raise ValueError(f'{c["id"]}: incomplete electrical pin declaration')
        mechanical=c['mechanical_pads']
        if (any(not isinstance(pin,str) or not pin for pin in mechanical) or
                len(set(mechanical))!=len(mechanical) or electrical.intersection(mechanical)):
            raise ValueError(f'{c["id"]}: invalid mechanical pin declaration')
        add(c['pcb_reference'],c['board'],{**c['pin_map'],**dict.fromkeys(mechanical)})
    for terminal in partition['load_side_terminals']:
        pin=terminal['manufacturer_pin']
        if not isinstance(pin,str) or not pin:raise ValueError('invalid load terminal pin')
        add(terminal['reference'],terminal['board'],{pin:terminal['net']})
    return result


def verify_header_identity(connector, node, catalogue):
    ref=connector['pcb_reference'];count=connector['contacts']
    expected=catalogue.get(count)
    component=native_component(ref,node)
    properties=dict(component.fields)
    source=children(node,'libsource')
    if (expected is None or connector['header_mpn']!=expected or
            component.value!=expected or properties.get('MPN')!=expected or
            properties.get('Manufacturer')!='JST' or 'dnp' in properties or
            component.footprint!=f'zudo-osc-hole-field:JST_GH{count}_BM_TopEntry' or
            len(source)!=1 or children(source[0],'lib')!=[['lib','zudo-osc-hole-field']] or
            children(source[0],'part')!=[['part',f'JST_GH{count}_BM']]):
        raise ValueError(f'{ref}: fitted interface header identity differs from declared/audited GH source')


def verify(partition, board_netlists, master_netlist):
    assignment = {x['ref']: x for x in partition['assignment']['components']}
    if len(assignment) != len(partition['assignment']['components']): raise ValueError('duplicate component assignment')
    edges = assert_partition(partition, assignment)
    master = exported_pin_nets(master_netlist)
    master_components = components(master_netlist)
    native_master={ref:native_component(ref,node) for ref,node in master_components.items()}
    abstract={ref for ref,component in native_master.items() if is_abstract_boundary(component)}
    declared_abstract=partition['assignment']['abstract_boundaries']
    if len(set(declared_abstract))!=len(declared_abstract) or set(declared_abstract)!=abstract:
        raise ValueError('declared abstract boundaries differ from validated master boundaries')
    physical_master=set(master_components)-abstract
    if set(assignment)!=physical_master:
        raise ValueError(f'master physical component coverage mismatch: missing={sorted(physical_master-set(assignment))[:8]} extra={sorted(set(assignment)-physical_master)[:8]}')
    master_dnp={ref:'dnp' in dict(native_master[ref].fields) for ref in physical_master}
    for ref,item in assignment.items():
        if type(item.get('fitted')) is not bool or item['fitted']!= (not master_dnp[ref]):
            raise ValueError(f'{ref}: assignment fitted population differs from native master DNP')
    master={key:net for key,net in master.items() if key[0] not in abstract}
    interface_maps=interface_pin_maps(partition)
    headers={c['pcb_reference']:c for c in partition['connectors']}
    catalogue={row['positions']:row['header_mpn'] for row in json.loads(
        (ROOT/'design/connectors/jst-gh.json').read_text())['sizes']}
    if set(assignment).intersection(ref for pins in interface_maps.values() for ref,pin in pins):
        raise ValueError('interface reference collides with a master physical component')
    projected = {}
    net_boards = defaultdict(set)
    refs = Counter()
    interface_pins=unconnected_interface_pins=0
    board_by_id = {b['id']: b['board_key'] for b in partition['boards']}
    if (len(board_by_id)!=len(partition['boards']) or
            len(set(board_by_id.values()))!=len(board_by_id) or set(board_netlists)!=set(board_by_id)):
        raise ValueError('board export set differs from unique declared boards')
    for board_id, data in board_netlists.items():
        board = board_by_id[board_id]
        comp = components(data)
        actual = exported_pin_nets(data)
        expected_refs = {r for r, a in assignment.items() if a['board'] == board}
        physical = set(comp) & set(assignment)
        if physical != expected_refs: raise ValueError(f'{board_id}: component set mismatch: missing={sorted(expected_refs-physical)[:8]} extra={sorted(physical-expected_refs)[:8]}')
        for ref in physical: refs[ref] += 1
        expected_pins=interface_maps[board]
        expected_interfaces={ref for ref,pin in expected_pins}
        if any(ref not in comp for ref,pin in actual):
            raise ValueError(f'{board_id}: exported pin has no component')
        actual_interfaces={key:net for key,net in actual.items() if key[0] in expected_interfaces}
        if actual_interfaces!=expected_pins:
            missing=sorted(set(expected_pins)-set(actual_interfaces))
            extra=sorted(set(actual_interfaces)-set(expected_pins))
            changed=sorted(key for key in set(expected_pins)&set(actual_interfaces)
                           if expected_pins[key]!=actual_interfaces[key])
            raise ValueError(f'{board_id}: interface pin set/map mismatch: missing={missing[:8]} extra={extra[:8]} changed={changed[:8]}')
        interface_pins+=len(actual_interfaces)
        unconnected_interface_pins+=sum(net is None for net in actual_interfaces.values())
        if set(comp) != physical | expected_interfaces:
            raise ValueError(f'{board_id}: interface component set mismatch')
        for ref in expected_interfaces & headers.keys():
            verify_header_identity(headers[ref],comp[ref],catalogue)
        for ref in physical:
            if ('dnp' in dict(native_component(ref,comp[ref]).fields))!=master_dnp[ref]:
                raise ValueError(f'{ref}: projected DNP population differs from native master')
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
            'interface_pins': interface_pins, 'unconnected_interface_pins': unconnected_interface_pins,
            'validated_abstract_exclusions': sorted(abstract), 'verified_header_identities':len(headers),
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
