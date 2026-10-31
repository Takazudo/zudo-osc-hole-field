"""PROPOSAL generator: carry the repository LED pin-type fix into a COPY of a candidate tree.

The candidate sheets embed frozen copies of the Kingbright_White_0402 / Kingbright_Red_0402
symbols with both pins typed `unspecified`. This retypes only those symbols' pins to `passive`
(in every embedded lib_symbols copy and in candidate/library/zudo-osc-hole-field.kicad_sym),
matching the proposed (held) symbols/src change. Other symbols, such as DW254P-2X8-L0, are
left as they are. Usage: python3 -I led_pin_types.py <candidate-tree-root>
"""
import re
import sys
from pathlib import Path

NAMES = ("Kingbright_White_0402", "Kingbright_Red_0402")


def block_end(text: str, start: int) -> int:
    depth = 0
    i = start
    in_str = False
    while i < len(text):
        ch = text[i]
        if in_str:
            if ch == "\\":
                i += 1
            elif ch == '"':
                in_str = False
        elif ch == '"':
            in_str = True
        elif ch == "(":
            depth += 1
        elif ch == ")":
            depth -= 1
            if depth == 0:
                return i + 1
        i += 1
    raise ValueError("unbalanced symbol block")


def retype(text: str) -> tuple[str, int]:
    pattern = re.compile(r'\(symbol "(?:[^":]+:)?(' + "|".join(NAMES) + r')"')
    out, pos, changed = [], 0, 0
    for m in pattern.finditer(text):
        if m.start() < pos:
            continue
        end = block_end(text, m.start())
        block = text[m.start():end]
        n = block.count("(pin unspecified ")
        out.append(text[pos:m.start()])
        out.append(block.replace("(pin unspecified ", "(pin passive "))
        changed += n
        pos = end
    out.append(text[pos:])
    return "".join(out), changed


def main(root: Path) -> int:
    files = sorted((root / "candidate/rendered/variant").rglob("*.kicad_sch")) + [root / "candidate/library/zudo-osc-hole-field.kicad_sym"]
    total = 0
    for f in files:
        text = f.read_text()
        new, n = retype(text)
        if n:
            if n % 2:
                raise ValueError(f"{f}: odd LED pin count {n}")
            f.write_text(new)
            total += n
    print(f"{root}: {total} LED pins retyped passive in {len(files)} files scanned")
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1])))
