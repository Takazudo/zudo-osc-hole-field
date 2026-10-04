"""Bounded partition transition for the core locality placement (#43).

The core packages are placed by scripts/checks/jack_locality.py, anchored on the
core GH headers instead of panel hardware (see partition35_floorplan.py).
"""
from __future__ import annotations
import copy


def prove_core_locality_transition(old,new):
    """Whole-partition equality except core package faces and the core layer stack."""
    expected=copy.deepcopy(old)
    current={b['id']:b for b in new['boards']}
    for board in expected['boards']:
        if board.get('board_key')=='K':
            board['layers']=current[board['id']]['layers'];board['layer_reason']=current[board['id']]['layer_reason']
    old_rows={r['ref']:r for r in expected['assignment']['components']}
    for row in new['assignment']['components']:
        before=old_rows.get(row['ref'])
        if before is not None and before['board']=='K':before['side']=row['side']
    if expected!=new:raise ValueError('Partition changed beyond the core locality placement and core layer stack')


def without_core_locality(partition,base):
    """The partition with core package faces and the core layer stack restored from base.

    Later jack-half changes stay, so the jack transition is proved on this
    intermediate and the core transition from it to the current partition.
    """
    result=copy.deepcopy(partition)
    before={b['id']:b for b in base['boards']}
    for board in result['boards']:
        if board.get('board_key')=='K':
            board['layers']=before[board['id']]['layers'];board['layer_reason']=before[board['id']]['layer_reason']
    sides={r['ref']:r['side'] for r in base['assignment']['components'] if r['board']=='K'}
    for row in result['assignment']['components']:
        if row['board']=='K':row['side']=sides[row['ref']]
    return result
