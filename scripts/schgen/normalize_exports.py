#!/usr/bin/env python3
"""Remove only KiCad export timestamps so draft PDF/SVG bytes are reproducible."""
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[2]
EXPORTS=ROOT/'schematic/exports'
pdf=EXPORTS/'master-hierarchy.pdf'
raw=pdf.read_bytes()
normalized,n=re.subn(rb'(/CreationDate\s*\()D:\d{4}:\d{2}:\d{2}:\d{2}:\d{2}:\d{2}(\))',
                     rb'\g<1>D:2000:01:01:00:00:00\2',raw)
if n!=1 or len(normalized)!=len(raw):
    raise ValueError('expected exactly one fixed-width PDF creation timestamp')
pdf.write_bytes(normalized)
for path in sorted(EXPORTS.rglob('*.svg')):
    body=path.read_text()
    body,n=re.subn(r'(<title>SVG Image created as [^<]*? date )\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}( </title>)',
                   r'\g<1>2000-01-01T00:00:00\2',body)
    if n!=1:raise ValueError(f'expected one SVG title timestamp in {path}')
    # KiCad emits presentation-only spaces before many SVG newlines. Strip
    # those bytes so normal git whitespace checks remain useful.
    body='\n'.join(line.rstrip(' \t') for line in body.split('\n'))
    path.write_text(body)
