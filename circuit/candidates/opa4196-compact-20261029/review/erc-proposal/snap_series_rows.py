"""PROPOSAL generator: snap the inherited R9000xx series-resistor rows of the candidate sheets onto the 1.27 mm grid.

The rows come from the predecessor development baseline (Series250k/Series14 splits) and were
placed at round millimetre coordinates (x = 50/80/110, y = 590...960), so their pin ends and
the joining wires sit off KiCad's 1.27 mm connection grid. This rewrites a COPY of a sheet:
each R9000xx symbol centre is rounded to the grid, its pin-end wires and labels follow the
pins, and mid-wire net labels are rounded to the grid on their wire. Nothing else moves.
Usage: python3 -I snap_series_rows.py <in.kicad_sch> <out.kicad_sch>
"""
import re
import sys
from pathlib import Path

GRID = 1.27
PIN = 5.08  # RT0603/RC0603 representative symbol pin-end offset; 4 grid steps
NUM = r"-?\d+(?:\.\d+)?"


def snap(v: float) -> float:
    return round(round(v / GRID) * GRID, 4)


def fmt(v: float) -> str:
    return f"{v:.4f}".rstrip("0").rstrip(".")


def main(src: Path, dst: Path) -> int:
    lines = src.read_text().split("\n")
    sym_re = re.compile(rf'^  \(symbol \(lib_id "[^"]+"\) \(at ({NUM}) ({NUM}) 0\)')
    rows, blocks = {}, []
    i = 0
    while i < len(lines):
        m = sym_re.match(lines[i])
        if m:
            j = i
            while lines[j] != "  )":
                j += 1
            body = "\n".join(lines[i:j + 1])
            if re.search(r'\(reference "R9\d{5}"\)', body):
                x, y = float(m.group(1)), float(m.group(2))
                blocks.append((i, j, x, y))
                rows.setdefault(y, []).append(x)
            i = j + 1
            continue
        i += 1
    if not blocks:
        raise SystemExit("no R9000xx series rows found")
    for i, j, x, y in blocks:
        dx, dy = snap(x) - x, snap(y) - y
        for k in range(i, j + 1):
            lines[k] = re.sub(rf"\(at ({NUM}) ({NUM})", lambda m: f"(at {fmt(float(m.group(1)) + dx)} {fmt(float(m.group(2)) + dy)}", lines[k])
    moved = 0
    item_re = re.compile(r"^  \((label|wire|junction|global_label|hierarchical_label|no_connect) ")
    for y, xs in rows.items():
        pin_map = {round(x + s * PIN, 4): round(snap(x) + s * PIN, 4) for x in xs for s in (-1, 1)}
        lo, hi = min(xs) - PIN, max(xs) + PIN

        def mx(v: float) -> float:
            v = round(v, 4)
            return pin_map.get(v, snap(v))

        def sub_point(m, kw):
            px, py = float(m.group(1)), float(m.group(2))
            if abs(py - y) > 1e-6 or not (lo - 1e-6 <= px <= hi + 1e-6):
                return m.group(0)
            return f"({kw} {fmt(mx(px))} {fmt(snap(py))}"

        for k, text in enumerate(lines):
            if not item_re.match(text):
                continue
            new = re.sub(rf"\(xy ({NUM}) ({NUM})", lambda m: sub_point(m, "xy"), text)
            new = re.sub(rf"\(at ({NUM}) ({NUM})", lambda m: sub_point(m, "at"), new)
            if new != text:
                lines[k] = new
                moved += 1
    dst.write_text("\n".join(lines))
    print(f"{src.name}: {len(blocks)} series symbols in {len(rows)} rows snapped; {moved} wire/label lines moved")
    return 0


if __name__ == "__main__":
    sys.exit(main(Path(sys.argv[1]), Path(sys.argv[2])))
