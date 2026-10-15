"""Rebudget an explicit whole-middle-header repair; no routing or hardware execution."""
import argparse,copy,json,math
from pathlib import Path
import assembly as a
import direct_study as d
ROOT=a.ROOT;OUT=a.OUT/'stage5'

def apply_moves(candidate,assembly,spec):
    out=copy.deepcopy(candidate);moves={}
    for move in spec['moves']:
        key=(move['instance'],move['header_ref']);delta=move['delta_mm']
        a.c.require(key not in moves and key[0] in assembly['front_instances'],'duplicate/unknown header instance')
        a.c.require(len(delta)==2 and all(math.isfinite(x)for x in delta),'finite XY translation')
        a.c.require(any(p['ref']==key[1]for p in assembly['middle_header_placements']),'unknown header')
        moves[key]=delta
    headers={}
    for instance in assembly['front_instances']:
        for p in assembly['middle_header_placements']:
            delta=moves.get((instance,p['ref']),[0,0]);offset=[17*(int(instance[1:])-1)+delta[0],delta[1]]
            q=copy.deepcopy(p);q['instance']=instance;q['origin_mm']=a.transform(p['origin_mm'],offset,0);q['box_mm']=a.box_transform(p['box_mm'],offset,0)
            q['pads_mm']={pin:[a.transform(xy,offset,0)for xy in points]for pin,points in p['pads_mm'].items()}
            headers[instance,p['ref']]=q
    config=assembly['config'];changed=[]
    for index,row in enumerate(out['paths']):
        if 'link'not in row:continue
        header=headers[row['instance'],'M:'+row['link']];point=header['pads_mm'][row['link_pin']][0]
        if point!=row['middle_header_pad_mm']:changed.append(index)
        row['middle_header_pad_mm']=point
        target=row['other_pad_mm']if row['DIN_pad_mm']is None else row['DIN_pad_mm']
        row['segments']['middle_trace_mm']=d.segment(point,target,config)
        row['total_mm']=sum(row['segments'].values());row['margin_mm']=300-row['total_mm']
    def ground_contact(label,instance):
        n=int(label.split(':')[-1][1:]);point=a.transform([0,-39.37+(n-1)*2.54],out['connector_centre_mm'],out['connector_turn_deg']//90);origin=out['origins_mm'][instance]
        return [point[0]+origin[0],point[1]+origin[1]]
    changed_returns=[]
    for index,row in enumerate(out['returns']):
        if 'link'not in row:continue
        point=headers[row['instance'],'M:'+row['link']]['pads_mm'][row['contact']][0]
        if point!=row['middle_header_pad_mm']:changed_returns.append(index)
        row['middle_header_pad_mm']=point
        for corridor in row['middle_return_corridors']:corridor['allocation_mm']=d.segment(point,ground_contact(corridor['to'],row['instance']),config)
    wire=[]
    for prior in assembly['wire_checks']:
        r=copy.deepcopy(prior);inst,link,pin=r['instance'],r['link'],r['pin']
        front=next(p for p in assembly['front_instances'][inst]if p['ref']=='H:'+link);middle=headers[inst,'M:'+link]
        fp=front['pads_mm'][pin][0];mp=middle['pads_mm'][pin][0];z=front['conditional_pcb_depth_mm']
        distance=math.dist(fp+[z],mp+[50]);r['straight_pad_distance_mm']=distance;r['minimum_remaining_slack_mm']=57-distance;r['within_slack_allocation']=57-distance>=10
        wire.append(r)
    a.c.require(len(headers)==85 and len(wire)==270,'transport coverage')
    a.c.require(all(r['within_slack_allocation']for r in wire),'minimum wire service slack')
    a.c.require(len(out['paths'])==225 and len(out['returns'])==240,'path/return coverage')
    out['middle_header_placements_all_instances']=list(headers.values());out['wire_checks']=wire
    out['maximum_mm']=max(r['total_mm']for r in out['paths']);out['minimum_margin_mm']=min(r['margin_mm']for r in out['paths']);out['overlength_count']=sum(r['total_mm']>300 for r in out['paths'])
    out['by_instance']={i:{'maximum_mm':max(r['total_mm']for r in out['paths']if r['instance']==i),'overlength_count':sum(r['total_mm']>300 for r in out['paths']if r['instance']==i)}for i in out['origins_mm']}
    out['tolerance_service']['wire_minimum_slack_mm']=min(r['minimum_remaining_slack_mm']for r in wire)
    return out,{'changed_path_indices':changed,'changed_return_indices':changed_returns,'minimum_wire_slack_mm':min(r['minimum_remaining_slack_mm']for r in wire),'all270_wire_checks_pass':True}

def build():
    files=[a.OUT/'stage4/candidate-report.json',a.OUT/'assembly-report.json',OUT/'header-repair-input.json'];prior,assembly,spec=[json.loads(p.read_text())for p in files]
    candidate,changes=apply_moves(prior['candidate'],assembly,spec)
    sources=files+[Path(__file__),Path(__file__).with_name('test_stage5_rebudget.py')]
    return {'status':'EXPLICIT MIDDLE HEADER REPAIR; SOURCE ONLY; ELECTRICAL/PHYSICAL QUALIFICATION UNKNOWN','source_sha256':a.binding(sources),'candidate':candidate,'repair':spec,'changes':changes,'power_coordinate_scope':'Front/shared/rear sourcepackage pads unchanged fromstage4 baseline_shared_x6 normalizedpowerinventory.85transportheaderpadsets are rebound here; no new powerplacement/impedance claim.','combined_acceptance':'NOT QUALIFIED','native':'NOT RUN','physical':'NOT RUN'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args();r=build();data=json.dumps(r,separators=(',',':'),sort_keys=True)+'\n';path=OUT/'candidate-report.json'
    if args.check:a.c.require(path.read_text()==data,'stale stage5 repair')
    else:path.write_text(data)
    print('rebudget',r['changes'],'max',r['candidate']['maximum_mm'],'strictfail',r['candidate']['overlength_count'])
if __name__=='__main__':main()
