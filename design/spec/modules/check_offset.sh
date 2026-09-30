#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
bash scripts/schgen/regen.sh
scratch=.circuit-cache/offset-check
mkdir -p "$scratch"
bash scripts/kicad/run.sh kicad-cli sch erc --format json --severity-all -o "$scratch/erc.json" schematic/zudo-osc-hole-field.kicad_sch
bash scripts/kicad/run.sh kicad-cli sch export netlist --format kicadsexpr -o "$scratch/netlist.net" schematic/zudo-osc-hole-field.kicad_sch
python3 scripts/schgen/verify_netlist.py "$scratch/netlist.net"
python3 - <<'PY'
import hashlib,json
from pathlib import Path
from design.spec.modules.offset import specification,panel_bindings,PANEL
from scripts.schgen.core import designator
from scripts.schgen.verify_netlist import exported_pin_nets
scratch=Path('.circuit-cache/offset-check')
erc=json.loads((scratch/'erc.json').read_text())
violations=[v for s in erc['sheets'] for v in s.get('violations',[])]
assert not [v for v in violations if v['severity']=='error']
families,instances=specification();f=families[0]
assert len(panel_bindings())==54
assert {p.attributes['PanelUid'] for p in f.parts if p.panel_refs}=={template.replace('{}','${SHEETNAME}') for template in PANEL}
assert len([p for p in f.parts if p.panel_refs])==9
actual=exported_pin_nets((scratch/'netlist.net').read_text())
restore=next(p for p in f.parts if p.attributes.get('Role')=='offset:RESTORE')
outpins=[pin for pin,net in restore.pins.items() if net=='OUT_INTERNAL']
assert len(outpins)==1
observed=[]
for i in instances:
    sheet=next(s for s in erc['sheets'] if s['path']=='/'+i.name+'/')
    warnings=sheet.get('violations',[])
    assert len(warnings)==8 and all(v['severity']=='warning' and v['type']=='pin_to_pin' for v in warnings),(i.name,warnings)
    observed.append(actual[(designator(restore,i),outpins[0])])
assert observed==['/'+i.name+'/OUT_INTERNAL' for i in instances],observed
report={'schema_version':1,'status':'PASS - native ERC, locked binding and netlist only','global_erc_errors':0,'offset_warnings':48,'warning_basis':'Eight retained pin_to_pin warnings per instance from four panel LEDs; see offset-erc-notes.md.','panel_bindings':54,'instance_internal_outputs':observed,'other_existing_warnings':len(violations)-48,'netlist_sha256':hashlib.sha256((scratch/'netlist.net').read_bytes()).hexdigest(),'source_files':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path('design/spec/modules/offset.py'),Path('schematic/sheets/offset.kicad_sch')]},'limits':'No physical headroom, tracking, drift, output stability or current maximum established.'}
Path('schematic/reports/offset-checks.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS: 54 UIDs, six isolated internal outputs, zero errors, 48 justified LED warnings')
PY
python3 -m design.spec.modules.build_offset_current --check
python3 -m design.spec.modules.run_offset_spice
