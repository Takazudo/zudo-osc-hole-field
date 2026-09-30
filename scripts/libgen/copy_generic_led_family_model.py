#!/usr/bin/env python3
"""Give the shared generic 0603 LED family geometry a distinct package basename."""
from pathlib import Path

root = Path(__file__).resolve().parents[2]
source = root / "footprints/kicad/zudo-osc-hole-field.3dshapes/LED0603-RD.wrl"
target = root / "footprints/kicad/zudo-osc-hole-field.3dshapes/LED0603-Generic-Family.wrl"
text = source.read_text(encoding="utf-8")
header, separator, body = text.partition("\n")
if not separator or header.strip() != "#VRML V2.0 utf8":
    raise SystemExit("source model is not VRML 2.0 utf8")
target.write_text(header + "\n# Shared 0603 family envelope; not a white-variant model.\n" + body, encoding="utf-8")
