#!/usr/bin/env python3
"""Build the smoke PCB from the fixture's KiCad S-expression netlist."""

from __future__ import annotations

import os
import re
import sys
import uuid
from pathlib import Path

import pcbnew

UUID_NAMESPACE = uuid.UUID("96274ca0-f419-487c-9c99-ab204ed93049")


def tokenize(text: str) -> list[str]:
    return re.findall(r'"(?:\\.|[^"\\])*"|[()]|[^\s()]+', text)


def atom_value(token: str) -> str:
    if token.startswith('"'):
        import json

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


def child(node, name: str):
    return next(item for item in node if isinstance(item, list) and item and item[0] == name)


def children(node, name: str):
    return [item for item in node if isinstance(item, list) and item and item[0] == name]


def component_data(node):
    sheet_path = child(node, "sheetpath")
    return {
        "ref": child(node, "ref")[1],
        "value": child(node, "value")[1],
        "footprint": child(node, "footprint")[1],
        "sheetname": child(sheet_path, "names")[1],
        "sheet_ts": child(sheet_path, "tstamps")[1],
        "symbol_ts": child(node, "tstamps")[1],
    }


def read_netlist(path: Path):
    root, _ = parse_expr(tokenize(path.read_text(encoding="utf-8")))
    component_group = child(root, "components")
    net_group = child(root, "nets")
    components = [component_data(node) for node in children(component_group, "comp")]
    pin_nets = {}
    for net in children(net_group, "net"):
        net_name = child(net, "name")[1]
        for node in children(net, "node"):
            pin_nets[(child(node, "ref")[1], child(node, "pin")[1])] = net_name
    return components, pin_nets


def mm(value: float) -> int:
    return pcbnew.FromMM(value)


def footprint_directory(library: str) -> Path:
    root = (
        os.environ.get("KICAD10_FOOTPRINT_DIR")
        or os.environ.get("KICAD_FOOTPRINT_DIR")
    )
    if root is None:
        candidates = (
            Path("/usr/share/kicad/footprints"),
            Path("/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"),
        )
        root = str(
            next((candidate for candidate in candidates if candidate.is_dir()), candidates[0])
        )
    return Path(root) / f"{library}.pretty"


def build_board(directory: Path) -> None:
    components, pin_nets = read_netlist(directory / "smoke.net")
    board = pcbnew.BOARD()

    nets = {}
    for net_name in sorted(set(pin_nets.values())):
        net_info = pcbnew.NETINFO_ITEM(board, net_name)
        board.Add(net_info)
        nets[net_name] = net_info
    library_cache = {}
    for index, component in enumerate(sorted(components, key=lambda item: item["ref"])):
        library, footprint_name = component["footprint"].split(":", 1)
        if component["footprint"] not in library_cache:
            footprint_path = footprint_directory(library)
            loaded = pcbnew.FootprintLoad(str(footprint_path), footprint_name)
            if loaded is None:
                raise FileNotFoundError(f"Stock footprint missing from the oracle: {component['footprint']}")
            library_cache[component["footprint"]] = loaded

        footprint = pcbnew.FOOTPRINT(library_cache[component["footprint"]])
        footprint.SetParent(board)
        footprint.SetFPID(pcbnew.LIB_ID(library, footprint_name))
        footprint.SetReference(component["ref"])
        footprint.SetValue(component["value"])
        footprint.SetPath(pcbnew.KIID_PATH(component["sheet_ts"] + component["symbol_ts"]))
        footprint.SetSheetname(component["sheetname"])
        footprint.SetSheetfile("smoke.kicad_sch")
        footprint.SetPosition(pcbnew.VECTOR2I(mm(12 + index * 13), mm(12)))
        for pad in footprint.Pads():
            net_name = pin_nets.get((component["ref"], pad.GetNumber()))
            if net_name is not None:
                pad.SetNet(nets[net_name])
        board.Add(footprint)

    outline = pcbnew.PCB_SHAPE(board)
    outline.SetShape(pcbnew.SHAPE_T_RECT)
    outline.SetStart(pcbnew.VECTOR2I(mm(4), mm(4)))
    outline.SetEnd(pcbnew.VECTOR2I(mm(50), mm(22)))
    outline.SetLayer(pcbnew.Edge_Cuts)
    outline.SetWidth(mm(0.05))
    board.Add(outline)

    board_path = directory / "smoke.kicad_pcb"
    board.SetFileName(str(board_path))
    pcbnew.SaveBoard(str(board_path), board)
    normalize_board_uuids(board_path)
    print(f"Built smoke PCB from {len(components)} netlisted components")


def normalize_board_uuids(board_path: Path) -> None:
    """Replace pcbnew's random item IDs with stable IDs, leaving schematic paths intact."""
    text = board_path.read_text(encoding="utf-8")
    item_index = 0

    def stable_id(match):
        nonlocal item_index
        value = str(uuid.uuid5(UUID_NAMESPACE, f"board-item:{item_index}"))
        item_index += 1
        return f"{match.group(1)}{value}{match.group(2)}"

    normalized = re.sub(r'(\(uuid\s+")[^"]+("\))', stable_id, text)
    board_path.write_text(normalized, encoding="utf-8")


def main() -> int:
    if len(sys.argv) != 2:
        print("Usage: build_board.py <fixture-directory>", file=sys.stderr)
        return 2
    build_board(Path(sys.argv[1]))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
