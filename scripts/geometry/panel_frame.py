"""Fixed R21 front-panel frame and placement conventions.

The handoff grid is the authority for item identity and cell assignment. This
module supplies the shared millimetre frame and the deterministic mappings
used by the panel and board generators.
"""

from __future__ import annotations

import json
import re
from collections.abc import Mapping
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
GRID_RELATIVE_PATH = Path("project/osc-hole-field/workbench/layout/grid.json")
PROVENANCE_RELATIVE_PATH = Path("project/osc-hole-field/handoff/rename-provenance.json")
PANEL_SVG_RELATIVE_PATH = Path("project/osc-hole-field/workbench/panels/panel.svg")
PLACEMENTS_RELATIVE_PATH = Path("design/grid/placements.lock.json")

# All dimensions are millimetres. The front-panel origin is its top-left
# corner; +X points right and +Y points down. There is no Y-axis inversion.
PX, PY = 17.0, 14.0
COLS, JACK_ROWS, CTRL_ROWS = 18, 10, 8
MARGIN_X, JTOP, DIV_GAP, CTRL_GAP, BOTTOM = 6.0, 22.0, 4.0, 12.0, 8.0
DIV = JTOP + JACK_ROWS * PY + DIV_GAP
CTOP = DIV + CTRL_GAP
PANEL_W = COLS * PX + 2 * MARGIN_X
PANEL_H = CTOP + CTRL_ROWS * PY + BOTTOM

LED_MAGNITUDE = (6.15, 0.0)
LED_CLIP = (6.15, 2.05)
LED_STAGE = (5.9, 0.0)
LED_OFFSETS = {
    "mag": LED_MAGNITUDE,
    "clip": LED_CLIP,
    "stage": LED_STAGE,
}

# KiCad uses the same X/Y directions as the panel frame. Apply translation
# only, using this same origin on the panel and every board.
KICAD_OX, KICAD_OY = 100.0, 50.0

PROPOSAL_STATUS = "PROPOSAL"
LED_DOMAIN_OVERRIDES = {"stage": "EL"}
HOLE_DIAMETERS_MM = {
    "jack": 6.2,
    "pot": 6.3,
    "octave": json.loads((REPO_ROOT / "design/mechanical/selector-assembly.json").read_text())["panel"]["aperture_diameter_mm"],
    "switch": 5.2,
    "button": 5.0,
}

# The ownership and dimensions below are provisional handoff-preview data.
# Later mechanical decisions update these tables and regenerate the lock; the
# coordinate and record-generation algorithms do not need to change.
BOARD_DOMAIN_RULES = {
    "jacks": {"default": "J"},
    "controls": (
        {"block_prefix": "O", "by_kind": {"octave": "O", "switch": "OS"}, "default": "OP"},
        {"block_prefix": "E", "by_kind": {"switch": "ES", "button": "ET"}, "default": "EP"},
        {"block_prefix": "A", "by_kind": {}, "default": "EP"},
        {"block_prefix": "H", "by_kind": {"pot": "UP"}, "default": "UT"},
        {"block_prefix": "X", "by_kind": {}, "default": "US"},
        {"block_prefix": "", "by_kind": {}, "default": "MP"},
    ),
}

_SLUG_TRANSLATION = str.maketrans({"±": "PM", "/": "-", ":": "_", ".": "_"})
_VALID_SLUG = re.compile(r"[A-Za-z0-9_-]+\Z")


def cell_center(field: str, col: int, row: int) -> tuple[float, float]:
    """Return the centre of a zero-based R21 grid cell in panel millimetres."""

    field_tops = {"jacks": JTOP, "controls": CTOP}
    field_rows = {"jacks": JACK_ROWS, "controls": CTRL_ROWS}
    if field not in field_tops:
        raise ValueError(f"unknown panel field: {field!r}")
    if not isinstance(col, int) or isinstance(col, bool) or not 0 <= col < COLS:
        raise ValueError(f"column outside 0..{COLS - 1}: {col!r}")
    max_rows = field_rows[field]
    if not isinstance(row, int) or isinstance(row, bool) or not 0 <= row < max_rows:
        raise ValueError(f"row outside 0..{max_rows - 1} for {field}: {row!r}")
    return (MARGIN_X + (col + 0.5) * PX, field_tops[field] + (row + 0.5) * PY)


def to_kicad(x: float, y: float) -> tuple[float, float]:
    """Translate a panel-frame position to the shared KiCad frame."""

    return (x + KICAD_OX, y + KICAD_OY)


def slug_uid(uid: str) -> str:
    """Map a full uid to a path- and identifier-safe stable slug."""

    slug = uid.translate(_SLUG_TRANSLATION)
    if not _VALID_SLUG.fullmatch(slug):
        raise ValueError(f"uid has characters without a slug mapping: {uid!r}")
    return slug


def cell_number(col: int, row: int) -> int:
    """Return the cell-coded reference number used by panel hardware."""

    if not isinstance(col, int) or isinstance(col, bool) or col < 0:
        raise ValueError(f"column must be a non-negative integer: {col!r}")
    if not isinstance(row, int) or isinstance(row, bool) or row < 0:
        raise ValueError(f"row must be a non-negative integer: {row!r}")
    return (col + 1) * 100 + (row + 1)


def reference_designator(
    field: str,
    kind: str,
    col: int,
    row: int,
    *,
    led_type: str | None = None,
) -> str:
    """Return a deterministic cell-coded reference designator.

    Jack, control and indicator references have distinct prefixes or an
    explicit field offset. A clip LED shares a cell with its magnitude LED
    and receives an additional numeric discriminator.
    """

    number = cell_number(col, row)
    prefixes = {
        "jack": "J",
        "pot": "RV",
        "switch": "SW",
        "button": "SW",
        "octave": "SW",
    }
    if kind != "led":
        try:
            return f"{prefixes[kind]}{number}"
        except KeyError as exc:
            raise ValueError(f"no reference prefix for feature kind {kind!r}") from exc

    if field not in {"jacks", "controls"}:
        raise ValueError(f"unknown panel field for LED: {field!r}")
    if led_type not in LED_OFFSETS:
        raise ValueError(f"unknown LED type: {led_type!r}")
    if led_type == "clip":
        return f"D{number}1"
    # Jack and control cell numbers overlap. Keep control LEDs in a separate
    # numeric range while preserving the cell number as the low three digits.
    field_offset = 0 if field == "jacks" else 10_000
    return f"D{number + field_offset}"


def board_domain(field: str, block: str, kind: str) -> str:
    """Return the handoff-preview board domain for one hardware item."""

    try:
        rules = BOARD_DOMAIN_RULES[field]
    except KeyError as exc:
        raise ValueError(f"unknown panel field: {field!r}") from exc
    if field == "jacks":
        if kind != "jack":
            raise ValueError(f"non-jack feature in jack field: {kind!r}")
        return rules["default"]

    for rule in rules:
        if block.startswith(rule["block_prefix"]):
            return rule["by_kind"].get(kind, rule["default"])
    raise ValueError(f"no board-domain rule matches block {block!r}")


def hole_diameter_mm(kind: str) -> float | None:
    """Return the handoff-preview hole diameter, if one is specified."""

    return HOLE_DIAMETERS_MM.get(kind)


def net_name(item: Mapping[str, Any]) -> str:
    """Return the net key; printed labels are intentionally not substituted."""

    key = item.get("key")
    if not isinstance(key, str) or not key:
        raise ValueError(f"item has no usable net key: {item!r}")
    return key
