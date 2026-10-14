"""Bounded raster replay of one pinned #252 case; never edits a PCB.

This creates the existing grid proposal shape for later native/route-shard
review. Its result is evidence about a search, never copper acceptance.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import resource
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from prepare import BOARD, CASES, EXPECTED_DUMP, digest, prepare


def group_hash(members: list[str]) -> str:
    packed = json.dumps(sorted(members), separators=(",", ":")).encode()
    return hashlib.sha256(packed).hexdigest()


def replay(dump_path: Path, case_key: str, resolution: float) -> dict:
    manifest = prepare()
    case = next((row for row in manifest["cases"] if row["case"] == case_key), None)
    if case is None:
        raise ValueError(f"unknown case {case_key}")
    if digest(dump_path) != EXPECTED_DUMP:
        raise ValueError("full accepted K1402 dump absent or wrong SHA256")
    dump = json.loads(dump_path.read_text())
    if dump["board_sha256"] != manifest["retained_native_settled_board_sha256"]:
        raise ValueError("dump is not the pinned settled K board")
    groups = dump["islands"][case["net"]]
    source = [g for g in groups if group_hash(g) == case["source_group_sha256"]]
    if len(source) != 1:
        raise ValueError("source group absent or ambiguous in full dump")
    source = source[0]
    if case["source_pad"]["uuid"] not in source:
        raise ValueError("case pad is absent from selected native group")
    main = max((g for g in groups if g != source), key=len)
    if not main:
        raise ValueError("no existing target group")
    pad = case["source_pad"]
    x, y = (v / 1_000_000 for v in pad["xy"])
    bounds = [x - 6, y - 6, x + 6, y + 6]

    # Delay router imports until after provenance checks. A missing archive
    # must fail before any expensive geometry is built.
    from scripts.pcbgen.grid_router import copper_rows, route
    from scripts.pcbgen.route_jack_grid import (
        LAYER_COST, RAILS, SIGNAL_LAYERS, neck_kwargs,
    )

    search = {**dump, "islands": {case["net"]: [source] if case["net"] == "AGND" else [main, source]}}
    common = dict(
        res=resolution, clearance=.25, allowed_layers=SIGNAL_LAYERS,
        layer_cost=LAYER_COST, rail_nets=RAILS,
        fill_guards={"-12V": "In3.Cu"}, window_mm=6,
        max_expansions=300_000, bounds_mm=bounds,
        **neck_kwargs("osc-core"),
    )
    if case["net"] == "AGND":
        common.update(rail_width=.3, via_diameter=.6, planes={"AGND": "In1.Cu"})
    elif case["net"] in ("+12V", "-12V"):
        common.update(rail_width=.25)
    else:
        common.update(signal_width=.2, signal_via_diameter=.6,
                      grow={n: .05 for n in [*RAILS, "AGND"]})
    events = []
    started = time.monotonic()
    results, removed = route(search, [case["net"]], diagnostics=events, **common)
    rows, _ = copper_rows(results, "osc-core", f"epic242-252-{case_key}-{resolution}")
    if removed:
        raise ValueError("bounded additive screen unexpectedly removed original copper")
    complete = bool(rows) and all(row.get("path") for row in results)
    return {
        "status": "RASTER SCREEN ONLY; NATIVE NOT RUN",
        "case": case_key, "resolution_mm": resolution,
        "input_native_dump_sha256": digest(dump_path),
        "published_board_sha256": digest(BOARD),
        "router_sha256": digest(ROOT / "scripts/pcbgen/grid_router.py"),
        "route_entry_sha256": digest(ROOT / "scripts/pcbgen/route_jack_grid.py"),
        "elapsed_seconds": time.monotonic() - started,
        "peak_rss_kib": resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
        "bounds_mm": bounds,
        "diagnostics": events,
        "complete_raster_path": complete,
        "results": results,
        "proposal": {
            "board_sha256": manifest["published_board_sha256"],
            "removed_uuids": [], "copper": rows,
        },
        "acceptance": "NOT RUN: requires coupled rail/AGND transaction, native checks and coordinator adoption",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dump", type=Path, required=True)
    parser.add_argument("--case", choices=[row[0] for row in CASES], required=True)
    parser.add_argument("--resolution", type=float, choices=[.025, .0125], default=.025)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = replay(args.dump, args.case, args.resolution)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(args.output, digest(args.output), result["complete_raster_path"])
