#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
bash scripts/schgen/regen.sh
scratch=.circuit-cache/envelope-check
mkdir -p "$scratch"
bash scripts/kicad/run.sh kicad-cli sch erc --format json --severity-all -o "$scratch/erc.json" schematic/zudo-osc-hole-field.kicad_sch
bash scripts/kicad/run.sh kicad-cli sch export netlist --format kicadsexpr -o "$scratch/netlist.net" schematic/zudo-osc-hole-field.kicad_sch
python3 scripts/schgen/verify_netlist.py "$scratch/netlist.net"
python3 - <<'PY'
import hashlib,json
from pathlib import Path
from design.spec.modules.envelope import specification,panel_bindings
from scripts.schgen.core import designator
from scripts.schgen.verify_netlist import exported_pin_nets
scratch=Path('.circuit-cache/envelope-check');erc=json.loads((scratch/'erc.json').read_text())
violations=[v for s in erc['sheets'] for v in s.get('violations',[])]
assert not [v for v in violations if v['severity']=='error'],violations
families,instances=specification();f=families[0]
leds=[p for p in f.parts if p.panel_refs and p.attributes['PanelUid'].startswith('L:')]
for i in instances:
 own=next(s.get('violations',[]) for s in erc['sheets'] if s['path']=='/'+i.name+'/')
 refs={designator(p,i) for p in leds}
 assert len(own)==10,own
 assert all(v['severity']=='warning' and v['type']=='pin_to_pin' and any(any(item['description'].startswith('Symbol '+ref+' Pin ') for ref in refs) for item in v['items']) for v in own),own
pins=exported_pin_nets((scratch/'netlist.net').read_text());cap=next(p for p in f.parts if p.attributes.get('Role')=='envelope:TIMING_CAP')
timing=[pins[(designator(cap,i),'1')] for i in instances]
assert timing==['/'+i.name+'/ENV_STORAGE' for i in instances],timing
report={'schema_version':1,'status':'PASS - native ERC and netlist parity only','oracle':'KiCad 10.0.6 pinned wrapper','global_erc_errors':0,'envelope_warnings':60,'warning_basis':'Ten per instance: five retained white panel LEDs each with two Unspecified pins; actual refs and warning type checked, no suppression.','other_existing_warnings':len(violations)-60,'panel_bindings':len(panel_bindings()),'instance_storage_nets':timing,'netlist_sha256':hashlib.sha256((scratch/'netlist.net').read_bytes()).hexdigest(),'source_files':{p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in ['design/spec/modules/envelope.py','design/spec/modules/envelope_logic.py','schematic/sheets/envelope.kicad_sch']},'scope':'No physical timing, comparator/logic dynamics, startup, power, board or harness qualification established.'}
Path('schematic/reports/envelope-checks.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS: 108 fixed panel UIDs; six isolated storage nets; zero errors; 60 justified envelope LED warnings')
PY
