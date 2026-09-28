"""Route exact short two-pad same-package signal loops on a full native draft.

This deterministic step writes only to --output. Callers must run complete
native DRC/parity and ratsnest checks before replacing their source board.
"""
from __future__ import annotations
import argparse,collections,json,math,sys
from pathlib import Path
import pcbnew
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.pcbgen.uuid_tools import stable_uuid
from scripts.pcbgen.netlist import read_netlist

def route(board_id,source,output,receipt,cross_nets=()):
    board=pcbnew.LoadBoard(str(source));before={t.m_Uuid.AsString() for t in board.GetTracks()}
    components,_=read_netlist(ROOT/'schematic/boards'/f'{board_id}.net')
    blocks={c.ref:dict(c.fields).get('Block','') for c in components}
    pads=collections.defaultdict(list)
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetCode()>0:pads[pad.GetNetname()].append((fp.GetReference(),pad))
    added=[]
    if len(set(cross_nets))!=len(cross_nets):raise ValueError('duplicate explicit cross net')
    for net,ends in sorted(pads.items()):
        if net in ('AGND','+12V','-12V','+5V') or len(ends)!=2:continue
        same_package=ends[0][0]==ends[1][0]
        if not same_package and net not in cross_nets:continue
        if not same_package and (not blocks.get(ends[0][0]) or blocks[ends[0][0]]!=blocks.get(ends[1][0])):raise ValueError(f'{net}: cross net leaves one source Block')
        a,b=(p for _,p in ends)
        layers=[layer for layer in (pcbnew.F_Cu,pcbnew.B_Cu) if a.GetLayerSet().Contains(layer) and b.GetLayerSet().Contains(layer)]
        if len(layers)!=1:continue
        pa,pb=a.GetPosition(),b.GetPosition()
        distance=math.hypot(pa.x-pb.x,pa.y-pb.y)
        limit=1.3 if same_package else 5.0
        if distance>pcbnew.FromMM(limit) or distance<pcbnew.FromMM(.1):
            if not same_package:raise ValueError(f'{net}: explicit cross net exceeds {limit} mm')
            continue
        stable=stable_uuid(board_id,'local-link',net)
        if stable in before:continue
        trace=pcbnew.PCB_TRACK(board);trace.SetStart(pa);trace.SetEnd(pb);trace.SetLayer(layers[0]);trace.SetWidth(pcbnew.FromMM(.2));trace.SetNetCode(a.GetNetCode());trace.SetUuid(pcbnew.KIID(stable));board.Add(trace)
        added.append({'net':net,'refs':[r for r,_ in ends],'block':blocks.get(ends[0][0]),'pad_uuids':[a.m_Uuid.AsString(),b.m_Uuid.AsString()],'distance_mm':round(pcbnew.ToMM(distance),4),'layer':board.GetLayerName(layers[0]),'track_uuid':stable})
    if set(cross_nets)-{r['net'] for r in added}- {p.GetNetname() for p in board.GetTracks()}:
        raise ValueError('explicit cross net absent or already routed unexpectedly')
    pcbnew.SaveBoard(str(output),board)
    receipt.write_text(json.dumps({'schema_version':1,'board_id':board_id,'source':str(source),'output':str(output),'tracks_added':added,'preexisting_track_uuids':sorted(before)},indent=2,sort_keys=True)+'\n')
    print(f'{board_id}: disposable full-board copy has {len(added)} new exact local signal links')

def main():
    p=argparse.ArgumentParser();p.add_argument('board_id');p.add_argument('--board',required=True,type=Path);p.add_argument('--output',required=True,type=Path);p.add_argument('--receipt',required=True,type=Path);p.add_argument('--cross-net',action='append',default=[]);a=p.parse_args()
    route(a.board_id,a.board,a.output,a.receipt,a.cross_net)
if __name__=='__main__':main()
