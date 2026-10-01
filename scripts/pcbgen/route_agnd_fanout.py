"""Conservative disposable AGND SMD-to-filled-plane fanout experiment.

No board is promoted by this script. Full native DRC, per-board identity and
ratsnest reduction must be verified by the caller before promotion.
"""
from __future__ import annotations
import argparse,json,math,sys
from pathlib import Path
import pcbnew
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.pcbgen.uuid_tools import stable_uuid

OFFSETS=((1,0),(-1,0),(0,1),(0,-1),(0.70710678,0.70710678),(0.70710678,-0.70710678),(-0.70710678,0.70710678),(-0.70710678,-0.70710678))

def distance_to_box(point,box):
    dx=max(box.GetLeft()-point.x,0,point.x-box.GetRight())
    dy=max(box.GetTop()-point.y,0,point.y-box.GetBottom())
    return math.hypot(dx,dy)

def hole_clear(point,holes):
    # KiCad project min_hole_to_hole is 0.25 mm. Keep 0.05 mm margin.
    return all(math.hypot(point.x-pos.x,point.y-pos.y)-radius-pcbnew.FromMM(.15)>=pcbnew.FromMM(.30) for pos,radius in holes)

def route(board_id,source,output,receipt,limit,probe=False,net='AGND'):
    board=pcbnew.LoadBoard(str(source))
    if net not in ('AGND','+12V','-12V','+5V'):raise ValueError('unsupported plane net')
    plane_layer=pcbnew.In1_Cu if net=='AGND' else pcbnew.In2_Cu
    slug='agnd' if net=='AGND' else {'+12V':'plus12v','-12V':'minus12v','+5V':'plus5v'}[net]
    planes=[z for z in board.Zones() if z.GetNetname()==net and z.IsOnLayer(plane_layer) and not z.GetIsRuleArea()]
    if len(planes)!=1 or not planes[0].HasFilledPolysForLayer(plane_layer):raise ValueError(f'one filled {net} plane required')
    plane=planes[0]
    keepouts=[z.GetBoundingBox() for z in board.Zones() if z.GetIsRuleArea()]
    all_pads=[p for fp in board.GetFootprints() for p in fp.Pads()]
    holes=[(p.GetPosition(),max(p.GetDrillSize().x,p.GetDrillSize().y)/2) for p in all_pads if p.HasDrilledHole()]
    holes += [(via.GetPosition(),via.GetDrillValue()/2) for via in board.GetTracks() if isinstance(via,pcbnew.PCB_VIA)]
    candidates=[]
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            if pad.GetNetname()!=net or pad.GetAttribute()!=pcbnew.PAD_ATTRIB_SMD:continue
            face=[layer for layer in (pcbnew.F_Cu,pcbnew.B_Cu) if pad.GetLayerSet().Contains(layer)]
            if len(face)!=1:continue
            key=fp.GetReference()+':'+pad.GetNumber()+':'+pad.m_Uuid.AsString()
            if any(t.m_Uuid.AsString()==stable_uuid(board_id,slug+'-fanout-via',key) for t in board.GetTracks()):continue
            pos=pad.GetPosition();choices=[]
            for ux,uy in OFFSETS:
                at=pcbnew.VECTOR2I(pos.x+round(ux*pcbnew.FromMM(.95)),pos.y+round(uy*pcbnew.FromMM(.95)))
                if not plane.HitTestFilledArea(plane_layer,at,0):continue
                if any(distance_to_box(at,box)<pcbnew.FromMM(.65) for box in keepouts):continue
                if not hole_clear(at,holes):continue
                gap=min(distance_to_box(at,p.GetBoundingBox()) for p in all_pads if p is not pad)
                if gap<pcbnew.FromMM(.65):continue
                choices.append((gap,at))
            if choices:candidates.append((max(choices,key=lambda x:x[0])[0],fp.GetReference(),pad.GetNumber(),key,pad,face[0],sorted(choices,key=lambda x:-x[0])))
    candidates.sort(key=lambda row:(-row[0],row[1],row[2],row[3]))
    if probe:
        print(json.dumps({'board_id':board_id,'net':net,'eligible_proposals':len(candidates),'scope':'Own filled plane, 0.95 mm offset, pad/keepout and drilled-hole screening only; route conflicts still need DRC'}))
        return
    added=[]
    for _,ref,number,key,pad,face_layer,choices in candidates:
        legal=next(((gap,at) for gap,at in choices if hole_clear(at,holes)),None)
        if legal is None:continue
        gap,at=legal
        via=pcbnew.PCB_VIA(board);via.SetViaType(pcbnew.VIATYPE_THROUGH);via.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);via.SetPosition(at);via.SetWidth(pcbnew.FromMM(.7));via.SetDrill(pcbnew.FromMM(.3));via.SetNetCode(pad.GetNetCode());via.SetUuid(pcbnew.KIID(stable_uuid(board_id,slug+'-fanout-via',key)));board.Add(via)
        track=pcbnew.PCB_TRACK(board);track.SetStart(pad.GetPosition());track.SetEnd(at);track.SetLayer(face_layer);track.SetWidth(pcbnew.FromMM(.5 if net=='AGND' else .4));track.SetNetCode(pad.GetNetCode());track.SetUuid(pcbnew.KIID(stable_uuid(board_id,slug+'-fanout-track',key)));board.Add(track)
        added.append({'ref':ref,'pad':number,'pad_uuid':pad.m_Uuid.AsString(),'layer':board.GetLayerName(face_layer),'plane_layer':board.GetLayerName(plane_layer),'via_x_mm':round(pcbnew.ToMM(at.x),4),'via_y_mm':round(pcbnew.ToMM(at.y),4),'nearest_other_pad_gap_mm':round(pcbnew.ToMM(gap),4),'track_uuid':track.m_Uuid.AsString(),'via_uuid':via.m_Uuid.AsString(),'net':net})
        holes.append((at,pcbnew.FromMM(.15)))
        if len(added)>=limit:break
    if not added:raise ValueError(f'no {net} fanout candidate met filled-plane/clearance proposal')
    pcbnew.SaveBoard(str(output),board)
    receipt.write_text(json.dumps({'schema_version':1,'board_id':board_id,'source':str(source),'output':str(output),'net':net,'candidate_pool':len(candidates),'added':added,'status':'DISPOSABLE DRAFT; native DRC/ratsnest/preservation pending'},indent=2,sort_keys=True)+'\n')
    print(f'{board_id}: disposable {net} fanout added {len(added)} vias+tracks from {len(candidates)} eligible proposals')

def main():
    p=argparse.ArgumentParser();p.add_argument('board_id');p.add_argument('--board',required=True,type=Path);p.add_argument('--output',required=True,type=Path);p.add_argument('--receipt',required=True,type=Path);p.add_argument('--limit',type=int,default=10);p.add_argument('--probe-only',action='store_true');p.add_argument('--net',choices=('AGND','+12V','-12V','+5V'),default='AGND');a=p.parse_args()
    if not 1<=a.limit<=100:raise ValueError('limit must be 1..100')
    route(a.board_id,a.board,a.output,a.receipt,a.limit,a.probe_only,a.net)
if __name__=='__main__':main()
