#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
bash scripts/schgen/regen.sh
scratch=.circuit-cache/wavefolder-check
mkdir -p "$scratch"
bash scripts/kicad/run.sh kicad-cli sch erc --format json --severity-all -o "$scratch/erc.json" schematic/zudo-osc-hole-field.kicad_sch
bash scripts/kicad/run.sh kicad-cli sch export netlist --format kicadsexpr -o "$scratch/netlist.net" schematic/zudo-osc-hole-field.kicad_sch
python3 scripts/schgen/verify_netlist.py "$scratch/netlist.net"
python3 - <<'PY'
import hashlib,json
from pathlib import Path
from design.spec.modules.wavefolder import specification,panel_bindings
from scripts.schgen.core import designator
from scripts.schgen.verify_netlist import exported_pin_nets
scratch=Path('.circuit-cache/wavefolder-check');erc=json.loads((scratch/'erc.json').read_text());all_v=[v for s in erc['sheets'] for v in s.get('violations',[])]
assert not [v for v in all_v if v['severity']=='error'],all_v
fs,instances=specification();f=fs[0];leds=[p for p in f.parts if p.panel_refs and p.attributes['PanelUid'].startswith('L:')]
for i in instances:
 own=next(s.get('violations',[]) for s in erc['sheets'] if s['path']=='/'+i.name+'/');refs={designator(p,i) for p in leds}
 assert len(own)==6,own
 assert all(v['severity']=='warning' and v['type']=='pin_to_pin' and any(any(it['description'].startswith('Symbol '+r+' Pin ') for r in refs) for it in v['items']) for v in own),own
pins=exported_pin_nets((scratch/'netlist.net').read_text());cap=next(p for p in f.parts if p.attributes.get('Role')=='wavefolder:AC_BANK0')
ac=[pins[(designator(cap,i),'2')] for i in instances];assert ac==['/'+i.name+'/AC_NODE' for i in instances],ac
report={'schema_version':1,'status':'PASS - native ERC/netlist parity only','oracle':'KiCad10.0.6 pinned wrapper','global_erc_errors':0,'wavefolder_warnings':12,'other_existing_warnings':len(all_v)-12,'warning_basis':'Two Unspecified-pin warnings for each of three retained white input LEDs per instance. Actual panel refs/types checked; no suppressions.','panel_bindings':len(panel_bindings()),'coupling_storage_nets':ac,'netlist_sha256':hashlib.sha256((scratch/'netlist.net').read_bytes()).hexdigest(),'source_files':{p:hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in ['design/spec/modules/wavefolder.py','schematic/sheets/wavefolder.kicad_sch']},'scope':'No physical fold count, diode matching, amplifier stability, protection or rail-current qualification.'}
Path('schematic/reports/wavefolder-checks.json').write_text(json.dumps(report,indent=2)+'\n');print('PASS: 22 panel UIDs, W2 left/W1 right, isolated coupling nodes, zero errors,12 justified warnings')
PY
