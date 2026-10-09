"""Regenerate and natively verify JR133 in disposable copies; never publish copper."""
import collections
import copy
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
from scripts.pcbgen.netlist import read_netlist
from scripts.pcbgen.uuid_tools import top_level_spans

BOARD = 'osc-jack-right'
REF = 'RB4413'
PILOT = ROOT / 'circuit/routing/issue189/jr-rb4413-edge-bridge'
READ = lambda p: json.loads(Path(p).read_text())
SHA = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def check_netlists(before, after, old_origin, new_origin):
    old, old_pins = before
    new, new_pins = after
    if old_pins != new_pins:
        raise ValueError('source regeneration changed pin/net assignments')
    old = {c.ref: c for c in old}
    new = {c.ref: c for c in new}
    if old.keys() != new.keys():
        raise ValueError('source regeneration changed components')
    for ref, component in new.items():
        if ref == REF:
            if dict(old[ref].fields).get('FootprintOriginMm') != old_origin or dict(component.fields).get('FootprintOriginMm') != new_origin:
                raise ValueError('reviewed source origin does not match netlist')
            component = replace(component, fields=tuple(
                (key, old_origin if key == 'FootprintOriginMm' else value)
                for key, value in component.fields))
        if component != old[ref]:
            raise ValueError('unreviewed component/source-field change: ' + ref)


def physical(text, expected_origin):
    rows = []
    seen = 0
    for a, b in top_level_spans(text):
        block = text[a:b]
        if block.startswith(('(segment', '(via', '(zone')):
            continue
        if block.startswith('(footprint') and re.search(r'\(property "Reference" "RB4413"', block):
            seen += 1
            block = re.sub(r'(\(at)\s+[^\s)]+\s+[^\s)]+([^)]*\))',
                           r'\1 REVIEWED_X REVIEWED_Y\2', block, count=1)
            pattern = r'(\(property "FootprintOriginMm" )("(?:\\.|[^"\\])*")'
            matches = list(re.finditer(pattern, block))
            if len(matches) != 1 or json.loads(matches[0][2]) != expected_origin:
                raise ValueError('unexpected native source-origin field')
            block = re.sub(pattern, r'\1"REVIEWED_SOURCE_ORIGIN"', block, count=1)
        rows.append(block)
    if seen != 1:
        raise ValueError('missing/ambiguous reviewed footprint')
    return collections.Counter(rows)


def main():
    from scripts.pcbgen import route_jack_grid as driver
    from scripts.pcbgen.route_shards import copper_block_groups
    from scripts.pcbgen.audit_zone_silk_scope import zone_metadata
    from scripts.checks.routing_placement_translations import apply_translations

    out = ROOT / '.circuit-cache/issue189-jr-source-adoption'
    if subprocess.check_output(['git', 'status', '--porcelain'], cwd=ROOT, text=True).strip():
        raise ValueError('requires clean committed worker input')
    for pattern in (f'{BOARD}-grid-189-jr-rb4413-*', f'{BOARD}-grid-189-source-*', 'issue189-rb4413-move'):
        if list((ROOT / '.circuit-cache').glob(pattern)):
            raise ValueError('refuse to replace an earlier pilot workspace')
    out.mkdir(parents=True, exist_ok=False)
    receipt = dict(status='RUNNING; NOT ADOPTED', adopted=False, source_regenerated=False,
                   source_commit=subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=ROOT, text=True).strip())
    boards = {str(p.relative_to(ROOT)): SHA(p) for p in (ROOT / 'boards').rglob('*.kicad_pcb')}
    receipt['canonical_board_sha256'] = boards
    (out / 'result.json').write_text(json.dumps(receipt, indent=2) + '\n')
    lock = ROOT / 'design/grid/placements.lock.json'
    lock_sha = SHA(lock)
    floor = ROOT / 'design/partition/floorplan-candidate.json'
    adjustment = ROOT / 'design/partition/routing-placement-translations.json'
    netlist = ROOT / 'schematic/boards' / (BOARD + '.net')
    protected = [*list((ROOT / 'design/boards').glob('*.json')),
                 ROOT / 'design/partition/partition-input.json',
                 *(p for p in (ROOT / 'schematic/boards').glob('*.net') if p != netlist)]
    protected_sha = {str(p.relative_to(ROOT)): SHA(p) for p in protected}
    old_rows = READ(floor)['placements']
    old_netlist = read_netlist(netlist, include_abstract=True)
    shutil.copyfile(netlist, out / 'before.net')
    old_origin = dict(next(c for c in old_netlist[0] if c.ref == REF).fields)['FootprintOriginMm']
    try:
        if READ(adjustment) != dict(schema_version=1, translations=[]):
            raise ValueError('source translation input is not the reviewed empty baseline')
        changes = READ(PILOT / 'pending-source-translation.json')
        changes['translations'][0]['evidence'] = 'circuit/routing/issue189/jr-rb4413-edge-bridge/native-result.json; circuit/routing/issue189/jr-source-adoption native source/copper receipts required'
        expected_rows = apply_translations(old_rows, READ(ROOT / 'design/partition/partition-input.json'), changes,
            headers=READ(ROOT / 'design/partition/connector-packing-candidate.json')['headers'])
        expected_part = next(p for p in expected_rows if p['ref'] == REF)
        new_origin = f"{expected_part['x_mm']},{expected_part['y_mm']}"
        driver.run('python3', str(PILOT / 'pilot.py'))
        original_pilot = READ(ROOT / '.circuit-cache/issue189-rb4413-move/result.json')
        if not (original_pilot['gate']['adopted'] and original_pilot['fresh_gate']['adopted'] and original_pilot['fresh_agreement']):
            raise ValueError('reviewed disposable pilot did not reproduce')
        if original_pilot['fresh_sha256'] != 'ae6e998c8b490394c6d3f7e2749e7d1521b4f9c6120067358a6bdf766cead5ff':
            raise ValueError('reviewed native pilot bytes differ; investigate before source adoption')
        base = ROOT / '.circuit-cache' / f'{BOARD}-grid-189-jr-rb4413-base' / (BOARD + '.kicad_pcb')
        pilot = ROOT / '.circuit-cache' / f'{BOARD}-grid-189-jr-rb4413-fresh' / base.name
        before = READ(base.with_name('dump.json'))
        before_drc = READ(base.with_name('drc.json'))
        if before_drc.get('kicad_version') != '10.0.6':
            raise ValueError('baseline native version differs from pinned oracle')
        receipt['native_version'] = before_drc['kicad_version']
        adjustment.write_text(json.dumps(changes, indent=2) + '\n')

        def regenerate():
            print('Regenerating reviewed source translation', flush=True)
            driver.run('bash', 'scripts/partition/regen.sh')
            driver.run('bash', 'scripts/schgen/regen-boards.sh')
            if READ(floor)['placements'] != expected_rows or SHA(lock) != lock_sha:
                raise ValueError('source regeneration changed unreviewed placement/fixed hardware')
            if protected_sha != {str(p.relative_to(ROOT)): SHA(p) for p in protected}:
                raise ValueError('source regeneration changed another board or physical definition')
            check_netlists(old_netlist, read_netlist(netlist, include_abstract=True), old_origin, new_origin)
            driver.run('python3', '-m', 'unittest', 'scripts.checks.test_routing_placement_translations', 'scripts.pcbgen.test_placement_geometry')

        regenerate()
        source_patch = subprocess.check_output(['git', 'diff', '--binary'], cwd=ROOT)
        (out / 'source.patch').write_bytes(source_patch)
        shutil.copyfile(netlist, out / 'after.net')
        candidate = driver.workspace(BOARD, '189-source-candidate') / base.name
        shutil.copyfile(pilot, candidate)

        def sync(path):
            driver.run('bash', 'scripts/kicad/run.sh', 'python3', 'scripts/pcbgen/sync.py', BOARD, '--output', driver.rel(path))
            driver.run('bash', 'scripts/kicad/run.sh', 'python3', 'scripts/pcbgen/place.py', BOARD, '--board', driver.rel(path))

        sync(candidate)
        after_drc, after = driver.check(candidate)
        fresh = driver.workspace(BOARD, '189-source-fresh') / base.name
        shutil.copyfile(candidate, fresh)
        fresh_drc, verified = driver.check(fresh)
        regenerate()
        if subprocess.check_output(['git', 'diff', '--binary'], cwd=ROOT) != source_patch:
            raise ValueError('source regeneration is not byte-deterministic')
        repeat = driver.workspace(BOARD, '189-source-repeat') / base.name
        shutil.copyfile(fresh, repeat)
        sync(repeat)
        repeat_drc, repeated = driver.check(repeat)
        expected_pads = copy.deepcopy(before['pads'])
        for pad in expected_pads:
            if pad['ref'] == REF:
                pad['xy'] = [pad['xy'][0], pad['xy'][1] - 200000]
                pad['poly'] = [[x, y - 200000] for x, y in pad['poly']]
        copper = lambda path: collections.Counter(block for blocks in copper_block_groups(path.read_text()).values() for block in blocks)
        old_copper = copper(base)
        expected_copper = copper(pilot)
        if sum(old_copper.values()) != 51177 or old_copper - expected_copper or sum((expected_copper - old_copper).values()) != 8:
            raise ValueError('reviewed copper scope differs')
        gates = {}
        for label, path, drc, dump in (('candidate', candidate, after_drc, after), ('fresh', fresh, fresh_drc, verified), ('repeat', repeat, repeat_drc, repeated)):
            if drc.get('kicad_version') != '10.0.6':
                raise ValueError('post-source native version differs from pinned oracle')
            gates[label] = driver.promotion_gate(before, dump, before_drc, drc)
            if not gates[label]['adopted'] or dump['open_edges'] != 133:
                raise ValueError('post-source ordinary native promotion gate rejected')
            if dump['pads'] != expected_pads or any(dump[k] != before[k] for k in ('edges', 'keepouts', 'layers')):
                raise ValueError('post-source physical pad/outline/layer change is unreviewed')
            if physical(base.read_text(), old_origin) != physical(path.read_text(), new_origin):
                raise ValueError('post-source nonrouting metadata/geometry changed beyond reviewed origin')
            if zone_metadata(base.read_text()) != zone_metadata(path.read_text()) or copper(path) != expected_copper:
                raise ValueError('post-source zone metadata or successful copper changed')
            for suffix in ('.kicad_pro', '.kicad_dru'):
                if base.with_suffix(suffix).read_bytes() != path.with_suffix(suffix).read_bytes():
                    raise ValueError('post-source native project/rules changed')
            if driver.connectivity_signature(dump) != driver.connectivity_signature(after):
                raise ValueError('post-source fresh/repeat connectivity disagreement')
        if len({SHA(p) for p in (candidate, fresh, repeat)}) != 1:
            raise ValueError('post-source sync/refill board bytes are not deterministic')
        receipt.update(status='SOURCE AND NATIVE CHECKED; REVIEW GENERATED PATCH BEFORE ADOPTION',
                       source_regenerated=True, gates=gates, open_edges_before=before['open_edges'],
                       open_edges_after=133, retained_copper=51177, added_copper=8, removed_copper=0,
                       candidate_sha256=SHA(candidate), fresh_sha256=SHA(fresh), repeat_sha256=SHA(repeat),
                       source_patch_sha256=SHA(out / 'source.patch'), source_translation_sha256=SHA(adjustment),
                       before_netlist_sha256=SHA(out / 'before.net'), after_netlist_sha256=SHA(out / 'after.net'),
                       fixed_lock_sha256=lock_sha, protected_source_sha256=protected_sha,
                       old_origin=old_origin, new_origin=new_origin, source_and_sync_deterministic=True)
    except Exception as error:
        receipt.update(status='ERROR; NOT ADOPTED', error=repr(error))
        raise
    finally:
        (out / 'generated.patch').write_bytes(subprocess.check_output(['git', 'diff', '--binary'], cwd=ROOT))
        receipt['changed_source_paths'] = subprocess.check_output(['git', 'diff', '--name-only'], cwd=ROOT, text=True).splitlines()
        unchanged = boards == {str(p.relative_to(ROOT)): SHA(p) for p in (ROOT / 'boards').rglob('*.kicad_pcb')}
        receipt['all_canonical_pcbs_unchanged'] = unchanged
        if not unchanged:
            receipt.update(status='ERROR; CANONICAL PCB MUTATION; NEVER ADOPT', source_regenerated=False)
        (out / 'result.json').write_text(json.dumps(receipt, indent=2) + '\n')
        if not unchanged:
            raise ValueError('canonical PCB mutation detected; never adopt this worker output')


if __name__ == '__main__':
    main()
