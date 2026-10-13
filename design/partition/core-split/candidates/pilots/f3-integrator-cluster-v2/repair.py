#!/usr/bin/env python3
"""One finite copper-aware placement repair; no routing, PCB writes or native."""
import argparse
from collections import Counter, defaultdict
import copy
import gzip
import importlib.util
import json
import math
from pathlib import Path
import resource
import time

import shapely
from shapely.geometry import Polygon, Point, LineString, box
from shapely.ops import unary_union
from shapely.strtree import STRtree

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[5]
CONTRACT_SHA='da96e8a60bd8232116a067a6cf1f3fffee713791b952090df7db91e0221312b9'
spec=importlib.util.spec_from_file_location('pose_v1',HERE.parent/'f3-integrator-cluster-v1/check_pose.py')
v1=importlib.util.module_from_spec(spec); spec.loader.exec_module(v1)


def polygon(pad):
    return Polygon([(x/1e6,y/1e6) for x,y in pad['poly']])


def expanded_bounds(g,margin):
    a,b,c,d=g.bounds
    return box(a-margin,b-margin,c+margin,d+margin)


def preserved_foreign(row,pad,faces,reconstruction_ids):
    return (row['uuid'] not in reconstruction_ids and row['net_token']!=pad['net']
            and bool(set(pad['layers']).intersection(faces)))


def pose_domain(row,contract):
    """A finite, deterministic domain; no adaptive seeds, widening or retries."""
    found={}
    for seed in (row['old_physical_pose'],row['candidate_physical_pose']):
        for dx in contract['domain']['translation_offsets_mm']:
            for dy in contract['domain']['translation_offsets_mm']:
                for angle in contract['domain']['orientations_deg']:
                    key=(round((seed['x_mm']+dx)*1e6),round((seed['y_mm']+dy)*1e6),angle)
                    found[key]=dict(x_mm=key[0]/1e6,y_mm=key[1]/1e6,kicad_orientation_deg=angle,side=seed['side'])
    return [found[k] for k in sorted(found)]


def load_copper(index,text,layers):
    rows=[]; gs=[]; radii=[]; faces=[]; endpoints=[]
    for row in index:
        a,b=row['source_span'];block=text[a:b]
        v1.require(v1.digest(block.encode())==row['sha256'],'original object hash drift '+row['uuid'])
        if row['kind']=='segment':
            pts=[list(map(float,v1.scalar(block,t).split())) for t in ('start','end')]
            g=LineString(pts);radius=float(v1.scalar(block,'width'))/2;face=[v1.scalar(block,'layer')]
        elif row['kind']=='via':
            pts=[list(map(float,v1.scalar(block,'at').split()))]
            g=Point(pts[0]);radius=float(v1.scalar(block,'size'))/2
            v1.require(v1.scalar(block,'layers')=='F.Cu" "B.Cu','unsupported via layers')
            face=layers
            row=row|{'drill_mm':float(v1.scalar(block,'drill'))}
        else:
            v1.require(row['kind'] in ('zone','rule_area'),'unsupported copper type')
            continue
        rows.append(row);gs.append(g);radii.append(radius);faces.append(face);endpoints.append(pts)
    return rows,gs,radii,faces,endpoints


class BoundStop(Exception):
    pass


class Screen:
    def __init__(self,contract,board,original,copper,start):
        self.contract=contract;self.board=board;self.original=original;self.start=start
        self.rows,self.cg,self.cr,self.cl,self.ends=copper
        self.ct=STRtree(self.cg);self.max_radius=max(self.cr)
        self.replay={r['uuid'] for r in contract['copper_classification'] if r['classification']=='EXPLICIT_CANDIDATE_RECONSTRUCTION_OBLIGATION'}
        self.movable=set(contract['movable_refs'])
        self.placements={p['ref']:p for p in board['placements']}
        self.old={r:dict(x_mm=p['x_mm']+100,y_mm=p['y_mm']+50,kicad_orientation_deg=p['kicad_orientation_deg'],side=p['side']) for r,p in self.placements.items()}
        self.fixed_refs=sorted(set(self.placements)-self.movable)
        self.fg=[v1.shape(self.placements[r]) for r in self.fixed_refs];self.ft=STRtree(self.fg)
        self.pads=defaultdict(list)
        for p in original['pads']:self.pads[p['ref']].append(p)
        self.fixed_pads=[p for p in original['pads'] if p['ref'] not in self.movable]
        self.pg=[polygon(p) for p in self.fixed_pads];self.pt=STRtree(self.pg)
        self.drills=[(p,Point(p['xy'][0]/1e6,p['xy'][1]/1e6),p['drill']/2e6) for p in self.fixed_pads if p['drill']]
        self.dt=STRtree([g for _,g,_ in self.drills]);self.max_drill=max((r for _,_,r in self.drills),default=0)
        self.reserves=[]
        for row in board['measurement']['faces']['B.Cu']['reservation_polygons_mm']:
            self.reserves.append((row['id'],unary_union([Polygon([(x+100,y+50) for x,y in poly]) for poly in row['polygons']])))
        self.rt=STRtree([g for _,g in self.reserves])
        self.outline=Polygon([(x+100,y+50) for x,y in board['outline_mm']]).buffer(-.30,join_style=2)
        part=v1.read(ROOT/'design/partition/partition.json')
        self.holes=[(r['header_id'],Point(r['center_mm'][0]+100,r['center_mm'][1]+50),r['diameter_mm']/2) for r in part['K_service_apertures']]
        self.copper_pair_checks=0;self.pose_checks=0;self.joint_checks=0
        self.bypass={p['ref']:p['decouples_ref'] for p in board['source_parts'] if p['decouples_ref'] and p['ref'] in self.movable}
        self.bypass_max={c:math.dist([self.old[c][k] for k in ('x_mm','y_mm')],[self.old[u][k] for k in ('x_mm','y_mm')]) for c,u in self.bypass.items()}

    def limits(self):
        if time.monotonic()-self.start>=self.contract['domain']['soft_wall_seconds']:
            raise BoundStop('SOFT_WALL_LIMIT')

    def pack(self,ref,pose):
        shape=v1.shape(self.placements[ref],{'old_physical_pose':self.old[ref],'candidate_physical_pose':pose})
        pads=[v1.transform_pad(p,self.old[ref],pose) for p in self.pads[ref]]
        return {'ref':ref,'pose':pose,'shape':shape,'pads':pads,'pad_shapes':[polygon(p) for p in pads]}

    def screen(self,ref,pose):
        self.limits();self.pose_checks+=1
        v1.require(self.pose_checks<=self.contract['domain']['max_distinct_pose_screens'],'pose domain cap exceeded')
        a=self.pack(ref,pose);g=a['shape']
        if not self.outline.covers(g):return None,{'gate':'EDGE_ALLOCATION','outside_mm2':g.difference(self.outline).area}
        for j in sorted(map(int,self.ft.query(expanded_bounds(g,.35)))):
            s=self.fixed_refs[j]
            if self.placements[s]['side']!=pose['side']:continue
            distance=g.distance(self.fg[j]);overlap=g.intersection(self.fg[j]).area
            if distance<.35-1e-7 or overlap>1e-7:
                return None,{'gate':'FIXED_COURTYARD','ref':s,'gap_mm':distance,'overlap_mm2':overlap}
        for j in sorted(map(int,self.rt.query(g))):
            name,r=self.reserves[j];area=g.intersection(r).area
            if area>1e-7:return None,{'gate':'FIXED_RESERVATION','reservation':name,'overlap_mm2':area}
        for name,center,radius in self.holes:
            margin=g.distance(center)-radius
            if margin< -1e-7:return None,{'gate':'SERVICE_HOLE','id':name,'margin_mm':margin}
        for pad,pg in zip(a['pads'],a['pad_shapes']):
            for j in sorted(map(int,self.dt.query(expanded_bounds(pg,self.max_drill+.25)))):
                drill,center,radius=self.drills[j];gap=pg.distance(center)-radius
                if gap<.25-1e-7:return None,{'gate':'FIXED_DRILL_TO_SMD','pad':pad['pad'],'obstacle_uuid':drill['uuid'],'gap_mm':gap,'required_mm':.25}
            for j in sorted(map(int,self.pt.query(expanded_bounds(pg,.25)))):
                other=self.fixed_pads[j]
                if not set(pad['layers']).intersection(other['layers']) or pad['net']==other['net']:continue
                gap=pg.distance(self.pg[j])
                if gap<.25-1e-7:return None,{'gate':'FIXED_FOREIGN_PAD','pad':pad['pad'],'obstacle_uuid':other['uuid'],'obstacle_ref':other['ref'],'gap_mm':gap}
            for j in sorted(map(int,self.ct.query(expanded_bounds(pg,self.max_radius+.25)))):
                other=self.rows[j]
                if other['kind']=='via':
                    gap=pg.distance(self.cg[j])-self.cr[j]
                    if gap<1e-6:return None,{'gate':'PRESERVED_VIA_SMD','pad':pad['pad'],'obstacle_uuid':other['uuid'],'net':other['net_token'],'annulus_gap_mm':gap,'drill_mm':other['drill_mm'],'required_margin_mm':1e-6}
                if not preserved_foreign(other,pad,self.cl[j],self.replay):continue
                self.copper_pair_checks+=1
                gap=pg.distance(self.cg[j])-self.cr[j]
                if gap<.25-1e-7:return None,{'gate':'PRESERVED_FOREIGN_COPPER','pad':pad['pad'],'obstacle_uuid':other['uuid'],'net':other['net_token'],'gap_mm':gap,'object_sha256':other['sha256']}
        return a,{'gate':'INDIVIDUAL_SCREEN_PASS','meaning':'Other movable refs and exactly29 reconstruction obligations temporarily absent; joint fit/continuity not established'}

    def compatible(self,a,b):
        if a['shape'].distance(b['shape'])<.35-1e-7 or a['shape'].intersection(b['shape']).area>1e-7:return False
        for c,u in self.bypass.items():
            if {c,u}=={a['ref'],b['ref']}:
                distance=math.dist([a['pose'][k] for k in ('x_mm','y_mm')],[b['pose'][k] for k in ('x_mm','y_mm')])
                if distance>self.bypass_max[c]+1e-7:return False
        for p,pg in zip(a['pads'],a['pad_shapes']):
            for q,qg in zip(b['pads'],b['pad_shapes']):
                if p['net']!=q['net'] and set(p['layers']).intersection(q['layers']) and pg.distance(qg)<.25-1e-7:return False
        return True

    def choose(self,domains):
        order=sorted(domains,key=lambda r:(len(domains[r]),r))
        def visit(i,selected):
            self.limits()
            if i==len(order):return selected
            for a in domains[order[i]]:
                if self.joint_checks>=self.contract['domain']['max_joint_assignments']:raise BoundStop('JOINT_ASSIGNMENT_CAP')
                self.joint_checks+=1
                if all(self.compatible(a,b) for b in selected.values()):
                    out=visit(i+1,selected|{a['ref']:a})
                    if out:return out
            return None
        return visit(0,{})

    def same_net_contacts(self,i):
        contacts=[]
        for j in sorted(map(int,self.ct.query(expanded_bounds(self.cg[i],self.max_radius+self.cr[i])))):
            if i==j or self.rows[j]['net_token']!=self.rows[i]['net_token'] or not set(self.cl[i]).intersection(self.cl[j]):continue
            gap=self.cg[i].distance(self.cg[j])-self.cr[i]-self.cr[j]
            if gap<=1e-7:
                contacts.append({'uuid':self.rows[j]['uuid'],'sha256':self.rows[j]['sha256'],'kind':self.rows[j]['kind'],
                    'layers':self.cl[j],'diameter_or_width_mm':2*self.cr[j],'drill_mm':self.rows[j].get('drill_mm'),
                    'full_object_gap_mm':gap,'disposition':'RECONSTRUCTION_OBLIGATION' if self.rows[j]['uuid'] in self.replay else 'PRESERVED_IN_PLACE'})
        return contacts

    def reconstruction_plan(self):
        lookup={r['uuid']:i for i,r in enumerate(self.rows)}
        original_pads={p['uuid']:p for p in self.original['pads']}
        pad_rows=list(original_pads.values());pad_shapes=[polygon(p) for p in pad_rows];pad_tree=STRtree(pad_shapes)
        out=[]
        for row in self.contract['copper_classification']:
            item=copy.deepcopy(row)
            i=lookup[row['uuid']]
            item['original_geometry']={'endpoints_or_center_mm':self.ends[i],'diameter_or_width_mm':2*self.cr[i],
                                       'layers':self.cl[i],'drill_mm':self.rows[i].get('drill_mm')}
            if row['classification']=='EXPLICIT_CANDIDATE_RECONSTRUCTION_OBLIGATION':
                ports=[]
                for xy in self.ends[i]:
                    at=Point(xy);adjacent=[]
                    for j in sorted(map(int,self.ct.query(expanded_bounds(at,self.max_radius+self.cr[i])))):
                        if i==j or self.rows[j]['net_token']!=row['net_token'] or not set(self.cl[i]).intersection(self.cl[j]):continue
                        if at.distance(self.cg[j])<=self.cr[i]+self.cr[j]+1e-7:
                            adjacent.append({'uuid':self.rows[j]['uuid'],'sha256':self.rows[j]['sha256'],
                                             'disposition':'RECONSTRUCTION_OBLIGATION' if self.rows[j]['uuid'] in self.replay else 'PRESERVED_IN_PLACE'})
                    pad_contacts=[p['pad_uuid'] for p in row['original_contacts']
                                  if polygon(original_pads[p['pad_uuid']]).distance(at)<=self.cr[i]+1e-7]
                    ports.append({'xy_mm':xy,'layers':self.cl[i],'same_net_source_neighbors':adjacent,
                                  'contacted_original_pad_uuids':pad_contacts,
                                  'role':'OLD_MOVED_PAD_CONTACT_AND_ANY_LISTED_COPPER_BRANCHES' if pad_contacts else 'ORIGINAL_COPPER_SPLICE_OR_EXPOSED_ENDPOINT'})
                item['continuity_ports']=ports
                item['full_object_same_net_contacts']=self.same_net_contacts(i)
                item['full_object_original_fixture_pad_contacts']=[]
                for j in sorted(map(int,pad_tree.query(expanded_bounds(self.cg[i],self.cr[i])))):
                    p=pad_rows[j]
                    if p['net']==row['net_token'] and set(p['layers']).intersection(self.cl[i]) and pad_shapes[j].distance(self.cg[i])<=self.cr[i]+1e-7:
                        item['full_object_original_fixture_pad_contacts'].append({'uuid':p['uuid'],'ref':p['ref'],'pad':p['pad'],'net':p['net'],'original_xy_nm':p['xy'],'moved_scope':p['ref'] in self.movable})
                item['reconstruction_requirement']='Reconnect every listed original pad UUID at its selected pose and preserve connection to every listed endpoint/neighbor on this exact net and layer. If old endpoint lies inside a moved-pad contact it is a historical contact locator, not a required obsolete terminal. Any wider reconstruction requires explicit object classification; no silent cuts.'
                item['native_group_gate']='Original fixture pad contacts are source evidence only. Full accepted-board native connected groups and zone-mediated contacts must also be preserved and freshly verified before acceptance.'
                item['continuity_status']='NOT RECONSTRUCTED; NOT VERIFIED CONNECTED'
            out.append(item)
        return out


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--input-dump',required=True,type=Path);p.add_argument('--output',required=True,type=Path);args=p.parse_args()
    v1.require(not args.output.exists(),'fresh output required; no retries/overwrite')
    raw=(HERE/'repair-contract.json').read_bytes();v1.require(v1.digest(raw)==CONTRACT_SHA,'repair contract changed')
    c=json.loads(raw);v1.require(shapely.__version__=='2.1.2' and shapely.geos_version_string=='3.13.1','runtime drift')
    for name,h in c['input_sha256'].items():v1.require(v1.digest((ROOT/name).read_bytes())==h,'input drift '+name)
    v1.require(v1.digest(args.input_dump.read_bytes())==c['original_dump_sha256'],'original dump drift')
    b=v1.read(ROOT/'design/partition/core-split/candidates/two.json')['boards']['two-A'];original=v1.read(args.input_dump)
    v1.require(v1.closure(b,{'C2312','U2306','U2312'})==c['closure_refs'],'sensitive/bypass closure drift')
    v1.require('U2306' not in c['movable_refs'] and set(c['movable_refs'])<=set(c['closure_refs']),'scope or fixed anchor drift')
    prior=v1.read(HERE.parent/'f3-integrator-cluster-v1/pose-epoch.json');seeds={r['ref']:r for r in prior['poses']}
    index=[json.loads(x) for x in gzip.open(ROOT/'design/partition/core-split/candidates/copper-index.jsonl.gz','rt')]
    start=time.monotonic();screen=Screen(c,b,original,load_copper(index,(ROOT/'boards/osc-core/osc-core.kicad_pcb').read_text(),original['layers']),start)
    args.output.mkdir(parents=True)
    receipt={'status':'STARTED_ONE_EPOCH','source_sha256':v1.digest(Path(__file__).read_bytes()),'contract_sha256':CONTRACT_SHA,'retry_policy':'Do not restart this epoch when STARTED receipt exists without terminal result'}
    (args.output/'execution-start.json').write_text(json.dumps(receipt,indent=2)+'\n')
    records=[];domains={};counts={};selected=None;failure=None
    goal=next(p for p in original['pads'] if p['ref']=='U2306' and p['pad']=='5')['xy']
    def score(a):
        target=next((p for p in a['pads'] if (p['ref'],p['pad']) in [('C2312','1'),('U2312','12')]),None)
        old=screen.old[a['ref']]
        return ((math.dist(target['xy'],goal)/1e6 if target else math.dist([a['pose'][k] for k in ('x_mm','y_mm')],[old[k] for k in ('x_mm','y_mm')])),a['pose']['x_mm'],a['pose']['y_mm'],a['pose']['kicad_orientation_deg'])
    try:
        for ref in c['movable_refs']:
            domains[ref]=[];counts[ref]=Counter()
            for pose in pose_domain(seeds[ref],c):
                a,why=screen.screen(ref,pose);records.append({'ref':ref,'pose':pose,'first_refusal_or_pass':why});counts[ref][why['gate']]+=1
                if a:domains[ref].append(a)
            domains[ref].sort(key=score)
        if all(domains.values()):selected=screen.choose(domains)
    except BoundStop as exc:failure=str(exc)
    empty=[r for r in c['movable_refs'] if r in domains and not domains[r]]
    domain_complete=screen.pose_checks==sum(len(pose_domain(seeds[r],c)) for r in c['movable_refs'])
    complete=domain_complete and failure is None
    status='GEOMETRY_SCREENED_CANDIDATE; CONTINUITY_PENDING' if selected else 'INFEASIBLE_IN_SEALED_FINITE_REPAIR_DOMAIN' if complete else 'BOUNDED_CHECK_INCOMPLETE'
    plan=screen.reconstruction_plan()
    prior_copper=v1.read(HERE.parent/'f3-integrator-cluster-v1/evidence/copper-accounting.json')
    categories={r['uuid']:r['classification'] for r in c['copper_classification']}
    pairs=[r|{'object_classification':categories[r['copper_uuid']]} for r in prior_copper['candidate_pad_foreign_copper_conflicts']]
    result={'status':status,'source_sha256':receipt['source_sha256'],'contract_sha256':CONTRACT_SHA,
        'independent_pose_domains_complete':domain_complete,'first_refusal_counts':{r:dict(x) for r,x in counts.items()},
        'individual_survivors':{r:len(x) for r,x in domains.items()},'empty_domains':empty,'pose_screens':screen.pose_checks,
        'joint_assignment_checks':screen.joint_checks,'exact_foreign_copper_pair_checks':screen.copper_pair_checks,'bound_stop':failure,
        'scope':'Only the sealed finite repair domain and exact29-reconstruction relaxation. Empty optimistic per-ref domain rules out joint placement there; no continuous/global infeasibility claim.',
        'selected_candidate':selected is not None,'complete_routes':False,'continuity_verified':False,'native_executed':False,'adopted':False,
        'full_warning_DRC_parity_fill':'NOT RUN; source-only','rails':'Original U2309 positive/negative own-pad blockers unchanged',
        'accepted_objects_authenticated':len(index),'accepted_segments_vias_screened':len(screen.rows),
        'all_original_files_unchanged':True,'prior_conflict_pairs':len(pairs),'prior_conflict_unique_objects':len({x['copper_uuid'] for x in pairs}),
        'prior_pairs_absent_from_fixture':sum(not x['present_in_original_candidate_fixture'] for x in pairs),
        'reconstruction_objects':len(screen.replay),'direct_objects_preserved_in_place':len(categories)-len(screen.replay),'verified_group_transforms':0,
        'elapsed_seconds':time.monotonic()-start,'peak_memory_kib_linux':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    if selected:
        poses=[]
        for ref in c['closure_refs']:
            new=selected[ref]['pose'] if ref in selected else screen.old[ref]
            poses.append({'ref':ref,'old_physical_pose':screen.old[ref],'candidate_physical_pose':new,'moved':new!=screen.old[ref]})
        # Recheck all original copper: conflicts with the29 exact replay obligations
        # remain pending reconstruction; any other collision invalidates selection.
        allpads=[v1.transform_pad(p,screen.old[p['ref']],selected[p['ref']]['pose']) if p['ref'] in selected else copy.deepcopy(p) for p in original['pads']]
        account=v1.copper_accounting(b,original,allpads,set(selected),index,(ROOT/'boards/osc-core/osc-core.kicad_pcb').read_text())
        unresolved=[r for r in account['candidate_pad_foreign_copper_conflicts'] if r['copper_uuid'] not in screen.replay]
        v1.require(not unresolved,'selection has unclassified retained copper conflict')
        (args.output/'candidate-pose.json').write_text(json.dumps({'status':status,'poses':poses,'preserved_copper_conflicts':0,'reconstruction_still_pending':True},indent=2)+'\n')
        (args.output/'candidate-copper-accounting.json').write_text(json.dumps(account,indent=2)+'\n')
    for name,value in [('result.json',result),('object-dispositions.json',plan),('prior-conflict-reconciliation.json',pairs)]:
        (args.output/name).write_text(json.dumps(value,indent=2)+'\n')
    data=b''.join(v1.canonical(r)+b'\n' for r in records)
    (args.output/'pose-screens.jsonl.gz').write_bytes(gzip.compress(data,mtime=0))
    for name,h in c['input_sha256'].items():v1.require(v1.digest((ROOT/name).read_bytes())==h,'input mutated '+name)
    v1.require(v1.digest(args.input_dump.read_bytes())==c['original_dump_sha256'],'dump mutated')
    print(json.dumps(result))


if __name__=='__main__':main()
