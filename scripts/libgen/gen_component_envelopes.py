#!/usr/bin/env python3
"""Generate small, source-bounded WRL cuboids for component catalogue references.

These files are display envelopes only. They deliberately omit seats, terminals,
levers, nuts, actuators, lens shape, and any feature not bounded by the retained
sources. They do not qualify mechanical fit.
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "footprints/kicad/zudo-osc-hole-field.3dshapes"
MODELS = {
    "Jack_3.5mm_QingPu_WQP518MA.wrl": (9.0, 10.5, 9.0, (0.22, 0.22, 0.22),
        "Provisional family body envelope from retained PJ398SM drawing callouts 9 x 10.5 x 9 mm; no panel datum or exact WQP body claim."),
    "Toggle_Dailywell_2MS_T1B1M2.wrl": (8.13, 5.08, 5.08, (0.65, 0.65, 0.65),
        "Provisional 2M family body envelope from retained drawing dimensions; third axis is a display bound only, not a mounted-height or fit claim."),
    "Button_Omron_B3F_6x6_P6.5x4.5.wrl": (6.0, 6.0, 5.0, (0.18, 0.18, 0.18),
        "Coarse B3F-1020 envelope from Omron 6 x 6 mm body and 5.0 mm board-to-plunger-top dimension; no actuator or seated-stack detail."),
}
FACES = "0,3,2,1,-1,4,5,6,7,-1,0,1,5,4,-1,1,2,6,5,-1,2,3,7,6,-1,3,0,4,7,-1"

def fmt(value):
    return f"{value:.6f}".rstrip("0").rstrip(".") if value else "0"

def render(name, dims, color, note):
    dx, dy, dz = dims
    x, y = dx / 2, dy / 2
    points = [(-x,-y,0),(x,-y,0),(x,y,0),(-x,y,0),(-x,-y,dz),(x,-y,dz),(x,y,dz),(-x,y,dz)]
    point_text = ", ".join(" ".join(fmt(v) for v in point) for point in points)
    return (
        "#VRML V2.0 utf8\n"
        f"# {note}\n"
        "Shape {\n"
        f" appearance Appearance {{ material Material {{ diffuseColor {fmt(color[0])} {fmt(color[1])} {fmt(color[2])} }} }}\n"
        " geometry IndexedFaceSet {\n"
        "  ccw TRUE\n"
        "  solid FALSE\n"
        f"  coord Coordinate {{ point [ {point_text} ] }}\n"
        f"  coordIndex [{FACES}]\n"
        " }\n"
        "}\n"
    )

OUT.mkdir(parents=True, exist_ok=True)
for filename, (dx, dy, dz, color, note) in MODELS.items():
    (OUT / filename).write_text(render(filename, (dx, dy, dz), color, note), encoding="utf-8")
