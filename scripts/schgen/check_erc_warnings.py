#!/usr/bin/env python3
"""Compare master ERC warnings by sheet, type, description, and pin identities."""
from __future__ import annotations

from collections import Counter
import json
from pathlib import Path
import sys
import hashlib

ROOT = Path(__file__).resolve().parents[2]
BASELINE = ROOT / 'design/reports/master-erc-warning-baseline.json'


def warning_identity(path: str, violation: dict) -> dict:
    return {
        'sheet_path': path,
        'severity': violation['severity'],
        'type': violation['type'],
        'description': violation['description'],
        'items': sorted(item['description'] for item in violation.get('items', [])),
    }


def canonical_warnings(report: dict) -> list[dict]:
    return sorted(
        (warning_identity(sheet['path'], violation)
         for sheet in report['sheets']
         for violation in sheet.get('violations', [])
         if violation.get('severity') == 'warning'),
        key=lambda item: json.dumps(item, sort_keys=True, separators=(',', ':')),
    )


def main() -> int:
    if len(sys.argv) != 2:
        print('Usage: python3 scripts/schgen/check_erc_warnings.py <erc-report.json>', file=sys.stderr)
        return 2
    actual_report = json.loads(Path(sys.argv[1]).read_text())
    baseline = json.loads(BASELINE.read_text())
    violations = [v for sheet in actual_report['sheets'] for v in sheet.get('violations', [])]
    errors = [v for v in violations if v.get('severity') == 'error']
    actual = canonical_warnings(actual_report)
    expected = baseline['warnings']
    expected_counts = baseline['warnings_by_sheet']
    inventory_digest = hashlib.sha256(json.dumps(
        expected, sort_keys=True, separators=(',', ':')
    ).encode()).hexdigest()
    actual_counts = dict(sorted(Counter(item['sheet_path'] for item in actual).items()))
    if actual_report.get('kicad_version') != baseline['kicad_version']:
        raise SystemExit(f"ERC oracle changed: {actual_report.get('kicad_version')} != {baseline['kicad_version']}")
    if baseline.get('warning_inventory_sha256') != inventory_digest:
        raise SystemExit('ERC warning baseline inventory checksum is invalid')
    if errors:
        raise SystemExit(f'instrument ERC has {len(errors)} error(s): {errors[:3]}')
    if len(violations) != len(actual):
        raise SystemExit('instrument ERC contains a non-warning finding outside the retained baseline')
    if len(actual) != baseline['warning_count'] or actual_counts != expected_counts:
        raise SystemExit(f'warning count/path drift: {len(actual)} and {actual_counts} != {baseline["warning_count"]} and {expected_counts}')
    if actual != expected:
        expected_set = {json.dumps(x, sort_keys=True, separators=(',', ':')) for x in expected}
        actual_set = {json.dumps(x, sort_keys=True, separators=(',', ':')) for x in actual}
        missing = sorted(expected_set - actual_set)
        added = sorted(actual_set - expected_set)
        raise SystemExit(f'ERC warning identities changed: missing={missing[:3]}, added={added[:3]}')
    if any(item['type'] != 'pin_to_pin' for item in actual):
        raise SystemExit('ERC warning class changed; review the new warning type')
    print(f"PASS: instrument ERC zero errors; {len(actual)} exact pin_to_pin warning identities match the KiCad {baseline['kicad_version']} baseline")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
