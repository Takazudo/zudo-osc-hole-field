#!/usr/bin/env python3
"""Refresh reviewed public copies from the workbench; never edits generated components."""
import argparse,shutil,json
from pathlib import Path
ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser(description=__doc__);p.add_argument('project',type=Path,nargs='?',default=ROOT/'payload');p.add_argument('--apply',action='store_true');a=p.parse_args();host=a.project.resolve();w=host/'project/osc-hole-field/workbench';out=host/'doc/public/assets/osc-hole-field'
pairs=[('index.html','workbench.html'),('panels/panel.svg','panel.svg'),('panels/panel.png','panel.png'),('panels/panel-1to1.pdf','panel-1to1.pdf'),('studies/utility-controls.svg','slew-controls.svg'),('studies/utility-controls.png','slew-controls.png'),('studies/control-grid.png','control-grid.png'),('studies/assembly.png','assembly.png'),('studies/boards.png','boards.png'),('studies/exploded.png','exploded.png'),('vendor/THREE-LICENSE.txt','THREE-LICENSE.txt')]
for src,name in pairs:
 if not (w/src).is_file():raise SystemExit(f'Missing publication source: {w/src}')
 print(w/src,'->',out/name)
if a.apply:
 out.mkdir(parents=True,exist_ok=True)
 for src,name in pairs:shutil.copyfile(w/src,out/name)
 print('Refreshed project publication copies. Run the official site and publication checks locally.')
else:print('Dry run; --apply updates only these named authored-project public copies.')
