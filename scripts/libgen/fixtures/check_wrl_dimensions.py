#!/usr/bin/env python3
"""Compare KiCad 10's imported WRL bounds with the source display envelopes.

Run inside the pinned oracle: bash scripts/kicad/run.sh python3
scripts/libgen/fixtures/check_wrl_dimensions.py
This checks coordinate units and footprint model scale, not mechanical fit.
"""

from __future__ import annotations

import math
import re
import subprocess
import sys
from pathlib import Path

import pcbnew

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / "scripts/libgen"))
from gen_component_envelopes import MODELS as COMPONENT_MODELS  # noqa: E402
from gen_ic_package_envelopes import MODELS as IC_MODELS  # noqa: E402

LIBRARY = ROOT / "footprints/kicad/zudo-osc-hole-field.pretty"
FIXTURE = ROOT / ".circuit-cache/fixtures"
EXPECTED = {
    "PTV09A-4020F": (10.0, 10.0, 6.8),
    "Jack_3.5mm_QingPu_WQP518MA": COMPONENT_MODELS["Jack_3.5mm_QingPu_WQP518MA.wrl"][:3],
    "Toggle_Dailywell_2MS_T1B1M2": COMPONENT_MODELS["Toggle_Dailywell_2MS_T1B1M2.wrl"][:3],
    "Button_Omron_B3F_6x6_P6.5x4.5": COMPONENT_MODELS["Button_Omron_B3F_6x6_P6.5x4.5.wrl"][:3],
    **{name: model["dims"] for name, model in IC_MODELS.items()},
}
NUMBER = r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?"


def exported_bounds(footprint_name: str) -> tuple[float, float, float]:
    board = pcbnew.BOARD()
    footprint = pcbnew.FootprintLoad(str(LIBRARY), footprint_name)
    if footprint is None:
        raise AssertionError(f"KiCad cannot load {footprint_name}")
    footprint.SetPosition(pcbnew.VECTOR2I(0, 0))
    board.Add(footprint)
    pcb_path = FIXTURE / "wrl-dimensions.kicad_pcb"
    vrml_path = FIXTURE / "wrl-dimensions.wrl"
    pcbnew.SaveBoard(str(pcb_path), board)
    result = subprocess.run(
        ["kicad-cli", "pcb", "export", "vrml", "--units", "mm", "--force",
         "-o", str(vrml_path), str(pcb_path)],
        text=True, capture_output=True,
    )
    if result.returncode:
        raise AssertionError(f"KiCad VRML export failed for {footprint_name}: {result.stderr}")
    exported = vrml_path.read_text(encoding="utf-8")
    match = re.search(r"\bCoordinate\s*\{\s*point\s*\[([^]]+)\]", exported, re.S)
    if match is None:
        raise AssertionError(f"KiCad exported no model coordinates for {footprint_name}")
    # The first Coordinate node belongs to the sole attached model; subsequent
    # nodes may describe pads and the board. Native Transform scales preceding
    # that node include the exporter unit conversion and footprint model scale.
    prefix = exported[:match.start()]
    scales = [tuple(map(float, re.findall(NUMBER, line))) for line in
              re.findall(r"^\s*scale\s+[^\n]+", prefix, re.M)]
    if not scales or not math.isclose(scales[0][0], 2.54, abs_tol=1e-6):
        raise AssertionError(f"unexpected KiCad VRML unit transform for {footprint_name}: {scales}")
    scale = [math.prod(axis[n] for axis in scales) for n in range(3)]
    numbers = [float(value) for value in re.findall(NUMBER, match.group(1))]
    if len(numbers) < 24 or len(numbers) % 3:
        raise AssertionError(f"incomplete native model coordinates for {footprint_name}")
    points = list(zip(*(iter(numbers),) * 3))
    return tuple((max(point[n] for point in points) - min(point[n] for point in points))
                 * abs(scale[n]) for n in range(3))


def main() -> None:
    FIXTURE.mkdir(parents=True, exist_ok=True)
    for footprint_name, expected in EXPECTED.items():
        actual = exported_bounds(footprint_name)
        if any(not math.isclose(got, want, abs_tol=0.005) for got, want in zip(actual, expected)):
            raise AssertionError(f"{footprint_name}: native KiCad bounds {actual} mm; expected {expected} mm")
        print(f"PASS: {footprint_name}: {tuple(round(value, 3) for value in actual)} mm")
    print(f"PASS: {len(EXPECTED)} project-authored display WRLs match source x/y/z envelopes in KiCad 10")


if __name__ == "__main__":
    main()
