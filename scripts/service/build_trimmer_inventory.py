#!/usr/bin/env python3
"""Join the reviewed semantic contract to current source and retained KiCad inputs.

This is a read-only source consistency check, not a fresh native KiCad check.
No references, component identities, circuits, placements or copper are modified.
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from design.spec.instrument import specification
from scripts.schgen.core import children, designator, parse, tokens
from scripts.schgen.verify_netlist import expected_pin_nets
from scripts.schgen.project_boards import net_token

FOOTPRINT = 'zudo-osc-hole-field:Potentiometer_Bourns_TC33X_Vertical'
SYMBOLS = {'TC33X-2-102E', 'TC33X-2-103E'}
FUNCTIONS = 'design/service/trimmer-functions.json'
OUTPUT = 'design/service/trimmer-inventory.json'
NETLIST = 'schematic/boards/osc-core.net'
PLACEMENTS = 'design/partition/floorplan-candidate.json'
PCB = 'boards/osc-core/osc-core.kicad_pcb'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def is_trimmer(part):
    # Union detection prevents a lost footprint, lost Role or MPN from hiding a trim.
    return (part.footprint == FOOTPRINT or
            part.symbol.rsplit(':', 1)[-1] in SYMBOLS)


def source_rows(families, instances):
    rows = {}
    for instance in instances:
        family = next(f for f in families if f.name == instance.family)
        for part in family.parts:
            if not is_trimmer(part):
                continue
            ref = designator(part, instance)
            if ref in rows:
                raise ValueError(f'duplicate source trimmer: {ref}')
            if part.footprint != FOOTPRINT or not part.attributes.get('Role'):
                raise ValueError(f'{ref}: missing/unsupported trimmer footprint or Role')
            rows[ref] = {
                'ref': ref, 'block': instance.name, 'role': part.attributes['Role'],
                'family': family.name, 'part_key': part.key, 'value': part.value,
                'mpn': part.attributes.get('MPN', ''),
                'manufacturer': part.attributes.get('Manufacturer', ''),
                'footprint': part.footprint, 'symbol': part.symbol,
            }
    return rows


def netlist_data(text):
    ts = tokens(text)
    tree, end = parse(ts)
    if end != len(ts) or tree[0] != 'export':
        raise ValueError('not a complete retained KiCad netlist')
    components = {}
    for c in children(children(tree, 'components')[0], 'comp'):
        ref = children(c, 'ref')[0][1]
        if ref in components:
            raise ValueError(f'duplicate netlist reference: {ref}')
        props = {children(p, 'name')[0][1]:
                 (children(p, 'value')[0][1] if children(p, 'value') and len(children(p, 'value')[0]) > 1 else '')
                 for p in children(c, 'property')}
        components[ref] = {
            'value': children(c, 'value')[0][1],
            'footprint': children(c, 'footprint')[0][1] if children(c, 'footprint') else '', **props,
        }
    pins = {}
    for net in children(children(tree, 'nets')[0], 'net'):
        name = children(net, 'name')[0][1]
        for node in children(net, 'node'):
            key = (children(node, 'ref')[0][1], children(node, 'pin')[0][1])
            if key in pins:
                raise ValueError(f'duplicate netlist pin: {key}')
            pins[key] = None if name.startswith('unconnected-(') else name
    return components, pins


def pcb_trimmers(text):
    # Read only footprint expressions, avoiding the large filled-zone/copper tree.
    # KiCad's saved top-level indentation supplies boundaries; parse each expression.
    result = {}
    for match in re.finditer(r'^\t\(footprint .*?^\t\)', text, re.M | re.S):
        fragment = match.group()
        if 'Potentiometer_Bourns_TC33X_Vertical' not in fragment:
            continue
        ts = tokens(fragment)
        fp, end = parse(ts)
        if end != len(ts) or fp[1] != FOOTPRINT:
            raise ValueError('unsupported native trimmer footprint')
        props = {p[1]: p[2] for p in children(fp, 'property')}
        ref = props['Reference']
        if ref in result:
            raise ValueError(f'duplicate PCB trimmer: {ref}')
        at = children(fp, 'at')[0]
        pads = {}
        for pad in children(fp, 'pad'):
            number = pad[1]
            if number in pads:
                raise ValueError(f'{ref}: duplicate trimmer pad {number}')
            nets = children(pad, 'net')
            pads[number] = nets[0][-1] if nets else None
        result[ref] = {
            'properties': props,
            # scripts/pcbgen/place.py translates fixed source coordinates by [100,50].
            'x_mm': float(at[1]) - 100, 'y_mm': float(at[2]) - 50,
            'native_x_mm': float(at[1]), 'native_y_mm': float(at[2]),
            'native_orientation_deg': float(at[3]) if len(at) > 3 else 0,
            'kicad_orientation_deg': (float(at[3]) if len(at) > 3 else 0) % 360,
            'side': children(fp, 'layer')[0][1], 'pads': pads,
        }
    return result


def build(families, instances, dictionary, components, pins, placements, native):
    if dictionary.get('schema_version') != 1:
        raise ValueError('unsupported function dictionary schema')
    source = source_rows(families, instances)
    roles = dictionary['roles']
    if len(roles) != 28 or len({r['role'] for r in roles}) != len(roles):
        raise ValueError('expected 28 unique reviewed roles')
    role_map = {r['role']: r for r in roles}
    for role in roles:
        if (any(k in role for k in ('x_mm', 'y_mm', 'rotation_deg', 'side', 'board')) or
                role['calibration_status'] != 'NEEDS BENCH' or
                role['rotation_direction'] != 'UNKNOWN / NEEDS BENCH'):
            raise ValueError('invalid role placement/calibration/direction contract')
    if {r['role'] for r in source.values()} != set(role_map):
        raise ValueError('missing, unknown or stale trimmer roles')
    entries = dictionary['trimmers']
    if len(entries) != 100 or len({r['ref'] for r in entries}) != len(entries):
        raise ValueError('expected 100 unique dictionary rows')
    if {r['ref'] for r in entries} != set(source) or set(native) != set(source):
        raise ValueError('source/dictionary/PCB trimmer coverage differs')
    net_refs = {ref for ref, c in components.items() if c['footprint'] == FOOTPRINT}
    if net_refs != set(source):
        raise ValueError('retained netlist trimmer coverage differs')
    expected = expected_pin_nets(families, instances)
    placed = {}
    for p in placements:
        if p['ref'] in source:
            if p['ref'] in placed:
                raise ValueError(f'duplicate placement: {p["ref"]}')
            placed[p['ref']] = p
    if set(placed) != set(source):
        raise ValueError('missing trimmer placement')
    output = []
    for row in sorted(entries, key=lambda r: r['ref']):
        ref = row['ref']
        src, comp, fp, place = source[ref], components[ref], native[ref], placed[ref]
        for key in ('ref', 'block', 'role', 'family', 'part_key', 'value', 'mpn',
                    'manufacturer', 'footprint', 'symbol'):
            if row[key] != src[key]:
                raise ValueError(f'{ref}: reviewed {key} differs from source')
        if any(k in row for k in ('x_mm', 'y_mm', 'rotation_deg', 'side', 'board')):
            raise ValueError(f'{ref}: placement leaked into function dictionary')
        role = role_map[row['role']]
        module_label = dictionary['module_labels'].get(src['block'])
        calibration_slug = row['role'].replace(':', '-').replace('_', '-').lower()
        if (row['function_label'] != role['function_label'] or
                not module_label or row['module_label'] != module_label or
                row['label'] != module_label + ' ' + role['function_label'] or
                row['reference_label'] != ref or row['calibration_status'] != 'NEEDS BENCH' or
                row['calibration_reference'] != 'doc/src/content/docs/verification/osc-trimmer-calibration.mdx#' + calibration_slug or
                row['source_locator'] != role['source_locator'] or
                row['rotation_direction'] != 'UNKNOWN / NEEDS BENCH' or
                row['mpn_status'] != ('SOURCE ASSIGNED / NOT QUALIFIED' if src['mpn'] else 'UNRESOLVED')):
            raise ValueError(f'{ref}: invalid semantic/identity/direction contract')
        nominal = '1 kΩ' if src['value'] == 'TC33X-2-102E' else src['value']
        if row['nominal_resistance'] != nominal:
            raise ValueError(f'{ref}: nominal resistance differs from source identity/value')
        for key, prop in (('block', 'Block'), ('role', 'Role'), ('value', 'value'),
                          ('mpn', 'MPN'), ('manufacturer', 'Manufacturer'), ('footprint', 'footprint')):
            if comp.get(prop, '') != src[key]:
                raise ValueError(f'{ref}: retained netlist {prop} drift')
            # PCB library name was checked when parsing, not a Footprint property.
            if prop != 'footprint' and fp['properties'].get(prop.title() if prop == 'value' else prop, '') != src[key]:
                raise ValueError(f'{ref}: retained PCB {prop} drift')
        source_pins = {pin: net for (r, pin), net in expected.items() if r == ref}
        expected_pins = {pin: net_token(net) if net is not None else None for pin, net in source_pins.items()}
        if set(expected_pins) != {'1', '2', '3'} or any(net is None for net in expected_pins.values()):
            raise ValueError(f'{ref}: trimmer must retain all three connected pins')
        retained_pins = {pin: net for (r, pin), net in pins.items() if r == ref}
        if fp['pads'] != expected_pins or retained_pins != expected_pins:
            raise ValueError(f'{ref}: retained netlist/PCB pin connectivity drift')
        for key in ('x_mm', 'y_mm', 'kicad_orientation_deg', 'side'):
            if isinstance(place[key], str):
                equal = place[key] == fp[key]
            else:
                equal = abs(place[key] - fp[key]) < 1e-5
            if not equal:
                raise ValueError(f'{ref}: source/native placement {key} drift')
        if comp.get('BoardAssignment') != place['board'] or comp.get('BoardSide') != fp['side']:
            raise ValueError(f'{ref}: board/face identity drift')
        output.append({**row, 'source_pins': source_pins, 'pins': expected_pins, 'placement': {
            'board': place['board'], 'board_id': 'osc-core' if place['board'] == 'K' else place['board'],
            **{k: fp[k] for k in ('x_mm', 'y_mm', 'kicad_orientation_deg', 'side')},
            **{k: fp[k] for k in ('native_x_mm', 'native_y_mm', 'native_orientation_deg')},
            'rotation_deg': place['rotation_deg'], 'courtyard_mm': place['courtyard_mm'],
        }})
    counts = Counter(r['mpn'] or 'UNRESOLVED' for r in output)
    if counts != {'TC33X-2-102E': 21, 'TC33X-2-103E': 56, 'UNRESOLVED': 23}:
        raise ValueError('MPN assignment/loss differs from reviewed 21/56/23 contract')
    return {'schema_version': 1, 'status': 'RETAINED SOURCE CONSISTENCY ONLY / UNVALIDATED DRAFT',
            'input_source_sha': dictionary['input_source_sha'],
            'summary': {'trimmers': len(output), 'roles': len(roles),
                        'mpn_counts': dict(sorted(counts.items())),
                        'faces': dict(sorted(Counter(r['placement']['side'] for r in output).items()))},
            'trimmers': output}


def generate():
    dictionary = json.loads((ROOT / FUNCTIONS).read_text())
    components, pins = netlist_data((ROOT / NETLIST).read_text())
    result = build(*specification(), dictionary, components, pins,
                   json.loads((ROOT / PLACEMENTS).read_text())['placements'],
                   pcb_trimmers((ROOT / PCB).read_text()))
    sources = [FUNCTIONS, NETLIST, PLACEMENTS, PCB, 'scripts/service/build_trimmer_inventory.py']
    sources += ['scripts/pcbgen/place.py', 'design/standard/pin-maps/trim_102.json',
                'design/standard/pin-maps/trim_103.json']
    sources += [str(p.relative_to(ROOT)) for folder in ('design/spec', 'design/standard', 'scripts/schgen')
                for p in (ROOT / folder).rglob('*') if p.suffix in ('.py', '.json')]
    sources += ['design/partition/partition.json',
                'footprints/kicad/zudo-osc-hole-field.pretty/Potentiometer_Bourns_TC33X_Vertical.kicad_mod']
    result['input_sha256'] = {p: digest(ROOT / p) for p in sorted(set(sources))}
    return json.dumps(result, ensure_ascii=False, indent=2) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    try:
        rendered = generate()
        target = ROOT / OUTPUT
        if args.check:
            if not target.exists() or target.read_text() != rendered:
                raise ValueError('generated trimmer inventory is stale; run builder without --check')
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(rendered)
    except (ValueError, KeyError, IndexError) as exc:
        print(f'FAIL: {exc}', file=sys.stderr)
        return 1
    print('PASS: 100 unique trimmers, 28 roles; retained source/netlist/PCB consistency (not native acceptance)')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
