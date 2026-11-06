"""Read-only whole-instrument source/reuse ledger. No CAD or native execution."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'design/architecture-278/source-ledger.json'
BASE = '65cefd41fc39e064d38319115ad96016a1c6b71c'
PARKED = '5af0e7b675123b40367078ee605a1355bae49a62'
LINKED = '011e8be351e81d51a13d2d56cb246fd36d623843'
SOURCES = ['project/osc-hole-field/block-contracts.json', 'design/grid/placements.lock.json',
 'design/reports/io-partition.json', 'design/partition/partition.json',
 'design/reports/connectors.json', 'design/power/rail-ledger.json',
 '.claude/skills/component-spec-audit/references/inventory.json',
 '.claude/skills/circuit-spec-integration/references/rules.json']

def read(path):
    return json.loads((ROOT / path).read_text())

def build():
    io = read(SOURCES[2]); partition = read(SOURCES[3])
    contracts = read(SOURCES[0]); panel = read(SOURCES[1])['placements']
    assert len(contracts) == 33 and len(panel) == 438
    assert len({p['uid'] for p in panel}) == 438
    assignments = {p['ref']:p for p in partition['assignment']['components']}
    units = {}
    for unit in io['package_units']:
        key = (unit['ref'], unit['unit'])
        assert key not in units, key
        units[key] = unit
    packages = []
    for p in io['physical_packages']:
        assert p['ref'] in assignments
        members = [units[(p['ref'],u)] for u in p['units']]
        assert len(set(u['region'] for u in members)) == 1, p['ref']
        packages.append({**{k:p[k] for k in ('ref','instance','family','mpn','dnp','units','regions','islands','decouples_ref')}, 'current_board':assignments[p['ref']]['board']})
    assert sum(len(p['units']) for p in packages) == len(units)
    inputs=[]
    for path in SOURCES:
        raw=(ROOT/path).read_bytes()
        original=subprocess.check_output(['git','show',f'{BASE}:{path}'],cwd=ROOT)
        assert raw == original, f'protected source drift: {path}'
        inputs.append({'path':path,'revision':BASE,'sha256':hashlib.sha256(raw).hexdigest()})
    trim_rev='7aba720c1246d6ec3f02909af6fb08dc774b3d31'
    trim_path='design/service/trimmer-functions.json'
    trim_bytes=subprocess.check_output(['git','show',f'{trim_rev}:{trim_path}'],cwd=ROOT)
    trim_source=json.loads(trim_bytes)
    trim_rows=[]
    package_index={p['ref']:p for p in packages}
    assert len(trim_source['trimmers'])==100 and len(trim_source['roles'])==28
    for t in trim_source['trimmers']:
        p=package_index[t['ref']]
        members=[u for u in io['package_units'] if u['ref']==t['ref']]
        assert p['instance']==t['block'] and p['mpn']==t['mpn']
        assert all(u['role']==t['role'] for u in members)
        trim_rows.append({k:t[k] for k in ('ref','block','role','label','mpn','nominal_resistance','rotation_direction','calibration_status')})
    functions=[]
    for f in contracts:
        functions.append({**f,'panel_uids':[p['uid'] for p in panel if p['block']==f['id']],
            'source_packages':[p['ref'] for p in packages if p['instance']==f['id']],
            'owner':'#280 OSC interfaces' if f['id'].startswith('O') and f['family']=='OSC' else '#278 boundary preservation; existing family acceptance remains open',
            'architecture_scope':'O1/O2 representative; O3/O4/O5 parity only' if f['family']=='OSC' else 'interface-boundary only; no relocation or qualification'})
    return {'schema_version':1,'status':'DESIGN EVIDENCE ONLY; canonical unvalidated drafts preserved',
      'base':BASE,'parked_260':PARKED,'parked_277':'fdac23b2611dcb26f840c520348771821ea9c35d',
      'linked_evidence':LINKED,'inputs':inputs,'functions':functions,'panel':panel,
      'boards':partition['boards'],'packages':packages,'package_units':io['package_units'],
      'shared_services': ['+12V','-12V','+5V','AGND','OSC_REF5','OSC_REFN5','OSC_GATE_REF']+[f'OSC_OCT{i}' for i in range(6)],
      'shared_reference_packages':[p['ref'] for p in packages if p['family']=='octave_reference'],
      'reused_trimmer_semantics':{'revision':trim_rev,'path':trim_path,'sha256':hashlib.sha256(trim_bytes).hexdigest(),'roles':28,'rows':trim_rows,'status':'100 Ref+Block+Role+MPN joins checked; no native label or physical calibration adoption'},
      'counts':{'functions':len(functions),'panel_centres':len(panel),'packages':len(packages),'units':len(units),'dnp':sum(p['dnp'] for p in packages)},
      'scope':'Retained source report inventory, not fresh native pin/net verification; interface extractor separately rebinds O1/O2/O5 to current specification.'}

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');a=parser.parse_args()
    data=json.dumps(build(),ensure_ascii=False,separators=(',', ':'))+'\n'
    if a.check:
        if not OUT.exists() or OUT.read_text()!=data:raise SystemExit('source-ledger drift')
    else:OUT.write_text(data)
    print('PASS: 33 functions, 438 centres, complete retained package/unit ledger; no native qualification')
if __name__=='__main__':main()
