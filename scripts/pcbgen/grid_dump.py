#!/usr/bin/env python3
"""Export native board geometry and open pad islands for the grid router.

Run inside the KiCad oracle (scripts/kicad/run.sh). Read-only: the board is
never saved. The JSON feeds grid_router.py and cut_capacity.py on the host.
"""
from __future__ import annotations
import argparse,collections,hashlib,json
from pathlib import Path
import pcbnew

LAYERS={pcbnew.F_Cu:'F.Cu',pcbnew.In1_Cu:'In1.Cu',pcbnew.In2_Cu:'In2.Cu',pcbnew.B_Cu:'B.Cu'}

def outline(shape):
    if shape.OutlineCount()==0:return []
    o=shape.Outline(0);return [[o.CPoint(i).x,o.CPoint(i).y] for i in range(o.PointCount())]

def dump(board_path):
    board=pcbnew.LoadBoard(str(board_path))
    if board.GetCopperLayerCount()!=4:raise ValueError('grid router supports four copper layers')
    pads=[]
    for fp in board.GetFootprints():
        for pad in fp.Pads():
            layers=[name for layer,name in LAYERS.items() if pad.IsOnLayer(layer)]
            poly=outline(pad.GetEffectivePolygon(next(l for l in LAYERS if pad.IsOnLayer(l)),pcbnew.ERROR_INSIDE)) if layers else []
            pads.append({'uuid':pad.m_Uuid.AsString(),'ref':fp.GetReference(),'pad':pad.GetNumber(),'net':pad.GetNetname(),
                         'xy':[pad.GetPosition().x,pad.GetPosition().y],'layers':layers,'poly':poly,
                         'drill':pad.GetDrillSize().x if pad.HasHole() else 0,'npth':pad.GetAttribute()==pcbnew.PAD_ATTRIB_NPTH,
                         'locked':fp.IsLocked()})
    tracks=[];vias=[]
    for t in board.GetTracks():
        if t.Type()==pcbnew.PCB_VIA_T:
            vias.append({'uuid':t.m_Uuid.AsString(),'net':t.GetNetname(),'xy':[t.GetPosition().x,t.GetPosition().y],
                         'diameter':t.GetWidth(pcbnew.F_Cu),'drill':t.GetDrillValue()})
        elif t.Type()==pcbnew.PCB_TRACE_T:
            tracks.append({'uuid':t.m_Uuid.AsString(),'net':t.GetNetname(),'a':[t.GetStart().x,t.GetStart().y],
                           'b':[t.GetEnd().x,t.GetEnd().y],'width':t.GetWidth(),'layer':LAYERS[t.GetLayer()]})
        else:raise ValueError('arc tracks are not supported by the grid router')
    keepouts=[]
    for z in board.Zones():
        if z.GetIsRuleArea():
            keepouts.append({'name':z.GetZoneName(),'layers':[n for l,n in LAYERS.items() if z.IsOnLayer(l)],'poly':outline(z.Outline()),
                             'tracks':z.GetDoNotAllowTracks(),'vias':z.GetDoNotAllowVias()})
    edges=[]
    for s in board.GetDrawings():
        if s.GetLayer()!=pcbnew.Edge_Cuts:continue
        if s.GetShape()!=pcbnew.SHAPE_T_SEGMENT:raise ValueError('only straight Edge.Cuts segments are supported')
        edges.append([s.GetStart().x,s.GetStart().y,s.GetEnd().x,s.GetEnd().y])
    conn=board.GetConnectivity();conn.RecalculateRatsnest()
    seeds=[p for fp in board.GetFootprints() for p in fp.Pads()]+list(board.GetTracks())
    seen=set();groups=collections.defaultdict(list)
    for item in seeds:
        uid=item.m_Uuid.AsString()
        if item.GetNetCode()<=0 or uid in seen:continue
        ids={m.m_Uuid.AsString() for m in conn.GetConnectedItems(item) if m.Type()!=pcbnew.PCB_ZONE_T}|{uid};seen|=ids
        groups[item.GetNetname()].append(sorted(ids))
    islands={net:g for net,g in groups.items() if len(g)>1}
    count=sum(len(g)-1 for g in islands.values())
    if count!=conn.GetUnconnectedCount(False):raise ValueError('island count differs from native ratsnest')
    return {'schema':'grid-router-dump-1','board':str(board_path),'board_sha256':hashlib.sha256(Path(board_path).read_bytes()).hexdigest(),
            'pads':pads,'tracks':tracks,'vias':vias,'keepouts':keepouts,'edges':edges,'open_edges':count,'islands':islands}

def main():
    p=argparse.ArgumentParser();p.add_argument('board',type=Path);p.add_argument('output',type=Path);a=p.parse_args()
    result=dump(a.board);a.output.write_text(json.dumps(result)+'\n')
    print(f"{a.board}: {len(result['pads'])} pads, {len(result['tracks'])} tracks, {len(result['vias'])} vias, {result['open_edges']} native open edges")
if __name__=='__main__':main()
