"""Deterministic source-only checkpoint; never invokes a native executable."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import stage20_observation as n
import stage19_request as previous

ROOT=n.source.ROOT
OUT=ROOT/'design/architecture-278/implementation/stage20'
EVIDENCE=ROOT/'design/architecture-278/implementation/stage19/x0x-run-20261016'
BASE='f62c8650710bfa9d013e2e14ca2305c172160737'


def protected():
    changed=subprocess.check_output(['git','diff',BASE,'--name-only','--diff-filter=DMRTUXB'],cwd=ROOT,text=True).splitlines()
    n.need(set(changed)<={'design/architecture-278/implementation/WORK.md'},'historical/protected file changed: '+repr(changed))
    added=subprocess.check_output(['git','diff',BASE,'--name-only','--diff-filter=A'],cwd=ROOT,text=True).splitlines()
    added+=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines()
    n.need(all(name.startswith('design/architecture-278/implementation/stage20/') or
        name in {'scripts/architecture278/implementation/'+x for x in ('stage20_observation.py','stage20_replay.py','test_stage20_observation.py')} for name in added),'out-of-scope addition')
    return {'baseline_commit':BASE,'all_preexisting_tracked_bytes_preserved_except':['design/architecture-278/implementation/WORK.md']}


def report():
    protection=protected()
    saved=json.loads((previous.OUT/'native-request.json').read_text())
    n.need(saved==previous.request(saved['verification_commit']),'historical request changed')
    inputs=saved['input_files_sha256']
    n.need(len(inputs)==72,'complete native input manifest')
    for path,sha in inputs.items(): n.need(n.source.digest(ROOT/'design/architecture-278/implementation'/path)==sha,'native input changed: '+path)
    manifest=json.loads((EVIDENCE/'manifest.json').read_text())
    for path,entry in manifest.items():
        raw=(EVIDENCE/path).read_bytes()
        n.need(len(raw)==entry['bytes'] and hashlib.sha256(raw).hexdigest()==entry['sha256'],'historical published evidence changed: '+path)
    retention=json.loads((EVIDENCE/'run/retention.json').read_text())
    n.need(len(retention['files'])==40,'complete raw retention roster')
    for entry in retention['files']:
        raw=(EVIDENCE/'run/retained'/entry['path']).read_bytes()
        n.need(len(raw)==entry['size'] and hashlib.sha256(raw).hexdigest()==entry['sha256'],'raw retained receipt changed: '+entry['path'])
    xml=EVIDENCE/'run/retained/netlist.xml'
    historical=json.loads((EVIDENCE/'run/xml-parity.json').read_text())
    n.need(historical['status']=='FAIL' and historical['observation_sha256']==n.source.digest(xml),'historical FAIL lost')
    n.need((n.source.OUT/'compatibility-report.json').read_text()==n.source.json_text(n.source.report()),'source regeneration or compatibility report drift')
    result=n.compare(n.parse_xml(xml.read_text()),n.expected_from_source())
    files=sorted((ROOT/'scripts/architecture278/implementation').glob('*stage20*.py'))
    files += [OUT/'README.md',OUT/'exporter-source.json']
    result.update({'preservation':protection,'observation_sha256':n.source.digest(xml),
        'source_commit':saved['source_commit'],'native_verification_commit':saved['verification_commit'],
        'consumed_request_sha256':n.source.digest(previous.OUT/'native-request.json'),
        'input_files_sha256':inputs,'historical_result':historical,
        'published_evidence_manifest_sha256':n.source.digest(EVIDENCE/'manifest.json'),
        'retained_files_rechecked':len(retention['files']),
        'source_sha256':{str(path.relative_to(ROOT)):n.source.digest(path) for path in files},
        'native_execution':'NONE: replay only; original opportunity consumed',
        'next_native_request':'NOT NEEDED for representation-only reconciliation; no new admission granted',
        'acceptance_scope':'All 118 references, 561 pins, 154 source unit UUIDs and 196 explicit NCs in this unchanged source and retained XML only. Not electrical acceptance.'})
    return result


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args()
    text=n.source.json_text(report());path=OUT/'replay-report.json'
    if args.check:n.need(path.read_text()==text,'Stage20 replay report drift')
    else:path.write_text(text)
    print('PASS source-only retained XML replay; 118 refs / 561 pins / 154 UUIDs / 196 NCs; historical FAIL preserved')

if __name__=='__main__':main()
