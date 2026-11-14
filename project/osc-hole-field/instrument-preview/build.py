"""Assemble the self-contained, offline instrument preview page.

    python3 project/osc-hole-field/instrument-preview/build.py [--check]

Writes index.html here and the byte-identical published copy
doc/public/assets/osc-hole-field/instrument-3d.html. ``--check`` writes nothing and
fails when any recorded input hash differs from the current file (stale view data)
or when either HTML file differs from a fresh build. Never touches board sources.
"""
from __future__ import annotations

import base64
import hashlib
import json
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
VENDOR = ROOT / 'project/osc-hole-field/workbench/vendor'
MODELS = ROOT / 'project/osc-hole-field/workbench/component-preview/models'
OUT = HERE / 'index.html'
PUBLISHED = ROOT / 'doc/public/assets/osc-hole-field/instrument-3d.html'
LIMIT = 12_000_000


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1 << 20), b''):
            h.update(block)
    return h.hexdigest()


def stale_inputs(view):
    return [p for p, v in view['inputs'].items() if sha256(ROOT / p) != v['sha256']]


def script_text(s: str, what: str) -> str:
    if re.search(r'</script|<!--', s, re.I):
        raise SystemExit(f'{what} contains a sequence that would end or confuse an inline script element')
    return s


def build() -> str:
    view = json.loads((HERE / 'view-data.json').read_text())
    stale = stale_inputs(view)
    if stale:
        raise SystemExit('FAIL view-data.json is stale for: ' + ', '.join(stale) + ' (run extract.py)')
    view['artwork'] = (ROOT / 'design/panel/current-audit/current-panel.svg').read_text()
    tex = {}
    for b in view['boards']:
        for c in b['copper']:
            raw = (HERE / c['file']).read_bytes()
            if len(raw) != c['bytes']:
                raise SystemExit(f'FAIL {c["file"]} differs from view-data.json (run extract.py)')
            tex[c['file'].removeprefix('data/')] = base64.b64encode(raw).decode()
    licences = '\n\n'.join([
        'Three.js r180 (vendored from project/osc-hole-field/workbench/vendor):\n' + (HERE / 'THREE-LICENSE.txt').read_text().strip(),
        (MODELS / 'ATTRIBUTION.md').read_text().strip(),
        (MODELS / 'POT-LICENSE.md').read_text().strip(),
    ])
    parts = {
        'DATA': json.dumps(view, separators=(',', ':'), ensure_ascii=False).replace('<', '\\u003c'),
        'TEX': json.dumps(tex, separators=(',', ':')),
        'LICENSES': script_text(licences, 'licence text'),
        'CORE': script_text((VENDOR / 'three.core.js').read_text(), 'three.core.js'),
        'MOD': script_text((VENDOR / 'three.module.js').read_text(), 'three.module.js'),
        'ORBIT': script_text((VENDOR / 'OrbitControls.js').read_text(), 'OrbitControls.js'),
        'APP': script_text((HERE / 'viewer.js').read_text(), 'viewer.js'),
    }
    shell = (HERE / 'shell.html').read_text()
    html = re.sub(r'@@(DATA|TEX|LICENSES|CORE|MOD|ORBIT|APP)@@', lambda m: parts[m.group(1)], shell)
    if len(html.encode()) > LIMIT:
        raise SystemExit(f'FAIL page is {len(html.encode())} bytes, over the {LIMIT} byte budget')
    return html


def main():
    html = build()
    data = html.encode()
    if '--check' in sys.argv:
        bad = [str(p.relative_to(ROOT)) for p in (OUT, PUBLISHED) if not p.exists() or p.read_bytes() != data]
        if bad:
            raise SystemExit('FAIL stale preview page: ' + ', '.join(bad) + ' (run build.py)')
        print(f'PASS instrument preview is current ({len(data)} bytes; inputs match recorded hashes)')
        return
    OUT.write_bytes(data)
    PUBLISHED.parent.mkdir(parents=True, exist_ok=True)
    PUBLISHED.write_bytes(data)
    print(f'wrote {OUT.relative_to(ROOT)} and {PUBLISHED.relative_to(ROOT)} ({len(data)} bytes)')


if __name__ == '__main__':
    main()
