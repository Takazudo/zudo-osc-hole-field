#!/usr/bin/env python3
"""Generate provisional family WRL envelopes for the selected IC packages.

These cuboids are catalogue geometry only. They omit leads, seating details,
mold shape, optical paths, and any physical-fit conclusion. Every dimension is
bounded by a retained package drawing or the retained family footprint; where
the retained evidence does not give height, the model omits that height and the
open domain remains explicit in the component evidence.
"""

from __future__ import annotations

import argparse
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "footprints/kicad/zudo-osc-hole-field.3dshapes"
FOOTPRINTS = ROOT / "footprints/kicad/zudo-osc-hole-field.pretty"
MODEL_PREFIX = "${KIPRJMOD}/../../footprints/kicad/zudo-osc-hole-field.3dshapes/"
VRML_UNIT_MM = 2.54  # KiCad 10 VRML importer: one coordinate unit is 0.1 inch.

# Footprint family -> model, provisional body maximum in mm, retained dimension
# source paths, and the exact limits used. Dimensions follow footprint X/Y/Z.
# Model offsets use the KiCad 3D convention: +Y points opposite PCB +Y. The SOIC-16 model covers the largest
# retained planform across this package family; its exact D16 height remains open.
MODELS = {
    "SOIC-14_3.9x8.7mm_P1.27mm": {
        "file": "IC_SOIC-14_3.9x8.7.wrl", "dims": (4.0, 8.75, 1.75),
        "sources": ["circuit/sources/ic-library/OPA4196.pdf"],
        "note": "Provisional family envelope: TI D0014A SOIC-14 package-outline maxima 8.75 x 4.0 x 1.75 mm. Other records using this footprint retain their own package checks; no physical-fit verdict.",
    },
    "TSSOP-14_4.4x5mm_P0.65mm": {
        "file": "IC_TSSOP-14_4.4x5.0.wrl", "dims": (4.5, 5.1, 1.2),
        "sources": ["circuit/sources/ic-library/OPA4197.pdf"],
        "note": "Provisional family envelope: TI PW0014A TSSOP-14 outline maxima 5.1 x 4.5 x 1.2 mm. No land-pattern or physical-fit verdict.",
    },
    "TSSOP-16_4.4x5mm_P0.65mm": {
        "file": "IC_TSSOP-16_4.4x5.0.wrl", "dims": (4.5, 5.1, 1.2),
        "sources": ["circuit/sources/ic-library/ADG5412F.pdf"],
        "note": "Provisional family envelope: ADG5412F RU-16 outline maxima 5.10 x 4.50 x 1.20 mm. No board-fit or system protection verdict.",
    },
    "SOIC-8_3.9x4.9mm_P1.27mm": {
        "file": "IC_SOIC-8_3.9x4.9.wrl", "dims": (3.98, 5.0, 1.75),
        "sources": ["circuit/sources/ic-library/LM393B.pdf"],
        "note": "Provisional family envelope: TI D0008A SOIC-8 package-outline maxima 5.00 x 3.98 x 1.75 mm. No land-pattern or physical-fit verdict.",
    },
    "SOIC-16_3.9x9.9mm_P1.27mm": {
        "file": "IC_SOIC-16_3.9x9.9.wrl", "dims": (4.0, 10.0, 1.75),
        "sources": ["circuit/sources/ic-library/AS3340.pdf", "circuit/sources/ic-library/LM13700.pdf", "circuit/sources/ic-library/OPA4196.pdf"],
        "note": "Provisional narrow-SOIC-16 family envelope: ALFA RPAR AS3340D drawing gives 10.0 x 4.0 mm nominal planform; TI LM13700 gives 9.90 x 3.91 mm. Uses the largest retained planform. 1.75 mm height is a family estimate from the retained D0014A outline, not an exact D16 limit. Exact height and physical fit remain OPEN.",
    },
    "DIP-8_W7.62mm": {
        "file": "IC_DIP-8_W7.62mm.wrl", "dims": (6.35, 10.16, 0.1),
        "offset_mm": (3.81, -3.81, 0),
        "sources": ["circuit/sources/ic-library/cad/DIP-8_W7.62mm.stock.kicad_mod"],
        "note": "Planform-only family display from retained DIP-8 footprint F.Fab extents 10.16 x 6.35 mm. The 0.1 mm plate is not a package-height claim; NOISE2 body height and optical/board clearance remain OPEN.",
    },
    "SOT-23-5": {
        "file": "IC_SOT-23-5.wrl", "dims": (1.75, 3.05, 1.45),
        "sources": ["circuit/sources/ic-library/TLV755P.pdf"],
        "note": "Provisional family envelope: TI DBV0005A SOT-23-5 maxima 3.05 x 1.75 x 1.45 mm. No exact solderability or physical-fit verdict.",
    },
    "SOD-123": {
        "file": "D_SOD-123.wrl", "dims": (2.8, 1.7, 1.3),
        "sources": ["circuit/sources/ic-library/BAS16GW-Q.pdf"],
        "note": "Provisional family envelope: Nexperia SOD123 outline maxima 2.80 x 1.70 x 1.30 mm. No placement, diode-transfer, or physical-fit verdict.",
    },
    "SOT-23": {
        "file": "IC_SOT-23.wrl", "dims": (1.4, 3.0, 1.1),
        "sources": ["circuit/sources/ic-library/MMBT3904.pdf"],
        "note": "Provisional family envelope: Nexperia MMBT3904 SOT23 package-outline maxima 3.0 x 1.4 x 1.1 mm, reused only as a common-family display envelope. No exact-part fit verdict.",
    },
    "SOT-363_SC-70-6": {
        "file": "IC_SOT-363_SC-70-6.wrl", "dims": (1.35, 2.2, 1.1),
        "sources": ["circuit/sources/ic-library/BCM847BS.pdf"],
        "note": "Provisional family envelope: Nexperia SOT363-3 outline maxima 2.2 x 1.35 x 1.1 mm. No land-pattern or physical-fit verdict.",
    },
}

FACES = "0,3,2,1,-1,4,5,6,7,-1,0,1,5,4,-1,1,2,6,5,-1,2,3,7,6,-1,3,0,4,7,-1"
COLOR = (0.34, 0.47, 0.60)


def fmt(value: float) -> str:
    return f"{value:.6f}".rstrip("0").rstrip(".") if value else "0"


def render(name: str, dims: tuple[float, float, float], note: str) -> str:
    dx, dy, dz = dims
    x, y, dz = dx / (2 * VRML_UNIT_MM), dy / (2 * VRML_UNIT_MM), dz / VRML_UNIT_MM
    points = [(-x, -y, 0), (x, -y, 0), (x, y, 0), (-x, y, 0),
              (-x, -y, dz), (x, -y, dz), (x, y, dz), (-x, y, dz)]
    point_text = ", ".join(" ".join(fmt(v) for v in point) for point in points)
    return (
        "#VRML V2.0 utf8\n"
        f"# {note}\n"
        f"# {name}; display envelope only; no fit, clearance, or qualification claim.\n"
        "Shape {\n"
        f" appearance Appearance {{ material Material {{ diffuseColor {fmt(COLOR[0])} {fmt(COLOR[1])} {fmt(COLOR[2])} }} }}\n"
        " geometry IndexedFaceSet {\n"
        "  ccw TRUE\n"
        "  solid FALSE\n"
        f"  coord Coordinate {{ point [ {point_text} ] }}\n"
        f"  coordIndex [{FACES}]\n"
        " }\n"
        "}\n"
    )


def owned_model_span(original: str, filename: str):
    """Locate the one owned model clause without rewriting any 2D geometry."""
    marker = f'"{MODEL_PREFIX}{filename}"'
    matches = list(re.finditer(r'\(model\s+' + re.escape(marker), original))
    if len(matches) != 1 or len(re.findall(r'\(model\s', original)) != 1:
        raise ValueError(f"expected one owned model reference for {filename}")
    start = matches[0].start()
    depth = 0
    for token in re.finditer(r'"(?:\\.|[^"\\])*"|[()]', original[start:]):
        if token[0] == "(": depth += 1
        elif token[0] == ")": depth -= 1
        if depth == 0:
            return start, start + token.end()
    raise ValueError("unterminated owned model clause")


def footprint_with_model(original: str, filename: str, offset_mm=(0, 0, 0)) -> str:
    if len(offset_mm) != 3 or any(isinstance(v, bool) or not math.isfinite(v) for v in offset_mm):
        raise ValueError("invalid model offset")
    offset = " ".join(fmt(v) for v in offset_mm)
    clause = (
        f'(model "{MODEL_PREFIX}{filename}"\n'
        f"\t\t(offset (xyz {offset}))\n"
        "\t\t(scale (xyz 1 1 1))\n"
        "\t\t(rotate (xyz 0 0 0))\n"
        "\t)"
    )
    if re.search(r"\(model\s", original):
        start, end = owned_model_span(original, filename)
        return original[:start] + clause + original[end:]
    stripped = original.rstrip()
    if not stripped.endswith(")"):
        raise ValueError("footprint does not end with a closing parenthesis")
    return stripped[:-1] + "\n\t" + clause + "\n)\n"


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    failures: list[str] = []
    OUT.mkdir(parents=True, exist_ok=True)
    for footprint_name, model in MODELS.items():
        model_path = OUT / model["file"]
        expected_model = render(model["file"], model["dims"], model["note"])
        footprint_path = FOOTPRINTS / f"{footprint_name}.kicad_mod"
        if not footprint_path.exists():
            failures.append(f"missing footprint: {footprint_path.relative_to(ROOT)}")
            continue
        original = footprint_path.read_text(encoding="utf-8")
        expected_footprint = footprint_with_model(original, model["file"], model.get("offset_mm", (0, 0, 0)))
        if args.check:
            if not model_path.exists() or model_path.read_text(encoding="utf-8") != expected_model:
                failures.append(f"stale model: {model_path.relative_to(ROOT)}")
            if original != expected_footprint:
                failures.append(f"stale model reference: {footprint_path.relative_to(ROOT)}")
        else:
            model_path.write_text(expected_model, encoding="utf-8")
            footprint_path.write_text(expected_footprint, encoding="utf-8")
    if failures:
        raise SystemExit("\n".join(failures))
    print(f"{'PASS' if args.check else 'Generated'} {len(MODELS)} provisional IC package family WRL envelopes")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
