#!/usr/bin/env python3
"""Assemble one deterministic KiCad symbol library from one-symbol fragments."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
FRAGMENT_DIR = ROOT / "symbols" / "src"
OUTPUT = ROOT / "symbols" / "zudo-osc-hole-field.kicad_sym"


def symbol_spans(text: str, parent_depth: int = 1) -> list[tuple[int, int]]:
    spans: list[tuple[int, int]] = []
    depth = 0
    quoted = False
    escaped = False
    start: int | None = None
    for index, char in enumerate(text):
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
            continue
        if char == '"':
            quoted = True
            continue
        if char == "(":
            if depth == parent_depth and text.startswith("(symbol", index):
                after = index + len("(symbol")
                if after == len(text) or text[after].isspace() or text[after] == ")":
                    start = index
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == parent_depth and start is not None:
                spans.append((start, index + 1))
                start = None
            if depth < 0:
                raise ValueError("unbalanced closing parenthesis")
    if quoted or depth != 0:
        raise ValueError("unbalanced KiCad symbol expression")
    return spans


def symbol_name(block: str) -> str:
    match = re.match(r'\(symbol\s+"((?:\\.|[^"\\])*)"', block)
    if not match:
        raise ValueError("symbol block has no quoted name")
    return bytes(match.group(1), "utf-8").decode("unicode_escape")


def fragment_header(text: str) -> tuple[str, str, str]:
    version = re.search(r"(?m)^\s*\(version\s+(\d+)\s*\)", text)
    generator = re.search(r'(?m)^\s*\(generator\s+"((?:\\.|[^"\\])*)"\s*\)', text)
    generator_version = re.search(r'(?m)^\s*\(generator_version\s+"((?:\\.|[^"\\])*)"\s*\)', text)
    if not version or not generator or not generator_version:
        raise ValueError("fragment library wrapper must declare version, generator and generator_version")
    return version.group(1), generator.group(1), generator_version.group(1)


def assemble() -> bytes:
    fragments = sorted(FRAGMENT_DIR.glob("*.kicad_sym"), key=lambda path: path.name)
    if not fragments:
        raise ValueError(f"no symbol fragments found under {FRAGMENT_DIR}")

    header: tuple[str, str, str] | None = None
    symbols: list[tuple[str, str]] = []
    seen_names: set[str] = set()
    for path in fragments:
        text = path.read_text(encoding="utf-8")
        if not text.lstrip().startswith("(kicad_symbol_lib"):
            raise ValueError(f"{path.relative_to(ROOT)} is not a KiCad symbol library fragment")
        current_header = fragment_header(text)
        if header is None:
            header = current_header
        elif current_header != header:
            raise ValueError(f"{path.relative_to(ROOT)} uses a different symbol library format header")
        spans = symbol_spans(text)
        if len(spans) != 1:
            raise ValueError(f"{path.relative_to(ROOT)} must contain exactly one top-level symbol; found {len(spans)}")
        block = text[spans[0][0] : spans[0][1]].strip()
        name = symbol_name(block)
        if path.stem != name:
            raise ValueError(f"fragment filename {path.name} does not match symbol {name!r}")
        if name in seen_names:
            raise ValueError(f"duplicate symbol fragment name {name!r}")
        seen_names.add(name)
        symbols.append((name, block))

    assert header is not None
    version, generator, generator_version = header
    lines = [
        "(kicad_symbol_lib",
        f"\t(version {version})",
        f'\t(generator "{generator}")',
        f'\t(generator_version "{generator_version}")',
    ]
    for _name, block in sorted(symbols, key=lambda item: item[0]):
        lines.append("\t" + block.replace("\n", "\n\t"))
    lines.append(")")
    return ("\n".join(lines) + "\n").encode("utf-8")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--check", action="store_true", help="fail if the assembled library is stale")
    args = parser.parse_args()
    expected = assemble()
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    if args.check:
        if not OUTPUT.is_file() or OUTPUT.read_bytes() != expected:
            print("Symbol library drift: regenerate symbols/zudo-osc-hole-field.kicad_sym", file=sys.stderr)
            return 1
        print(f"Symbol library: current ({len(symbol_spans(expected.decode('utf-8')))} fragments)")
        return 0
    OUTPUT.write_bytes(expected)
    print(f"Assembled {len(symbol_spans(expected.decode('utf-8')))} symbols into {OUTPUT.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as exc:
        print(f"build_symbol_lib: {exc}", file=sys.stderr)
        raise SystemExit(1)
