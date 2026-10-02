#!/usr/bin/env python3
"""Generate rectangular IPC-style courtyards for the project footprint library."""

from __future__ import annotations

import argparse
import json
import math
import re
import sys
from pathlib import Path
from decimal import Decimal, InvalidOperation, ROUND_FLOOR, ROUND_CEILING

ROOT = Path(__file__).resolve().parents[2]
FOOTPRINT_DIR = ROOT / "footprints" / "kicad" / "zudo-osc-hole-field.pretty"
CLEARANCE_MM = 0.25
LINE_WIDTH_MM = 0.05
BODY_LAYERS = {"F.Fab", "B.Fab", "F.SilkS", "B.SilkS"}
GRAPHIC_NODES = {"fp_line", "fp_rect", "fp_circle", "fp_arc", "fp_poly"}
GEOMETRY_TOLERANCE_MM = 1e-6


def tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    index = 0
    while index < len(text):
        char = text[index]
        if char.isspace():
            index += 1
            continue
        if char == ";":
            newline = text.find("\n", index)
            index = len(text) if newline == -1 else newline + 1
            continue
        if char in "()":
            tokens.append(char)
            index += 1
            continue
        if char == '"':
            start = index
            index += 1
            escaped = False
            while index < len(text):
                current = text[index]
                index += 1
                if escaped:
                    escaped = False
                elif current == "\\":
                    escaped = True
                elif current == '"':
                    break
            else:
                raise ValueError("unclosed string")
            tokens.append(text[start:index])
            continue
        start = index
        while index < len(text) and not text[index].isspace() and text[index] not in "();":
            index += 1
        tokens.append(text[start:index])
    return tokens


def atom_value(token: str) -> str:
    return json.loads(token) if token.startswith('"') else token


def parse_expr(tokens: list[str], position: int = 0):
    if position >= len(tokens) or tokens[position] != "(":
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


def parse(text: str):
    tokens = tokenize(text)
    tree, position = parse_expr(tokens)
    if position != len(tokens):
        raise ValueError("unexpected trailing S-expression tokens")
    return tree


def node_name(node) -> str | None:
    return node[0] if isinstance(node, list) and node and isinstance(node[0], str) else None


def child(node, name: str):
    for item in node[1:] if isinstance(node, list) else []:
        if isinstance(item, list) and node_name(item) == name:
            return item
    return None


def numbers(node) -> list[float]:
    out: list[float] = []
    for item in node[1:] if isinstance(node, list) else []:
        if not isinstance(item, list):
            try:
                out.append(float(item))
            except (TypeError, ValueError):
                pass
    return out


def layers_of(node) -> set[str]:
    found: set[str] = set()
    for name in ("layer", "layers"):
        holder = child(node, name)
        if holder:
            found |= {item for item in holder[1:] if isinstance(item, str)}
    return found


def walk(node):
    if isinstance(node, list):
        yield node
        for item in node:
            yield from walk(item)


def pad_box(pad) -> tuple[float, float, float, float] | None:
    at, size = child(pad, "at"), child(pad, "size")
    if not at or not size:
        return None
    coords, dims = numbers(at), numbers(size)
    if len(coords) < 2 or len(dims) < 2:
        return None
    x, y = coords[0], coords[1]
    rotation = coords[2] if len(coords) > 2 else 0.0
    width, height = dims[0], dims[1]
    if abs(math.sin(math.radians(rotation))) > 0.999:
        width, height = height, width
    elif abs(math.cos(math.radians(rotation))) < 0.999:
        width = height = math.hypot(width, height)
    return (x - width / 2, y - height / 2, x + width / 2, y + height / 2)


def graphic_box(node) -> tuple[float, float, float, float] | None:
    if not layers_of(node) & BODY_LAYERS:
        return None
    name = node_name(node)
    points: list[tuple[float, float]] = []
    if name == "fp_circle":
        centre, edge = child(node, "center"), child(node, "end")
        if centre and edge:
            cx, cy = numbers(centre)[:2]
            ex, ey = numbers(edge)[:2]
            radius = math.dist((cx, cy), (ex, ey))
            points = [(cx - radius, cy - radius), (cx + radius, cy + radius)]
    elif name == "fp_poly":
        pts = child(node, "pts")
        for point in pts[1:] if pts else []:
            if isinstance(point, list) and node_name(point) == "xy":
                coords = numbers(point)
                if len(coords) >= 2:
                    points.append((coords[0], coords[1]))
    else:
        for key in ("start", "mid", "end", "center"):
            point = child(node, key)
            if point:
                coords = numbers(point)
                if len(coords) >= 2:
                    points.append((coords[0], coords[1]))
    if not points:
        return None
    xs, ys = [point[0] for point in points], [point[1] for point in points]
    return min(xs), min(ys), max(xs), max(ys)


def envelope(tree, clearance: float = CLEARANCE_MM, rounded: bool = True):
    boxes: list[tuple[float, float, float, float]] = []
    pads = 0
    for node in walk(tree):
        name = node_name(node)
        if name == "pad":
            pads += 1
            box = pad_box(node)
            if box is None:
                raise ValueError("a pad has no parseable at/size")
            boxes.append(box)
        elif name in GRAPHIC_NODES:
            box = graphic_box(node)
            if box:
                boxes.append(box)
    if not pads:
        raise ValueError("no pads found")
    box = (
        min(item[0] for item in boxes) - clearance,
        min(item[1] for item in boxes) - clearance,
        max(item[2] for item in boxes) + clearance,
        max(item[3] for item in boxes) + clearance,
    )
    return tuple(round(value, 2) for value in box) if rounded else box


def desired_courtyard(tree):
    """Union the generated envelope with an optional local-mm source minimum.

    Floorless footprints retain their historical rounding. Explicit minima use
    outward 0.01 mm rounding, so serialization cannot shrink either boundary.
    This does not alter envelope(), which also serves raw geometry callers.
    """
    properties = [node for node in tree[1:]
                  if node_name(node) == "property" and len(node) > 1
                  and node[1] == "ProjectCourtyardMinimumBox"]
    if not properties:
        return envelope(tree)
    if len(properties) != 1:
        raise ValueError("duplicate ProjectCourtyardMinimumBox")
    prop = properties[0]
    try:
        if len(prop) < 3 or not isinstance(prop[2], str):
            raise ValueError("missing box coordinates")
        box = tuple(Decimal(value) for value in prop[2].split())
        if len(box) != 4 or not all(value.is_finite() for value in box):
            raise ValueError("expected four finite coordinates")
        if box[0] >= box[2] or box[1] >= box[3]:
            raise ValueError("minimum box must have positive area")
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("invalid ProjectCourtyardMinimumBox: " + str(exc)) from exc
    generated = tuple(Decimal(str(v)) for v in envelope(tree, rounded=False))
    combined = (min(box[0], generated[0]), min(box[1], generated[1]),
                max(box[2], generated[2]), max(box[3], generated[3]))
    try:
        result = []
        for i, value in enumerate(combined):
            quantized = value.quantize(Decimal("0.01"),
                        rounding=ROUND_FLOOR if i < 2 else ROUND_CEILING)
            converted = float(quantized)
            if not math.isfinite(converted) or Decimal(format(converted, ".2f")) != quantized:
                raise ValueError("ProjectCourtyardMinimumBox exceeds coordinate precision")
            result.append(converted)
        return tuple(result)
    except InvalidOperation as exc:
        raise ValueError("ProjectCourtyardMinimumBox exceeds coordinate precision") from exc


def courtyard_box(text: str) -> tuple[float, float, float, float]:
    graphics = [node for node in walk(parse(text)) if node_name(node) in GRAPHIC_NODES and "F.CrtYd" in layers_of(node)]
    for node in graphics:
        width = child(node, "width")
        stroke = child(node, "stroke")
        if stroke:
            width = child(stroke, "width")
            style = child(stroke, "type")
            if style and style[1] not in {"solid", "default"}:
                raise ValueError("courtyard stroke must be solid")
        if not width or len(numbers(width)) != 1 or not math.isclose(numbers(width)[0], LINE_WIDTH_MM, abs_tol=GEOMETRY_TOLERANCE_MM):
            raise ValueError("courtyard stroke width differs")
        fill = child(node, "fill")
        if fill and fill[1] != "none":
            raise ValueError("courtyard must be an unfilled outline")

    def point(node, key: str) -> tuple[float, float]:
        value = child(node, key)
        result = numbers(value) if value else []
        if len(result) != 2 or not all(math.isfinite(item) for item in result):
            raise ValueError("invalid courtyard endpoint")
        return result[0], result[1]

    if len(graphics) == 1 and node_name(graphics[0]) == "fp_rect":
        first, second = point(graphics[0], "start"), point(graphics[0], "end")
        box = min(first[0], second[0]), min(first[1], second[1]), max(first[0], second[0]), max(first[1], second[1])
    elif len(graphics) == 4 and all(node_name(node) == "fp_line" for node in graphics):
        edges = [tuple(sorted((point(node, "start"), point(node, "end")))) for node in graphics]
        points = [value for edge in edges for value in edge]
        x0, y0 = min(item[0] for item in points), min(item[1] for item in points)
        x1, y1 = max(item[0] for item in points), max(item[1] for item in points)
        box = x0, y0, x1, y1
        corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
        expected = {tuple(sorted((start, end))) for start, end in zip(corners, corners[1:])}
        if len(set(edges)) != 4 or set(edges) != expected:
            raise ValueError("courtyard lines do not form one closed rectangle")
    else:
        raise ValueError("courtyard must be one rectangle or four closed rectangle edges")
    if box[0] >= box[2] or box[1] >= box[3]:
        raise ValueError("courtyard rectangle has no area")
    return box


def courtyard_matches(text: str, expected: tuple[float, float, float, float], *, exact=False) -> bool:
    try:
        actual = courtyard_box(text)
    except (ValueError, IndexError):
        return False
    if exact:
        return actual == expected
    return all(math.isclose(a, b, abs_tol=GEOMETRY_TOLERANCE_MM) for a, b in zip(actual, expected))


def render(box: tuple[float, float, float, float], indent: str, quoted: bool) -> str:
    x0, y0, x1, y1 = box
    layer = '"F.CrtYd"' if quoted else "F.CrtYd"
    corners = [(x0, y0), (x1, y0), (x1, y1), (x0, y1), (x0, y0)]
    return "".join(
        f"{indent}(fp_line (start {start[0]:.2f} {start[1]:.2f}) (end {end[0]:.2f} {end[1]:.2f})"
        f" (layer {layer}) (width {LINE_WIDTH_MM}))\n"
        for start, end in zip(corners, corners[1:])
    )


def strip_courtyard(text: str) -> str:
    output: list[str] = []
    index, length = 0, len(text)
    pattern = re.compile(r"[ \t]*\((fp_line|fp_rect|fp_poly|fp_circle|fp_arc)\s")
    while index < length:
        match = pattern.match(text, index)
        if not match:
            output.append(text[index])
            index += 1
            continue
        depth, cursor = 0, text.index("(", index)
        quoted, escaped = False, False
        while cursor < length:
            char = text[cursor]
            if quoted:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    quoted = False
            elif char == '"':
                quoted = True
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    cursor += 1
                    break
            cursor += 1
        block = text[index:cursor]
        trailing = cursor
        while trailing < length and text[trailing] in " \t":
            trailing += 1
        if trailing < length and text[trailing] == "\n":
            trailing += 1
        if re.search(r'\(layer\s+"?F\.CrtYd"?\s*\)', block):
            index = trailing
            continue
        output.append(text[index:trailing])
        index = trailing
    return "".join(output)


def rewrite(text: str) -> str:
    tree = parse(text)
    box = desired_courtyard(tree)
    has_minimum = any(node_name(node) == "property" and len(node) > 1
                      and node[1] == "ProjectCourtyardMinimumBox" for node in tree[1:])
    # The historical tolerance may accept an inward edge. Explicit source
    # minima must match the canonical rectangle exactly before reusing bytes.
    if courtyard_matches(text, box, exact=has_minimum):
        return text
    stripped = strip_courtyard(text)
    quoted = '(layer "' in stripped
    body = re.search(r"^([ \t]+)\(pad", stripped, re.M)
    indent = body.group(1) if body else "\t"
    anchor = stripped.rfind(f"{indent}(model ")
    if anchor == -1:
        tail = stripped.rstrip()
        anchor = tail.rfind("\n)")
        anchor = anchor + 1 if anchor != -1 else len(stripped)
    return stripped[:anchor] + render(box, indent, quoted) + stripped[anchor:]


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="report courtyard drift without writing")
    args = parser.parse_args()
    files = sorted(FOOTPRINT_DIR.glob("*.kicad_mod"))
    if not files:
        print(f"No footprint files found under {FOOTPRINT_DIR}", file=sys.stderr)
        return 1
    drift: list[str] = []
    for path in files:
        original = path.read_text(encoding="utf-8")
        try:
            updated = rewrite(original)
            box = courtyard_box(updated)
        except (ValueError, IndexError) as exc:
            print(f"FAIL  {path.name}: {exc}", file=sys.stderr)
            return 1
        if updated != original:
            drift.append(path.name)
            if not args.check:
                path.write_text(updated, encoding="utf-8", newline="\n")
        print(f"{'DRIFT' if updated != original else '  ok '} {path.name:55s} {box[2] - box[0]:6.2f} x {box[3] - box[1]:6.2f} mm")
    if args.check and drift:
        print(f"\n{len(drift)} footprint(s) need a courtyard refresh; run without --check", file=sys.stderr)
        return 1
    print(f"\n{len(drift)} footprint(s) {'would be ' if args.check else ''}updated")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, IndexError) as exc:
        print(f"gen_courtyards: {exc}", file=sys.stderr)
        raise SystemExit(1)
