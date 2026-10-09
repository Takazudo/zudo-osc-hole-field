"""Read-only, uncapped hole-warning evidence from bounded native fixtures.

This does not replace full-board DRC or change promotion eligibility. Only boards
with global hole clearance and no custom hole constraints are supported. Every
potentially violating pair is covered by a native fixture with at most 14 holes
(at most 182 reports including repeated via/pad pairs, below KiCad 10.0.6's 199-report cap). Source hole geometry,
native types/layers, net names, project and custom-rule bytes are preserved.
"""
from __future__ import annotations

import argparse
import collections
import hashlib
import json
import math
from pathlib import Path
import re
import shutil
import subprocess


def possible_pairs(holes, clearance):
    """Integer conservative spatial cover; epsilon can only reduce violations."""
    if clearance < 0:
        raise ValueError('negative clearance')
    size = max([h['radius'] * 2 for h in holes] + [1]) + clearance
    bins = collections.defaultdict(list)
    pairs = []
    for i, h in enumerate(holes):
        x, y = h['xy']; bx, by = x // size, y // size
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for j in bins[bx + dx, by + dy]:
                    other = holes[j]
                    radius = clearance + h['radius'] + other['radius']
                    if sum((a-b)**2 for a,b in zip(h['xy'], other['xy'])) <= radius**2:
                        pairs.append((j, i))
        bins[bx, by].append(i)
    return pairs


def pack_pairs(pairs, limit=14, uuids=None):
    if not 2 <= limit <= 14:
        raise ValueError('fixture must stay below the native per-code cap')
    groups = []; current = set()
    for pair in pairs:
        if uuids and len({uuids[i] for i in pair}) != len(set(pair)):
            raise ValueError('nearby duplicate UUID pair needs a separate native identity strategy')
        combined=current | set(pair)
        ambiguous=uuids is not None and len({uuids[i] for i in combined}) != len(combined)
        if len(combined) > limit or ambiguous:
            groups.append(sorted(current)); current = set()
        current.update(pair)
    if current:
        groups.append(sorted(current))
    covered = {p for group in groups for p in pairs if set(p) <= set(group)}
    if covered != set(pairs):
        raise AssertionError('pair coverage incomplete')
    return groups


def native_holes(board, pcbnew):
    items = list(board.GetTracks()) + [p for f in board.GetFootprints() for p in f.Pads()]
    rows = []; objects = {}
    for item in items:
        if item.Type() == pcbnew.PCB_VIA_T:
            drill = item.GetDrillValue()
            kind = 'via'; subtype = int(item.GetViaType())
        elif item.Type() == pcbnew.PCB_PAD_T:
            drill_size = item.GetDrillSize()
            # Exact hole-provider scope: slots are milled, not round drilled holes.
            if not item.HasDrilledHole() or drill_size.x <= 0 or drill_size.x != drill_size.y:
                continue
            drill = drill_size.x; kind = 'pad'; subtype = int(item.GetAttribute())
        else:
            continue
        uid = item.m_Uuid.AsString()
        row=dict(uuid=uid, kind=kind, subtype=subtype,
                         xy=[item.GetPosition().x, item.GetPosition().y], radius=drill//2,
                         drill=drill, layers=list(item.GetLayerSet().Seq()), net=item.GetNetname())
        key=hashlib.sha256(json.dumps(row,sort_keys=True).encode()).hexdigest()
        if key in objects:
            raise ValueError('identical duplicate hole objects require explicit multiplicity handling')
        row['object_key']=key;objects[key]=item;rows.append(row)
    return sorted(rows, key=lambda h:(h['uuid'],h['object_key'])), objects


def make_fixture(source, objects, selected, path, pcbnew):
    board = pcbnew.BOARD()
    board.SetCopperLayerCount(source.GetCopperLayerCount())
    board.SetEnabledLayers(source.GetEnabledLayers())
    nets = {}
    for uid in selected:
        name = objects[uid].GetNetname()
        if name not in nets:
            net = pcbnew.NETINFO_ITEM(board, name); board.Add(net); nets[name] = net
    selected_uuids={objects[k].m_Uuid.AsString() for k in selected}
    if len(selected_uuids)!=len(selected):raise ValueError('fixture UUIDs must be unambiguous')
    footprints = {}
    for uid in selected:
        item = objects[uid]
        if item.Type() == pcbnew.PCB_VIA_T:
            clone = pcbnew.Cast_to_PCB_VIA(pcbnew.Cast_to_BOARD_ITEM(item.Clone())); clone.SetParent(board)
            clone.SetNet(nets[item.GetNetname()]); board.Add(clone)
        else:
            fp = item.GetParentFootprint(); key = fp.m_Uuid.AsString()
            if key not in footprints:
                clone = pcbnew.Cast_to_FOOTPRINT(pcbnew.Cast_to_BOARD_ITEM(fp.Clone())); clone.SetParent(board)
                for pad in list(clone.Pads()):
                    if pad.m_Uuid.AsString() not in selected_uuids:
                        clone.Remove(pad)
                    else:
                        pad.SetNet(nets[pad.GetNetname()])
                board.Add(clone); footprints[key] = clone
    pcbnew.SaveBoard(str(path), board)
    return board


def restore_fixture_context(source_path, fixture):
    # SaveBoard on a newly constructed BOARD writes a default project. Restore
    # the reviewed context only after serialization, before loading/running DRC.
    for suffix in ('.kicad_pro', '.kicad_dru'):
        shutil.copyfile(source_path.with_suffix(suffix), fixture.with_suffix(suffix))


def verify_fixture_context(source_path, fixture):
    for suffix in ('.kicad_pro', '.kicad_dru'):
        if source_path.with_suffix(suffix).read_bytes() != fixture.with_suffix(suffix).read_bytes():
            raise ValueError('native fixture context changed: ' + suffix)


def audit(path, output):
    import pcbnew
    version = subprocess.check_output(['kicad-cli','version'], text=True).strip()
    if version != '10.0.6':
        raise ValueError('requires pinned KiCad 10.0.6, got ' + version)
    project = path.with_suffix('.kicad_pro'); rules = path.with_suffix('.kicad_dru')
    rule_text = rules.read_text()
    if re.search(r'\(constraint\s+(?:hole|drilled)', rule_text):
        raise ValueError('custom hole constraints require a separate complete rule-equivalence proof')
    settings = json.loads(project.read_text())['board']['design_settings']
    # Restrict the audit to the reviewed project rather than guessing rule defaults.
    minimum = settings['rules']['min_hole_to_hole']
    clearance = math.ceil(minimum * 1_000_000)
    source = pcbnew.LoadBoard(str(path))
    holes, objects = native_holes(source, pcbnew)
    pairs = possible_pairs(holes, clearance); groups = pack_pairs(pairs,uuids=[h['uuid'] for h in holes])
    output.mkdir(parents=True, exist_ok=True)
    identities = set(); object_identities=set(); receipts = []
    for i, group in enumerate(groups):
        folder = output / f'fixture-{i:04d}'; folder.mkdir(exist_ok=True)
        fixture = folder / path.name
        selected = {holes[j]['object_key'] for j in group}
        uuid_to_key={holes[j]['uuid']:holes[j]['object_key'] for j in group}
        make_fixture(source, objects, selected, fixture, pcbnew)
        restore_fixture_context(path, fixture)
        actual, _ = native_holes(pcbnew.LoadBoard(str(fixture)), pcbnew)
        expected = [h for h in holes if h['object_key'] in selected]
        if actual != expected:
            raise ValueError('fixture changed native hole geometry or identity')
        report = folder / 'drc.json'
        verify_fixture_context(path, fixture)
        subprocess.run(['kicad-cli','pcb','drc','--format','json','--severity-all',
                        '--output',str(report),str(fixture)], check=True, stdout=subprocess.DEVNULL)
        verify_fixture_context(path, fixture)
        drc = json.loads(report.read_text())
        found = []
        for violation in drc['violations']:
            if violation['type'] not in ('hole_to_hole', 'holes_co_located'):
                continue
            ids = tuple(sorted(item['uuid'] for item in violation['items']))
            if len(ids) != 2 or not set(ids) <= set(uuid_to_key):
                raise ValueError('unexpected hole violation identity')
            identity = (violation['type'], violation['severity'], ids)
            identities.add(identity); found.append(identity)
            object_identities.add((violation['type'],violation['severity'],tuple(sorted(uuid_to_key[u] for u in ids))))
        if len(found) > len(group)*(len(group)-1):
            raise ValueError('unexpected duplicate pair reporting')
        receipts.append(dict(fixture=str(fixture),holes=sorted(selected),identities=found,
                             report_sha256=hashlib.sha256(report.read_bytes()).hexdigest()))
        print(f'{i+1}/{len(groups)} fixtures; {len(identities)} full identities', flush=True)
    result = dict(status='READ-ONLY NATIVE FIXTURE EVIDENCE; NOT FULL-BOARD ACCEPTANCE',
                  version=version, source_sha256=hashlib.sha256(path.read_bytes()).hexdigest(),
                  project_sha256=hashlib.sha256(project.read_bytes()).hexdigest(),
                  rules_sha256=hashlib.sha256(rules.read_bytes()).hexdigest(),
                  clearance_nm=clearance, holes=holes, covered_pairs=pairs,
                  identities=sorted(identities), object_identities=sorted(object_identities), fixtures=receipts)
    (output/'result.json').write_text(json.dumps(result,indent=2)+'\n')


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('board',type=Path); parser.add_argument('output',type=Path)
    args=parser.parse_args(); audit(args.board,args.output)
