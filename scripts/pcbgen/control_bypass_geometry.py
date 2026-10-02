"""Exact P-board IC/bypass pad-distance audit using native KiCad geometry."""
import math


def audit(board, io, *, require_connected=False):
    import pcbnew
    footprints = {f.GetReference(): f for f in board.GetFootprints()}
    connectivity = board.GetConnectivity()
    connectivity.RecalculateRatsnest()
    rows = []
    for package in io['physical_packages']:
        ref, parent = package['ref'], package['decouples_ref']
        if not parent or ref not in footprints:
            continue
        if parent not in footprints:
            raise ValueError('P bypass parent is absent: '+ref)
        capacitor, ic = footprints[ref], footprints[parent]
        if capacitor.GetLayer() != ic.GetLayer():
            raise ValueError('P bypass and IC must share a face: '+ref)
        supply_pads = [p for p in capacitor.Pads() if p.GetNetname() in ('+12V', '-12V', '+5V')]
        if len(supply_pads) != 1:
            raise ValueError('P bypass requires exactly one named supply pad: '+ref)
        pad = supply_pads[0]
        matching = [p for p in ic.Pads() if p.GetNetname() == pad.GetNetname()]
        if not matching:
            raise ValueError('P bypass IC supply pin is absent: '+ref)
        position = pad.GetPosition()
        pin = min(matching, key=lambda p: math.hypot(position.x-p.GetPosition().x, position.y-p.GetPosition().y))
        other = pin.GetPosition()
        distance = pcbnew.ToMM(math.hypot(position.x-other.x, position.y-other.y))
        if distance > 3:
            raise ValueError(f'P bypass exceeds 3 mm native pad distance: {ref} -> {parent}: {distance:.6f} mm')
        connected = pin.m_Uuid.AsString() in {m.m_Uuid.AsString() for m in connectivity.GetConnectedItems(pad)}
        if require_connected and not connected:
            raise ValueError('P bypass rail pair is disconnected: '+ref)
        rows.append({'capacitor': ref, 'capacitor_pad': pad.GetNumber(), 'IC': parent,
                     'IC_pad': pin.GetNumber(), 'rail': pad.GetNetname(), 'pad_distance_mm': distance, 'rail_connected': connected})
    if len(rows) != 16:
        raise ValueError('Complete sixteen-pair P bypass inventory required')
    return {'pair_count': len(rows), 'rail_pairs_connected': sum(r['rail_connected'] for r in rows), 'maximum_pad_distance_mm': max(r['pad_distance_mm'] for r in rows),
            'pairs': rows, 'scope': 'Native pad geometry and reported rail connectivity only; electrical/physical loop qualification not established'}


def reject_displaced_capacitor(board, io):
    """A native off-target capacitor must not retain a successful geometry result."""
    import pcbnew
    capacitor = next(f for f in board.GetFootprints() if f.GetReference() == 'C130')
    position = capacitor.GetPosition()
    original = pcbnew.VECTOR2I(position.x, position.y)
    capacitor.SetPosition(pcbnew.VECTOR2I(position.x+pcbnew.FromMM(20), position.y))
    try:
        try:
            audit(board, io)
        except ValueError as error:
            if 'exceeds 3 mm native pad distance: C130' not in str(error):
                raise
        else:
            raise ValueError('Native displaced-bypass negative control was accepted')
    finally:
        capacitor.SetPosition(original)
