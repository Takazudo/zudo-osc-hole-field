"""Compare the inherited SOIC-14 land with TI D0014A example values (no geometry change).

TI values: SBOS869 PDF (retrieved 2026-10-31, sha256 c68223d5...5fde), physical page
index 39-41, drawing 4220718/A 09/2016: package outline, land pattern example and
0.125 mm stencil example. Paste is assumed equal to the copper pad because the
footprint has no paste margin and KiCad's default board paste margin is zero; the
eventual board setting and the assembler's stencil rules are NOT known.
"""
import hashlib
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
FOOTPRINT = ROOT / "footprints/kicad/zudo-osc-hole-field.pretty/SOIC-14_3.9x8.7mm_P1.27mm.kicad_mod"
OUT = Path(__file__).resolve().parent / "land-compare.json"
TI = {"pad_center_x_mm": 5.4 / 2, "pad_length_mm": 1.55, "pad_width_mm": 0.6, "corner_radius_mm": 0.05,
      "pitch_mm": 1.27, "stencil_mm": 0.125,
      "lead_span_E_mm": (5.8, 6.2), "foot_length_L_mm": (0.40, 1.27), "body_width_mm": (3.8, 4.0),
      "lead_width_b_mm": (0.31, 0.51)}


def roundrect_area(length, width, radius):
    return length * width - (4 - math.pi) * radius ** 2


def aperture_ratios(length, width, t):
    return {"area_ratio": round(length * width / (2 * (length + width) * t), 3),
            "aspect_ratio": round(width / t, 3)}


def main() -> int:
    text = FOOTPRINT.read_text()
    pads = re.findall(r'\(pad "(\d+)" smd roundrect\s*\(at ([-\d.]+) ([-\d.]+)\)\s*\(size ([\d.]+) ([\d.]+)\)\s*'
                      r'\(layers ([^)]*)\)\s*\(roundrect_rratio ([\d.]+)\)', text)
    if len(pads) != 14:
        print("FAIL: expected 14 smd roundrect pads")
        return 1
    xs = {abs(float(p[1])) for p in pads}
    sizes = {(float(p[3]), float(p[4])) for p in pads}
    if len(xs) != 1 or len(sizes) != 1:
        print("FAIL: non-uniform pads")
        return 1
    cx = xs.pop()
    length, width = sizes.pop()
    rratio = float(pads[0][6])
    radius = rratio * min(length, width)
    paste_in_layers = all("F.Paste" in p[5] for p in pads)
    margins = re.findall(r"solder_paste_(?:margin|ratio)[^)]*\)", text)
    proj = {"inner_edge_mm": cx - length / 2, "outer_edge_mm": cx + length / 2}
    ti = {"inner_edge_mm": TI["pad_center_x_mm"] - TI["pad_length_mm"] / 2,
          "outer_edge_mm": TI["pad_center_x_mm"] + TI["pad_length_mm"] / 2}
    e_min, e_max = TI["lead_span_E_mm"]
    l_min, l_max = TI["foot_length_L_mm"]
    toe = (e_min / 2, e_max / 2)
    heel = (e_min / 2 - l_max, e_max / 2 - l_min)  # nearest and farthest possible heel position
    body_edge = (TI["body_width_mm"][0] / 2, TI["body_width_mm"][1] / 2)

    def fillets(edges):
        return {"toe_extension_mm": [round(edges["outer_edge_mm"] - toe[1], 3), round(edges["outer_edge_mm"] - toe[0], 3)],
                "heel_extension_mm": [round(heel[0] - edges["inner_edge_mm"], 3), round(heel[1] - edges["inner_edge_mm"], 3)],
                "pad_length_under_body_mm": [round(max(0.0, body_edge[0] - edges["inner_edge_mm"]), 3),
                                              round(max(0.0, body_edge[1] - edges["inner_edge_mm"]), 3)]}

    a_proj = roundrect_area(length, width, radius)
    a_ti = roundrect_area(TI["pad_length_mm"], TI["pad_width_mm"], TI["corner_radius_mm"])
    result = {
        "status": "COMPARISON ONLY; no footprint, paste or board change; not assembly acceptance",
        "footprint": FOOTPRINT.relative_to(ROOT).as_posix(),
        "footprint_sha256": hashlib.sha256(FOOTPRINT.read_bytes()).hexdigest(),
        "project_pad": {"center_x_mm": cx, "length_mm": length, "width_mm": width, "corner_radius_mm": round(radius, 4),
                        **{k: round(v, 3) for k, v in proj.items()}, "f_paste_layer": paste_in_layers,
                        "footprint_paste_margin_overrides": margins},
        "ti_example_pad": {"center_x_mm": TI["pad_center_x_mm"], "length_mm": TI["pad_length_mm"], "width_mm": TI["pad_width_mm"],
                           **{k: round(v, 3) for k, v in ti.items()}},
        "differences": {"inner_edge_further_inward_mm": round(ti["inner_edge_mm"] - proj["inner_edge_mm"], 3),
                        "outer_edge_shorter_mm": round(ti["outer_edge_mm"] - proj["outer_edge_mm"], 3),
                        "pad_gap_mm": round(TI["pitch_mm"] - width, 3),
                        "pad_gap_mm_ti": round(TI["pitch_mm"] - TI["pad_width_mm"], 3)},
        "package_geometry_from_D0014A": {"toe_x_mm": toe, "heel_x_mm_range": [round(h, 3) for h in heel],
                                         "body_edge_x_mm": body_edge},
        "fillet_envelope": {"project": fillets(proj), "ti_example": fillets(ti)},
        "paste_if_equal_to_pad": {
            "project_area_mm2": round(a_proj, 4), "ti_area_mm2": round(a_ti, 4),
            "area_ratio_project_over_ti": round(a_proj / a_ti, 3),
            "volume_mm3_at_0p125": {"project": round(a_proj * TI["stencil_mm"], 4), "ti": round(a_ti * TI["stencil_mm"], 4)},
            "aperture_project": aperture_ratios(length, width, TI["stencil_mm"]),
            "aperture_ti": aperture_ratios(TI["pad_length_mm"], TI["pad_width_mm"], TI["stencil_mm"]),
        },
    }
    OUT.write_text(json.dumps(result, indent=1) + "\n")
    print(json.dumps(result["differences"]), json.dumps(result["paste_if_equal_to_pad"]["area_ratio_project_over_ti"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
