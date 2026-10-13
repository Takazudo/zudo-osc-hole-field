#!/usr/bin/env python3
"""Recover/rebind F3 fixtures from complete retained route artifacts; no search."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile

HERE = Path(__file__).resolve().parent
PILOT = HERE.parent
sys.path.insert(0, str(PILOT))
import check
import matching
from prepare_matched import copy_prefix

ORIGINAL_METHOD = '29140d4e19d526eed3a02a73c33f8ce4219c78f0'
EVIDENCE_COMMIT = '191a4db30d90fe43025ec2633e23f9b069f12b85'
ARTIFACTS = {
    'K1402': {'run_id': 38147266896, 'artifact_id': 11705153530, 'file': 'epic242-route-1420-38147266896.zip',
              'sha256': '9232ff3212f41604a72b3f49a9d3a8b10884186884bf50f367a57693a7e082a5'},
    'two-A': {'run_id': 38148185181, 'artifact_id': 11705755937, 'file': 'epic242-route-1438-38148185181.zip',
              'sha256': 'ed8de7933f40369ecefb3ea28f382662923b414298e0cdb72ed5e32578e64e3f'}}
EXTRA = ('f3_adapter.py', 'f3_fixture.py', 'route_f3_access.py', 'exact_access.py',
         'cohort-validation.json')


def method_hashes():
    return {**matching.tool_hashes(), **{str((HERE/n).relative_to(check.ROOT)): check.digest(HERE/n) for n in EXTRA},
            **{name: check.digest(check.ROOT/name) for name in ('scripts/pcbgen/grid_astar.c',
               'scripts/kicad/native_start_gate.sh', 'scripts/kicad/settle_only_pilot.py')}}


def verify_committed_method():
    for name, expected in method_hashes().items():
        raw = subprocess.check_output(['git', 'show', 'HEAD:'+name], cwd=check.ROOT)
        check.require(hashlib.sha256(raw).hexdigest() == expected, 'method file differs from committed HEAD: '+name)


def original_groups(dump, manifest, board):
    domain = manifest['domains']['F3']
    pads = {p['uuid']: p for p in dump['pads']}
    for target in domain['targets'].values():
        ids = [p['uuid'] for p in target['anchor_records']]
        check.require(all(pads.get(p['uuid']) == p for p in target['anchor_records']), 'anchor drift')
        check.require(not matching.connected(dump, target['net_token'], ids), 'original demand is already connected')
        check.require([matching.group_receipt(dump, target['net_token'], u) for u in ids] == target['boards'][board]['original_groups'], 'full native group drift')


def access_plan(dump, manifest):
    from route_matched import numerical_versions
    versions = numerical_versions()
    from f3_adapter import portals, saved_pool
    domain = manifest['domains']['F3']
    spec = check.read(PILOT/'matching-spec.json')
    pool = saved_pool(check.read(HERE/'cohort-validation.json'), domain)
    rows = {}
    for kind in spec['route_policy']['target_order']:
        groups, records, rejected = portals(dump, domain['targets'][kind], pool[kind], spec['budget'], domain['common_bounds_mm'])
        rows[kind] = {'groups': groups, 'records': records, 'rejected': rejected, 'portal_counts': list(map(len, groups))}
    return {'status': 'SOURCE-ONLY INITIAL LANDINGS; NO ROUTE SEARCH OR COPPER', 'versions': versions,
            'bounds_mm': domain['common_bounds_mm'], 'pool': pool, 'demands': rows}


def validate(fixture, board, expected_lock_sha256):
    # Literal digest comes from the independently reviewed packet, never this file.
    check.require(check.digest(fixture/'fixture-lock.json') == expected_lock_sha256, 'external fixture-lock digest mismatch')
    check.source_checks()
    verify_committed_method()
    lock = check.read(fixture/'fixture-lock.json')
    manifest = check.read(PILOT/'matched-demands.json')
    matching.validate_fixture_method(lock, manifest, 'F3', board)
    check.require(lock['source_tree_sha'] == subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=check.ROOT, text=True).strip(), 'wrong adapter commit')
    check.require(lock['original_input_method_sha'] == ORIGINAL_METHOD and lock['access_tool_sha256'] == method_hashes(), 'adapter/input method drift')
    check.require(lock['recovery_artifact'] == ARTIFACTS[board], 'wrong recovery artifact')
    actual = {str(p.relative_to(fixture)) for directory in ('before', 'context') for p in (fixture/directory).rglob('*') if p.is_file()}
    expected = {n for n in lock['files'] if n.startswith(('before/', 'context/'))}
    check.require(actual == expected, 'before/context member census mismatch')
    for name, expected in lock['files'].items():
        check.require(not Path(name).is_absolute() and '..' not in Path(name).parts, 'unsafe lock path')
        check.require(check.digest(fixture/name) == expected, 'fixture file drift '+name)
    dump = check.read(fixture/'before/dump.json')
    binding = manifest['bindings'][board]
    check.require(check.digest(fixture/'before/dump.json') == binding['dump_sha256'], 'dump drift')
    check.require(check.digest(fixture/'before/osc-core.kicad_pcb') == binding['board_sha256'] == dump['board_sha256'], 'PCB drift')
    original_groups(dump, manifest, board)
    return dump, manifest, lock


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--board', required=True, choices=tuple(ARTIFACTS))
    p.add_argument('--artifact', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    check.source_checks()
    verify_committed_method()
    subprocess.run([sys.executable, str(check.ROOT/'circuit/routing/epic-242/baseline/verify_inputs.py')], check=True)
    manifest = check.read(PILOT/'matched-demands.json')
    binding = manifest['bindings'][args.board]
    artifact = ARTIFACTS[args.board]
    output = args.output.resolve()
    check.require(output.is_relative_to(check.SPLIT/'candidates/pilots/generated') and not output.exists(), 'new private fixture required')
    check.require(check.digest(args.artifact) == artifact['sha256'], 'complete ZIP hash mismatch')
    # The reviewed cohort evidence is immutable input, separate from adapter code.
    prior = subprocess.check_output(['git', 'show', EVIDENCE_COMMIT+':'+str((HERE/'cohort-validation.json').relative_to(check.ROOT))], cwd=check.ROOT)
    check.require(prior == (HERE/'cohort-validation.json').read_bytes(), 'cohort evidence changed')
    with zipfile.ZipFile(args.artifact) as z:
        check.require(z.testzip() is None, 'ZIP CRC mismatch')
        old = json.loads(z.read('fixture/fixture-lock.json'))
        check.require(old['source_tree_sha'] == ORIGINAL_METHOD and old['board'] == args.board, 'original method/board mismatch')
        check.require(old['spec_sha256'] == check.digest(PILOT/'matching-spec.json')
                      and old['matched_demands_sha256'] == check.digest(PILOT/'matched-demands.json'), 'frozen specification/manifest drift')
        # Authenticate every recovered before/context byte against its old fixture lock.
        for name, expected in old['files'].items():
            if name.startswith(('before/', 'context/')):
                check.require(hashlib.sha256(z.read('fixture/'+name)).hexdigest() == expected, 'retained fixture member drift')
        copy_prefix(z, 'fixture/before/', output/'before')
        copy_prefix(z, 'fixture/context/', output/'context')
    check.require(check.digest(output/'before/dump.json') == binding['dump_sha256'], 'recovered dump mismatch')
    check.require(check.digest(output/'before/osc-core.kicad_pcb') == binding['board_sha256'], 'recovered PCB mismatch')
    original_groups(check.read(output/'before/dump.json'), manifest, args.board)
    for phase in ('after', 'fresh'):
        shutil.copytree(output/'before', output/phase, ignore=shutil.ignore_patterns('*.kicad_pcb', '*.kicad_prl', '*.json', '*.log', '*.txt'))
    targets = {k: {'source_net': t['source_net'], 'net_token': t['net_token'], 'pads': [{x: p[x] for x in ('uuid', 'ref', 'pad')} for p in t['anchor_records']]}
               for k, t in manifest['domains']['F3']['targets'].items()}
    (output/'mapping.json').write_text(json.dumps({'pilot': {'targets': targets}, 'source_pcb_sha256': binding['board_sha256'], 'native_status': 'NOT RUN'}, indent=2)+'\n')
    plan = access_plan(check.read(output/'before/dump.json'), manifest)
    (output/'access-plan.json').write_text(json.dumps(plan, indent=2, sort_keys=True)+'\n')
    files = {str(p.relative_to(output)): check.digest(p) for p in sorted(output.rglob('*')) if p.is_file()}
    lock = {'domain': 'F3', 'board': args.board, 'spec_sha256': check.digest(PILOT/'matching-spec.json'),
            'matched_demands_sha256': check.digest(PILOT/'matched-demands.json'), 'tool_sha256': matching.tool_hashes(),
            'access_tool_sha256': method_hashes(), 'source_tree_sha': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=check.ROOT, text=True).strip(),
            'original_input_method_sha': ORIGINAL_METHOD, 'cohort_evidence_commit': EVIDENCE_COMMIT,
            'artifact': binding, 'recovery_artifact': artifact, 'files': files, 'native_status': 'NOT RUN'}
    (output/'fixture-lock.json').write_text(json.dumps(lock, indent=2, sort_keys=True)+'\n')
    validate(output, args.board, check.digest(output/'fixture-lock.json'))
    print(json.dumps({'fixture': str(output.relative_to(check.ROOT)), 'lock_sha256': check.digest(output/'fixture-lock.json'), 'files': len(files), 'board_sha256': binding['board_sha256'], 'native': 'NOT RUN'}))


if __name__ == '__main__':
    main()
