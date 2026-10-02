#!/usr/bin/env python3
"""Propose GH connector sites against fixed hardware pads; no PCB is generated."""
from __future__ import annotations
from collections import defaultdict
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.checks.partition35_json import dumps
from scripts.partition.model import jack_board, JACK_BOARDS, source
from scripts.pcbgen.netlist import TOKEN, parse, many, one
from scripts.checks.partition35_diagnostic import footprint_geometry
OUT=ROOT/'design/partition/connector-packing-candidate.json'


def partition_source_digest(spec):
    """Bind source content, independent of JSON whitespace and member order."""
    return hashlib.sha256(json.dumps(spec,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def core_service_depths(spec):
    """Positive-rear proposal depths, never manufacturer tool/fit evidence."""
    core=spec['boards']['K'];proposal=core['service_access']
    depth=-core['face_z_mm'];rear=spec['enclosure']['inside_depth_mm']
    offset=proposal['support_front_offset_mm'];near,far=proposal['hook_forward_offsets_mm']
    if not all(math.isfinite(v) for v in (depth,rear,offset,near,far)) or not (0<=offset<depth and 0<=near<far<depth and depth+core['thickness_mm']<=rear):
        raise ValueError('invalid K support/tool depth proposal')
    return {'support_mm':[depth-offset,rear],'hook_mm':[depth-far,depth-near]}


def board_for(part):
    if part['regions'][0]=='jack':return jack_board(part['instance'])
    return {'control':'P','core':'K','stage_optical':'EL'}.get(part['regions'][0],part['instance'])


def rect_collision(a,b,gap=.25):
    return a[0]<b[2]+gap-1e-9 and b[0]<a[2]+gap-1e-9 and a[1]<b[3]+gap-1e-9 and b[1]<a[3]+gap-1e-9


def pads(part,lock):
    p=lock[part['panel_uid']];path=ROOT/'footprints/kicad/zudo-osc-hole-field.pretty'/(part['footprint'].split(':')[1]+'.kicad_mod')
    root,_=parse(TOKEN.findall(path.read_text()));angle=math.radians(p['rot_deg']);co,si=math.cos(angle),math.sin(angle)
    result=[]
    for pad in many(root,'pad'):
        if pad[2] not in ('thru_hole','np_thru_hole'):continue
        pos=one(pad,'at');x,y=map(float,pos[1:3]);w,h=map(float,one(pad,'size')[1:3]);extra=math.radians(float(pos[3])) if len(pos)>3 else 0
        a=angle+extra;bw=abs(w*math.cos(a))+abs(h*math.sin(a));bh=abs(w*math.sin(a))+abs(h*math.cos(a))
        x,y=p['x_mm']+x*co-y*si,p['y_mm']+x*si+y*co
        result.append((part['ref']+'.'+pad[1],[x-bw/2,y-bh/2,x+bw/2,y+bh/2]))
    return result


def candidate():
    spec=source();service_depths=core_service_depths(spec)
    io=json.loads((ROOT/'design/reports/io-partition.json').read_text());lock={p['uid']:p for p in json.loads((ROOT/'design/grid/placements.lock.json').read_text())['placements']}
    parts={p['ref']:p for p in io['physical_packages']};boards={r:board_for(p) for r,p in parts.items()};pairs=defaultdict(dict)
    for row in io['allowed_crossings']:
        if row['kind']=='power/return':continue
        touched={boards[m['ref']] for m in row['members']};drivers={boards[m['ref']] for m in row['direction']['source_nodes']}
        if len(drivers)!=1:raise ValueError('ambiguous signal source '+row['net'])
        driver=next(iter(drivers))
        for other in touched-{driver}:pairs[tuple(sorted((driver,other)))][row['net']]={'driver_board':driver,'receiver_board':other,'kind':row['kind']}
    pots=sorted((p for p in lock.values() if p['kind']=='pot'),key=lambda p:(p['y_mm'],p['x_mm']))
    utility=[(40,276),(57,276),(74,276),(91,276)]
    ps=[(p['x_mm'],p['y_mm']) for p in pots if (p['x_mm'],p['y_mm']) not in utility]
    ps +=[(14.5+17*i,y) for i in range(5) for y in (206,218.5)]
    ps +=[(218.5+17*i,y) for i in range(6) for y in (192,206,219.75)]
    # Keep every loom clear of the EXT inlet XYZ reservation. Relocate only
    # free connectors, never the controls whose traces reach these sites.
    ps=[s for s in ps if not(s[0]>254 and s[1]>242)]
    ps +=[(142+17*i,y) for y in (234,248) for i in range(4)]+[(142,262)]
    js={'JL':[(x,y) for y in (38,80,122) for x in range(23,160,17)][:25],
        'JR':[(x,y) for y in (38,80,122) for x in range(193,296,17)]+[(x,150) for x in (193,210,227,244,261,278)]}
    families={3:{'header':'BM03B-GHS-TBT(LF)(SN)','housing':'GHR-03V-S','bbox':[7.5,6.1]},
              7:{'header':'BM07B-GHS-TBT(LF)(SN)','housing':'GHR-07V-S','bbox':[12.5,6.1]},
              8:{'header':'BM08B-GHS-TBT(LF)(SN)','housing':'GHR-08V-S','bbox':[13.75,6.1]}}
    for n,f in families.items():
        f['footprint']='zudo-osc-hole-field:JST_GH%d_BM_TopEntry'%n
        f['courtyard']=footprint_geometry(ROOT/'footprints/kicad/zudo-osc-hole-field.pretty'/('JST_GH%d_BM_TopEntry.kicad_mod'%n))['courtyard_bbox_mm']
        b=f['courtyard'];f['bbox']=[b[2]-b[0],b[3]-b[1]]
    headers=[];harnesses=[];ji={b:0 for b in JACK_BOARDS};pi=0;orphans=0
    def add(hid,board,site,pins,n,base_angle=0):
        f=families[n];w,h=f['bbox'];x,y=site
        angle=base_angle+(180 if board=='K' else 0)
        if base_angle==90:w,h=h,w
        centre_y=(f['courtyard'][1]+f['courtyard'][3])/2
        a=math.radians(angle);origin=[x+centre_y*math.sin(a),y-centre_y*math.cos(a)]
        headers.append({'id':hid,'board':board,'center_mm':[x,y],'footprint_origin_mm':[round(v,6) for v in origin],'rotation_deg':angle,'kicad_orientation_deg':((0 if board=='K' else 180)-angle)%360,'side':'F.Cu' if board=='K' else 'B.Cu',
                        'header_mpn':f['header'],'housing_mpn':f['housing'],'contact_mpn':'SSHL-002T-P0.2',
                        'contacts':n,'pin_map':{str(i+1):v for i,v in enumerate(pins)},
                        'land_courtyard_mm':[x-w/2,y-h/2,x+w/2,y+h/2],
                        'status':'DERIVED from exact #63 generated footprint; location PROPOSAL'})
    for pair,ns in sorted(pairs.items()):
        if pair==('EL','K'):continue
        n=3 if 'P' in pair else 7 if any(b.startswith('O') for b in pair) else 8
        nets=sorted(ns);chunks=[]
        if n==7:
            chunks=[nets[:4],nets[4:]]
        else:
            count=(n+1)//2;chunks=[nets[i:i+count] for i in range(0,len(nets),count)]
        for index,chunk in enumerate(chunks):
            pins=[]
            for net in chunk:pins.extend([net,'AGND'])
            pins=pins[:n]+['NC']*max(0,n-len(pins))
            if n==7 and len(chunk)==3:pins[-1]='AGND'
            name='-'.join(pair)+'-'+str(index+1)
            if pair==('K','P'):
                if pi>=len(ps):raise ValueError('control header site overflow')
                site=ps[pi];pi+=1;ksite=site
                if site[0]>254 and site[1]>242:
                    ksite=(244,218+7*orphans);orphans+=1
                locations={'P':site,'K':ksite}
            elif pair==('JL','P'):
                if index>=len(utility):raise ValueError('utility header site overflow')
                locations={'P':utility[index],'JL':(utility[index][0],150)}
            elif pair[1]=='K' and pair[0] in JACK_BOARDS:
                jb=pair[0];site=js[jb][ji[jb]];ji[jb]+=1
                locations={jb:site,'K':site}
            else:
                selector=next(b for b in pair if b.startswith('O'))
                shaft=lock['C:'+selector+'.OCT'];site=(shaft['x_mm'],shaft['y_mm']+(-3.5 if index==0 else 3.5))
                locations={selector:site,'K':site}
            for board in pair:add(name+'-'+board,board,locations[board],pins,n,90 if pair==('K','P') else 0)
            harnesses.append({'id':name,'boards':list(pair),'header_ids':[name+'-'+b for b in pair],
                              'signals':[{'net':net,**ns[net]} for net in chunk],
                              'signal_count':len(chunk),'return_contacts':pins.count('AGND'),'unused_contacts':pins.count('NC')})
    optical=json.loads((ROOT/'design/partition/stage-optical-input.json').read_text())
    for port in optical['ports']:
        pins=list(port['pins'].values());name=port['id']
        for board in ('EL','K'):add(name+'-'+board,board,port['center_mm'],pins,8)
        harnesses.append({'id':name,'boards':['EL','K'],'header_ids':[name+'-EL',name+'-K'],
                          'signals':[{'net':net,**pairs['EL','K'][net]} for net in pins if net in pairs['EL','K']],
                          'signal_count':3,'return_contacts':2,'rail_contacts':3,'unused_contacts':0})
    for header in headers:
        b=header['land_courtyard_mm'];header['native_cached_courtyard_envelope_mm']=[b[0]-.05,b[1]-.05,b[2]+.05,b[3]+.05]
    errors=[];byboard=defaultdict(list)
    for h in headers:byboard[h['board']].append(h)
    for board,items in byboard.items():
        pads_here=[entry for p in parts.values() if boards[p['ref']]==board and p['panel_uid'] for entry in pads(p,lock)]
        for i,h in enumerate(items):
            box=h['native_cached_courtyard_envelope_mm']
            for other in items[:i]:
                if rect_collision(box,other['native_cached_courtyard_envelope_mm']):errors.append(f'header overlap {h["id"]} {other["id"]}')
            for ref,pad in pads_here:
                if rect_collision(box,pad):errors.append(f'header/pad overlap {h["id"]} {ref}')
            l,t,r,b=box
            if board in JACK_BOARDS:
                polygon=source()['boards'][board]['outline'];inside=min(p[0] for p in polygon)+.25<=l and r<=max(p[0] for p in polygon)-.25 and 20.25<=t and b<=163.75
            elif board=='P':inside=6.25<=l and r<=311.75 and 176.25<=t and b<=291.75 and (l>=94.25 or t>=194.25)
            elif board=='K':inside=6.25<=l and r<=311.75 and 8.25<=t and b<=291.75 and (r<=257.75 or b<=245.75)
            elif board=='EL':inside=210.25<=l and r<=316.75 and 164.25<=t and b<=276.75
            else:
                shaft=lock['C:'+board+'.OCT'];inside=shaft['x_mm']-9.65<=l and r<=shaft['x_mm']+9.65 and 174.75<=t and b<=195.25
            if not inside:errors.append('header outside outline/keepout '+h['id'])
    service=[]
    for h in byboard['K']:
        x,y=h['center_mm'];box=h['land_courtyard_mm'];w=box[2]-box[0];d=box[3]-box[1]
        candidates=[(x+w/2+1.75,y),(x-w/2-1.75,y),(x,y+d/2+1.75),(x,y-d/2-1.75)]
        chosen=None
        for sx,sy in candidates:
            b=[sx-1.1,sy-1.1,sx+1.1,sy+1.1]
            if not(4.25<=b[0] and b[2]<=313.75 and 8.25<=b[1] and b[3]<=291.75 and (b[2]<=257.75 or b[3]<=245.75)):continue
            if any(rect_collision(b,k['land_courtyard_mm']) for k in byboard['K']):continue
            if any(rect_collision(b,k['box_mm']) for k in service):continue
            sweep=[min(x,sx)-.75,min(y,sy)-.75,max(x,sx)+.75,max(y,sy)+.75]
            if any(rect_collision(sweep,k['land_courtyard_mm'],0) for k in byboard['K'] if k['id']!=h['id']):continue
            chosen={'header_id':h['id'],'center_mm':[sx,sy],'diameter_mm':2.2,'box_mm':b,'tool_shaft_diameter_mm':1.5,'hook_sweep_xy_mm':sweep,'hook_sweep_positive_depth_mm':service_depths['hook_mm'],'status':'PROPOSAL straight hook approach; mating/latch mechanics and installed tool fit NOT RUN'};break
        if chosen is None:errors.append('no service aperture '+h['id'])
        else:service.append(chosen)
    from scripts.checks.control_connector_locality import reassign
    locality_source = ROOT/'design/partition/control-connector-locality.json'
    headers, service, locality = reassign(headers, service, json.loads(locality_source.read_text()))
    return {'schema_version':1,'status':'PASS - preliminary pad/edge packing only' if not errors else 'FAIL',
            'errors':errors,'partition_source_digest':partition_source_digest(spec),'family_envelopes':families,'header_count':len(headers),'harness_count':len(harnesses),
            'headers_by_board':{b:len(hs) for b,hs in sorted(byboard.items())},'control_sites_available':len(ps)+len(utility),
            'control_sites_used':pi+len(utility),'jack_sites_used':ji,'core_inlet_notch_relocations':orphans,
            'headers':headers,'harnesses':harnesses,'K_service_apertures':service,
            'control_connector_locality':{'source':'design/partition/control-connector-locality.json',**locality},
            'limits':['Exact #63 generated footprint courtyards consumed; no tolerance-qualified 3D fit.','No mounted hardware/body or routed PCB PASS follows from 2D bounds.',
                      'Detailed harness bend/service/strain-relief sweeps and all free component placements still need full partition check.',
                      'No source or power inlet selected; #59 protection and #55/#57 installed fit remain open.']}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args();report=candidate();text=dumps(report)+'\n'
    if args.check:
        if not OUT.exists() or OUT.read_text()!=text:raise SystemExit('connector packing report drift')
    else:OUT.write_text(text)
    print(report['status'],report['header_count'],'headers',report['harness_count'],'harnesses',report['headers_by_board'])
    if report['errors']:raise SystemExit('\n'.join(report['errors']))


if __name__=='__main__':main()
