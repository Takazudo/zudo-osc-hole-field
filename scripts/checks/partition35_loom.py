#!/usr/bin/env python3
"""Conservative sampled ribbon corridors for proposed GH and load-side wiring."""
from __future__ import annotations
import argparse
from collections import defaultdict
import json
import math
from fractions import Fraction
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
import sys
sys.path.insert(0,str(ROOT))
from scripts.checks.partition35_json import dumps
from scripts.partition.model import JACK_BOARDS
from scripts.checks.connector_packing35 import core_service_depths,partition_source_digest
from scripts.geometry.power_wire import registered_route,directed
OUT=ROOT/'design/partition/loom-candidate.json'


def intersects(a,b):return all(a[i]<b[i+3]-1e-8 and b[i]<a[i+3]-1e-8 for i in range(3))


def power_cut_requirement(points,maximum,continuous_upper=None):
    """Keep the full ten millimetres for factory preparation and slack."""
    if not math.isfinite(maximum) or maximum<=0 or len(points)<2 or any(len(p)!=3 or not all(math.isfinite(v) for v in p) for p in points):
        raise ValueError('invalid power wire cut geometry or ceiling')
    length=sum(math.dist(p,q) for p,q in zip(points,points[1:]))
    if continuous_upper is not None:
        if not math.isfinite(continuous_upper) or continuous_upper<length:
            raise ValueError('continuous wire bound is below sampled length')
    minimum=length+10 if continuous_upper is None else directed(Fraction(continuous_upper)+10,True)
    return {'centreline_length_mm':length,'cut_length_allowance_mm':10,
            'minimum_cut_length_mm':minimum,'max_cut_length_mm':maximum}


def wire_reference(source,board,index):
    fan=json.loads((ROOT/'design/partition/contact-transfer-proposal.json').read_text())['main_strand_class']
    wire=json.loads((ROOT/'design/partition/wire-transfer-proposal.json').read_text())
    return registered_route(source,board,index,fan,wire['endpoint_adapter_class'],
                            metal_radius=wire['bulk_potential_class']['maximum_metal_radius_from_bundle_axis_mm'])


def power_route_errors(routes,source):
    """Recheck the actual route points before consuming their wire budget."""
    errors=[];power=source['load_distribution']
    expected={'POWER-'+b+'-'+label for b in power['branches'] for label in power['wire_labels']}
    if len(routes)!=len(expected) or {r['id'] for r in routes}!=expected:
        errors.append('power route inventory differs from source')
    for route in routes:
        continuous=None
        boards=[board for board in power['branches'] if route['id'].startswith('POWER-'+board+'-')]
        if len(boards)!=1:
            errors.append('unknown power route '+route['id']);continue
        if boards:
            board=boards[0];label=route['id'][len('POWER-'+board+'-'):]
            if label not in power['wire_labels']:
                errors.append('unknown power wire '+route['id']);continue
            reference=wire_reference(source,board,power['wire_labels'].index(label))
            if route.get('finite_endpoint_reference')!=reference or route['points_mm_positive_rear']!=reference['points_mm_positive_rear']:
                errors.append('power finite endpoint geometry differs from source '+route['id'])
            else:
                radius=reference['bulk_curve_bounds']['curvature_radius_lower_mm']
                if route.get('minimum_bend_radius_bound_mm')!=radius:
                    errors.append('power finite endpoint bend receipt differs from source '+route['id'])
                if radius<power['minimum_bend_radius_mm']:
                    errors.append('power wire bend too tight '+route['id'])
                continuous=reference['continuous_centreline_length_upper_mm']
        required=power_cut_requirement(route['points_mm_positive_rear'],power['max_wire_length_mm'],continuous)
        if any(not math.isfinite(route.get(k,float('nan'))) or not math.isclose(route[k],v,rel_tol=0,abs_tol=1e-6) for k,v in required.items()):
            errors.append('power wire cut receipt differs from source/geometry '+route['id'])
        if required['minimum_cut_length_mm']>required['max_cut_length_mm']:
            errors.append('power wire length exceeds loss budget '+route['id'])
    return errors


def build():
    src=json.loads((ROOT/'design/partition/partition-input.json').read_text());c=json.loads((ROOT/'design/partition/connector-packing-candidate.json').read_text())
    evidence=json.loads((ROOT/'design/connectors/jst-gh.json').read_text());family={r['positions']:r for r in evidence['sizes']};headers={h['id']:h for h in c['headers']}
    corridors=[];segments=[];errors=[];service_depths=core_service_depths(src)
    if c.get('partition_source_digest')!=partition_source_digest(src):errors.append('connector packing partition source digest drift')
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
    for board,branch in power['branches'].items():
        for index,(x,net) in enumerate(zip(branch['x_mm'],power['net_order'])):
            y=branch['pad_y_mm'];Y=branch['core_pad_y_mm'][index]
            name='POWER-'+board+'-'+power['wire_labels'][index]
            reference=wire_reference(src,board,index);points=reference['points_mm_positive_rear']
            bulk_points=reference['bulk_points_mm_positive_rear'];caps=reference['endpoint_reservations_mm_positive_rear']
            chord=reference['bulk_chord_error_upper_mm'];radius=reference['bulk_curve_bounds']['curvature_radius_lower_mm']
            if radius<power['minimum_bend_radius_mm']:errors.append('power wire bend too tight '+name)
            r=max(power['diameter_max_mm']/2,reference['bulk_metal_radius_mm'])+.25+chord
            for p,q in zip(bulk_points,bulk_points[1:]):
                b=[min(p[k],q[k])-r for k in range(3)]+[max(p[k],q[k])+r for k in range(3)]
                segments.append((name,b))
                if intersects(b,[260,248,45,308,293,85]):errors.append('power wire enters EXT reservation '+name)
            for cap in caps:
                b=[v-.25 for v in cap[:3]]+[v+.25 for v in cap[3:]]
                segments.append((name,b))
                if intersects(b,[260,248,45,308,293,85]):errors.append('power endpoint enters EXT reservation '+name)
            row={'id':name,'wire_mpn':power['wire'],'net':net,'points_mm_positive_rear':points,
                 **power_cut_requirement(points,power['max_wire_length_mm'],reference['continuous_centreline_length_upper_mm']),
                 'minimum_bend_radius_bound_mm':radius,'status':'PROPOSAL factory-soldered existing load-side nets only; no abstract inlet bridge'}
            row['finite_endpoint_reference']=reference
            power_routes.append(row)
    errors.extend(power_route_errors(power_routes,src))
    support_volumes=[]
    for board,bs in src['boards'].items():
        front,rear=service_depths['support_mm'] if board=='K' else (0,src['enclosure']['inside_depth_mm'])
        for x,y in bs['supports_mm']:support_volumes.append((board+' edge support',[x-1.6,y-1.6,front,x+1.6,y+1.6,rear]))
    carrier=src['jack_split']['carrier']
    for rect,z in [(carrier['rear_rect_mm'],carrier['rear_z_mm']),(carrier['front_lip_rect_mm'],carrier['front_lip_z_mm'])]+[(m['rect_mm'],m['z_mm']) for m in carrier['cross_members']]:
        support_volumes.append(('J split seam carrier',[rect[0],rect[1],-z[1],rect[2],rect[3],-z[0]]))
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
            'partition_source_digest':partition_source_digest(src),'K_service_depths_positive_rear_mm':service_depths,
            'support_reservation_count':len(support_volumes),'harness_count':len(corridors),'routes':corridors,'load_power_routes':power_routes,'max_cut_length_mm':max(r['cut_length_max_mm'] for r in corridors),
            'limits':['No measured cable solid, latch-access, crimp, stiffness or installed-fit PASS.',
                      'Mated 7.3 mm reference has no sourced tolerance; all planes and controlled loom guides are PROPOSAL.',
                      'Power distribution, support/hardware solids and connector service tooling are separate gates.',
                      'No live disassembly: disconnect external source, prove rails discharged, remove rear cover, release combs and unlatch K mates before releasing K supports. The 18 soldered main wires still tether K; supported service displacement or factory desoldering/replacement needs qualification #65. No unrestricted K removal or owner soldering is implied.']}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args();report=build();text=dumps(report)+'\n'
    if args.check:
        if not OUT.exists() or OUT.read_text()!=text:raise SystemExit('loom report drift')
    else:OUT.write_text(text)
    print(report['status'],'harnesses',report['harness_count'],'max cut',report['max_cut_length_mm'])
    if report['errors']:raise SystemExit('\n'.join(report['errors']))

if __name__=='__main__':main()
