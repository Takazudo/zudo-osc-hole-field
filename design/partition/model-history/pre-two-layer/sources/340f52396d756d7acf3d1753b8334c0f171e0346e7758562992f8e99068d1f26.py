"""Narrow native exceptions for the exact owning main lands.

Keepout polygons and track/zone prohibitions stay unchanged. Native rules
permit the exact owning pad/footprint and contained same-net main vias only.
"""
from scripts.pcbgen.uuid_tools import stable_uuid


def rules(entries):
    lines=['(version 1)']
    for row in entries:
        condition=("A.intersectsArea('"+row['keepout_name']+"') && !(A.NetName == '"+
                   row['net']+"' && A.enclosedByArea('"+row['window_name']+"'))")
        lines.append('(rule "own-land-via-'+row['ref']+'" (condition "'+condition+'") (constraint disallow via))')
        pad_condition=("A.intersectsArea('"+row['keepout_name']+"') && !(A.Reference == '"+row['ref']+
            "' && A.NetName == '"+row['net']+"' && A.enclosedByArea('"+row['window_name']+"'))")
        lines.append('(rule "own-land-pad-'+row['ref']+'" (condition "'+pad_condition+'") (constraint disallow pad))')
        footprint_condition=("A.intersectsArea('"+row['keepout_name']+"') && !(A.Reference == '"+row['ref']+
            "' && A.enclosedByArea('"+row['keepout_name']+"'))")
        lines.append('(rule "own-land-footprint-'+row['ref']+'" (condition "'+footprint_condition+'") (constraint disallow footprint))')
    return '\n'.join(lines)+'\n'


def source_entries(definition,lands):
    result=[]
    for land in lands:
        x,y=land['center_mm'];matches=[]
        for keepout in definition['keepouts']:
            points=keepout['polygon'];xs=[p[0] for p in points];ys=[p[1] for p in points]
            if keepout['id'].startswith('POWER-') and keepout['layers']==['F.Cu'] and min(xs)<x<max(xs) and min(ys)<y<max(ys):
                matches.append(keepout)
        if len(matches)!=1:raise ValueError('main land requires one exact POWER reservation')
        result.append({'ref':land['reference'],'net':land['net'],'center_mm':[x,y],
            'keepout_id':matches[0]['id'],'keepout_polygon':matches[0]['polygon'],
            'keepout_name':'pcbgen:osc-core:keepout:'+matches[0]['id']+':F.Cu',
            'window_name':'pcbgen:osc-core:own-land-via:'+land['reference'],'land_size_mm':[4,4]})
    return result


def apply(board,entries):
    import pcbnew
    zones={z.GetZoneName():z for z in board.Zones()}
    receipts=[]
    for row in entries:
        owners=[f for f in board.GetFootprints() if f.GetReference()==row['ref']]
        if len(owners)!=1:raise ValueError('own main land needs one exact native footprint')
        owner=owners[0];pads=list(owner.Pads())
        if owner.m_Uuid.AsString()!=stable_uuid('osc-core','footprint:'+row['ref'],'root') or owner.GetLayer()!=pcbnew.F_Cu:
            raise ValueError('own main footprint UUID or face changed')
        if len(pads)!=1 or pads[0].GetNumber()!='1' or pads[0].GetNetname()!=row['net']:
            raise ValueError('own main pad identity or net changed')
        pad=pads[0];x,y=row['center_mm'];expected=[x+100,y+50]
        for item in (owner,pad):
            at=item.GetPosition()
            if max(abs(a-b) for a,b in zip([pcbnew.ToMM(at.x),pcbnew.ToMM(at.y)],expected))>1.001e-6:
                raise ValueError('own main source origin changed')
        if pad.GetAttribute()!=pcbnew.PAD_ATTRIB_SMD or pad.GetShape()!=pcbnew.PAD_SHAPE_RECT or [pcbnew.ToMM(pad.GetSize().x),pcbnew.ToMM(pad.GetSize().y)]!=[4,4]:
            raise ValueError('own main pad shape changed')
        keepout=zones[row['keepout_name']]
        if not keepout.GetIsRuleArea() or not all((keepout.GetDoNotAllowTracks(),keepout.GetDoNotAllowVias(),
            keepout.GetDoNotAllowPads(),keepout.GetDoNotAllowZoneFills(),keepout.GetDoNotAllowFootprints())):
            raise ValueError('POWER reservation prohibitions changed before own-land exception')
        keepout.SetDoNotAllowVias(False)
        keepout.SetDoNotAllowPads(False);keepout.SetDoNotAllowFootprints(False)
        window=pcbnew.ZONE(board);window.SetZoneName(row['window_name']);window.SetLayer(pcbnew.F_Cu)
        window.SetIsRuleArea(True)
        for setter in ('SetDoNotAllowTracks','SetDoNotAllowVias','SetDoNotAllowPads','SetDoNotAllowZoneFills','SetDoNotAllowFootprints'):
            getattr(window,setter)(False)
        x,y=row['center_mm'];poly=window.Outline();index=poly.NewOutline()
        for dx,dy in ((-2,-2),(2,-2),(2,2),(-2,2)):
            poly.Append(pcbnew.VECTOR2I(pcbnew.FromMM(x+100+dx),pcbnew.FromMM(y+50+dy)),index)
        window.SetUuid(pcbnew.KIID(stable_uuid('osc-core','terminal-via-window',row['ref'])))
        board.Add(window)
        receipts.append({**row,'keepout_uuid':keepout.m_Uuid.AsString(),'window_uuid':window.m_Uuid.AsString(),
            'owning_footprint_uuid':owner.m_Uuid.AsString(),'owning_pad_uuid':pad.m_Uuid.AsString(),
            'unchanged_prohibitions':['track','zone'],
            'via_rule':'Only owning net and entire finite via enclosed by exact own land; every other via prohibited.',
            'pad_rule':'Exact owning reference, same net and entire pad within own land only; native source audit separately requires exact UUID and one 4x4 pad.',
            'footprint_rule':'Exact owning reference and entire footprint within its existing POWER reservation only; source origin/face/UUID remains mandatory.'})
    return receipts
