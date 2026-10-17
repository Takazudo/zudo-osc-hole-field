"""Design-only provisional DIN position integration for A01, J-PWR route study and M-01 print; source only, no native/physical claims."""
import argparse
import copy
import hashlib
import html
import json
import math
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import assembly
import stage10_interfaces as interfaces
import stage28_din_harness as s28
import stage29_din_column_reversal as s29

ROOT=Path(__file__).resolve().parents[3]
REL='design/architecture-278/implementation/'
OUT=ROOT/REL/'stage30'
BASE='00266037a7e2134c9c6c70d1ae95695932e7f1f6'
MUTABLE={REL+'README.md',REL+'WORK.md','scripts/architecture278/implementation/check_source.py'}
SCRIPTS={'scripts/architecture278/implementation/'+n for n in ('stage30_din_design_integration.py','test_stage30_din_design_integration.py')}
SIDES=s29.SIDES
NODE_SIDE={'female':'middle','male':'rear'}
CORNERS=s29.CORNERS
need,read,dump,sha,rev=s28.need,s28.read,s28.dump,s28.sha,s29.rev
# Stage10 release sweeps are "Mated7.3mm+15mm axial release" about each GH header face.
MATED_MM=7.3
OWN_LINK='J-PWR'
EXCLUDED_SCOPE=('manufacturing or assembly qualification','canonical schematic, board or library changes','native KiCad, ERC/DRC or simulation runs',
    'ordering, quotes, uploads or supplier contact','overall architecture adoption','D02 or overall manufacturing fit as a pass','binding contact numbers to production copper')
FOOTPRINTS=['footprints/kicad/zudo-osc-hole-field.pretty/'+n+'.kicad_mod' for n in ('Jack_3.5mm_QingPu_WQP518MA','PTV09A-4020F','Toggle_Dailywell_2MS_T1B1M2',
    'Button_Omron_B3F_6x6_P6.5x4.5','SRBV160803','LED0402-Kingbright-Red','LED0402-Kingbright-White')]
MEASURED_KEYS=('measured_path_mm','chosen_cut_mm','bend_radius_mm')
PAGE_MM=(210.0,297.0)
PT=72/25.4


def order(p):return ('abc'.index(p[0]),int(p[1:]))


def validate_approval(a,mapping):
    s28.no_claims(a,'approval')
    need(a['status']=='DESIGN_ONLY_PROVISIONAL' and a['date']=='2026-10-17' and a['decided_by']=='OWNER','design-only provisional owner record')
    need(a['mapping']==mapping,'approved mapping differs from Stage29')
    need(set(EXCLUDED_SCOPE)<=set(a['scope_excludes']),'approval scope widened beyond design study')
    need(not any(re.search(r'\b(adopt(ed)? for manufactur|qualif|release)',x,re.I) for x in a['scope_includes']),'approval includes manufacturing/qualification scope')


def stage29_current():
    """Re-derive Stage29 from its own inputs and require the committed outputs to match."""
    data=s29.load();cmap,report=s29.build(data,preserve=False)
    committed=read(ROOT/REL/'stage29/report.json');report['preservation_baseline']=committed['preservation_baseline']
    # Only the reviewed entrypoints may differ from the Stage29 commit; every other bound hash must still match.
    for path in set(report['source_sha256'])&MUTABLE:report['source_sha256'][path]=committed['source_sha256'][path]
    for name,body in s29.outputs(cmap,report).items():need((ROOT/REL/'stage29'/name).read_text()==body,'Stage29 output is not current '+name)
    need(report['status']=='SOURCE_CORRECTION_CANDIDATE_NOT_ADOPTED','Stage29 history status changed')
    return data,cmap,report


def design_positions(cmap):
    out={s:{} for s in SIDES}
    for r in cmap['contacts']:out[r['side']][r['physical_contact']]=[r['candidate_xy_mm']+[r['z_mm']]]
    return out


def verify_design(design,s29data,s29report):
    """Stage29 verification applied to the design map: column reversal on both sides, nets fixed, holes and planes fixed."""
    mech=s29data['mech'];stage10=s29.stage10_positions(mech)
    for s,pads in design.items():
        for p,v in pads.items():need(v!=stage10[s][p],'Stage10 coordinate left in the design map '+s+' '+p)
    facts=s28.frame_facts(s29data['lock'],mech)
    drawings,_=s29.drawing_facts(s29data['evidence'],s29data['vector'],s29data['reading'],s29data['sources'])
    frozen={c['label']:c['net'] for c in s29data['ledger28']['din_contacts']}
    fits=s29.verify(design,stage10,drawings,facts,mech,s29data['interfaces']['DIN_pinmap'],frozen)
    for s in SIDES:need(s29.det(fits[s][0])==s29report['matrices'][s]['candidate_det']==facts[s]['expected_det'],'design determinant '+s)
    return stage10,fits


def contact_rows(design,stage10,s29data,cmap):
    pinmap=s29data['interfaces']['DIN_pinmap'];src={(r['side'],r['physical_contact']):r for r in cmap['contacts']}
    rows=[]
    for s,(side,ref,board) in SIDES.items():
        for p in sorted(design[s],key=order):
            c=src[(s,p)]
            need(c['net']==pinmap[p] and c['nc']==(pinmap[p] is None),'Stage29 contact map net/NC differs '+p)
            rows.append({'connector':ref,'side':s,'board':board,'physical_contact':p,'net':pinmap[p],'nc':pinmap[p] is None,'contact_attribute':c['contact_attribute'],
                'design_xy_mm':design[s][p][0][:2],'z_mm':design[s][p][0][2],'stage10_xy_mm':stage10[s][p][0][:2],'stage10_label_at_design_xy':rev(p),
                'graph_node':'DIN:'+NODE_SIDE[s]+':'+p,
                'source':{'position':'stage29/contact-map.json (column reversal of Stage10 '+side+' pads)','net':'stage15/interfaces-report.json DIN_pinmap'}})
    return rows


def node_board(node,mech,packages):
    if node['kind']=='DIN':return {'DIN:middle':'A01-middle','DIN:rear':'A01-core'}[node['id'].rsplit(':',1)[0]]
    if node['kind']=='GH':return mech['headers'][node['ref']]['board']
    if node['kind'] in ('terminal_land','LED_wire_land'):return 'A01-jack' if node['kind']=='terminal_land' else 'A01-fixed'
    return packages[node['ref']]['placement']['board']


def impact(graph,paths,stage16,design,mech):
    """Recompute only the Stage10 trace-length allocations that end on a DIN node."""
    need(all(stage16['transport_contract'][k]==graph[k] for k in ('edges','nodes','wires','terminal_wires','DIN_pinmap','headers','counts','local_net_groups')),'Stage16 transport contract differs from Stage15 interfaces')
    nodes=copy.deepcopy(graph['nodes'])
    for s,pads in design.items():
        for p,v in pads.items():
            key='DIN:'+NODE_SIDE[s]+':'+p;need(nodes[key]['net']==graph['DIN_pinmap'][p],'graph DIN net '+key);nodes[key]['pad_xyz_mm']=v[0]
    edges=[];changed={}
    for i,e in enumerate(graph['edges']):
        ends=[k for k in (e['from'],e['to']) if k.startswith('DIN:')]
        if not ends:continue
        a,b=graph['nodes'][e['from']]['pad_xyz_mm'],graph['nodes'][e['to']]['pad_xyz_mm'];na,nb=nodes[e['from']]['pad_xyz_mm'],nodes[e['to']]['pad_xyz_mm']
        need(all(graph['DIN_pinmap'][k.rsplit(':',1)[1]] is not None for k in ends),'NC DIN contact connected by edge '+str(i))
        need(e['net']==nodes[e['from']]['net']==nodes[e['to']]['net'],'DIN edge net identity '+str(i))
        if e['kind']=='DIN_mated_pair':
            need(e['allocated_developed_mm']==25 and na[:2]==nb[:2] and a[:2]==b[:2],'mated DIN pair must coincide and keep the 25 mm pair allocation '+str(i))
            new=25
        else:
            need(math.isclose(interfaces.trace_length(a,b),e['allocated_developed_mm'],abs_tol=1e-9),'Stage15 allocation not reproducible from Stage10 DIN XY '+str(i))
            new=interfaces.trace_length(na,nb);changed[i]=new
        edges.append({'edge_index':i,'kind':e['kind'],'net':e['net'],'from':e['from'],'to':e['to'],
            'stage10_straight_mm':round(math.dist(a,b),6),'design_straight_mm':round(math.dist(na,nb),6),
            'stage10_allocation_mm':round(e['allocated_developed_mm'],6),'design_allocation_mm':round(new,6),'delta_allocation_mm':round(new-e['allocated_developed_mm'],6),
            'routed_copper_mm':None,'routed_copper_status':'NOT RUN (no copper routing)','model':'DIN pair fixed 25 mm' if e['kind']=='DIN_mated_pair' else 'Stage10 trace_length: 1.15 octile XY + 7 mm + |dz|'})
    need(len(changed)==34 and len(edges)==50,'34 DIN-incident copper allocations and 16 mated pairs')
    out={}
    for name,metric in (('signal_net_paths','complete_net_pad_path_allocation_mm'),('power_and_return_endpoint_paths','allocated_developed_mm'),('local_endpoint_paths','complete_net_pad_path_allocation_mm')):
        rows=[]
        for r in paths[name]:
            need(math.isclose(sum(graph['edges'][j]['allocated_developed_mm'] for j in r['edge_indices']),r[metric],abs_tol=1e-8),'Stage15 path sum '+name)
            if not set(r['edge_indices'])&set(changed):continue
            new=sum(changed.get(j,graph['edges'][j]['allocated_developed_mm']) for j in r['edge_indices'])
            rows.append({'net':r['net'],'from':r['from'],'to':r['to'],'changed_edges':sorted(set(r['edge_indices'])&set(changed)),
                'stage10_allocation_mm':round(r[metric],6),'design_allocation_mm':round(new,6),'delta_mm':round(new-r[metric],6),
                'harness_wire_cut_max_mm':r.get('harness_wire_cut_max_mm',r.get('wire_cut_max_mm',r.get('all_wire_cut_max_mm'))),'routed_mm':None})
        out[name]=rows
    need(len(out['signal_net_paths'])==11 and not out['power_and_return_endpoint_paths'] and not out['local_endpoint_paths'],'DIN XY reaches 11 signal paths only')
    contacts=[]
    for p in sorted(graph['DIN_pinmap'],key=order):
        net=graph['DIN_pinmap'][p]
        if net is None:continue
        row={'physical_contact':p,'net':net}
        for side in ('middle','rear'):
            key='DIN:'+side+':'+p;links=[]
            for e in edges:
                if e['kind']=='DIN_mated_pair' or key not in (e['from'],e['to']):continue
                other=e['to'] if e['from']==key else e['from'];n=graph['nodes'][other]
                links.append({'node':other,'ref':n['ref'],'pin':n['pin'],'kind':n['kind'],'board':node_board(n,mech,stage16['packages']),'xyz_mm':n['pad_xyz_mm'],'edge_kind':e['kind'],
                    'stage10_allocation_mm':e['stage10_allocation_mm'],'design_allocation_mm':e['design_allocation_mm']})
            row[side]={'graph_node':key,'stage10_xyz_mm':graph['nodes'][key]['pad_xyz_mm'],'design_xyz_mm':nodes[key]['pad_xyz_mm'],'connections':links}
        endpoints=sorted(k for k in graph['source_endpoints'] if graph['nodes'][k]['net']==net)
        row['net_source_endpoints']=[{'endpoint':k,'board':node_board(graph['nodes'][k],mech,stage16['packages'])} for k in endpoints]
        row['beyond_A01']=None if net!='AGND' else 'upstream supply and chassis earth excluded (Stage28 exclusions); position null'
        contacts.append(row)
    need(len(contacts)==16,'16 assigned DIN contacts traced')
    return {'edges':edges,'paths':out,'contacts':contacts}


def historical_consumers(graph,edges):
    """Committed files that still carry the Stage10 DIN-incident allocations; kept as history."""
    raw=[repr(graph['edges'][e['edge_index']]['allocated_developed_mm']) for e in edges if e['kind']!='DIN_mated_pair']
    out=[]
    for p in sorted((ROOT/REL).glob('stage*/**/*.json')):
        rel=str(p.relative_to(ROOT))
        if rel.startswith(REL+'stage30/'):continue
        text=p.read_text();found=sum(1 for v in raw if v in text)
        if found:out.append({'path':rel,'sha256':sha(p),'matching_allocation_values':found,'status':'HISTORICAL_STAGE10_DIN_XY; superseded for design use by stage30/connection-impact.json; bytes unchanged'})
    return out


def harness_preserved(ledger28,report28,inventory,policy):
    rows=ledger28['conductors'];c=ledger28['counts']
    need((c['GH_harnesses'],c['GH_conductors'],c['permanent_tails'],c['conductors'],c['land_annotations'])==(4,20,14,34,22) and len(rows)==34,'harness counts changed')
    need({r['kind'] for r in rows}=={'GH_HARNESS','PERMANENT_TAIL'} and not any('DIN' in r['kind'] for r in rows),'DIN contacts must not become harness conductors')
    need({l:sum(1 for r in rows if r['link']==l) for l in s28.LINKS}==s28.LINKS and sum(1 for r in rows if r['kind']=='PERMANENT_TAIL')==14,'GH link / tail conductor counts')
    for r in rows:
        need(all(r['geometry'][k] is None for k in MEASURED_KEYS) and r['anchor']['position_mm'] is None and r['results']=='NOT_RUN','assumption or proposal recorded as a measurement '+r['id'])
    tp={ref:row for ref,row in inventory['unbound'].items() if ref.startswith('TP')}
    need(len(tp)==22 and all(r['in_bom'] is False and r['on_board'] is False for r in tp.values()),'22 land annotations keep their exclusion flags')
    need(policy['exclusions']==ledger28['exclusions'],'harness exclusions changed')
    need(hashlib.sha256(dump(ledger28).encode()).hexdigest()==report28['ledger_sha256'],'Stage28 ledger differs from its report hash')
    return {'conductors':34,'GH_harnesses':4,'GH_conductors':20,'permanent_tails':14,'land_annotations':22,'land_annotation_flags':'in_bom=false, on_board=false',
        'exclusions':[e['scope'] for e in ledger28['exclusions']],'DIN_contacts_as_harness':0,'measured_values':'all null',
        'stage28_ledger_sha256':report28['ledger_sha256'],'status':'UNCHANGED_FROM_STAGE28'}


def box(i,lo,hi,kind='known',link=None):return {'id':i,'link':link,'lo':[float(v) for v in lo],'hi':[float(v) for v in hi],'kind':kind}


def obstacles(mech,lock,assume,cap=None):
    """The modelled Stage10 keep-out classes, the locked foreign hardware, and assumed A01 body envelopes."""
    obs=[box(o['id'],o['lo'],o['hi'],link=o['link']) for o in s28.obstacles(mech)]
    for k,f in sorted(mech['carrier_frames'].items()):
        z0,z1=f['z_mm']
        for i,b in enumerate(f['rails_boxes_mm']):obs.append(box(f'rail:{k}:{i}',[b[0],b[1],z0],[b[2],b[3],z1]))
        for i,b in enumerate(f['crossmembers_boxes_mm']):obs.append(box(f'crossmember:{k}:{i}',[b[0],b[1],z0],[b[2],b[3],z1]))
        if 'mount_tabs' in f:
            for i,b in enumerate(f['mount_tabs']['boxes_mm']):obs.append(box(f'tab:{k}:{i}',[b[0],b[1],f['mount_tabs']['z_mm'][0]],[b[2],b[3],f['mount_tabs']['z_mm'][1]]))
    (nx0,ny0,nx1,ny1),=mech['middle_access_edge_notches_mm']
    for n,b in sorted(mech['boards'].items()):
        x0,y0,x1,y1=b['outline_mm'];z0,z1=b['z_mm']
        if n=='A01-middle':
            need(x0==nx0 and y0<ny0<ny1<y1,'middle access notch on the left board edge')
            for j,(lo,hi) in enumerate((([x0,y0],[x1,ny0]),([x0,ny1],[x1,y1]),([nx1,ny0],[x1,ny1]))):obs.append(box(f'board:{n}:{j}',lo+[z0],hi+[z1]))
        else:obs.append(box('board:'+n,[x0,y0,z0],[x1,y1,z1]))
    x0,y0,x1,y1=mech['fixed_LED_substrate']['outline_mm'];z0,z1=mech['fixed_LED_substrate']['z_mm'];obs.append(box('board:A01-fixed-LED',[x0,y0,z0],[x1,y1,z1]))
    for h in mech['service']['core_handles']:
        x,y=h['xy_mm'];r=h['attachment_radius_mm'];obs.append(box(f'handle:{x}:{y}',[x-r,y-r,h['rear_projection_z_mm'][0]],[x+r,y+r,h['rear_projection_z_mm'][1]]))
    height=assume['component_body_height_mm']['value']
    for ref,p in sorted(mech['placements'].items()):
        b=p['box_mm'];z=p['conditional_pad_depth_mm']
        if p['side']=='rear':obs.append(box('body:'+ref,[b[0],b[1],z],[b[2],b[3],z+height],kind='assumed_height'))
        else:obs.append(box('body:'+ref,[b[0],b[1],0],[b[2],b[3],z]))
    placed=set(mech['placements']);top=assume['foreign_unknown_depth_top_z_mm']
    need(top['status']=='ASSUMPTION' and top['value']==mech['carrier_frames']['middle']['z_mm'][0],'unknown foreign depth is capped at the middle carrier front by assumption')
    front=top['value'] if cap is None else cap
    for q in assembly.locked_hardware(lock['placements']):
        if q['ref'] in placed:continue
        b=q['box_mm'];pcb=q['conditional_pcb_depth_mm']+1.6
        obs.append(box('foreign:'+q['ref'],[b[0],b[1],0],[b[2],b[3],pcb]))
        # Stage10: foreign XY projection is not free space and its depth behind its PCB is UNKNOWN.
        obs.append(box('foreign-depth:'+q['ref'],[b[0],b[1],pcb],[b[2],b[3],front],kind='unknown_depth'))
        obs[-1]['block']=q['uid'].split(':')[1].split('.')[0]
    return obs


def relieve(obs,mod):
    out=[];found=False
    for o in obs:
        if o['id']!=mod['obstacle']:out.append(o);continue
        found=True;(y0,y1),zr=mod['y_mm'],mod['relieved_top_z_mm'];lo,hi=o['lo'],o['hi']
        need(lo[1]<y0<y1<hi[1] and lo[2]<zr<hi[2],'relief inside the rail')
        out+=[dict(o,id=o['id']+':relieved',lo=[lo[0],y0,lo[2]],hi=[hi[0],y1,zr]),dict(o,id=o['id']+':a',hi=[hi[0],y0,hi[2]]),dict(o,id=o['id']+':b',lo=[lo[0],y1,lo[2]])]
    need(found,'relief obstacle exists')
    return out


def hits(pts,obs,e,link=OWN_LINK):
    out={}
    for p,q in zip(pts,pts[1:]):
        for o in obs:
            if o['link']==link:continue
            if s28.segment_box(p,q,[v-e for v in o['lo']],[v+e for v in o['hi']]):out[o['id']]=o['kind']
    return dict(sorted(out.items()))


def clearance(pts,obs,kinds=('known','assumed_height')):
    sel=[o for o in obs if o['kind'] in kinds]
    if hits(pts,sel,0.0):return 0.0
    lo,hi=0.0,20.0
    for _ in range(40):
        mid=(lo+hi)/2
        if hits(pts,sel,mid):hi=mid
        else:lo=mid
    return round(lo,4)


def polyline_length(pts):return sum(math.dist(p,q) for p,q in zip(pts,pts[1:]))


def bend_limit(pts):
    """Largest fillet radius each corner admits; a leg is shared with the far corner only if that corner also turns (housing segments stay straight)."""
    turns=[0.0]*len(pts)
    for i in range(1,len(pts)-1):
        u=[pts[i][k]-pts[i-1][k] for k in range(3)];v=[pts[i+1][k]-pts[i][k] for k in range(3)]
        turns[i]=math.acos(max(-1.0,min(1.0,sum(x*y for x,y in zip(u,v))/math.dist(pts[i],pts[i-1])/math.dist(pts[i],pts[i+1]))))
    out=[]
    for i in range(2,len(pts)-2):
        if turns[i]<1e-9:continue
        lu=math.dist(pts[i],pts[i-1])/(2 if turns[i-1]>1e-9 else 1);lv=math.dist(pts[i],pts[i+1])/(2 if turns[i+1]>1e-9 else 1)
        out.append({'vertex':pts[i],'turn_deg':round(math.degrees(turns[i]),3),'max_radius_mm':round(min(lu,lv)/math.tan(turns[i]/2),4)})
    need(all(turns[i]<1e-9 for i in (1,len(pts)-2)),'route must leave each housing axially')
    return out


def ends(mech,ref,pin):
    pad=mech['headers'][ref]['pads_xyz_mm'][pin][0];b=mech['boards'][mech['headers'][ref]['board']]['z_mm']
    need(pad[2] in b,'header pad on a board face '+ref);axis=1 if pad[2]==b[1] else -1
    return pad,axis


def route_study(mech,lock,inp,ledger28):
    need(inp['status']=='ROUTE_STUDY_INPUT_ASSUMPTIONS_NOT_MEASURED','route input status')
    a=inp['assumptions'];s28.no_claims(inp,'route-input')
    need(all(v['status'] in ('ASSUMPTION','STAGE10_PROPOSAL') for k,v in a.items() if isinstance(v,dict)),'route assumptions must not be recorded as measured')
    for s in mech['connector_release_sweeps']:need(math.isclose(s['z_mm'][1]-s['z_mm'][0],MATED_MM+a['release_travel_mm']['value'],abs_tol=1e-9),'release sweep depth')
    od=a['wire_od_mm']['value'];need(ledger28['conductors'][0]['wire']['insulation_od_mm'][1]==od,'assumed OD is the JST GH maximum')
    radius=od*a['bundle_diameter_factor']['value']/2;env=radius+a['placement_margin_mm']['value']
    obs=obstacles(mech,lock,a);rows=[r for r in ledger28['conductors'] if r['link']==OWN_LINK]
    need([r['id'] for r in rows]==[f'H-J-PWR-{i}' for i in (1,2,3,4)],'four J-PWR conductors')
    la=[ends(mech,'A01:J-PWR:local',str(i)) for i in (1,2,3,4)];ma=[ends(mech,'A01:J-PWR:middle',str(i)) for i in (1,2,3,4)]
    centre=lambda e:[sum(p[0][k] for p in e)/4 for k in range(3)]
    lc,mc=centre(la),centre(ma);lax,max_=la[0][1],ma[0][1]
    need(all(x[1]==lax for x in la) and all(x[1]==max_ for x in ma),'header axes')
    lexit=[lc[0],lc[1],lc[2]+lax*MATED_MM];mexit=[mc[0],mc[1],mc[2]+max_*MATED_MM]
    proxy=[ledger28['conductors'][i] for i,r in enumerate(ledger28['conductors']) if r['link']=='J-SIG']
    cut=(rows[0]['geometry']['stage10_nominal_cut_mm'],rows[0]['geometry']['stage10_tolerance_mm'])
    need(all((r['geometry']['stage10_nominal_cut_mm'],r['geometry']['stage10_tolerance_mm'])==cut for r in rows),'one Stage10 J-PWR cut')
    out=[]
    for c in inp['candidates']:
        o=relieve(obs,c['modification']) if 'modification' in c else obs
        need(c['existing_geometry']==('modification' not in c),'candidate geometry flag '+c['id'])
        centreline=[lexit]+c['waypoints_mm']+[mexit];h=hits(centreline,o,env)
        known=sorted(k for k,v in h.items() if v!='unknown_depth');unknown=sorted(k for k,v in h.items() if v=='unknown_depth')
        status='BLOCKED_BY_KEEP_OUT' if known else 'UNKNOWN_FOREIGN_DEPTH' if unknown else 'CENTRELINE_CLEAR_UNDER_ASSUMPTIONS'
        full=[lc]+centreline+[mc];bends=bend_limit(full);rmax=min(b['max_radius_mm'] for b in bends)
        conductors=[]
        for r,(lp,_),(mp,_) in zip(rows,la,ma):
            le=[lp[0],lp[1],lp[2]+lax*MATED_MM];me=[mp[0],mp[1],mp[2]+max_*MATED_MM];path=[lp,le]+c['waypoints_mm']+[me,mp]
            cases=[]
            for dl in (0,1):
                for dm in (0,1):
                    t=a['release_travel_mm']['value'];l2=[le[0],le[1],le[2]+lax*t*dl];m2=[me[0],me[1],me[2]+max_*t*dm]
                    cases.append(2*MATED_MM+polyline_length([l2]+c['waypoints_mm']+[m2]))
            length=polyline_length(path);req=max(cases)+a['service_slack_mm']['value']
            conductors.append({'id':r['id'],'net':r['net'],'centreline_length_mm':round(length,3),'release_case_lengths_mm':[round(x,3) for x in cases],
                'required_min_cut_mm':round(req,3),'stage10_cut_mm':f'{cut[0]}±{cut[1]}','stage10_cut_sufficient':cut[0]-cut[1]>=req})
        jsig=[round(min(segment_distance(p,q,r['end_a']['pad_xyz_mm'],r['end_b']['pad_xyz_mm']) for r in proxy),3) for p,q in zip(centreline,centreline[1:])]
        flip=depth_flip(centreline,o,env,mech['boards']['A01-middle']['z_mm'][0])
        blocks=sorted({b['block'] for b in o if b['id'] in unknown})
        out.append({'id':c['id'],'title':c['title'],'existing_geometry':c['existing_geometry'],'modification':c.get('modification'),'waypoints_mm':c['waypoints_mm'],
            'status':status,'keep_out_hits':known,'unknown_depth_hits':unknown,'centreline_clearance_known_keep_outs_mm':clearance(centreline,o),'required_clearance_mm':round(env,4),
            'bend_limits':bends,'max_bend_radius_mm':rmax,'assumed_min_bend_radius_mm':a['min_bend_radius_mm']['value'],'bend_ok_under_assumption':rmax>=a['min_bend_radius_mm']['value'],
            'conductors':conductors,'core_withdrawal_volume_clear':'core-extraction-40mm' not in h,'min_distance_to_J_SIG_straight_proxies_per_segment_mm':jsig,
            'unknown_depth_blocks':blocks,'foreign_depth_cap_that_adds_unknown_hits_z_mm':flip,
            'feasible_under_existing_conditions':c['existing_geometry'] and status=='CENTRELINE_CLEAR_UNDER_ASSUMPTIONS' and rmax>=a['min_bend_radius_mm']['value'] and all(x['stage10_cut_sufficient'] for x in conductors),
            'physical':'NOT_RUN; centreline clearance is not physical non-interference'})
    return {'envelope':{'wire_od_mm':od,'bundle_radius_mm':round(radius,4),'margin_mm':a['placement_margin_mm']['value'],'required_centreline_clearance_mm':round(env,4)},
        'exits':{'local_exit_mm':lexit,'middle_exit_mm':mexit,'local_axis':'+z' if lax>0 else '-z','middle_axis':'+z' if max_>0 else '-z'},
        'candidates':out,'corridors':corridors(mech,a,env),'proxy_screen':proxy_screen(ledger28,obs),'obstacles':len(obs)},obs


def depth_flip(centreline,obs,env,top):
    """Lowest foreign-depth cap (z) at which the candidate first meets unknown-depth hardware; None up to the A01-middle face."""
    depth=[b for b in obs if b['kind']=='unknown_depth'];lo=min(b['lo'][2] for b in depth)
    unknown=lambda cap:bool(hits(centreline,[dict(b,hi=b['hi'][:2]+[cap]) for b in depth],env))
    if not unknown(top):return None
    hi=top
    if unknown(lo+1e-6):return lo
    for _ in range(30):
        mid=(lo+hi)/2
        if unknown(mid):hi=mid
        else:lo=mid
    return round(hi,3)


def segment_distance(p1,q1,p2,q2):
    """Minimum distance between two 3D segments (closed form with clamping)."""
    d1=[q1[i]-p1[i] for i in range(3)];d2=[q2[i]-p2[i] for i in range(3)];r=[p1[i]-p2[i] for i in range(3)]
    dot=lambda u,v:sum(x*y for x,y in zip(u,v));a,e,f=dot(d1,d1),dot(d2,d2),dot(d2,r);c,b=dot(d1,r),dot(d1,d2);den=a*e-b*b
    s=min(1.0,max(0.0,(b*f-c*e)/den)) if den>1e-12 else 0.0;t=(b*s+f)/e
    if t<0:t,s=0.0,min(1.0,max(0.0,-c/a))
    elif t>1:t,s=1.0,min(1.0,max(0.0,(b-c)/a))
    return math.dist([p1[i]+d1[i]*s for i in range(3)],[p2[i]+d2[i]*t for i in range(3)])


def corridors(mech,a,env):
    """The middle carrier ring encloses the J-PWR middle header; list every way in."""
    f=mech['carrier_frames']['middle'];rail=f['rails_boxes_mm'][0];lower=f['rails_boxes_mm'][1];board=mech['boards']['A01-middle'];jack=mech['boards']['A01-jack']
    csig=next(s for s in mech['connector_release_sweeps'] if s['ref']=='A01:C-SIG:middle')
    slot=board['z_mm'][0]-f['z_mm'][1];gap=[rail[3],lower[1]];open_=[max(0.0,csig['box_mm'][1]-gap[0]),max(0.0,gap[1]-csig['box_mm'][3])]
    channel=rail[0]-jack['outline_mm'][2];need(csig['box_mm'][0]<=rail[0] and csig['box_mm'][2]>=rail[2],'C-SIG sweep spans the rail gap width')
    sens=[{'wire_od_mm':od,'margin_mm':m,'required_gap_mm':round(2*(od*a['bundle_diameter_factor']['value']/2+m),4),'fits':slot>2*(od*a['bundle_diameter_factor']['value']/2+m)}
        for od in a['w2_sensitivity_od_mm'] for m in a['w2_sensitivity_margin_mm']]
    local=mech['headers']['A01:J-PWR:local']['pads_xyz_mm']['1'][0][2]+MATED_MM;ceiling=board['z_mm'][0]-env-local
    return {'ring_member_z_mm':f['z_mm'],'middle_front_face_z_mm':board['z_mm'][0],'J_PWR_local_exit_z_mm':round(local,6),
        'local_end_axial_lead_ceiling_mm':round(ceiling,4),'local_end_bend_note':'A route that turns directly toward the ring below the A01-middle face leaves the J-PWR local housing with at most this axial lead, so its first 90 degree turn admits at most this radius (loop routes through the own release sweep are not considered).',
        'other_ring_members':'The top crossmember (y 138-142) and the right rail have the same 2.4 mm slot under A01-middle.',
        'slot_over_ring_mm':round(slot,6),'slot_sensitivity':sens,
        'left_rail_gap_y_mm':gap,'left_rail_gap_left_by_C_SIG_sweep_mm':[round(v,6) for v in open_],
        'jack_edge_to_rail_channel_mm':round(channel,6),'open_front_below_z_mm':f['z_mm'][0],
        'required_bundle_gap_mm':round(2*env,4),
        'conclusion':'Every way into the closed middle carrier ring is narrower than the assumed bundle envelope, except the open front (z < ring front), which lies over locked foreign panel hardware (A02-A05 jacks/LEDs, E2-E5 switches) of unknown depth.'}


def proxy_screen(ledger28,obs):
    out={}
    for r in ledger28['conductors']:
        a,b=r['end_a']['pad_xyz_mm'],r['end_b']['pad_xyz_mm'];h=hits([a,b],[o for o in obs if not o['id'].startswith(('board:A01-jack','board:A01-middle','board:A01-core','board:A01-control','board:A01-fixed'))],0.0,r['link'])
        if r['link']!='TAIL':h={k:v for k,v in h.items() if v!='unknown_depth'}
        else:h={k:v for k,v in h.items() if v=='known'}
        if h:out[r['id']]=sorted(h)
    return out


def rail_relief_need(study,obs):
    """Smallest rail relief the W4 centreline needs, checked against the proposed one."""
    c=next(x for x in study['candidates'] if x['id']=='W4');m=c['modification'];e=study['envelope']['required_centreline_clearance_mm']
    r=next(b for b in obs if b['id']==m['obstacle']);pts=[study['exits']['local_exit_mm']]+c['waypoints_mm']+[study['exits']['middle_exit_mm']];near=[]
    a0,a1=r['lo'][0]-e,r['hi'][0]+e
    for p,q in zip(pts,pts[1:]):
        d=q[0]-p[0]
        if abs(d)<1e-12:
            if a0<=p[0]<=a1:near+=[p,q]
            continue
        t0,t1=sorted(((a0-p[0])/d,(a1-p[0])/d));t0,t1=max(t0,0.0),min(t1,1.0)
        if t0<=t1:near+=[[p[k]+(q[k]-p[k])*t for k in range(3)] for t in (t0,t1)]
    need(near,'W4 crosses the relieved rail')
    window=[round(min(x[1] for x in near)-e,3),round(max(x[1] for x in near)+e,3)];top=round(min(x[2] for x in near)-e,3)
    need(m['y_mm'][0]<=window[0] and m['y_mm'][1]>=window[1] and m['relieved_top_z_mm']<=top,'proposed relief smaller than the W4 centreline needs')
    return {'obstacle':m['obstacle'],'rail_box_mm':[r['lo'],r['hi']],'relieved_y_mm':m['y_mm'],'relieved_top_z_mm':m['relieved_top_z_mm'],
        'minimum_window_y_mm':window,'maximum_relieved_top_z_mm':top,'relief_depth_mm':round(r['hi'][2]-m['relieved_top_z_mm'],3),
        'remaining_rail_depth_mm':round(m['relieved_top_z_mm']-r['lo'][2],3),'status':m['status'],'route_status':c['status'],
        'centreline_clearance_mm':c['centreline_clearance_known_keep_outs_mm'],'foreign_depth_flip_z_mm':c['foreign_depth_cap_that_adds_unknown_hits_z_mm'],'max_bend_radius_mm':c['max_bend_radius_mm'],
        'still_open':['rail stiffness after relief (Stage10 planning model, 90 N DIN sensitivity)','J-PWR cut length after M-09','local-end bend radius accepted by the harness maker','J-SIG crossing of the same rail']}


# ---------- M-01 print (pure-Python PDF; no external renderer) ----------

def pdf_text(s):return s.encode('cp1252').replace(b'\\',b'\\\\').replace(b'(',b'\\(').replace(b')',b'\\)')


class Page:
    def __init__(self):self.ops=[]
    def P(self,x,y):return f'{x*PT:.4f} {(PAGE_MM[1]-y)*PT:.4f}'
    def line(self,a,b,w=0.25,grey=0):self.ops.append(f'{grey:.2f} G {w*PT:.3f} w {self.P(*a)} m {self.P(*b)} l S')
    def circle(self,c,d,w=0.12,grey=0):
        r=d/2;k=0.5522847498*r;x,y=c
        pts=[(x+r,y),(x+r,y-k,x+k,y-r,x,y-r),(x-k,y-r,x-r,y-k,x-r,y),(x-r,y+k,x-k,y+r,x,y+r),(x+k,y+r,x+r,y+k,x+r,y)]
        s=f'{grey:.2f} G {w*PT:.3f} w {self.P(*pts[0])} m '+' '.join(f'{self.P(q[0],q[1])} {self.P(q[2],q[3])} {self.P(q[4],q[5])} c' for q in pts[1:])+' h S'
        self.ops.append(s)
    def poly(self,pts,fill=0):self.ops.append(f'{fill:.2f} g '+f'{self.P(*pts[0])} m '+' '.join(f'{self.P(*p)} l' for p in pts[1:])+' h f')
    def text(self,xy,s,size=8,bold=False,grey=0):
        self.ops.append(b'BT '+f'{grey:.2f} g /{"F2" if bold else "F1"} {size:.2f} Tf {self.P(*xy)} Td ('.encode()+pdf_text(s)+b') Tj ET')
    def stream(self):return b'\n'.join(o if isinstance(o,bytes) else o.encode() for o in self.ops)+b'\n'


def write_pdf(pages):
    objs=[b'<< /Type /Catalog /Pages 2 0 R >>',None,b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica /Encoding /WinAnsiEncoding >>',
          b'<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica-Bold /Encoding /WinAnsiEncoding >>']
    kids=[]
    for p in pages:
        body=p.stream();objs.append(b'<< /Length %d >>\nstream\n'%len(body)+body+b'endstream')
        objs.append(f'<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {PAGE_MM[0]*PT:.3f} {PAGE_MM[1]*PT:.3f}] /Resources << /Font << /F1 3 0 R /F2 4 0 R >> >> /Contents {len(objs)} 0 R >>'.encode())
        kids.append(len(objs))
    objs[1]=('<< /Type /Pages /Kids ['+' '.join(f'{k} 0 R' for k in kids)+f'] /Count {len(kids)} >>').encode()
    out=bytearray(b'%PDF-1.4\n%\xe2\xe3\xcf\xd3\n');offsets=[]
    for i,o in enumerate(objs,1):offsets.append(len(out));out+=b'%d 0 obj\n'%i+o+b'\nendobj\n'
    x=len(out);out+=b'xref\n0 %d\n0000000000 65535 f \n'%(len(objs)+1)+b''.join(b'%010d 00000 n \n'%v for v in offsets)
    out+=b'trailer\n<< /Size %d /Root 1 0 R >>\nstartxref\n%d\n%%%%EOF\n'%(len(objs)+1,x)
    return bytes(out)


def pattern_layout(side,labels,mech,centre):
    """Board XY -> sheet mm, component side up: female seen from the rear (x reversed), male from the front."""
    v=s29.COMPONENT_VIEW[side];cx,cy=centre
    screen=lambda xy:(105+v[0][0]*(xy[0]-cx)+v[0][1]*(xy[1]-cy),160+v[1][0]*(xy[0]-cx)+v[1][1]*(xy[1]-cy))
    holes={lab:screen(xy) for lab,xy in labels.items()}
    fixing=[screen(h['point_mm']) for h in mech['DIN_flange_holes']] if side=='female' else []
    return holes,fixing,screen


def m01_pages(rows,stage10,mech,report29,commit_note):
    centre=read(ROOT/REL/'stage10/mechanical-input.json')['DIN_centre_mm'];pages=[];layout={}
    for side,(dside,ref,board) in SIDES.items():
        mpn=mech['din_connectors'][dside]['mpn']
        for variant in ('stage10','design'):
            labels={p:(v[0][:2] if variant=='stage10' else next(r['design_xy_mm'] for r in rows if r['side']==side and r['physical_contact']==p)) for p,v in stage10[side].items()}
            holes,fixing,screen=pattern_layout(side,labels,mech,centre);pg=Page();layout[f'{side}-{variant}']={'holes_mm':{p:[round(x,6) for x in xy] for p,xy in sorted(holes.items(),key=lambda t:order(t[0]))},'fixing_mm':[[round(x,6) for x in f] for f in fixing]}
            hist=variant=='stage10'
            pg.text((12,14),('M-01 1:1 PRINT  -  '+('STAGE10 HISTORICAL LABELS (mirrored; superseded, do not use for design)' if hist else 'STAGE30 DESIGN-ONLY PROVISIONAL LABELS (column reversal)')),9,True,0.45 if hist else 0)
            pg.text((12,20),f'{ref}  HARTING {mpn}  {"female" if side=="female" else "male"}  on {board} ({"rear" if side=="female" else "front"} face, board plane z = {mech["din_connectors"][dside]["mount_surface_z_mm"]} mm)',8,True)
            pg.text((12,25.5),'COMPONENT SIDE: viewed from the connector body toward the board, '+('from the rear along -z (panel +x points LEFT).' if side=='female' else 'from the front along +z (panel +x points RIGHT).'),7)
            pg.text((12,30.5),'PRINT AT 100% / ACTUAL SIZE. Turn off "fit to page". Measure both 100 mm bars before use; reject the print if either is off by more than 0.5 mm.',7,True)
            pg.text((12,35.5),'Holes: dia 1.0 contact drill centres (2.54 mm pitch). '+('Large circles: dia 2.8 fixing holes, 90 mm apart, 0.3 mm from row b toward row a.' if side=='female' else 'No board fixing holes on the male (its dia 2.55 holes are body flange features).'),7)
            for p,xy in holes.items():
                pg.circle(xy,1.0,grey=0.45 if hist else 0)
            for f in fixing:pg.circle(f,2.8,w=0.2,grey=0.45 if hist else 0)
            g=0.45 if hist else 0;tw=lambda t,size:0.55*size*len(t)/PT
            # Text sits outside the pattern: row a side gets the a-corner labels, pin-1 mark and span; row c side the numbers and c-corner labels.
            sa=1 if holes['a1'][0]>105 else -1;sc=-sa
            put=lambda x,y,t,size,bold=False,dx=0:pg.text(((x+dx) if dx>=0 else (x+dx-tw(t,size)),y),t,size,bold,g)
            top=min(y for _,y in holes.values())
            for r in 'abc':pg.text((holes[r+'1'][0]-0.7,top-12),r,7,True)
            cx_=holes['c1'][0]
            for n in range(1,33):put(cx_,holes['c'+str(n)][1]+0.8,str(n),4.5,dx=sc*4)
            for p in CORNERS:
                x,y=holes[p];put(x,y+1.2,p,7,True,dx=(sa*6 if p[0]=='a' else sc*9))
            ax,ay=holes['a1']
            pg.poly([(ax+sa*1.2,ay),(ax+sa*3.6,ay-1.2),(ax+sa*3.6,ay+1.2)],g)
            put(ax,ay+1.0,'pin 1',6,dx=sa*11)
            a1,a32=holes['a1'],holes['a32'];off=sa*24
            pg.line((a1[0]+off,a1[1]),(a32[0]+off,a32[1]),0.15);pg.line((a1[0]+off-1,a1[1]),(a1[0]+off+1,a1[1]),0.15);pg.line((a32[0]+off-1,a32[1]),(a32[0]+off+1,a32[1]),0.15)
            put(a1[0]+off,(a1[1]+a32[1])/2,'a1-a32 centres 78.74 mm',5.5,dx=sa*1.5)
            if fixing:
                f0,f1=sorted(fixing,key=lambda t:t[1]);put(f0[0],f0[1]+0.8,'fixing hole',5.5,dx=sc*9);put(f1[0],f1[1]+0.8,'fixing hole (90.00 mm centres)',5.5,dx=sc*9)
            pg.line((55,246),(155,246),0.3)
            for t in range(0,101,10):pg.line((55+t,244.5 if t%50 else 243.5),(55+t,246),0.2)
            pg.text((80,251),'SCALE CHECK: 100.00 mm (horizontal)',7)
            pg.line((22,110),(22,210),0.3)
            for t in range(0,101,10):pg.line((20.5 if t%50 else 19.5,110+t),(22,110+t),0.2)
            pg.text((8,108),'100.00 mm',6);pg.text((8,214),'(vertical)',6)
            ox,oy=165,232;vx=s29.COMPONENT_VIEW[side][0][0]
            pg.line((ox,oy),(ox+vx*10,oy),0.25);pg.text((ox+vx*10+(1 if vx>0 else -14),oy+1),'panel +x',5.5)
            pg.line((ox,oy),(ox,oy+10),0.25);pg.text((ox+1,oy+13),'panel +y (down)',5.5)
            pg.text((12,262),'Check: set the UNSOLDERED part on this print, body side toward you as shown, pins over the circles; photograph a1, c1, a32, c32 and the pin-1 mark.',6.5)
            pg.text((12,267),'Record the result on the M-01 record sheet (last page). Compare with the other variant of the same connector. M-01 is NOT RUN until the sheet is filled in.',6.5)
            pg.text((12,276),'DESIGN STUDY ONLY - not for fabrication. D02 stays CONFLICT_REQUIRES_DECISION. Mapping (design): candidate_position(row,n) = Stage10_position(row,33-n).',6)
            pg.text((12,281),commit_note,5.5)
            pg.text((12,286),f'Sheet {len(pages)+1} of 5. Drawing basis: HARTING {"0903296X824 rev C view A" if side=="female" else "0903196X922 rev B view B"} (stage29/drawing-reading.json).',5.5)
            pages.append(pg)
    rec=Page()
    rec.text((12,16),'M-01 RECORD SHEET (empty) - DIN contact orientation check, unpowered, unsoldered parts',10,True)
    rec.text((12,23),'Status: NOT RUN. Fill in by hand. Do not mark PASS here; the owner decides Q-O01 from this record.',7.5)
    fields=['Date / operator','Printer, paper, scaling setting (must be 100% / actual size)','Part lot / marking: J17909 09032966824','Part lot / marking: J17910 09031966922']
    y=33
    for f in fields:rec.text((12,y),f+':',8);rec.line((95,y+0.8),(198,y+0.8),0.15);y+=8
    rec.text((12,y+2),'Per sheet',8,True);y+=8
    cols=[(12,'Sheet'),(26,'H bar mm'),(44,'V bar mm'),(62,'a1 at label?'),(84,'c1?'),(98,'a32?'),(114,'c32?'),(130,'pin-1 mark?'),(152,'fixing holes?'),(176,'photo IDs')]
    for x,t in cols:rec.text((x,y),t,6.5,True)
    y+=3
    for i,name in enumerate(['1 J17909 Stage10','2 J17909 design','3 J17910 Stage10','4 J17910 design']):
        rec.line((12,y),(198,y),0.15);rec.text((12,y+6),name,6.5);y+=10
    rec.line((12,y),(198,y),0.15)
    rec.text((12,y+9),'Which variant matches the part (labels, pin-1 mark, body side)?  J17909: ____________   J17910: ____________',8)
    rec.text((12,y+18),'Fixing-hole offset side seen on the J17909 part (row a / row c): ____________',8)
    rec.text((12,y+27),'Notes / deviations:',8)
    for k in range(4):rec.line((12,y+35+k*8),(198,y+35+k*8),0.15)
    rec.text((12,276),'DESIGN STUDY ONLY - not for fabrication. Physical result fields are empty by design; machine-readable template: stage30/m01-record-template.json.',6)
    rec.text((12,281),commit_note,5.5);rec.text((12,286),'Sheet 5 of 5.',5.5)
    pages.append(rec)
    return pages,layout


def layout_checks(layout):
    out={}
    for key,l in layout.items():
        h=l['holes_mm'];cols=[h['a'+str(n)] for n in range(1,33)]
        pitch=[math.dist(p,q) for p,q in zip(cols,cols[1:])];span=math.dist(cols[0],cols[-1]);rowpitch=[math.dist(h[r+'1'],h[s+'1']) for r,s in (('a','b'),('b','c'))]
        need(len(h)==96 and all(abs(p-2.54)<1e-6 for p in pitch+rowpitch) and abs(span-78.74)<1e-6,'print hole pitch/span '+key)
        row={'contacts':96,'pitch_mm':round(min(pitch),6),'span_a1_a32_mm':round(span,6)}
        if key.startswith('female'):
            f=sorted(l['fixing_mm'],key=lambda t:t[1]);need(len(f)==2 and abs(math.dist(*f)-90)<1e-6,'print fixing holes 90 mm '+key)
            b=(h['b16'][1]+h['b17'][1])/2;row['fixing_spacing_mm']=round(math.dist(*f),6);row['fixing_offset_toward_row_a_mm']=round(abs(f[0][0]-h['b1'][0]),6)
            need(abs(abs(f[0][0]-h['b1'][0])-0.3)<1e-6 and (f[0][0]-h['b1'][0])*(h['a1'][0]-h['b1'][0])>0 and abs((f[0][1]+f[1][1])/2-b)<1e-6,'print fixing-hole offset toward row a '+key)
        else:need(not l['fixing_mm'],'male print has no fixing holes')
        out[key]=row
    for side in SIDES:
        a,b=layout[side+'-stage10']['holes_mm'],layout[side+'-design']['holes_mm']
        need(sorted(map(tuple,a.values()))==sorted(map(tuple,b.values())),'same hole set on both variants '+side)
        need(all(b[p]==a[rev(p)] for p in a),'design labels are the column reversal of the Stage10 labels on the print '+side)
    return out


def record_template():
    sheets=['J17909-stage10','J17909-design','J17910-stage10','J17910-design']
    return {'status':'M-01_NOT_RUN_EMPTY_TEMPLATE','print':'stage30/m01-print.pdf','instructions':'Unpowered, unsoldered parts on 100% prints; values are filled in by the person who runs M-01.',
        'date':None,'operator':None,'printer_and_scaling':None,'part_markings':{'J17909':None,'J17910':None},
        'sheets':{s:{'horizontal_bar_mm':None,'vertical_bar_mm':None,'a1_at_label':None,'c1_at_label':None,'a32_at_label':None,'c32_at_label':None,'pin1_mark_matches':None,'fixing_holes_align':None,'photo_ids':[]} for s in sheets},
        'matching_variant':{'J17909':None,'J17910':None},'fixing_hole_offset_side_observed':None,'notes':None}


# ---------- figures ----------

def esc(s):return html.escape(str(s),quote=True)


def render_connection_svg(rows,imp,mech):
    k=4.0;x0w,y0w=226,138;X=lambda x:round(30+(x-x0w)*k,2);Y=lambda y:round(80+(y-y0w)*k,2);W=1000;H=int(Y(296))+60
    o=[f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" font-family="sans-serif" font-size="10">','<rect width="100%" height="100%" fill="#fff"/>',
       '<text x="30" y="24" font-size="14" font-weight="bold">A01 DIN design-only provisional positions and their connections (panel front view, x right, y down)</text>',
       '<text x="30" y="42">Black dots: design XY of the 16 assigned contacts (light grey: 80 NC). Hollow grey: Stage10 XY of the same physical contact.</text>',
       '<text x="30" y="58">Blue: A01-middle edges to the GH middle headers. Purple dashed: A01-core edges to source pads and K-PWR. Lines are Stage15 allocation edges, not copper.</text>']
    for n in ('A01-middle','A01-core'):
        bx0,by0,bx1,by1=mech['boards'][n]['outline_mm'];dash='' if n=='A01-middle' else ' stroke-dasharray="5,3"'
        o.append(f'<rect x="{X(bx0)}" y="{Y(by0)}" width="{round((bx1-bx0)*k,2)}" height="{round((by1-by0)*k,2)}" fill="none" stroke="#999"{dash}/><text x="{X(bx0)+4}" y="{Y(by0)+13}" fill="#666">{n}</text>')
    for h,v in sorted(mech['headers'].items()):
        if v['board'] in ('A01-middle','A01-core'):
            bx0,by0,bx1,by1=v['box_mm'];o.append(f'<rect x="{X(bx0)}" y="{Y(by0)}" width="{round((bx1-bx0)*k,2)}" height="{round((by1-by0)*k,2)}" fill="#eef" stroke="#447"/><text x="{X(bx0)}" y="{Y(by0)-4}" fill="#447">{esc(h.replace("A01:",""))}</text>')
    for r in rows:
        if r['side']=='female' and not r['net']:
            x,y=r['design_xy_mm'];o.append(f'<circle cx="{X(x)}" cy="{Y(y)}" r="1.2" fill="#ccc"/>')
    for c in imp['contacts']:
        dx,dy=c['middle']['design_xyz_mm'][:2]
        for side,col,dash in (('middle','#1f5fbf',''),('rear','#8a3ab9',' stroke-dasharray="3,2"')):
            for l in c[side]['connections']:
                x,y=l['xyz_mm'][:2];o.append(f'<line x1="{X(dx)}" y1="{Y(dy)}" x2="{X(x)}" y2="{Y(y)}" stroke="{col}" stroke-width="0.7"{dash}/>')
    for c in imp['contacts']:
        sx,sy=c['middle']['stage10_xyz_mm'][:2];dx,dy=c['middle']['design_xyz_mm'][:2];left=c['physical_contact'][0]=='c'
        o.append(f'<circle cx="{X(sx)}" cy="{Y(sy)}" r="2.4" fill="none" stroke="#999"/><circle cx="{X(dx)}" cy="{Y(dy)}" r="2" fill="#000"/>')
        tx=X(296.46)-8 if left else X(301.54)+8
        o.append(f'<text x="{tx}" y="{Y(dy)+3.5}" text-anchor="{"end" if left else "start"}" font-size="9">{c["physical_contact"]} {esc(c["net"].replace("/A01/",""))}</text>')
    pin=next(x for x in rows if x['side']=='female' and x['physical_contact']=='a1')['design_xy_mm']
    o.append(f'<text x="{X(pin[0])+8}" y="{Y(pin[1])-10}" font-weight="bold" fill="#c00">a1 / pin 1 (column 1 at this end)</text>')
    end=next(x for x in rows if x['side']=='female' and x['physical_contact']=='a32')['design_xy_mm']
    o.append(f'<text x="{X(end[0])+8}" y="{Y(end[1])+14}" font-weight="bold" fill="#c00">a32</text>')
    o.append(f'<text x="30" y="{H-24}">Design-only provisional (owner, 2026-10-17). M-01 NOT RUN, D02 CONFLICT_REQUIRES_DECISION, no copper routed, not bound to production copper.</text>')
    o.append('</svg>');return '\n'.join(o)+'\n'


def render_route_svg(study,obs,mech):
    k=8.0;xa,xb,ya,yb,za,zb=215,295,140,200,25,60
    X=lambda x:round(30+(x-xa)*k,2);Y=lambda y:round(90+(y-ya)*k,2);top=int(Y(yb))+50;Z=lambda z:round(top+(zb-z)*k,2);H=int(Z(za))+40+18*len(study['candidates'])
    colors={'W1':'#d62728','W2':'#ff7f0e','W3':'#2ca02c','W4':'#1f77b4'}
    style=lambda b:('#f7c6dc' if b['id'].startswith('release') else '#c8a27a' if b['id'].startswith(('rail','crossmember','tab')) else '#9ec5e8' if b['kind']=='unknown_depth' else '#d9d9d9' if b['id'].startswith(('board','foreign:')) else '#f2b56b' if b['id'].startswith('tool') else '#eeeeee')
    o=[f'<svg xmlns="http://www.w3.org/2000/svg" width="1120" height="{H}" font-family="sans-serif" font-size="10">','<rect width="100%" height="100%" fill="#fff"/>',
       '<text x="30" y="24" font-size="14" font-weight="bold">A01 J-PWR route study, separate from the DIN correction: centrelines only, not measured, not physical clearance</text>',
       '<text x="30" y="42">Brown: carrier rails/crossmembers/tabs. Pink: other links\' release sweeps. Grey: boards and known panel hardware. Orange: mount tool access.</text>',
       '<text x="30" y="58">Light blue: locked foreign hardware (A02-A05, E2-E5) of unknown depth (Stage10: not free space). Dashed blue: W4 rail relief, PROPOSAL only. Black dotted: Stage28 straight proxy.</text>',
       f'<text x="30" y="{Y(ya)-8}" font-weight="bold">Plan (x right, y down), window x {xa}-{xb}, y {ya}-{yb} mm</text>',
       f'<text x="30" y="{Z(zb)-8}" font-weight="bold">Elevation (x right, z up = toward the rear), obstacles with y in {ya}-{yb} mm</text>']
    for view in ('plan','elev'):
        o.append('<g>')
        for b in sorted(obs,key=lambda b:style(b)):
            lo,hi=b['lo'],b['hi']
            if b['kind']=='assumed_height' or hi[0]<=xa or lo[0]>=xb or hi[1]<=ya or lo[1]>=yb or hi[2]<=za or lo[2]>=zb:continue
            lo=[max(lo[0],xa),max(lo[1],ya),max(lo[2],za)];hi=[min(hi[0],xb),min(hi[1],yb),min(hi[2],zb)]
            if view=='plan':x,y,w,h=X(lo[0]),Y(lo[1]),(hi[0]-lo[0])*k,(hi[1]-lo[1])*k
            else:x,y,w,h=X(lo[0]),Z(hi[2]),(hi[0]-lo[0])*k,(hi[2]-lo[2])*k
            o.append(f'<rect x="{x}" y="{y}" width="{round(w,2)}" height="{round(h,2)}" fill="{style(b)}" fill-opacity="0.45" stroke="#888" stroke-width="0.4"/>')
        for c in study['candidates']:
            pts=[study['exits']['local_exit_mm']]+c['waypoints_mm']+[study['exits']['middle_exit_mm']]
            if c['modification']:
                m=c['modification'];r=next(b for b in obs if b['id']==m['obstacle'])
                if view=='plan':o.append(f'<rect x="{X(r["lo"][0])}" y="{Y(m["y_mm"][0])}" width="{(r["hi"][0]-r["lo"][0])*k}" height="{(m["y_mm"][1]-m["y_mm"][0])*k}" fill="none" stroke="#1f77b4" stroke-width="1.2" stroke-dasharray="4,3"/>')
                else:o.append(f'<rect x="{X(r["lo"][0])}" y="{Z(r["hi"][2])}" width="{(r["hi"][0]-r["lo"][0])*k}" height="{round((r["hi"][2]-m["relieved_top_z_mm"])*k,2)}" fill="none" stroke="#1f77b4" stroke-width="1.2" stroke-dasharray="4,3"/>')
            f=(lambda p:f"{X(p[0])},{Y(p[1])}") if view=='plan' else (lambda p:f"{X(p[0])},{Z(p[2])}")
            o.append(f'<polyline points="{" ".join(f(p) for p in pts)}" fill="none" stroke="{colors[c["id"]]}" stroke-width="1.6"/>')
        a,b=[226,173,36.6],[283,150,48.4];f=(lambda p:(X(p[0]),Y(p[1]))) if view=='plan' else (lambda p:(X(p[0]),Z(p[2])))
        (x1,y1),(x2,y2)=f(a),f(b);o.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#000" stroke-dasharray="1.5,2.5" stroke-width="1"/>')
        o.append('</g>')
    o.append(f'<rect x="{X(xa)}" y="{Y(ya)}" width="{(xb-xa)*k}" height="{(yb-ya)*k}" fill="none" stroke="#333"/><rect x="{X(xa)}" y="{Z(zb)}" width="{(xb-xa)*k}" height="{(zb-za)*k}" fill="none" stroke="#333"/>')
    for x in range(xa,xb+1,10):o.append(f'<text x="{X(x)-8}" y="{Y(yb)+14}" font-size="8">x{x}</text><text x="{X(x)-8}" y="{Z(za)+14}" font-size="8">x{x}</text>')
    for y in range(ya,yb+1,10):o.append(f'<text x="2" y="{Y(y)+3}" font-size="8">y{y}</text>')
    for z in range(30,zb+1,10):o.append(f'<text x="2" y="{Z(z)+3}" font-size="8">z{z}</text>')
    y=int(Z(za))+34
    for i,c in enumerate(study['candidates']):
        o.append(f'<text x="30" y="{y+18*i}" fill="{colors[c["id"]]}" font-weight="bold">{c["id"]}: {esc(c["status"])}; clearance {c["centreline_clearance_known_keep_outs_mm"]} mm of {c["required_clearance_mm"]} mm; max bend R {c["max_bend_radius_mm"]} mm; {esc(c["title"])}</text>')
    o.append('</svg>');return '\n'.join(o)+'\n'


# ---------- markdown ----------

def cell(v):return s28.cell(v)


def render_map(rows):
    out=['# Stage30 design contact map (DESIGN_ONLY_PROVISIONAL)','','Mapping `candidate_position(row, n) = Stage10_position(row, 33-n)`, provisionally adopted by the owner on 2026-10-17 for design study only. M-01 NOT RUN; D02 stays CONFLICT_REQUIRES_DECISION. Nets stay with the physical contact ID.','']
    for ref in ('J17909','J17910'):
        r0=[r for r in rows if r['connector']==ref]
        out+=['## '+ref+' ('+r0[0]['side']+', '+r0[0]['board']+', z='+str(r0[0]['z_mm'])+' mm)','','| Physical contact | Net | Design XY (mm) | Stage10 XY (history) | Graph node |','|---|---|---|---|---|']
        out+=[f"| {r['physical_contact']} | {cell(r['net'] or 'NC')} | {r['design_xy_mm'][0]}, {r['design_xy_mm'][1]} | {r['stage10_xy_mm'][0]}, {r['stage10_xy_mm'][1]} | {r['graph_node']} |" for r in r0]
        out.append('')
    return '\n'.join(out)


def render_impact(imp,hist):
    o=['# Stage30 A01 connection impact of the provisional DIN positions','','Generated. Allocations are the Stage10 `trace_length` engineering model (1.15 × octile XY + 7 mm + |dz|), not routed copper. Straight = 3D pad-to-pad distance. Routed copper: NOT RUN (null everywhere).','',
       '## Assigned contacts and where they connect','','| Contact | Net | A01-middle side (Ref:pin, board) | A01-core side (Ref:pin, board) |','|---|---|---|---|']
    for c in imp['contacts']:
        f=lambda side:'<br>'.join(f"{l['ref']}:{l['pin']} ({l['board']})" for l in c[side]['connections'])
        o.append(f"| {c['physical_contact']} | {cell(c['net'])} | {f('middle')} | {f('rear')} |")
    o+=['','## DIN-incident edges (34 copper allocations change; 16 mated pairs keep 25 mm)','','| Edge | Kind | Net | From → To | Straight S10 → design mm | Allocation S10 → design mm | Δ mm |','|---|---|---|---|---|---|---|']
    for e in imp['edges']:
        o.append(f"| {e['edge_index']} | {e['kind']} | {cell(e['net'])} | {e['from']} → {e['to']} | {e['stage10_straight_mm']:.3f} → {e['design_straight_mm']:.3f} | {e['stage10_allocation_mm']:.3f} → {e['design_allocation_mm']:.3f} | {e['delta_allocation_mm']:+.3f} |")
    o+=['','## Signal path allocations that include a changed edge','','| Net | From → To | S10 mm | Design mm | Δ mm | Wire cut max mm |','|---|---|---|---|---|---|']
    for r in imp['paths']['signal_net_paths']:
        o.append(f"| {cell(r['net'])} | {r['from']} → {r['to']} | {r['stage10_allocation_mm']:.3f} | {r['design_allocation_mm']:.3f} | {r['delta_mm']:+.3f} | {r['harness_wire_cut_max_mm']} |")
    o+=['','Power/return endpoint paths and local endpoint paths contain no DIN-incident copper edge, so they are unchanged. Stage15 lists one explicit path per power endpoint; the 16 changed AGND joins to the DIN b contacts (middle and core) are parallel return branches that no listed path uses.','','## Historical files that still carry Stage10 DIN allocations (unchanged bytes)','']
    o+=[f"- `{h['path']}` ({h['matching_allocation_values']} Stage10 allocation values found by text match)" for h in hist]
    return '\n'.join(o+[''])


def render_route(study,relief):
    e=study['envelope'];c0=study['corridors']
    o=['# Stage30 J-PWR route study (separate from the DIN correction)','','Centreline comparison only. Wire size, bundle size and bend radius are **assumptions** (route-input.json). Clear centrelines are not physical non-interference. Measured lengths, cut lengths, fit, M-09 and M-12 are NOT RUN.','',
       f"Envelope: OD {e['wire_od_mm']} mm, 4-wire bundle radius {e['bundle_radius_mm']} mm + margin {e['margin_mm']} mm = required centreline clearance **{e['required_centreline_clearance_mm']} mm** to every keep-out.",'',
       '## Ways into the middle carrier ring','',
       f"- Slot between ring top z={c0['ring_member_z_mm'][1]} and A01-middle front face z={c0['middle_front_face_z_mm']}: **{c0['slot_over_ring_mm']} mm** (bundle needs {c0['required_bundle_gap_mm']} mm).",
       f"- Left rail gap y={c0['left_rail_gap_y_mm']}: the C-SIG middle release sweep leaves {c0['left_rail_gap_left_by_C_SIG_sweep_mm']} mm.",
       f"- Jack board edge to left rail: {c0['jack_edge_to_rail_channel_mm']} mm.",
       f"- Open front below z={c0['open_front_below_z_mm']}: over locked foreign panel hardware (A02-A05 jacks/LEDs, E2-E5 switches) whose depth is unknown (Stage10: XY projection is not free space). Stage30 assumes that depth ends at the middle carrier front, z={c0['open_front_below_z_mm']} (ASSUMPTION; see the foreign-depth sensitivity below).",
       f"- {c0['other_ring_members']}",
       f"- J-PWR local housing exit z={c0['J_PWR_local_exit_z_mm']}: a route that turns directly toward the ring below the A01-middle face has at most **{c0['local_end_axial_lead_ceiling_mm']} mm** of axial lead there, so its first 90° bend radius is at most that.",'',
       '| Slot sensitivity: OD mm | margin mm | gap needed mm | fits 2.4 mm slot |','|---|---|---|---|']
    o+=[f"| {s['wire_od_mm']} | {s['margin_mm']} | {s['required_gap_mm']} | {s['fits']} |" for s in c0['slot_sensitivity']]
    o+=['','## Candidates','','| ID | Geometry | Status | Keep-out hits | Unknown-depth hits (blocks) | Clearance to known keep-outs mm | Max bend R mm (assumed need) | Longest required cut mm (Stage10 90±3) |','|---|---|---|---|---|---|---|---|']
    for c in study['candidates']:
        o.append(f"| {c['id']} {cell(c['title'])} | {'existing' if c['existing_geometry'] else 'PROPOSED CHANGE'} | **{c['status']}** | {cell(', '.join(c['keep_out_hits']) or '—')} | {cell(', '.join(c['unknown_depth_hits']) or '—')}{' ('+', '.join(c['unknown_depth_blocks'])+')' if c['unknown_depth_blocks'] else ''} | {c['centreline_clearance_known_keep_outs_mm']} | {c['max_bend_radius_mm']} ({c['assumed_min_bend_radius_mm']}{'' if c['bend_ok_under_assumption'] else ', short'}) | {max(x['required_min_cut_mm'] for x in c['conductors'])} |")
    o+=['','Foreign-depth sensitivity: the unknown depth of the locked foreign hardware is capped at the middle carrier front by assumption. The cap (z) at which each candidate first meets unknown-depth hardware:','']
    o+=[f"- {c['id']}: {'no unknown-depth hit up to the A01-middle face' if c['foreign_depth_cap_that_adds_unknown_hits_z_mm'] is None else 'z = '+str(c['foreign_depth_cap_that_adds_unknown_hits_z_mm'])+' mm'}" for c in study['candidates']]
    o+=['','## Minimum change proposal (not adopted)','',f"Relieve `{relief['obstacle']}` (middle carrier left rail, z {relief['rail_box_mm'][0][2]}-{relief['rail_box_mm'][1][2]}) to top z={relief['relieved_top_z_mm']} mm over y={relief['relieved_y_mm']} mm: {relief['relief_depth_mm']} mm deep, leaving {relief['remaining_rail_depth_mm']} mm of rail. The W4 centreline needs at least y={relief['minimum_window_y_mm']} and top z <= {relief['maximum_relieved_top_z_mm']}. W4 then reads `{relief['route_status']}` with {relief['centreline_clearance_mm']} mm centreline clearance to known keep-outs; it meets unknown-depth foreign hardware if that depth reaches z = {relief['foreign_depth_flip_z_mm']} mm. Status: {relief['status']}.",'',
       'Still open after the relief: '+'; '.join(relief['still_open'])+'.','',
       ('Even then the J-PWR cut must be re-derived after M-09: the Stage10 cut is shorter than every routed candidate needs under the Stage10 release and slack rule. ' if not any(x['stage10_cut_sufficient'] for c in study['candidates'] for x in c['conductors']) else 'Some candidates fit the Stage10 cut; it is still a proposal until M-09. ')
       +f"The local-end bend stays tight: the J-PWR local housing exit is {round(c0['middle_front_face_z_mm']-c0['J_PWR_local_exit_z_mm'],3)} mm below the A01-middle front face.",'',
       '## Stage28 straight proxies against the full keep-out set','','Board slabs are left out (straight lines through boards are expected for proxies).','']
    o+=[f"- {k}: {', '.join(v)}" for k,v in study['proxy_screen'].items()]
    o+=['','Service is unchanged: disconnect K-PWR, then withdraw the core 40 mm; no candidate enters the core withdrawal volume.','']
    return '\n'.join(o)


def protected():
    changed=subprocess.check_output(['git','diff',BASE,'--name-only','--diff-filter=DMRTUXB'],cwd=ROOT,text=True).splitlines()
    need(set(changed)<=MUTABLE,'historical/canonical protected bytes changed')
    new=subprocess.check_output(['git','diff',BASE,'--name-only','--diff-filter=A'],cwd=ROOT,text=True).splitlines()
    new+=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines()
    need(all(p.startswith(REL+'stage30/') or p in SCRIPTS for p in new),'out-of-scope addition')
    return BASE


def load():
    return {'approval':read(OUT/'approval.json'),'route':read(OUT/'route-input.json'),'graph':read(ROOT/REL/'stage15/interfaces-report.json'),
        'paths':read(ROOT/REL/'stage15/paths-report.json'),'stage16':read(ROOT/REL/'stage16/inputs-report.json'),'ledger28':read(ROOT/REL/'stage28/harness-ledger.json'),
        'report28':read(ROOT/REL/'stage28/report.json'),'policy28':read(ROOT/REL/'stage28/harness-policy.json'),'lock':read(ROOT/'design/grid/placements.lock.json')}


def build(data,preserve=True):
    s29data,cmap,report29=stage29_current()
    validate_approval(data['approval'],report29['mapping'])
    design=data['design'] if 'design' in data else design_positions(cmap)
    stage10,fits=verify_design(design,s29data,report29)
    rows=contact_rows(design,stage10,s29data,cmap)
    mech=s29data['mech'];need(data['graph']['DIN_pinmap']==s29data['interfaces']['DIN_pinmap'],'Stage15 DIN pin map')
    imp=impact(data['graph'],data['paths'],data['stage16'],design,mech)
    hist=historical_consumers(data['graph'],imp['edges'])
    harness=harness_preserved(data['ledger28'],data['report28'],s29data['inventory'],data['policy28'])
    study,obs=route_study(mech,data['lock'],data['route'],data['ledger28'])
    relief=rail_relief_need(study,obs)
    note='Source: stage30_din_design_integration.py from '+BASE[:12]+' inputs; geometry from stage29/contact-map.json and stage10/mechanical-report.json.'
    pages,layout=m01_pages(rows,stage10,mech,report29,note);pdf=write_pdf(pages);checks=layout_checks(layout)
    paths=imp['paths']['signal_net_paths']
    report={'status':'DESIGN_ONLY_PROVISIONAL','approval':{k:data['approval'][k] for k in ('date','decided_by','status','order_change','scope_excludes')},
        'mapping':report29['mapping'],'determinants':{s:report29['matrices'][s]['candidate_det'] for s in SIDES},'pin1_xy_mm':{s:design[s]['a1'][0][:2] for s in SIDES},
        'corners':{s:{p:design[s][p][0][:2] for p in CORNERS} for s in SIDES},'fixing_holes_xy_mm':report29['fixing_holes_xy_mm'],
        'counts':{'contacts_per_connector':96,'assigned':16,'NC':80,'changed_copper_allocations':34,'unchanged_mated_pairs':16,'changed_signal_paths':len(paths),'changed_power_paths':0,'changed_local_paths':0},
        'impact_summary':{'max_abs_edge_delta_mm':round(max(abs(e['delta_allocation_mm']) for e in imp['edges']),6),'signal_path_delta_range_mm':[min(r['delta_mm'] for r in paths),max(r['delta_mm'] for r in paths)],
            'harness_conductors_changed':0,'historical_consumers':len(hist)},
        'harness':harness,'route_study':{'scope':'J-PWR only; separate from the DIN correction','results':{c['id']:c['status'] for c in study['candidates']},
            'feasible_under_existing_conditions':[c['id'] for c in study['candidates'] if c['feasible_under_existing_conditions']],
            'minimum_change_proposal':relief,'J_SIG_proxies_cross_middle_rail':sorted(k for k,v in study['proxy_screen'].items() if k.startswith('H-J-SIG') and 'rail:middle:0' in v)},
        'm01':{'pdf_sha256':hashlib.sha256(pdf).hexdigest(),'pages':5,'layout_checks':checks,'record':'m01-record-template.json','status':'PRINT_PREPARED; M-01 NOT_RUN'},
        'decision_status':{'design_mapping':'DESIGN_ONLY_PROVISIONAL (owner 2026-10-17)','D02':'CONFLICT_REQUIRES_DECISION (unchanged)','M-01':'NOT_RUN',
            'Q-O01':'PROVISIONAL_DESIGN_ONLY; final adoption after M-01','manufacturing_and_assembly':'UNCONFIRMED','production_copper':'NOT_BOUND','canonical_CAD':'UNCHANGED',
            'route':'NO_ROUTE_ADOPTED; rail relief is a proposal'},
        'unconfirmed':s29.UNCONFIRMED+['wire MPN, bundle diameter and bend radius','measured path and cut lengths (M-09)','harness fit and anchors (M-12)'],
        'native':'NOT_RUN','physical':'NOT_RUN','external_contact':'NONE','production_CAD_changed':False,'architecture_adopted':False,
        'preservation_baseline':protected() if preserve else None}
    files=[OUT/n for n in ('approval.json','route-input.json','README.md')]+[ROOT/REL/p for p in ('stage29/contact-map.json','stage29/report.json','stage15/interfaces-report.json',
        'stage15/paths-report.json','stage16/inputs-report.json','stage28/harness-ledger.json','stage28/report.json','stage28/harness-policy.json','stage10/mechanical-report.json',
        'stage10/mechanical-input.json','stage21/inventory-input.json')]
    files+=[ROOT/'design/grid/placements.lock.json']+[ROOT/f for f in FOOTPRINTS]
    files+=[Path(__file__).with_name(n) for n in ('test_stage30_din_design_integration.py','stage29_din_column_reversal.py','stage28_din_harness.py','stage10_interfaces.py','assembly.py','check_source.py')]+[Path(__file__)]
    report['source_sha256']={str(p.relative_to(ROOT)):sha(p) for p in files}
    cmap30={'status':'DESIGN_ONLY_PROVISIONAL','mapping':report29['mapping'],'contacts':rows}
    return {'cmap':cmap30,'impact':dict(imp,historical_consumers=hist),'study':study,'report':report,'pdf':pdf,'layout':layout,'obs':obs,'mech':mech}


def outputs(b):
    imp={k:v for k,v in b['impact'].items()};study=b['study'];rel=b['report']['route_study']['minimum_change_proposal']
    return {'design-contact-map.json':dump(b['cmap']),'design-contact-map.md':render_map(b['cmap']['contacts']),'connection-impact.json':dump(imp),
        'connection-impact.md':render_impact(imp,imp['historical_consumers']),'connection-impact.svg':render_connection_svg(b['cmap']['contacts'],imp,b['mech']),
        'route-study.json':dump(study),'route-study.md':render_route(study,rel),'route-study.svg':render_route_svg(study,b['obs'],b['mech']),
        'm01-record-template.json':dump(record_template()),'report.json':dump(b['report'])}


def check_outputs(bodies,pdf):
    for name,body in bodies.items():need((OUT/name).read_text()==body,'deterministic drift '+name)
    need((OUT/'m01-print.pdf').read_bytes()==pdf,'deterministic drift m01-print.pdf')


def pdf_check(check):
    """Independent read-back of the written PDF with PyMuPDF: circle centres, bar lengths, label placement, renders."""
    import fitz
    doc=fitz.open(OUT/'m01-print.pdf');mech=read(ROOT/REL/'stage10/mechanical-report.json');stage10=s29.stage10_positions(mech)
    centre=read(ROOT/REL/'stage10/mechanical-input.json')['DIN_centre_mm'];out={'tool':'PyMuPDF '+fitz.VersionBind,'pages':doc.page_count,'sheets':{}}
    need(doc.page_count==5,'five PDF pages')
    keys=['female-stage10','female-design','male-stage10','male-design'];images={}
    for i,page in enumerate(doc):
        w,h=page.rect.width/PT,page.rect.height/PT;need(abs(w-210)<1e-3 and abs(h-297)<1e-3,'A4 page '+str(i))
        images[f'm01-sheet-{i+1}.png']=page.get_pixmap(dpi=110,colorspace=fitz.csGRAY).tobytes('png')
        if i==4:continue
        circles=[];bars=[]
        for d in page.get_drawings():
            r=d['rect']
            if sum(1 for it in d['items'] if it[0]=='c')>=4 and abs(r.width-r.height)<.01:circles.append(((r.x0+r.x1)/2/PT,(r.y0+r.y1)/2/PT,r.width/PT))
            for it in d['items']:
                if it[0]=='l':
                    L=math.dist(it[1],it[2])/PT
                    if abs(L-100)<0.05:bars.append(round(L,4))
        small=sorted((x,y) for x,y,dd in circles if abs(dd-1.0)<1e-3);big=sorted((x,y) for x,y,dd in circles if abs(dd-2.8)<1e-3)
        need(len(small)==96,'96 contact circles on sheet '+str(i+1));need(len(bars)==2 and all(abs(x-100)<1e-3 for x in bars),'two 100 mm scale bars sheet '+str(i+1))
        xs=sorted({round(x,4) for x,_ in small});ys=sorted({round(y,4) for _,y in small})
        need(len(xs)==3 and len(ys)==32,'3 rows x 32 columns sheet '+str(i+1))
        pitch=[b2-a2 for a2,b2 in zip(ys,ys[1:])]+[b2-a2 for a2,b2 in zip(xs,xs[1:])]
        need(all(abs(p-2.54)<1e-3 for p in pitch) and abs(ys[-1]-ys[0]-78.74)<1e-3,'2.54 pitch / 78.74 span sheet '+str(i+1))
        row={'contact_circles':96,'pitch_mm':[round(min(pitch),4),round(max(pitch),4)],'span_mm':round(ys[-1]-ys[0],4),'scale_bars_mm':bars}
        found=[(w[4],((w[0]+w[2])/2/PT,(w[1]+w[3])/2/PT)) for w in page.get_text('words') if w[4] in CORNERS and math.dist(((w[0]+w[2])/2/PT,(w[1]+w[3])/2/PT),(105,160))<60]
        need(sorted(l for l,_ in found)==sorted(CORNERS),'exactly one label per corner sheet '+str(i+1));words=dict(found)
        side,variant=keys[i].split('-');v=s29.COMPONENT_VIEW[side];cx,cy=centre
        # Expected sheet positions straight from the Stage10 pads and the 33-n rule, not from build().
        expect={p:(105+v[0][0]*(xy[0]-cx)+v[0][1]*(xy[1]-cy),160+v[1][0]*(xy[0]-cx)+v[1][1]*(xy[1]-cy)) for p in stage10[side] for xy in [stage10[side][p if variant=='stage10' else rev(p)][0][:2]]}
        need(all(min(math.dist(c,xy) for c in small)<1e-3 for xy in expect.values()),'PDF holes differ from the Stage10 hole set sheet '+str(i+1))
        if keys[i].startswith('female'):
            need(len(big)==2 and abs(math.dist(*big)-90)<1e-3,'fixing holes 90 mm sheet '+str(i+1));row['fixing_spacing_mm']=round(math.dist(*big),4)
            row['fixing_offset_from_row_b_mm']=round(abs(big[0][0]-xs[1]),4)
            ra=[c[0] for c in small if math.dist(c,expect['a1'])<1e-3][0]
            need(all((b[0]-xs[1])*(ra-xs[1])>0 and abs(abs(b[0]-xs[1])-0.3)<1e-3 for b in big),'fixing holes offset toward row a on sheet '+str(i+1));row['fixing_offset_side']='row a'
        else:need(not big,'male sheet without fixing holes')
        near={}
        for lab,(x,y) in words.items():
            hole=min(small,key=lambda c:math.dist(c,(x,y)));near[lab]=next(p for p,xy in expect.items() if math.dist(xy,hole)<1e-3)
        need(near=={p:p for p in CORNERS},'corner label next to the wrong hole sheet '+str(i+1));row['corner_labels_nearest_hole']=near
        out['sheets'][keys[i]]=row
    txt=''.join(p.get_text() for p in doc)
    need(txt.count('PRINT AT 100% / ACTUAL SIZE')==4 and 'RECORD SHEET' in txt,'print instruction on each pattern sheet and record sheet present')
    body=dump(out)
    if check:
        need((OUT/'pdf-check.json').read_text()==body,'pdf check drift')
        for n,v in images.items():need((OUT/'previews'/n).read_bytes()==v,'preview drift '+n)
    else:
        (OUT/'pdf-check.json').write_text(body);(OUT/'previews').mkdir(exist_ok=True)
        for n,v in images.items():(OUT/'previews'/n).write_bytes(v)


def history():
    protected()
    with tempfile.TemporaryDirectory(prefix='osc-stage30-history-') as tmp:
        checkout=Path(tmp)/'repo'
        subprocess.run(['git','worktree','add','--detach',str(checkout),BASE],cwd=ROOT,check=True,stdout=subprocess.DEVNULL)
        try:
            # The full nested chain (Stage28 -> Stage27 ...) already passed at BASE and BASE bytes are immutable; replay the Stage29 checks only.
            subprocess.run([sys.executable,'scripts/architecture278/implementation/stage29_din_column_reversal.py','--check','--check-review'],cwd=checkout,check=True)
            for flags in ([],['-O']):
                subprocess.run([sys.executable,*flags,'-m','unittest','discover','-s','scripts/architecture278/implementation','-p','test_stage29_din_column_reversal.py'],cwd=checkout,check=True)
        finally:subprocess.run(['git','worktree','remove','--force',str(checkout)],cwd=ROOT,check=True)
    print('PASS immutable Stage29 source checkpoint (generator, review binding, tests normal and -O)')


def review():
    r=read(OUT/'independent-review.json');need(r['status']=='PASS_SOURCE_REVIEW_ONLY','independent source review')
    required=set(read(OUT/'report.json')['source_sha256'])|{REL+'stage30/'+n for n in ('report.json','design-contact-map.json','design-contact-map.md','connection-impact.json',
        'connection-impact.md','connection-impact.svg','route-study.json','route-study.md','route-study.svg','m01-print.pdf','m01-record-template.json','pdf-check.json')}
    need(required<=set(r['reviewed_sha256']),'complete review bindings')
    for path,value in r['reviewed_sha256'].items():need(sha(ROOT/path)==value,'review drift '+path)


def main():
    p=argparse.ArgumentParser()
    for flag in ('check','check-history','check-review','write-pdf-check','check-pdf'):p.add_argument('--'+flag,action='store_true')
    a=p.parse_args()
    if a.check_history:history()
    b=build(load());bodies=outputs(b)
    if a.check:check_outputs(bodies,b['pdf'])
    else:
        for name,body in bodies.items():(OUT/name).write_text(body)
        (OUT/'m01-print.pdf').write_bytes(b['pdf'])
    if a.write_pdf_check or a.check_pdf:pdf_check(a.check_pdf)
    if a.check_review:review()
    r=b['report']['route_study']['results']
    print(f"PASS Stage30 source checks: 2x96 DIN design positions DESIGN_ONLY_PROVISIONAL, 34 allocations / 11 signal paths updated, harness unchanged; J-PWR routes {r}; M-01/native NOT RUN")


if __name__=='__main__':main()
