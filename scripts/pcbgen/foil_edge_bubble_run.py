"""Hash-bound two-column retained current enrichment, without a field solve.

Current-inner physical containment remains an explicit inherited premise.
Only complete ordinary two-triangle edge patches are admissible. Native/barrel
interfaces are reconstructed by the unchanged geometry method, without calling
an operator constructor, factorization, or solve.
"""
from fractions import Fraction as F
import hashlib
import json
import math
from pathlib import Path
import time
from scripts.pcbgen import foil_edge_bubble_probe as core

REPO=Path(__file__).resolve().parents[2]


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for chunk in iter(lambda:f.read(1<<20),b''):h.update(chunk)
    return h.hexdigest()


def read_json(path, expected=None):
    data=Path(path).read_bytes();digest=hashlib.sha256(data).hexdigest()
    if expected is not None and digest!=expected:raise ValueError('JSON input hash changed: '+str(path))
    return json.loads(data),digest


def inside(root,name):
    root=Path(root).resolve();p=(root/name).resolve()
    if not p.is_relative_to(root):raise ValueError('input outside historical root')
    return p


def merge_bindings(*maps):
    out={}
    for m in maps:
        for name,value in m.items():
            if name in out and out[name]!=value:raise ValueError('conflicting source binding: '+name)
            out[name]=value
    return out


def geometry_interfaces(native,full):
    """Use precisely the constructor's scalar geometry, never __init__.

    Stored ownership is checked against the complete native AGND hole list in
    source order. The immutable interface_polygon method consumes only these
    four known scalar attributes; no operator state is guessed or synthesized.
    """
    from types import SimpleNamespace
    from scripts.pcbgen.barrel_volume import BarrelVolume
    from scripts.pcbgen.foil_stack import resolve_stack,require_native_layers
    stack=resolve_stack(native['stackup'],native.get('thickness_mm'))
    require_native_layers(native['enabled_copper_layers'],stack['layers'])
    if len(stack['layers'])!=4 or list(stack['layers'])!=full['active_sheet_layers'] or stack['layers'][-1]!='B.Cu':
        raise ValueError('complete four-foil ownership required')
    members=set(native['ground_reference_members'] if native.get('ground_reference') is not None
                else native['main_rail_members']['AGND'])
    holes=[h for h in native['holes'] if h['net']=='AGND' and h['uuid'] in members]
    if len({h['uuid'] for h in holes})!=len(holes) or len(holes)!=len(full['barrel_ownership']):
        raise ValueError('native barrel ownership count changed')
    refinement=full['refinement']
    if type(refinement) is not int or refinement!=1:raise ValueError('only frozen refinement1 geometry supported')
    out=[]
    for hole,owner in zip(holes,full['barrel_ownership']):
        diameter=hole['size_mm'][0]
        if (not hole['plated'] or hole['size_mm']!=[diameter,diameter]
                or hole['copper_layers']!=list(stack['layers']) or not math.isfinite(diameter) or diameter<=0):
            raise ValueError('native circular full-stack barrel required')
        radius=diameter/2+.1
        expected={'uuid':hole['uuid'],'xy_mm':hole['xy_mm'],
                  'finished_drill_mm':diameter,'flange_radius_mm':radius}
        if owner!=expected:raise ValueError('native barrel geometry/order changed')
        chord=2*radius*math.tan(math.pi/16)
        descriptor=SimpleNamespace(flange_radius=radius,polygon_sides=16,
            angular_subdivisions=refinement,interface_chord_mm=chord/refinement)
        out.append({'centre':hole['xy_mm'],'relative':BarrelVolume.interface_polygon(descriptor)})
    return out,stack


def select_edges(sheet,flux,interface_vertices,limit,edge_cap):
    """Deterministic selection proxy only; no floating value supplies a bound."""
    import numpy as np
    triangles=sheet.triangles
    edges0=np.sort(triangles[:,[[1,2],[2,0],[0,1]]],axis=2)
    edges,inverse,counts=np.unique(edges0.reshape(-1,2),axis=0,return_inverse=True,return_counts=True)
    if len(edges)>edge_cap or np.any(counts>2):raise ValueError('edge cap or manifold topology failed')
    ordinary=~np.isin(triangles,list(interface_vertices)).any(axis=1)
    order=np.argsort(inverse,kind='stable');starts=np.r_[0,np.cumsum(counts)[:-1]]
    ids=np.flatnonzero(counts==2)
    first=order[starts[ids]]//3;second=order[starts[ids]+1]//3
    keep=ordinary[first]&ordinary[second];ids=ids[keep];first=first[keep];second=second[keep]
    ends=edges[ids];xy=np.asarray(sheet.metric_xy,dtype=float)
    midpoint=xy[ends].mean(axis=1);direction=xy[ends[:,1]]-xy[ends[:,0]]
    qs=[];areas=[]
    for tri_ids in (first,second):
        vertices=xy[triangles[tri_ids]]
        u=vertices[:,1]-vertices[:,0];v=vertices[:,2]-vertices[:,0]
        area=abs(u[:,0]*v[:,1]-u[:,1]*v[:,0])/2
        if np.any(area<=0):raise ValueError('degenerate ranking cell')
        q=np.einsum('nfk,nfj->njk',flux[tri_ids],midpoint[:,None,:]-vertices)/(2*area[:,None,None])
        qs.append(q);areas.append(area)
    jump=np.einsum('njk,nj->nk',qs[0]-qs[1],direction)
    denominator=np.sum(direction*direction,axis=1)*(1/areas[0]+1/areas[1])
    scores=np.sum(jump*jump,axis=1)/denominator
    if not np.isfinite(scores).all() or np.any(scores<0):raise ValueError('nonfinite selection proxy')
    ranking=np.lexsort((ends[:,1],ends[:,0],-scores))
    chosen=[];used=set()
    for k in ranking:
        pair=(int(first[k]),int(second[k]))
        if used.intersection(pair):continue
        used.update(pair)
        chosen.append({'triangles':list(pair),'edge_vertices':list(map(int,ends[k])),
                       'selection_proxy':float(scores[k])})
        if len(chosen)==limit:break
    return chosen,{'all_edges':len(edges),'eligible_edges':len(ids),'selected_patches':len(chosen)}


def exact_interface_polygons(interfaces):
    from scripts.pcbgen.partial_cell_energy import exact,signed_twice_area,sub,cross
    out=[]
    for interface in interfaces:
        centre=tuple(F(round(exact(v)*10**6),10**6) for v in interface['centre'])
        poly=tuple(tuple(centre[j]+exact(p[j]) for j in range(2)) for p in interface['relative'])
        if signed_twice_area(poly)<=0 or any(cross(sub(poly[(i+1)%len(poly)],poly[i]),
                sub(poly[(i+2)%len(poly)],poly[(i+1)%len(poly)]))<0 for i in range(len(poly))):
            raise ValueError('interface polygon is not positively convex')
        out.append(poly)
    return out


def bounds(poly):return tuple(min(p[j] for p in poly) for j in range(2))+tuple(max(p[j] for p in poly) for j in range(2))
def boxes_touch(a,b):return all(a[j]<=b[j+2] and b[j]<=a[j+2] for j in range(2))


def checked_patch(row,chart,index,interface_polygons,flux,sheet_ohm,budget):
    from scripts.pcbgen.partial_cell_energy import triangle,intersect,area,signed_twice_area
    sheet=chart.sheet;ids=row['triangles'];edge_ids=row['edge_vertices']
    if len(ids)!=2 or len(set(ids))!=2 or len(edge_ids)!=2 or len(set(edge_ids))!=2:
        raise ValueError('two distinct cells and edge endpoints required')
    points=[];columns=[]
    for ident in ids:
        if any(int(v) in chart.interface for v in sheet.triangles[ident]):raise ValueError('selected interface vertex forbidden')
        _,canonical,_=chart.cell(ident)
        permutation=[0,1,2] if signed_twice_area(canonical)>0 else [0,2,1]
        p=tuple(canonical[i] for i in permutation);box=bounds(p)
        for poly in interface_polygons:
            if boxes_touch(box,bounds(poly)):
                budget.charge('overlap_checks',1)
                if area(intersect(p,poly))>0:raise ValueError('selected support crosses complete barrel interface')
        for other in index.query_box(index.boxes[ident]):
            if other==ident:continue
            budget.charge('overlap_checks',1)
            _,candidate,_=chart.cell(other)
            if area(intersect(p,triangle(candidate)))>0:raise ValueError('current cells overlap in positive area')
        points.append(p)
        columns.append(tuple(tuple(F(float(x)) for x in flux[ident,i]) for i in permutation))
    edge=tuple(chart.vertex(i)[1] for i in edge_ids)
    g,h=core.patch_work(points,columns,edge,sheet_ohm)
    return {**row,'status':'accepted conditional current support',
        'coordinates_exact':[[[str(x) for x in p] for p in tri] for tri in points],
        'local_flux_A_exact':[[[str(x) for x in p] for p in tri] for tri in columns],
        'raw_work_exact':list(map(str,g)),'bubble_energy_exact':str(h)}



def verify_pair_binding(config,pair,full,capture,root):
    """Pair U/L/C and raw fields are inseparable; no full-basis submatrix reuse."""
    if (pair['selected_columns']!=[['J900134','2'],['C107','2']] or pair['matrix_indices']!=[4,128]
            or pair['reference_contact']!=full['reference_contact'] or pair['reference_contact']['ref']!='TP990031'
            or pair['raw_field_artifacts']['current-fields.npz']!=config['input_sha256'][config['current_fields']]
            or inside(root,config['current_fields'])!=inside(root,config['pair_receipt']).parent/'current-fields.npz'):
        raise ValueError('source/current archive identity mismatch')
    normalized={}
    for name,value in full['model_source_sha256'].items():
        key=name if name.startswith('design/') else 'scripts/pcbgen/'+name
        if key in normalized or pair['input_sha256'].get(key)!=value:
            raise ValueError('full and pair model epochs differ: '+key)
        normalized[key]=value
    if (capture['source_pair']!=pair['selected_columns'] or
            capture['input_sha256'].get(config['pair_receipt'])!=config['input_sha256'][config['pair_receipt']]):
        raise ValueError('capture/library epoch is not tied to paired receipt')

def output_path(path,root):
    p=Path(path).resolve()
    if p.exists() or not p.is_relative_to(REPO/'.circuit-cache') or p.is_relative_to(root):
        raise ValueError('fresh own ignored output required')
    return p


def run(manifest,artifact_root,output,frozen_core,frozen_runner):
    import gc
    import pickle
    import platform
    import resource
    import sys
    import numpy as np
    import scipy
    import shapely
    from types import SimpleNamespace
    from scripts.pcbgen.partial_cell_energy import CanonicalChart,ConservativeIndex,Budget,WorkCap
    from scripts.pcbgen.observation_support_bound import upward
    started=time.monotonic();root=Path(artifact_root).resolve();output=output_path(output,root)
    config,digest=read_json(manifest)
    if (config['status']!='UNSELECTED conditional current enrichment' or config['layer_index']!=3
            or type(config['patch_limit']) is not int or not 1<=config['patch_limit']<=128
            or config['edge_cap']!=500000 or config['overlap_cap']!=100000):
        raise ValueError('changed diagnostic scope/work cap')
    own={str(Path(manifest).resolve()):digest,str(Path(__file__).resolve()):frozen_runner,
         str(REPO/'scripts/pcbgen/foil_edge_bubble_probe.py'):frozen_core}
    own.update({str(REPO/name):value for name,value in config['executed_helper_sha256'].items()})
    def verify_own():
        if any(sha(name)!=value for name,value in own.items()):raise ValueError('executed diagnostic source changed')
    verify_own()
    for name,value in config['input_sha256'].items():
        if sha(inside(root,name))!=value:raise ValueError('configured historical input changed: '+name)
    pair,_=read_json(inside(root,config['pair_receipt']),config['input_sha256'][config['pair_receipt']])
    full,_=read_json(inside(root,config['full_receipt']),config['input_sha256'][config['full_receipt']])
    capture,_=read_json(inside(root,config['capture']),config['input_sha256'][config['capture']])
    native,_=read_json(inside(root,config['native']),config['input_sha256'][config['native']])
    historical=merge_bindings(config['input_sha256'],pair['input_sha256'],pair['native_prerequisite']['dependency_sha256'])
    def verify():
        verify_own()
        for name,value in historical.items():
            if sha(inside(root,name))!=value:raise ValueError('historical dependency changed: '+name)
        # Every actually imported project module is explicitly source-bound.
        for module in list(sys.modules.values()):
            filename=getattr(module,'__file__',None)
            if not filename:continue
            p=Path(filename).resolve()
            if p.is_relative_to(REPO/'scripts'):
                relative=str(p.relative_to(REPO));expected=config['executed_helper_sha256'].get(relative)
                if p==Path(__file__).resolve():expected=frozen_runner
                if p==REPO/'scripts/pcbgen/foil_edge_bubble_probe.py':expected=frozen_core
                if expected is None or sha(p)!=expected:raise ValueError('unbound executed module: '+relative)
    verify()
    libraries={'python':platform.python_version(),'numpy':np.__version__,'scipy':scipy.__version__,'shapely':shapely.__version__}
    if libraries!=capture['libraries']:raise ValueError('numeric environment differs from retained capture')
    verify_pair_binding(config,pair,full,capture,root)
    C=pair['raw_to_conserved']['combined_energy_upper_ohm']
    if len(C)!=2 or any(F(x)<0 for x in C):raise ValueError('two finite correction energies required')
    interfaces,stack=geometry_interfaces(native,full)
    print('edge-bubble: load immutable current mesh; no operator construction or solve',flush=True)
    with inside(root,config['current_mesh']).open('rb') as stream:key,sheets=pickle.load(stream)
    if key!=config['current_cache_key']:raise ValueError('current cache key changed')
    sheet=SimpleNamespace(**{name:getattr(sheets[3],name) for name in ('metric_xy','triangles','metric_factors','interface_faces')})
    del sheets;gc.collect()
    if len(sheet.triangles)!=139921:raise ValueError('current triangle count changed')
    chart=CanonicalChart(sheet,interfaces);chart.validate_all_vertices();index=ConservativeIndex(sheet)
    with np.load(inside(root,config['current_fields'])) as fields:flux=fields['sheet_flux_3']
    if flux.shape!=(len(sheet.triangles),3,2) or not np.isfinite(flux).all():raise ValueError('raw current field shape/finiteness changed')
    verify()
    selected,census=select_edges(sheet,flux,chart.interface,config['patch_limit'],config['edge_cap'])
    polygons=exact_interface_polygons(interfaces);budget=Budget({'overlap_checks':config['overlap_cap']})
    rho=1.7241e-5*(1+.003947*50)
    # Preserve the historical constructor's represented sheet-resistance scalar.
    sheet_ohm=F(float(rho/stack['thickness'][3]))
    rows=[];accepted=[];exhausted=False
    for row in selected:
        if exhausted:rows.append({**row,'status':'unprocessed work cap; zero perturbation'});continue
        try:
            record=checked_patch(row,chart,index,polygons,flux,sheet_ohm,budget)
            accepted.append(record);rows.append(record)
        except WorkCap as exc:
            exhausted=True;rows.append({**row,'status':'unprocessed work cap; zero perturbation','reason':str(exc)})
        except ValueError as exc:
            rows.append({**row,'status':'rejected geometry; zero perturbation','reason':str(exc)})
    G,H,coefficients=core.combine_patches(accepted)
    for row,beta in zip(accepted,coefficients):row['chosen_binary64_coefficients_A']=beta
    U=pair['matrices_ohm']['upper'];L=pair['matrices_ohm']['lower']
    new=core.gram_update(U,L,[[(x,x) for x in row] for row in G],H,C)
    serialized=core.upper_float_matrix(new)
    old_interval=core.transfer_interval(U,L);new_interval=core.transfer_interval(serialized,L)
    intersection=(max(old_interval[0],new_interval[0]),min(old_interval[1],new_interval[1]))
    if intersection[0]>intersection[1]:raise ValueError('contradictory old/new transfer intervals')
    verify()
    down=lambda x:-upward(-x)
    record={'status':'CONDITIONAL retained two-column current enrichment; no physical/common admission',
        'artifact_root':str(root),'manifest_sha256':digest,'input_sha256':historical,'executed_sha256':own,
        'libraries':libraries,'selected_columns':pair['selected_columns'],'reference_contact':pair['reference_contact'],
        'selection':census,'patches':rows,'accepted_patches':len(accepted),'work_used':budget.used,'chart':chart.audit(),
        'sheet_resistance_exact_ohm':str(sheet_ohm),'raw_to_conserved_energy_upper_ohm':C,
        'raw_perturbation_work_exact_ohm':[[str(x) for x in row] for row in G],
        'perturbation_gram_exact_ohm':[[str(x) for x in row] for row in H],
        'old_upper_ohm':U,'unchanged_lower_ohm':L,'new_upper_exact_ohm':[[str(x) for x in row] for row in new],
        'new_upper_ohm':serialized,'diagonal_upper_reduction_lower_ohm':[down(F(U[i][i])-F(serialized[i][i])) for i in range(2)],
        'old_transfer_interval_ohm':[down(old_interval[0]),upward(old_interval[1])],
        'new_transfer_interval_ohm':[down(new_interval[0]),upward(new_interval[1])],
        'intersection_transfer_interval_ohm':[down(intersection[0]),upward(intersection[1])],
        'scope':['Same finite source normal flux a.e.; tangential jumps allowed.',
            'No field solve, matrix factorization, mesh/material/contact/geometry change or source-lift change.',
            'Conditional canonical current-inner containment; no actual physical class or joined common admission.',
            'Zero contribution from every rejected/unprocessed patch; no replacement or second batch.'],
        'runtime_sec':time.monotonic()-started,'peak_rss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    output.mkdir(parents=True);(output/'result.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({k:record[k] for k in ('accepted_patches','diagonal_upper_reduction_lower_ohm','intersection_transfer_interval_ohm','runtime_sec','peak_rss_kib')}),flush=True)
    return record


def main():
    import argparse
    p=argparse.ArgumentParser();p.add_argument('--manifest',default='design/partition/foil-edge-bubble-probe.json')
    p.add_argument('--artifact-root',required=True);p.add_argument('--output',required=True)
    p.add_argument('--frozen-core-sha256',required=True);p.add_argument('--frozen-runner-sha256',required=True)
    a=p.parse_args()
    try:run(a.manifest,a.artifact_root,a.output,a.frozen_core_sha256,a.frozen_runner_sha256)
    except Exception as exc:
        out=output_path(a.output,Path(a.artifact_root).resolve());out.mkdir(parents=True)
        (out/'failure.json').write_text(json.dumps({'status':'FAILED diagnostic; no new bound admitted',
            'exception_type':type(exc).__name__,'reason':str(exc),'requested_core_sha256':a.frozen_core_sha256,
            'requested_runner_sha256':a.frozen_runner_sha256},indent=2)+'\n')
        raise

if __name__=='__main__':main()
