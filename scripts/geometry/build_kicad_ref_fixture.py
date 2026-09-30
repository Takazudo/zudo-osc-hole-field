#!/usr/bin/env python3
"""Render a KiCad schematic fixture from the ten generated clip LED references."""

from __future__ import annotations

import argparse
from pathlib import Path
import sys

from build_placements import build_lock
from panel_frame import REPO_ROOT, cell_number

sys.path.insert(0, str(REPO_ROOT))
from design.spec.cells._builder import load_symbol  # noqa: E402
from scripts.schgen.core import Family, Instance, Part, render  # noqa: E402


def build_fixture(output_dir: Path, *, legacy_suffix: bool = False) -> None:
    clip_leds = [
        row for row in build_lock(REPO_ROOT)["placements"]
        if row.get("led_type") == "clip"
    ]
    if len(clip_leds) != 10:
        raise ValueError(f"expected ten clip LED references, found {len(clip_leds)}")

    symbol = load_symbol("0603Whitelight_C2290")
    parts = tuple(
        Part(
            key=f"CLIP_LED_{ordinal}",
            symbol=symbol.lib_id,
            prefix="D",
            ordinal=ordinal,
            unit=0,
            x=55.0 + ((ordinal - 1) % 5) * 25.4,
            y=55.0 + ((ordinal - 1) // 5) * 25.4,
            pins={"1": f"LED{ordinal}_A", "2": f"LED{ordinal}_K"},
            value="clip reference fixture",
            attributes={
                "Role": "geometry:clip-reference-fixture",
                "MPN": "",
                "Manufacturer": "",
                "LCSC": "",
                "PanelUid": "",
                "Island": "",
            },
            panel_ref=(f"D{cell_number(row['col'], row['row'])}A" if legacy_suffix else row["ref"]),
        )
        for ordinal, row in enumerate(clip_leds, start=1)
    )
    generated = render(
        (Family("clip_ref_fixture", parts),),
        (Instance("clip_ref_fixture", "CLIPFIX", 998),),
        {symbol.lib_id: symbol},
        project="clip-ref-fixture",
    )
    for relative, body in generated.items():
        path = output_dir / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output_dir", type=Path)
    parser.add_argument(
        "--legacy-suffix",
        action="store_true",
        help="build a negative-control fixture using the former nonnumeric A suffix",
    )
    args = parser.parse_args()
    build_fixture(args.output_dir, legacy_suffix=args.legacy_suffix)
    print(f"PASS: rendered ten {'legacy-suffix' if args.legacy_suffix else 'numeric'} clip LED references")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
