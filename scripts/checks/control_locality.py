"""Source-controlled compact placement of whole P-board slew circuits.

This is a courtyard and supply-pad screen, not routed or physical qualification.
"""
import math
from collections import Counter
from scripts.pcbgen.placement_geometry import Box, inside_outline


def apply_locality(placements, io, source, connectors, lock, shapes, proposal, optical):
    # Imported lazily because the floorplan generator calls this after its base
    # capacity packing. The base generator remains the owner of frame geometry.
    from scripts.checks.partition35_floorplan import Grid, oriented_box, pads, footprint_pads, turn
    from scripts.checks.connector_packing35 import board_for, rect_collision
    parts={p['ref']:p for p in io['physical_packages']}
    prior={p['ref']:p for p in placements}
    if type(proposal.get('schema_version')) is not int or proposal['schema_version']!=1:
        raise ValueError('unsupported control locality schema')
    groups=proposal['groups']
    if set(groups)!={'H1','H2'}:raise ValueError('exactly both slew groups required')
    expected={};anchors={};all_refs=set()
    for instance,group in groups.items():
        candidates=[u for u in io['package_units'] if parts[u['ref']]['instance']==instance and u['region']=='control']
        def ref(role):
            found={u['ref'] for u in candidates if u['role']=='slew_island:'+role}
            if len(found)!=1:raise ValueError('incomplete source slew role '+instance+':'+role)
            return next(iter(found))
        amp=ref('PRE')
        if ref('POST')!=amp:raise ValueError('slew buffers must stay one complete source package')
        caps={p['ref'] for p in parts.values() if p['decouples_ref']==amp}
        if len(caps)!=2:raise ValueError('both physical bypasses required')
        refs={amp,ref('R_MIN'),*(ref('C'+str(i)) for i in range(1,6)),*caps}
        if len(refs)!=9 or set(group['placements'])!=refs or all_refs&refs:
            raise ValueError('slew placement must contain all nine unique non-panel parts')
        all_refs |= refs
        expected[instance]=(amp,caps,refs)
        uid='C:'+instance+'.SLEW'
        if group['anchor_uid']!=uid:raise ValueError('wrong fixed slew anchor')
        anchors[instance]=lock[uid]
        for r in refs:
            if parts[r]['panel_uid'] or parts[r]['dnp'] or board_for(parts[r])!='P' or prior[r]['fixed']:
                raise ValueError('cannot move fixed, DNP or non-control hardware')
    g=Grid('P','B.Cu',source['boards']['P']['outline'])
    for p in parts.values():
        if board_for(p)=='P' and p['panel_uid']:
            for _,b in pads(p,lock):g.fill(b)
    for h in connectors['headers']:
        if h['board']=='P' and h['side']=='B.Cu':g.fill(h['land_courtyard_mm'])
    for x,y in source['boards']['P']['supports_mm']:g.fill([x-1.6,y-1.6,x+1.6,y+1.6])
    for x in optical['support']['x_mm']:
        for y in optical['support']['y_mm']:
            if y>=176:g.fill([x-1.6,y-1.6,x+1.6,y+1.6])
    for r in source['boards']['P'].get('reserves',[]):
        if 'B.Cu' in r['sides']:g.fill(r['rect'])
    for p in placements:
        if p['board']=='P' and not p['fixed'] and p['ref'] not in all_refs:g.fill(p['courtyard_mm'])
    new={};report=[]
    for instance,group in groups.items():
        anchor=anchors[instance]
        for ref,pose in group['placements'].items():
            if set(pose)!={'x_mm','y_mm','rotation_deg'} or any(type(v) not in (int,float) or not math.isfinite(v) for v in pose.values()):
                raise ValueError('finite source pose required')
            x,y,angle=pose['x_mm'],pose['y_mm'],pose['rotation_deg']
            if angle not in (0,90,180,270):raise ValueError('orthogonal component rotation required')
            if math.hypot(x-anchor['x_mm'],y-anchor['y_mm'])>25:
                raise ValueError('slew component exceeds 25 mm geometric locality budget')
            b=oriented_box(shapes[parts[ref]['footprint']],'B.Cu',angle)
            box=[b[0]+x,b[1]+y,b[2]+x,b[3]+y]
            if not inside_outline(Box(*box),source['boards']['P']['outline'],.30):raise ValueError('slew courtyard outside P')
            x0,x1=math.floor(box[0]*g.scale),math.ceil(box[2]*g.scale)
            y0,y1=math.floor(box[1]*g.scale),math.ceil(box[3]*g.scale)
            mask=((1<<(x1-x0))-1)<<x0
            if any(row&mask for row in g.rows[y0:y1]):raise ValueError('slew courtyard collides: '+ref)
            if any(rect_collision(box,row['courtyard_mm'],.35) for row in new.values()):
                raise ValueError('new slew courtyards collide: '+ref)
            new[ref]={**prior[ref],**pose,'side':'B.Cu','courtyard_mm':box,'locality_group':instance}
        amp,caps,refs=expected[instance]
        pin_nets={r:{} for r in refs}
        for u in io['package_units']:
            if u['ref'] in refs:pin_nets[u['ref']].update(u['pins'])
        def point(ref,net):
            item=new[ref];pin=next(k for k,v in pin_nets[ref].items() if v==net)
            x,y=footprint_pads(parts[ref]['footprint'])[pin]
            x,y=turn((-x,y),item['rotation_deg'])
            return x+item['x_mm'],y+item['y_mm']
        distances=[]
        for cap in sorted(caps):
            rail=next(n for n in pin_nets[cap].values() if n in ('+12V','-12V','+5V'))
            distance=math.dist(point(amp,rail),point(cap,rail))
            if distance>3:raise ValueError('slew bypass exceeds 3 mm supply-pad screen')
            distances.append({'capacitor':cap,'amplifier':amp,'rail':rail,'distance_mm':distance})
        report.append({'instance':instance,'anchor_uid':group['anchor_uid'],'moved_references':sorted(refs),
                       'maximum_component_centre_distance_mm':max(math.hypot(new[r]['x_mm']-anchor['x_mm'],new[r]['y_mm']-anchor['y_mm']) for r in refs),
                       'bypass_supply_pad_distances':distances})
    result=[new.get(p['ref'],p) for p in placements]
    if Counter(p['ref'] for p in result)!=Counter(p['ref'] for p in placements):raise ValueError('locality changed package roster')
    return result,report
