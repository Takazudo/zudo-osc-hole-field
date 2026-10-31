#!/usr/bin/env python3
"""Instrument BOM identity and price coverage for the A/B readiness matrix.

Counts physical placements from the generated instrument specification (one
package per multi-unit IC). It is a coverage report, not a fabrication BOM: no
order file, supplier code inference or price lookup is performed.
"""
import argparse
import collections
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from design.spec.instrument import specification  # noqa: E402

OUTPUT = ROOT / 'design/readiness/bom-readiness.json'
LOT = 5


def build():
    families, instances = specification()
    copies = collections.Counter(i.family for i in instances)
    inventory = json.loads((ROOT / '.claude/skills/component-spec-audit/references/inventory.json').read_text())
    owners = {line['mpn']: line['owner_skill'] for line in inventory['lines']}
    lines = collections.defaultdict(lambda: {'qty_per_unit': 0, 'lcsc': set(), 'manufacturer': set()})
    value_only = collections.Counter()
    placements = 0
    for family in families:
        packages = {}
        for part in family.parts:
            stem = part.key.rsplit('.', 1)[0] if part.prefix == 'U' else part.key
            packages.setdefault(stem, part)
        for part in packages.values():
            if part.abstract or not part.in_bom or part.dnp:
                continue
            n = copies[family.name]
            placements += n
            mpn = part.attributes.get('MPN', '')
            if not mpn:
                value_only[f'{part.prefix} {part.value}'] += n
                continue
            row = lines[mpn]
            row['qty_per_unit'] += n
            if part.attributes.get('LCSC'):
                row['lcsc'].add(part.attributes['LCSC'])
            row['manufacturer'].add(part.attributes.get('Manufacturer', ''))
    rows = []
    for mpn, row in sorted(lines.items(), key=lambda x: (-x[1]['qty_per_unit'], x[0])):
        rows.append({'mpn': mpn, 'manufacturer': '|'.join(sorted(row['manufacturer'])),
                     'lcsc': '|'.join(sorted(row['lcsc'])) or None,
                     'owner_skill': owners.get(mpn),
                     'qty_per_unit': row['qty_per_unit'], 'qty_per_lot': row['qty_per_unit'] * LOT,
                     'unit_price': 'UNKNOWN', 'stock': 'UNKNOWN'})
    exact = sum(r['qty_per_unit'] for r in rows)
    return {
        'schema_version': 1,
        'status': 'COVERAGE REPORT ONLY; not a fabrication BOM, quote or order file',
        'lot_units': LOT,
        'placements_per_unit': placements,
        'exact_mpn_placements_per_unit': exact,
        'value_only_placements_per_unit': sum(value_only.values()),
        'exact_mpn_lines': len(rows),
        'lines_with_lcsc': sum(1 for r in rows if r['lcsc']),
        'lines_without_owner_skill': [r['mpn'] for r in rows if not r['owner_skill']],
        'price_evidence': 'No retained OSC price evidence; every unit price is UNKNOWN',
        'lines': rows,
        'value_only': [{'part': k, 'qty_per_unit': v, 'qty_per_lot': v * LOT}
                       for k, v in sorted(value_only.items(), key=lambda x: (-x[1], x[0]))],
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    text = json.dumps(build(), indent=1, ensure_ascii=False) + '\n'
    if args.check:
        if not OUTPUT.exists() or OUTPUT.read_text() != text:
            raise SystemExit('bom-readiness.json is stale')
        print('PASS: bom-readiness.json current')
        return
    OUTPUT.write_text(text)
    report = json.loads(text)
    print(f"placements {report['placements_per_unit']}, exact {report['exact_mpn_placements_per_unit']}, "
          f"value-only {report['value_only_placements_per_unit']}, lines {report['exact_mpn_lines']}, "
          f"LCSC {report['lines_with_lcsc']}")


if __name__ == '__main__':
    main()
