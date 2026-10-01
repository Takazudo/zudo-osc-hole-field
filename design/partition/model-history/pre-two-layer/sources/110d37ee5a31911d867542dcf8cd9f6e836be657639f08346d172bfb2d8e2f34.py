#!/usr/bin/env python3
"""Full native KiCad ratsnest count; CLI DRC JSON truncates large boards."""
from __future__ import annotations
import argparse,collections,hashlib,json
from pathlib import Path
import pcbnew

def inspect(board_path):
    board=pcbnew.LoadBoard(str(board_path))
    connectivity=board.GetConnectivity()
    connectivity.RecalculateRatsnest()
    pads=collections.Counter(pad.GetNetname() for fp in board.GetFootprints() for pad in fp.Pads() if pad.GetNetCode()>0)
    # SWIG does not expose RN_NET/CN_EDGE, but GetConnectedItems performs
    # native SearchClusters(CSM_CONNECTIVITY_CHECK), including zone islands.
    # Seed only real pads/tracks/vias: native ratsnest ignores orphan zone-only
    # islands. Zone parent UUIDs cannot identify a cluster because one pour
    # can contain several disconnected filled islands.
    seeds=[p for fp in board.GetFootprints() for p in fp.Pads()]+list(board.GetTracks())
    seen=set();clusters=collections.Counter()
    for item in seeds:
        if item.GetNetCode()<=0 or item.m_Uuid.AsString() in seen:continue
        members=connectivity.GetConnectedItems(item)
        keys={m.m_Uuid.AsString() for m in members if m.Type()!=pcbnew.PCB_ZONE_T}
        keys.add(item.m_Uuid.AsString());seen.update(keys)
        clusters[item.GetNetname()]+=1
    per_net={name:n-1 for name,n in sorted(clusters.items()) if n>1}
    total=connectivity.GetUnconnectedCount(False)
    if sum(per_net.values())!=total:
        raise ValueError('native cluster-derived per-net counts do not sum to complete native ratsnest; refuse incomplete names')
    token_path=Path(__file__).resolve().parents[2]/'design/reports/board-net-tokens.json';tokens=json.loads(token_path.read_text()) if token_path.exists() else {}
    return {'schema_version':2,'board':str(board_path),'board_sha256':hashlib.sha256(board_path.read_bytes()).hexdigest(),'native_unconnected_edges':total,
            'native_open_net_count':len(per_net),'native_open_edges_by_net':per_net,
            'named_edge_count_sum':sum(per_net.values()),'native_open_edge_source_identities':[{'native_net_name':name,'source_net_name':tokens.get(name,name),'native_open_edges':count} for name,count in per_net.items()],
            'named_edge_basis':'Native GetConnectedItems connectivity clusters including filled-zone islands; each net has clusters minus one edges; sum must equal native GetUnconnectedCount(False). Orphan zone-only islands excluded by native ratsnest policy.',
            'board_net_count':connectivity.GetNetCount(),'multi_pad_candidate_net_count':sum(n>1 for n in pads.values()),
            'multi_pad_candidate_net_names':sorted(name for name,n in pads.items() if n>1),
            'name_scope':'native_open_edges_by_net is complete and sum-checked. multi_pad_candidate_net_names is a separate candidate inventory; CLI DRC JSON can truncate its item list.'}

def main():
    p=argparse.ArgumentParser();p.add_argument('board',type=Path);p.add_argument('output',type=Path);args=p.parse_args()
    result=inspect(args.board)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(f"native ratsnest: {result['native_unconnected_edges']} edges; {result['multi_pad_candidate_net_count']} candidate net names")

if __name__=='__main__':main()
