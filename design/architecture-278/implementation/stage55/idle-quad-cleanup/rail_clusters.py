"""Stage55: rail connectivity clusters (pad membership) of an already refilled board.

Runs in the pinned oracle: rail_clusters.py REFILLED_PCB OUTPUT_JSON
Per-net edge counts cannot show which opens closed or whether a surviving chain was
cut; pad membership of every cluster can. Seeds are pads and tracks, as in
scripts/pcbgen/ratsnest.py.
"""
import hashlib, json, sys
from pathlib import Path
import pcbnew

RAILS = ('+12V', '-12V', 'AGND', '+5V')
source, output = map(Path, sys.argv[1:3])
assert not output.exists(), 'refuse overwrite'
board = pcbnew.LoadBoard(str(source))
connectivity = board.GetConnectivity()
connectivity.RecalculateRatsnest()
seeds = [p for fp in board.GetFootprints() for p in fp.Pads() if p.GetNetname() in RAILS]
seeds += [t for t in board.GetTracks() if t.GetNetname() in RAILS]
seen = set(); clusters = {r: [] for r in RAILS}
for item in seeds:
    key = item.m_Uuid.AsString()
    if key in seen:
        continue
    members = list(connectivity.GetConnectedItems(item)) + [item]
    seen.update(m.m_Uuid.AsString() for m in members if m.Type() != pcbnew.PCB_ZONE_T)
    pads = sorted({f'{m.GetParentFootprint().GetReference()}.{m.GetNumber()}' for m in members if m.Type() == pcbnew.PCB_PAD_T})
    copper = sum(1 for m in members if m.Type() in (pcbnew.PCB_TRACE_T, pcbnew.PCB_ARC_T, pcbnew.PCB_VIA_T))
    clusters[item.GetNetname()].append({'pads': pads, 'copper_items': copper})
for r in RAILS:
    clusters[r].sort(key=lambda c: (c['pads'], c['copper_items']))
result = {'board_sha256': hashlib.sha256(source.read_bytes()).hexdigest(), 'clusters': clusters,
          'cluster_counts': {r: len(c) for r, c in clusters.items()}}
output.write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
print('rail clusters', result['cluster_counts'])
