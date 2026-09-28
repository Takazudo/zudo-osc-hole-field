#!/usr/bin/env python3
"""Conservative sampled ribbon corridors for proposed GH and load-side wiring."""
from __future__ import annotations
import argparse
from collections import defaultdict
import json
import math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0,str(ROOT))
from scripts.checks.partition35_json import dumps
OUT=ROOT/'design/partition/loom-candidate.json'


def intersects(a,b):return all(a[i]<b[i+3]-1e-8 and b[i]<a[i+3]-1e-8 for i in range(3))


def build():
    src=json.loads((ROOT/'design/partition/partition-input.json').read_text());c=json.loads((ROOT/'design/partition/connector-packing-candidate.json').read_text())
    evidence=json.loads((ROOT/'design/connectors/jst-gh.json').read_text());family={r['positions']:r for r in evidence['sizes']};headers={h['id']:h for h in c['headers']}
    corridors=[];segments=[];errors=[]
    for h in c['harnesses']:
        a,b=[headers[i] for i in h['header_ids']]
        if a['board']=='K':a,b=b,a
        x,y=a['center_mm'];X,Y=b['center_mm'];n=a['contacts'];f=family[n]
        da=-src['boards'][a['board']]['face_z_mm']+src['boards'][a['board']]['thickness_mm']+f['mated_height_reference_mm']
        db=-src['boards'][b['board']]['face_z_mm']+(src['boards'][b['board']]['thickness_mm']+f['mated_height_reference_mm'] if b['board']!='K' else -f['mated_height_reference_mm'])
        points=[]
        if b['board']=='K':
            if (x,y)!=(X,Y):raise ValueError('offset core port requires a new route '+h['id'])
            for i in range(101):
                t=i/100;points.append([x,y+4*math.sin(math.pi*t)**2,da+(db-da)*t])
            min_radius=(db-da)**2/(8*math.pi**2)
            form='axial ribbon with 4 mm common smooth bow; conductor order preserved by K 180-degree orientation'
        else:
            if x!=X:raise ValueError('utility loop must retain x corridor')
            for i in range(201):
                t=i/200;points.append([x,(y+Y)/2-(Y-y)/2*math.cos(math.pi*t),da+(db-da)*t+60*math.sin(math.pi*t)])
            min_radius=min(60,(Y-y)/2)**2/max(60,(Y-y)/2)-1
            form='separate utility service loop; 60 mm rearward ellipse; mates both rear-facing'
        length=sum(math.dist(p,q) for p,q in zip(points,points[1:]));width=(n-1)*f['pitch_mm']+.9398+.5;depth=f['header_body_depth_mm']+.5
        if a['rotation_deg']%180==90:width,depth=depth,width
        if min_radius<9.398:errors.append('bend too tight '+h['id'])
        if length+10>300:errors.append('wire length exceeds limit '+h['id'])
        envelope=[]
        # Contact pitch fixes ribbon width; retain the entire header depth plus
        # 0.5 mm for its guided conductor exit. 0.05 mm covers interpolation chord error.
        for p,q in zip(points,points[1:]):
            b=[min(p[0],q[0])-width/2-.05,min(p[1],q[1])-depth/2-.05,min(p[2],q[2])-.05,
               max(p[0],q[0])+width/2+.05,max(p[1],q[1])+depth/2+.05,max(p[2],q[2])+.05]
            envelope.append(b);segments.append((h['id'],b))
            if intersects(b,[260,248,45,308,293,85]):errors.append('EXT reservation crossing '+h['id']);break
        corridors.append({'id':h['id'],'status':'PROPOSAL controlled flat loom; physical assembly NOT RUN','route':form,
                          'conductor_count':n,'wire_mpn':'Alpha Wire 6821 BK005','centreline_points_mm_positive_rear':points,
                          'centreline_length_mm':round(length,6),'cut_length_max_mm':math.ceil(length+10),
                          'minimum_curvature_radius_bound_mm':round(min_radius,6),'ribbon_channel_width_mm':width,'ribbon_channel_depth_mm':depth,
                          'strain_relief':'Insulating combs fixed to enclosure carrier within 15 mm of each header; intermediate comb spacing <=25 mm. Unclamp with power removed before service.',
                          'capacitance':'Whole-driver aggregate <=1 nF including all branches; assembled measurement NOT RUN.'})
    power_routes=[]
    power=src['load_distribution']
    for board in ('J','P'):
        for index,(x,net) in enumerate(zip(power['x_mm'],power['net_order'])):
            y=power[board+'_pad_y_mm'];Y=power['K_'+board+'_pad_y_mm_by_wire'][index]
            da=-src['boards'][board]['face_z_mm']+src['boards'][board]['thickness_mm']+1
            db=-src['boards']['K']['face_z_mm']-1
            points=[[x,y+(Y-y)*i/100+10*math.sin(math.pi*i/100)**2,da+(db-da)*i/100] for i in range(101)]
            name='POWER-'+board+'-'+power['wire_labels'][index];radius=(db-da)**2/(20*math.pi**2);length=sum(math.dist(p,q) for p,q in zip(points,points[1:]))
            if radius<power['minimum_bend_radius_mm']:errors.append('power wire bend too tight '+name)
            if length+10>power['max_wire_length_mm']:errors.append('power wire length exceeds loss budget '+name)
            r=power['diameter_max_mm']/2+.25
            for p,q in zip(points,points[1:]):
                b=[min(p[k],q[k])-r for k in range(3)]+[max(p[k],q[k])+r for k in range(3)]
                segments.append((name,b))
                if intersects(b,[260,248,45,308,293,85]):errors.append('power wire enters EXT reservation '+name)
            power_routes.append({'id':name,'wire_mpn':power['wire'],'net':net,'points_mm_positive_rear':points,'centreline_length_mm':length,'max_cut_length_mm':125,'minimum_bend_radius_bound_mm':radius,'status':'PROPOSAL factory-soldered existing load-side nets only; no abstract inlet bridge'})
    support_volumes=[]
    for board,bs in src['boards'].items():
        for x,y in bs['supports_mm']:support_volumes.append((board+' edge support',[x-1.6,y-1.6,98 if board=='K' else 0,x+1.6,y+1.6,120]))
    optical=json.loads((ROOT/'design/partition/stage-optical-candidate.json').read_text())
    for post in optical['support_posts']:
        x,y=post['center_mm'];support_volumes.append(('optical post/collar',[x-1.6,y-1.6,3.6,x+1.6,y+1.6,14.8]))
    support_volumes.append(('selected octave carrier rails',[5.4,170,0,91.6,172,34]))
    for name,b in segments:
        for support,q in support_volumes:
            if intersects(b,q):errors.append('loom/support collision '+name+' '+support)
    # Spatial buckets only cull tests; every retained pair receives an exact AABB test.
    buckets=defaultdict(list);collisions=set()
    for current,(name,b) in enumerate(segments):
        cells=[(x,y,z) for x in range(math.floor(b[0]/10),math.floor(b[3]/10)+1) for y in range(math.floor(b[1]/10),math.floor(b[4]/10)+1) for z in range(math.floor(b[2]/10),math.floor(b[5]/10)+1)]
        seen=set()
        for cell in cells:
            for index in buckets[cell]:
                if index in seen:continue
                seen.add(index);other,q=segments[index]
                if other!=name and intersects(b,q):collisions.add(tuple(sorted((name,other))))
        for cell in cells:buckets[cell].append(current)
    errors +=['loom corridor overlap '+a+' '+b for a,b in sorted(collisions)]
    return {'schema_version':1,'status':'FAIL' if errors else 'PASS - nominal controlled ribbon corridor geometry only','errors':sorted(set(errors)),
            'support_reservation_count':len(support_volumes),'harness_count':len(corridors),'routes':corridors,'load_power_routes':power_routes,'max_cut_length_mm':max(r['cut_length_max_mm'] for r in corridors),
            'limits':['No measured cable solid, latch-access, crimp, stiffness or installed-fit PASS.',
                      'Mated 7.3 mm reference has no sourced tolerance; all planes and controlled loom guides are PROPOSAL.',
                      'Power distribution, support/hardware solids and connector service tooling are separate gates.',
                      'No live disassembly: disconnect external source, prove rails discharged, remove rear cover, release combs, unlatch all K mates through proposed service apertures, then remove K supports.']}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args();report=build();text=dumps(report)+'\n'
    if args.check:
        if not OUT.exists() or OUT.read_text()!=text:raise SystemExit('loom report drift')
    else:OUT.write_text(text)
    print(report['status'],'harnesses',report['harness_count'],'max cut',report['max_cut_length_mm'])
    if report['errors']:raise SystemExit('\n'.join(report['errors']))

if __name__=='__main__':main()
