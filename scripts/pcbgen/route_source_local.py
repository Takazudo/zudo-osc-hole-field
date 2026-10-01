"""Obstacle-aware straight/elbow signal routing on a disposable full board.

Exact pads, source Block identity and native effective copper shapes drive
the proposal. Native full-board gates remain mandatory before promotion.
"""
from __future__ import annotations
import argparse,collections,json,math,sys
from pathlib import Path
import pcbnew
sys.path.insert(0,str(Path(__file__).resolve().parents[2]))
from scripts.pcbgen.netlist import read_netlist
from scripts.pcbgen.uuid_tools import stable_uuid
from scripts.pcbgen.verify_local_links import blocks as board_blocks
ROOT=Path(__file__).resolve().parents[2]

def route(board_id,source,output,receipt,limit,probe=False,bypass=False):
    board=pcbnew.LoadBoard(str(source));conn=board.GetConnectivity();conn.RecalculateRatsnest()
    components,_=read_netlist(ROOT/'schematic/boards'/f'{board_id}.net')
    blocks={c.ref:dict(c.fields).get('Block','') for c in components}
    pads=[(fp.GetReference(),p) for fp in board.GetFootprints() for p in fp.Pads()]
    grouped=collections.defaultdict(list)
    for ref,pad in pads:
        if pad.GetNetCode()>0 and pad.GetNetname() not in ('AGND','+12V','-12V','+5V') and blocks.get(ref):
            grouped[(pad.GetNetname(),blocks[ref])].append((ref,pad))
    pairs=[]
    for (net,block),ends in grouped.items():
        for i,(ra,a) in enumerate(ends):
            joined={p.m_Uuid.AsString() for p in conn.GetConnectedItems(a) if p.Type()!=pcbnew.PCB_ZONE_T}
            for rb,b in ends[i+1:]:
                if b.m_Uuid.AsString() in joined:continue
                pa,pb=a.GetPosition(),b.GetPosition();distance=math.hypot(pa.x-pb.x,pa.y-pb.y)
                if not pcbnew.FromMM(.1)<=distance<=pcbnew.FromMM(10):continue
                for layer in (pcbnew.F_Cu,pcbnew.B_Cu):
                    if a.GetLayerSet().Contains(layer) and b.GetLayerSet().Contains(layer):
                        pairs.append((distance,net,block,ra,a,rb,b,layer))
    if bypass:
        pairs=[];fps={fp.GetReference():fp for fp in board.GetFootprints()}
        packages=json.loads((ROOT/'design/reports/io-partition.json').read_text())['physical_packages']
        for package in packages:
            ref,ic=package['ref'],package['decouples_ref']
            if not ic or ref not in fps:continue
            if ic not in fps or fps[ref].GetLayer()!=fps[ic].GetLayer():raise ValueError('bypass source face/package mismatch')
            for pad in fps[ref].Pads():
                net=pad.GetNetname()
                if net not in ('+12V','-12V','+5V'):continue
                pa=pad.GetPosition();pins=[p for p in fps[ic].Pads() if p.GetNetname()==net]
                if not pins:raise ValueError('bypass has no exact IC supply pin')
                pin=min(pins,key=lambda p:math.hypot(pa.x-p.GetPosition().x,pa.y-p.GetPosition().y));pb=pin.GetPosition();distance=math.hypot(pa.x-pb.x,pa.y-pb.y)
                if distance>pcbnew.FromMM(3):raise ValueError('source bypass exceeds unchanged3mm pad locality')
                if pin.m_Uuid.AsString() in {m.m_Uuid.AsString() for m in conn.GetConnectedItems(pad)}:continue
                layer=fps[ref].GetLayer();pairs.append((distance,net,blocks[ref],ref,pad,ic,pin,layer))
    pairs.sort(key=lambda x:(x[0],x[1],x[3],x[5],x[7]))
    keepouts=[z for z in board.Zones() if z.GetIsRuleArea() and z.GetDoNotAllowTracks()]
    width=.4 if bypass else .2
    clearance=pcbnew.FromMM(.25+width/2)
    tracks=list(board.GetTracks());added=[];rejected=0
    parents={}
    def find(k):
        parents.setdefault(k,k)
        if parents[k]!=k:parents[k]=find(parents[k])
        return parents[k]
    for distance,net,block,ra,a,rb,b,layer in pairs:
        ka,kb=a.m_Uuid.AsString(),b.m_Uuid.AsString()
        if find(ka)==find(kb):continue
        pa,pb=a.GetPosition(),b.GetPosition()
        paths=([pa,pb],[pa,pcbnew.VECTOR2I(pa.x,pb.y),pb],[pa,pcbnew.VECTOR2I(pb.x,pa.y),pb])
        obstacles=[p.GetEffectiveShape(layer) for _,p in pads if p.GetLayerSet().Contains(layer) and p.GetNetname()!=net]
        obstacles += [t.GetEffectiveShape(layer) for t in tracks if t.IsOnLayer(layer) and t.GetNetname()!=net]
        chosen=None
        for path in paths:
            path=[p for i,p in enumerate(path) if i==0 or p!=path[i-1]]
            segments=[pcbnew.SEG(x,y) for x,y in zip(path,path[1:])]
            if any(shape.Collide(seg,clearance) for shape in obstacles for seg in segments):continue
            # Source keepouts are rectangles; the inflated box test is
            # deliberately conservative and never cuts across a reservation.
            if any(z.IsOnLayer(layer) and box_hit(z.GetBoundingBox(),x,y,clearance) for z in keepouts for x,y in zip(path,path[1:])):continue
            chosen=path;break
        if chosen is None:rejected+=1;continue
        parents[find(kb)]=find(ka)
        for p in conn.GetConnectedItems(a):
            if p.Type()!=pcbnew.PCB_ZONE_T:parents[find(p.m_Uuid.AsString())]=find(ka)
        for p in conn.GetConnectedItems(b):
            if p.Type()!=pcbnew.PCB_ZONE_T:parents[find(p.m_Uuid.AsString())]=find(ka)
        row={'net':net,'block':block,'refs':[ra,rb],'pad_uuids':[ka,kb],
             'direct_distance_mm':round(pcbnew.ToMM(distance),4),'layer':board.GetLayerName(layer),'tracks':[]}
        for index,(start,end) in enumerate(zip(chosen,chosen[1:])):
            uid=stable_uuid(board_id,'source-local',net+':'+ka+':'+kb+':'+str(index))
            track=pcbnew.PCB_TRACK(board);track.SetStart(start);track.SetEnd(end);track.SetLayer(layer);track.SetWidth(pcbnew.FromMM(width));track.SetNetCode(a.GetNetCode());track.SetUuid(pcbnew.KIID(uid))
            board.Add(track);tracks.append(track)
            row['tracks'].append({'uuid':uid,'start_mm':[pcbnew.ToMM(start.x),pcbnew.ToMM(start.y)],'end_mm':[pcbnew.ToMM(end.x),pcbnew.ToMM(end.y)]})
        added.append(row)
        if len(added)>=limit:break
    report={'board_id':board_id,'candidate_pad_pairs':len(pairs),'obstacle_rejected_pairs':rejected,'added':added,'status':'PROPOSAL ONLY' if probe else 'DISPOSABLE DRAFT; native gates pending','scope':'Same source Block, exact same-face pad pairs <=10 mm; 0.20 mm trace, conservative 0.25 mm copper clearance; straight/elbow paths; no new vias or changed footprints'}
    if bypass:report['scope']='Exact source DecouplesRef IC/bypass supply pads on same face <=3mm;0.4mm Rails traces/0.25mm clearance; no new vias or changed footprints'
    if not probe:
        pcbnew.SaveBoard(str(output),board)
        # Native serialization is used only for genuinely new track blocks.
        # Reconstruct from the complete input bytes so owner state and every
        # existing copper block remain unchanged before the separate refill.
        original=board_blocks(source);serialized=board_blocks(output)
        expected={t['uuid'] for row in added for t in row['tracks']}
        new={k:v for k,v in serialized['segment'].items() if k not in original['segment']}
        if set(new)!=expected:raise ValueError('native proposal serialized unexpected copper')
        text=source.read_text();end=text.rfind(')')
        output.write_text(text[:end]+''.join('\t'+new[k]+'\n' for k in sorted(new))+text[end:])
        restored=board_blocks(output)
        if restored['non_copper']!=original['non_copper']:raise ValueError('signal proposal changed owner state')
        for kind in ('segment','via','arc'):
            if any(restored[kind].get(k)!=v for k,v in original[kind].items()):raise ValueError('signal proposal changed prior copper')
        report['all_input_non_copper_and_prior_copper_blocks_preserved']=True
    receipt.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(f'{board_id}: {len(pairs)} close source-local pad pairs; {len(added)} legal geometric proposals; {rejected} obstacle rejections')

def box_hit(box,a,b,margin):
    # Segment versus inflated rectangle, including diagonal straight paths.
    lo,hi=0.,1.;dx,dy=b.x-a.x,b.y-a.y
    for p,q in ((-dx,a.x-box.GetLeft()+margin),(dx,box.GetRight()+margin-a.x),(-dy,a.y-box.GetTop()+margin),(dy,box.GetBottom()+margin-a.y)):
        if p==0:
            if q<0:return False
        else:
            r=q/p
            if p<0:lo=max(lo,r)
            else:hi=min(hi,r)
            if lo>hi:return False
    return True

def main():
    p=argparse.ArgumentParser();p.add_argument('board_id');p.add_argument('--board',type=Path,required=True);p.add_argument('--output',type=Path,required=True);p.add_argument('--receipt',type=Path,required=True);p.add_argument('--limit',type=int,default=50);p.add_argument('--probe',action='store_true');p.add_argument('--bypass',action='store_true');a=p.parse_args()
    if not 1<=a.limit<=1000 or a.output.resolve()==a.board.resolve():raise ValueError('require bounded limit and disposable output')
    route(a.board_id,a.board,a.output,a.receipt,a.limit,a.probe,a.bypass)
if __name__=='__main__':main()
