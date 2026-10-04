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
