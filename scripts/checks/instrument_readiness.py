#!/usr/bin/env python3
"""Source-bound assembly coverage. This is neither a manufacturing BOM nor a native check."""
from __future__ import annotations
import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.pcbgen.netlist import TOKEN, parse, many, read_netlist
from scripts.pcbgen.uuid_tools import top_level_spans
from scripts.schgen.core import designator
from scripts.schgen.project_boards import interface_family
from design.spec.instrument import specification

CONFIG = 'circuit/readiness/instrument-manifest.json'
OUTPUT = 'design/reports/instrument-readiness.json'
MARKDOWN = 'design/reports/instrument-readiness.md'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def physical_source():
    """Deduplicate every multi-unit package by generated reference, including Q."""
    families, instances = specification()
    by_family = {f.name: f for f in families}
    packages = {}
    excluded = defaultdict(set)
    for instance in instances:
        for part in by_family[instance.family].parts:
            ref = designator(part, instance)
            if part.abstract or part.prefix.startswith('#'):
                excluded['abstract_boundary' if part.abstract else 'power_flag'].add(ref)
                continue
            row = {'mpn': part.attributes.get('MPN', ''),
                   'manufacturer': part.attributes.get('Manufacturer', ''),
                   'dnp': part.dnp, 'in_bom': part.in_bom, 'value': part.value,
                   'footprint': part.footprint, 'supplier_code': part.attributes.get('LCSC', '')}
            if ref in packages and packages[ref] != row:
                raise ValueError('Conflicting physical source units: ' + ref)
            packages[ref] = row
    return packages, {k: sorted(v) for k, v in sorted(excluded.items())}


def footprints(text):
    result = {}
    for start, end in top_level_spans(text):
        block = text[start:end]
        if not block.startswith('(footprint '):
            continue
        tree, consumed = parse(TOKEN.findall(block))
        properties = {}
        for prop in many(tree, 'property'):
            if prop[1] in properties:
                raise ValueError('Duplicate footprint property: ' + prop[1])
            properties[prop[1]] = prop[2]
        ref = properties.get('Reference')
        if not ref or ref in result:
            raise ValueError('Missing/duplicate footprint reference: ' + str(ref))
        attrs = many(tree, 'attr')
        result[ref] = {'footprint': tree[1], 'properties': properties,
                       'attributes': attrs[0][1:] if attrs else []}
    return result


def membership(expected, actual):
    return {'missing': sorted(set(expected) - set(actual)),
            'unexpected': sorted(set(actual) - set(expected))}


def classify(fields):
    if fields.get('AbstractBoundary') == 'true':
        return 'abstract_non_orderable'
    if 'dnp' in fields:
        return 'dnp'
    if 'exclude_from_bom' in fields or fields.get('Manufacturer') == 'Project CAD feature':
        return 'non_procured_geometry'
    if not fields.get('MPN') or not fields.get('Manufacturer'):
        return 'fitted_identity_incomplete'
    return 'fitted_identity_declared'


def retained_connectivity(root, board, report_path):
    if report_path is None:
        return {'status': 'NOT APPLICABLE', 'reason': 'Board-only panel'}
    path = root / report_path
    if not path.is_file():
        return {'status': 'MISSING', 'path': report_path}
    report = json.loads(path.read_text())
    bound = report.get('native_board_sha256', report.get('board_sha256', report.get('input_board_sha256')))
    if report.get('schema') == 'osc-current-native-state-1':
        bound = report['source']['input_board_sha256']
    count = report.get('native_unconnected_edge_count', report.get('native_unconnected_edges'))
    if count is None:
        count = report.get('native', report.get('connectivity', {})).get('open_edges')
    return {'path': report_path, 'sha256': digest(path), 'recorded_board_sha256': bound,
            'status': 'MATCHED BOARD BYTES' if bound == digest(root / board) else 'STALE OR UNBOUND',
            'complete_native_open_edges': count,
            'scope': 'Board-byte binding only; other report input dependencies are not revalidated here. No new native execution or electrical qualification'}


def build(root=ROOT):
    config = json.loads((root / CONFIG).read_text())
    partition = json.loads((root / 'design/partition/partition.json').read_text())
    source = json.loads((root / 'design/partition/partition-input.json').read_text())
    keys = set(source['boards'])
    if set(config['functional_units']) != keys or len(keys) != 10:
        raise ValueError('Manifest must cover exactly the ten current partition units')
    inventory = json.loads((root / '.claude/skills/component-spec-audit/references/inventory.json').read_text())
    owners = defaultdict(list)
    for line in inventory['lines']:
        owners[(line['manufacturer'], line['mpn'])].append(line)
    packages, excluded = physical_source()
    assignment = {r['ref']: r for r in partition['assignment']['components']}
    if len(assignment) != len(partition['assignment']['components']):
        raise ValueError('Duplicate partition assignment')
    source_membership = membership(packages, assignment)
    inputs = {CONFIG, 'design/partition/partition-input.json', 'design/partition/partition.json',
              'design/reports/io-partition.json', '.claude/skills/component-spec-audit/references/inventory.json',
              'scripts/checks/instrument_readiness.py', 'scripts/pcbgen/netlist.py',
              'scripts/pcbgen/uuid_tools.py', 'scripts/schgen/core.py',
              'circuit/routing/osc-pcb-current-checkpoint.json',
              'project/osc-hole-field/electrical-decisions.json'}
    inputs.update(str(p.relative_to(root)) for p in (root / 'design/spec').rglob('*.py'))
    inputs.update(str(p.relative_to(root)) for p in (root / 'design/standard').rglob('*.json'))
    inputs.add('design/connectors/jst-gh.json')
    inputs.add('scripts/schgen/project_boards.py')
    inputs.add('scripts/libgen/build_symbol_lib.py')
    inputs.update(str(p.relative_to(root)) for p in (root / 'symbols/src').glob('*.kicad_sym'))
    checkpoint = json.loads((root / 'circuit/routing/osc-pcb-current-checkpoint.json').read_text())
    for record in checkpoint['boards'].values():
        inputs.add(record['receipt']['path'])
        if record.get('adoption'):
            inputs.add(record['adoption']['path'])
    units = []
    total = Counter()
    for key in sorted(keys):
        selected = config['functional_units'][key]
        board_id = source['boards'][key]['id']
        board = selected['board']
        if not board.startswith('boards/' + board_id + '/'):
            raise ValueError('Board outside selected unit: ' + key)
        definition = 'design/boards/' + board_id + '.json'
        netlist = 'schematic/boards/' + board_id + '.net'
        inputs.update([board, definition, netlist])
        if selected.get('candidate_definition'):
            inputs.add(selected['candidate_definition'])
        folder = root / 'boards' / board_id
        inputs.update(str(p.relative_to(root)) for p in folder.rglob('*.kicad_sch'))
        inputs.update(str(p.relative_to(root)) for p in folder.glob('*.kicad_pro'))
        inputs.update(str(p.relative_to(root)) for p in folder.glob('*.kicad_dru'))
        components, _ = read_netlist(root / netlist, include_abstract=True)
        expected_parts = dict(packages)
        for part in interface_family(key, partition, {}).parts:
            expected_parts[part.panel_ref] = {
                'mpn': part.attributes.get('MPN', ''), 'manufacturer': part.attributes.get('Manufacturer', ''),
                'dnp': part.dnp, 'in_bom': part.in_bom, 'value': part.value,
                'footprint': part.footprint, 'supplier_code': part.attributes.get('LCSC', '')}
        expected = {r for r, a in assignment.items() if a['board'] == key}
        expected |= {r['pcb_reference'] for r in partition['connectors'] if r['board'] == key}
        expected |= {r['reference'] for r in partition['load_side_terminals'] if r['board'] == key}
        native = footprints((root / board).read_text())
        groups = defaultdict(list)
        discrepancies = []
        counts = Counter()
        for c in components:
            fields = dict(c.fields)
            disposition = classify(fields)
            counts[disposition] += 1
            identity = (fields.get('Manufacturer', ''), fields.get('MPN', ''))
            matches = owners.get(identity, []) if all(identity) else []
            owner_state = 'UNMATCHED' if not matches else ('AMBIGUOUS' if len(matches) > 1 else matches[0]['identity_state'])
            owner = matches[0]['owner_skill'] if len(matches) == 1 else None
            if owner:
                for name in ('manifest.json', 'sources.json', 'facts.json', 'pin-map.json', 'coverage.json'):
                    path = '.claude/skills/' + owner + '/' + name
                    if (root / path).is_file():
                        inputs.add(path)
            group = (disposition, *identity, c.footprint, fields.get('LCSC', ''), owner, owner_state)
            groups[group].append(c.ref)
            source_part = expected_parts.get(c.ref)
            if source_part:
                for field, expected_value, actual_value in (
                    ('MPN', source_part['mpn'], fields.get('MPN', '')),
                    ('Manufacturer', source_part['manufacturer'], fields.get('Manufacturer', '')),
                    ('dnp', source_part['dnp'], 'dnp' in fields),
                    ('in_bom', source_part['in_bom'], 'exclude_from_bom' not in fields),
                    ('value', source_part['value'], c.value),
                    ('footprint', source_part['footprint'], c.footprint),
                    ('supplier_code', source_part['supplier_code'], fields.get('LCSC', '')),
                ):
                    if expected_value != actual_value:
                        discrepancies.append({'ref': c.ref, 'field': field, 'specification': expected_value, 'netlist': actual_value})
            fp = native.get(c.ref)
            if fp:
                comparisons = {'footprint': (c.footprint, fp['footprint']),
                               'MPN': (fields.get('MPN', ''), fp['properties'].get('MPN', '')),
                               'Manufacturer': (fields.get('Manufacturer', ''), fp['properties'].get('Manufacturer', '')),
                               'Value': (c.value, fp['properties'].get('Value', '')),
                               'LCSC': (fields.get('LCSC', ''), fp['properties'].get('LCSC', '')),
                               'dnp': ('dnp' in fields, 'dnp' in fp['attributes']),
                               'exclude_from_bom': ('exclude_from_bom' in fields, 'exclude_from_bom' in fp['attributes'])}
                for field, (wanted, found) in comparisons.items():
                    if wanted != found:
                        discrepancies.append({'ref': c.ref, 'field': field, 'netlist': wanted, 'pcb': found})
        source_refs = {c.ref for c in components}
        extra = {r: fp for r, fp in native.items() if r not in source_refs}
        geometry = sorted(r for r, fp in extra.items() if {'board_only', 'exclude_from_bom', 'exclude_from_pos_files'} <= set(fp['attributes']))
        report_path = selected['connectivity_report']
        if report_path:
            inputs.add(report_path)
        rows = []
        for group, refs in sorted(groups.items(), key=lambda item: str(item[0])):
            disposition, manufacturer, mpn, footprint, lcsc, owner, state = group
            rows.append(dict(disposition=disposition, manufacturer=manufacturer, mpn=mpn,
                             footprint=footprint, supplier_order_code_declared=lcsc, owner_skill=owner,
                             owner_identity_state=state, designators=sorted(refs), quantity=len(refs)))
        total.update(counts)
        units.append({'key': key, 'board_id': board_id, **selected, 'board_sha256': digest(root / board),
                      'definition': definition, 'netlist': netlist, 'counts': dict(sorted(counts.items())),
                      'partition_netlist_membership': membership(expected, source_refs),
                      'netlist_pcb_membership': membership(source_refs | set(geometry), native),
                      'pcb_only_non_procured_geometry': geometry, 'field_discrepancies': discrepancies,
                      'retained_connectivity': retained_connectivity(root, board, report_path), 'parts': rows})
    panel = config['panel']
    inputs.update([panel['board'], panel['native_review'], 'design/panel/panel-params.json', 'design/grid/placements.lock.json'])
    p_report = json.loads((root / panel['native_review']).read_text())
    panel_bound = p_report['inputs'][panel['board']]['sha256']
    all_selected = {u['board'] for u in units} | {panel['board']}
    excluded_pcbs = sorted(str(p.relative_to(root)) for p in (root / 'boards').glob('*/*.kicad_pcb') if str(p.relative_to(root)) not in all_selected)
    discrepancy_count = sum(len(v) for v in source_membership.values()) + sum(
        len(u['field_discrepancies']) + sum(len(v) for v in u['partition_netlist_membership'].values()) +
        sum(len(v) for v in u['netlist_pcb_membership'].values()) for u in units)
    return {'reconciliation': {'status': 'MATCHED DECLARED FIELDS' if discrepancy_count == 0 else 'DISCREPANCIES',
                               'discrepancy_count': discrepancy_count,
                               'unverified': 'Net connectivity, pin/pad correspondence, placements/orientation, electrical behavior and external assembly are not checked by this coverage command'},
            'schema_version': 1, 'status': 'ENGINEERING COVERAGE ONLY; NOT ORDER READY; NOT A MANUFACTURING BOM',
            'scope': 'Offline source and retained-file reconciliation. No new native, physical, availability or assembly acceptance.',
            'source_sha256': {p: digest(root / p) for p in sorted(inputs)},
            'physical_source': {'unique_packages': len(packages), 'fitted_packages': sum(not r['dnp'] and r['in_bom'] for r in packages.values()),
                                'excluded': excluded, 'partition_membership': source_membership},
            'native_population_counts': dict(sorted(total.items())), 'units': units,
            'panel': {**panel, 'board_sha256': digest(root / panel['board']),
                      'retained_board_binding': 'MATCHED BOARD BYTES' if panel_bound == digest(root / panel['board']) else 'STALE'},
            'excluded_board_files': excluded_pcbs, 'assembly': config['assembly'],
            'unresolved': config['unresolved']}


def markdown(report):
    lines = ['# Current instrument readiness', '', report['status'], '', report['scope'], '',
             'Reconciliation: ' + report['reconciliation']['status'] + '; discrepancies: ' + str(report['reconciliation']['discrepancy_count']) + '.', '',
             '| Unit | Disposition | Retained complete native open edges | Identity-declared fitted rows | Incomplete fitted identity rows |',
             '| --- | --- | ---: | ---: | ---: |']
    for u in report['units']:
        evidence = u['retained_connectivity']
        count = evidence.get('complete_native_open_edges') if evidence['status'] == 'MATCHED BOARD BYTES' else 'STALE/UNBOUND'
        lines.append(f"| {u['key']} | {u['adoption']} | {count} | {u['counts'].get('fitted_identity_declared',0)} | {u['counts'].get('fitted_identity_incomplete',0)} |")
    lines += ['', 'The JSON companion contains exact file hashes, designator groups, membership discrepancies and owner identity states. Declared identities are not procurement or performance approval.', '',
              'P remains a geometry candidate. The panel is a separate board-only unit. Experimental, historical single-jack and alternative control files are excluded explicitly.', '',
              '## Open requirements', '']
    lines += ['- ' + row for row in report['unresolved']]
    lines += ['', '## Assembly responsibility', '', *['- ' + row for row in report['assembly']], '']
    return '\n'.join(lines)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    report = build()
    outputs = {OUTPUT: json.dumps(report, indent=2, ensure_ascii=False) + '\n', MARKDOWN: markdown(report)}
    for path, content in outputs.items():
        target = ROOT / path
        if args.check:
            if not target.exists() or target.read_text() != content:
                raise SystemExit('STALE readiness output: ' + path)
        else:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content)
    print('CURRENT coverage report; reconciliation=' + report['reconciliation']['status'] +
          '; discrepancies=' + str(report['reconciliation']['discrepancy_count']) +
          '; engineering/physical/order gates remain OPEN')


if __name__ == '__main__':
    main()
