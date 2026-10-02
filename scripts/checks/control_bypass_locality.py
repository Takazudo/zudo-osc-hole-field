"""Keep complete P IC/bypass groups local without moving panel hardware.

This is a source courtyard and supply-pad screen, not electrical qualification.
"""
import math
from collections import Counter
from scripts.pcbgen.placement_geometry import Box, inside_outline


def apply_bypass_locality(placements, io, source, connectors, lock, shapes, proposal, optical, slew):
    from scripts.checks.partition35_floorplan import Grid, oriented_box, pads, footprint_pads, turn
    from scripts.checks.connector_packing35 import board_for, rect_collision
    parts = {p['ref']: p for p in io['physical_packages']}
    prior = {p['ref']: p for p in placements}
    if type(proposal.get('schema_version')) is not int or proposal['schema_version'] != 1:
        raise ValueError('Unsupported control bypass locality schema')
    preserved = {ref for group in slew['groups'].values() for ref in group['placements']}
    expected = {}
    all_caps = [p for p in parts.values() if p['decouples_ref'] and board_for(p) == 'P']
    for cap in all_caps:
        if cap['ref'] not in preserved:
            expected.setdefault(cap['decouples_ref'], set()).add(cap['ref'])
    groups = proposal['groups']
    if set(groups) != set(expected):
        raise ValueError('Every remaining P IC/bypass group is required')
    all_refs = set()
    for parent, group in groups.items():
        refs = {parent, *expected[parent]}
        if set(group['placements']) != refs or all_refs & refs or preserved & refs:
            raise ValueError('Exact complete independent IC/bypass closure required')
        for ref in refs:
            if parts[ref]['panel_uid'] or parts[ref]['dnp'] or board_for(parts[ref]) != 'P' or prior[ref]['fixed']:
                raise ValueError('Cannot move fixed, DNP or non-P hardware')
            if prior[ref]['side'] != 'B.Cu':
                raise ValueError('Bypass repair must preserve the existing B face')
        all_refs |= refs
    grid = Grid('P', 'B.Cu', source['boards']['P']['outline'])
    for part in parts.values():
        if board_for(part) == 'P' and part['panel_uid']:
            for _, box in pads(part, lock):
                grid.fill(box)
    for header in connectors['headers']:
        if header['board'] == 'P' and header['side'] == 'B.Cu':
            grid.fill(header['land_courtyard_mm'])
    for x, y in source['boards']['P']['supports_mm']:
        grid.fill([x-1.6, y-1.6, x+1.6, y+1.6])
    for x in optical['support']['x_mm']:
        for y in optical['support']['y_mm']:
            if y >= 176:
                grid.fill([x-1.6, y-1.6, x+1.6, y+1.6])
    for reserve in source['boards']['P'].get('reserves', []):
        if 'B.Cu' in reserve['sides']:
            grid.fill(reserve['rect'])
    for row in placements:
        if row['board'] == 'P' and not row['fixed'] and row['ref'] not in all_refs:
            grid.fill(row['courtyard_mm'])
    new = {}
    for parent, group in groups.items():
        for ref, pose in group['placements'].items():
            if set(pose) != {'x_mm', 'y_mm', 'rotation_deg'} or any(
                    type(v) not in (int, float) or not math.isfinite(v) for v in pose.values()):
                raise ValueError('Finite complete source pose required')
            x, y, angle = pose['x_mm'], pose['y_mm'], pose['rotation_deg']
            if angle not in (0, 90, 180, 270):
                raise ValueError('Orthogonal source rotation required')
            b = oriented_box(shapes[parts[ref]['footprint']], 'B.Cu', angle)
            box = [b[0]+x, b[1]+y, b[2]+x, b[3]+y]
            if not inside_outline(Box(*box), source['boards']['P']['outline'], .30):
                raise ValueError('Bypass courtyard outside P: '+ref)
            x0, x1 = math.floor(box[0]*grid.scale), math.ceil(box[2]*grid.scale)
            y0, y1 = math.floor(box[1]*grid.scale), math.ceil(box[3]*grid.scale)
            mask = ((1 << (x1-x0))-1) << x0
            if any(row & mask for row in grid.rows[y0:y1]):
                raise ValueError('Bypass courtyard collides with retained geometry: '+ref)
            if any(rect_collision(box, row['courtyard_mm'], .35) for row in new.values()):
                raise ValueError('New bypass courtyards collide: '+ref)
            new[ref] = {**prior[ref], **pose, 'side': 'B.Cu', 'courtyard_mm': box,
                        'bypass_cluster': parent}
    result = [new.get(row['ref'], row) for row in placements]
    if Counter(p['ref'] for p in result) != Counter(p['ref'] for p in placements):
        raise ValueError('Bypass locality changed package roster')
    final = {row['ref']: row for row in result}
    pin_nets = {ref: {} for ref in parts}
    for unit in io['package_units']:
        pin_nets[unit['ref']].update(unit['pins'])
    def points(ref, net):
        row = final[ref]
        values = []
        for pin, value in pin_nets[ref].items():
            if value != net:
                continue
            x, y = footprint_pads(parts[ref]['footprint'])[pin]
            x, y = turn((-x if row['side']=='B.Cu' else x, y), row['rotation_deg'])
            values.append((x+row['x_mm'], y+row['y_mm']))
        return values
    distances = []
    for cap in sorted(all_caps, key=lambda p: p['ref']):
        ref, parent = cap['ref'], cap['decouples_ref']
        rail = next(n for n in pin_nets[ref].values() if n in ('+12V', '-12V', '+5V'))
        distance = min(math.dist(a, b) for a in points(ref, rail) for b in points(parent, rail))
        if final[ref]['side'] != final[parent]['side'] or distance > 3:
            raise ValueError('P bypass exceeds same-face 3 mm supply-pad screen: '+ref)
        distances.append({'capacitor': ref, 'IC': parent, 'rail': rail,
                          'supply_pad_centre_distance_mm': distance})
    return result, {'status': 'Source geometry only; native routing and physical qualification required',
                    'moved_references': sorted(all_refs), 'preserved_slew_references': sorted(preserved),
                    'supply_pad_limit_mm': 3, 'pairs': distances,
                    'maximum_supply_pad_distance_mm': max(row['supply_pad_centre_distance_mm'] for row in distances)}
