"""Pin #252 cases to the retained, accepted K1402 endpoint snapshot.

This is a source-only projection. A pad-neighbour is not a legal route target;
the full native dump and the existing route-shard gates decide that later.
"""
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from scripts.pcbgen.trimmer_labels import _children, _property

HERE = Path(__file__).resolve().parent
ENDPOINTS = ROOT / "circuit/routing/epic-242/baseline/k-endpoints.json"
BOARD = ROOT / "boards/osc-core/osc-core.kicad_pcb"
EXPECTED_BOARD = "fa60b4e1587a67501782fb55374f0e5d5133f65cd0bbe62624aef502441fda10"
EXPECTED_DUMP = "5218becd38f6bb612f9a169230bd8e6657776a09fc12af5baa6113825e671ffb"

# Covers both packages/rails, the historically unattempted oscillator cluster,
# one coupled signal/return interaction, and an oscillator reference region.
CASES = (
    ("opa-osc-plus", "+12V", "U1602", "4", "OPA4197IPWR"),
    ("opa-osc-minus", "-12V", "U1602", "11", "OPA4197IPWR"),
    ("opa-osc-neighbour-plus", "+12V", "U1603", "4", "OPA4197IPWR"),
    ("opa-osc-neighbour-minus", "-12V", "U1604", "11", "OPA4197IPWR"),
    ("adg-filter-plus", "+12V", "U4206", "13", "ADG5412FBRUZ"),
    ("adg-filter-minus", "-12V", "U4206", "4", "ADG5412FBRUZ"),
    ("adg-filter-return", "AGND", "U4206", "5", "ADG5412FBRUZ"),
    ("adg-filter-signal", "XD9992CFFE3B9C146B5E5", "U4206", "3", "ADG5412FBRUZ"),
    ("filter-reference-return", "AGND", "U4231", "7", None),
)


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def packages() -> dict[str, str]:
    result = {}
    for _, _, block in _children(BOARD.read_text()):
        if block.startswith("(footprint "):
            ref = _property(block, "Reference")
            if ref in {case[2] for case in CASES}:
                if ref in result:
                    raise ValueError(f"duplicate footprint {ref}")
                result[ref] = _property(block, "Value")
    return result


def prepare() -> dict:
    if digest(BOARD) != EXPECTED_BOARD:
        raise ValueError("published K changed; obtain a new accepted baseline")
    snapshot = json.loads(ENDPOINTS.read_text())
    if snapshot["dump_sha256"] != EXPECTED_DUMP or snapshot["native_open_edges"] != 1402:
        raise ValueError("retained K endpoint snapshot changed")
    values = packages()
    rows = []
    for key, net, ref, pad, expected_value in CASES:
        if expected_value and values.get(ref) != expected_value:
            raise ValueError(f"wrong exact package for {ref}")
        groups = snapshot["disconnected_nets"][net]
        matches = [(i, group, member) for i, group in enumerate(groups)
                   for member in group["pads"]
                   if (member["ref"], member["pad"]) == (ref, pad)]
        if len(matches) != 1:
            raise ValueError(f"expected one retained pad: {net} {ref}.{pad}")
        index, group, member = matches[0]
        if net in ("+12V", "-12V") and group["all_member_count"] != 1:
            raise ValueError(f"rail source no longer isolated: {ref}.{pad}")
        others = [g for g in groups if g is not group]
        main = max(others, key=lambda g: g["all_member_count"])
        # Candidates are geometry context only. A legal terminal requires the
        # full saved dump's copper, pad polygons, fill and clearance rules.
        neighbours = sorted(
            (p for g in others for p in g["pads"]),
            key=lambda p: ((p["xy"][0]-member["xy"][0])**2
                           +(p["xy"][1]-member["xy"][1])**2,
                           p["ref"], p["pad"], p["uuid"]),
        )[:5]
        main_neighbours = sorted(
            main["pads"],
            key=lambda p: ((p["xy"][0]-member["xy"][0])**2
                           +(p["xy"][1]-member["xy"][1])**2,
                           p["ref"], p["pad"], p["uuid"]),
        )[:5]
        rows.append({
            "case": key, "net": net, "package": expected_value or values.get(ref),
            "source_group_index": index,
            "source_group_member_count": group["all_member_count"],
            "source_group_sha256": group["all_sorted_members_sha256"],
            "source_group_pads": group["pads"],
            "source_pad": member,
            "largest_other_group_member_count": main["all_member_count"],
            "largest_other_group_sha256": main["all_sorted_members_sha256"],
            "nearby_largest_other_group_pads_not_proven_targets": main_neighbours,
            "nearby_other_group_pads_not_proven_targets": neighbours,
        })
    return {
        "schema_version": 1,
        "status": "SOURCE PREPARATION ONLY; NO NATIVE OR RASTER ACCEPTANCE",
        "baseline_epoch": "epic242-e0",
        "integration_parent_sha": "40aa1cec58190487dc70aa5048a366e29a6b32a1",
        "published_board_sha256": digest(BOARD),
        "retained_endpoint_snapshot_sha256": digest(ENDPOINTS),
        "retained_native_dump_sha256": EXPECTED_DUMP,
        "retained_native_settled_board_sha256": snapshot["settled_board_sha256"],
        "retained_context_manifest_sha256": snapshot["context_file_manifest_sha256"],
        "retained_artifact_archive_digest": snapshot["archive_digest"],
        "accepted_native_source_sha": snapshot["source_sha"],
        "router_sha256": digest(ROOT / "scripts/pcbgen/grid_router.py"),
        "route_entry_sha256": digest(ROOT / "scripts/pcbgen/route_jack_grid.py"),
        "grid_apply_sha256": digest(ROOT / "scripts/pcbgen/grid_apply.py"),
        "route_shards_sha256": digest(ROOT / "scripts/pcbgen/route_shards.py"),
        "accepted_run_id": snapshot["run_id"],
        "accepted_artifact_id": snapshot["artifact_id"],
        "native_open_edges": snapshot["native_open_edges"],
        "cases": rows,
    }


if __name__ == "__main__":
    output = HERE / "cases.json"
    output.write_text(json.dumps(prepare(), indent=2, sort_keys=True) + "\n")
    print(output.relative_to(ROOT), digest(output))
