#!/usr/bin/env python3
"""Full native KiCad ratsnest count; CLI DRC JSON truncates large boards."""
from __future__ import annotations
import argparse,collections,json
from pathlib import Path
import pcbnew

def inspect(board_path):
    board=pcbnew.LoadBoard(str(board_path))
    connectivity=board.GetConnectivity()
    connectivity.RecalculateRatsnest()
    pads=collections.Counter(pad.GetNetname() for fp in board.GetFootprints() for pad in fp.Pads() if pad.GetNetCode()>0)
    return {'schema_version':1,'board':str(board_path),'native_unconnected_edges':connectivity.GetUnconnectedCount(False),
            'board_net_count':connectivity.GetNetCount(),'multi_pad_candidate_net_count':sum(n>1 for n in pads.values()),
            'multi_pad_candidate_net_names':sorted(name for name,n in pads.items() if n>1),
            'name_scope':'Candidates only: a multi-pad net may already be joined by copper. Native edge count is complete; CLI DRC JSON can truncate its item list.'}

def main():
    p=argparse.ArgumentParser();p.add_argument('board',type=Path);p.add_argument('output',type=Path);args=p.parse_args()
    result=inspect(args.board)
    args.output.parent.mkdir(parents=True,exist_ok=True)
    args.output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(f"native ratsnest: {result['native_unconnected_edges']} edges; {result['multi_pad_candidate_net_count']} candidate net names")

if __name__=='__main__':main()
