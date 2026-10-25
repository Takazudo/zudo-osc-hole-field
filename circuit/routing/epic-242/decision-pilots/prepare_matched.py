#!/usr/bin/env python3
"""Recover a private matched fixture from authenticated saved bytes; no KiCad."""
import argparse
import json
from pathlib import Path
import shutil
import subprocess
import sys
import zipfile
import check
import matching


def copy_prefix(archive, prefix, destination):
    for member in archive.namelist():
        if not member.startswith(prefix) or member.endswith('/'):
            continue
        relative = Path(member[len(prefix):])
        check.require(not relative.is_absolute() and '..' not in relative.parts, 'unsafe archive path')
        target = destination / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(archive.read(member))


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--artifacts', required=True, type=Path)
    p.add_argument('--domain', required=True, choices=('O1', 'F3', 'E1'))
    p.add_argument('--board', required=True)
    p.add_argument('--output', required=True, type=Path)
    args = p.parse_args()
    check.source_checks()
    # K's recovered library tables are rebound to the same frozen source bytes.
    subprocess.run([sys.executable, str(check.ROOT/'circuit/routing/epic-242/baseline/verify_inputs.py')], check=True)
    dumps, bindings = matching.load_dumps(args.artifacts)
    report = matching.build(dumps, bindings)
    matching.validate_published(report, check.read(check.HERE/'matched-demands.json'))
    domain = report['domains'][args.domain]
    check.require(args.board in domain['boards'], 'board outside matched domain')
    output = args.output.resolve()
    check.require(not output.exists(), 'new private output required; no overwrite/retry')
    if output.is_relative_to(check.ROOT):
        check.require(output.is_relative_to(check.SPLIT/'candidates/pilots/generated'), 'private repo-depth output required')
    receipt = bindings[args.board]
    with zipfile.ZipFile(args.artifacts/receipt['file']) as archive:
        if args.board == 'K1402':
            prefix = '.circuit-cache/osc-core-grid-189-compact-refill/'
            copy_prefix(archive, prefix, output/'before')
            for name in ('fp-lib-table', 'sym-lib-table'):
                path = output/'before'/name
                path.write_text(path.read_text().replace('${KIPRJMOD}/../../', '${KIPRJMOD}/../context/'))
            for name in ('symbols', 'footprints/kicad/zudo-osc-hole-field.pretty', 'scripts/schgen/fixtures'):
                shutil.copytree(check.ROOT/name, output/'context'/name)
        else:
            copy_prefix(archive, 'working-result/before/', output/'before')
            copy_prefix(archive, 'working-result/context/', output/'context')
    check.require(check.digest(output/'before/dump.json') == receipt['dump_sha256'], 'recovered dump differs')
    check.require(check.digest(output/'before/osc-core.kicad_pcb') == receipt['board_sha256'], 'recovered board differs')
    check.require((output/'context/symbols/zudo-osc-hole-field.kicad_sym').is_file(), 'missing context')
    settled = {key: check.digest(output/'before'/name) for key, name in
               [('board_sha256', 'osc-core.kicad_pcb'), ('drc_sha256', 'drc.json'), ('dump_sha256', 'dump.json')]}
    settled['status'] = 'RECOVERED AUTHENTICATED SAVED SETTLE; NOT A NEW NATIVE MEASUREMENT'
    (output/'before/settled-receipt.json').write_text(json.dumps(settled, indent=2)+'\n')
    for phase in ('after', 'fresh'):
        shutil.copytree(output/'before', output/phase,
                        ignore=shutil.ignore_patterns('*.kicad_pcb', '*.kicad_prl', '*.json', '*.log', '*.txt'))
    targets = {kind: {'source_net': row['source_net'], 'net_token': row['net_token'],
                      'pads': [{key: pad[key] for key in ('uuid', 'ref', 'pad')} for pad in row['anchor_records']]}
               for kind, row in domain['targets'].items()}
    (output/'mapping.json').write_text(json.dumps({'pilot': {'targets': targets},
                                                  'source_pcb_sha256': receipt['board_sha256'],
                                                  'native_status': 'NOT RUN; corrected #253 targets only'}, indent=2)+'\n')
    files = {str(path.relative_to(output)): check.digest(path) for path in sorted(output.rglob('*')) if path.is_file()}
    lock = {'domain': args.domain, 'board': args.board, 'spec_sha256': report['spec_sha256'],
            'matched_demands_sha256': check.digest(check.HERE/'matched-demands.json'),
            'tool_sha256': matching.tool_hashes(),
            'source_tree_sha': subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=check.ROOT, text=True).strip(),
            'artifact': receipt, 'files': files, 'native_status': 'NOT RUN',
            'context_note': 'K library table URI rewrite only; native parity recheck remains mandatory. Candidate context recovered byte-for-byte.'}
    (output/'fixture-lock.json').write_text(json.dumps(lock, indent=2)+'\n')
    print(json.dumps({'fixture': str(output), 'files': len(files), 'board_sha256': receipt['board_sha256'], 'native': 'NOT RUN'}))


if __name__ == '__main__':
    main()
