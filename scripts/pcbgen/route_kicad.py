#!/usr/bin/env python3
"""KiCad 10 portion of the draft DSN/SES routing pipeline."""
from __future__ import annotations
import argparse,json,sys
from pathlib import Path
import pcbnew
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.geometry.panel_frame import to_kicad
from scripts.pcbgen.definition import load_definition
from scripts.pcbgen.uuid_tools import stable_uuid,normalize_file

def vec(x,y):return pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y))
def uid(item):return item.m_Uuid.AsString()

def apply_classes(board,routing):
    settings=board.GetDesignSettings();net_settings=settings.m_NetSettings
    settings.m_TrackMinWidth=pcbnew.FromMM(routing['min_track_width_mm'])
    for spec in routing['net_classes']:
        name=spec['name']
        cls=net_settings.GetDefaultNetclass() if name=='Default' else pcbnew.NETCLASS(name)
        cls.SetTrackWidth(pcbnew.FromMM(spec['track_width_mm']))
        cls.SetClearance(pcbnew.FromMM(spec['clearance_mm']))
        cls.SetViaDiameter(pcbnew.FromMM(spec['via_diameter_mm']))
        cls.SetViaDrill(pcbnew.FromMM(spec['via_drill_mm']))
        if name!='Default':net_settings.SetNetclass(name,cls)
        for net in spec['nets']:
            if name!='Default':net_settings.SetNetclassPatternAssignment(net,name)
    net_settings.ClearAllCaches()

def ensure_zones(board,board_id,definition):
    new_ids={};managed=set();existing={z.GetZoneName():z for z in board.Zones()}
    for spec in definition.routing['zones']:
        net=board.FindNet(spec['net'])
        if net is None:raise ValueError(f"zone {spec['name']}: net {spec['net']!r} absent")
        for layer_name in spec['layers']:
            name=f"pcbgen:{board_id}:pour:{spec['name']}:{layer_name}"
            stable=stable_uuid(board_id,'pour',f"{spec['name']}:{layer_name}")
            zone=existing.get(name)
            if zone is not None:
                if uid(zone)!=stable:raise ValueError(f'{name}: unowned zone name conflict')
                zone.RemoveAllContours()
            else:
                zone=pcbnew.ZONE(board);zone.SetZoneName(name)
                board.Add(zone);new_ids[uid(zone)]=stable
            zone.SetLayer(board.GetLayerID(layer_name));zone.SetNet(net)
            poly=zone.Outline();idx=poly.NewOutline()
            for x,y in definition.outline:
                px,py=to_kicad(x,y);poly.Append(vec(px,py),idx)
            zone.SetLocalClearance(pcbnew.FromMM(spec['clearance_mm']))
            zone.SetMinThickness(pcbnew.FromMM(spec['min_thickness_mm']))
            zone.SetIslandRemovalMode(pcbnew.ISLAND_REMOVAL_MODE_ALWAYS)
            zone.SetPadConnection(pcbnew.ZONE_CONNECTION_FULL if spec.get('pad_connection')=='full' else pcbnew.ZONE_CONNECTION_THERMAL)
            managed.add(stable)
    return new_ids,managed

def track_signature(item):
    a=item.GetStart();b=item.GetEnd()
    width=item.GetWidth(pcbnew.F_Cu) if isinstance(item,pcbnew.PCB_VIA) else item.GetWidth()
    return (uid(item),item.GetClass(),a.x,a.y,b.x,b.y,width,item.GetLayer(),item.GetNetname())

def stats(board):
    tracks=list(board.GetTracks())
    vias=[x for x in tracks if isinstance(x,pcbnew.PCB_VIA)]
    lines=[x for x in tracks if isinstance(x,pcbnew.PCB_TRACK) and not isinstance(x,pcbnew.PCB_VIA)]
    return {'track_count':len(lines),'via_count':len(vias),'via_nets':sorted({x.GetNetname() for x in vias}),'total_track_length_mm':round(sum(pcbnew.ToMM(x.GetLength()) for x in lines),4),'track_uuids':sorted(uid(x) for x in tracks)}

def prepare(board_id,board_path,dsn):
    definition=load_definition(ROOT/'design/boards'/f'{board_id}.json')
    if not definition.routing:raise ValueError(f'{board_id}: routing definition missing')
    board=pcbnew.LoadBoard(str(board_path));board.SetFileName(str(board_path))
    apply_classes(board,definition.routing)
    new_ids,managed=ensure_zones(board,board_id,definition)
    for item in board.GetTracks():item.SetLocked(True)
    if not pcbnew.ZONE_FILLER(board).Fill(board.Zones()):raise RuntimeError('zone refill failed')
    pcbnew.SaveBoard(str(board_path),board)
    normalize_file(board_path,board_id,set(),new_ids,False,managed)
    if not pcbnew.ExportSpecctraDSN(board,str(dsn)):raise RuntimeError('DSN export failed')
    print(f'{board_id}: draft zones/classes applied; {len(list(board.GetTracks()))} existing tracks fixed; DSN exported')

def finish(board_path,ses,stats_path):
    board=pcbnew.LoadBoard(str(board_path));board.SetFileName(str(board_path))
    before={uid(x):track_signature(x) for x in board.GetTracks()}
    zones={uid(z) for z in board.Zones()}
    footprints={fp.GetReference():(uid(fp),fp.GetPosition().x,fp.GetPosition().y,fp.GetLayer(),fp.GetOrientationDegrees(),fp.IsLocked()) for fp in board.GetFootprints()}
    if not pcbnew.ImportSpecctraSES(board,str(ses)):raise RuntimeError('SES import failed')
    after={uid(x):track_signature(x) for x in board.GetTracks()}
    changed=[key for key,value in before.items() if after.get(key)!=value]
    if changed:raise RuntimeError(f'SES changed/removed {len(changed)} existing fixed tracks/vias: {changed[:5]}')
    if zones!={uid(z) for z in board.Zones()}:raise RuntimeError('SES changed/removed an existing zone')
    after_footprints={fp.GetReference():(uid(fp),fp.GetPosition().x,fp.GetPosition().y,fp.GetLayer(),fp.GetOrientationDegrees(),fp.IsLocked()) for fp in board.GetFootprints()}
    if footprints!=after_footprints:raise RuntimeError('SES changed a pre-existing footprint or fixed hardware position')
    if not pcbnew.ZONE_FILLER(board).Fill(board.Zones()):raise RuntimeError('post-route zone refill failed')
    pcbnew.SaveBoard(str(board_path),board)
    result=stats(board)
    result['preexisting_tracks_preserved']=len(before)
    result['preexisting_zones_preserved']=len(zones)
    Path(stats_path).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(f'SES imported; {result["track_count"]} tracks, {result["via_count"]} vias, {result["total_track_length_mm"]} mm; existing geometry preserved')

def inspect(board_path,stats_path):
    board=pcbnew.LoadBoard(str(board_path));result=stats(board)
    result['zone_count']=len(list(board.Zones()))
    Path(stats_path).write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')

def main():
    p=argparse.ArgumentParser();p.add_argument('stage',choices=('prepare','finish','inspect'));p.add_argument('board_id');p.add_argument('--board',required=True);p.add_argument('--dsn');p.add_argument('--ses');p.add_argument('--stats')
    a=p.parse_args();board=Path(a.board)
    if a.stage=='prepare':prepare(a.board_id,board,Path(a.dsn))
    elif a.stage=='finish':finish(board,Path(a.ses),Path(a.stats))
    else:inspect(board,Path(a.stats))
if __name__=='__main__':main()
