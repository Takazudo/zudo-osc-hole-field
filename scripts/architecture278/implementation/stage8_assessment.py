"""Independent source composition and critical-corridor geometry checks."""
import argparse
import hashlib
import json
import math
from collections import Counter
from pathlib import Path
import stage8_rebudget as rebudget
import stage7_demonstrator as prior
import assembly

ROOT=rebudget.ROOT;OUT=rebudget.OUT

def require(ok,message):
    if not ok:raise ValueError(message)

def touches(a,b,box,margin):
    require(a[0]==b[0] or a[1]==b[1],'nonorthogonal corridor segment')
    return (max(min(a[0],b[0]),box[0]-margin)<=min(max(a[0],b[0]),box[2]+margin)
            and max(min(a[1],b[1]),box[1]-margin)<=min(max(a[1],b[1]),box[3]+margin))

def verify_corridors(report,mechanical):
    placements=mechanical['placements'];outline=mechanical['boards']['X1-jack']['outline_mm'];settings=report['routing_settings']
    expected_cuts={c['id']:c['box_mm'] for c in mechanical['manufacturing_sweep_bounds'] if c['board']=='X1-jack'}
    actual_cuts={o['id']:o['box_mm'] for o in report['obstacles'] if o['kind']=='substrate'}
    require(actual_cuts==expected_cuts and all(o['layers']==[0,1] for o in report['obstacles'] if o['kind']=='substrate'),'mechanical substrate obstacles omitted or changed')
    expected_mounts={m['id']:m['attachment_box_mm'] for m in mechanical['mounts']if m['board']=='X1-jack'}
    require({o['id']:o['box_mm'] for o in report['obstacles']if o['kind']=='mount_attachment'}==expected_mounts,'mechanical mount obstacles changed')
    expected_headers={h['ref']:h['box_mm']for h in mechanical['header_obstacles'].values()if h['board']=='X1-jack'}
    require({o['id']:o['box_mm']for o in report['obstacles']if o['kind']=='header'}==expected_headers,'header obstacles changed')
    expected_courtyards={p['ref']:p['box_mm']for p in placements.values()if p['board']=='X1-jack'}
    require({o['ref']:o['box_mm']for o in report['obstacles']if o['kind']=='courtyard'}==expected_courtyards,'package courtyard obstacles changed')
    for obstacle in report['obstacles']:
        require(obstacle['layers'] and set(obstacle['layers'])<= {0,1},'unknown obstacle layer')
        if obstacle['kind']=='mount_attachment':require(obstacle['layers']==[0,1],'mount obstacle layers changed')
        if obstacle['kind']=='header':require(obstacle['layers']==[1],'header obstacle layers changed')
        if obstacle['kind']=='courtyard':require(obstacle['layers']==[0 if placements[obstacle['ref']]['side']=='panel'else 1],'courtyard obstacle layers changed')
    kinds={};expected_pads=[]
    for ref,package in placements.items():
        pads={}
        for node in assembly.c.sexpr((ROOT/package['source']).read_text()):
            if isinstance(node,list)and node and node[0]=='pad':
                kinds[ref,node[1]]=node[2];pads.setdefault(node[1],[]).append(node)
        if package['board']!='X1-jack':continue
        for pin,coordinates in package['pads_mm'].items():
            require(len(coordinates)==len(pads[pin]),'source pad multiplicity changed')
            for xy,node in zip(coordinates,pads[pin]):
                size=list(map(float,assembly.c.field(node,'size')));at=assembly.c.field(node,'at')
                angle=float(at[2])if len(at)>2 else 0
                if (round(angle/90)+package['quarter_turn'])%2:size.reverse()
                box=(xy[0]-size[0]/2,xy[1]-size[1]/2,xy[0]+size[0]/2,xy[1]+size[1]/2)
                layers=(0,1)if node[2]in ('thru_hole','np_thru_hole')else(0 if package['side']=='panel'else 1,)
                expected_pads.append((ref,pin,package['pins'].get(pin),box,layers))
    actual_pads=[(o['ref'],o['pin'],o['net'],tuple(o['box_mm']),tuple(o['layers']))for o in report['obstacles']if o['kind']=='pad']
    require(Counter(actual_pads)==Counter(expected_pads),'source footprint pad obstacles changed')
    reservations=[]
    for row in report['corridors']:
        if row['status']!='CONDITIONAL_CORRIDOR':continue
        for a,b in zip(row['points_xy_layer'],row['points_xy_layer'][1:]):
            via=a[2]!=b[2];radius=settings['via_diameter_mm']/2 if via else settings['trace_width_mm']/2
            box=(min(a[0],b[0])-radius,min(a[1],b[1])-radius,max(a[0],b[0])+radius,max(a[1],b[1])+radius)
            reservations.append(('reserved_via'if via else'reserved_trace',row['net'],box,(0,1)if via else(a[2],)))
    actual_reservations=[(o['kind'],o['net'],tuple(o['box_mm']),tuple(o['layers']))for o in report['obstacles']if o['kind']in ('reserved_trace','reserved_via')]
    require(Counter(reservations)==Counter(actual_reservations),'critical copper reservations inventory omitted or changed')
    expected={('U3305','8','C3301','1'),('U3305','9','C3301','2'),('U3305','9','R3316','2'),('R3316','1','J1009','T'),('U3305','8','R3314','1'),('R3314','2','R3315','1'),('R3315','2','J1009','T'),('U3305','4','C3308','1'),('U3305','11','C3309','1')}
    expected.add(('C3308','2','C3309','2'))
    rows=report['corridors'];actual=[];success=0
    for row in rows:
        ends=row['endpoints'];actual.append(tuple(v for e in ends for v in (e['ref'],e['pin'])))
        for e in ends:
            package=placements[e['ref']]
            require(package['pins'][e['pin']]==row['net'],'corridor source net changed')
            require(package['pads_xyz_mm'][e['pin']]==[e['pad_xyz_mm']],'corridor detached from actual source pad')
            layers=[0,1]if kinds[e['ref'],e['pin']]in ('thru_hole','np_thru_hole')else[0 if package['side']=='panel'else 1]
            require(e['layers']==layers,'corridor endpoint layers disagree with footprint')
        if row['status']=='BLOCKED':continue
        require(row['status']=='CONDITIONAL_CORRIDOR','unknown corridor status')
        points=row['points_xy_layer'];require(len(points)>=2,'empty successful corridor')
        require(all(p[2]in (0,1)for p in points),'unknown corridor layer')
        for p,e in ((points[0],ends[0]),(points[-1],ends[1])):
            require(p[:2]==e['pad_xyz_mm'][:2] and p[2]in e['layers'],'corridor endpoint/layer mismatch')
        require(row['width_mm']==settings['trace_width_mm'] and row['clearance_mm']==settings['copper_clearance_mm'],'corridor width/clearance drift')
        obstacles=[o for o in report['obstacles'] if not(o['kind']in ['pad','reserved_trace','reserved_via'] and o.get('net')==row['net'])]
        segments=iter(row['segments']);via_count=0
        for a,b in zip(points,points[1:]):
            if a[2]!=b[2]:
                require(a[:2]==b[:2],'diagonal or displaced via');via_count+=1
                radius=settings['via_diameter_mm']/2;layers=[0,1];exemption=None
            else:
                segment=next(segments,None);require(segment is not None,'missing corridor segment')
                require(segment['from_xy_mm']==a[:2] and segment['to_xy_mm']==b[:2] and segment['layer']==a[2],'polyline/segment disagreement')
                exemption=segment['endpoint_courtyard_escape_exemption'];require(exemption is None or exemption in {e['ref'] for e in ends},'unrelated courtyard exemption')
                radius=row['width_mm']/2;layers=[a[2]]
            edge=radius+settings['substrate_edge_clearance_mm']
            require(all(outline[0]+edge<=p[0]<=outline[2]-edge and outline[1]+edge<=p[1]<=outline[3]-edge for p in (a,b)),'corridor outside substrate outline')
            for o in obstacles:
                if not set(layers)&set(o['layers']):continue
                if o['kind']=='courtyard' and o['ref']==exemption:continue
                clearance=max(row['clearance_mm'],settings['substrate_edge_clearance_mm']) if o['kind']=='substrate' else row['clearance_mm']
                require(not touches(a,b,o['box_mm'],radius+clearance),'corridor intersects obstacle '+o['id'])
        require(next(segments,None)is None,'extra corridor segment')
        require(via_count==len(row['vias']),'via inventory mismatch')
        require(math.isclose(row['copper_centreline_mm'],sum(math.dist(a[:2],b[:2])for a,b in zip(points,points[1:])),abs_tol=1e-9),'reported copper length changed')
        require(math.isclose(row['via_barrel_mm'],via_count*1.6,abs_tol=1e-9),'reported via length changed')
        terminal_barrels=sum(abs((20 if p[2]==0 else 21.6)-e['pad_xyz_mm'][2])for p,e in ((points[0],ends[0]),(points[-1],ends[1])))
        require(math.isclose(row['endpoint_THT_barrel_mm'],terminal_barrels,abs_tol=1e-9),'endpoint through-hole barrel length changed')
        require(math.isclose(row['developed_copper_and_barrel_mm'],row['copper_centreline_mm']+row['via_barrel_mm']+terminal_barrels,abs_tol=1e-9),'developed corridor length changed')
        transitions=Counter(tuple(a[:2])for a,b in zip(points,points[1:])if a[2]!=b[2])
        require(Counter(tuple(v['xy_mm'])for v in row['vias'])==transitions and all(v['layers']==[0,1]for v in row['vias']),'via positions or layers detached from polyline')
        require(all(v['diameter_mm']==settings['via_diameter_mm'] and v['drill_mm']==settings['via_drill_mm'] for v in row['vias']),'via geometry drift')
        success+=1
    require(len(actual)==len(expected) and set(actual)==expected,'critical connection inventory changed')
    return {'critical_connections':len(rows),'compatible_checked_corridors':success,'blocked_connections':len(rows)-success,'scope':'Independent full final obstacle inventory includes all different-net reserved traces/vias. No native DRC, full routing, return-plane or stability acceptance.'}

def build():
    require((OUT/'interface-input.json').exists(),'missing explicit Stage8 interface repair')
    paths={name:OUT/(name+'-report.json') for name in ('mechanical','locality','interfaces','electrical','currents')}
    reports={name:json.loads(path.read_text()) for name,path in paths.items()}
    for report in reports.values():rebudget.validate_bindings(report)
    rebudget.validate_interface_object(reports['interfaces'],reports['electrical'])
    corridor=verify_corridors(reports['locality'],reports['mechanical'])
    prior.verify_transport(reports['interfaces'])
    osc=OUT.parent/'stage6/candidate-report.json'
    require(hashlib.sha256(osc.read_bytes()).hexdigest()=='2a7eb6d0c9095d864854209cf7280a6e1f8719b06ec5f1142ad2694c855431f7','OSC baseline changed')
    paths.update({'scope':OUT/'scope.json','script':Path(__file__),'rebudget_script':Path(rebudget.__file__),'tests':Path(__file__).with_name('test_stage8_assessment.py'),'OSC':osc})
    return {'status':'X1 SOURCE REPAIR STUDY; READ EXPLICIT REMAINING CONSTRAINTS','corridors':corridor,'preserved':reports['interfaces']['conservation_counts'],'OSC_paths':225,'OSC_returns':240,'source_sha256':rebudget.bound(paths.values()),'hardware_acceptance':False,'native':'NOT RUN','ERC_DRC':'NOT RUN','simulation':'NOT RUN','physical':'NOT RUN'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args();r=build();data=rebudget.encode(r);path=OUT/'assessment-report.json'
    if args.check:require(path.read_text()==data,'stale Stage8 assessment')
    else:path.write_text(data)
    print(r['corridors'])

if __name__=='__main__':main()
