"""Disposable cut-topology measurement, always ineligible for copper adoption."""
import argparse
import json
import shutil
import subprocess
import sys
import time
from pathlib import Path

from prepare_diagnostic import BASELINE, BOARD, CUTS, HERE, ROOT, PREFIX, read, sha, write


def execute(archive, label, slot):
    if not slot or not label.startswith('251-') or any(c not in 'abcdefghijklmnopqrstuvwxyz0123456789-' for c in label):
        raise ValueError('parent-assigned slot and unique 251- label required')
    from prepare_diagnostic import prepare
    import zipfile
    probe = ROOT / '.circuit-cache' / (BOARD + '-grid-' + label + '-preflight')
    names = [label + suffix for suffix in ('-base', '-cut', '-fresh')]
    targets = [ROOT / '.circuit-cache' / (BOARD + '-grid-' + name) for name in names]
    if probe.exists() or any(p.exists() for p in targets):
        raise ValueError('workspace already exists; retain it and choose a new label')
    prepare(archive, probe)
    plan = read(HERE / 'diagnostic-plan.json')
    proposal = read(HERE / 'cut-proposal.json')
    if plan != read(probe / 'diagnostic-plan.json') or proposal != read(probe / 'cut-proposal.json'):
        raise ValueError('committed diagnostic differs from independently rebound inputs')
    if proposal['copper'] or proposal['removed_uuids'] != CUTS:
        raise ValueError('only the diagnosed cut-only negative is allowed')
    subprocess.run([sys.executable, str(BASELINE / 'verify_inputs.py')], cwd=ROOT, check=True)
    sys.path.insert(0, str(ROOT))
    from scripts.pcbgen import route_jack_grid as driver
    from scripts.pcbgen.copper_identity import retention
    from scripts.pcbgen.route_shards import delta
    source = ROOT / 'boards' / BOARD / (BOARD + '.kicad_pcb')
    original_context = {str(p.relative_to(source.parent)): sha(p.read_bytes())
                        for p in source.parent.rglob('*') if p.is_file() and
                        (p.suffix in ('.kicad_sch', '.kicad_dru', '.kicad_pro')
                         or p.name in ('fp-lib-table', 'sym-lib-table'))}
    source_hash = sha(source.read_bytes())
    receipt = {'status': 'RUNNING NEGATIVE DIAGNOSTIC; NOT ACCEPTABLE', 'adopted': False,
               'slot_assignment': slot, 'label': label, 'plan_sha256': sha((HERE / 'diagnostic-plan.json').read_bytes()),
               'published_board_sha256': source_hash, 'native_acceptance': 'NOT RUN',
               'complete_warning_audit': 'NOT RUN; cut-only diagnostic has no adoption audit',
               'boundary_obligations': plan['boundary_endpoints']}
    started = time.monotonic()
    write(probe / 'native-result.json', receipt)
    try:
        version = driver.run('bash', 'scripts/kicad/run.sh', 'kicad-cli', 'version').strip()
        if version != '10.0.6':
            raise ValueError('required KiCad 10.0.6 unavailable: ' + version)
        receipt['oracle_version'] = version
        base = driver.workspace(BOARD, names[0]) / source.name
        shutil.copyfile(source, base)
        base_drc, before = driver.check(base)
        with zipfile.ZipFile(archive) as z:
            retained = json.loads(z.read(PREFIX + 'dump.json'))
        if driver.connectivity_signature(before) != driver.connectivity_signature(retained):
            raise ValueError('fresh baseline differs from retained JR129; request coordinator epoch review')
        if any(v['severity'] == 'error' for v in base_drc['violations']) or base_drc['schematic_parity']:
            raise ValueError('fresh baseline DRC/parity failed')
        receipt.update(settled_board_sha256=sha(base.read_bytes()),
                       before_dump_sha256=sha(base.with_name('dump.json').read_bytes()))
        if sha(base.read_bytes()) != proposal['board_sha256']:
            raise ValueError('settled PCB bytes differ from source-bound proposal; never rewrite its hash')
        cut = driver.workspace(BOARD, names[1]) / source.name
        driver.run('bash', 'scripts/kicad/run.sh', 'python3', 'scripts/pcbgen/grid_apply.py',
                   driver.rel(base), str((HERE / 'cut-proposal.json').relative_to(ROOT)),
                   '--output', driver.rel(cut))
        cut_drc, after = driver.check(cut)
        fresh = driver.workspace(BOARD, names[2]) / source.name
        shutil.copyfile(cut, fresh)
        fresh_drc, verified = driver.check(fresh)
        keep = retention(before, after)
        if keep['removed_uuids'] != sorted(CUTS) or keep['added_objects'] or keep['changed_existing_uuids']:
            raise ValueError('cut-only transaction changed unexplained copper')
        if any(before[k] != after[k] for k in ('pads', 'edges', 'keepouts', 'layers')):
            raise ValueError('nonrouting dump geometry changed')
        victims = sorted({o['net'] for o in plan['removed_objects']})
        membership = driver.connected_pad_groups(before)
        receipt.update(status='MEASURED NEGATIVE DIAGNOSTIC; NEVER ADOPT',
                       native_acceptance='INELIGIBLE: cuts are deliberately not restored',
                       before_open_edges=before['open_edges'], cut_open_edges=after['open_edges'],
                       fresh_open_edges=verified['open_edges'],
                       settled_fresh_agreement=driver.connectivity_signature(after) == driver.connectivity_signature(verified),
                       candidate_sha256=sha(cut.read_bytes()), fresh_board_sha256=sha(fresh.read_bytes()),
                       cut_dump_sha256=sha(cut.with_name('dump.json').read_bytes()),
                       fresh_dump_sha256=sha(fresh.with_name('dump.json').read_bytes()),
                       retained_copper=keep, original_victim_pad_groups={n: membership[n] for n in victims},
                       native_cut_victim_components={n: after['islands'].get(n, []) for n in victims},
                       original_group_splits=driver.split_pad_groups(before, after),
                       settled_warnings=driver.warning_identities(cut_drc),
                       fresh_warnings=driver.warning_identities(fresh_drc),
                       new_warning_identities=sorted(set(driver.warning_identities(cut_drc))-set(driver.warning_identities(base_drc))),
                       native_errors=[v for v in cut_drc['violations'] if v['severity'] == 'error'],
                       schematic_parity=cut_drc['schematic_parity'],
                       fresh_native_errors=[v for v in fresh_drc['violations'] if v['severity'] == 'error'],
                       fresh_schematic_parity=fresh_drc['schematic_parity'],
                       fresh_retained_copper=retention(after, verified))
        write(probe / 'diagnostic-delta.json', delta(base.read_text(), cut.read_text()))
    except Exception as error:
        receipt.update(status='DIAGNOSTIC FAILED; NOT ACCEPTABLE', error=str(error))
        raise
    finally:
        receipt['elapsed_seconds'] = time.monotonic()-started
        write(probe / 'native-result.json', receipt)
        if sha(source.read_bytes()) != source_hash or any(sha((source.parent / p).read_bytes()) != h for p, h in original_context.items()):
            raise RuntimeError('canonical PCB/project context changed during diagnostic')
    print('Negative topology evidence:', probe / 'native-result.json')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive', type=Path)
    parser.add_argument('--label', required=True)
    parser.add_argument('--native-slot', help='parent-issued assignment; omit for source-only preflight')
    parser.add_argument('--execute', action='store_true')
    args = parser.parse_args()
    if args.execute:
        if not args.native_slot:
            parser.error('--execute requires the parent-issued --native-slot')
        execute(args.archive, args.label, args.native_slot)
    else:
        from prepare_diagnostic import prepare
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            plan = prepare(args.archive, Path(tmp))
        print(json.dumps({'status': 'SOURCE PREFLIGHT PASS; NATIVE NOT RUN',
                          'input_board_sha256': plan['input_board_sha256'],
                          'pipeline': ['pinned 10.0.6 version', 'settled baseline with retained membership comparison',
                                       'grid_apply.py exact cut proposal --output disposable candidate',
                                       'settled cut topology', 'independent fresh topology',
                                       'route_shards.delta and retention evidence'],
                          'adopted': False}, indent=2))


if __name__ == '__main__':
    main()
