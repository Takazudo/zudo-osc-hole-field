#!/usr/bin/env python3
"""Update a KiCad PCB in place from a netlist and the fixed placement lock.

Run only through scripts/kicad/run.sh with pcbnew 10.0.6. Draft output only.
"""
from __future__ import annotations
import argparse
import sys
from pathlib import Path
import pcbnew

sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.geometry.panel_frame import to_kicad
from scripts.pcbgen.definition import load_definition,load_lock,selected_hardware
from scripts.pcbgen.netlist import read_netlist
from scripts.pcbgen.uuid_tools import stable_uuid,normalize_file
from scripts.pcbgen.geometry import outline_segments,staging_position

LIB='zudo-osc-hole-field'

def vec(x,y):return pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y))
def item_uuid(item):return item.m_Uuid.AsString()
def fp_dir(library):
    if library==LIB:return ROOT/'footprints/kicad'/f'{LIB}.pretty'
    path=Path('/usr/share/kicad/footprints')/f'{library}.pretty'
    if not path.is_dir():raise FileNotFoundError(f'footprint library not found: {library}')
    return path

def sync(board_id:str,output:Path|None=None,netlist:Path|None=None):
    definition=load_definition(ROOT/'design/boards'/f'{board_id}.json')
    lock=load_lock(ROOT/'design/grid/placements.lock.json')
    hardware=selected_hardware(definition,lock)
    by_ref={p['ref']:p for p in hardware}
    if len(by_ref)!=len(hardware):raise ValueError('lockfile selections share a reference')
    netpath=netlist or ROOT/definition.netlist
    components,pin_nets=read_netlist(netpath)
    refs={c.ref for c in components}
    hole_refs={f"MH_{h['id']}" for h in definition.mounting_holes}
    if refs & hole_refs:raise ValueError('mounting-hole reference collides with netlist')
    desired_refs=refs | hole_refs
    path=output or ROOT/'boards'/board_id/f'{board_id}.kicad_pcb'
    path.parent.mkdir(parents=True,exist_ok=True)
    created=not path.exists()
    board=pcbnew.BOARD() if created else pcbnew.LoadBoard(str(path))
    board.SetFileName(str(path))
    settings=board.GetDesignSettings()
    settings.SetBoardThickness(pcbnew.FromMM(definition.thickness_mm))
    settings.SetCopperLayerCount(definition.layers)
    settings.SetAuxOrigin(vec(*to_kicad(0,0)))
    settings.SetGridOrigin(vec(*to_kicad(0,0)))
    # Only UUID-labelled generator items can be removed. All others are hands-off.
    old_managed={}
    by_current_ref={}
    for fp in list(board.GetFootprints()):
        ref=fp.GetReference()
        if ref in by_current_ref:raise ValueError(f'duplicate board reference {ref}')
        by_current_ref[ref]=fp
        if item_uuid(fp)==stable_uuid(board_id,'footprint:'+ref,'root'):
            if ref in desired_refs:old_managed[ref]=fp
            else:board.Remove(fp)
    for ref in desired_refs:
        if ref in by_current_ref and ref not in old_managed:
            raise ValueError(f'cannot take over unowned footprint {ref}')
    nets={}
    for name in sorted(set(pin_nets.values())):
        current=board.FindNet(name)
        if current is None:
            current=pcbnew.NETINFO_ITEM(board,name);board.Add(current)
        nets[name]=current
    cache={};new_ids={};owned_refs=set()
    for index,c in enumerate(sorted(components,key=lambda x:x.ref)):
        fields=dict(c.fields)
        if ':' not in c.footprint:raise ValueError(f'{c.ref}: footprint lacks library nickname')
        library,name=c.footprint.split(':',1)
        fp=old_managed.get(c.ref)
        if fp is None:
            if c.ref in by_current_ref:raise ValueError(f'cannot replace unowned footprint {c.ref}')
            if c.footprint not in cache:
                src=pcbnew.FootprintLoad(str(fp_dir(library)),name)
                if src is None:raise FileNotFoundError(c.footprint)
                cache[c.footprint]=src
            fp=pcbnew.FOOTPRINT(cache[c.footprint]);fp.SetParent(board)
            fp.SetFPID(pcbnew.LIB_ID(library,name))
            fp.SetReference(c.ref)
            if c.ref in by_ref:
                placement=by_ref[c.ref]
                fp.SetPosition(vec(*to_kicad(placement['x_mm'],placement['y_mm'])))
                fp.SetOrientationDegrees(placement['rot_deg'])
                fp.SetLocked(True)
            else:
                origin=fields.get('FootprintOriginMm','')
                if origin:
                    x,y=(float(v) for v in origin.split(','))
                    fp.SetPosition(vec(*to_kicad(x,y)))
                else:
                    # Temporary staging remains bounded for unproposed boards.
                    fp.SetPosition(vec(*to_kicad(*staging_position(index))))
            board.Add(fp)
        # KiCad 10 returns wxString wrappers; compare their text, not wrapper identity.
        elif str(fp.GetFPID().GetLibItemName())!=name or str(fp.GetFPID().GetLibNickname())!=library:
            prior_position=fp.GetPosition();prior_orientation=fp.GetOrientationDegrees()
            board.Remove(fp)
            src=cache.get(c.footprint)
            if src is None:
                src=pcbnew.FootprintLoad(str(fp_dir(library)),name)
                if src is None:raise FileNotFoundError(c.footprint)
                cache[c.footprint]=src
            fp=pcbnew.FOOTPRINT(src);fp.SetParent(board);fp.SetFPID(pcbnew.LIB_ID(library,name));fp.SetReference(c.ref)
            fp.SetPosition(prior_position);fp.SetOrientationDegrees(prior_orientation);board.Add(fp)
        fp.SetValue(c.value)
        fp.SetPath(pcbnew.KIID_PATH(c.sheet_ts+c.symbol_ts))
        fp.SetSheetname(c.sheetname)
        fp.SetSheetfile(c.fields and dict(c.fields).get('Sheetfile',Path(definition.schematic).name) or Path(definition.schematic).name)
        for field_name,field_value in c.fields:
            if field_name not in {'Reference','Value','Footprint','Datasheet','Sheetname','Sheetfile'} and not field_name.startswith('ki_'):
                fp.SetField(field_name,field_value)
                fp.GetField(field_name).SetVisible(False)
        if board_id=='osc-jack':
            for unit_field in ('Role','LogicalCellKey','Island'):
                if unit_field not in fields and fp.HasField(unit_field):
                    fp.SetField(unit_field,'')
        if c.ref in by_ref:
            p=by_ref[c.ref]
            fp.SetPosition(vec(*to_kicad(p['x_mm'],p['y_mm'])))
            fp.SetOrientationDegrees(p['rot_deg'])
            fp.SetLocked(True)
        requested_side=dict(c.fields).get('BoardSide','')
        if requested_side not in {'','F.Cu','B.Cu'}:raise ValueError(f'{c.ref}: invalid BoardSide')
        if c.ref in by_ref and requested_side=='B.Cu':raise ValueError(f'{c.ref}: panel hardware must face F.Cu')
        if requested_side:
            target_layer=pcbnew.F_Cu if requested_side=='F.Cu' else pcbnew.B_Cu
            if fp.GetLayer()!=target_layer:fp.Flip(fp.GetPosition(),False)
        orientation=fields.get('KiCadOrientationDeg','')
        if orientation:fp.SetOrientationDegrees(float(orientation))
        if fields.get('FootprintOriginMm') and not fields.get('BoardRegion'):
            fp.SetLocked(True)
        if fields.get('Role')=='factory load-side solder terminal':
            fp.SetAttributes(fp.GetAttributes()|pcbnew.FP_EXCLUDE_FROM_BOM)
        for pad in fp.Pads():
            net_name=pin_nets.get((c.ref,pad.GetNumber()))
            if net_name is None:pad.SetNetCode(0)
            else:pad.SetNet(nets[net_name])
        owned_refs.add(c.ref)
    # Drawing-defined NPTH mounting holes are generator-owned footprints.
    for hole in definition.mounting_holes:
        ref=f"MH_{hole['id']}";fp=old_managed.get(ref)
        if fp is None:
            fp=pcbnew.FOOTPRINT(board);fp.SetReference(ref);fp.SetValue('NPTH mounting hole')
            pad=pcbnew.PAD(fp);pad.SetNumber('');pad.SetAttribute(pcbnew.PAD_ATTRIB_NPTH)
            pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE);mask=pcbnew.LSET();mask.AddLayer(pcbnew.F_Mask);mask.AddLayer(pcbnew.B_Mask);pad.SetLayerSet(mask)
            pad.SetPosition(vec(0,0));fp.Add(pad);board.Add(fp)
        pads=list(fp.Pads())
        if len(pads)!=1:raise ValueError(f'{ref}: expected one NPTH pad')
        diameter=pcbnew.FromMM(hole['diameter_mm'])
        pads[0].SetSize(pcbnew.VECTOR2I(diameter,diameter))
        pads[0].SetDrillSize(pcbnew.VECTOR2I(diameter,diameter))
        fp.SetPosition(vec(*to_kicad(*hole['center'])))
        fp.SetLocked(True);fp.SetBoardOnly(True)
        fp.SetAttributes(fp.GetAttributes()|pcbnew.FP_EXCLUDE_FROM_BOM|pcbnew.FP_EXCLUDE_FROM_POS_FILES)
        fp.Reference().SetVisible(False)
        owned_refs.add(ref)
    # Keep existing generator-owned Edge.Cuts segments in place and only edit them.
    outlines=outline_segments(definition.outline,definition.corner_radius_mm)
    existing={item_uuid(x):x for x in board.GetDrawings()}
    managed_outline_ids={stable_uuid(board_id,'outline',str(i)) for i in range(1024)}
    for i,segment in enumerate(outlines):
        stable=stable_uuid(board_id,'outline',str(i));shape=existing.pop(stable,None)
        if shape is None:
            shape=pcbnew.PCB_SHAPE(board);shape.SetLayer(pcbnew.Edge_Cuts);shape.SetWidth(pcbnew.FromMM(0.05));board.Add(shape)
            new_ids[item_uuid(shape)]=stable
        if segment[0]=='line':
            shape.SetShape(pcbnew.SHAPE_T_SEGMENT)
            shape.SetStart(vec(*to_kicad(*segment[1])))
            shape.SetEnd(vec(*to_kicad(*segment[2])))
        else:
            shape.SetShape(pcbnew.SHAPE_T_ARC)
            shape.SetArcGeometry(*(vec(*to_kicad(*p)) for p in segment[1:]))
    for uid,shape in existing.items():
        if uid in managed_outline_ids:board.Remove(shape)
    # Copper keepouts are rule-area zones. Names and UUIDs establish ownership;
    # all other zones, including hand-filled planes, are left untouched.
    keepout_prefix=f'pcbgen:{board_id}:keepout:'
    existing_keepouts={}
    for zone in list(board.Zones()):
        name=zone.GetZoneName()
        if name.startswith(keepout_prefix):
            if item_uuid(zone)!=stable_uuid(board_id,'keepout',name[len(keepout_prefix):]):
                raise ValueError(f'unowned keepout name conflict: {name}')
            existing_keepouts[name]=zone
    owned_zone_ids=set()
    for keepout in definition.keepouts:
        for layer_name in keepout['layers']:
            if layer_name not in {'F.Cu','B.Cu'} and not layer_name.startswith('In'):
                raise ValueError(f"unsupported keepout layer {layer_name}")
            key=f"{keepout['id']}:{layer_name}"
            name=keepout_prefix+key
            zone=existing_keepouts.pop(name,None)
            if zone is None:
                zone=pcbnew.ZONE(board);zone.SetZoneName(name);board.Add(zone)
                new_ids[item_uuid(zone)]=stable_uuid(board_id,'keepout',key)
            else:zone.RemoveAllContours()
            zone.SetLayer(board.GetLayerID(layer_name));zone.SetIsRuleArea(True)
            zone.SetDoNotAllowTracks(True);zone.SetDoNotAllowVias(True)
            zone.SetDoNotAllowPads(True);zone.SetDoNotAllowZoneFills(True)
            zone.SetDoNotAllowFootprints(True)
            poly=zone.Outline();index=poly.NewOutline()
            for x,y in keepout['polygon']:
                px,py=to_kicad(x,y);poly.Append(vec(px,py),index)
            stable=stable_uuid(board_id,'keepout',key)
            owned_zone_ids.add(stable)
    for zone in existing_keepouts.values():board.Remove(zone)
    pcbnew.SaveBoard(str(path),board)
    owned_zone_ids.update(item_uuid(z) for z in board.Zones() if z.GetZoneName().startswith(f'pcbgen:{board_id}:'))
    normalize_file(path,board_id,owned_refs,new_ids,created,owned_zone_ids)
    print(f'{board_id}: {len(components)} footprints, {len(outlines)} outline edges; unowned board items retained; unvalidated draft')
    return path

def main():
    p=argparse.ArgumentParser();p.add_argument('board_id');p.add_argument('--output',type=Path);p.add_argument('--netlist',type=Path)
    a=p.parse_args();sync(a.board_id,a.output,a.netlist)
if __name__=='__main__':main()
