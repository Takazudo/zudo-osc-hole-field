#!/usr/bin/env python3
"""Assert the smoke loop's ERC, schematic parity, and export results."""

from __future__ import annotations

import json
import sys
from pathlib import Path


def count_report_items(value) -> int | None:
    if isinstance(value, list):
        return len(value)
    if isinstance(value, int):
        return value
    if isinstance(value, dict):
        for key in ("count", "total", "items", "violations", "issues"):
            if key in value:
                count = count_report_items(value[key])
                if count is not None:
                    return count
        return None
    return None


def report_count(report: dict, keys: tuple[str, ...]) -> int:
    counts = []

    def visit(value):
        if isinstance(value, dict):
            for key in keys:
                if key in value:
                    count = count_report_items(value[key])
                    if count is not None:
                        counts.append(count)
            for child in value.values():
                visit(child)
        elif isinstance(value, list):
            for child in value:
                visit(child)

    visit(report)
    if not counts:
        raise ValueError(f"KiCad JSON report is missing expected fields: {', '.join(keys)}")
    return sum(counts)


def main() -> int:
    if len(sys.argv) != 5:
        print("Usage: check_reports.py <ERC.json> <DRC.json> <SVG> <PNG>", file=sys.stderr)
        return 2
    erc_path, drc_path, svg_path, png_path = map(Path, sys.argv[1:])
    try:
        erc = json.loads(erc_path.read_text(encoding="utf-8"))
        drc = json.loads(drc_path.read_text(encoding="utf-8"))
        erc_count = report_count(erc, ("violations",))
        parity_count = report_count(
            drc,
            (
                "schematic_parity",
                "schematic_parity_issues",
                "schematic_parity_issue_count",
                "parity_issues",
            ),
        )
    except (OSError, json.JSONDecodeError, ValueError) as error:
        print(f"Smoke report check failed: {error}", file=sys.stderr)
        return 1

    failures = []
    if erc_count != 0:
        failures.append(f"ERC reported {erc_count} violation(s)")
    if parity_count != 0:
        failures.append(f"PCB parity reported {parity_count} issue(s)")
    for path, label in ((svg_path, "SVG"), (png_path, "PNG")):
        if not path.is_file() or path.stat().st_size == 0:
            failures.append(f"{label} export is missing or empty: {path}")
    if failures:
        print("Smoke report check failed: " + "; ".join(failures), file=sys.stderr)
        return 1
    print("Smoke reports: ERC 0 violations; PCB parity 0 issues")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
