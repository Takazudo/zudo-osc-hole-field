"""Independently reconcile a SHA-verified JR source pilot; never adopt its output."""
import argparse
import collections
import copy
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(HERE))
from pilot import check_netlists, physical, BOARD, REF
from scripts.pcbgen.netlist import read_netlist
from scripts.pcbgen.route_shards import copper_block_groups
from scripts.pcbgen.route_jack_grid import promotion_gate, connectivity_signature
from scripts.pcbgen.audit_zone_silk_scope import zone_metadata

read = lambda p: json.loads(Path(p).read_text())
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main(root, metadata, output):
    meta = read(metadata)
    if sha(meta['zip_path']) != meta['zip_sha256']:
        raise ValueError('artifact ZIP digest mismatch')
    cache = root / '.circuit-cache' if (root / '.circuit-cache').is_dir() else root
    result_root = cache / 'issue189-jr-source-adoption'
    result = read(result_root / 'result.json')
    if (result['source_commit'] != meta['source_commit'] or result['adopted'] is not False
            or result['status'] != 'SOURCE AND NATIVE CHECKED; REVIEW GENERATED PATCH BEFORE ADOPTION'
            or not result['source_regenerated'] or not result['all_canonical_pcbs_unchanged']):
        raise ValueError('worker is incomplete, failed or bound to another source')
    source = meta['source_commit']
    def git_sha(path):
        return hashlib.sha256(subprocess.check_output(['git', 'show', source + ':' + path], cwd=ROOT)).hexdigest()
    for path, expected in {**result['canonical_board_sha256'], **result['protected_source_sha256']}.items():
        if git_sha(path) != expected:
            raise ValueError('input manifest differs from immutable worker source: ' + path)
    if git_sha('design/grid/placements.lock.json') != result['fixed_lock_sha256']:
        raise ValueError('fixed lock hash mismatch')
    if git_sha(f'schematic/boards/{BOARD}.net') != sha(result_root / 'before.net'):
        raise ValueError('saved original netlist differs from immutable source')
    plan_root = ROOT / 'circuit/routing/issue189/jr-rb4413-edge-bridge'
    original = read(cache / 'issue189-rb4413-move/result.json')
    if original['plan_sha256'] != sha(plan_root / 'plan.json'):
        raise ValueError('reviewed replay plan mismatch')
    known = read(plan_root / 'native-result.json')['board_sha256']
    paths = dict(base=cache / f'{BOARD}-grid-189-jr-rb4413-base',
                 pilot=cache / f'{BOARD}-grid-189-jr-rb4413-fresh',
                 **{name: cache / f'{BOARD}-grid-189-source-{name}' for name in ('candidate', 'fresh', 'repeat')})
    files = {name: folder / (BOARD + '.kicad_pcb') for name, folder in paths.items()}
    if sha(files['base']) != known['base'] or sha(files['pilot']) != known['fresh']:
        raise ValueError('original native input or reviewed pilot bytes changed')
    dumps = {name: read(folder / 'dump.json') for name, folder in paths.items()}
    reports = {name: read(folder / 'drc.json') for name, folder in paths.items()}
    for name in paths:
        if dumps[name]['board_sha256'] != sha(files[name]) or reports[name].get('kicad_version') != '10.0.6':
            raise ValueError('native version/board dump binding mismatch')
        if any(v['severity'] == 'error' for v in reports[name]['violations']) or reports[name]['schematic_parity']:
            raise ValueError('native DRC/parity errors')
    change = read(plan_root / 'pending-source-translation.json')['translations'][0]
    part = change['expected_source']
    old_origin = f"{part['x_mm']},{part['y_mm']}"
    new_origin = f"{part['x_mm'] + change['delta_mm'][0]},{part['y_mm'] + change['delta_mm'][1]}"
    check_netlists(read_netlist(result_root / 'before.net', include_abstract=True),
                   read_netlist(result_root / 'after.net', include_abstract=True), old_origin, new_origin)
    for name in ('before', 'after'):
        if sha(result_root / (name + '.net')) != result[name + '_netlist_sha256']:
            raise ValueError('netlist receipt digest mismatch')
    expected_pads = copy.deepcopy(dumps['base']['pads'])
    for pad in expected_pads:
        if pad['ref'] == REF:
            pad['xy'] = [pad['xy'][0], pad['xy'][1] - 200000]
            pad['poly'] = [[x, y - 200000] for x, y in pad['poly']]
    texts = {name: file.read_text() for name, file in files.items()}
    copper = {name: collections.Counter(b for rows in copper_block_groups(text).values() for b in rows)
              for name, text in texts.items()}
    if sum(copper['base'].values()) != 51177 or copper['base'] - copper['pilot'] or sum((copper['pilot'] - copper['base']).values()) != 8:
        raise ValueError('reviewed original/additive copper scope mismatch')
    gates = {}
    for name in ('candidate', 'fresh', 'repeat'):
        if sha(files[name]) != result[name + '_sha256'] or dumps[name]['open_edges'] != 133:
            raise ValueError('post-source native board receipt mismatch')
        if dumps[name]['pads'] != expected_pads or any(dumps[name][k] != dumps['base'][k] for k in ('edges', 'keepouts', 'layers')):
            raise ValueError('unreviewed native pad/fixed-geometry change')
        if physical(texts['base'], old_origin) != physical(texts[name], new_origin):
            raise ValueError('unreviewed native metadata or physical change')
        if zone_metadata(texts['base']) != zone_metadata(texts[name]) or copper[name] != copper['pilot']:
            raise ValueError('zone metadata or successful copper changed')
        for suffix in ('.kicad_pro', '.kicad_dru'):
            if files['base'].with_suffix(suffix).read_bytes() != files[name].with_suffix(suffix).read_bytes():
                raise ValueError('native project/rules changed')
        gates[name] = promotion_gate(dumps['base'], dumps[name], reports['base'], reports[name])
        if not gates[name]['adopted'] or connectivity_signature(dumps[name]) != connectivity_signature(dumps['candidate']):
            raise ValueError('ordinary/fresh native gate rejected')
    if len({sha(files[n]) for n in ('candidate', 'fresh', 'repeat')}) != 1:
        raise ValueError('post-source board bytes are not deterministic')
    if files['fresh'].stat().st_size >= 95 * 1024 * 1024:
        raise ValueError('candidate requires separate native-checked publication compaction')
    patch = result_root / 'source.patch'
    if sha(patch) != result['source_patch_sha256'] or patch.read_bytes() != (result_root / 'generated.patch').read_bytes():
        raise ValueError('generated source patch differs from deterministic receipt')
    subprocess.run(['git', 'apply', '--check', str(patch)], cwd=ROOT, check=True)
    proof = dict(status='NATIVE SOURCE PILOT RECONCILED; GENERATED PATCH STILL REQUIRES REVIEW; NOT ADOPTED',
                 download=meta, native_version='10.0.6', gates=gates,
                 board_sha256={n: sha(p) for n, p in files.items()},
                 native_edges={n: d['open_edges'] for n, d in dumps.items()},
                 old_copper_retained=51177, exact_reviewed_additions=8, removed_copper=0,
                 source_patch_sha256=sha(patch), original_netlist_sha256=sha(result_root / 'before.net'),
                 regenerated_netlist_sha256=sha(result_root / 'after.net'),
                 all_native_drc_parity_zero=True, source_patch_applies_cleanly=True,
                 publication_bytes=files['fresh'].stat().st_size,
                 fresh_repeat_connectivity_and_bytes_agree=True)
    output.write_text(json.dumps(proof, indent=2) + '\n')
    print(json.dumps(proof, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('root', type=Path)
    parser.add_argument('metadata', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    main(args.root, args.metadata, args.output)
