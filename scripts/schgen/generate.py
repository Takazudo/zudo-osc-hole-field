#!/usr/bin/env python3
"""Generate functional master schematic from design.spec.instrument."""
import json
from pathlib import Path
import sys
sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.schgen.core import LibrarySymbol, render  # noqa: E402
from design.spec.instrument import specification  # noqa: E402
from design.spec.cells._builder import load_symbol  # noqa: E402

FIXTURES = {'LM2902':'Fixture:LM2902', 'LM2903':'Fixture:LM2903', 'R':'Fixture:R',
            'Conn_01x02':'Fixture:Conn_01x02', 'PWR_FLAG':'Fixture:PWR_FLAG', 'GND':'Fixture:GND', 'VCC':'Fixture:VCC'}
PROJECT = 'zudo-osc-hole-field'

def main():
    symbols = {lib_id: LibrarySymbol.from_fixture(lib_id, ROOT/'scripts/schgen/fixtures'/f'{name}.kicad_sympart') for name,lib_id in FIXTURES.items()}
    families, instances = specification()
    for family in families:
        for part in family.parts:
            if part.symbol.startswith('zudo-osc-hole-field:') and part.symbol not in symbols:
                symbols[part.symbol]=load_symbol(part.symbol.split(':',1)[1])
    output = ROOT/'schematic'
    output.mkdir(exist_ok=True)
    generated = render(families, instances, symbols, PROJECT)
    for stale in (output/'sheets').glob('*.kicad_sch') if (output/'sheets').exists() else ():
        if f'sheets/{stale.name}' not in generated and '(generator \"zudo_schgen\")' in stale.read_text():
            stale.unlink()
    for path, body in generated.items():
        target=output/path
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(body)
    (output/f'{PROJECT}.kicad_pro').write_text(json.dumps({'meta': {'filename':f'{PROJECT}.kicad_pro','version':1}, 'sheets': [], 'text_variables': {}}, indent=2)+'\n')
    fixture_body='(kicad_symbol_lib (version 20231120) (generator "zudo_schgen")\n'+''.join(symbols[lib_id].body+'\n' for lib_id in FIXTURES.values())+')\n'
    (ROOT/'scripts/schgen/fixtures/fixture.kicad_sym').write_text(fixture_body)
    (output/'sym-lib-table').write_text('(sym_lib_table\n  (version 7)\n  (lib (name "zudo-osc-hole-field") (type "KiCad") (uri "${KIPRJMOD}/../symbols/zudo-osc-hole-field.kicad_sym") (options "") (descr ""))\n  (lib (name "Fixture") (type "KiCad") (uri "${KIPRJMOD}/../scripts/schgen/fixtures/fixture.kicad_sym") (options "") (descr "Test-only symbols and pilot power flags"))\n)\n')
    (output/'fp-lib-table').write_text('(fp_lib_table\n  (version 7)\n  (lib (name "zudo-osc-hole-field") (type "KiCad") (uri "${KIPRJMOD}/../footprints/kicad/zudo-osc-hole-field.pretty") (options "") (descr ""))\n)\n')
    return 0

if __name__ == '__main__': raise SystemExit(main())
