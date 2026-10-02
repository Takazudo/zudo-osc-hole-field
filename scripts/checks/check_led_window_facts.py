#!/usr/bin/env python3
"""Check optical-window declarations against fixed parent/LED centres."""
import json
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def number(value):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError('window offset must be numeric')
    result = Decimal(str(value))
    if not result.is_finite():
        raise ValueError('window offset must be finite')
    return result


def check(facts, lock):
    placement = facts['placement']
    if 'offset_from_jack_centre_mm' in placement:
        raise ValueError('single offset cannot describe both LED types')
    groups = placement['groups']
    declared = {row['led_type']: row for row in groups}
    if len(declared) != len(groups) or set(declared) != {'mag', 'clip'}:
        raise ValueError('expected one magnitude and one clip declaration')
    rows = lock['placements']
    by_uid = {row['uid']: row for row in rows}
    if len(rows) != len(by_uid):
        raise ValueError('duplicate fixed hardware UID')
    observed = {kind: [] for kind in declared}
    for led in rows:
        if led['kind'] != 'led' or led.get('field') != 'jacks':
            continue
        kind = led['led_type']
        if kind not in observed:
            raise ValueError('unexpected jack LED type')
        parent = by_uid[led['parent']]
        if parent['kind'] != 'jack':
            raise ValueError('jack LED parent is not a jack')
        offset = tuple(number(led[axis])-number(parent[axis]) for axis in ('x_mm','y_mm'))
        stored = tuple(number(led[axis]) for axis in ('offset_x_mm','offset_y_mm'))
        if offset != stored:
            raise ValueError('lock offset disagrees with actual parent centres')
        observed[kind].append(offset)
    total = 0
    for kind, row in declared.items():
        count = row['count']
        if type(count) is not int or count <= 0 or count != len(observed[kind]):
            raise ValueError('declared LED count disagrees with lock')
        offset = tuple(number(v) for v in row['offset_from_jack_centre_mm'])
        if len(offset) != 2 or any(value != offset for value in observed[kind]):
            raise ValueError('declared LED offset disagrees with parent centres')
        total += count
    if type(facts['count']) is not int or facts['count'] != total:
        raise ValueError('total jack LED count disagrees with groups')
    return {kind: len(rows) for kind, rows in observed.items()}


if __name__ == '__main__':
    counts = check(json.loads((ROOT/'design/mechanical/facts/led-window.json').read_bytes()),
                   json.loads((ROOT/'design/grid/placements.lock.json').read_bytes()))
    print(f'PASS: declared jack LED offsets match fixed parent centres: {counts}; optical qualification OPEN')
