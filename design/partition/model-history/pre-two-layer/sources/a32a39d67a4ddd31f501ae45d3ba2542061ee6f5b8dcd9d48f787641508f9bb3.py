"""Exact owning terminal exceptions on the source-declared board and face.

The historical K helper remains unchanged for its retained native authority.
No new reservation is invented when a source land has no POWER rule area.
"""
from scripts.pcbgen.uuid_tools import stable_uuid
from scripts.pcbgen.core_terminal_access import rules


def source_entries(definition,lands):
    result=[];board_id=definition['board_id']
    for land in lands:
        x,y=land['center_mm'];side=land['side'];matches=[]
        for keepout in definition['keepouts']:
            xs=[p[0] for p in keepout['polygon']];ys=[p[1] for p in keepout['polygon']]
            if keepout['id'].startswith('POWER-') and keepout['layers']==[side] and min(xs)<x<max(xs) and min(ys)<y<max(ys):
                matches.append(keepout)
        if not matches:continue
        if len(matches)!=1:raise ValueError('ambiguous existing main POWER reservation')
        k=matches[0]
        result.append({'board_id':board_id,'side':side,'ref':land['reference'],'net':land['net'],'center_mm':[x,y],
            'keepout_id':k['id'],'keepout_polygon':k['polygon'],
            'keepout_name':'pcbgen:'+board_id+':keepout:'+k['id']+':'+side,
            'window_name':'pcbgen:'+board_id+':own-land-via:'+land['reference'],'land_size_mm':[4,4]})
    return result


def apply(board,entries):
    import pcbnew
    zones={z.GetZoneName():z for z in board.Zones()};receipts=[]
    for row in entries:
        owners=[f for f in board.GetFootprints() if f.GetReference()==row['ref']]
        if len(owners)!=1:raise ValueError('one exact source owning footprint required')
        owner=owners[0];pads=list(owner.Pads());layer=pcbnew.F_Cu if row['side']=='F.Cu' else pcbnew.B_Cu
        if row['side'] not in ('F.Cu','B.Cu') or owner.GetLayer()!=layer or owner.m_Uuid.AsString()!=stable_uuid(row['board_id'],'footprint:'+row['ref'],'root'):
            raise ValueError('own terminal native UUID or face changed')
        if len(pads)!=1 or pads[0].GetNumber()!='1' or pads[0].GetNetname()!=row['net']:
            raise ValueError('own terminal pad identity or net changed')
        pad=pads[0];x,y=row['center_mm']
        for item in (owner,pad):
            at=item.GetPosition()
            if max(abs(a-b) for a,b in zip([pcbnew.ToMM(at.x),pcbnew.ToMM(at.y)],[x+100,y+50]))>1.001e-6:
                raise ValueError('own terminal source origin changed')
        if pad.GetAttribute()!=pcbnew.PAD_ATTRIB_SMD or pad.GetShape()!=pcbnew.PAD_SHAPE_RECT or [pcbnew.ToMM(pad.GetSize().x),pcbnew.ToMM(pad.GetSize().y)]!=[4,4]:
            raise ValueError('own terminal finite pad geometry changed')
        keepout=zones[row['keepout_name']]
        if keepout.GetLayer()!=layer or not keepout.GetIsRuleArea() or not all((keepout.GetDoNotAllowTracks(),keepout.GetDoNotAllowVias(),keepout.GetDoNotAllowPads(),keepout.GetDoNotAllowZoneFills(),keepout.GetDoNotAllowFootprints())):
            raise ValueError('original POWER reservation face/prohibitions changed')
        keepout.SetDoNotAllowVias(False);keepout.SetDoNotAllowPads(False);keepout.SetDoNotAllowFootprints(False)
        window=pcbnew.ZONE(board);window.SetZoneName(row['window_name']);window.SetLayer(layer);window.SetIsRuleArea(True)
        for setter in ('SetDoNotAllowTracks','SetDoNotAllowVias','SetDoNotAllowPads','SetDoNotAllowZoneFills','SetDoNotAllowFootprints'):
            getattr(window,setter)(False)
        outline=window.Outline();index=outline.NewOutline()
        for dx,dy in ((-2,-2),(2,-2),(2,2),(-2,2)):
            outline.Append(pcbnew.VECTOR2I(pcbnew.FromMM(x+100+dx),pcbnew.FromMM(y+50+dy)),index)
        window.SetUuid(pcbnew.KIID(stable_uuid(row['board_id'],'terminal-via-window',row['ref'])));board.Add(window)
        receipts.append({**row,'owning_footprint_uuid':owner.m_Uuid.AsString(),'owning_pad_uuid':pad.m_Uuid.AsString(),
            'keepout_uuid':keepout.m_Uuid.AsString(),'window_uuid':window.m_Uuid.AsString(),'unchanged_prohibitions':['track','zone']})
    return receipts
