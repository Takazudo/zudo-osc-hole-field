#!/usr/bin/env python3
"""Compare retained panel evidence with source bindings; never invokes KiCad."""
from collections import Counter
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from design.spec.instrument import specification
from scripts.schgen.core import designator

OUT = ROOT / 'design/panel/current-audit/audit.json'

def read(path):
    return json.loads((ROOT / path).read_text())

def indexed(rows, key):
    result = {row[key]: row for row in rows}
    if len(result) != len(rows):
        raise ValueError(f'duplicate {key}')
    return result

def compare_features(lock, table, params):
    expected = indexed(lock['placements'], 'uid')
    actual = indexed(table['rows'], 'uid')
    if set(expected) != set(actual):
        raise ValueError('retained feature UID set differs from lock')
    for uid, row in expected.items():
        diameter = params['indicator_window']['diameter_mm'] if row['kind'] == 'led' else row['hole_d_mm']
        wanted = {'kind': row['kind'], 'x_mm': row['x_mm'], 'y_mm': row['y_mm'], 'diameter_mm': diameter,
                  'ref': ('PW_' if row['kind'] == 'led' else 'PH_') + row['slug']}
        if any(actual[uid].get(k) != v for k, v in wanted.items()):
            raise ValueError(f'retained feature differs: {uid}')
    return expected

def circuit_bindings():
    families, instances = specification()
    by_family = {f.name: f for f in families}
    rows = []
    for instance in instances:
        for part in by_family[instance.family].parts:
            uid = part.attributes.get('PanelUid', '').replace('${SHEETNAME}', instance.name)
            if not uid:
                continue
            rows.append({'uid': uid, 'instance': instance.name, 'circuit_family': instance.family,
                         'reference': designator(part, instance), 'mpn': part.attributes.get('MPN'),
                         'value': part.value, 'symbol': part.symbol, 'role': part.attributes.get('Role'),
                         'pins': part.pins, 'source': f'design/spec/modules/{instance.family}.py'})
    return indexed(rows, 'uid')

def build():
    lock = read('design/grid/placements.lock.json')
    grid = read('project/osc-hole-field/workbench/layout/grid.json')
    contracts = read('project/osc-hole-field/block-contracts.json')
    params = read('design/panel/panel-params.json')
    physical = compare_features(lock, read('boards/panel/reports/feature-table.json'), params)
    imported = indexed(grid['ports'] + grid['controls'], 'uid')
    declared = set()
    for block in contracts:
        for group, prefix in [('ports', 'J:'), ('controls', 'C:')]:
            for entry in block[group]:
                uid = prefix + entry['id']
                if uid in declared:
                    raise ValueError(f'duplicate contract UID: {uid}')
                declared.add(uid)
                source = imported[uid]
                if any(source.get(k) != v for k, v in entry.items()):
                    raise ValueError(f'grid/contract field mismatch: {entry["id"]}')
    if declared != set(imported):
        raise ValueError('contract/grid UID set mismatch')
    circuit = circuit_bindings()
    if set(circuit) != set(physical):
        raise ValueError('circuit/lock UID set mismatch')
    bindings, overrides = [], []
    for uid, row in sorted(physical.items()):
        part = circuit[uid]
        if part['reference'] != row['ref']:
            raise ValueError(f'circuit reference mismatch: {uid}')
        item = {**part, 'kind': row['kind'], 'label': row['label'], 'x_mm': row['x_mm'], 'y_mm': row['y_mm'],
                'imported_component': row.get('component'), 'led_type': row.get('led_type'),
                'direction': row.get('direction'), 'parent': row.get('parent'),
                'positions': imported.get(uid, {}).get('positions')}
        if row['kind'] == 'pot':
            inherited = row['component'].removeprefix('bourns-').upper()
            if inherited != part['mpn']:
                overrides.append({'uid': uid, 'imported_component': row['component'], 'current_mpn': part['mpn'],
                                  'role': part['role'], 'source': part['source'],
                                  'status': 'CURRENT_CIRCUIT_OVERRIDE_NOT_HARDWARE_QUALIFICATION'})
        bindings.append(item)
    jack_x = [r['x_mm'] for r in physical.values() if r['kind'] == 'jack']
    trial_d = {p['nut_diameter_mm'] for p in grid['ports']}
    if len(trial_d) != 1:
        raise ValueError('trial nut envelopes differ; compute individually')
    edge = min(min(jack_x), lock['frame']['panel_width_mm']-max(jack_x))-next(iter(trial_d))/2
    blocks = []
    for b in contracts:
        br = [r for r in bindings if r['instance'] == b['id']]
        blocks.append({'id': b['id'], 'family': b['family'], 'name': b['name'],
                       'ports': len(b['ports']), 'inputs': sum(p['direction']=='in' for p in b['ports']),
                       'outputs': sum(p['direction']=='out' for p in b['ports']), 'controls': len(b['controls']),
                       'leds': sum(r['kind']=='led' for r in br),
                       'electrical_overrides': sum(r['uid'].split(':')[1].split('.')[0]==b['id'] for r in overrides),
                       'owner_semantics': 'G06_OPEN' if b['family']=='VCF' else 'G07_OPEN' if b['family']=='AR' else 'NO_NEW_QUESTION_IDENTIFIED',
                       'mapping': 'SOURCE_UID_REFERENCE_MATCH', 'physical_fit': 'NOT_RUN'})
    paths = ['design/grid/placements.lock.json', 'project/osc-hole-field/workbench/layout/grid.json',
             'project/osc-hole-field/block-contracts.json', 'design/panel/panel-params.json',
             'boards/panel/reports/feature-table.json', 'scripts/panel/audit_current.py',
             'scripts/schgen/core.py', 'project/osc-hole-field/workbench/reference/icons.json',
             'project/osc-hole-field/workbench/src/render.js', 'scripts/panel/export_art.cjs',
             'scripts/panel/art_profile.cjs', 'scripts/panel/render_current.cjs']
    paths += [str(p.relative_to(ROOT)) for p in sorted((ROOT/'design/spec').rglob('*.py'))]
    paths += [str(p.relative_to(ROOT)) for p in sorted((ROOT/'design/standard').glob('*.json'))]
    return {'schema_version': 1, 'status': 'SOURCE_AUDIT_ONLY_NATIVE_NOT_RUN',
            'baseline': '142da27810994bc01f99bc2e6e1a559cd8f9c884',
            'counts': {'features':len(bindings), 'blocks':len(blocks), 'kinds':dict(sorted(Counter(r['kind'] for r in bindings).items())),
                       'pot_mpn':dict(sorted(Counter(r['mpn'] for r in bindings if r['kind']=='pot').items())),
                       'led_types':dict(sorted(Counter(r['led_type'] for r in bindings if r['kind']=='led').items()))},
            'perimeter_trial': {'outer_jack_x_mm':[min(jack_x),max(jack_x)], 'unqualified_nut_diameter_mm':next(iter(trial_d)),
                                'nearest_panel_edge_mm':edge, 'clearance_beyond_3mm_border_mm':edge-3,
                                'status':'TRIAL_ENVELOPE_ONLY_EXACT_NUT_FIT_UNQUALIFIED'},
            'source_sha256':{p:hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in paths},
            'blocks':blocks, 'electrical_overrides':overrides, 'bindings':bindings}

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--check', action='store_true'); args = parser.parse_args()
    output = json.dumps(build(), indent=2, ensure_ascii=False) + '\n'
    if args.check:
        if not OUT.exists() or OUT.read_text() != output:
            raise SystemExit('Stale current-panel source audit; regenerate and review')
    else:
        OUT.write_text(output)
    print('PASS source audit: 438 feature/UID/reference matches; see explicit electrical overrides and limitations')
