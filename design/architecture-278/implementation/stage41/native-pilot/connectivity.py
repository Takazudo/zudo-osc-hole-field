"""Native connectivity snapshot preserving distinct duplicate-UUID objects."""
from collections import defaultdict
from pathlib import Path
import argparse
import json
import pcbnew
from identity_guard import digest
from native_guard import check_native, copper_identity


def key(identity):
    return json.dumps(identity, separators=(',', ':'))


def snapshot(path, output):
    raw = path.read_text(); board = pcbnew.LoadBoard(str(path)); check_native(board, raw)
    conn = board.GetConnectivity(); conn.RecalculateRatsnest(); check_native(board, raw)
    seeds = []; pointers = {}; keys = set(); metadata = {}
    for f in board.GetFootprints():
        for p in f.Pads():
            if p.GetNetCode() <= 0: continue
            ident = key(['pad', f.m_Uuid.AsString(), p.m_Uuid.AsString(), f.GetReference(), p.GetNumber()])
            seeds.append(p); pointers[int(p.this)] = ident
            metadata[ident] = {'kind': 'pad', 'ref': f.GetReference(), 'pin': p.GetNumber(), 'net': p.GetNetname()}
    for t in board.GetTracks():
        if t.GetNetCode() <= 0: continue
        contract = copper_identity(board, t); ident = key(contract[:-1])
        seeds.append(t); pointers[int(t.this)] = ident
        metadata[ident] = {'kind': contract[0], 'uuid': contract[1], 'net': contract[-1]}
    if len(pointers) != len(seeds) or len(metadata) != len(seeds):
        raise ValueError('ambiguous native object identity/pointer')
    groups = defaultdict(list); seen = set()
    for item in seeds:
        ident = pointers[int(item.this)]
        if ident in seen: continue
        members = {ident}
        for other in conn.GetConnectedItems(item):
            if other.Type() == pcbnew.PCB_ZONE_T: continue
            ptr = int(other.this)
            if ptr not in pointers: raise ValueError('native connected item missing from complete seed inventory')
            members.add(pointers[ptr])
        if members & seen: raise ValueError('overlapping native connectivity components')
        if any(metadata[k]['net'] != item.GetNetname() for k in members): raise ValueError('native cross-net component')
        seen.update(members); groups[item.GetNetname()].append(sorted(members))
    count = sum(len(v)-1 for v in groups.values())
    if count != conn.GetUnconnectedCount(False): raise ValueError('occurrence-aware components differ from native open-edge count')
    check_native(board, raw)
    result = {'version': pcbnew.GetBuildVersion(), 'board_sha256': digest(raw), 'objects': metadata,
              'groups': {n: sorted(v) for n,v in sorted(groups.items())}, 'native_open_edges': count,
              'identity_mode': 'native pointers within load; stable pad/geometry keys across loads, never UUID-set collapse'}
    output.write_text(json.dumps(result, separators=(',', ':'))+'\n')
    print(json.dumps({'objects':len(seeds),'native_open_edges':count,'snapshot':str(output)}))


if __name__ == '__main__':
    p=argparse.ArgumentParser();p.add_argument('board',type=Path);p.add_argument('output',type=Path)
    a=p.parse_args();snapshot(a.board,a.output)
