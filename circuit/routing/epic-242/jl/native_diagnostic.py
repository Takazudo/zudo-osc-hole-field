"""Optional admitted baseline/fresh measurement; never route or adopt copper."""
import argparse
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

from prepare_diagnostic import (BASELINE, BOARD, HERE, ROOT, authenticate, encoded,
                                prepare, probe_masks, read, sha, validate_dump)


def require_admission(slot, label):
    if not slot or not label.startswith('250-') or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in label):
        raise ValueError('explicit parent slot and unique 250- label required')
    worker = os.environ.get('EPIC242_NATIVE_WORKER', '')
    slice_name = os.environ.get('EPIC242_NATIVE_SLICE', '')
    if not worker or not slice_name or not os.environ.get('EPIC242_NATIVE_DEADLINE'):
        raise ValueError('qualified parent-reviewed bounded guard required; no direct execution')
    if (not 1 <= len(worker) <= 61 or worker[0] not in 'abcdefghijklmnopqrstuvwxyz0123456789'
            or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in worker)
            or slice_name != 'epic242-w' + worker.encode('ascii').hex() + '.slice'):
        raise ValueError('invalid bounded worker identity')
    lines = Path('/proc/self/cgroup').read_text().splitlines()
    unified = [line[3:] for line in lines if line.startswith('0::')]
    expected = '/epic242.slice/' + slice_name
    if len(unified) != 1 or not unified[0].startswith(expected + '/'):
        raise ValueError('driver is outside the assigned cgroupv2 slice')
    relative = Path(unified[0].lstrip('/'))
    slice_path = next((p for p in (relative, *relative.parents) if p.name == slice_name), None)
    if slice_path is None:
        raise ValueError('assigned bounded cgroup unavailable')
    cgroup = Path('/sys/fs/cgroup') / slice_path
    if (cgroup / 'memory.max').read_text().strip() != '6442450944' or (
            cgroup / 'memory.swap.max').read_text().strip() != '0':
        raise ValueError('whole-worker 6 GiB/no-swap cap is not enforced')
    parent = Path('/sys/fs/cgroup/epic242.slice')
    if (parent / 'memory.max').read_text().strip() != '12884901888' or (
            parent / 'memory.swap.max').read_text().strip() != '0':
        raise ValueError('aggregate 12 GiB/no-swap cap is not enforced')
    if time.time() >= int(os.environ['EPIC242_NATIVE_DEADLINE']):
        raise ValueError('native deadline expired')


def execute(archive, label, slot):
    require_admission(slot, label)
    tooling = read(HERE / 'tooling-reconciliation.json')
    for name, expected in tooling['reviewed_current_tool_sha256'].items():
        if sha((ROOT / name).read_bytes()) != expected:
            raise ValueError('current reviewed wrapper/guard seal unavailable; historical input remains source-only')
    # Fail on source drift before importing anything that can launch KiCad.
    prepare(archive, HERE, check=True)
    retained, endpoints, _ = authenticate(archive)
    plan = read(HERE / 'diagnostic-plan.json')
    names = [label + '-base', label + '-fresh']
    targets = [ROOT / '.circuit-cache' / (BOARD + '-grid-' + n) for n in names]
    receipt_dir = ROOT / '.circuit-cache' / (BOARD + '-grid-' + label + '-receipt')
    if receipt_dir.exists() or any(p.exists() for p in targets):
        raise ValueError('existing evidence cannot be overwritten; choose a new admitted label')
    subprocess.run([sys.executable, str(BASELINE / 'verify_inputs.py')], cwd=ROOT, check=True)
    sys.path.insert(0, str(ROOT))
    from scripts.pcbgen import route_jack_grid as driver
    from scripts.pcbgen.copper_identity import retention
    from scripts.pcbgen.route_shards import delta
    source = ROOT / 'boards' / BOARD / (BOARD + '.kicad_pcb')
    source_hash = sha(source.read_bytes())
    receipt = {'status': 'RUNNING BASELINE DIAGNOSTIC; NEVER ADOPT', 'adopted': False,
               'slot': slot, 'label': label, 'published_board_sha256': source_hash,
               'plan_sha256': sha((HERE / 'diagnostic-plan.json').read_bytes()),
               'native_acceptance': 'NOT RUN', 'complete_warning_audit': 'NOT RUN',
               'search_executed': False, 'cuts': [], 'added_copper': []}
    receipt_dir.mkdir(parents=True)
    started = time.monotonic()
    try:
        version = driver.run('bash', 'scripts/kicad/run.sh', 'kicad-cli', 'version').strip()
        if version != '10.0.6':
            raise ValueError('pinned KiCad 10.0.6 required')
        measured = []
        for index, name in enumerate(names):
            board = driver.workspace(BOARD, name) / source.name
            shutil.copyfile(source if index == 0 else measured[0][0], board)
            drc, dump = driver.check(board)
            validate_dump(dump, endpoints)
            if driver.connectivity_signature(dump) != driver.connectivity_signature(retained):
                raise ValueError('retained/full native topology drift; coordinator epoch review required')
            if sha(board.read_bytes()) != source_hash:
                raise ValueError('settled board byte drift; retain and report separately')
            if any(v['severity'] == 'error' for v in drc['violations']) or drc['schematic_parity']:
                raise ValueError('native baseline DRC/parity failed')
            if probe_masks(dump) != plan['diagnostic']:
                raise ValueError('fresh first-via masks changed; do not silently rebind')
            measured.append((board, dump, drc))
        before, fresh = measured
        replay = delta(source.read_text(), fresh[0].read_text())
        if replay['removed'] or replay['added']:
            raise ValueError('no-copper baseline diagnostic changed copper')
        receipt.update(status='BASELINE/FRESH NEGATIVE MASK REPRODUCED; NEVER ADOPT',
                       oracle_version=version, native_acceptance='NOT APPLICABLE: no copper candidate',
                       settled_fresh_agreement=True, retained_copper=retention(before[1], fresh[1]),
                       measurements=[{'directory': str(b.parent.relative_to(ROOT)),
                                      'settled_board_sha256': sha(b.read_bytes()),
                                      'native_dump_sha256': sha(b.with_name('dump.json').read_bytes()),
                                      'native_drc_sha256': sha(b.with_name('drc.json').read_bytes()),
                                      'open_edges': d['open_edges'],
                                      'raw_warning_identity_count': len(driver.warning_identities(c)),
                                      'raw_warning_identities': driver.warning_identities(c)}
                                     for b, d, c in measured])
        (receipt_dir / 'no-copper-delta.json').write_bytes(encoded(replay))
    except Exception as error:
        receipt.update(status='DIAGNOSTIC FAILED; NOT ACCEPTABLE', error=str(error))
        raise
    finally:
        receipt['elapsed_seconds'] = time.monotonic() - started
        receipt['artifact_files_sha256'] = {str(p.relative_to(ROOT)): sha(p.read_bytes())
                                           for folder in targets for p in sorted(folder.rglob('*')) if p.is_file()}
        (receipt_dir / 'native-result.json').write_bytes(encoded(receipt))
        if sha(source.read_bytes()) != source_hash or any(
                sha((source.parent / n).read_bytes()) != h for n, h in endpoints['context_files'].items()):
            raise RuntimeError('canonical PCB or native project context changed')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--label', required=True)
    parser.add_argument('--native-slot')
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    if args.execute:
        if not args.native_slot:
            parser.error('--execute requires explicit parent slot; no slot is assigned')
        execute(args.archive, args.label, args.native_slot)
    else:
        prepare(args.archive, HERE, check=True)
        print('SOURCE PREFLIGHT PASS; NATIVE NOT RUN; no admission or copper adoption')
