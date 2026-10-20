"""Stage55: remove the Stage54 idle quads and owned bypasses from a disposable osc-core PCB copy.

Runs inside the pinned KiCad 10.0.6 oracle (`bash scripts/kicad/run.sh python3 ...`).
Usage: pcb_cleanup.py SOURCE_PCB OUTPUT_PCB RECEIPT_JSON SCHEMATIC_RECEIPT_JSON

Deletion rules, all explicit and reported item by item:
1. the 36 removed footprints;
2. every track, arc and via on the 48 removed private nets (must have no zone);
3. iteratively, on shared rail nets, a track/via with an end that touched a removed pad
   or deleted copper and now meets no remaining track, via or pad there. Copper that
   still joins other copper at a removed pad location is kept, so no chain is cut.
Zones are never edited; refill happens in the DRC step. Nothing else moves.
"""
import json, sys, hashlib
import pcbnew

SRC, DST, RECEIPT, SCH = sys.argv[1:5]
schematic = json.load(open(SCH))
REMOVED = set(schematic['removed_refs'])
PRIVATE = set(schematic['removed_board_net_tokens'])
assert len(REMOVED) == 36 and len(PRIVATE) == 48

board = pcbnew.LoadBoard(SRC)
mm = pcbnew.ToMM


def pt(v): return [round(mm(v.x), 6), round(mm(v.y), 6)]


def describe(item):
    row = {'uuid': item.m_Uuid.AsString(), 'net': item.GetNetname()}
    if item.Type() == pcbnew.PCB_VIA_T:
        row.update(kind='via', at=pt(item.GetPosition()), width_mm=round(mm(item.GetWidth(pcbnew.F_Cu)), 4),
                   drill_mm=round(mm(item.GetDrillValue()), 4))
    else:
        row.update(kind='arc' if item.Type() == pcbnew.PCB_ARC_T else 'track', layer=item.GetLayerName(),
                   start=pt(item.GetStart()), end=pt(item.GetEnd()), width_mm=round(mm(item.GetWidth()), 4))
    return row


def ends(item):
    if item.Type() == pcbnew.PCB_VIA_T:
        return [item.GetPosition()]
    return [item.GetStart(), item.GetEnd()]


def on_layer(item, layer):
    return item.IsOnLayer(layer)


def item_layers(item):
    return [l for l in item.GetLayerSet().Seq() if pcbnew.IsCopperLayer(l)]


footprints = [fp for fp in board.Footprints() if fp.GetReference() in REMOVED]
assert sorted(fp.GetReference() for fp in footprints) == sorted(REMOVED), 'footprint roster'
zones_private = [z.GetNetname() for z in board.Zones() if z.GetNetname() in PRIVATE]
assert not zones_private, 'private net has a zone'
removed_pads = []
for fp in footprints:
    for pad in fp.Pads():
        removed_pads.append(pad)
pad_nets = {p.GetNetname() for p in removed_pads}
assert PRIVATE <= pad_nets
shared = sorted(pad_nets - PRIVATE)

tracks = list(board.GetTracks())
deleted = {}
reason = {}


def mark(item, why):
    key = item.m_Uuid.AsString()
    if key not in deleted:
        deleted[key] = item; reason[key] = why


for t in tracks:
    if t.GetNetname() in PRIVATE:
        mark(t, 'private-net')

surviving_pads = [p for fp in board.Footprints() if fp.GetReference() not in REMOVED for p in fp.Pads()]


CELL = 1000000  # 1 mm spatial hash for candidate lookup only; exact tests use HitTest


def cells(item):
    box = item.GetBoundingBox()
    for x in range(box.GetX()//CELL, box.GetRight()//CELL+1):
        for y in range(box.GetY()//CELL, box.GetBottom()//CELL+1):
            yield (x, y)


grid = {}
for t in tracks:
    if t.GetNetname() in shared:
        for c in cells(t):
            grid.setdefault(c, []).append(t)
for pad in surviving_pads:
    if pad.GetNetname() in shared:
        for c in cells(pad):
            grid.setdefault(c, []).append(pad)


def near(point):
    return grid.get((point.x//CELL, point.y//CELL), [])


def connected_at(point, item, net):
    """Remaining copper of the same net that meets `item` at `point` on a shared layer."""
    layers = item_layers(item)
    for other in near(point):
        if other is item or other.GetNetname() != net:
            continue
        if isinstance(other, pcbnew.PAD):
            if any(other.IsOnLayer(l) for l in layers) and other.HitTest(point):
                return True
            continue
        if other.m_Uuid.AsString() in deleted or not any(on_layer(other, l) for l in layers):
            continue
        if other.Type() == pcbnew.PCB_VIA_T:
            if other.HitTest(point):
                return True
        elif other.HitTest(point, 1000):
            return True
    return False


def touched_deleted(point, item, net):
    layers = item_layers(item)
    for d in near(point):
        if isinstance(d, pcbnew.PAD) or d is item or d.m_Uuid.AsString() not in deleted:
            continue
        if not any(on_layer(d, l) for l in layers):
            continue
        if d.Type() == pcbnew.PCB_VIA_T:
            if d.HitTest(point):
                return True
        elif d.HitTest(point, 1000):
            return True
    for pad in removed_pads:
        if pad.GetNetname() == net and any(pad.IsOnLayer(l) for l in layers) and pad.HitTest(point):
            return True
    return False


changed = True
rounds = 0
while changed:
    changed = False; rounds += 1
    for t in tracks:
        key = t.m_Uuid.AsString(); net = t.GetNetname()
        if key in deleted or net not in shared:
            continue
        for p in ends(t):
            if touched_deleted(p, t, net) and not connected_at(p, t, net):
                mark(t, f'free-end-round{rounds}'); changed = True
                break
    assert rounds < 50

rows = []
for key, item in deleted.items():
    r = describe(item); r['reason'] = reason[key]; rows.append(r)
rows.sort(key=lambda r: (r['reason'], r['net'], r['uuid']))
fp_rows = sorted(({'ref': fp.GetReference(), 'value': fp.GetValue(), 'fpid': fp.GetFPIDAsString(),
                   'at': pt(fp.GetPosition()), 'side': fp.GetLayerName(),
                   'pads': sorted([p.GetNumber(), p.GetNetname()] for p in fp.Pads())} for fp in footprints),
                 key=lambda r: r['ref'])
for item in deleted.values():
    board.Remove(item)
for fp in footprints:
    board.Remove(fp)
board.Save(DST)
counts = {}
for r in rows:
    k = r['reason'].split(':')[0].split('-round')[0]
    counts[k] = counts.get(k, 0) + 1
receipt = {
    'status': 'DISPOSABLE PCB copy; zones unchanged and unfilled until DRC refill',
    'kicad_build': pcbnew.GetBuildVersion(),
    'source_sha256': hashlib.sha256(open(SRC, 'rb').read()).hexdigest(),
    'output_sha256': hashlib.sha256(open(DST, 'rb').read()).hexdigest(),
    'removed_footprints': fp_rows,
    'shared_nets_touched': shared,
    'deleted_copper_counts': counts,
    'deleted_copper': rows,
    'orphan_rounds': rounds,
}
json.dump(receipt, open(RECEIPT, 'w'), indent=2, sort_keys=True); open(RECEIPT, 'a').write('\n')
print('PASS removed', len(fp_rows), 'footprints and', len(rows), 'copper items', counts)
