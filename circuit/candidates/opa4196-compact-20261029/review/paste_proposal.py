"""Emit the PROPOSED (not adopted) U110/U210 paste-aperture set as data only.

Copper stays the inherited 1.95 x 0.60 mm pad. The aperture keeps the pad's outer
(toe) edge and drops the inner 0.40 mm, giving the TI D0014A example length
1.55 mm (fact-op-audio-land-pattern-example). Writes no footprint or board file.
"""
import hashlib
import json
import math
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
FP = ROOT / "footprints/kicad/zudo-osc-hole-field.pretty/SOIC-14_3.9x8.7mm_P1.27mm.kicad_mod"
OUT = Path(__file__).resolve().parent / "paste-aperture-proposal.json"
LENGTH, WIDTH, RADIUS, FOIL = 1.55, 0.60, 0.05, 0.125


def main():
    text = FP.read_text()
    pads = re.findall(r'\(pad "(\d+)" smd roundrect\s*\(at ([-\d.]+) ([-\d.]+)\)\s*\(size ([\d.]+) ([\d.]+)\)', text)
    apertures = []
    for num, x, y, sx, sy in pads:
        x, y, sx = float(x), float(y), float(sx)
        sign = 1 if x > 0 else -1
        outer = abs(x) + sx / 2
        cx = sign * (outer - LENGTH / 2)
        apertures.append({"pad": num, "copper_center_mm": [x, y], "aperture_center_mm": [round(cx, 4), y],
                          "aperture_size_mm": [LENGTH, WIDTH], "corner_radius_mm": RADIUS,
                          "aperture_x_span_mm": sorted([round(cx - LENGTH / 2, 4), round(cx + LENGTH / 2, 4)])})
    area = LENGTH * WIDTH - (4 - math.pi) * RADIUS ** 2
    result = {
        "status": "PROPOSAL ONLY; NOT ADOPTED; no footprint, board, stencil or fabrication file is changed or produced",
        "scope": "U110/U210 (sample_hold H1/H2) of the UNADOPTED OPA4196 candidate; the inherited footprint is shared by 347 SOIC-14 package rows per variant",
        "footprint": FP.relative_to(ROOT).as_posix(),
        "footprint_sha256": hashlib.sha256(FP.read_bytes()).hexdigest(),
        "pad_count": len(apertures),
        "apertures": apertures,
        "per_lead": {"area_mm2": round(area, 4), "volume_mm3_at_0p125": round(area * FOIL, 4),
                     "area_ratio_at_0p125": round(LENGTH * WIDTH / (2 * (LENGTH + WIDTH) * FOIL), 3),
                     "vs_1to1_area_mm2": 1.1507},
    }
    OUT.write_text(json.dumps(result, indent=1) + "\n")
    print(len(apertures), apertures[0]["aperture_x_span_mm"], result["per_lead"])


if __name__ == "__main__":
    main()
