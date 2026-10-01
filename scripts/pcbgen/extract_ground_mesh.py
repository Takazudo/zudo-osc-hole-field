"""Read-only native filled AGND mesh for task-local resistance extraction."""
from __future__ import annotations
import argparse,collections,hashlib,json,math,re
from pathlib import Path
import pcbnew

def extract(source,output,pitch,raw=False):
    board=pcbnew.LoadBoard(str(source));conn=board.GetConnectivity();conn.RecalculateRatsnest()
    plane=next(z for z in board.Zones() if z.GetNetname()=='AGND' and z.IsOnLayer(pcbnew.In1_Cu) and not z.GetIsRuleArea())
    box=board.GetBoardEdgesBoundingBox();x0=pcbnew.ToMM(box.GetLeft());y0=pcbnew.ToMM(box.GetTop());nx=math.floor(pcbnew.ToMM(box.GetWidth())/pitch);ny=math.floor(pcbnew.ToMM(box.GetHeight())/pitch)
    mask=[]
    for iy in range(0 if raw else ny):
        for ix in range(nx):
            # Nine samples per cell exclude pierced or edge-straddling cells.
            mask.append(int(all(plane.HitTestFilledArea(pcbnew.In1_Cu,pcbnew.VECTOR2I(pcbnew.FromMM(x0+(ix+dx)*pitch),pcbnew.FromMM(y0+(iy+dy)*pitch)),0) for dx in (.05,.5,.95) for dy in (.05,.5,.95))))
    ports=[];lands=[]
    for f in board.GetFootprints():
        land=str(f.GetFPID().GetLibItemName())=='LoadWireTerminal_4x4mm'
        header=bool(re.fullmatch(r'J9\d{5}',f.GetReference()))
        if not land and not header:continue
        for pad in f.Pads():
            if pad.GetNetname()!='AGND':continue
            at=pad.GetPosition();members=conn.GetConnectedItems(pad)
            row={'ref':f.GetReference(),'pad':pad.GetNumber(),'x_mm':pcbnew.ToMM(at.x),'y_mm':pcbnew.ToMM(at.y),'plane_connected':any(m.Type()==pcbnew.PCB_ZONE_T and m.GetNetname()=='AGND' for m in members),'native_connected_items':len(members),'pad_width_mm':pcbnew.ToMM(pad.GetSize().x),'pad_height_mm':pcbnew.ToMM(pad.GetSize().y),'pad_copper_layers':[board.GetLayerName(layer) for layer in (pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.B_Cu) if pad.GetLayerSet().Contains(layer)]}
            (lands if land else ports).append(row)
    report={'board':str(source),'board_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'kicad_version':pcbnew.GetBuildVersion(),'pitch_mm':pitch,'x0_mm':x0,'y0_mm':y0,'nx':nx,'ny':ny,'mask':mask,'ports':ports,'lands':lands,'scope':'In1 filled-copper nine-sample cell mesh. Numerical plane-only estimate; absent native terminal/contact transfers remain open circuits. No original board bytes changed.'}
    if raw:
        def points(chain):return [[pcbnew.ToMM(chain.CPoint(i).x),pcbnew.ToMM(chain.CPoint(i).y)] for i in range(chain.PointCount())]
        report['filled_contours']={}
        report['fractured_contours']={};report['native_unfracture_audit']=[]
        report['native_membership_samples']={}
        for layer in (pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.B_Cu):
            polygons=[];original=[];native_polys=[]
            for zone in board.Zones():
                if zone.GetNetname()!='AGND' or zone.GetIsRuleArea() or not zone.IsOnLayer(layer):continue
                raw_poly=zone.GetFilledPolysList(layer)
                for index in range(raw_poly.OutlineCount()):original.append({'shell':points(raw_poly.COutline(index)),'holes':[points(raw_poly.CHole(index,h)) for h in range(raw_poly.HoleCount(index))]})
                polys=raw_poly.CloneDropTriangulation();before=polys.Area()/1e12;polys.Unfracture();after=polys.Area()/1e12
                perimeter=sum(math.dist(ring[i],ring[(i+1)%len(ring)]) for item in original for ring in [item['shell'],*item['holes']] for i in range(len(ring)))
                tolerance=perimeter*2e-6+1e-6
                if abs(before-after)>tolerance:raise ValueError('native Unfracture area change exceeds2nm boundary envelope')
                native_polys.append(polys);report['native_unfracture_audit'].append({'zone':zone.GetZoneName(),'layer':board.GetLayerName(layer),'area_before_mm2':before,'area_after_mm2':after,'area_delta_mm2':after-before,'area_envelope_mm2':tolerance,'original_outline_count':raw_poly.OutlineCount(),'unfractured_outline_count':polys.OutlineCount(),'unfractured_hole_count':sum(polys.HoleCount(i) for i in range(polys.OutlineCount()))})
                for index in range(polys.OutlineCount()):polygons.append({'shell':points(polys.COutline(index)),'holes':[points(polys.CHole(index,h)) for h in range(polys.HoleCount(index))]})
            report['filled_contours'][board.GetLayerName(layer)]=polygons
            report['fractured_contours'][board.GetLayerName(layer)]=original
            coords={(x0+(i+.5)*pcbnew.ToMM(box.GetWidth())/17,y0+(j+.5)*pcbnew.ToMM(box.GetHeight())/17) for i in range(17) for j in range(17)}
            repeated=collections.Counter(tuple(p) for poly in original for ring in [poly['shell'],*poly['holes']] for p in ring)
            for (x,y),count in repeated.items():
                if count<2:continue
                for delta in (.00001,.01,.25):
                    coords.update((x+dx,y+dy) for dx,dy in ((delta,0),(-delta,0),(0,delta),(0,-delta)))
            layer_zones=[z for z in board.Zones() if z.GetNetname()=='AGND' and not z.GetIsRuleArea() and z.IsOnLayer(layer)]
            report['native_membership_samples'][board.GetLayerName(layer)]=[{'x_mm':x,'y_mm':y,'inside':any(p.Contains(pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y))) for p in native_polys),'original_fractured_inside':any(z.HitTestFilledArea(layer,pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y)),0) for z in layer_zones)} for x,y in sorted(coords)]
        bridges=[]
        for fp in board.GetFootprints():
            for pad in fp.Pads():
                if pad.GetNetname()!='AGND' or pad.GetAttribute()!=pcbnew.PAD_ATTRIB_PTH:continue
                diameter=min(pad.GetDrillSize().x,pad.GetDrillSize().y)
                if diameter<=0:raise ValueError('plated AGND pad has no finite drill')
                at=pad.GetPosition();size=pad.GetSize();drill=pad.GetDrillSize();annulus=pcbnew.ToMM(min(size.x-drill.x,size.y-drill.y))/2
                if annulus<=0:raise ValueError('plated pad lacks finite annular copper')
                bridges.append({'uuid':pad.m_Uuid.AsString(),'ref':fp.GetReference(),'x_mm':pcbnew.ToMM(at.x),'y_mm':pcbnew.ToMM(at.y),'drill_mm':pcbnew.ToMM(diameter),'annular_width_mm':annulus,'full_through_span':all(pad.IsOnLayer(l) for l in (pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.B_Cu)),'type':'plated pad; minimum-circle perimeter conservative for oblong holes'})
        for via in board.GetTracks():
            if not isinstance(via,pcbnew.PCB_VIA) or via.GetNetname()!='AGND':continue
            at=via.GetPosition();bridges.append({'uuid':via.m_Uuid.AsString(),'x_mm':pcbnew.ToMM(at.x),'y_mm':pcbnew.ToMM(at.y),'drill_mm':pcbnew.ToMM(via.GetDrillValue()),'annular_width_mm':pcbnew.ToMM(via.GetWidth(pcbnew.F_Cu)-via.GetDrillValue())/2,'full_through_span':via.GetViaType()==pcbnew.VIATYPE_THROUGH and via.TopLayer()==pcbnew.F_Cu and via.BottomLayer()==pcbnew.B_Cu,'native_layer_span':[board.GetLayerName(via.TopLayer()),board.GetLayerName(via.BottomLayer())],'type':'native AGND via'})
        report['plated_bridges']=bridges
        report['board_thickness_mm']=pcbnew.ToMM(board.GetDesignSettings().GetBoardThickness())
        drilled=[]
        for fp in board.GetFootprints():
            for pad in fp.Pads():
                if not pad.HasDrilledHole():continue
                at=pad.GetPosition();size=pad.GetDrillSize();drilled.append({'x_mm':pcbnew.ToMM(at.x),'y_mm':pcbnew.ToMM(at.y),'size_mm':[pcbnew.ToMM(size.x),pcbnew.ToMM(size.y)],'angle_deg':pad.GetOrientationDegrees()})
        for via in board.GetTracks():
            if not isinstance(via,pcbnew.PCB_VIA):continue
            at=via.GetPosition();d=pcbnew.ToMM(via.GetDrillValue());drilled.append({'x_mm':pcbnew.ToMM(at.x),'y_mm':pcbnew.ToMM(at.y),'size_mm':[d,d],'angle_deg':0})
        report['drilled_holes']=drilled
        report['actual_AGND_pad_track_polygons']={}
        conductors=[p for fp in board.GetFootprints() for p in fp.Pads() if p.GetNetname()=='AGND']+[t for t in board.GetTracks() if t.GetNetname()=='AGND']
        for layer in (pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.B_Cu):
            polygons=[]
            for item in conductors:
                if not item.IsOnLayer(layer):continue
                poly=pcbnew.SHAPE_POLY_SET();item.TransformShapeToPolygon(poly,layer,0,pcbnew.FromMM(.001),pcbnew.ERROR_INSIDE)
                for index in range(poly.OutlineCount()):polygons.append({'shell':points(poly.COutline(index)),'holes':[points(poly.CHole(index,h)) for h in range(poly.HoleCount(index))]})
            report['actual_AGND_pad_track_polygons'][board.GetLayerName(layer)]=polygons
        report['pad_track_polygon_error_mm']=.001
        port_records={(p['ref'],p['pad']):p for p in ports}
        for fp in board.GetFootprints():
            for pad in fp.Pads():
                key=(fp.GetReference(),pad.GetNumber())
                if key not in port_records:continue
                poly=pcbnew.SHAPE_POLY_SET();pad.TransformShapeToPolygon(poly,pcbnew.B_Cu,0,pcbnew.FromMM(.001),pcbnew.ERROR_INSIDE)
                port_records[key]['native_B_pad_polygons']=[{'shell':points(poly.COutline(i)),'holes':[points(poly.CHole(i,h)) for h in range(poly.HoleCount(i))]} for i in range(poly.OutlineCount())]
        report['GH_private_courtyards']={}
        for fp in board.GetFootprints():
            if not re.fullmatch(r'J9\d{5}',fp.GetReference()):continue
            box=fp.GetCourtyard(pcbnew.B_CrtYd).BBox()
            report['GH_private_courtyards'][fp.GetReference()]=[pcbnew.ToMM(box.GetLeft()),pcbnew.ToMM(box.GetTop()),pcbnew.ToMM(box.GetRight()),pcbnew.ToMM(box.GetBottom())]
        report['scope']='Exact native filled contour shells/holes for three AGND layers; downstream uses exact whole-cell inclusion and actual plated AGND bridge geometry. Native connectivity remains a separate gate.'
    output.write_text(json.dumps(report,separators=(',',':'))+'\n');print(f'{source}: {sum(mask)} filled ground mesh cells; {sum(p["plane_connected"] for p in ports)}/{len(ports)} contacts native-plane connected')

def main():
    p=argparse.ArgumentParser();p.add_argument('board',type=Path);p.add_argument('output',type=Path);p.add_argument('--pitch-mm',type=float,default=1.0);p.add_argument('--raw-multilayer',action='store_true');a=p.parse_args()
    if not .25<=a.pitch_mm<=2:raise ValueError('mesh pitch outside bounded extraction range')
    extract(a.board,a.output,a.pitch_mm,a.raw_multilayer)
if __name__=='__main__':main()
