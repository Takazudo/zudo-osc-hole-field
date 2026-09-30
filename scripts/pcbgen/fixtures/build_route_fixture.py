#!/usr/bin/env python3
"""Derive route fixture schematics from the checked cluster-placer source."""
import json,shutil,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from scripts.pcbgen.fixtures.build_placer_fixture import build

CASES={'one':'one','six':'six','four':'one','unroutable':'one'}
def make(case):
    source=CASES[case];build(source)
    src=ROOT/'.circuit-cache/placer'/source;dst=ROOT/'.circuit-cache/router'/case
    dst.mkdir(parents=True,exist_ok=True)
    for name in ('sym-lib-table','fp-lib-table'):
        shutil.copyfile(src/name,dst/name)
    old=f'fixture-place-{source}';new=f'fixture-route-{case}'
    shutil.copyfile(src/(old+'.kicad_sch'),dst/(new+'.kicad_sch'))
    sheets=dst/'sheets';sheets.mkdir(exist_ok=True)
    for path in (src/'sheets').glob('*.kicad_sch'):shutil.copyfile(path,sheets/path.name)
    (dst/(new+'.kicad_pro')).write_text(json.dumps({'meta':{'filename':new+'.kicad_pro','version':1},'sheets':[],'text_variables':{}},indent=2)+'\n')
    print(f'{case}: schematic source ready')
if __name__=='__main__':
    for case in (sys.argv[1:] or CASES):make(case)
