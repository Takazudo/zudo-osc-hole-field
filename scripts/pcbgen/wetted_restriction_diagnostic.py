"""No-solve mismatch lower bounds for the frozen P wetting restriction.

Only retained meshes/fields are read. No operator is assembled or factored,
and no current/potential linear solve is called. This does not admit hardware
or change copper, source profiles, the prior receipt, or the common target.
"""
import argparse
from fractions import Fraction as F
import json
import math
from pathlib import Path
import pickle
import time

from scripts.pcbgen.observation_support_bound import sqrt_upper, upward
from scripts.pcbgen.regional_probe import sha, verify_hashes


def down(value):
    return -upward(-value)


def exact(value):
    """Retain even the cached long-double coordinate's full binary value."""
    if hasattr(value,'as_integer_ratio'):return F(*value.as_integer_ratio())
    return F(value)


def bubble_floor(load, energy_upper):
    """Green+Cauchy: energy_W(q) >= |f(psi)|² / E(psi)_upper.

    psi must have zero extension outside W. The complete finite boundary load,
    not terminal totals, defines load. Exact rational arithmetic rounds down.
    """
    f=F(load);e=F(energy_upper)
    if e<0 or (e==0 and f!=0):raise ValueError('invalid bubble energy/load')
    return 0. if not f else down(f*f/e)


def corrected_lower(raw_lower, correction_upper):
    """Lower squared norm after an explicitly bounded field perturbation."""
    a,c=F(raw_lower),F(correction_upper)
    if min(a,c)<0:raise ValueError('negative squared norm')
    # sqrt(a) LOWER = a / sqrt(a)_UPPER; all arithmetic remains rational.
    root=F(0) if not a else a/sqrt_upper(a)
    lower=max(F(0),root-sqrt_upper(c))
    return down(lower*lower)


def geometry_terms(points, area, rho, thickness, metric_factor):
    p=[[exact(v) for v in row] for row in points]
    centre=[sum(row[k] for row in p)/3 for k in range(2)]
    rel=[[row[k]-centre[k] for k in range(2)] for row in p]
    moment=sum(v*v for row in rel for v in row)/12
    area=exact(area);factor=exact(metric_factor)
    if area<=0 or factor<1:raise ValueError('invalid cached triangle metric')
    return p,rel,moment,exact(rho)/exact(thickness)/(4*area),factor


def rt_energy_lower(points, area, flux, rho, thickness, metric_factor):
    """Exact positive RT polynomial formula divided by the metric envelope."""
    p,rel,moment,scale,factor=geometry_terms(points,area,rho,thickness,metric_factor)
    q=[exact(v) for v in flux]
    value=moment*sum(q)**2+sum(sum(q[i]*rel[i][k] for i in range(3))**2 for k in range(2))
    return down(scale*value/factor)


def binary_p1_energy_upper(points, area, values, rho, thickness, metric_factor):
    """For binary nodal values, a nonconstant cell is ±one barycentric basis."""
    values=list(map(int,values))
    if any(v not in (0,1) for v in values):raise ValueError('binary bubble values required')
    if len(set(values))==1:return 0.
    p,_,_,_,factor=geometry_terms(points,area,rho,thickness,metric_factor)
    minority=1 if sum(values)==1 else 0
    i=values.index(minority);j,k=[a for a in range(3) if a!=i]
    length_squared=sum((p[j][a]-p[k][a])**2 for a in range(2))
    return upward(length_squared*exact(thickness)/(4*exact(area)*exact(rho))*factor)


def axial_gap_lower(ports, bands, inner_radius, rho):
    """No internal basis solve: axial cut Cauchy in each dielectric gap.

    The exact balanced projector is the retained barrel basis trace. Shell
    annulus area uses pi<=22/7, hence the resistance/energy expression is lower.
    Collar/flange/band energies are nonnegative and omitted explicitly here.
    """
    count=len(ports);n=len(bands)
    if not count or count%n:raise ValueError('ports do not match foil bands')
    per=count//n;cols=len(ports[0])
    ri=F(math.nextafter(float(inner_radius),-math.inf))
    ro=F(math.nextafter(float(inner_radius)+.025,math.inf))
    area_upper=F(22,7)*(ro*ro-ri*ri)
    result=[]
    for col in range(cols):
        raw=[exact(row[col]) for row in ports];mean=sum(raw)/count
        balanced=[x-mean for x in raw];cut=F(0);energy=F(0)
        for band in range(n-1):
            cut+=sum(balanced[band*per:(band+1)*per])
            gap=exact(bands[band+1][0])-exact(bands[band][1])
            if gap<=0:raise ValueError('nonpositive dielectric gap')
            energy+=F(rho)*gap*cut*cut/area_upper
        result.append(down(energy))
    return result


def choose_cells_and_bubble(sheet, bounds, guard=F(2,10**9)):
    """Whole-cell inclusion; zero bubble on all mesh boundaries and cut stars."""
    import numpy as np
    points=sheet.metric_xy[sheet.triangles]
    x0,y0,x1,y1=map(F,bounds);g=np.longdouble(guard.numerator)/guard.denominator
    eligible=np.all((points[:,:,0]>np.longdouble(float(x0))+g)&
                    (points[:,:,0]<np.longdouble(float(x1))-g)&
                    (points[:,:,1]>np.longdouble(float(y0))+g)&
                    (points[:,:,1]<np.longdouble(float(y1))-g),axis=1)
    # Work on the complete layer topology, not a cropped list that could hide
    # an outgoing triangle star or native/barrel boundary.
    nodal=np.zeros(len(sheet.xy),dtype=np.int8)
    nodal[np.unique(sheet.triangles[eligible])]=1
    nodal[np.unique(sheet.triangles[~eligible])]=0
    edges=np.sort(sheet.triangles[:,[[1,2],[2,0],[0,1]]].reshape(-1,2),axis=1)
    unique,counts=np.unique(edges,axis=0,return_counts=True)
    if np.any(counts>2):raise ValueError('overlapping sheet triangle incidence')
    nodal[np.unique(unique[counts==1])]=0
    if np.any(nodal[sheet.triangles[~eligible]]):raise ValueError('bubble leaves selected region')
    return eligible,nodal


def source_terms(sheet, selected, nodal, profiles, layer, rho, thickness):
    """Exact one-face functional and source-lift energy on selected whole cells.

    Source profiles and source triangles use the original exact 1-pm grid.
    The bubble is depth-constant, so the vertical field has zero dot product
    with its gradient; its physical boundary trace still supplies f(psi).
    """
    import numpy as np
    import shapely
    from scripts.pcbgen.sheet_flux import grid_area_twice
    loads=[F(0),F(0)];lifts=[F(0),F(0)];covered=[0,0]
    for column,profile in enumerate(profiles):
        density={}
        for pl,patch,sign in profile:
            if pl!=layer:continue
            total=F(grid_area_twice(patch),2*10**18)
            if total<=0:raise ValueError('empty finite source profile')
            for i in sheet.tree.query(patch,predicate='intersects'):
                if not selected[i]:continue
                overlap=sheet.polygons[i].intersection(patch).area
                if overlap<=1e-18:continue
                grid=np.rint(sheet.metric_xy[sheet.triangles[i]]*10**9).astype(np.int64)
                contained=False
                for part in shapely.get_parts(patch):
                    if not part.equals(shapely.box(*part.bounds)):
                        raise ValueError('rectangular finite source components required')
                    x0,y0,x1,y1=[round(v*10**9) for v in part.bounds]
                    if np.all((grid[:,0]>=x0)&(grid[:,0]<=x1)&(grid[:,1]>=y0)&(grid[:,1]<=y1)):
                        contained=True;break
                if not contained:
                    raise ValueError('source cut is not an exact complete grid triangle')
                density[int(i)]=density.get(int(i),F(0))+F(sign)/total
        for i,d in density.items():
            p=sheet.metric_xy[sheet.triangles[i]]
            grid=np.rint(p*10**9).astype(np.int64)
            if np.max(abs(p-grid.astype(np.longdouble)/np.longdouble(10**9)))>1e-15:
                raise ValueError('source triangle is not on the exact source grid')
            a,b,c=grid.tolist()
            area=F(abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0])),2*10**18)
            loads[column]+=d*area*sum(int(v) for v in nodal[sheet.triangles[i]])/3
            lifts[column]+=F(rho)*F(thickness)/3*area*d*d
            covered[column]+=1
    return loads,[down(x) for x in lifts],covered


def validate_links(manifest, pair):
    bound={str(Path(k).resolve()):v for k,v in pair['input_sha256'].items()}
    for key in ('current_mesh','profiles','native','full_receipt'):
        path=manifest[key]
        if path not in manifest['input_sha256'] or str(Path(path).resolve()) not in bound or bound[str(Path(path).resolve())]!=manifest['input_sha256'][path]:
            raise ValueError('diagnostic input is not bound by the paired receipt: '+key)
    if manifest['input_sha256'].get(manifest['fields'])!=pair['raw_field_artifacts']['current-fields.npz']:
        raise ValueError('current fields differ from paired receipt')


def validate_union(terminals, ownership):
    """Disjoint full terminal/ownership identity checks before summing floors."""
    import shapely
    if sorted(t['ref'] for t in terminals)!=['TP990031','TP990033','TP990035']:
        raise ValueError('exact three retained P main terminals required')
    ids=[row['uuid'] for row in ownership]
    if len(set(ids))!=len(ids):raise ValueError('duplicate native barrel ownership')
    used=set();polygons=[]
    for terminal in terminals:
        polygon=shapely.geometry.shape(terminal['maximum_wetting_geojson'])
        if terminal['layer']!=3 or polygon.geom_type!='Polygon' or not polygon.equals(shapely.box(*polygon.bounds)):
            raise ValueError('retained B-foil rectangular wetting region required')
        if any(polygon.intersection(p).area>0 for p in polygons):
            raise ValueError('overlapping wetting regions')
        polygons.append(polygon)
        rows=terminal['tied_barrels']
        if len(rows)!=25 or len(set(rows))!=25 or any(type(i)!=int or not 0<=i<len(ownership) for i in rows):
            raise ValueError('exact native 25-barrel tie set required')
        if used.intersection(rows):raise ValueError('barrel assigned to two terminal regions')
        used.update(rows)
    return len(used)


def run(manifest_path, output):
    import numpy as np
    import shapely
    from scripts.pcbgen.foil_stack import resolve_stack
    start=time.monotonic();m=json.loads(Path(manifest_path).read_text());out=Path(output)
    if out.exists():raise ValueError('fresh output directory required')
    if not out.resolve().is_relative_to(Path('.circuit-cache').resolve()):raise ValueError('output must remain ignored')
    verify_hashes(m['input_sha256']);verify_hashes(m['helper_sha256'])
    pair=json.loads(Path(m['pair_receipt']).read_text());old=json.loads(Path(m['full_receipt']).read_text())
    verify_hashes(pair['input_sha256']);validate_links(m,pair)
    restriction=old['counts']['potential']['wetted_terminal_trial_restriction']
    validate_union(restriction['terminals'],old['barrel_ownership'])
    if pair['matrix_indices']!=[4,128] or pair['reference_contact']['ref']!='TP990031':raise ValueError('wrong preserved P pair')
    cache_key,sheets=pickle.loads(Path(m['current_mesh']).read_bytes())
    if cache_key!=m['current_cache_key']:raise ValueError('mesh epoch changed')
    profile_rows=json.loads(Path(m['profiles']).read_text())['profiles']
    lookup={(p['ref'],p['pad']):p for p in profile_rows}
    ref=lookup[('TP990031','1')]
    profiles=[]
    for identity in [('J900134','2'),('C107','2')]:
        p=lookup[identity]
        profiles.append([(p['layer'],shapely.geometry.shape(p['patch_geojson']),1),
                         (ref['layer'],shapely.geometry.shape(ref['patch_geojson']),-1)])
    native=json.loads(Path(m['native']).read_text());stack=resolve_stack(native['stackup'],native['thickness_mm'])
    rho=1.7241e-5*(1+.003947*50)
    own={str(Path(manifest_path)):sha(manifest_path),str(Path(__file__)):sha(__file__)}
    correction=pair['raw_to_conserved']['combined_energy_upper_ohm']
    rows=[];raw_union=[F(0),F(0)];forced_union=[F(0),F(0)]
    with np.load(m['fields']) as fields:
        for terminal in restriction['terminals']:
            polygon=shapely.geometry.shape(terminal['maximum_wetting_geojson'])
            if polygon.geom_type!='Polygon' or not polygon.equals(shapely.box(*polygon.bounds)):
                raise ValueError('exact axis-aligned wetting rectangle required')
            layer=terminal['layer'];sheet=sheets[layer];t=stack['thickness'][layer]
            selected,nodal=choose_cells_and_bubble(sheet,polygon.bounds)
            ids=np.flatnonzero(selected);flux=fields['sheet_flux_'+str(layer)]
            raw=[F(0),F(0)];denominator=F(0)
            for i in ids:
                pts=sheet.metric_xy[sheet.triangles[i]];area=sheet.areas[i];factor=sheet.metric_factors[i]
                for k in range(2):raw[k]+=F(rt_energy_lower(pts,area,flux[i,:,k],rho,t,factor))
                denominator+=F(binary_p1_energy_upper(pts,area,nodal[sheet.triangles[i]],rho,t,factor))
            loads,lift,count=source_terms(sheet,selected,nodal,profiles,layer,rho,t)
            for k in range(2):raw[k]+=F(lift[k])
            gap_lower=[F(0),F(0)]
            for ib in terminal['tied_barrels']:
                owner=old['barrel_ownership'][ib]
                values=axial_gap_lower(fields['barrel_port_'+str(ib)],stack['bands'],F(owner['finished_drill_mm'])/2,F(rho))
                for k in range(2):gap_lower[k]+=F(values[k]);raw[k]+=F(values[k])
            forced=[bubble_floor(loads[k],denominator) for k in range(2)]
            for k in range(2):raw_union[k]+=raw[k];forced_union[k]+=F(forced[k])
            rows.append({'ref':terminal['ref'],'layer':layer,'wetting_bounds_mm':list(polygon.bounds),
                'whole_current_triangles':len(ids),'nonzero_bubble_vertices':int(nodal.sum()),
                'tied_barrel_indices':terminal['tied_barrels'],'source_triangles_in_subset':count,
                'bubble_load_exact':[str(x) for x in loads],
                'bubble_energy_upper_S':upward(denominator),
                'restriction_forced_floor_ohm':forced,
                'source_vertical_lift_lower_ohm':lift,
                'barrel_gap_trace_energy_lower_ohm':[down(x) for x in gap_lower],
                'raw_mismatch_energy_lower_ohm':[down(x) for x in raw],
                'present_conserved_mismatch_lower_ohm':[corrected_lower(raw[k],correction[k]) for k in range(2)]})
    gaps=[F(pair['matrices_ohm']['gap'][k][k]) for k in range(2)]
    present=[corrected_lower(raw_union[k],correction[k]) for k in range(2)]
    result={'status':'NO-SOLVE NOMINAL RESTRICTION DIAGNOSTIC; no hardware/common admission',
        'source_pair':pair['selected_columns'],'reference_contact':pair['reference_contact'],
        'input_sha256':{**m['input_sha256'],**m['helper_sha256'],**own},'terminals':rows,
        'union_present_trial_mismatch_lower_ohm':present,
        'union_restriction_forced_floor_ohm':[down(x) for x in forced_union],
        'retained_variational_gap_ohm':[float(x) for x in gaps],
        'present_lower_fraction_of_retained_gap':[down(F(present[k])/gaps[k]) for k in range(2)],
        'forced_floor_fraction_of_retained_gap':[down(forced_union[k]/gaps[k]) for k in range(2)],
        'scope':['Whole-cell B-foil subsets and tied whole barrel gap volumes are disjoint.',
            'Potential is exactly constant there by the retained trial restriction, not physical equipotentiality.',
            'Present field lower bound is not an irreducible floor for a different current trial.',
            'Bubble floor holds for every conserved current with the SAME full finite source traces.',
            'Exact source functional includes the external-face normal trace of the vertical lift.',
            'Reported fractions use the retained upper variational gap including its numerical allowances.',
            'Barrel axial lower uses the exact balanced local trace, never raw internal RT divergence.',
            'The mixed raw-sheet/exact-local-barrel reference is covered by the retained global correction; retaining its extra internal-basis allowance is conservative.',
            'Barrel band/flange/collar energy outside the axial-gap lower bound is omitted nonnegative energy.',
            'No operator assembly, factorization, or linear solve was performed.'],
        'runtime_sec':time.monotonic()-start}
    verify_hashes(m['input_sha256']);verify_hashes(m['helper_sha256']);verify_hashes(pair['input_sha256']);verify_hashes(own)
    out.mkdir(parents=True);(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'receipt':str(out/'receipt.json'),'sha256':sha(out/'receipt.json'),
                     'present_lower_ohm':present,'forced_floor_ohm':result['union_restriction_forced_floor_ohm'],
                     'runtime_sec':result['runtime_sec']}),flush=True)
    return result


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest',default='design/partition/wetted-restriction-diagnostic.json')
    p.add_argument('--output',required=True);a=p.parse_args();run(a.manifest,a.output)
