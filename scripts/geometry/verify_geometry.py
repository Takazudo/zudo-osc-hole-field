#!/usr/bin/env python3
"""Compare the generated placement lock with the R21 panel SVG geometry."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
import hashlib
import json
from pathlib import Path
import sys
import xml.etree.ElementTree as ET
from typing import Any

from panel_frame import (
    GRID_RELATIVE_PATH,
    PANEL_SVG_RELATIVE_PATH,
    PLACEMENTS_RELATIVE_PATH,
    PROVENANCE_RELATIVE_PATH,
    REPO_ROOT,
)


class GeometryMismatch(ValueError):
    """Raised when a placement centre differs from the handoff SVG."""


def _local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def _coordinate(x: str | float, y: str | float) -> tuple[str, str]:
    return (f"{float(x):.4f}", f"{float(y):.4f}")


def _svg_geometry(svg_path: Path) -> tuple[dict[str, list[tuple[str, str]]], Counter]:
    root = ET.parse(svg_path).getroot()
    if root.attrib.get("viewBox") != "0 0 318 298":
        raise GeometryMismatch(
            f"unexpected panel SVG viewBox: {root.attrib.get('viewBox')!r}"
        )

    hardware: dict[str, list[tuple[str, str]]] = defaultdict(list)
    for group in root.iter():
        if _local_name(group.tag) != "g" or "item" not in group.attrib.get("class", "").split():
            continue
        uid = group.attrib.get("data-id")
        if not uid:
            raise GeometryMismatch("panel item group has no data-id")
        focus = [
            circle
            for circle in group.iter()
            if _local_name(circle.tag) == "circle"
            and "focus" in circle.attrib.get("class", "").split()
        ]
        if len(focus) != 1:
            raise GeometryMismatch(f"{uid}: expected one focus circle, found {len(focus)}")
        hardware[uid].append(_coordinate(focus[0].attrib["cx"], focus[0].attrib["cy"]))

    leds: Counter = Counter()
    for circle in root.iter():
        if _local_name(circle.tag) != "circle":
            continue
        if "data-led" in circle.attrib or "data-stage" in circle.attrib:
            leds[_coordinate(circle.attrib["cx"], circle.attrib["cy"])] += 1
    return hardware, leds


def _counter_difference(expected: Counter, actual: Counter, limit: int = 8) -> str:
    missing = list((expected - actual).elements())[:limit]
    extra = list((actual - expected).elements())[:limit]
    return f"missing centres={missing}; extra centres={extra}"


def verify_geometry(lock: dict[str, Any], svg_path: Path) -> tuple[int, int]:
    """Verify hardware centres by uid and indicator centres as a multiset."""

    placements = lock.get("placements")
    if not isinstance(placements, list):
        raise GeometryMismatch("placement lock has no placements list")

    hardware_records = [record for record in placements if record.get("kind") != "led"]
    led_records = [record for record in placements if record.get("kind") == "led"]
    if len(hardware_records) != 324:
        raise GeometryMismatch(f"expected 324 hardware records, found {len(hardware_records)}")
    if len(led_records) != 114:
        raise GeometryMismatch(f"expected 114 LED records, found {len(led_records)}")

    svg_hardware, svg_leds = _svg_geometry(svg_path)
    expected_uids = [record["uid"] for record in hardware_records]
    if len(set(expected_uids)) != len(expected_uids):
        raise GeometryMismatch("placement lock contains duplicate hardware uids")
    if set(svg_hardware) != set(expected_uids):
        missing = sorted(set(expected_uids) - set(svg_hardware))
        extra = sorted(set(svg_hardware) - set(expected_uids))
        raise GeometryMismatch(f"hardware uid set differs; missing={missing[:8]}, extra={extra[:8]}")

    hardware_mismatches = []
    for record in hardware_records:
        uid = record["uid"]
        centers = svg_hardware[uid]
        if len(centers) != 1:
            raise GeometryMismatch(f"{uid}: duplicate SVG focus centres: {centers}")
        expected = _coordinate(record["x_mm"], record["y_mm"])
        if expected != centers[0]:
            hardware_mismatches.append((uid, expected, centers[0]))
    if hardware_mismatches:
        raise GeometryMismatch(
            f"{len(hardware_mismatches)} hardware centres differ; "
            f"first mismatches={hardware_mismatches[:8]}"
        )

    expected_leds = Counter(
        _coordinate(record["x_mm"], record["y_mm"]) for record in led_records
    )
    if len(svg_leds) != 114:
        raise GeometryMismatch(f"expected 114 SVG LED markers, found {len(svg_leds)}")
    if expected_leds != svg_leds:
        raise GeometryMismatch(_counter_difference(expected_leds, svg_leds))
    return (len(hardware_records), len(led_records))


def validate_source_pin(lock: dict[str, Any], root: Path = REPO_ROOT) -> None:
    source = lock.get("source", {})
    if source.get("grid") != GRID_RELATIVE_PATH.as_posix():
        raise GeometryMismatch(f"unexpected source grid path: {source.get('grid')!r}")
    provenance = json.loads((root / PROVENANCE_RELATIVE_PATH).read_text(encoding="utf-8"))
    pinned = provenance["grid"]["renamed_sha256"]
    actual = hashlib.sha256((root / GRID_RELATIVE_PATH).read_bytes()).hexdigest()
    if source.get("sha256") != pinned or actual != pinned:
        raise GeometryMismatch(
            "placement lock, rename provenance, and grid SHA-256 do not agree: "
            f"lock={source.get('sha256')}, provenance={pinned}, grid={actual}"
        )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--lock", type=Path, default=REPO_ROOT / PLACEMENTS_RELATIVE_PATH)
    parser.add_argument("--svg", type=Path, default=REPO_ROOT / PANEL_SVG_RELATIVE_PATH)
    args = parser.parse_args(argv)
    try:
        lock = json.loads(args.lock.read_text(encoding="utf-8"))
        validate_source_pin(lock)
        hardware_count, led_count = verify_geometry(lock, args.svg)
    except (OSError, KeyError, ValueError, json.JSONDecodeError, ET.ParseError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    print(f"PASS: {hardware_count} hardware centres match panel.svg focus circles")
    print(f"PASS: {led_count} LED centres match panel.svg as a multiset")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
