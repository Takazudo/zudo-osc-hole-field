#!/usr/bin/env python3
"""Generate a tiny schematic fixture with two resistors and a connector."""

from __future__ import annotations

import json
import re
import sys
import uuid
from pathlib import Path

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from extract_stock import extract_symbol  # noqa: E402


NAMESPACE = uuid.UUID("4a6cdb8c-6553-4a10-9a87-b1a87677e404")
PROJECT = "smoke"


def stable_uuid(value: str) -> str:
    return str(uuid.uuid5(NAMESPACE, value))


def tokenize(text: str) -> list[str]:
    return re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', text)


def atom_value(token: str) -> str:
    if token.startswith('"'):
        return json.loads(token)
    return token


def parse_expr(tokens: list[str], position: int = 0):
    if tokens[position] != "(":
        raise ValueError("expected opening parenthesis")
    position += 1
    expression = []
    while position < len(tokens) and tokens[position] != ")":
        if tokens[position] == "(":
            child, position = parse_expr(tokens, position)
            expression.append(child)
        else:
            expression.append(atom_value(tokens[position]))
            position += 1
    if position >= len(tokens):
        raise ValueError("unclosed S-expression")
    return expression, position + 1


def descendants(node, name: str):
    if not isinstance(node, list):
        return
    if node and node[0] == name:
        yield node
    for item in node:
        if isinstance(item, list):
            yield from descendants(item, name)


def library_pins(symbol_expression: str):
    node, _ = parse_expr(tokenize(symbol_expression))
    pins = {}
    for pin in descendants(node, "pin"):
        pin_number = next(child[1] for child in pin if isinstance(child, list) and child[0] == "number")
        pin_at = next(child for child in pin if isinstance(child, list) and child[0] == "at")
        pins[pin_number] = (float(pin_at[1]), float(pin_at[2]), float(pin_at[3]))
    if not pins:
        raise ValueError(f"symbol has no pins: {node[1]}")
    return pins


def symbol_expression(library: str, name: str) -> str:
    expression = extract_symbol(library, name)
    if expression is None:
        raise FileNotFoundError(f"Stock symbol missing from the oracle: {library}:{name}")
    return expression.replace(f'(symbol "{name}"', f'(symbol "{library}:{name}"', 1)


def escape_property(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"')


def property_line(name: str, value: str, x: float, y: float, hidden: bool = False) -> str:
    hide = " (hide yes)" if hidden else ""
    return (
        f'\t\t(property "{name}" "{escape_property(value)}" (at {x:g} {y:g} 0) '
        f'(effects (font (size 1.27 1.27)){hide}))'
    )


def component(
    library: str,
    name: str,
    ref: str,
    value: str,
    footprint: str,
    x: float,
    y: float,
    pins: dict[str, tuple[float, float, float]],
) -> str:
    symbol_uuid = stable_uuid(f"symbol:{ref}")
    lines = [
        f'\t(symbol (lib_id "{library}:{name}") (at {x:g} {y:g} 0) (unit 1)',
        '\t\t(exclude_from_sim no) (in_bom yes) (on_board yes) (dnp no)',
        f'\t\t(uuid "{symbol_uuid}")',
        property_line("Reference", ref, x + 2.54, y - 1.27),
        property_line("Value", value, x + 2.54, y + 1.27),
        property_line("Footprint", footprint, x, y, hidden=True),
        property_line("Datasheet", "", x, y, hidden=True),
    ]
    for pin_number in sorted(pins, key=lambda value: int(value)):
        lines.append(f'\t\t(pin "{pin_number}" (uuid "{stable_uuid(f"{ref}:pin:{pin_number}")}"))')
    lines.extend(
        [
            f'\t\t(instances (project "{PROJECT}" (path "/{ROOT_UUID}" (reference "{ref}") (unit 1))))',
            "\t)",
        ]
    )
    return "\n".join(lines)


ROOT_UUID = stable_uuid("root-sheet")


def global_label(net: str, x: float, y: float, angle: float, seed: str) -> str:
    justify = "left" if angle in (0, 90) else "right"
    return (
        f'\t(global_label "{net}" (shape passive) (at {x:g} {y:g} {angle:g}) '
        f'(effects (font (size 1.27 1.27)) (justify {justify})) '
        f'(uuid "{stable_uuid(seed)}"))'
    )


def write_project_tables(directory: Path) -> None:
    (directory / "sym-lib-table").write_text(
        "(sym_lib_table\n"
        "  (version 7)\n"
        '  (lib (name "Device") (type "KiCad") (uri "${KICAD10_SYMBOL_DIR}/Device.kicad_sym") (options "") (descr ""))\n'
        '  (lib (name "Connector_Generic") (type "KiCad") (uri "${KICAD10_SYMBOL_DIR}/Connector_Generic.kicad_sym") (options "") (descr ""))\n'
        ")\n",
        encoding="utf-8",
    )
    (directory / "fp-lib-table").write_text(
        "(fp_lib_table\n"
        "  (version 7)\n"
        '  (lib (name "Resistor_SMD") (type "KiCad") (uri "${KICAD10_FOOTPRINT_DIR}/Resistor_SMD.pretty") (options "") (descr ""))\n'
        '  (lib (name "Connector_PinHeader_2.54mm") (type "KiCad") (uri "${KICAD10_FOOTPRINT_DIR}/Connector_PinHeader_2.54mm.pretty") (options "") (descr ""))\n'
        ")\n",
        encoding="utf-8",
    )


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: build_fixture.py <output-directory>", file=sys.stderr)
        return 2
    directory = Path(sys.argv[1])
    directory.mkdir(parents=True, exist_ok=True)

    symbol_sources = {
        "Device:R": symbol_expression("Device", "R"),
        "Connector_Generic:Conn_01x02": symbol_expression("Connector_Generic", "Conn_01x02"),
    }
    pin_maps = {
        lib_id: library_pins(expression) for lib_id, expression in symbol_sources.items()
    }

    # Each pin receives a global label. Matching names form three deterministic nets.
    net_map = {
        ("R1", "1"): "NET_A",
        ("R1", "2"): "NET_B",
        ("R2", "1"): "NET_B",
        ("R2", "2"): "NET_C",
        ("J1", "1"): "NET_A",
        ("J1", "2"): "NET_C",
    }
    components = [
        ("Device", "R", "R1", "10k", "Resistor_SMD:R_0603_1608Metric", 50.8, 50.8),
        ("Device", "R", "R2", "10k", "Resistor_SMD:R_0603_1608Metric", 76.2, 50.8),
        (
            "Connector_Generic",
            "Conn_01x02",
            "J1",
            "Conn_01x02",
            "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
            101.6,
            50.8,
        ),
    ]
    lines = [
        "(kicad_sch",
        "  (version 20260306)",
        '  (generator "eeschema")',
        '  (generator_version "10.0")',
        f'  (uuid "{ROOT_UUID}")',
        '  (paper "A4")',
        "  (lib_symbols",
    ]
    for expression in symbol_sources.values():
        lines.append("    " + expression.replace("\n", "\n    "))
    lines.append("  )")

    for library, name, ref, value, footprint, x, y in components:
        pins = pin_maps[f"{library}:{name}"]
        lines.append(component(library, name, ref, value, footprint, x, y, pins))
        for pin_number, (local_x, local_y, local_angle) in pins.items():
            sheet_x = x + local_x
            sheet_y = y - local_y
            label_angle = (360 - local_angle) % 360
            lines.append(
                global_label(
                    net_map[(ref, pin_number)],
                    sheet_x,
                    sheet_y,
                    label_angle,
                    f"label:{ref}:{pin_number}",
                )
            )
    lines.extend(
        [
            '\t(sheet_instances (path "/" (page "1")))',
            "\t(embedded_fonts no)",
            ")",
        ]
    )
    (directory / "smoke.kicad_sch").write_text("\n".join(lines) + "\n", encoding="utf-8")
    (directory / "smoke.kicad_pro").write_text(
        '{\n'
        '  "board": {"design_settings": {"defaults": {}, "diff_pair_dimensions": [], "drc_exclusions": [], "rules": {}, "track_widths": [], "via_dimensions": []}},\n'
        '  "boards": [],\n'
        '  "libraries": {"pinned_footprint_libs": [], "pinned_symbol_libs": []},\n'
        '  "meta": {"filename": "smoke.kicad_pro", "version": 1},\n'
        '  "net_settings": {"classes": [], "meta": {"version": 0}},\n'
        '  "pcbnew": {"page_layout_descr_file": ""},\n'
        '  "sheets": [],\n'
        '  "text_variables": {}\n'
        '}\n',
        encoding="utf-8",
    )
    write_project_tables(directory)
    print(f"Generated deterministic smoke schematic in {directory}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
