#!/usr/bin/env python3
"""Exactly one approved rigid source census; no PCB writes, optimizer or native."""
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import importlib.util
import json
import math
import os
from pathlib import Path
import resource
import signal
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
PLAN = HERE.parent.parent/'planning/f3-next-approach'
DELTA = (71.25, -85.85)
DUMP_SHA = '2dae7737731cb9d6f230e3f61848d01f6939fd7e7e6b56d3ed23f74ea8684807'


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path):
    return json.loads(path.read_text())


def write(out, name, obj):
    raw = (json.dumps(obj, sort_keys=True, separators=(',', ':'))+'\n').encode()
    temporary=out/(name+'.tmp')
    temporary.write_bytes(gzip.compress(raw,mtime=0) if name.endswith('.gz') else raw)
    temporary.replace(out/name)


def identity(row):
    return ':'.join(map(str, row['source_span']))+':'+row['sha256']


def verify_seals(seals, root=ROOT):
    for path, expected in seals.items():
        assert sha((root/path).read_bytes()) == expected, path


def contact_component_ok(group, bad, contacts):
    return any(contacts[i]['original_pad_contacts'] for i in group) and not bool(group & bad)


def hole_margins(distance, h, q):
    drill_gap = distance-(h['radius']+q['radius'])
    annulus_gaps = [distance-h['annulus']-q['radius']] if h['annulus'] else []
    if q['annulus']:
        annulus_gaps.append(distance-q['annulus']-h['radius'])
    gap = min([drill_gap]+annulus_gaps)
    return drill_gap, gap, gap < .25-1e-7


def child(args):
    resource.setrlimit(resource.RLIMIT_AS, (2*1024**3, 2*1024**3))
    started = time.monotonic()
    signal.signal(signal.SIGALRM, lambda *_: (_ for _ in ()).throw(TimeoutError('180-second bound')))
    signal.setitimer(signal.ITIMER_REAL, 180)
    # Import numerical libraries only after the memory and wall limits are active.
    from shapely import affinity
    from shapely.geometry import Point, Polygon, box
    from shapely.ops import unary_union
    from shapely.strtree import STRtree
    spec = importlib.util.spec_from_file_location('repair', HERE.parent/'f3-integrator-cluster-v2/repair.py')
    r = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(r)
    v = r.v1
    assert r.shapely.__version__ == '2.1.2'
    out = args.output
    stage = 'INPUTS'
    summary = {'status':'INCOMPLETE', 'stage':stage, 'authored_transforms':1,
               'pose_searches':0, 'native_calls':0, 'canonical_edits':0}
    def checkpoint(name, obj):
        write(out, name, obj)
        summary['stage'] = name
        write(out, 'progress.json', summary)
    try:
        seals = read(HERE/'input-seals.json')
        verify_seals(seals)
        join=read(HERE/'full-footprint-source-join.json')
        artifact=read(HERE/'retained-artifact.json')
        assert join['all_full_footprint_bytes_equal'] and join['full_footprint_count']==3793
        assert join['source_sha256']==seals['boards/osc-core/osc-core.kicad_pcb']
        assert join['settled_sha256']==artifact['settled_board_sha256']
        assert artifact['dump_sha256']==DUMP_SHA
        checkpoint('full-source-authentication.json', {'footprints':join,'artifact':artifact})
        assert sha(args.dump.read_bytes()) == DUMP_SHA
        original = read(args.dump)
        assert original['board_sha256'] == 'b9f5ca13f83c7ffdbe5836fd271e7c1099e04b901ca1798a7be06f025bd02d66'
        assert len(original['pads']) == 13406
        data = read(ROOT/'design/partition/core-split/candidates/two.json')
        b = data['boards']['two-A']
        boundary = read(PLAN/'whole-f3-boundary.json')
        refs = set(boundary['refs'])
        assert len(refs)==171 and refs=={p['ref'] for p in b['source_parts'] if p['module']=='F3'}
        classes = {n['net_token']:n['classification'] for n in boundary['nets']}
        internal = {n for n,c in classes.items() if c=='GROUP_INTERNAL'}
        places = {p['ref']:p for p in b['placements']}
        fixed_candidate_refs = set(places)-refs
        poses = {}
        for ref in sorted(refs):
            p = places[ref]
            old = dict(x_mm=p['x_mm']+100,y_mm=p['y_mm']+50,
                       kicad_orientation_deg=p['kicad_orientation_deg'],side=p['side'])
            new = old | {'x_mm':old['x_mm']+DELTA[0],'y_mm':old['y_mm']+DELTA[1]}
            poses[ref] = {'ref':ref,'old_physical_pose':old,'candidate_physical_pose':new,'moved':True}
        pads = original['pads']
        assert len({p['uuid'] for p in pads})==len(pads)
        pg = [r.polygon(p) for p in pads]
        assert all(g.is_valid and (not g.is_empty or (p['npth'] and not p['layers'])) for p,g in zip(pads,pg))
        pt = STRtree(pg)
        moved_pads = [i for i,p in enumerate(pads) if p['ref'] in refs]
        assert {pads[i]['ref'] for i in moved_pads}==refs
        fixture = read(ROOT/'design/partition/core-split/candidates/pilots/generated/f3-two-a-c2312-breakout-v1-reviewed/original-dump.json')
        full_by_uuid = {p['uuid']:p for p in pads}
        compare_fields = ('uuid','ref','pad','net','xy','layers','poly','drill','npth')
        assert all(all(p[k]==full_by_uuid[p['uuid']][k] for k in compare_fields) for p in fixture['pads'])
        checkpoint('source-pad-join.json', {'full_pads':len(pads),'candidate_fixture_pads':len(fixture['pads']),
            'all_fixture_pad_geometry_matches_full':True,'moved_pad_count':len(moved_pads),
            'full_dump_sha256':DUMP_SHA,'source_footprint_join':'full-source-authentication.json',
            'native_scope':'Retained native polygons only, no fresh measurement; native polygon approximation retained.'})
        del fixture
        text = (ROOT/'boards/osc-core/osc-core.kicad_pcb').read_text()
        index = [json.loads(x) for x in gzip.open(ROOT/'design/partition/core-split/candidates/copper-index.jsonl.gz','rt')]
        for row in index:
            a,z = row['source_span']
            assert sha(text[a:z].encode())==row['sha256']
        rows,cg,cr,cl,ends = r.load_copper(index,text,original['layers'])
        assert len(index)==133902 and len(rows)==133551
        keys = [identity(row) for row in rows]
        assert len(set(keys))==len(keys)
        ct = STRtree(cg)
        maxrad = max(cr)
        chosen = {i for i,row in enumerate(rows) if row['net_token'] in internal}
        assert len(chosen)==4491
        zones = [row for row in index if row['kind']=='zone']
        same_net_zones = {row['net_token'] for row in zones}
        contacts = {}
        adjacency = defaultdict(set)
        bad = set()
        def hits(tree,g,margin):
            return sorted(map(int,tree.query(r.expanded_bounds(g,margin))))
        def same_layer(a,z):
            return bool(set(a).intersection(z))
        for i in sorted(chosen):
            row = rows[i]
            neighbors = []
            pad_contacts = []
            for j in hits(ct,cg[i],cr[i]+maxrad):
                if i==j or row['net_token']!=rows[j]['net_token'] or not same_layer(cl[i],cl[j]):continue
                gap = cg[i].distance(cg[j])-cr[i]-cr[j]
                if gap<=1e-7:
                    neighbors.append({'object_key':keys[j],'gap_mm':gap,'in_internal_inventory':j in chosen})
                    adjacency[i].add(j)
                    if j not in chosen:bad.add(i)
            for j in hits(pt,cg[i],cr[i]):
                p=pads[j]
                if p['net']!=row['net_token'] or not same_layer(p['layers'],cl[i]):continue
                gap=pg[j].distance(cg[i])-cr[i]
                if gap<=1e-7:
                    pad_contacts.append({'uuid':p['uuid'],'ref':p['ref'],'pad':p['pad'],'gap_mm':gap})
                    if p['ref'] not in refs:bad.add(i)
            if row['net_token'] in same_net_zones:bad.add(i)
            contacts[i]={'same_net_copper':neighbors,'original_pad_contacts':pad_contacts}
        seen=set();components=[];eligible=set();component_of={}
        for seed in sorted(chosen):
            if seed in seen:continue
            todo=[seed];group=set()
            while todo:
                i=todo.pop()
                if i in group:continue
                group.add(i);todo.extend(adjacency[i]&chosen-group)
            seen |= group
            has_pad=any(contacts[i]['original_pad_contacts'] for i in group)
            ok=contact_component_ok(group,bad,contacts)
            if ok:eligible|=group
            n=len(components)
            component_of.update({i:n for i in group})
            components.append({'id':n,'objects':[keys[i] for i in sorted(group)],
                'has_group_pad_contact':has_pad,'external_or_zone_dependency':bool(group&bad),
                'source_contact_closed':ok,'native_acceptance':False})
        inventory=[]
        for i in sorted(chosen):
            inventory.append(rows[i]|{'object_key':keys[i],'component':component_of[i],
                'original_geometry':{'points_mm':ends[i],'radius_mm':cr[i],'layers':cl[i]},
                'contacts':contacts[i],
                'proposal_disposition':'RIGID_SOURCE_CONTACT_CLOSED_TRANSFORM' if i in eligible else 'PRESERVED_IN_PLACE_BLOCKED_RECONSTRUCTION',
                'actual_canonical_disposition':'PRESERVED_UNCHANGED',
                'remaining_gate':'Destination clearance, complete zones and fresh native connectivity/eligibility are not established by contact closure.'})
        checkpoint('internal-copper-classification.json.gz',inventory)
        checkpoint('internal-source-components.json.gz',components)
        # Only source-contact-closed components follow the group in this disposable geometry.
        ng=[affinity.translate(g,*DELTA) if i in eligible else g for i,g in enumerate(cg)]
        nt=STRtree(ng)
        npg=[affinity.translate(g,*DELTA) if p['ref'] in refs else g for p,g in zip(pads,pg)]
        npt=STRtree(npg)
        npads=[v.transform_pad(p,poses[p['ref']]['old_physical_pose'],poses[p['ref']]['candidate_physical_pose']) if p['ref'] in refs else p for p in pads]
        checkpoint('selected-poses.json',poses)
        checkpoint('selected-pads.json.gz',[npads[i] for i in moved_pads])
        checkpoint('transformed-copper.json.gz',[{'object_key':keys[i],
            'points_mm':[[x+DELTA[0],y+DELTA[1]] for x,y in ends[i]],
            'layers':cl[i],'radius_mm':cr[i],'net_token':rows[i]['net_token']} for i in sorted(eligible)])
        placement=v.placement_checks(b,poses,read(ROOT/'design/partition/partition.json'))
        for q in placement['same_face_gap_violations']:
            q['origin']='INTRINSIC_PRESERVED' if set(q['refs'])<=refs else 'LOCATION_DEPENDENT'
        placement['bypass_distances']=[{'ref':p['ref'],'ic':p['decouples_ref'],
            'old_mm':math.dist([places[p['ref']][k] for k in ('x_mm','y_mm')],[places[p['decouples_ref']][k] for k in ('x_mm','y_mm')]),
            'new_mm':math.dist([poses[p['ref']]['candidate_physical_pose'][k] for k in ('x_mm','y_mm')],[poses[p['decouples_ref']]['candidate_physical_pose'][k] for k in ('x_mm','y_mm')])}
            for p in b['source_parts'] if p['ref'] in refs and p['decouples_ref']]
        assert all(abs(x['old_mm']-x['new_mm'])<1e-7 for x in placement['bypass_distances'])
        checkpoint('placement.json',placement)
        checkpoint('selected-courtyards.json',[{'ref':ref,'side':places[ref]['side'],
            'physical_polygons_mm':[[[x+100+DELTA[0],y+50+DELTA[1]] for x,y in poly] for poly in places[ref]['courtyard_polygons_mm']]} for ref in sorted(refs)])
        def ownership(row):
            n=row['net_token'];owners=data['net_owners'].get(n,[])
            return ('SHARED_RAIL' if n in ('AGND','+12V','-12V','+5V') else
                    'TWO_A' if owners==['A'] else 'OTHER_CANDIDATE' if owners and 'A' not in owners else 'UNRESOLVED')
        def pad_owner(p):
            return 'F3_MOVED' if p['ref'] in refs else 'FIXED_TWO_A' if p['ref'] in fixed_candidate_refs else 'OTHER_SOURCE_FOOTPRINT'
        pad_pairs=[];copper_pad=[];boundary_contacts=[];new_contacts=[];drill_pairs=[]
        drill_ids=[i for i,p in enumerate(pads) if p['drill']]
        drill_geoms=[Point(npads[i]['xy'][0]/1e6,npads[i]['xy'][1]/1e6) for i in drill_ids]
        dt=STRtree(drill_geoms);maxdrill=max((pads[i]['drill']/2e6 for i in drill_ids),default=0)
        for i in moved_pads:
            p=pads[i];g=npg[i]
            for j in hits(npt,g,.25):
                q=pads[j]
                if i==j or (q['ref'] in refs and j<i) or p['net']==q['net'] or not same_layer(p['layers'],q['layers']):continue
                gap=g.distance(npg[j])
                if gap<.25-1e-7:
                    pad_pairs.append({'pad_uuid':p['uuid'],'ref':p['ref'],'pad':p['pad'],'other_uuid':q['uuid'],'other_ref':q['ref'],'other_pad':q['pad'],
                        'other_scope':pad_owner(q),'gap_mm':gap,'old_gap_mm':pg[i].distance(pg[j]),
                        'origin':'INTRINSIC_PRESERVED' if q['ref'] in refs else 'LOCATION_DEPENDENT'})
            for z in hits(dt,g,maxdrill+.25):
                j=drill_ids[z]
                if j==i:continue
                gap=g.distance(drill_geoms[z])-pads[j]['drill']/2e6
                if gap<.25-1e-7:drill_pairs.append({'pad_uuid':p['uuid'],'drill_uuid':pads[j]['uuid'],'other_scope':pad_owner(pads[j]),'gap_mm':gap})
            for j in hits(ct,pg[i],maxrad):
                if p['net']==rows[j]['net_token'] and same_layer(p['layers'],cl[j]) and pg[i].distance(cg[j])-cr[j]<=1e-7:
                    if j not in eligible:
                        boundary_contacts.append({'pad_uuid':p['uuid'],'ref':p['ref'],'pad':p['pad'],'net_token':p['net'],'net_class':classes[p['net']],
                            'fixed_object_key':keys[j],'source_pad_xy_nm':p['xy'],'destination_pad_xy_nm':npads[i]['xy'],
                            'destination_gap_mm':g.distance(ng[j])-cr[j],'obligation':'Reconnect this exact fixed object/contact to the moved pad; no cut or whole-net edit permission.'})
            for j in hits(nt,g,maxrad+.25):
                if not same_layer(p['layers'],cl[j]):continue
                gap=g.distance(ng[j])-cr[j]
                tags=[]
                if p['net']!=rows[j]['net_token'] and gap<.25-1e-7:tags.append('FOREIGN_COPPER_CLEARANCE')
                if rows[j]['kind']=='via' and not p['drill'] and gap<1e-6:tags.append('VIA_SMD_ANNULUS_EXCLUSION')
                if tags:copper_pad.append({'pad_uuid':p['uuid'],'ref':p['ref'],'pad':p['pad'],'object_key':keys[j],'object_scope':ownership(rows[j]),'gap_mm':gap,'reasons':tags,
                    'origin':'INTRINSIC_PRESERVED' if j in eligible else 'LOCATION_DEPENDENT'})
                if p['net']==rows[j]['net_token'] and gap<=1e-7 and j not in eligible:
                    new_contacts.append({'pad_uuid':p['uuid'],'object_key':keys[j],'net_token':p['net'],'gap_mm':gap})
        checkpoint('pad-clearance-conflicts.json.gz',pad_pairs)
        checkpoint('pad-drill-conflicts.json.gz',drill_pairs)
        checkpoint('pad-copper-conflicts.json.gz',copper_pad)
        checkpoint('fixed-contact-reconstruction.json.gz',boundary_contacts)
        checkpoint('destination-fixed-same-net-contacts.json',new_contacts)
        cp=[];cc=[];cd=[];ce=[];ck=[];copper_new_contacts=[]
        outline=affinity.translate(Polygon(b['outline_mm']),100,50).buffer(-.50,join_style=2)
        keepouts=[(q,Polygon([(x/1e6,y/1e6) for x,y in q['poly']])) for q in original['keepouts']]
        kt=STRtree([g for _,g in keepouts])
        for i in sorted(eligible):
            g=ng[i];row=rows[i]
            if not outline.covers(g.buffer(cr[i])):ce.append({'object_key':keys[i],'outside_mm2':g.buffer(cr[i]).difference(outline).area})
            for z in hits(kt,g,cr[i]):
                q,qg=keepouts[z]
                if same_layer(q['layers'],cl[i]) and q['vias' if row['kind']=='via' else 'tracks'] and g.distance(qg)<cr[i]+1e-7:
                    ck.append({'object_key':keys[i],'keepout':q['name'],'gap_mm':g.distance(qg)-cr[i]})
            for j in hits(npt,g,cr[i]+.25):
                p=pads[j]
                if p['ref'] in refs or not same_layer(p['layers'],cl[i]):continue
                gap=g.distance(npg[j])-cr[i]
                if p['net']==row['net_token'] and gap<=1e-7:
                    copper_new_contacts.append({'object_key':keys[i],'fixed_pad_uuid':p['uuid'],'gap_mm':gap})
                if (p['net']!=row['net_token'] and gap<.25-1e-7) or (row['kind']=='via' and not p['drill'] and gap<1e-6):
                    cp.append({'object_key':keys[i],'pad_uuid':p['uuid'],'ref':p['ref'],'pad':p['pad'],'other_scope':pad_owner(p),'gap_mm':gap})
            for z in hits(dt,g,cr[i]+maxdrill+.25):
                j=drill_ids[z]
                gap=g.distance(drill_geoms[z])-cr[i]-pads[j]['drill']/2e6
                if gap<.25-1e-7:cd.append({'object_key':keys[i],'drill_uuid':pads[j]['uuid'],'other_scope':pad_owner(pads[j]),'gap_mm':gap})
            for j in hits(nt,g,cr[i]+maxrad+.25):
                if i==j or (j in eligible and j<i) or not same_layer(cl[i],cl[j]):continue
                gap=g.distance(ng[j])-cr[i]-cr[j]
                if j not in eligible and row['net_token']==rows[j]['net_token'] and gap<=1e-7:
                    copper_new_contacts.append({'object_key':keys[i],'fixed_object_key':keys[j],'gap_mm':gap})
                if row['net_token']!=rows[j]['net_token'] and gap<.25-1e-7:
                    cc.append({'object_key':keys[i],'other_key':keys[j],'other_scope':ownership(rows[j]),'gap_mm':gap,
                        'origin':'INTRINSIC_PRESERVED' if j in eligible else 'LOCATION_DEPENDENT'})
        checkpoint('transformed-copper-new-same-net-contacts.json',copper_new_contacts)
        hole_pairs=[]
        all_holes=[{'id':pads[i]['uuid'],'kind':'PAD','center':drill_geoms[z],
            'radius':pads[i]['drill']/2e6,'annulus':None,'moved':pads[i]['ref'] in refs}
            for z,i in enumerate(drill_ids)]
        all_holes += [{'id':keys[i],'kind':'VIA','center':ng[i],
            'radius':rows[i]['drill_mm']/2,'annulus':cr[i],'moved':i in eligible}
            for i in range(len(rows)) if rows[i]['kind']=='via']
        ht=STRtree([h['center'] for h in all_holes])
        max_hole=max(h['annulus'] or h['radius'] for h in all_holes)
        for i,h in enumerate(all_holes):
            if not h['moved']:continue
            margin=(h['annulus'] or h['radius'])+max_hole+.25
            for j in hits(ht,h['center'],margin):
                q=all_holes[j]
                if i==j or (q['moved'] and j<i):continue
                distance=h['center'].distance(q['center'])
                drill_gap,annulus_drill_gap,violation=hole_margins(distance,h,q)
                if violation:
                    hole_pairs.append({'a':h['id'],'b':q['id'],'kinds':[h['kind'],q['kind']],
                        'drill_gap_mm':drill_gap,'minimum_annulus_or_hole_gap_mm':annulus_drill_gap,
                        'required_mm':.25,'net_independent':True,
                        'origin':'INTRINSIC_PRESERVED' if q['moved'] else 'LOCATION_DEPENDENT'})
        checkpoint('all-drilled-hole-conflicts.json.gz',hole_pairs)
        checkpoint('transformed-copper-obstructions.json.gz',{'fixed_pads':cp,'foreign_copper':cc,'pad_drills':cd,'edge':ce,'keepouts':ck})
        checkpoint('boundary-net-obligations.json.gz',[n|{'all_original_objects':[rows[i]|{'object_key':keys[i]} for i in range(len(rows)) if rows[i]['net_token']==n['net_token']],
            'moved_pad_uuids':[pads[i]['uuid'] for i in moved_pads if pads[i]['net']==n['net_token']],
            'obligation':'All fixed original copper and external pads remain unchanged. Restore every original moved-pad contact and preserve full boundary/rail groups; whole-net scope is accounting only.'}
            for n in boundary['nets'] if n['classification']!='GROUP_INTERNAL'])
        checkpoint('zone-obligations.json',{'zones':zones,'status':'UNRESOLVED_NATIVE_REFILL_AND_CONTACT_GATE','all_original_zones_preserved':True,
            'internal_net_same_net_zones':sorted(internal&same_net_zones),'remaining':'Full foreign-zone clearance and connectivity/thermal return effects require separately admitted native audit; no zone moved.'})
        verify_seals(seals)
        summary.update(status='COMPLETE_SOURCE_CENSUS_NOFIT' if not placement['pass'] or pad_pairs or copper_pad or cp or cc or ce or ck or cd or drill_pairs or hole_pairs else 'COMPLETE_SOURCE_CENSUS_NATIVE_UNRESOLVED',
            moved_refs=len(refs),moved_pads=len(moved_pads),all_original_pad_count=len(pads),authenticated_objects=len(index),original_segments_vias=len(rows),
            internal_objects=len(chosen),source_contact_closed_transformed=len(eligible),blocked_preserved=len(chosen-eligible),source_components=len(components),
            counts={'courtyard':len(placement['same_face_gap_violations']),'reservation':len(placement['reservation_conflicts']),'service_hole':len(placement['analytic_service_hole_conflicts']),
                'pad_pad':len(pad_pairs),'pad_drill':len(drill_pairs),'pad_copper':len(copper_pad),'fixed_reconstruction_contacts':len(boundary_contacts),
                'transformed_copper_fixed_pad':len(cp),'transformed_copper_foreign_copper':len(cc),'transformed_copper_pad_drill':len(cd),'copper_edge':len(ce),'copper_keepout':len(ck),'drilled_hole_pairs':len(hole_pairs)},
            source_fit=False,final_copper_eligibility='UNRESOLVED; source contact closure is not native or destination acceptance',
            canonical_inputs_unchanged=True,elapsed_seconds=time.monotonic()-started,peak_memory_kib_linux=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
        checkpoint('summary.json',summary)
    except (TimeoutError,MemoryError,Exception) as exc:
        summary.update(status='INCOMPLETE',error=type(exc).__name__+': '+str(exc),elapsed_seconds=time.monotonic()-started)
        write(out,'summary.json',summary)
        raise


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--dump',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    ap.add_argument('--child',action='store_true')
    args=ap.parse_args()
    if args.child:
        child(args);return
    assert not args.output.exists(), 'One new output directory only; no overwrite/retry'
    args.output.mkdir(parents=True)
    write(args.output,'execution-start.json',{'source_sha256':sha(Path(__file__).read_bytes()),'plan_commit':'c3e4bc95858ac573332b47bd34032b2358fa009c',
        'command':'one source-only child; address-space cap2GiB; wall180s; no retries','delta_mm':DELTA})
    env=os.environ|{'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1'}
    start=time.monotonic()
    try:
        result=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--child','--dump',str(args.dump.resolve()),'--output',str(args.output.resolve())],env=env,timeout=180)
        code=result.returncode
    except subprocess.TimeoutExpired:
        code=124
    if code or not (args.output/'summary.json').exists():
        try:
            progress=read(args.output/'progress.json') if (args.output/'progress.json').exists() else {}
        except (OSError,ValueError) as exc:
            progress={'read_error':type(exc).__name__+': '+str(exc)}
        write(args.output,'supervisor-incomplete.json',{'status':'INCOMPLETE','returncode':code,'last_checkpoint':progress,'no_retry':True})
    write(args.output,'execution-receipt.json',{'returncode':code,'elapsed_seconds':time.monotonic()-start,'child_workers':1,'native_calls':0,'retries':0})
    sys.exit(code)


if __name__=='__main__':main()
