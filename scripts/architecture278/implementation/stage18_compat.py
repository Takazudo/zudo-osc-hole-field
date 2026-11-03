"""Source-only KiCad 10.0.6 compatibility checkpoint; preserves Stage17 evidence."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import subprocess

import stage17_schematic as old
import stage17_parity as p

ROOT = old.ROOT
BASE = '6b8c54a08639bc4b3ba11f9851c56acff47b76f5'
OUT = ROOT / 'design/architecture-278/implementation/stage18'
GENERATED = OUT / 'generated'
need = p.need


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def json_text(value):
    return json.dumps(value, sort_keys=True, indent=2, allow_nan=False) + '\n'


def original_units():
    inp = old.inputs()
    p.check(old.GENERATED / 'a01.kicad_sch', inp)
    return p.audit_documents(p.hierarchy(old.GENERATED / 'a01.kicad_sch'))


def build_files():
    library = old.library_objects((old.GENERATED/'A01Candidate.kicad_sym').read_text())
    library.update(old.library_objects((old.GENERATED/'A01Transport.kicad_sym').read_text(), 'A01Transport'))
    packages = defaultdict(list)
    for row in original_units():
        packages[row['ref']].append(row)
    parts = []
    page = 1
    slot = 0
    for ref, rows in sorted(packages.items()):
        need(len(rows) <= 20, 'package exceeds schematic page capacity')
        if slot + len(rows) > 20:
            page += 1
            slot = 0
        for row in sorted(rows, key=lambda r:r['unit']):
            props = row['properties']
            attrs = {k:v for k,v in props.items() if k not in ('Reference','Value','Footprint','Datasheet')}
            parts.append(old.core.Part(key=f'{ref}.{row["unit"]}', symbol=row['lib_id'],
                prefix=ref.rstrip('0123456789'), ordinal=1, unit=row['unit'],
                x=90+(slot%4)*195, y=65+(slot//4)*100, pins=row['resolved'],
                value=props['Value'], footprint=props['Footprint'], attributes=attrs,
                panel_ref=ref, page=page,
                in_bom=p.one(row['symbol'],'in_bom')[1]=='yes',
                on_board=p.one(row['symbol'],'on_board')[1]=='yes'))
            slot += 1
    family = old.core.Family('a01-circuit', tuple(parts), global_nets=tuple(sorted(old.inputs()['nets'])), paper='A1')
    files = old.core.render((family,), (old.core.Instance('a01-circuit','A01',71),), library, project='a01')
    # Keep libraries immutable and shared; mount the entire stage17/stage18 tree for the proposed run.
    for name in ('sym-lib-table','fp-lib-table'):
        files[name] = (old.GENERATED/name).read_text().replace('${KIPRJMOD}/', '${KIPRJMOD}/../../stage17/generated/')
    return files


def source_check(root=GENERATED/'a01.kicad_sch'):
    preserve()
    result = p.check(root, old.inputs(), old.GENERATED)
    before = {(r['ref'],r['unit']):r for r in original_units()}
    rows = p.audit_documents(p.hierarchy(root))
    after = {(r['ref'],r['unit']):r for r in rows}
    need(len(rows)==len(after)==154 and before.keys()==after.keys(), 'complete 154-unit roster')
    sheets = defaultdict(set)
    for key, row in after.items():
        prior = before[key]
        for field in ('properties','resolved','lib_id','library'):
            need(row[field]==prior[field], 'unit source metadata/identity/connectivity changed '+str(key)+' '+field)
        for field in ('uuid','in_bom','on_board','dnp','exclude_from_sim'):
            need(p.one(row['symbol'],field)==p.one(prior['symbol'],field), 'unit identity/flag changed '+str(key))
        need(p.children(row['symbol'],'pin')==p.children(prior['symbol'],'pin'), 'pin UUID changed '+str(key))
        sheets[row['ref']].add(row['sheet'])
    need(all(len(s)==1 for s in sheets.values()), 'package units cross schematic sheets')
    for name in ('sym-lib-table','fp-lib-table'):
        wanted = (old.GENERATED/name).read_text().replace('${KIPRJMOD}/','${KIPRJMOD}/../../stage17/generated/')
        need((root.parent/name).read_text()==wanted, 'shared immutable library table differs')
    return result, rows


def preserve():
    # Whole-repository diff protects canonical boards and every historical receipt, not just selected paths.
    changed = subprocess.check_output(['git','diff','--name-only','--diff-filter=DMRTUXB',BASE],cwd=ROOT,text=True).splitlines()
    allowed = {'design/architecture-278/implementation/WORK.md', 'scripts/architecture278/implementation/check_source.py'}
    need(not (set(changed)-allowed), 'predecessor bytes changed: '+str(sorted(set(changed)-allowed)))
    return {'baseline_commit':BASE, 'all_preexisting_tracked_files_preserved_except':sorted(allowed)}


def report():
    result, rows = source_check()
    metadata = {}
    for r in sorted(rows,key=lambda x:(x['ref'],x['unit'])):
        metadata[f'{r["ref"]}.{r["unit"]}'] = {
            'ref':r['ref'], 'unit':r['unit'], 'uuid':p.one(r['symbol'],'uuid')[1],
            'sheet':str(r['sheet'].relative_to(GENERATED)), 'properties':r['properties'],
            'pins':r['resolved'],
            'pin_uuids':{x[1]:p.one(x,'uuid')[1] for x in p.children(r['symbol'],'pin')},
            'flags':{k:p.one(r['symbol'],k)[1] for k in ('in_bom','on_board','dnp','exclude_from_sim')}}
    source_paths = list((ROOT/'scripts/architecture278/implementation').glob('*stage18*.py'))
    source_paths += [OUT/'exporter-source.json', OUT/'README.md', ROOT/'scripts/architecture278/implementation/check_source.py']
    # Bind every historical generated file and all original source bindings; no old report is rewritten.
    historical = json.loads((old.OUT/'schematic-report.json').read_text())
    bound = {str((old.GENERATED/k).relative_to(ROOT)):v for k,v in historical['generated_sha256'].items()}
    bound.update(historical['source_sha256'])
    for name, sha in bound.items():
        actual = hashlib.sha256(subprocess.check_output(['git','show','5469def6cdf2a5f0f9d4a61cec88efbc7ac2130b:'+name],cwd=ROOT)).hexdigest() if name.endswith('/check_source.py') else digest(ROOT/name)
        need(actual==sha, 'historical source hash changed '+name)
    bound.update({str(x.relative_to(ROOT)):digest(x) for x in source_paths})
    return {'status':'PASS source compatibility; new native observation NOT RUN',
        'hardware_acceptance':False,'native_admission_granted':False,'native':'NOT RUN',
        'ERC':'NOT RUN','DRC':'NOT RUN','simulation':'NOT RUN','physical':'NOT RUN',
        'source_parity':result,'unit_metadata':metadata,
        'preservation':preserve(), 'source_sha256':dict(sorted(bound.items())),
        'generated_sha256':{name:hashlib.sha256(text.encode()).hexdigest() for name,text in sorted(build_files().items())}}


def check_predecessor():
    files=old.build_files();old.write_files(files,check=True)
    actual=old.report(files);expected=json.loads((old.OUT/'schematic-report.json').read_text())
    added={str(Path('scripts/architecture278/implementation')/name) for name in (
        'stage17_native_host.py','stage17_native_container.py','stage17_native_parity.py',
        'stage17_retain.py','test_stage17_retain.py','test_stage17_native_parity.py')}
    need(set(actual['source_sha256'])-set(expected['source_sha256'])==added, 'unexpected historical source discovery expansion')
    for name in added:
        frozen=hashlib.sha256(subprocess.check_output(['git','show',BASE+':'+name],cwd=ROOT)).hexdigest()
        need(actual['source_sha256'].pop(name)==frozen, 'historical native helper drift '+name)
    mutable='scripts/architecture278/implementation/check_source.py'
    historical=hashlib.sha256(subprocess.check_output(['git','show','5469def6cdf2a5f0f9d4a61cec88efbc7ac2130b:'+mutable],cwd=ROOT)).hexdigest()
    need(expected['source_sha256'][mutable]==historical, 'historical guard binding')
    actual['source_sha256'][mutable]=historical
    need(actual==expected, 'historical Stage17 report changed beyond exact source discovery/guard integration')
    for role in ('code','electrical','root'):
        review=json.loads((old.OUT/f'review-{role}.json').read_text())
        need(review.get('independent_review') and review.get('authorship_exclusion'), 'historical review attribution')
        for name,sha in review['source_sha256'].items():
            need((historical if name==mutable else digest(ROOT/name))==sha, 'historical review binding '+name)
    print('PASS immutable Stage17 source/report/reviews; exactly six post-export helper discoveries accounted for')


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');parser.add_argument('--check-predecessor',action='store_true');args=parser.parse_args()
    if args.check_predecessor:check_predecessor();return
    old.write_files(build_files(), GENERATED, check=args.check)
    content=json_text(report()); path=OUT/'compatibility-report.json'
    if args.check:need(path.read_text()==content,'compatibility report drift')
    else:path.write_text(content)
    print('PASS source-only compatibility: 118 references / 561 pins / 154 UUIDs; native NOT RUN')


if __name__=='__main__':main()
