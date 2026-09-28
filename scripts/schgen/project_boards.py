#!/usr/bin/env python3
"""Project the locked master packages and declared interfaces onto nine draft boards."""
from __future__ import annotations
from collections import defaultdict
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from design.spec.instrument import specification
from design.spec.cells._builder import load_symbol
from scripts.schgen.core import Family, Instance, LibrarySymbol, Part, designator, render

FIXTURES = {'LM2902', 'LM2903', 'R', 'Conn_01x02', 'PWR_FLAG', 'GND', 'VCC'}
RAILS = {'AGND', '+12V', '-12V', '+5V', '+12V_IN', '-12V_IN', '+5V_IN'}


def net_token(net: str) -> str:
    if net in RAILS:
        return net
    return 'X' + hashlib.sha256(net.encode()).hexdigest()[:20].upper()


def source_net(family: Family, instance: Instance, part: Part, net: str) -> str:
    if net in family.global_nets:
        return net
    sheet = instance.name if part.page == 1 else f'{instance.name}-P{part.page}'
    return f'/{sheet}/{net}'


def load_partition():
    return json.loads((ROOT / 'design/partition/partition.json').read_text())


def project(partition=None):
    partition = partition or load_partition()
    source_families, source_instances = specification()
    family_by_name = {f.name: f for f in source_families}
    assignment = {x['ref']: x for x in partition['assignment']['components']}
    floorplan = {x['ref']: x for x in json.loads((ROOT/'design/partition/floorplan-candidate.json').read_text())['placements']}
    if set(floorplan) != set(assignment): raise ValueError('floorplan/assignment reference mismatch')
    if len(assignment) != len(partition['assignment']['components']):
        raise ValueError('duplicate assigned package')
    boards = {b['id']: b for b in partition['boards']}
    short_to_id = {x['board']: x['board_id'] for x in (
        {'board': 'J', 'board_id': 'osc-jack'}, {'board': 'P', 'board_id': 'osc-control'},
        {'board': 'K', 'board_id': 'osc-core'}, {'board': 'EL', 'board_id': 'osc-stage-optical'},
        *({'board': f'O{i}', 'board_id': f'osc-octave-{i}'} for i in range(1, 6)))}
    assert set(boards) == set(short_to_id.values())
    abstract = set(partition['assignment']['abstract_boundaries'])
    families = defaultdict(list)
    instances = defaultdict(list)
    canon = {}
    package_units = defaultdict(list)
    for inst in source_instances:
        source_family = family_by_name[inst.family]
        slices = defaultdict(list)
        for part in source_family.parts:
            ref = designator(part, inst)
            if part.abstract or ref in abstract:
                continue
            if part.symbol.rsplit(':', 1)[-1] in {'PWR_FLAG', 'GND', 'VCC'}:
                continue
            item = assignment.get(ref)
            if item is None:
                raise ValueError(f'physical package missing board assignment: {ref}')
            board = item['board']
            package_units[ref].append(board)
            pins = {}
            for pin, net in part.pins.items():
                if net is None:
                    pins[pin] = None
                else:
                    original = source_net(source_family, inst, part, net)
                    token = net_token(original)
                    previous = canon.setdefault(token, original)
                    if previous != original:
                        raise ValueError(f'net-token collision: {previous} / {original}')
                    pins[pin] = token
            placement = floorplan[ref]
            if placement['side'] != item['side'] or placement['board'] != board:
                raise ValueError(f'{ref}: floorplan side/board mismatch')
            attrs = {**part.attributes, 'BoardSide': item['side'], 'BoardAssignment': board,
                     'KiCadOrientationDeg': str(placement['kicad_orientation_deg']),
                     'FootprintOriginMm': f"{placement['x_mm']},{placement['y_mm']}"}
            if board == 'J':
                # Multi-unit physical packages have unit-specific source roles.
                # The board's one footprint cannot truthfully carry all of them.
                for unit_field in ('Role','LogicalCellKey','Island'):
                    attrs.pop(unit_field, None)
            slices[board].append(replace(part, pins=pins, panel_ref=ref, panel_refs={}, attributes=attrs))
        for board, parts in slices.items():
            board_id = short_to_id[board]
            name = f'{source_family.name}_{inst.name}_{board}'
            all_nets = sorted({n for part in parts for n in part.pins.values() if n is not None})
            families[board_id].append(Family(name, tuple(parts), tuple(all_nets), (), source_family.paper))
            instances[board_id].append(Instance(name, inst.name, inst.index))
    if set(package_units) != set(assignment):
        raise ValueError(f'assignment mismatch: missing={sorted(set(assignment)-set(package_units))[:8]} extra={sorted(set(package_units)-set(assignment))[:8]}')
    if any(len(set(v)) != 1 for v in package_units.values()):
        raise ValueError('package units assigned to multiple boards')
    return partition, source_families, source_instances, short_to_id, families, instances, canon


def interface_family(board, partition, canon):
    parts = []
    contacts = [c for c in partition['connectors'] if c['board'] == board]
    terminals = [t for t in partition['load_side_terminals'] if t['board'] == board]
    for n, c in enumerate(contacts):
        pins = {str(i): net_token(v) if v not in (None, 'NC') else None for i, v in c['pin_map'].items()}
        for v in c['pin_map'].values():
            if v not in (None, 'NC'):
                canon.setdefault(net_token(v), v)
        pins.update({x: None for x in c['mechanical_pads']})
        count = c['contacts']
        parts.append(Part(key=c['pcb_reference'], symbol=f'zudo-osc-hole-field:JST_GH{count}_BM', prefix='J', ordinal=1,
            unit=0, x=35 + (n % 3) * 65, y=40 + ((n // 3) % 8) * 30, page=1 + n // 24,
            pins=pins, panel_ref=c['pcb_reference'], footprint=f'zudo-osc-hole-field:JST_GH{count}_BM_TopEntry',
            value=c['header_mpn'], attributes={'MPN': c['header_mpn'], 'Manufacturer': 'JST',
            'BoardSide': c['side'], 'KiCadOrientationDeg': str(c['kicad_orientation_deg']),
            'FootprintOriginMm': ','.join(map(str, c['footprint_origin_mm']))}))
    start_page = 1 + (len(contacts) + 23) // 24
    for n, t in enumerate(terminals):
        net = t['net']; canon.setdefault(net_token(net), net)
        parts.append(Part(key=t['reference'], symbol='zudo-osc-hole-field:TestPoint', prefix='TP', ordinal=1,
            unit=0, x=35 + (n % 3) * 65, y=40 + ((n // 3) % 8) * 30, page=start_page + n // 24,
            pins={'1': net_token(net)}, panel_ref=t['reference'], in_bom=False,
            footprint='zudo-osc-hole-field:LoadWireTerminal_4x4mm', value='LOAD WIRE SOLDER LAND',
            attributes={'BoardSide': t['side'], 'FootprintOriginMm': ','.join(map(str, t['center_mm'])),
                        'Role': 'factory load-side solder terminal'}))
    return Family(f'board_interfaces_{board}', tuple(parts), tuple(sorted({n for p in parts for n in p.pins.values() if n})), (), 'A0')


def write_footprint():
    path = ROOT/'footprints/kicad/zudo-osc-hole-field.pretty/LoadWireTerminal_4x4mm.kicad_mod'
    path.write_text('''(footprint "LoadWireTerminal_4x4mm" (version 20240108) (generator "zudo_schgen")
  (layer "F.Cu")
  (attr smd)
  (fp_text reference "REF**" (at 0 -3.2) (layer "F.SilkS") (effects (font (size 1 1) (thickness 0.15))))
  (fp_text value "LoadWireTerminal_4x4mm" (at 0 3.2) (layer "F.Fab") (effects (font (size 1 1) (thickness 0.15))))
  (fp_rect (start -2.5 -2.5) (end 2.5 2.5) (stroke (width 0.05) (type default)) (fill none) (layer "F.CrtYd"))
  (pad "1" smd rect (at 0 0) (size 4 4) (layers "F.Cu" "F.Mask") (solder_mask_margin 0.1))
)
''')
    from scripts.libgen.gen_courtyards import rewrite
    path.write_text(rewrite(path.read_text()))
    source = ROOT/'design/partition/partition-input.json'
    key = path.relative_to(ROOT).as_posix()
    source_key = source.relative_to(ROOT).as_posix()
    receipt = {
        'receipt_version': 1,
        'identity': {'asset_id': 'footprint-load-wire-terminal-4x4mm', 'record_id': None,
                     'manufacturer': None, 'mpn': None, 'package': 'LoadWireTerminal_4x4mm',
                     'variant_notes': 'Project-defined bare copper terminal, not an orderable inlet.'},
        'acquisition': {'provider': 'Project partition proposal', 'library_release_tag': None,
                        'source_url': source_key, 'acquired_on': '2026-09-28',
                        'original_filenames': [source.name],
                        'sha256': {source_key: hashlib.sha256(source.read_bytes()).hexdigest()}},
        'representation': {'files': [key], 'formats': ['kicad_mod'], 'units': 'mm',
                           'original_paths': [source_key]},
        'fidelity': {'class': 'derived', 'reason': 'Exact project-proposed 4x4 mm copper land; physical solder/thermal/strain behavior NOT RUN.',
                     'evidence': [source_key]},
        'derivation': {'derived': True,
                       'input_sha256': {source_key: hashlib.sha256(source.read_bytes()).hexdigest()},
                       'tool': 'scripts/schgen/project_boards.py and scripts/libgen/gen_courtyards.py',
                       'tool_version': '1', 'parameters': {'copper_land_mm': [4, 4], 'mask_margin_mm': 0.1},
                       'output_sha256': {key: hashlib.sha256(path.read_bytes()).hexdigest()}},
        'cad_use': {'symbol': 'zudo-osc-hole-field:TestPoint',
                    'footprint': 'zudo-osc-hole-field:LoadWireTerminal_4x4mm', 'model_path': None},
        'checks': {'performed': ['KiCad parse and generated courtyard check'],
                   'remaining_physical_checks': ['Factory solder profile, ampacity and strain relief #65 NOT RUN']},
        'publication': {'preview_selected': False, 'download_published': False, 'permitted_scope': None}}
    (ROOT/'circuit/cad-receipts/footprint-load-wire-terminal-4x4mm.receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')


def main():
    partition, _, _, short_to_id, families, instances, canon = project()
    write_footprint()
    symbols = {}
    for fs in families.values():
        for f in fs:
            for p in f.parts:
                if p.symbol in symbols: continue
                key = p.symbol.split(':', 1)[1]
                symbols[p.symbol] = (LibrarySymbol.from_fixture(p.symbol, ROOT/'scripts/schgen/fixtures'/f'{key}.kicad_sympart')
                    if key in FIXTURES else load_symbol(key))
    for key in ('JST_GH3_BM', 'JST_GH7_BM', 'JST_GH8_BM', 'TestPoint'):
        symbols[f'zudo-osc-hole-field:{key}'] = load_symbol(key)
    symbols['Fixture:PWR_FLAG'] = LibrarySymbol.from_fixture('Fixture:PWR_FLAG', ROOT/'scripts/schgen/fixtures/PWR_FLAG.kicad_sympart')
    for short, board_id in short_to_id.items():
        fs = [*families[board_id], interface_family(short, partition, canon)]
        ins = [*instances[board_id], Instance(fs[-1].name, f'INTERFACES_{short}', 999)]
        power_nets = set()
        for family in fs:
            for part in family.parts:
                for pin in symbols[part.symbol].units[part.unit]:
                    if pin.electrical == 'power_in' and part.pins.get(pin.number):
                        power_nets.add(part.pins[pin.number])
        flags = [Part(key=f'PWR{i}', symbol='Fixture:PWR_FLAG', prefix='PWR', ordinal=i,
                      unit=0, x=35+(i%3)*65, y=40+((i//3)%8)*30, page=1+i//24,
                      pins={'1': net}, panel_ref=f'#PWR{i}', in_bom=False, on_board=False)
                 for i, net in enumerate(sorted(power_nets), 1)]
        if flags:
            ff = Family(f'board_power_flags_{short}', tuple(flags), tuple(sorted(power_nets)), (), 'A0')
            fs.append(ff)
            ins.append(Instance(ff.name, f'POWER_FLAGS_{short}', 998))
        generated = render(tuple(fs), tuple(ins), symbols, board_id)
        output = ROOT/'boards'/board_id
        for stale in (output/'sheets').glob('*.kicad_sch'):
            if f'sheets/{stale.name}' not in generated and '(generator "zudo_schgen")' in stale.read_text():
                stale.unlink()
        for path, data in generated.items():
            target = output/path; target.parent.mkdir(parents=True, exist_ok=True); target.write_text(data)
        (output/f'{board_id}.kicad_pro').write_text(json.dumps({'meta': {'filename': f'{board_id}.kicad_pro', 'version': 1}, 'sheets': [], 'text_variables': {}}, indent=2)+'\n')
        (output/'sym-lib-table').write_text('(sym_lib_table\n  (version 7)\n  (lib (name "zudo-osc-hole-field") (type "KiCad") (uri "${KIPRJMOD}/../../symbols/zudo-osc-hole-field.kicad_sym") (options "") (descr ""))\n  (lib (name "Fixture") (type "KiCad") (uri "${KIPRJMOD}/../../scripts/schgen/fixtures/fixture.kicad_sym") (options "") (descr ""))\n)\n')
        (output/'fp-lib-table').write_text('(fp_lib_table\n  (version 7)\n  (lib (name "zudo-osc-hole-field") (type "KiCad") (uri "${KIPRJMOD}/../../footprints/kicad/zudo-osc-hole-field.pretty") (options "") (descr ""))\n)\n')
    report = ROOT/'design/reports/board-net-tokens.json'
    report.write_text(json.dumps(canon, indent=2, sort_keys=True)+'\n')
    print(f'Generated {len(short_to_id)} draft board schematics, {len(partition["connectors"])} headers, {len(partition["load_side_terminals"])} terminals')


if __name__ == '__main__': main()
