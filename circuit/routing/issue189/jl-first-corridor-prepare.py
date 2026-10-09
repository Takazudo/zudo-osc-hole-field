"""Prepare R2316.2 plus its complete victim repair; native coupled gate required."""
from pathlib import Path
import hashlib,json
ROOT=Path(__file__).resolve().parents[3]
HERE=Path(__file__).resolve().parent
base_path=ROOT/'.circuit-cache/issue189-downloaded/jl-six-corridors/osc-jack-left-grid-189-local-base/dump.json'
candidate_path=ROOT/'.circuit-cache/issue189-downloaded/jl-six-corridors/osc-jack-left-grid-189-jl-six-corridors-verify/dump.json'
current_path=ROOT/'.circuit-cache/issue189-downloaded/jl-paired-corridors/.circuit-cache/osc-jack-left-grid-shards-fresh/dump.json'
base=json.loads(base_path.read_text());candidate=json.loads(candidate_path.read_text());current=json.loads(current_path.read_text())
assert base['board_sha256']=='b91bc8f1194dbaf9534863534ef2a090fae165b63f0aa01eaea2d367e7c94dbc'
assert candidate['board_sha256']=='e9bcfc326bb592286f4021720c748c20e903ca4e24dae4e3c69504753f962566'
sha='3d40f1db27f350ce063bf601cab2eeb9f6394b47da9930fca21b6bc0258d2352'
assert current['board_sha256']==sha==hashlib.sha256((ROOT/'boards/osc-jack-left/osc-jack-left.kicad_pcb').read_bytes()).hexdigest()
selection=next(e for e in json.loads((HERE/'jl-six-corridors-selection.json').read_text()) if e['target']=='XED7C19D453619667580D')
nets={selection['target'],*selection['victims']}
for kind in ('tracks','vias'):
    assert sorted(json.dumps(x,sort_keys=True) for x in base[kind] if x['net'] in nets)==sorted(json.dumps(x,sort_keys=True) for x in current[kind] if x['net'] in nets)
assert base['pads']==current['pads']
delta=json.loads((HERE/'jl-six-corridors-copper.json').read_text())
added={x['uuid'] for x in delta['added'] if x['net'] in nets};rows=[]
for t in candidate['tracks']:
    if t['uuid'] in added:rows.append({'kind':'segment','uuid':t['uuid'],'net':t['net'],'start_nm':t['a'],'end_nm':t['b'],'width_nm':t['width'],'layer':t['layer']})
for v in candidate['vias']:
    if v['uuid'] in added:rows.append({'kind':'via','uuid':v['uuid'],'net':v['net'],'at_nm':v['xy'],'diameter_nm':v['diameter'],'drill_nm':v['drill']})
assert len(rows)==len(added)
probe=json.loads((HERE/'jl-victim-return-probe.json').read_text())
assert probe['input_dump_sha256']==hashlib.sha256(candidate_path.read_bytes()).hexdigest()
rows += [r for r in probe['proposal']['copper'] if r['net'] in nets]
assert len({r['uuid'] for r in rows})==len(rows)
proposal={'board_sha256':sha,'removed_uuids':selection['removed_source_uuids'],'copper':rows}
p=HERE/'jl-first-corridor-proposal.json';p.write_text(json.dumps(proposal,indent=2)+'\n')
plan={'board':'osc-jack-left','input_board_sha256':sha,'name':'189-jl-first-corridor-restored','proposal':str(p.relative_to(ROOT)),'proposal_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'rail_method':'rail-links','restore_connectivity':True,'scope':'R2316.2 plus whole victim repair. Additional victim path was captured without heuristic fill guard; mandatory native coupled restoration and full original membership/warning/fresh gates must validate it. Four exact source cuts; all other accepted135 copper retained. Not native-eligible yet.'}
(HERE/'jl-coupled-plan.json').write_text(json.dumps(plan,indent=2)+'\n')
print('Prepared',len(rows),'objects;',len(proposal['removed_uuids']),'cuts; native coupled gate NOT RUN')
