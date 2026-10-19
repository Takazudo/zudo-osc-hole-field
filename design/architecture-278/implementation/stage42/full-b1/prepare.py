"""Prepare the full 31-electronics B1 trial, retaining Stage41 corrected poses."""
from pathlib import Path
from collections import Counter
import argparse
import copy
import hashlib
import json
import re
import shutil
import sys
import pcbnew
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "stage41/native-pilot"))
from identity_guard import inventory, compare, direct, kind, value, digest, bound_retirements
from native_guard import check_native

ROOT = Path(__file__).resolve().parents[5]
sys.path.insert(0, str(ROOT))
from scripts.pcbgen.uuid_tools import top_level_spans
REFS = {'U3101', 'U3102', 'U3103', *('C' + str(n) for n in range(3101, 3110)),
        *('R' + str(n) for n in range(3101, 3115)), *('D' + str(n) for n in range(3101, 3106))}


def prepare(directory):
    if directory.parent.resolve() != (ROOT / '.circuit-cache').resolve():
        raise ValueError('output must be a new direct child of ignored .circuit-cache')
    directory.mkdir(exist_ok=False)
    source = ROOT / 'boards/osc-jack-left/osc-jack-left.kicad_pcb'
    original = source.read_text()
    plan = json.loads((ROOT / 'design/architecture-278/implementation/stage40/mult-copper-plan/plan.json').read_text())
    if pcbnew.GetBuildVersion() != '10.0.6' or digest(original) != plan['native_board']['sha256']:
        raise ValueError('version or baseline mismatch')
    for p in source.parent.iterdir():
        if p.is_file() and (p.suffix in ('.kicad_pro', '.kicad_sch', '.kicad_dru') or p.name in ('fp-lib-table', 'sym-lib-table')):
            shutil.copy2(p, directory / p.name)
    shutil.copytree(source.parent / 'sheets', directory / 'sheets')
    moves = [copy.deepcopy(r) for r in plan['moves'] if r['ref'] in REFS]
    if len(moves) != 31 or {r['ref'] for r in moves} != REFS:
        raise ValueError('scope mismatch')
    private = {p['net'] for r in moves for p in r['old']['pads']} - {'AGND', '+12V', '-12V', '+5V', None, ''}
    # Explicit source-bound NC pads are preserved, never routed or retired.
    private -= {r['native_net'] for r in plan['NC_equivalence'] if r['ref'] in REFS}
    if not private <= {r['net'] for r in plan['private_net_retire_copper']}:
        raise ValueError('nonprivate net retirement')
    retired = [r for r in plan['private_net_retire_copper'] if r['net'] in private]
    bound_retirements({'retired_private_copper': retired}, original)
    retire_by_index = {r['index']: r for r in retired}
    changes = []
    for index, (a, z) in enumerate(top_level_spans(original)):
        if index in retire_by_index:
            if digest(original[a:z]) != retire_by_index[index]['sha256']:
                raise ValueError('retirement occurrence mismatch')
            changes.append((a, z))
    raw = original
    for a, z in reversed(changes):
        raw = raw[:a] + raw[z:]
    before = inventory(original)
    retired_hashes = [r['sha256'] for r in retired]
    if not compare(before, inventory(raw), retired_hashes)['accepted']:
        raise ValueError('preload retirement mismatch')
    board_path = directory / source.name
    board_path.write_text(raw)
    board = pcbnew.LoadBoard(str(board_path))
    check_native(board, raw)
    fps = {f.GetReference(): f for f in board.GetFootprints()}
    owners = {n: sorted({f.GetReference() for f in board.GetFootprints() for p in f.Pads() if p.GetNetname() == n}) for n in private}
    if any(not set(refs) <= set(plan['candidate_B1']) for refs in owners.values()):
        raise ValueError('foreign private-net owner')
    poses = []
    for row in moves:
        f = fps[row['ref']]
        pose = copy.deepcopy(row['proposed'])
        # Limited trial corrections; no foreign/fixed or B2 movement.
        if row['ref'] == 'R3109':
            old = row['old']
            pose.update(origin=old['origin'], layer=old['layer'], study_clockwise_angle=
                        (-old['native_angle'] if old['layer'] == 'F.Cu' else 180-old['native_angle']) % 360)
        elif row['ref'] == 'C3101':
            pose['origin'][0] += 1.0
        elif row['ref'] in ('U3102', 'C3106', 'C3107'):
            pose['origin'][1] += .2
        # First full-cell native DRC: six rail-clearance conflicts. Adjust only
        # proposed B1 electronics; keep the U3101 bypass cluster rigid.
        if row['ref'] in ('U3101', 'C3104', 'C3105'):
            pose['origin'][1] -= .2
        elif row['ref'] == 'D3102':
            pose['origin'][1] -= .4
        elif row['ref'] == 'R3103':
            pose['origin'][1] -= .1
        elif row['ref'] == 'R3104':
            # Closest passing 0.25mm-grid native-shape proposal; full DRC still
            # mandatory. Search retains all neighboring geometry unchanged.
            pose['origin'] = [12.75, 137.5]
        layer = board.GetLayerID(pose['layer'])
        if f.GetLayer() != layer:
            f.Flip(f.GetPosition(), pcbnew.FLIP_DIRECTION_LEFT_RIGHT)
        angle = (-pose['study_clockwise_angle'] if layer == pcbnew.F_Cu else 180-pose['study_clockwise_angle']) % 360
        f.SetOrientationDegrees(angle)
        f.SetPosition(pcbnew.VECTOR2I(*(pcbnew.FromMM(v + d) for v, d in zip(pose['origin'], (100, 50)))))
        poses.append({'ref': row['ref'], 'origin': pose['origin'], 'layer': pose['layer'], 'native_angle': angle,
                      'pads': [{'pin': p.GetNumber(), 'uuid': p.m_Uuid.AsString(), 'net': p.GetNetname(),
                                'xy_mm': [pcbnew.ToMM(p.GetPosition().x), pcbnew.ToMM(p.GetPosition().y)]} for p in f.Pads()]})
    check_native(board, raw)
    serialized = directory / 'native-serialization.kicad_pcb'
    pcbnew.SaveBoard(str(serialized), board)
    check_native(board, raw)
    generated = {}
    serialized_text = serialized.read_text()
    for a, z in top_level_spans(serialized_text):
        part = serialized_text[a:z]
        if kind(part) == 'footprint':
            ref = re.search(r'\(property\s+"Reference"\s+"([^"\\]*)"', part)[1]
            if ref in REFS:
                generated[ref] = part
    replacements = []
    for a, z in top_level_spans(raw):
        part = raw[a:z]
        if kind(part) == 'footprint':
            ref = re.search(r'\(property\s+"Reference"\s+"([^"\\]*)"', part)[1]
            if ref in REFS:
                replacements.append((a, z, generated[ref]))
    for a, z, part in reversed(replacements):
        raw = raw[:a] + part + raw[z:]
    guard = compare(before, inventory(raw), retired_hashes)
    if not guard['accepted']:
        raise ValueError('complete identity gate failed')
    board_path.write_text(raw)
    # Raw footprint/other-object preservation is checked in addition to nets.
    def untouched(text):
        rows = Counter()
        for a, z in top_level_spans(text):
            part = text[a:z]
            if kind(part) == 'footprint' and re.search(r'\(property\s+"Reference"\s+"([^"\\]*)"', part)[1] in REFS:
                continue
            rows[digest(part)] += 1
        return rows
    expected = untouched(original)
    expected.subtract(retired_hashes)
    if +expected != untouched(raw) or digest(source.read_text()) != digest(original):
        raise ValueError('unrelated bytes changed')
    prepared_inventory = inventory(raw)
    receipt = {'status': 'DISPOSABLE; native DRC/connectivity pending', 'canonical_sha256': digest(original),
               'candidate_sha256': digest(raw), 'scope_refs': sorted(REFS), 'poses': poses,
               'prepared_footprint_hashes': {r: prepared_inventory['footprints'][r] for r in REFS},
               'private_net_owners': owners, 'retired_private_copper': retired,
               'shared_copper_retired': 0, 'identity_guard': guard, 'other_objects_byte_preserved': True}
    (directory / 'prepare-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'candidate': str(board_path), 'retired': len(retired), 'identity_guard': guard}, indent=2))


if __name__ == '__main__':
    p = argparse.ArgumentParser(); p.add_argument('directory', type=Path); a = p.parse_args()
    prepare(a.directory)
