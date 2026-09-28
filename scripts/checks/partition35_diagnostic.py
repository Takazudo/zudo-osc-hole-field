#!/usr/bin/env python3
"""Quantify rejected issue #35 candidates; this never approves a partition.

Input is a fresh native KiCad 10.0.6 export. Courtyard rectangles follow the
existing placer's conservative geometry, not measured component solid volumes.
"""
from __future__ import annotations

import argparse
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.pcbgen.netlist import TOKEN, many, one, parse, read_netlist
from scripts.checks.prepartition54 import canonical_netlist_sha256

REPORT = ROOT / 'design/partition/diagnostic35.json'


def footprint_geometry(path: Path) -> dict:
    tokens = TOKEN.findall(path.read_text())
    root, end = parse(tokens)
    if end != len(tokens) or root[0] not in ('footprint', 'module'):
        raise ValueError(f'invalid footprint: {path}')
    points = []
    for item in root:
        if not isinstance(item, list) or item[0] not in ('fp_line', 'fp_rect'):
            continue
        if one(item, 'layer')[1] != 'F.CrtYd':
            continue
        points += [tuple(map(float, one(item, tag)[1:3])) for tag in ('start', 'end')]
    if not points:
        raise ValueError(f'missing rectangular courtyard: {path}')
    box = [min(p[0] for p in points), min(p[1] for p in points),
           max(p[0] for p in points), max(p[1] for p in points)]
    pads = []
    for pad in many(root, 'pad'):
        if pad[2] != 'thru_hole':
            continue
        x, y = map(float, one(pad, 'size')[1:3])
        if pad[3] == 'circle' and x == y:
            area = math.pi * x * y / 4
        elif pad[3] == 'rect':
            area = x * y
        elif pad[3] == 'oval':
            diameter = min(x, y)
            area = diameter * (max(x, y)-diameter) + math.pi * diameter**2 / 4
        elif pad[3] == 'roundrect':
            radius = float(one(pad, 'roundrect_rratio')[1]) * min(x, y)
            area = x*y - (4-math.pi)*radius**2
        else:
            raise ValueError(f'unsupported through-hole pad shape: {path}')
        pads.append({'pin': pad[1], 'at_mm': list(map(float, one(pad, 'at')[1:3])),
                     'size_mm': [x, y], 'shape': pad[3], 'area_mm2': area})
    return {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
            'courtyard_bbox_mm': box, 'courtyard_bbox_area_mm2': (box[2]-box[0])*(box[3]-box[1]),
            'through_hole_pads': pads}


def island_closure(seed: set[str], islands: dict, sensitive: list[set[str]]) -> set[str]:
    result = set(seed)
    groups = [*islands.values(), *sensitive]
    while True:
        count = len(result)
        for group in groups:
            if result & group:
                result.update(group)
        if len(result) == count:
            return result


def build_report(netlist: Path) -> dict:
    components, pin_nets = read_netlist(netlist)
    all_components, _ = read_netlist(netlist, include_abstract=True)
    by_ref = {c.ref: c for c in components}
    fields = {c.ref: dict(c.fields) for c in components}
    lock = json.loads((ROOT / 'design/grid/placements.lock.json').read_text())
    placements = {p['uid']: p for p in lock['placements']}
    audit = json.loads((ROOT / 'design/reports/master-audit.json').read_text())
    stats = json.loads((ROOT / 'design/reports/netlist-stats.json').read_text())
    if len(all_components) != stats['component_count']:
        raise ValueError('master statistics are stale')
    sensitive = [{m['ref'] for m in net['members'] if not m['ref'].startswith('#FLG')}
                 for net in audit['sensitive_nets']]
    if any(not group <= by_ref.keys() for group in sensitive):
        raise ValueError('master sensitive-net audit is stale')
    for net in audit['sensitive_nets']:
        for member in net['members']:
            if member['ref'].startswith('#FLG'):
                continue
            if pin_nets.get((member['ref'], member['pin'])) != net['net']:
                raise ValueError(f'stale sensitive pin mapping: {net["net"]} {member}')
    geometries = {}
    for c in components:
        if not c.footprint.startswith('zudo-osc-hole-field:'):
            raise ValueError(f'unexpected footprint library: {c.ref}')
        geometries.setdefault(c.footprint, None)
    for footprint in geometries:
        geometries[footprint] = footprint_geometry(
            ROOT / 'footprints/kicad/zudo-osc-hole-field.pretty' / (footprint.split(':')[1]+'.kicad_mod'))
    areas = {c.ref: geometries[c.footprint]['courtyard_bbox_area_mm2'] for c in components}
    islands, nets = defaultdict(set), defaultdict(set)
    for c in components:
        f = fields[c.ref]
        if f['Island']:
            # Reused names such as HOLD_LOCAL and OUT_LOCAL are instance-local.
            islands[(f['Block'], f['Island'])].add(c.ref)
    for (ref, _), net in pin_nets.items():
        nets[net].add(ref)
    jacks = {c.ref for c in components if fields[c.ref]['PanelUid'].startswith('J:')}
    raw_inputs, raw_seed = [], set(jacks)
    for ref in sorted(jacks):
        net = pin_nets[(ref, 'T')]
        refs = nets[net]
        switches = [r for r in refs if fields[r]['Role'].startswith('input_fault_switch:')]
        if not switches:
            continue
        raw_seed.update(refs)
        raw_inputs.append({'panel_uid': fields[ref]['PanelUid'], 'jack_ref': ref, 'net': net,
                           'nodes': [{'ref': r, 'pin': p} for (r, p), n in sorted(pin_nets.items()) if n == net],
                           'protection_refs': sorted(switches),
                           'protection_islands': sorted({fields[r]['Island'] for r in switches})})
    raw_local = island_closure(raw_seed, islands, sensitive)
    original_j = {c.ref for c in components if fields[c.ref]['PanelUid'] and
                  placements[fields[c.ref]['PanelUid']]['domain'] == 'J'}
    original_local = island_closure(raw_seed | original_j, islands, sensitive)
    jack_geometry = geometries['zudo-osc-hole-field:Jack_3.5mm_QingPu_WQP518MA']
    # Verify pad bounding boxes are disjoint across the fixed grid before summing.
    pad_boxes = []
    for ref in sorted(jacks):
        placement = placements[fields[ref]['PanelUid']]
        if placement['rot_deg'] != 0:
            raise ValueError('jack pad area check requires the locked zero rotation')
        for pad in jack_geometry['through_hole_pads']:
            x = placement['x_mm'] + pad['at_mm'][0]
            y = placement['y_mm'] + pad['at_mm'][1]
            w, h = pad['size_mm']
            box = (x-w/2, y-h/2, x+w/2, y+h/2)
            if any(box[0] < p[2] and p[0] < box[2] and box[1] < p[3] and p[1] < box[3]
                   for p in pad_boxes):
                raise ValueError('jack copper exclusions overlap; cannot sum their areas')
            pad_boxes.append(box)
    # Their exact copper shapes are smaller than the placer's rectangular pad
    # exclusions; adding them once on the opposite face is a lower bound.
    jack_back_pad_area = len(jacks)*sum(p['area_mm2'] for p in jack_geometry['through_hole_pads'])
    two_face_area = 2*306*140
    candidates = []
    for name, refs in [('preview_J_with_indicators', original_local),
                       ('J_with_separate_optical_board', raw_local)]:
        area = sum(areas[r] for r in sorted(refs))
        bound = area + jack_back_pad_area
        if bound <= two_face_area:
            raise ValueError(f'{name}: recorded area rejection no longer holds; reassess issue #35 instead of retaining BLOCKED evidence')
        candidates.append({'id': name, 'status': 'REJECTED - conservative placement area lower bound',
                           'outline_xywh_mm': [6, 22, 306, 140],
                           'component_count_forced_local': len(refs),
                           'courtyard_bbox_sum_mm2': round(area, 6),
                           'opposite_face_jack_copper_minimum_mm2': round(jack_back_pad_area, 6),
                           'minimum_two_face_occupied_mm2': round(bound, 6),
                           'available_two_face_area_mm2': two_face_area,
                           'deficit_mm2': round(bound-two_face_area, 6),
                           'forced_control_uids': sorted(fields[r]['PanelUid'] for r in refs
                                                         if fields[r]['PanelUid'].startswith('C:')),
                           'forced_component_refs': sorted(refs)})
    spanning = []
    for (block, island), refs in sorted(islands.items()):
        panel = [placements[fields[r]['PanelUid']] for r in sorted(refs) if fields[r]['PanelUid']]
        domains = sorted({p['domain'] for p in panel})
        if len(domains) > 1:
            spanning.append({'instance': block, 'island': island, 'domains': domains,
                             'component_count': len(refs),
                             'panel_members': [{'uid': p['uid'], 'x_mm': p['x_mm'], 'y_mm': p['y_mm'],
                                                'domain': p['domain']} for p in panel]})
    example = []
    for ref in ('U4147', 'U4148'):
        example.append({'ref': ref, 'mpn': fields[ref]['MPN'], 'island': fields[ref]['Island'],
                        'pins': {p: n for (r, p), n in sorted(pin_nets.items()) if r == ref}})
    return {
        'schema_version': 1, 'issue': 35,
        'status': 'HISTORICAL REJECTION - pre-#60 candidates; superseded by design/partition/partition.json',
        'authority': 'PROPOSAL (planning, owner-delegated)',
        'scope': 'Diagnostic of two bounded J candidates and rear-core transfer; no partition selected and no PCB generated.',
        'source': {'kicad_version': '10.0.6', 'canonical_native_netlist_sha256': canonical_netlist_sha256(netlist),
                   'schematic_sha256': hashlib.sha256((ROOT/'schematic/zudo-osc-hole-field.kicad_sch').read_bytes()).hexdigest(),
                   'placement_lock_sha256': hashlib.sha256((ROOT/'design/grid/placements.lock.json').read_bytes()).hexdigest()},
        'counts': {'native_components': len(all_components), 'physical_components': len(components),
                   'excluded_abstract_refs': sorted({c.ref for c in all_components}-{c.ref for c in components}),
                   'modules': stats['module_instance_count'], 'panel_uids': len(placements),
                   'input_jack_nets': len(raw_inputs), 'sensitive_nets': len(sensitive)},
        'area_method': 'Sum each physical footprint F.CrtYd bounding rectangle once, independent of board side. Compare against both complete J faces. Add only disjoint jack copper pad area on the opposite face as a conservative through-hole exclusion. No allowance for other tails, clearances, supports, connectors, routing, missing protection or bulk capacitors. This is an existing-placer geometry bound, not measured solid fit.',
        'all_components_courtyard_bbox_sum_mm2': round(sum(areas.values()), 6),
        'nonpanel_components_courtyard_bbox_sum_mm2': round(sum(areas[c.ref] for c in components if not fields[c.ref]['PanelUid']), 6),
        'footprints': geometries, 'candidates': candidates,
        'raw_input_nets_that_cannot_be_transferred_to_K': raw_inputs,
        'spanning_panel_islands': spanning, 'envelope_package_example': example,
        'preserved_open_obligations': {'output_paths': 82, 'precision_sense_paths': 16, 'octave_receivers': 30,
                                      'exact_protection': 'OPEN #59', 'source_installed_fit': 'NOT RUN #57',
                                      'selector_installed_fit': 'NOT RUN #55'},
        'limitations': ['This rejects the stated candidates, not every possible topology or a larger J outline.',
                        'No exact connector or board plane has been selected; unsourced installed hardware datums remain open.',
                        'CN301/XB301 remain abstract and imply neither footprints nor conducting rail continuity.',
                        'No board-assignment, connector, panel, support or physical-fit PASS is claimed.'],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('netlist', type=Path, nargs='?')
    parser.add_argument('--mark-historical', action='store_true', help='Annotate the retained pre-60 snapshot without recomputing its historical numbers')
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if args.mark_historical:
        report=json.loads(REPORT.read_text())
        report['status']='HISTORICAL REJECTION - pre-#60 candidates; superseded by design/partition/partition.json'
        report['superseded_by']='design/partition/partition.json; #60 source cut and #35 conditional physical proposal'
        REPORT.write_text(json.dumps(report,indent=2,ensure_ascii=False)+'\n')
        print('Annotated historical snapshot only; no current partition gate evaluated')
        return
    if args.netlist is None:parser.error('historical native netlist is required')
    retained=json.loads(REPORT.read_text())
    if canonical_netlist_sha256(args.netlist)!=retained['source']['canonical_native_netlist_sha256']:
        raise SystemExit('Historical snapshot requires its pre-60 netlist/checkout. Current gate: bash scripts/partition/regen.sh --check. This is not a current BLOCKED verdict.')
    report = build_report(args.netlist)
    report['superseded_by']='design/partition/partition.json; #60 source cut and #35 conditional physical proposal'
    output = json.dumps(report, indent=2, ensure_ascii=False)+'\n'
    if args.check:
        if not REPORT.exists() or REPORT.read_text() != output:
            raise SystemExit('FAIL: partition diagnostic drift; reproduce in the pinned historical checkout')
        print('PASS: historical diagnostic reproducibility only; current partition is tracked separately')
    else:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        REPORT.write_text(output)
        print('WROTE: historical diagnostic only; no current partition verdict')


if __name__ == '__main__':
    main()
