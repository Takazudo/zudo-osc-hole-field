"""Read-only native two-pad local-net inventory for bounded routing trials."""
from __future__ import annotations
import argparse,collections,json,math,sys
from pathlib import Path
import pcbnew
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.pcbgen.netlist import read_netlist

def inspect(board_id):
    board=pcbnew.LoadBoard(str(ROOT/'boards'/board_id/f'{board_id}.kicad_pcb'))
    components,_=read_netlist(ROOT/'schematic/boards'/f'{board_id}.net')
    block={c.ref:dict(c.fields).get('Block','') for c in components}
    pads=collections.defaultdict(list)
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetCode()>0:pads[pad.GetNetname()].append((fp.GetReference(),pad))
    candidates=[];cross_face=[];multi_pad=0
    for net,ends in pads.items():
        if net in ('AGND','+12V','-12V','+5V'):continue
        if len(ends)!=2:
            if len(ends)>2:multi_pad+=1
            continue
        if ends[0][0]==ends[1][0]:continue
        refs=[r for r,_ in ends]
        if not block.get(refs[0]) or block[refs[0]]!=block.get(refs[1]):continue
        layers=[board.GetLayerName(layer) for layer in (pcbnew.F_Cu,pcbnew.B_Cu) if all(p.GetLayerSet().Contains(layer) for _,p in ends)]
        a,b=(p.GetPosition() for _,p in ends)
        distance=pcbnew.ToMM(math.hypot(a.x-b.x,a.y-b.y))
        if len(layers)!=1:
            cross_face.append({'net':net,'refs':refs,'block':block[refs[0]],'pad_distance_mm':round(distance,4)})
            continue
        candidates.append({'net':net,'refs':refs,'block':block[refs[0]],'layer':layers[0],'pad_distance_mm':round(distance,4)})
    candidates.sort(key=lambda row:(row['pad_distance_mm'],row['net']))
    routed={t.GetNetname() for t in board.GetTracks()}
    remaining=[c for c in candidates if c['net'] not in routed]
    return {'board_id':board_id,'candidate_count':len(candidates),'counts_within_mm':{str(limit):sum(c['pad_distance_mm']<=limit for c in candidates) for limit in (2,3,4,5,10,20,30)},'closest':candidates[:30],
            'remaining_same_face_two_pad_source_local_nets':remaining,
            'cross_face_two_pad_source_local_nets':sorted(cross_face,key=lambda r:(r['pad_distance_mm'],r['net'])),
            'signal_multi_pad_net_count':multi_pad,
            'scope':'Complete two-pad signal nets on distinct footprints in one source Block. Remaining excludes nets with any existing copper; cross-face routes require vias. Distance alone does not prove a legal path.'}
def main():
    p=argparse.ArgumentParser();p.add_argument('board_id');p.add_argument('--output',type=Path);a=p.parse_args();report=inspect(a.board_id)
    if a.output:a.output.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(json.dumps(report,sort_keys=True))
if __name__=='__main__':main()
