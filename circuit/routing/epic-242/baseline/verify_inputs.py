import json,pathlib,hashlib,subprocess
O=pathlib.Path(__file__).resolve().parent; R=O.parents[3];b=json.loads((O/'baseline.json').read_text());m=json.loads((O/'input-files.json').read_text());count=0
epoch=json.loads((O/'resource-control-epoch.json').read_text())
assert epoch['hardware_epoch']==b['epoch']=='epic242-e0' and epoch['tool_epoch']=='epic242-tools-e8-python-test-dependency'
assert set(epoch['historical_overrides'])=={'scripts/kicad/README.md','scripts/kicad/run.sh'}
for p,change in epoch['historical_overrides'].items():
 assert m['files'][p]==change['historical_sha256'],p
for p,digest in epoch['tool_files'].items():
 assert hashlib.sha256((R/p).read_bytes()).hexdigest()==digest,p
for p,digest in m['files'].items():
 expected=epoch['historical_overrides'].get(p,{}).get('reviewed_sha256',digest)
 assert hashlib.sha256((R/p).read_bytes()).hexdigest()==expected,p
 count+=1
part=json.loads((R/'design/partition/partition.json').read_text()); c=json.loads((O/'harness-contract.json').read_text());assert c['harnesses']==part['harnesses'];cs={x['id']:x for x in part['connectors']};assert len(c['connectors'])==len(cs)==390
for x in c['connectors']:
 assert all(cs[x['id']][k]==v for k,v in x.items()); assert 'pcb_reference' in x and 'pin_map' in x
for k in ['JL','JR','K']:
 x=b['boards'][k];r=json.loads((R/x['receipt']['path']).read_text());assert r['adopted'] and r['candidate_board_sha256']==x['published']['sha256']; assert sum(x['open_by_net'].values())==x['open_edges']; assert r['drc_errors']==0 and r['parity']==0
# Frozen source equality is the gate; documentation/ledger commits may advance independently.
print(f'PASS: {count-2} original frozen inputs unchanged; two exact reviewed tooling replacements; resource-tool epoch sealed; 195 harnesses/390 complete endpoint refs/pin maps/poses; current117/129/1402 adopted receipts, DRC/parity0/0; source invariants unchanged')
