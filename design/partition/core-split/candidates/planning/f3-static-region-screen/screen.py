#!/usr/bin/env python3
"""Bounded static forbidden-translation regions, without a candidate pose or PCB."""
import argparse
from collections import Counter
import gzip
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import subprocess
import sys
import time

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[5]
QUANTUM=1e-6
GUARD=.001
QUADS=32
WINDOWS={'N-two-A':[124,88,164,168],'E-two-A':[164,48,244,168]}


def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def save(out,name,obj):
    raw=(json.dumps(obj,sort_keys=True,separators=(',',':'))+'\n').encode()
    tmp=out/(name+'.tmp');tmp.write_bytes(gzip.compress(raw,mtime=0) if name.endswith('.gz') else raw);tmp.replace(out/name)


def hull_int(points):
    points=sorted(set(points))
    def cross(o,a,b):return (a[0]-o[0])*(b[1]-o[1])-(a[1]-o[1])*(b[0]-o[0])
    lower=[];upper=[]
    for p in points:
        while len(lower)>=2 and cross(lower[-2],lower[-1],p)<=0:lower.pop()
        lower.append(p)
    for p in reversed(points):
        while len(upper)>=2 and cross(upper[-2],upper[-1],p)<=0:upper.pop()
        upper.append(p)
    return lower[:-1]+upper[:-1]


def forbidden_vertices(moving,fixed):
    m=[(round(x/QUANTUM),round(y/QUANTUM)) for x,y in moving]
    o=[(round(x/QUANTUM),round(y/QUANTUM)) for x,y in fixed]
    return [(x*QUANTUM,y*QUANTUM) for x,y in hull_int([(ox-mx,oy-my) for ox,oy in o for mx,my in m])]


def translation_domain(window,bounds):
    a,b,c,d=window;x,y,z,w=bounds
    return [a-x,b-y,c-z,d-w]


def convex_geometry(points):
    from shapely.geometry import Polygon
    assert all(math.isfinite(x) and math.isfinite(y) for x,y in points)
    g=Polygon(points)
    assert g.is_valid and g.area>0 and not g.interiors and g.equals(g.convex_hull)
    return g


def forbidden_bounds(core,expansion):
    lower=core.buffer(expansion-GUARD,quad_segs=QUADS)
    upper=core.buffer((expansion+GUARD)/math.cos(math.pi/(4*QUADS)),quad_segs=QUADS)
    return lower,upper


def excluded(lower,domain):
    return lower.covers(domain) and domain.difference(lower).is_empty


def worker(out):
    resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
    import shapely
    from shapely.geometry import Polygon,Point,box,mapping
    from shapely.ops import unary_union
    start=time.monotonic()
    seals=read(HERE/'input-seals.json')
    for f,h in seals.items():assert sha(ROOT/f)==h,f
    assert shapely.__version__=='2.1.2' and shapely.geos_version_string=='3.13.1'
    board=read(ROOT/'design/partition/core-split/candidates/two.json')['boards']['two-A']
    boundary=read(HERE.parent/'f3-next-approach/whole-f3-boundary.json')
    refs=set(boundary['refs']);assert len(refs)==171
    geometry=convex_geometry
    moving=[(p['ref'],p['side'],geometry(q)) for p in board['placements'] if p['ref'] in refs for q in p['courtyard_polygons_mm']]
    assert len(moving)==171
    fixed=[]
    for p in board['placements']:
        if p['ref'] in refs:continue
        for i,q in enumerate(p['courtyard_polygons_mm']):fixed.append({'id':p['ref'],'piece':i,'face':p['side'],'kind':'FIXED_COURTYARD','g':geometry(q),'expansion':.35})
    for face,data in board['measurement']['faces'].items():
        for p in data['reservation_polygons_mm']:
            for i,q in enumerate(p['polygons']):fixed.append({'id':p['id'],'piece':i,'face':face,'kind':'RESERVATION','g':geometry(q),'expansion':0})
    for p in read(ROOT/'design/partition/partition.json')['K_service_apertures']:
        fixed.append({'id':p['header_id'],'piece':0,'face':'ALL','kind':'ANALYTIC_SERVICE_HOLE','g':Point(p['center_mm']),'expansion':p['diameter_mm']/2})
    bounds=unary_union([g for _,_,g in moving]).bounds
    assert list(bounds)==boundary['courtyard_bbox_candidate_mm']
    outline=Polygon(board['outline_mm']).buffer(-.30,join_style=2)
    results=[]
    for name,window in WINDOWS.items():
        domain_box=translation_domain(window,bounds)
        base={'window':name,'window_mm':window,'domain_dx_dy_mm':domain_box,'whole_courtyard_containment_required':True,
              'current_orientation_only':True,'fixed_parts':len(board['placements'])-171,'inherited_internal_gate':'Separate invariant failure; not included in forbidden external regions.'}
        assert outline.covers(box(*window)), 'Window needs separate concave-outline erosion analysis'
        base['courtyard_board_margin_satisfied_for_domain']=True
        if domain_box[0]>domain_box[2] or domain_box[1]>domain_box[3]:
            base['status']='EMPTY_CONTAINMENT_DOMAIN';results.append(base);continue
        domain=box(*domain_box)
        lower_sets=[];upper_sets=[];records=[];broadphase=0
        for ref,face,m in moving:
            mx,my,mz,mw=m.bounds
            swept=box(mx+domain_box[0],my+domain_box[1],mz+domain_box[2],mw+domain_box[3])
            for obs in fixed:
                if obs['face'] not in (face,'ALL'):continue
                expansion=obs['expansion'];o=obs['g']
                if swept.distance(o.envelope)>expansion+GUARD:continue
                broadphase+=1
                points=list(o.coords) if o.geom_type=='Point' else list(o.exterior.coords)[:-1]
                core=Polygon(forbidden_vertices(list(m.exterior.coords)[:-1],points))
                # Integer hull: <=sqrt(2)*1nm source rounding error; 1um guard dominates it.
                lower,upper=forbidden_bounds(core,expansion)
                if not upper.intersects(domain):continue
                lo=lower.intersection(domain);hi=upper.intersection(domain)
                assert hi.buffer(1e-9).covers(lo)
                lower_sets.append(lo);upper_sets.append(hi)
                records.append({'moving_ref':ref,'face':face,'fixed_id':obs['id'],'piece':obs['piece'],'kind':obs['kind'],
                    'spacing_or_radius_mm':expansion,'lower_forbidden':mapping(lo),'upper_forbidden':mapping(hi)})
        lower_union=unary_union(lower_sets);upper_union=unary_union(upper_sets)
        not_excluded=domain.difference(lower_union)
        robust_free=domain.difference(upper_union.buffer(GUARD,quad_segs=QUADS))
        no_region=excluded(lower_union,domain)
        kind_coverage={k:unary_union([g for g,r in zip(lower_sets,records) if r['kind']==k]).covers(domain) for k in sorted({r['kind'] for r in records})}
        # A small separately retained subset can witness coverage; it is not a minimal set.
        witness=[];cover=Polygon()
        for i in sorted(range(len(records)),key=lambda j:(-lower_sets[j].area,records[j]['moving_ref'],records[j]['fixed_id'])):
            if lower_sets[i].difference(cover).area==0:continue
            witness.append(i);cover=cover.union(lower_sets[i])
            if cover.covers(domain):break
        base.update(status='NO_EXTERNAL_CLEAR_TRANSLATION_IN_DOMAIN' if no_region else 'ROBUST_EXTERNAL_CLEAR_REGION' if not robust_free.is_empty and robust_free.area>0 else 'NO_ROBUST_REGION_ESTABLISHED_NUMERICAL_FRINGE',
                    domain_area_mm2=domain.area,broadphase_pairs=broadphase,retained_obstacle_pairs=len(records),
                    lower_union_covers_domain=no_region,lower_uncovered_geometry=mapping(not_excluded),
                    upper_guarded_free_geometry=mapping(robust_free),robust_free_area_mm2=robust_free.area,
                    lower_covers_by_kind=kind_coverage,coverage_witness_record_indices=witness if cover.covers(domain) else [],
                    pair_counts_by_kind=dict(Counter(r['kind'] for r in records)),boundary_test='covers and empty difference; area alone never excludes boundary translations')
        save(out,name+'-forbidden-regions.json.gz',records)
        save(out,name+'-coverage.json',base)
        results.append(base)
    for f,h in seals.items():assert sha(ROOT/f)==h,f
    save(out,'result.json',{'status':'COMPLETE_STATIC_SOURCE_REGION_SCREEN','windows':results,
        'source_bbox_mm':bounds,'rounding_grid_mm':QUANTUM,'max_hull_vertex_rounding_error_mm':math.sqrt(2)*QUANTUM,
        'inward_outward_guard_mm':GUARD,'buffer_quadrant_segments':QUADS,
        'numerics':'Exact integer convex hull on1nm-rounded inputs; GEOS union/intersection/distance in floating point, with1um inner/outer guards. Source numerical certificate, not formal exact-real or native proof.',
        'limits':['Window containment domains only, current orientation; not entire two-A board','Only external courtyards/reservations/serviceholes/board margin; inherited internal failure separate','No copper/pad/drill routing clearance or zone/native acceptance from a free region','No candidate point, pose, PCB or route materialized'],
        'source_workers':1,'new_candidate_poses':0,'native_calls':0,'elapsed_seconds':time.monotonic()-start,
        'peak_memory_kib_linux':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss})


def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--output',type=Path,required=True);p.add_argument('--worker',action='store_true');a=p.parse_args()
    if a.worker:worker(a.output);return
    assert not a.output.exists(),'one bounded analysis output; no overwrite/retry'
    a.output.mkdir(parents=True)
    save(a.output,'start.json',{'screen_source_sha256':sha(Path(__file__)),'budget_seconds':30,'memory_GiB':2,'mode':'STATIC_REGION_ALGEBRA_NO_POSE_EVALUATION'})
    started=time.monotonic()
    try:
        r=subprocess.run([sys.executable,str(Path(__file__).resolve()),'--worker','--output',str(a.output.resolve())],timeout=30,
            env=os.environ|{'OPENBLAS_NUM_THREADS':'1','OMP_NUM_THREADS':'1','MKL_NUM_THREADS':'1'})
        code=r.returncode
    except subprocess.TimeoutExpired:code=124
    save(a.output,'receipt.json',{'status':'COMPLETE' if code==0 and (a.output/'result.json').exists() else 'INCOMPLETE','returncode':code,'elapsed_seconds':time.monotonic()-started,'workers':1,'retries':0})
    sys.exit(code)

if __name__=='__main__':main()
