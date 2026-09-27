#!/usr/bin/env python3
"""Print a stock KiCad symbol or footprint S-expression."""

from __future__ import annotations

import os
import re
import sys
from pathlib import Path


def top_level_forms(text: str):
    """Yield balanced top-level S-expressions, preserving their source text."""
    index = 0
    length = len(text)
    while index < length:
        start = text.find("(", index)
        if start < 0:
            return

        depth = 0
        in_string = False
        escaped = False
        cursor = start
        while cursor < length:
            char = text[cursor]
            if in_string:
                if escaped:
                    escaped = False
                elif char == "\\":
                    escaped = True
                elif char == '"':
                    in_string = False
            elif char == '"':
                in_string = True
            elif char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    yield text[start : cursor + 1]
                    index = cursor + 1
                    break
            cursor += 1
        else:
            raise ValueError("unclosed S-expression")


def balanced_form(text: str, start: int) -> str:
    depth = 0
    in_string = False
    escaped = False
    for cursor in range(start, len(text)):
        char = text[cursor]
        if in_string:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                in_string = False
        elif char == '"':
            in_string = True
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                return text[start : cursor + 1]
    raise ValueError("unclosed S-expression")


def checked_name(value: str, kind: str) -> str:
    if value in {"", ".", ".."} or "/" in value or "\\" in value:
        raise ValueError(f"invalid {kind}: {value!r}")
    return value


def library_roots(kind: str) -> list[Path]:
    if kind == "symbols":
        environment_names = ("KICAD10_SYMBOL_DIR", "KICAD_SYMBOL_DIR")
    else:
        environment_names = ("KICAD10_FOOTPRINT_DIR", "KICAD_FOOTPRINT_DIR")
    roots = [Path(os.environ[name]) for name in environment_names if os.environ.get(name)]
    roots.extend(
        [
            Path(f"/usr/share/kicad/{kind}"),
            Path(f"/Applications/KiCad/KiCad.app/Contents/SharedSupport/{kind}"),
        ]
    )
    return roots


def extract_symbol(library: str, name: str) -> str | None:
    source = next(
        (root / f"{library}.kicad_sym" for root in library_roots("symbols") if (root / f"{library}.kicad_sym").is_file()),
        None,
    )
    if source is None:
        return None
    text = source.read_text(encoding="utf-8")
    needle = re.compile(r'\(symbol\s+"' + re.escape(name) + r'"(?=\s|\))')
    match = needle.search(text)
    if match:
        return balanced_form(text, match.start())
    return None


def extract_footprint(library: str, name: str) -> str | None:
    source = next(
        (
            root / f"{library}.pretty" / f"{name}.kicad_mod"
            for root in library_roots("footprints")
            if (root / f"{library}.pretty" / f"{name}.kicad_mod").is_file()
        ),
        None,
    )
    if source is None:
        return None
    text = source.read_text(encoding="utf-8")
    for form in top_level_forms(text):
        match = re.match(r'\((?:footprint|module)\s+"((?:[^"\\]|\\.)*)"', form)
        if match and match.group(1) == name:
            return form
    return None


def main() -> int:
    if len(sys.argv) != 3:
        print("Usage: extract_stock.py <Library> <Symbol-or-Footprint>", file=sys.stderr)
        return 2
    try:
        library = checked_name(sys.argv[1], "library")
        name = checked_name(sys.argv[2], "symbol or footprint")
    except ValueError as error:
        print(error, file=sys.stderr)
        return 2

    expression = extract_symbol(library, name)
    if expression is None:
        expression = extract_footprint(library, name)
    if expression is None:
        print(f"Stock symbol or footprint not found: {library}:{name}", file=sys.stderr)
        return 1
    print(expression)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
