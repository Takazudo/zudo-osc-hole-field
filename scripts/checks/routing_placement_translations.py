"""Apply reviewed local resistor translations without repacking other parts.

This is source geometry only. Native copper, parity, connectivity, warning and
retention gates remain mandatory for every resulting routed board.
"""
import copy
import math
import re

from scripts.pcbgen.placement_geometry import Box, inside_outline


def apply_translations(placements, source, adjustments):
    if set(adjustments) != {'schema_version', 'translations'} or adjustments['schema_version'] != 1:
        raise ValueError('unsupported routing placement translation schema')
    rows = copy.deepcopy(placements)
    byref = {row['ref']: row for row in rows}
    if len(byref) != len(rows):
        raise ValueError('duplicate source placement reference')
    seen = set()
    for change in adjustments['translations']:
        if set(change) != {'ref', 'expected_source', 'delta_mm', 'evidence'}:
            raise ValueError('unsupported routing placement translation fields')
        ref = change['ref']
        if ref in seen or ref not in byref:
            raise ValueError('duplicate or missing translation reference')
        seen.add(ref)
        row = byref[ref]
        if row != change['expected_source']:
            raise ValueError('stale routing placement translation source')
        if (row['fixed'] or 'bypass_cluster' in row or row['board'] not in ('JL', 'JR')
                or not re.fullmatch(r'RB?\d+', ref) or row['side'] not in ('F.Cu', 'B.Cu')):
            raise ValueError('translation is outside movable jack resistor scope')
        delta = change['delta_mm']
        if (not isinstance(delta, list) or len(delta) != 2
                or any(isinstance(v, bool) or not isinstance(v, (int, float))
                       or not math.isfinite(v) or abs(v) > 2
                       or abs(v * 10 - round(v * 10)) > 1e-8 for v in delta)
                or not any(delta)):
            raise ValueError('translation must use bounded 0.1mm increments')
        if not isinstance(change['evidence'], str) or not change['evidence'].strip():
            raise ValueError('translation evidence reference required')
        dx, dy = delta
        row['x_mm'] += dx
        row['y_mm'] += dy
        row['courtyard_mm'] = [v + shift for v, shift in zip(row['courtyard_mm'], (dx, dy, dx, dy))]
    # Check the final joint placement, not a sequence that could hide collisions.
    for ref in seen:
        row = byref[ref]
        courtyard = Box(*row['courtyard_mm'])
        if not inside_outline(courtyard, source['boards'][row['board']]['outline'], .30):
            raise ValueError('translated courtyard violates source board edge')
        for other in rows:
            if other['ref'] == ref or (other['board'], other['side']) != (row['board'], row['side']):
                continue
            a, b, c, d = other['courtyard_mm']
            distance = math.hypot(max(a-courtyard.x1, courtyard.x0-c, 0),
                                  max(b-courtyard.y1, courtyard.y0-d, 0))
            if distance < .35 - 1e-8:
                raise ValueError('translated courtyard violates source separation: ' + other['ref'])
    return rows
