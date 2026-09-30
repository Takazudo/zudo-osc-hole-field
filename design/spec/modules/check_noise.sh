#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")/../../.."
bash scripts/schgen/regen.sh
scratch=.circuit-cache/noise-check
mkdir -p "$scratch"
bash scripts/kicad/run.sh kicad-cli sch erc --format json --severity-all -o "$scratch/erc.json" schematic/zudo-osc-hole-field.kicad_sch
bash scripts/kicad/run.sh kicad-cli sch export netlist --format kicadsexpr -o "$scratch/netlist.net" schematic/zudo-osc-hole-field.kicad_sch
python3 scripts/schgen/verify_netlist.py "$scratch/netlist.net"
python3 - <<'PY'
import hashlib,json
from pathlib import Path
from design.spec.modules.noise import specification,panel_bindings,OUTPUTS
from scripts.schgen.core import designator
from scripts.schgen.verify_netlist import exported_pin_nets
scratch=Path('.circuit-cache/noise-check')
erc=json.loads((scratch/'erc.json').read_text())
violations=[v for s in erc['sheets'] for v in s.get('violations',[])]
errors=[v for v in violations if v['severity']=='error']
assert not errors,errors
noise=next(s for s in erc['sheets'] if s['path']=='/N1/')
assert not noise.get('violations'),noise.get('violations')
families,instances=specification();f=families[0];i=instances[0]
assert len(panel_bindings())==4
assert {p.attributes['PanelUid'] for p in f.parts if p.panel_refs}=={'J:${SHEETNAME}.'+name for name in OUTPUTS}
for name in OUTPUTS:
    level=next(p for p in f.parts if p.attributes.get('Role')=='noise:'+name+'_LEVEL')
    assert name+'_LEVEL_SUM' in level.pins.values()
    if name in ('BLUE','BROWN'):
        stage=next(p for p in f.parts if p.attributes.get('Role')=='noise:'+('BLUE_DIFF' if name=='BLUE' else 'BROWN_LEAK'))
        assert name+'_SUM' in stage.pins.values() and name+'_SUM' not in level.pins.values()
actual=exported_pin_nets((scratch/'netlist.net').read_text())
source=next(p for p in f.parts if p.symbol.endswith(':NOISE2'))
assert actual[(designator(source,i),'1')]=='/N1/NOISE_VDD'
assert actual[(designator(source,i),'3')]=='/N1/WHITE_RAW'
assert actual[(designator(source,i),'7')]=='/N1/PINK_RAW'
report={'schema_version':1,'status':'PASS - KiCad ERC and pin/net parity only','global_erc_errors':0,'noise_warnings':0,'other_existing_warnings':len(violations),'panel_bindings':4,'source_pin_nets':{'1':'NOISE_VDD','3':'WHITE_RAW','7':'PINK_RAW'},'netlist_sha256':hashlib.sha256((scratch/'netlist.net').read_bytes()).hexdigest(),'source_files':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [Path('design/spec/modules/noise.py'),Path('schematic/sheets/noise.kicad_sch')]},'limits':'No hardware spectral, RMS, DC leakage, supply or assembly claim.'}
Path('schematic/reports/noise-checks.json').write_text(json.dumps(report,indent=2)+'\n')
print('PASS: N1 four locked jacks, source pins, zero errors/warnings, full netlist parity')
PY
python3 -m design.spec.modules.build_noise_current --check
python3 -m design.spec.modules.run_noise_spice
