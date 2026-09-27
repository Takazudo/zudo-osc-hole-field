#!/usr/bin/env python3
"""Build the deterministic 438-feature R21 placement lockfile."""

from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import sys
from typing import Any

from panel_frame import (
    COLS,
    CTRL_ROWS,
    GRID_RELATIVE_PATH,
    HOLE_DIAMETERS_MM,
    JACK_ROWS,
    KICAD_OX,
    KICAD_OY,
    LED_OFFSETS,
    PANEL_H,
    PANEL_W,
    PLACEMENTS_RELATIVE_PATH,
    PROPOSAL_STATUS,
    PROVENANCE_RELATIVE_PATH,
    REPO_ROOT,
    board_domain,
    cell_center,
    hole_diameter_mm,
    reference_designator,
    slug_uid,
)


EXPECTED_POT_COMPONENTS = {
    "bourns-ptv09a-4020f-b103": 99,  # 10 kOhm in the handoff inventory.
    "bourns-ptv09a-4020f-b504": 2,  # 500 kOhm in the handoff inventory.
}
EXPECTED_LED_COUNTS = {"mag": 92, "stage": 12, "clip": 10}


class StaleLockError(ValueError):
    """Raised when --check finds bytes different from the generated lock."""


def _read_authority(root: Path) -> tuple[dict[str, Any], str]:
    grid_path = root / GRID_RELATIVE_PATH
    provenance_path = root / PROVENANCE_RELATIVE_PATH
    grid_bytes = grid_path.read_bytes()
    provenance = json.loads(provenance_path.read_text(encoding="utf-8"))
    expected_sha256 = provenance["grid"]["renamed_sha256"]
    actual_sha256 = hashlib.sha256(grid_bytes).hexdigest()
    if actual_sha256 != expected_sha256:
        raise ValueError(
            "R21 grid does not match rename provenance: "
            f"expected {expected_sha256}, got {actual_sha256}"
        )
    grid = json.loads(grid_bytes.decode("utf-8"))
    return grid, actual_sha256


def _validate_grid_counts(grid: dict[str, Any]) -> None:
    if (grid.get("columns"), grid.get("jack_rows"), grid.get("control_rows")) != (
        COLS,
        JACK_ROWS,
        CTRL_ROWS,
    ):
        raise ValueError("grid dimensions do not match the locked panel frame")

    ports = grid.get("ports", [])
    controls = grid.get("controls", [])
    if len(ports) != 180:
        raise ValueError(f"expected 180 jacks, found {len(ports)}")
    direction_counts = Counter(item.get("direction") for item in ports)
    if direction_counts != Counter({"in": 98, "out": 82}):
        raise ValueError(f"unexpected jack directions: {dict(direction_counts)}")
    if len(controls) != 144:
        raise ValueError(f"expected 144 controls, found {len(controls)}")

    control_kinds = Counter(item.get("kind") for item in controls)
    expected_control_kinds = Counter({"pot": 101, "octave": 5, "switch": 30, "button": 8})
    if control_kinds != expected_control_kinds:
        raise ValueError(f"unexpected control kinds: {dict(control_kinds)}")

    pots = [item for item in controls if item.get("kind") == "pot"]
    pot_components = Counter(item.get("component") for item in pots)
    if pot_components != Counter(EXPECTED_POT_COMPONENTS):
        raise ValueError(f"unexpected pot component/value counts: {dict(pot_components)}")

    toggle_positions = Counter(
        len(item.get("positions", [])) for item in controls if item.get("kind") == "switch"
    )
    if toggle_positions != Counter({2: 19, 3: 11}):
        raise ValueError(f"unexpected toggle position counts: {dict(toggle_positions)}")

    led_counts = Counter()
    for item in ports:
        if item.get("led"):
            led_counts["mag"] += 1
        if item.get("clip"):
            led_counts["clip"] += 1
    for item in controls:
        if item.get("stage"):
            led_counts["stage"] += 1
    if led_counts != Counter(EXPECTED_LED_COUNTS):
        raise ValueError(f"unexpected LED counts: {dict(led_counts)}")


def _hardware_record(item: dict[str, Any], family: str) -> dict[str, Any]:
    field = item["field"]
    kind = item["kind"]
    col = item["col"]
    row = item["row"]
    x_mm, y_mm = cell_center(field, col, row)
    diameter = hole_diameter_mm(kind)
    if diameter is None:
        raise ValueError(f"no preview hole diameter for hardware kind {kind!r}")

    record: dict[str, Any] = {
        "uid": item["uid"],
        "slug": slug_uid(item["uid"]),
        "ref": reference_designator(field, kind, col, row),
        "kind": kind,
        "block": item["block"],
        "family": family,
        "key": item["key"],
        "label": item["label"],
        "field": field,
        "col": col,
        "row": row,
        "x_mm": x_mm,
        "y_mm": y_mm,
        "rot_deg": item.get("rot_deg", item.get("rotation_deg", 0)),
        "domain": board_domain(field, item["block"], kind),
        "domain_status": PROPOSAL_STATUS,
        "accent": bool(item.get("accent", False)),
        "hole_d_mm": diameter,
        "hole_status": PROPOSAL_STATUS,
        "component": item["component"],
    }
    if "direction" in item:
        record["direction"] = item["direction"]
    return record


def _led_records(item: dict[str, Any], parent: dict[str, Any]) -> list[dict[str, Any]]:
    led_types: list[str] = []
    if item["field"] == "jacks":
        if item.get("led"):
            led_types.append("mag")
        if item.get("clip"):
            led_types.append("clip")
    elif item.get("stage"):
        led_types.append("stage")

    records = []
    for led_type in led_types:
        dx, dy = LED_OFFSETS[led_type]
        uid = f"L:{item['block']}.{item['key']}.{led_type}"
        records.append(
            {
                "uid": uid,
                "slug": slug_uid(uid),
                "ref": reference_designator(
                    item["field"],
                    "led",
                    item["col"],
                    item["row"],
                    led_type=led_type,
                ),
                "kind": "led",
                "led_type": led_type,
                "parent": item["uid"],
                "block": parent["block"],
                "family": parent["family"],
                "key": parent["key"],
                "label": parent["label"],
                "field": parent["field"],
                "col": parent["col"],
                "row": parent["row"],
                "x_mm": parent["x_mm"] + dx,
                "y_mm": parent["y_mm"] + dy,
                "rot_deg": parent["rot_deg"],
                "domain": parent["domain"],
                "domain_status": parent["domain_status"],
                "offset_x_mm": dx,
                "offset_y_mm": dy,
            }
        )
    return records


def _validate_records(records: list[dict[str, Any]]) -> None:
    if len(records) != 438:
        raise ValueError(f"expected 438 total features, found {len(records)}")

    for field in ("uid", "slug", "ref"):
        values = [record[field] for record in records]
        duplicates = [value for value, count in Counter(values).items() if count > 1]
        if duplicates:
            raise ValueError(f"duplicate {field} values: {duplicates[:10]}")

    feature_counts = Counter(record["kind"] for record in records)
    expected = Counter({
        "jack": 180,
        "pot": 101,
        "octave": 5,
        "switch": 30,
        "button": 8,
        "led": 114,
    })
    if feature_counts != expected:
        raise ValueError(f"unexpected feature counts: {dict(feature_counts)}")

    led_counts = Counter(
        record["led_type"] for record in records if record["kind"] == "led"
    )
    if led_counts != Counter(EXPECTED_LED_COUNTS):
        raise ValueError(f"unexpected generated LED types: {dict(led_counts)}")


def build_lock(root: Path = REPO_ROOT) -> dict[str, Any]:
    """Read the pinned grid and build all hardware and indicator placements."""

    grid, grid_sha256 = _read_authority(root)
    _validate_grid_counts(grid)
    blocks = grid.get("blocks", {})
    if not isinstance(blocks, dict):
        raise ValueError("grid blocks must be an object keyed by block id")

    source_items = [*grid["ports"], *grid["controls"]]
    records: list[dict[str, Any]] = []
    seen_uids: set[str] = set()
    for item in source_items:
        uid = item["uid"]
        if uid in seen_uids:
            raise ValueError(f"duplicate source uid: {uid}")
        seen_uids.add(uid)
        if item["field"] not in {"jacks", "controls"}:
            raise ValueError(f"unexpected field on {uid}: {item['field']!r}")
        block = item["block"]
        try:
            family = blocks[block]["family"]
        except KeyError as exc:
            raise ValueError(f"grid block {block!r} has no family") from exc
        hardware = _hardware_record(item, family)
        records.append(hardware)
        records.extend(_led_records(item, hardware))

    records.sort(
        key=lambda record: (
            record["field"],
            record["col"],
            record["row"],
            record["family"],
            record["uid"],
        )
    )
    _validate_records(records)

    return {
        "schema_version": 1,
        "source": {
            "grid": GRID_RELATIVE_PATH.as_posix(),
            "sha256": grid_sha256,
        },
        "frame": {
            "units": "mm",
            "origin": "panel front top-left",
            "positive_x": "right",
            "positive_y": "down",
            "panel_width_mm": PANEL_W,
            "panel_height_mm": PANEL_H,
            "kicad_translation_mm": {"x": KICAD_OX, "y": KICAD_OY},
        },
        "placements": records,
    }


def render_json(value: Any, level: int = 0) -> str:
    """Serialize stable, two-space JSON with all floats fixed to four places."""

    indent = "  "
    prefix = indent * level
    child_prefix = indent * (level + 1)
    if isinstance(value, dict):
        if not value:
            return "{}"
        parts = [
            f"{child_prefix}{json.dumps(str(key), ensure_ascii=False)}: "
            f"{render_json(item, level + 1)}"
            for key, item in value.items()
        ]
        return "{\n" + ",\n".join(parts) + f"\n{prefix}}}"
    if isinstance(value, list):
        if not value:
            return "[]"
        parts = [f"{child_prefix}{render_json(item, level + 1)}" for item in value]
        return "[\n" + ",\n".join(parts) + f"\n{prefix}]"
    if isinstance(value, str):
        return json.dumps(value, ensure_ascii=False)
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, int):
        return str(value)
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError(f"non-finite number cannot be written to JSON: {value!r}")
        return f"{value:.4f}"
    raise TypeError(f"unsupported JSON value: {type(value).__name__}")


def lock_bytes(lock: dict[str, Any]) -> bytes:
    return (render_json(lock) + "\n").encode("utf-8")


def write_or_check(path: Path, lock: dict[str, Any], check: bool = False) -> bool:
    """Write the lock, or compare it byte-for-byte in check mode."""

    expected = lock_bytes(lock)
    if check:
        if not path.is_file() or path.read_bytes() != expected:
            raise StaleLockError(
                f"{path} is stale; run `bash scripts/geometry/regen.sh` to rebuild it"
            )
        return False
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(expected)
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail if the committed placement lock is not byte-for-byte current",
    )
    args = parser.parse_args(argv)
    output = REPO_ROOT / PLACEMENTS_RELATIVE_PATH
    try:
        lock = build_lock()
        wrote = write_or_check(output, lock, check=args.check)
    except (OSError, KeyError, ValueError, json.JSONDecodeError) as exc:
        print(f"FAIL: {exc}", file=sys.stderr)
        return 1

    if args.check:
        print(f"PASS: placement lock matches {len(lock['placements'])} generated features")
    elif wrote:
        print(f"WROTE: {output.relative_to(REPO_ROOT)} ({len(lock['placements'])} features)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
