"""New direct-mate outline/cluster/connector study; no native calls or adoption.

This is a bounded geometric allocation experiment. Unknown occupied space is
reserved, so no candidate here can be accepted from path arithmetic alone.
"""
import argparse
import copy
import hashlib
import itertools
import json
import math
from pathlib import Path
import assembly as a
from placement_search import matching

ROOT,OUT=a.ROOT,a.OUT

def bounds(boxes):return [min(b[0] for b in boxes),min(b[1] for b in boxes),max(b[2] for b in boxes),max(b[3] for b in boxes)]

def clusters(source,order,spec):
    result=[];y=spec['cluster_start_y_mm'];summary=[]
    for name in order:
        packages=[p for p in source if p['cluster']==name]
        turn=1 if name=='sine' else 0
        rotated=[a.box_transform(p['reserved_box_mm'],[0,0],turn) for p in packages]
        b=bounds(rotated);translation=[spec['cluster_column_x_mm']-b[0],y-b[1]]
        for p in packages:
            q=copy.deepcopy(p)
            q['origin_mm']=a.transform(p['origin_mm'],translation,turn)
            for key in ('box_mm','reserved_box_mm'):q[key]=a.box_transform(p[key],translation,turn)
            q['pads_mm']={pin:[a.transform(xy,translation,turn) for xy in pts] for pin,pts in p['pads_mm'].items()}
            q['whole_cluster_turn']=turn;q['whole_cluster_translation_mm']=translation
            result.append(q)
        summary.append({'id':name,'box_mm':[spec['cluster_column_x_mm'],y,spec['cluster_column_x_mm']+b[2]-b[0],y+b[3]-b[1]],'turn':turn})
        y+=b[3]-b[1]+spec['cluster_gap_mm']
    return result,summary

def fixtures(spec,cy):
    w,h=spec['card_mm'];cx=spec['connector_centre_x_mm']
    result=[{'id':'DIN','box_mm':[cx-7.5,cy-50,cx+7.5,cy+50]}]
    groups={'support':([[3.5,4],[w-3.5,4],[3.5,h-4],[w-3.5,h-4]],3),
            'guide':([[8,20],[17,209]],2), 'handle':([[14,h-4],[30,h-4]],3),
            'probe':([[5,225.5],[15,225.5],[25,225.5],[35,225.5]],2)}
    for name,(positions,r) in groups.items():
        for i,(x,y) in enumerate(positions):result.append({'id':name+str(i),'box_mm':[x-r,y-r,x+r,y+r]})
    for i,(x,y) in enumerate(((3,198),(22,198),(3,211),(22,211))):result.append({'id':'power'+str(i),'box_mm':[x,y,x+10,y+12]})
    return result

def geometry(packages,fixture,spec,origins):
    w,h=spec['card_mm'];edge=spec['panel_edge_mm'];gap=spec['minimum_pair_clearance_mm']
    objects=[{'id':p['ref'],'box_mm':p['reserved_box_mm']} for p in packages]+fixture
    errors=[]
    for p in objects:
        if not a.inside(p['box_mm'],[0,0,w,h],edge):errors.append('card edge '+p['id'])
    for p,q in itertools.combinations(objects,2):
        if a.c.overlap(p['box_mm'],q['box_mm'],gap-1e-8):errors.append('local collision '+p['id']+'/'+q['id'])
    cards={i:[x,y,x+w,y+h] for i,(x,y) in origins.items()}
    for i,b in cards.items():
        if not a.inside(b,[0,0,318,298],edge):errors.append('panel edge '+i)
    for (i,b),(j,c) in itertools.combinations(cards.items(),2):
        if a.c.overlap(b,c,1-1e-8):errors.append('five-card collision '+i+'/'+j)
    return {'proxy_errors':errors,'five_card_boxes_mm':cards,'other_28_occupied_volume':'UNKNOWN_RESERVED; not qualified free','Z_projections':'UNRESOLVED: see reservation study; fixed depth and service unchanged','accepted':False}

def segment(p,q,config):
    dx,dy=abs(p[0]-q[0]),abs(p[1]-q[1])
    return config['route_factor']*(max(dx,dy)+(math.sqrt(2)-1)*min(dx,dy))+config['route_extra_mm']+2*config['endpoint_tolerance_mm']

def evaluate(rows,packages,origins,cy,turn,spec,config):
    rear={p['ref']:p for p in packages};nets=sorted({r['net'] for r in rows if not r['net'].startswith('OSC_OCT')})
    fixed=[r for r in rows if r['net'].startswith('OSC_OCT')]
    moving=[r for r in rows if not r['net'].startswith('OSC_OCT')]
    def path(r,pin):
        origin=origins[r['instance']];ref,number=r['other_endpoint'].split(':')
        point=rear[ref]['pads_mm'][number][0];rp=[point[0]+origin[0],point[1]+origin[1]]
        contact=a.transform([2.54,-39.37+pin*2.54],[spec['connector_centre_x_mm'],cy],turn)
        dp=[contact[0]+origin[0],contact[1]+origin[1]]
        anchor=r['front_pad_mm'] if r['net'] in ('OSC_REF5','OSC_REFN5','OSC_GATE_REF') else r['middle_header_pad_mm']
        terms={'middle_trace_mm':segment(anchor,dp,config),'DIN_mm':config['DIN_developed_mm'],'rear_trace_mm':segment(dp,rp,config)}
        if 'link' in r:terms.update({k:r['segments'][k] for k in ('front_trace_mm','GH_pair_mm','wire_max_mm')})
        updated=dict(r); updated.pop('nominal_interface_geometric_comparison_mm',None)
        return dict(updated,other_pad_mm=rp,DIN_pad_mm=dp,segments=terms,total_mm=sum(terms.values()),margin_mm=300-sum(terms.values()),pad_separation_lower_bound_mm=math.dist(r['front_pad_mm'],rp))
    precomputed={(n,p):[path(r,p) for r in moving if r['net']==n] for n in nets for p in range(32)}
    costs=[[max(r['total_mm'] for r in precomputed[n,p]) for p in range(32)] for n in nets]
    levels=sorted({v for row in costs for v in row});lo,hi=0,len(levels)-1
    while lo<hi:
        m=(lo+hi)//2
        if matching(costs,levels[m]) is None:lo=m+1
        else:hi=m
    pins=matching(costs,levels[lo]);allrows=copy.deepcopy(fixed)
    for n,p in pins.items():allrows+=precomputed[nets[n],p]
    return {'common_DIN_signal_labels':{nets[n]:'c'+str(p+1) for n,p in pins.items()},'paths':allrows,'maximum_mm':max(r['total_mm'] for r in allrows),'minimum_margin_mm':min(r['margin_mm'] for r in allrows),'overlength_count':sum(r['total_mm']>300 for r in allrows),'direct_separation_over300_count':sum(r['pad_separation_lower_bound_mm']>300 for r in allrows),'by_instance':{i:{'maximum_mm':max(r['total_mm'] for r in allrows if r['instance']==i),'overlength_count':sum(r['total_mm']>300 for r in allrows if r['instance']==i)} for i in origins}}

def identity(r):
    return (r['instance'],r['net'],r['front_endpoint'],r['other_endpoint'],r.get('link'),r.get('link_pin'))

def complete_best(best,source,audit,config):
    original=source['alternatives']['five_card_two_rows']
    a.c.require(len(best['paths'])==225 and sorted(map(identity,best['paths']))==sorted(map(identity,original['paths'])),'complete crossing endpoint coverage')
    pinmap=best['common_DIN_signal_labels']
    a.c.require(len(pinmap)==26 and len(set(pinmap.values()))==26,'common injective26 signal map')
    a.c.require(all(label in {'c'+str(i) for i in range(1,33)} for label in pinmap.values()),'physical contact labels')
    indexed={(r['instance'],r['template_net'],r['template_front_endpoint'],r['template_other_endpoint'],r.get('link'),r.get('link_pin')):r for r in audit['audited_paths'] if r['alternative']=='five_card_two_rows'}
    for row in best['paths']:
        actual=indexed[identity(row)]
        row['actual_identity']={k:actual[k] for k in ('actual_net','actual_panel_uid','front','other','canonical_source_nodes')}
        row['length_limit_mm']=300;row['capacitance_limit_pF']=1000
        a.c.require(math.isclose(sum(row['segments'].values()),row['total_mm'],abs_tol=1e-8),'path decomposition')
    best['shared_aggregate_capacitance']=audit['shared_aggregate_capacitance']
    rear={p['ref']:p for p in best['packages']};links={h['id']:h for h in json.loads((OUT/'candidate-report.json').read_text())['front_links']}
    turn=best['connector_turn_deg']//90
    def contact(label,instance):
        point=a.transform([0,-39.37+(int(label[1:])-1)*2.54],best['connector_centre_mm'],turn)
        origin=best['origins_mm'][instance]
        return [point[0]+origin[0],point[1]+origin[1]]
    returns=[]
    for previous in original['returns']:
        row=copy.deepcopy(previous);instance=row['instance'];origin=best['origins_mm'][instance]
        if 'link' in row:
            row['middle_return_corridors']=[{'to':'DIN:b'+pinmap[n][1:],'allocation_mm':segment(row['middle_header_pad_mm'],contact('b'+pinmap[n][1:],instance),config)} for n in links[row['link']]['pins'].values() if n in pinmap]
        else:
            oldlabel=row['from'].split(':')[1]
            net=next(n for n,label in original['DIN_signal_labels'].items() if label[1:]==oldlabel[1:])
            label='b'+pinmap[net][1:];row['from']='DIN:'+label;point=contact(label,instance)
            row['rear_branch_allocations_mm']={}
            for endpoint in row['endpoint_ids']:
                ref,pin=endpoint.split(':');xy=rear[ref]['pads_mm'][pin][0]
                row['rear_branch_allocations_mm'][endpoint]=segment(point,[xy[0]+origin[0],xy[1]+origin[1]],config)
        row['status']='new geometric branch allocations only; common source/plane/via/current sharing/impedance OPEN'
        returns.append(row)
    best['returns']=returns
    best['power_distribution']=source['supply_graph']
    best['power_distribution_coordinate_frame']='retained compact source inventory; any stored XY is NOT new-card geometry; new rail topology/extraction OPEN'
    best['power_distribution_status']='complete source/common/branch/load/return inventory retained; new rail/support corridor topology and impedance NOT EXTRACTED; not qualified'
    best['connector_population_per_card']={'mating_positions':96,'signals':26,'adjacent_AGND':26,'NC':44,'solder_joints_both_halves':192}
    best['tolerance_service']={'endpoint_tolerance_mm':config['endpoint_tolerance_mm'],'wire_minimum_slack_mm':source['wire_minimum_slack_mm'],'required_service_slack_mm':10,'withdrawal_mm':40,'external_workspace_mm':100,'status':'positive front-wire reservation retained; rear mechanical service clearance UNKNOWN_RESERVED'}


def build():
    spec=json.loads((OUT/'direct-study.json').read_text());source=json.loads((OUT/'assembly-report.json').read_text());config=source['config']
    a.c.require(spec['other_functions_space_status']=='UNKNOWN_RESERVED; no qualified free volume','unknown space must remain reserved')
    a.c.require((spec['middle_depth_mm'],spec['core_depth_mm'],spec['cover_depth_mm'],spec['withdrawal_mm'],spec['external_workspace_mm'])==(50,69.2,105,40,100),'depth/service baseline changed')
    a.c.require(spec['minimum_pair_clearance_mm']>=.5 and spec['card_gap_mm']>=2 and spec['panel_edge_mm']>=.5,'geometry allowance weakened')
    refined=json.loads((OUT/'cluster-refinement-report.json').read_text())
    a.c.require(all(config[k]==v for k,v in {'route_factor':1.15,'route_extra_mm':5,'endpoint_tolerance_mm':1,'DIN_developed_mm':25,'GH_pair_developed_mm':15,'wire_nominal_mm':60,'wire_cut_tolerance_mm':3}.items()),'unchanged path allowances')
    rows=source['alternatives']['five_card_two_rows']['paths'];cases=[];best=None;best_by_variant={}
    expected={p['ref'] for p in source['rear_placements']}
    a.c.require(set(spec['connector_turns']) <= {0,2},'vertical DIN body only supports0/180 study')
    for variant,order,y,cy,turn in itertools.product(('baseline','bypass_refined'),spec['orders'],spec['origins_y_mm'],spec['connector_centres_y_mm'],spec['connector_turns']):
        a.c.require(sorted(order)==sorted(a.c.REQUIRED_CLUSTERS),'whole cluster coverage')
        packages,summary=clusters(refined['placements'] if variant=='bypass_refined' else source['rear_placements'],order,spec)
        a.c.require({p['ref'] for p in packages}==expected and len(packages)==154,'package coverage')
        a.c.require(sum(p['trim_tool_diameter_mm']==6 for p in packages)==6,'six rear trim axes')
        origins={f'O{i+1}':[2+i*(spec['card_mm'][0]+spec['card_gap_mm']),y] for i in range(5)}
        fixed=fixtures(spec,cy);screen=geometry(packages,fixed,spec,origins)
        label={'placement_variant':variant,'order':order,'origin_y_mm':y,'connector_centre_mm':[spec['connector_centre_x_mm'],cy],'connector_turn_deg':turn*90,'geometry':screen}
        if screen['proxy_errors']:cases.append(dict(label,status='geometry proxy rejected'));continue
        result=evaluate(rows,packages,origins,cy,turn,spec,config)
        cases.append(dict(label,status='allocation tested; physical RESERVED',**{k:v for k,v in result.items() if k not in ('paths','common_DIN_signal_labels')}))
        if variant not in best_by_variant or result['maximum_mm']<best_by_variant[variant]['maximum_mm']:
            best_by_variant[variant]=dict(label,origins_mm=origins,packages=packages,clusters=summary,fixtures=fixed,**result)
        if best is None or result['maximum_mm']<best['maximum_mm']:
            best=dict(label,origins_mm=origins,packages=packages,clusters=summary,fixtures=fixed,**result)
    for variant_best in best_by_variant.values():complete_best(variant_best,source,json.loads((OUT/'stage3-crossing-audit.json').read_text()),config)
    if best:best=best_by_variant[best['placement_variant']]
    paths=[Path(__file__),Path(a.__file__),ROOT/'scripts/architecture278/implementation/placement_search.py',OUT/'direct-study.json',Path(__file__).with_name('test_direct_study.py'),OUT/'candidate-report.json',OUT/'assembly-report.json',OUT/'cluster-refinement-report.json',OUT/'stage3-crossing-audit.json',OUT/'stage3/reservations-report.json']
    return {'status':'BOUNDED NEW DIRECT-MATE STUDY; NOT ADOPTED; Stage1 OPEN','source_sha256':a.binding(paths),'spec':spec,'case_count':len(cases),'tested_count':sum(c['status'].startswith('allocation') for c in cases),'cases':cases,'best':best,'best_by_variant':best_by_variant,'locality_tradeoffs':'bypass_refined improves rail-pad proxy but increases several timing/waveform/reference spans; full before/after cluster-refinement-report retained; neither variant adopted','capacitance':{'per_path_pF':None,'limit_pF':1000,'octave_direct_load_limit_pF':1000,'octave_scope':'aggregate five branches; actual segment union and parasitics not extracted; five1k/100nFreceiver dynamics retained separately'},'power_return':'all inherited graph/limits retained in assembly-report; no impedance/capacitance claim; new physical corridors require extraction','core_only_reuse_comparison':'retained source comparison only; no automatic adoption','native':'NOT RUN'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args();r=build();out=OUT/'direct-study-report.json';data=json.dumps(r,indent=2,sort_keys=True)+'\n'
    if args.check:a.c.require(out.read_text()==data,'stale direct study')
    else:out.write_text(data)
    print('direct study',r['case_count'],'cases',r['tested_count'],'geometry proxies tested','best',None if r['best'] is None else r['best']['maximum_mm'],'Stage1 OPEN; unknown volume RESERVED')
if __name__=='__main__':main()
