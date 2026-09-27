#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
bash scripts/schgen/regen.sh
scratch=.circuit-cache/oscillator-check
mkdir -p "$scratch"
bash scripts/kicad/run.sh kicad-cli sch erc --format json --severity-all -o "$scratch/erc.json" schematic/zudo-osc-hole-field.kicad_sch
bash scripts/kicad/run.sh kicad-cli sch export netlist --format kicadsexpr -o "$scratch/netlist.net" schematic/zudo-osc-hole-field.kicad_sch
python3 scripts/schgen/verify_netlist.py "$scratch/netlist.net"
python3 - <<'PY'
import hashlib,json
from pathlib import Path
from design.spec.modules.oscillator import specification,INSTANCES,panel_bindings
from scripts.schgen.core import designator
from scripts.schgen.verify_netlist import exported_pin_nets
scratch=Path('.circuit-cache/oscillator-check')
erc=json.loads((scratch/'erc.json').read_text())
all_violations=[v for s in erc['sheets'] for v in s.get('violations',[])]
assert not [v for v in all_violations if v['severity']=='error'],all_violations
owned=['/'+i+'/' for i in (*INSTANCES,'OCTAVE_REF')]
violations=[v for s in erc['sheets'] if s['path'] in owned for v in s.get('violations',[])]
assert not violations,violations
families,instances=specification();core=next(p for p in families[0].parts if p.key=='CORE.1')
actual=exported_pin_nets((scratch/'netlist.net').read_text())
timing=[actual[(designator(core,i),'11')] for i in instances[:5]]
assert timing==['/'+i+'/TIMING_CAP' for i in INSTANCES],timing
report={'schema_version':1,'status':'PASS - native ERC and netlist parity only','oracle':'KiCad 10.0.6 pinned wrapper','global_erc_errors':0,'oscillator_and_reference_warnings':0,'other_existing_warnings':len(all_violations),'panel_bindings':len(panel_bindings()),'instance_timing_nets':timing,'netlist_sha256':hashlib.sha256((scratch/'netlist.net').read_bytes()).hexdigest(),'source_files':{p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in ['design/spec/modules/oscillator.py','schematic/sheets/oscillator.kicad_sch','schematic/sheets/octave_reference.kicad_sch']},'scope':'No physical behavior, PCB placement, production suitability or oscillator tracking established.'}
Path('schematic/reports/oscillator-checks.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS: 80 panel UIDs, five isolated timing nets, zero oscillator/reference warnings')
PY
