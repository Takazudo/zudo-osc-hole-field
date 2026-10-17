"""Actual-pad candidate placement and conservative path study; never invokes KiCad.

Reports failed bounds as findings, not generator failures. A source PASS means only
reproducibility/invariants; no copper route, impedance, solids or fit is certified.
"""
import argparse
from collections import Counter
import copy
import hashlib
import itertools
import json
import math
from pathlib import Path
import candidate as c

ROOT,OUT=c.ROOT,c.OUT

def transform(xy,origin,turn=0):
    x,y=xy
    for _ in range(turn%4):x,y=-y,x
    return [x+origin[0],y+origin[1]]

def box_transform(box,origin,turn=0):
    pts=[transform(p,origin,turn) for p in itertools.product((box[0],box[2]),(box[1],box[3]))]
    return [min(p[0] for p in pts),min(p[1] for p in pts),max(p[0] for p in pts),max(p[1] for p in pts)]

def inside(box,bounds,gap=0):return bounds[0]+gap<=box[0] and bounds[1]+gap<=box[1] and box[2]<=bounds[2]-gap and box[3]<=bounds[3]-gap

def distance(a,b):return sum(abs(x-y) for x,y in zip(a,b))

def shape(ref,package):
    path='footprints/kicad/zudo-osc-hole-field.pretty/'+package['footprint'].split(':')[1]+'.kicad_mod'
    pads=c.footprint_pads(path)
    c.require(set(pads)==set(package['pins']),'actual pad equality '+ref)
    holes=[]
    for n in c.sexpr((ROOT/path).read_text()):
        if isinstance(n,list) and n[0]=='pad' and n[2] in ('thru_hole','np_thru_hole'):
            x,y=map(float,c.field(n,'at')[:2]);w,h=map(float,c.field(n,'size')[:2]);holes.append([x-w/2,y-h/2,x+w/2,y+h/2])
    return {'ref':ref,'owner':package['owner'],'box':c.courtyard(path),'pads':pads,'pins':package['pins'],'holes':holes,'source':path,'units':package['units']}

def header(link):
    n=len(link['pins']);a=(n-1)*1.25
    c.require(n in (2,3,4,7),'unsupported GH size')
    # Exact retained JST eGH drawing: see front-identity-evidence report.
    return {'ref':'H:'+link['id'],'owner':'header','box':[-a/2-2.6,-1.1,a/2+2.6,5],
        'pads':{**{str(i):[[a/2-(i-1)*1.25,0]] for i in range(1,n+1)},'MP1':[[-a/2-1.85,3.35]],'MP2':[[a/2+1.85,3.35]]},
        'pins':dict(link['pins'],MP1=None,MP2=None),'holes':[],'source':'design/connectors/sources/jst-gh.pdf','units':[],
        'header_mpn':f'BM{n:02}B-GHS-TBT(LF)(SN)','housing_mpn':f'GHR-{n:02}V-S','contact_mpn':'SSHL-002T-P0.2'}

def located(s,origin,turn=0,board='jack',side='rear'):
    return {'ref':s['ref'],'owner':s['owner'],'origin_mm':origin,'quarter_turn':turn,'board':board,'side':side,
        'box_mm':box_transform(s['box'],origin,turn),'pads_mm':{p:[transform(xy,origin,turn) for xy in coords] for p,coords in s['pads'].items()},
        'pins':s['pins'],'units':s['units'],'source':s['source'],'through_pad_keepouts_mm':[box_transform(b,origin,turn) for b in s['holes']],
        **{k:s[k] for k in ('header_mpn','housing_mpn','contact_mpn') if k in s}}

def face_shape(s,side):
    q=copy.deepcopy(s)
    if side=='rear':
        a,b,x,y=q['box'];q['box']=[-x,b,-a,y]
        q['pads']={p:[[-x,y] for x,y in coords] for p,coords in q['pads'].items()}
        q['holes']=[[-x,b,-a,y] for a,b,x,y in q['holes']]
    return q

def pack(shapes,bounds,obstacles,targets,board,dense=False,side='rear'):
    placed=[]
    # Place largest packages first; all units/pins remain one physical package.
    for original in sorted(shapes,key=lambda s:((targets[s['ref']][1] if dense else 0),-(s['box'][2]-s['box'][0])*(s['box'][3]-s['box'][1]),s['ref'])):
        s=face_shape(original,side)
        best=None
        for turn in (0,1,2,3):
            b=box_transform(s['box'],[0,0],turn)
            for xi in range(math.ceil((bounds[0]-b[0])*2),math.floor((bounds[2]-b[2])*2)+1):
                for yi in range(math.ceil((bounds[1]-b[1])*2),math.floor((bounds[3]-b[3])*2)+1):
                    origin=[xi/2,yi/2];box=box_transform(s['box'],origin,turn)
                    if any(c.overlap(box,o,.5) for o in obstacles+[p['box_mm'] for p in placed]):continue
                    cost=(box[1]*1000+box[0] if dense else distance(origin,targets[s['ref']]));key=(cost,turn,xi,yi)
                    if best is None or key<best[0]:best=(key,origin,turn)
        c.require(best is not None,'front/shared capacity '+s['ref'])
        placed.append(located(s,best[1],best[2],board,side))
    return placed

def locked_hardware(lock):
    names={'jack':'Jack_3.5mm_QingPu_WQP518MA','pot':'PTV09A-4020F','switch':'Toggle_Dailywell_2MS_T1B1M2','button':'Button_Omron_B3F_6x6_P6.5x4.5','octave':'SRBV160803'}
    result=[]
    for p in lock:
        name=('LED0402-Kingbright-Red' if p['led_type']=='clip' else 'LED0402-Kingbright-White') if p['kind']=='led' else names[p['kind']]
        path='footprints/kicad/zudo-osc-hole-field.pretty/'+name+'.kicad_mod'
        pads=c.footprint_pads(path)
        dummy={'footprint':'zudo-osc-hole-field:'+name,'pins':dict.fromkeys(pads),'owner':'locked-panel','units':[]}
        q=located(shape(p['ref'],dummy),[p['x_mm'],p['y_mm']],p['rot_deg']//90,'locked','panel')
        q['uid']=p['uid'];q['conditional_pcb_depth_mm']=-p.get('assembly_pcb_z_mm',-20);result.append(q)
    return result

def front_instance(front,instance,lock):
    dx=17*(int(instance[1:])-1);result=[]
    for p in front:
        q=copy.deepcopy(p);selector=p['board']=='selector'
        datum=next(h for h in lock if h['uid']=='C:'+instance+'.OCT') if selector else None
        turns=(datum['rot_deg']//90) if selector else 0
        def point(xy):
            if selector:return transform([xy[0]-14.5,xy[1]-185],[datum['x_mm'],datum['y_mm']],turns)
            return [xy[0]+dx,xy[1]]
        q['origin_mm']=point(p['origin_mm']);q['quarter_turn']=(p['quarter_turn']+turns)%4
        pts=[point(x) for x in itertools.product((p['box_mm'][0],p['box_mm'][2]),(p['box_mm'][1],p['box_mm'][3]))]
        q['box_mm']=[min(x for x,y in pts),min(y for x,y in pts),max(x for x,y in pts),max(y for x,y in pts)]
        q['pads_mm']={pin:[point(xy) for xy in coords] for pin,coords in p['pads_mm'].items()}
        q['through_pad_keepouts_mm']=[]
        for b in p['through_pad_keepouts_mm']:
            pts=[point(x) for x in itertools.product((b[0],b[2]),(b[1],b[3]))]
            q['through_pad_keepouts_mm'].append([min(x for x,y in pts),min(y for x,y in pts),max(x for x,y in pts),max(y for x,y in pts)])
        if 'uid' in q:q['uid']=q['uid'].replace('O1',instance)
        q['conditional_pcb_depth_mm']=-datum['assembly_pcb_z_mm'] if selector else p.get('conditional_pcb_depth_mm',20)
        q['instance']=instance;result.append(q)
    return result

def front_population(ps,links,lock):
    panel=[];shapes=[]
    for r,p in ps.items():
        if p['owner'] not in ('front-jack','front-control','octave-selector'):continue
        s=shape(r,p)
        uid=p['attributes'].get('PanelUid')
        if uid:
            datum=next(x for x in lock if x['uid']==uid)
            q=located(s,[datum['x_mm'],datum['y_mm']],datum['rot_deg']//90,'jack' if p['owner']=='front-jack' else ('selector' if r=='SW101' else 'control'),'panel')
            q['uid']=uid;q['conditional_pcb_depth_mm']=-datum.get('assembly_pcb_z_mm',-20)
            panel.append(q)
        else:shapes.append(s)
    bypanel={p['ref']:p for p in panel}
    targets={}
    # Source topology determines targets, not annotation display names.
    for s in shapes:
        connected=[p['origin_mm'] for p in panel if any(n and n!='AGND' and n in p['pins'].values() for n in s['pins'].values())]
        role=ps[s['ref']]['attributes'].get('Role','')
        if not connected:
            units=[u for u in c.read('interface-contract.json')['parts'] if u['ref']==s['ref']]
            keys=' '.join(u.get('key','')+' '+u['attributes'].get('LogicalCellKey','') for u in units)
            ys=[y for tag,y in [('1V__',29),('FM__',43),('PWM__',57),('SYNC__',71),('SIN__',85),('TRI__',99),('SAW__',113),('PUL__',127)] if tag in keys]
            connected=[[23,y] for y in ys] or [[23,78]]
        targets[s['ref']]=[23,sum(p[1] for p in connected)/len(connected)]
    for link in links:
        s=header(link);shapes.append(s)
        datum=next(x for x in lock if x['uid']==link['uid'])
        targets[s['ref']]=[23,datum['y_mm']]
    jack=[s for s in shapes if s['owner']!='header' or next(h for h in links if 'H:'+h['id']==s['ref'])['uid'].startswith('J:')]
    # Common front jack PCB can span oscillator columns; SMDs occupy the rear
    # face between THT pad columns. Through pads block both faces.
    obstacles=[b for p in panel if p['board']=='jack' for b in p['through_pad_keepouts_mm']]
    # Include next oscillator's through pads in the shared-board strip.
    obstacles += [[b[0]+17,b[1],b[2]+17,b[3]] for b in list(obstacles)]
    small=[s for s in jack if s['owner']!='header' and not s['ref'].startswith('U')]
    rear_shapes=[s for s in jack if s not in small]
    packed=pack(rear_shapes,[16,20,30,136],obstacles,targets,'jack',dense=True)
    body_obstacles=[p['box_mm'] for p in panel if p['board']=='jack']
    body_obstacles += [[b[0]+17,b[1],b[2]+17,b[3]] for b in list(body_obstacles)]
    keyrefs={u['key'].split('.')[0]:u['ref'] for u in c.read('interface-contract.json')['parts'] if u['instance']=='O1'}
    located_ics={p['ref']:p for p in packed}
    for s in small:
        target=ps[s['ref']]['attributes'].get('Decouples')
        if target:
            ic=located_ics[keyrefs[target]];targets[s['ref']]=ic['origin_mm']
    small_placed=[]
    for s in sorted(small,key=lambda s:(not bool(ps[s['ref']]['attributes'].get('Decouples')),-(s['box'][2]-s['box'][0])*(s['box'][3]-s['box'][1]),s['ref'])):
        options=[]
        for side,bounds,obs in [('rear',[16,20,30,136],obstacles),('panel',[19.75,20,26.25,136],body_obstacles)]:
            occupied=obs+[p['box_mm'] for p in packed+small_placed if p['side']==side]
            try:q=pack([s],bounds,occupied,targets,'jack',side=side)[0]
            except ValueError:continue
            q['side']=side;options.append(q)
        c.require(options,'two-face capacity '+s['ref'])
        small_placed.append(min(options,key=lambda q:distance(q['origin_mm'],targets[s['ref']])))
    packed+=small_placed
    control=[s for s in shapes if s not in jack]
    # Selector has its own retained staggered plane; control headers stay on
    # the rear face, with exact pot/switch THT pads blocking their placement.
    all_hardware=locked_hardware(lock)
    for s in control:
        link=next(h for h in links if 'H:'+h['id']==s['ref'])
        selector=link['uid'].endswith('.OCT')
        same=[p for p in panel if p['board']==('selector' if selector else 'control')]
        obs=[b for p in same for b in p['through_pad_keepouts_mm']]
        if not selector:
            obs=[[b[0]-dx,b[1],b[2]-dx,b[3]] for dx in (0,17,34,51,68) for h in all_hardware if h['conditional_pcb_depth_mm']==20 for b in h['through_pad_keepouts_mm']]
        obs += [p['box_mm'] for p in packed if p['board']==('selector' if selector else 'control')]
        y=next(x['y_mm'] for x in lock if x['uid']==link['uid'])
        bounds=[5,170,30,198] if selector else [6,y-9,23,min(296,y+12)]
        packed+=pack([s],bounds,obs,targets,'selector' if selector else 'control')
    placed=panel+packed
    c.require(Counter(p['ref'] for p in placed if p['owner']!='header')==Counter(r for r,p in ps.items() if p['owner'] in ('front-jack','front-control','octave-selector')),'front coverage')
    return placed

SHARED_BYPASS={'C1601':'U1601','C1603':'U1601','C1604':'U1602','C1605':'U1602','C1606':'U1603','C1607':'U1603','C1608':'U1604','C1609':'U1604'}

def shared_population(ps,config):
    shapes=[shape(r,p) for r,p in ps.items() if p['owner']=='shared-reference']
    b=config['shared_box_mm'];targets={s['ref']:[(b[0]+b[2])/2,(b[1]+b[3])/2] for s in shapes}
    ics=[s for s in shapes if s['ref'].startswith('U')]
    placed=pack(ics,b,[],targets,'middle-reference')
    for s in sorted([s for s in shapes if s not in ics],key=lambda s:(s['ref'] not in SHARED_BYPASS,s['ref'])):
        if s['ref'] in SHARED_BYPASS:targets[s['ref']]=next(p['origin_mm'] for p in placed if p['ref']==SHARED_BYPASS[s['ref']])
        else:
            nets=set(s['pins'].values())-{'AGND','+12V','-12V','+5V',None}
            adjacent=[p['origin_mm'] for p in placed if p['ref'].startswith('U') and nets.intersection(p['pins'].values())]
            if adjacent:targets[s['ref']]=[sum(x[i] for x in adjacent)/len(adjacent) for i in (0,1)]
        placed+=pack([s],b,[p['box_mm'] for p in placed],targets,'middle-reference')
    return placed

def endpoint_inventory(ps,placed):
    result=[]
    for ref,p in ps.items():
        physical=bool(p['footprint'])
        c.require(not physical or ref in placed,'missing placed package '+ref)
        if physical:c.require(set(placed[ref]['pads_mm'])==set(p['pins']),'placed pad coverage '+ref)
        for pin,net in p['pins'].items():
            result.append({'ref':ref,'pin':pin,'net':net,'owner':p['owner'],'physical':physical,'xy_mm':placed[ref]['pads_mm'][pin] if physical else None})
    return result

def validate_inventory(inventory,contract):
    expected=Counter((u['ref'],p,n,u['proposed_owner']) for u in contract['parts'] for p,n in u['pins'].items())
    actual=Counter((e['ref'],e['pin'],e['net'],e['owner']) for e in inventory)
    c.require(actual==expected,'complete endpoint/return/NC coverage')

def binding(paths):return {str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(paths))}

def build(config=None):
    config=copy.deepcopy(config if config is not None else c.read('implementation/assembly.json'))
    # finite() excludes booleans; candidate_only is a status flag, not geometry.
    c.finite({k:v for k,v in config.items() if k!='candidate_only'})
    for key,minimum in [('route_factor',1.15),('route_extra_mm',5),('endpoint_tolerance_mm',1),('wire_nominal_mm',60),('wire_cut_tolerance_mm',3),('minimum_service_slack_mm',10),('GH_pair_developed_mm',15),('DIN_developed_mm',25)]:c.require(config[key]>=minimum,'weakened '+key)
    ps=c.packages(c.read('interface-contract.json'));contract=c.read('interface-contract.json')
    baseline=c.read('implementation/candidate-report.json');compact=c.read('implementation/compact-rear.json')
    physical={r:p for r,p in ps.items() if p['owner']=='rear-core' and p['footprint']}
    compact_report,_=c.build(compact);rear=compact_report['rear_placements']
    lock=json.loads((ROOT/'design/grid/placements.lock.json').read_text())['placements'];links=baseline['front_links']
    front=front_population(ps,links,lock);shared=shared_population(ps,config)
    instances={f'O{i}':front_instance(front,f'O{i}',lock) for i in range(1,6)}
    instanceby={i:{p['ref']:p for p in pp} for i,pp in instances.items()}
    frontby={p['ref']:p for p in front};rearby={p['ref']:p for p in rear};sharedby={p['ref']:p for p in shared}
    inventory=endpoint_inventory(ps,{**frontby,**sharedby,**rearby});validate_inventory(inventory,contract)
    local_nets={n:{owner:[e for e in inventory if e['net']==n and e['owner']==owner] for owner in sorted({e['owner'] for e in inventory if e['net']==n})} for n in sorted({e['net'] for e in inventory if e['net'] is not None})}
    bypass=[]
    for u in contract['parts']:
        key=u['attributes'].get('Decouples')
        if not key:continue
        targets={v['ref'] for v in contract['parts'] if v['instance']==u['instance'] and v['key'].split('.')[0]==key}
        c.require(len(targets)==1,'ambiguous bypass target')
        target=targets.pop();locations={**frontby,**sharedby,**rearby}
        a0=locations[u['ref']]['origin_mm'];b0=locations[target]['origin_mm']
        bypass.append({'capacitor':u['ref'],'package':target,'owner':u['proposed_owner'],'origin_distance_mm':math.dist(a0,b0),'status':'pad/loop/via/plane qualification OPEN; full association conserved'})
    for cap,target in SHARED_BYPASS.items():
        bypass.append({'capacitor':cap,'package':target,'owner':'shared-reference','origin_distance_mm':math.dist(sharedby[cap]['origin_mm'],sharedby[target]['origin_mm']),'association_basis':'retained C_DEC source key / REF5050 C_IN supply connection; no inferred new component','status':'source association; pad/loop/via/plane qualification OPEN'})
    shared_drivers={'OSC_REF5':'U1602:1','OSC_REFN5':'U1602:7','OSC_GATE_REF':'U1602:8','OSC_OCT0':'U1602:14','OSC_OCT1':'U1603:1','OSC_OCT2':'U1603:7','OSC_OCT3':'U1603:8','OSC_OCT4':'U1603:14','OSC_OCT5':'U1604:1'}
    for net,endpoint in shared_drivers.items():
        ref,pin=endpoint.split(':');c.require(sharedby[ref]['pins'][pin]==net,'missing shared source')
    # Both GH PCB faces carry the same electrical number at identical XY; their
    # local poses are separately recorded. Mating cable pin reversal is not guessed.
    middle=[]
    for p in front:
        if p['owner']=='header':
            link=next(h for h in links if 'H:'+h['id']==p['ref'])
            datum=next(x for x in lock if x['uid']==link['uid'])
            yy=(170 if link['id']=='K-O1-1' else 185) if link['uid'].endswith('.OCT') else datum['y_mm']-1.95
            q=located(header(link),[27,yy],0,'middle','panel');q['ref']='M:'+p['ref'][2:];middle.append(q)
    middleby={p['ref']:p for p in middle}
    nets={n['net']:n for n in contract['nets']};factor=config['route_factor'];extra=config['route_extra_mm'];tol=2*config['endpoint_tolerance_mm']
    def segment(a,b):
        dx,dy=abs(a[0]-b[0]),abs(a[1]-b[1])
        return factor*(max(dx,dy)+(math.sqrt(2)-1)*min(dx,dy))+extra+tol
    def shifted(p,dx):return [p[0]+dx,p[1]]
    active_connector=compact['connector']
    def dp(pin,origin):return [origin[0]+active_connector['centre_mm'][0]+('abc'.index(pin[0])-1)*2.54,origin[1]+active_connector['centre_mm'][1]-39.37+(int(pin[1:])-1)*2.54]
    def endpoints(net,owner,by):
        return [(e['ref']+':'+e['pin'],xy) for e in nets[net]['endpoints'] if e['owner'] in owner and e['ref'] in by for xy in by[e['ref']]['pads_mm'][e['pin']]]
    def rows_for(origins,pinmap):
        rows=[];returns=[]
        for instance,origin in origins.items():
            dx=17*(int(instance[1:])-1)
            for link in links:
                fh=instanceby[instance]['H:'+link['id']];mh=middleby['M:'+link['id']]
                for pin,net in link['pins'].items():
                    if net=='AGND':continue
                    fe=endpoints(net,('front-jack','front-control','octave-selector'),frontby)
                    if link['uid'].startswith('C:'):
                        panel_ref=next(p['ref'] for p in front if p.get('uid')==link['uid'])
                        fe=[e for e in fe if e[0].split(':')[0]==panel_ref]
                    direction=nets[net].get('source_crossing',{}).get('direction',{})
                    drivers=direction.get('source_nodes',[]) if isinstance(direction,dict) else []
                    source_ids={d['ref']+':'+d['pin'] for d in drivers}
                    fe_sources=[e for e in fe if e[0] in source_ids]
                    if fe_sources:fe=fe_sources
                    c.require(fe,'missing physical front endpoint '+net)
                    hp=fh['pads_mm'][pin][0];mp=shifted(mh['pads_mm'][pin][0],dx)
                    if net.startswith('OSC_OCT'):
                        targets=endpoints(net,('shared-reference',),sharedby)
                        targets=[e for e in targets if e[0] in source_ids];din=None
                    else:
                        targets=endpoints(net,('rear-core',),rearby)
                        source_targets=[e for e in targets if e[0] in source_ids]
                        if source_targets:targets=source_targets
                        din=dp(pinmap[net],origin)
                    c.require(targets,'missing physical destination/source '+net)
                    for fref,fp0 in fe:
                        for rref,rp0 in targets:
                            fr,pp=fref.split(':');fp=instanceby[instance][fr]['pads_mm'][pp][0];rp=rp0 if din is None else [rp0[0]+origin[0],rp0[1]+origin[1]]
                            front_trace=segment(fp,hp)
                            middle_trace=segment(mp,rp if din is None else din)
                            rear_trace=0 if din is None else segment(din,rp)
                            parts={'front_trace_mm':front_trace,'GH_pair_mm':config['GH_pair_developed_mm'],'wire_max_mm':config['wire_nominal_mm']+config['wire_cut_tolerance_mm'],'middle_trace_mm':middle_trace,'DIN_mm':0 if din is None else config['DIN_developed_mm'],'rear_trace_mm':rear_trace}
                            direct=math.dist(fp,rp)+config['wire_nominal_mm']+config['GH_pair_developed_mm']+(0 if din is None else config['DIN_developed_mm'])
                            rows.append({'instance':instance,'link':link['id'],'link_pin':pin,'net':net,'front_endpoint':fref,'other_endpoint':rref,'front_pad_mm':fp,'other_pad_mm':rp,'front_header_pad_mm':hp,'middle_header_pad_mm':mp,'DIN_pad_mm':din,'segments':parts,'total_mm':sum(parts.values()),'margin_mm':300-sum(parts.values()),'nominal_interface_geometric_comparison_mm':direct,'pad_separation_lower_bound_mm':math.dist(fp,rp),'capacitance_pF':None})
                    # Every retained return contact is enumerated separately, not
                    # collapsed into a single equal-sharing assumption.
                for gp,gn in link['pins'].items():
                    if gn!='AGND':continue
                    owner=('front-jack',) if link['uid'].startswith('J:') else ('octave-selector',) if link['uid'].endswith('.OCT') else ('front-control',)
                    ground=endpoints('AGND',owner,frontby)
                    hp=fh['pads_mm'][gp][0];mp=shifted(mh['pads_mm'][gp][0],dx)
                    branches=[(ref,segment(instanceby[instance][ref.split(':')[0]]['pads_mm'][ref.split(':')[1]][0],hp)) for ref,xy in ground]
                    returns.append({'instance':instance,'link':link['id'],'contact':gp,'ground_endpoint_group':list(owner),'endpoint_ids':[ref for ref,_ in branches],'front_branch_allocations_mm':dict(branches),'front_header_pad_mm':hp,'middle_header_pad_mm':mp,'harness_max_mm':config['wire_nominal_mm']+config['wire_cut_tolerance_mm']+config['GH_pair_developed_mm'],'resistance_mOhm':None,'middle_return_corridors':[{'to':'DIN:b'+pinmap[n][1:],'allocation_mm':segment(mp,dp('b'+pinmap[n][1:],origin))} for n in link['pins'].values() if n in pinmap],'status':'parallel network candidates; exact ground topology/impedance OPEN'})
            for net,pin in pinmap.items():
                if net in ('OSC_REF5','OSC_REFN5','OSC_GATE_REF'):
                    for fref,fp in endpoints(net,('shared-reference',),sharedby):
                        if fref!={'OSC_REF5':'U1602:1','OSC_REFN5':'U1602:7','OSC_GATE_REF':'U1602:8'}[net]:continue
                        for rref,rp0 in endpoints(net,('rear-core',),rearby):
                            rp=[rp0[0]+origin[0],rp0[1]+origin[1]];din=dp(pin,origin)
                            parts={'middle_trace_mm':segment(fp,din),'DIN_mm':config['DIN_developed_mm'],'rear_trace_mm':segment(din,rp)}
                            rows.append({'instance':instance,'net':net,'front_endpoint':fref,'other_endpoint':rref,'front_pad_mm':fp,'other_pad_mm':rp,'DIN_pad_mm':din,'segments':parts,'total_mm':sum(parts.values()),'margin_mm':300-sum(parts.values()),'pad_separation_lower_bound_mm':math.dist(fp,rp),'capacitance_pF':None})
                gp='b'+pin[1:];gxy=dp(gp,origin)
                ground=endpoints('AGND',('rear-core',),rearby)
                returns.append({'instance':instance,'from':'DIN:'+gp,'ground_endpoint_group':'rear-core','endpoint_ids':[ref for ref,_ in ground],'rear_branch_allocations_mm':{ref:segment(gxy,[xy[0]+origin[0],xy[1]+origin[1]]) for ref,xy in ground},'DIN_max_mm':config['DIN_developed_mm'],'resistance_mOhm':None,'status':'parallel network candidates; common plane/source return OPEN'})
        expected={(i,h['id'],p,n) for i in origins for h in links for p,n in h['pins'].items() if n!='AGND'}
        actual={(r['instance'],r['link'],r['link_pin'],r['net']) for r in rows if 'link' in r}
        c.require(expected==actual,'crossing branch omission')
        return rows,returns
    oldpin={p['net']:p['pin'] for p in baseline['rear_connector_pinout'] if p['net'] and p['net']!='AGND'}
    # Costs include every endpoint and the nine formerly unmodeled shared nets.
    # Use the same bijection for all populated instances of an alternative.
    def optimize(origins):
        costs={n:{} for n in oldpin}
        for slot in ['c'+str(i) for i in range(1,33)]:
            trial={n:slot for n in oldpin};rows,_=rows_for(origins,trial)
            for net in costs:costs[net][slot]=max(r['total_mm'] for r in rows if r['net']==net)
        def match(t):
            used={}
            def visit(n,seen):
                for p,v in sorted(costs[n].items(),key=lambda z:(z[1],z[0])):
                    if v>t or p in seen:continue
                    seen.add(p)
                    if p not in used or visit(used[p],seen):used[p]=n;return True
                return False
            return used if all(visit(n,set()) for n in sorted(costs,key=lambda n:sum(v<=t for v in costs[n].values()))) else None
        values=sorted(set(v for d in costs.values() for v in d.values()));lo,hi=0,len(values)-1
        while lo<hi:
            mid=(lo+hi)//2
            if match(values[mid]) is None:lo=mid+1
            else:hi=mid
        selected={n:p for p,n in match(values[lo]).items()};rows,returns=rows_for(origins,selected)
        return selected,rows,returns
    alternatives={}
    for name,origins in config['rear_alternatives'].items():
        rearby={p['ref']:p for p in (baseline['rear_placements'] if name=='retained_150_recomputed' else rear)}
        active_connector=baseline['config']['connector'] if name=='retained_150_recomputed' else compact['connector']
        pins,rows,returns=optimize(origins)
        alternatives[name]={'origins_mm':origins,'DIN_signal_labels':pins,'paths':rows,'returns':returns,'maximum_mm':max(r['total_mm'] for r in rows),'minimum_margin_mm':min(r['margin_mm'] for r in rows),'overlength_endpoint_paths':sum(r['total_mm']>300 for r in rows),'geometrically_impossible_endpoint_pairs':sum(r.get('pad_separation_lower_bound_mm',0)>300 for r in rows),'status':'BOUND EVALUATION ONLY; actual routing/returns/fit OPEN'}
    # Rails and grounds retain every physical pin as a distinct node. Unknown
    # distribution/joint/source impedances remain null and block acceptance.
    rearby={p['ref']:p for p in rear}
    supply={}
    for net in ('+12V','-12V','+5V','AGND'):
        supply[net]={'source_node':{'id':'external-source:'+net,'xy_mm':None,'regulation_V':None},'physical_endpoints':[{'ref':ref,'xy_mm':xy,'owner':owner} for owner,by in [('front-jack',frontby),('front-control',frontby),('octave-selector',frontby),('shared-reference',sharedby),('rear-core',rearby)] for ref,xy in endpoints(net,(owner,),by)],'common_distribution_resistance_mOhm':None,'contact_joint_tolerance_mOhm':None,'parallel_return_solution':None,'state_maxima':'UNKNOWN; inherited seven states remain in candidate-report','status':'OPEN; inventory graph does not qualify current or voltage drop'}
    wire_checks=[]
    for link in links:
        mh=middleby['M:'+link['id']]
        for instance in ('O1','O2','O3','O4','O5'):
            fh=instanceby[instance]['H:'+link['id']]
            datum=next(p for p in lock if p['uid']==link['uid'].replace('O1',instance))
            depth=-datum.get('assembly_pcb_z_mm',-config['front_depth_mm'])
            for pin in link['pins']:
                fxy=fh['pads_mm'][pin][0];mxy=shifted(mh['pads_mm'][pin][0],17*(int(instance[1:])-1))
                straight=math.sqrt(math.dist(fxy,mxy)**2+(config['middle_depth_mm']-depth)**2)
                slack=config['wire_nominal_mm']-config['wire_cut_tolerance_mm']-straight
                wire_checks.append({'instance':instance,'link':link['id'],'pin':pin,'front_depth_mm':depth,'straight_pad_distance_mm':straight,'minimum_remaining_slack_mm':slack,'within_slack_allocation':slack>=config['minimum_service_slack_mm'],'status':'conditional seated datums and wire bend radius remain OPEN'})
    c.require(all(w['within_slack_allocation'] for w in wire_checks),'insufficient wire/slack')
    paths=[Path(__file__),OUT/'assembly.json',OUT/'compact-rear.json',OUT/'candidate-report.json',c.PACK/'interface-contract.json',ROOT/'design/grid/placements.lock.json']+[ROOT/p['source'] for p in front+shared]+[ROOT/p['footprint_source'] for p in rear]+[Path(c.__file__),ROOT/'scripts/architecture278/populated_mechanics.py']+[ROOT/p['source'] for p in locked_hardware(lock)]
    return {'status':'SOURCE PLACEMENT AND CONSERVATIVE BOUNDS; Stage1 OPEN','source_sha256':binding(paths),'shared_driver_endpoints':shared_drivers,'config':config,'front_instances':instances,'endpoint_inventory':inventory,'local_net_nodes':local_nets,'bypass_associations':bypass,'front_placements':front,'middle_header_placements':middle,'shared_middle_placements':shared,'rear_placements':rear,'all_package_count':len(ps),'placed_physical_package_count':len([p for p in front if p['owner']!='header'])+len(shared)+len(rear),'alternatives':alternatives,'supply_graph':supply,'wire_checks':wire_checks,'wire_minimum_slack_mm':min(w['minimum_remaining_slack_mm'] for w in wire_checks),'limitations':['Actual retained pads and courtyards; physical mating-face, seated front depths, cable bend/swept service, keying and neighboring full solids OPEN.','15% octilinear (45-degree) routing reservation,5mm per segment and1mm per endpoint are explicit design allowances, not extracted copper or measured tolerances.','60mm nominal wire includes service slack; maximum63mm used in lengths, minimum57mm used in slack check. GH developed pair15mm and DIN25mm additional.','Every enumerated crossing link and all nine shared nets included; all171 local net node sets retained as inventory, not routed local paths. Return branches retain unknown common middle/source impedances.','Shared island whole packages retained; feedback/bypass distances and routed stability require review.','Five-instance report transforms O1 package geometry only; no replication acceptance or canonical changes.'],'native':'NOT RUN'}

def drawing(r):
    out=['<svg xmlns="http://www.w3.org/2000/svg" width="954" height="894" viewBox="0 0 318 298">','<rect width="318" height="298" fill="white"/>','<g font-family="sans-serif" font-size="2">']
    for p in r['front_placements']+r['shared_middle_placements']:
        x,y,xx,yy=p['box_mm'];color='#9dc9e2' if p['owner']=='header' else ('#e1b377' if p['side']=='panel' else '#b6d8a4')
        out.append(f'<rect x="{x}" y="{y}" width="{xx-x}" height="{yy-y}" fill="{color}" stroke="#333" stroke-width=".15"/><text x="{x}" y="{y+1.5}" font-size="1.5">{p["ref"]}</text>')
    out+=['<text x="105" y="10">O1 actual-pad source placement; front/rear PCB faces overlaid.</text>','<text x="105" y="14">Shared middle island shown. NOT ROUTED / NOT FIT QUALIFIED.</text>','</g></svg>']
    return '\n'.join(out)+'\n'

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args();r=build()
    for name,data in {'assembly-report.json':json.dumps(r,indent=2,sort_keys=True)+'\n','assembly-placement.svg':drawing(r)}.items():
        if args.check:c.require((OUT/name).read_text()==data,'stale '+name)
        else:(OUT/name).write_text(data)
    for n,a in r['alternatives'].items():print(n,round(a['maximum_mm'],3),a['overlength_endpoint_paths'],'overlength endpoint paths; Stage1 OPEN')
if __name__=='__main__':main()
