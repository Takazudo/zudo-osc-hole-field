"""Optional complete-region mismatch bounds consuming an immutable capture.

Foils use Green boundary work, not a raw-current conservation assumption.
Whole potential cells strictly inside the current inner envelope give an
energy lower; all outer cells give an upper. Excluded/crossing-cell energy is
reported separately and is not called physical error or absent copper.
"""
from fractions import Fraction as F
import math
import numpy as np
from scripts.pcbgen.observation_support_bound import sqrt_upper,upward
from scripts.pcbgen.wetted_restriction_diagnostic import corrected_lower
from scripts.pcbgen.positive_energy_bound import positive_quadratic_energy


def down(x):return -upward(-x)


def exact(x):
    return F(*x.as_integer_ratio()) if hasattr(x,'as_integer_ratio') else F(x)


def balanced_collar_reference(raw, collar_upper):
    """Keep OLD exact repaired shell at raw alpha; replace ONLY collar trace.

    The old shell trace is exactly P*alpha. Giving the collar that same trace
    makes the complete local reference conserved. Its norm change from the
    old reference is purely the radial collar shift, not a recomputed shell.
    """
    a=list(map(exact,raw));d=list(map(exact,collar_upper))
    if not a or len(a)!=len(d) or min(d)<0:raise ValueError('complete nonnegative collar metric required')
    mean=sum(a)/len(a);balanced=[x-mean for x in a]
    energy=sum((weight*mean*mean for weight in d),F())
    if sum(balanced)!=0:raise ValueError('balanced reference is not exact')
    return balanced,upward(energy)


def green_work(currents, vertex_potentials, band_count, source_load, source_totals, centres):
    """Signed local boundary work and centered full-foil source functionals.

    Currents are outward from the complete barrel. Each angular trace is
    uniform current and linear potential, hence its exact mean is endpoints/2.
    The foil sees the opposite normal. Returns a foil reference work for this
    barrel set (source_load belongs to the entire foil, included once).
    """
    n=len(currents)
    if n%band_count or len(vertex_potentials)!=n or sum(map(F,currents))!=0:
        raise ValueError('complete balanced multi-foil trace required')
    per=n//band_count;band_work=[];band_currents=[]
    for layer in range(band_count):
        lo=layer*per;work=F(0);net=F(0)
        for sector in range(per):
            i=lo+sector;j=lo+(sector+1)%per
            current=F(currents[i]);mean=(F(vertex_potentials[i])+F(vertex_potentials[j]))/2
            work+=current*mean;net+=current
        band_work.append(work);band_currents.append(net)
    barrel=sum(band_work,F())
    foil=[]
    for i in range(band_count):
        # The centered finite source is f(v-c)=f(v)-c*f(1), not f(v).
        c=F(centres[i]);centered_work=band_work[i]-c*band_currents[i]
        centered_load=F(source_load[i])-c*F(source_totals[i])
        foil.append(-centered_work-centered_load)
    return barrel,foil,band_currents


def foil_extension_trace(values, layer, band_count, centre):
    if len(values)%band_count or not 0<=layer<band_count:raise ValueError('invalid foil test extension')
    per=len(values)//band_count
    return [F(value)-F(centre) if i//per==layer else F(0) for i,value in enumerate(values)]


def complete_foil_work(boundary_work, boundary_net, source_load, source_net, centre):
    """One complete foil after ALL barrel contributions have been accumulated."""
    c=F(centre)
    return -(F(boundary_work)-c*F(boundary_net))-(F(source_load)-c*F(source_net))


def combine_norms(*energies):
    return upward(sum((sqrt_upper(F(x)) for x in energies),F())**2)


def quadratic_upper(matrix, coefficients, audit=None):
    """Signed quadratic plus explicit coefficient/contraction rounding.

    matrix is an existing PSD physical energy upper. Coefficients can be exact
    rationals; their conversion error is bounded separately in the same norm.
    """
    exact_coeff=list(map(F,coefficients))
    if not any(exact_coeff):return 0.
    x=np.asarray([float(v) for v in exact_coeff])
    error=np.asarray([upward(abs(v-F(float(y)))) for v,y in zip(exact_coeff,x)])
    M=np.asarray(matrix,dtype=np.longdouble);z=x.astype(np.longdouble)
    if M.shape!=(len(x),len(x)) or not np.isfinite(M).all():raise ValueError('invalid local energy operator')
    value=np.sum(z*(M@z),dtype=np.longdouble)
    absolute=np.sum(abs(z)*(abs(M)@abs(z)),dtype=np.longdouble)
    ops=4*len(x)**2+16;eps=np.finfo(np.longdouble).eps
    if ops*eps>=.01:raise ValueError('local contraction arithmetic envelope exceeded')
    radius=absolute*(ops*eps/(1-ops*eps))
    upper=float(np.nextafter(float(value+radius),np.inf))
    if upper<0:raise ValueError('negative upper for a positive energy operator')
    coefficient_error=float(positive_quadratic_energy(matrix,error[:,None])[0])
    if audit is not None:
        audit['nonzero_quadratic_calls']=audit.get('nonzero_quadratic_calls',0)+1
        audit['maximum_coefficient_error_energy_ohm']=max(audit.get('maximum_coefficient_error_energy_ohm',0.),coefficient_error)
        audit['maximum_contraction_roundoff_ohm']=max(audit.get('maximum_contraction_roundoff_ohm',0.),float(np.nextafter(float(radius),np.inf)))
    return combine_norms(max(0.,upper),coefficient_error)


def mismatch_interval(q_interval,v_interval,work_interval,global_gap=None):
    qlo,qhi=map(F,q_interval);vlo,vhi=map(F,v_interval);wlo,whi=map(F,work_interval)
    if min(qlo,vlo)<0 or qlo>qhi or vlo>vhi or wlo>whi:raise ValueError('invalid energy/work intervals')
    low=qlo+vlo+2*wlo;high=qhi+vhi+2*whi
    if high<0 or low>high:raise ValueError('impossible negative/inverted mismatch interval')
    low=max(F(0),low)  # Nonnegativity can improve a lower bound, never an upper.
    if global_gap is not None:
        high=min(high,F(global_gap))
        if low>high:raise ValueError('regional mismatch contradicts complete gap')
    return [down(low),upward(high)]


def check_complete_mismatch(region_intervals,gap):
    gap=F(gap)
    if gap<0 or sum((F(x[0]) for x in region_intervals),F())>gap:
        raise ValueError('summed regional lower bounds contradict complete gap')


def diagonal_metric_interval(flux, upper, lower):
    """Use two-sided polarization with equal columns, not upper off-diagonals."""
    from scripts.pcbgen.regional_probe import metric_cross
    result=metric_cross(np.repeat(flux[:,:,None],2,axis=2),upper,lower)
    lo,hi=result['cross_interval']
    if hi<0:raise ValueError('negative physical diagonal energy upper')
    return max(0.,lo),min(hi,result['energy_upper'][0])


def sheet_energy_bounds(sheet, values, errors, rho, thickness, kind, inner=None, block=8192):
    """Stream complete cells; never classify a crossing cell by its centroid."""
    import shapely
    totals=[[F(0),F(0)] for _ in range(2)];excluded=[F(0),F(0)];inside_count=0
    inner_guard=inner.buffer(-2e-9,join_style='mitre') if inner is not None else None
    if inner_guard is not None:shapely.prepare(inner_guard)
    for start in range(0,len(sheet.triangles),block):
        ids=np.arange(start,min(start+block,len(sheet.triangles)))
        triangles=sheet.triangles[ids];xy=sheet.metric_xy[triangles]
        area=sheet.areas[ids];factor=sheet.metric_factors[ids]
        if kind=='current':
            relative=xy-xy.mean(axis=1)[:,None,:]
            moment=np.sum(relative*relative,axis=(1,2))/12
            mass=np.asarray((rho/thickness)*(moment[:,None,None]+np.einsum('tik,tjk->tij',relative,relative))/(4*area[:,None,None])*factor[:,None,None],dtype=float)
            q=values[ids];delta=None;inside=np.ones(len(ids),dtype=bool)
        elif kind=='potential':
            dx=xy[:,[1,2,0],1]-xy[:,[2,0,1],1]
            dy=xy[:,[2,0,1],0]-xy[:,[1,2,0],0]
            mass=np.asarray((dx[:,:,None]*dx[:,None,:]+dy[:,:,None]*dy[:,None,:])/(4*area[:,None,None]*(rho/thickness))*factor[:,None,None],dtype=float)
            raw=values[triangles].astype(np.longdouble)
            diff=raw-raw[:,:1];q=np.asarray(diff,dtype=float)
            # The same nodal anchor cancels exactly in row0. Other differences
            # include both endpoint export errors and explicit subtraction/
            # conversion error, not a single final nextafter.
            de=errors[triangles].astype(np.longdouble)+errors[triangles[:,:1]].astype(np.longdouble)
            de+=2*np.finfo(np.longdouble).eps*(abs(raw)+abs(raw[:,:1]))+abs(diff-q.astype(np.longdouble))
            de[:,0]=0;q[:,0]=0
            delta=np.nextafter(np.asarray(de,dtype=float),np.inf);delta[:,0]=0
            polys=shapely.polygons(np.asarray(xy,dtype=float))
            inside=shapely.covers(inner_guard,polys) if inner_guard is not None else np.ones(len(ids),dtype=bool)
        else:raise ValueError('unknown physical sheet field kind')
        lower=mass/factor[:,None,None]**2;inside_count+=int(inside.sum())
        for k in range(2):
            # Upper integrates every outer cell. Lower includes only complete
            # cells certified inside the inner physical copper envelope.
            low,high=diagonal_metric_interval(q[:,:,k],mass,lower)
            ce=0. if delta is None else float(positive_quadratic_energy(mass,delta[:,:,k:k+1])[0])
            high=combine_norms(high,ce)
            if inside.all():low=corrected_lower(low,ce)
            elif inside.any():
                a,b=diagonal_metric_interval(q[inside,:,k],mass[inside],lower[inside])
                e=0. if delta is None else float(positive_quadratic_energy(mass[inside],delta[inside,:,k:k+1])[0])
                low=corrected_lower(a,e)
            else:low=0.
            totals[k][0]+=F(low);totals[k][1]+=F(high)
            if (~inside).any():
                _,b=diagonal_metric_interval(q[~inside,:,k],mass[~inside],lower[~inside])
                e=0. if delta is None else float(positive_quadratic_energy(mass[~inside],delta[~inside,:,k:k+1])[0])
                excluded[k]+=F(combine_norms(b,e))
    return {'energy_interval_ohm':[[down(a),upward(b)] for a,b in totals],
            'guaranteed_inner_cells':inside_count,'outer_cells':len(sheet.triangles),
            'excluded_or_crossing_cell_energy_upper_ohm':[upward(x) for x in excluded],
            'geometry_scope':'Excluded cells may contain real copper; their upper energy is not identified as physical error.'}


def finite_source_loads(sheets, unit_indices, field, rhs, profiles):
    """Exact physical P1 source load on the SAME unit reduced nodal traces."""
    import shapely
    from scripts.pcbgen.sheet_flux import grid_area_twice
    loads=[[F(0),F(0)] for _ in sheets];net=[[F(0),F(0)] for _ in sheets]
    absolute=[F(0),F(0)];counts=[0,0]
    for k,profile in enumerate(profiles):
        for layer,patch,current in profile:
            sheet=sheets[layer];denom=grid_area_twice(patch);represented=0
            if denom<=0:raise ValueError('empty source profile')
            net[layer][k]+=F(current)
            rectangles=[]
            for part in shapely.get_parts(patch):
                if not part.equals(shapely.box(*part.bounds)):raise ValueError('rectangular source components required')
                rectangles.append([round(x*10**9) for x in part.bounds])
            for i in sheet.tree.query(patch,predicate='intersects'):
                if sheet.polygons[i].intersection(patch).area<=1e-18:continue
                vertices=sheet.triangles[i];p=sheet.metric_xy[vertices]
                grid=np.rint(p*10**9).astype(np.int64)
                if np.max(abs(p-grid.astype(np.longdouble)/np.longdouble(10**9)))>1e-15:
                    raise ValueError('source vertices leave exact grid convention')
                if not any(np.all((grid[:,0]>=x0)&(grid[:,0]<=x1)&(grid[:,1]>=y0)&(grid[:,1]<=y1)) for x0,y0,x1,y1 in rectangles):
                    raise ValueError('source profile partially cuts a potential triangle')
                a,b,c=grid.tolist();area2=abs((b[0]-a[0])*(c[1]-a[1])-(b[1]-a[1])*(c[0]-a[0]))
                indices=unit_indices[layer][vertices]
                if np.any(indices<0):raise ValueError('source potential needs a non-unit projection; functional not established')
                v=[exact(field[index,k]) for index in indices]
                weight=F(current)*F(area2,denom)
                loads[layer][k]+=weight*sum(v)/3
                absolute[k]+=abs(weight)*sum(map(abs,v))/3
                represented+=area2;counts[k]+=1
            if represented!=denom:raise ValueError('finite source coverage is not exact and complete')
    discrepancies=[]
    for k in range(2):
        discrete=sum((exact(rhs[i,k])*exact(field[i,k]) for i in np.flatnonzero(rhs[:,k])),F())
        physical=sum((row[k] for row in loads),F())
        n=4*counts[k]+64;g=F(n)*F(float(np.finfo(float).eps))
        if g>=F(1,100):raise ValueError('source arithmetic envelope too large')
        limit=g/(1-g)*absolute[k]
        if abs(physical-discrete)>limit:raise ValueError('finite source functional disagrees with captured operand beyond rounding')
        discrepancies.append({'exact_physical_load':str(physical),'exact_discrete_rhs_work':str(discrete),
                              'difference_upper_ohm':upward(abs(physical-discrete)),
                              'source_accumulation_allowance_ohm':upward(limit)})
    return loads,net,discrepancies


def analyze(capture_path, output):
    """No global solve: consume captured coefficients and prior current fields."""
    import argparse,gc,hashlib,json,pickle,time
    from pathlib import Path
    import shapely
    from scripts.pcbgen.regional_probe import sha,verify_hashes,source_lift_region
    from scripts.pcbgen.ground_volume_geometry import extract
    from scripts.pcbgen.wetted_restriction_diagnostic import axial_gap_lower
    started=time.monotonic();capture_path=Path(capture_path);raw=capture_path.read_bytes();capture=json.loads(raw)
    manifest_path=Path(capture['manifest']);manifest_bytes=manifest_path.read_bytes();m=json.loads(manifest_bytes);out=Path(output)
    if hashlib.sha256(manifest_bytes).hexdigest()!=capture['input_sha256'].get(str(manifest_path)):
        raise ValueError('parsed manifest differs from captured bytes')
    if out.exists():raise ValueError('fresh localization directory required')
    if not out.resolve().is_relative_to(Path('.circuit-cache').resolve()):raise ValueError('localization artifacts must remain ignored')
    own={str(capture_path):hashlib.sha256(raw).hexdigest(),str(manifest_path):hashlib.sha256(manifest_bytes).hexdigest(),str(Path(__file__)):sha(__file__)}
    field_path=capture_path.parent/'potential-fields.npz'
    own[str(field_path)]=capture['artifact_sha256']['potential-fields.npz']
    def verify():
        verify_hashes(own);verify_hashes(capture['input_sha256'])
        verify_hashes(capture['native_prerequisite']['dependency_sha256'])
    verify()
    pair=json.loads(Path(m['pair_receipt']).read_text());old=json.loads(Path(m['full_receipt']).read_text())
    rows_by_id={r['id']:r for r in pair['regions']}
    if len(rows_by_id)!=len(pair['regions']):raise ValueError('duplicate retained current regions')
    profile_rows=json.loads(Path(m['profiles']).read_text())['profiles'];lookup={(p['ref'],p['pad']):p for p in profile_rows}
    reference=lookup[('TP990031','1')];profiles=[]
    for identity in [('J900134','2'),('C107','2')]:
        p=lookup[identity]
        profiles.append([(p['layer'],shapely.geometry.shape(p['patch_geojson']),1),
                         (reference['layer'],shapely.geometry.shape(reference['patch_geojson']),-1)])
    rho=1.7241e-5*(1+.003947*50)
    print('localization: rebuild unchanged LOCAL barrel operators; no global factor or solve',flush=True)
    geometry=extract(m['native'],rho,refinement=old['refinement'],include_loads=True,main_strands=True)
    if geometry['barrel_ownership']!=old['barrel_ownership']:raise ValueError('barrel ownership epoch changed')
    operator_cache={};operators=[]
    for barrel,_ in geometry['barrels']:
        if id(barrel) not in operator_cache:operator_cache[id(barrel)]=barrel.condensed_operators()
        operators.append(operator_cache[id(barrel)])
    _,potential_sheets=pickle.loads(Path(m['potential_mesh']).read_bytes())
    with np.load(field_path) as fields:
        reduced=fields['reduced_field'];rhs=fields['rhs'];ports=fields['port_values']
        indices=[fields['node_reduced_index_'+str(l)] for l in range(4)]
        loads,net,load_receipts=finite_source_loads(potential_sheets,indices,reduced,rhs,profiles)
        potential=[]
        for layer,sheet in enumerate(potential_sheets):
            print('localization: potential foil',layer,flush=True)
            potential.append(sheet_energy_bounds(sheet,fields['nodal_'+str(layer)],fields['nodal_error_'+str(layer)],rho,
                geometry['thickness'][layer],'potential',geometry['inner'][layer]))
    del potential_sheets;gc.collect()
    _,current_sheets=pickle.loads(Path(m['current_mesh']).read_bytes())
    current_foil=[];base_c=pair['raw_to_conserved']['combined_energy_upper_ohm']
    with np.load(m['current_fields']) as current_fields:
        for layer,sheet in enumerate(current_sheets):
            print('localization: retained current foil',layer,flush=True)
            energy=sheet_energy_bounds(sheet,current_fields['sheet_flux_'+str(layer)],None,rho,geometry['thickness'][layer],'current')
            bounds=[]
            region=rows_by_id['foil:'+geometry['active_sheet_layers'][layer]]
            for k in range(2):
                lift=source_lift_region([profiles[k],profiles[k]],layer,rho,geometry['thickness'][layer])['cross_interval']
                lower=F(energy['energy_interval_ohm'][k][0])+F(lift[0]);upper=F(energy['energy_interval_ohm'][k][1])+F(lift[1])
                lo=corrected_lower(lower,base_c[k]);hi=min(combine_norms(upper,base_c[k]),region['conserved_trial']['energy_upper'][k])
                if lo>hi:raise ValueError('current foil lower contradicts retained conserving upper')
                bounds.append([lo,hi])
            current_foil.append(bounds)
        del current_sheets;gc.collect()
        band_count=4;offsets=np.cumsum([0]+[b.port_count for b,_ in geometry['barrels']])
        # One center per COMPLETE foil, chosen before any barrel accumulation.
        centres=[[F(0),F(0)] for _ in range(4)];counts=[0]*4
        for ib,(barrel,_) in enumerate(geometry['barrels']):
            n=barrel.angular_count
            for layer in range(4):
                sl=slice(offsets[ib]+layer*n,offsets[ib]+(layer+1)*n)
                for k in range(2):centres[layer][k]+=sum((exact(x) for x in ports[sl,k]),F())
                counts[layer]+=n
        for layer in range(4):
            centres[layer]=[v/counts[layer] for v in centres[layer]]
        arithmetic_audit={}
        projection=[F(0),F(0)];test_energy=[[F(0),F(0)] for _ in range(4)]
        band_work=[[F(0),F(0)] for _ in range(4)];band_net=[[F(0),F(0)] for _ in range(4)]
        barrels=[]
        for ib,((barrel,_),op,owner) in enumerate(zip(geometry['barrels'],operators,geometry['barrel_ownership'])):
            raw_port=current_fields['barrel_port_'+str(ib)]
            v=ports[offsets[ib]:offsets[ib+1]];references=[];energies=[];works=[];shifts=[]
            for k in range(2):
                balanced,shift=balanced_collar_reference(raw_port[:,k],op['collar_current_diagonal'])
                references.append(balanced);projection[k]+=F(shift);shifts.append(shift)
                exact_v=list(map(exact,v[:,k]));anchored=[x-exact_v[0] for x in exact_v]
                ev=quadratic_upper(op['potential_energy_upper'],anchored,arithmetic_audit);energies.append(ev)
                n=barrel.angular_count;work=F(0)
                for layer in range(4):
                    local=F(0);total=F(0)
                    for sector in range(n):
                        i=layer*n+sector;j=layer*n+(sector+1)%n
                        local+=balanced[i]*(exact_v[i]+exact_v[j])/2;total+=balanced[i]
                    band_work[layer][k]+=local;band_net[layer][k]+=total;work+=local
                    extension=foil_extension_trace(exact_v,layer,4,centres[layer][k])
                    extension=[x-extension[0] for x in extension] # safe whole-barrel constant
                    test_energy[layer][k]+=F(quadratic_upper(op['potential_energy_upper'],extension,arithmetic_audit))
                works.append(work)
            trace_rows=list(zip(*references))
            lower=axial_gap_lower(trace_rows,barrel.foil_bands,F(owner['finished_drill_mm'])/2,F(rho))
            barrels.append({'id':'barrel:'+owner['uuid'],'work':works,'potential_upper':energies,
                'reference_current_lower':lower,'collar_projection_energy_upper':shifts})
    trace_c=[combine_norms(base_c[k],projection[k]) for k in range(2)]
    result_rows=[]
    for layer,name in enumerate(geometry['active_sheet_layers']):
        row={'id':'foil:'+name,'current_energy_interval_ohm':current_foil[layer],
             'potential_energy_interval_ohm':potential[layer]['energy_interval_ohm'],
             'potential_envelope':potential[layer],'work_interval_ohm':[],
             'centering_potential_exact':[str(x) for x in centres[layer]],
             'finite_source_load_exact':[str(x) for x in loads[layer]],
             'finite_source_net_current_exact':[str(x) for x in net[layer]],
             'reference_layer_balance_residual_A':[str(band_net[layer][k]+net[layer][k]) for k in range(2)]}
        for k in range(2):
            c=centres[layer][k]
            # Complete source load occurs ONCE here, after accumulating every
            # barrel. Same center in interface and finite source terms.
            work=complete_foil_work(band_work[layer][k],band_net[layer][k],loads[layer][k],net[layer][k],c)
            radius=sqrt_upper(F(trace_c[k])*test_energy[layer][k])
            row['work_interval_ohm'].append([down(work-radius),upward(work+radius)])
        result_rows.append(row)
    for b in barrels:
        old_region=rows_by_id[b['id']];q=[];w=[]
        for k in range(2):
            q.append([corrected_lower(b['reference_current_lower'][k],trace_c[k]),old_region['conserved_trial']['energy_upper'][k]])
            radius=sqrt_upper(F(trace_c[k])*F(b['potential_upper'][k]))
            w.append([down(b['work'][k]-radius),upward(b['work'][k]+radius)])
        result_rows.append({'id':b['id'],'current_energy_interval_ohm':q,
            'potential_energy_interval_ohm':[[0.,u] for u in b['potential_upper']],
            'work_interval_ohm':w,'collar_projection_energy_upper_ohm':b['collar_projection_energy_upper']})
    if {r['id'] for r in result_rows}!=set(rows_by_id) or len(result_rows)!=len(rows_by_id):
        raise ValueError('incomplete or duplicate complete physical region partition')
    # Independent dual evaluation of the canonical continuous trace. It may
    # be looser than the API's lower, and is reported rather than hidden.
    dual=[];global_gap=[];api_gap=[]
    for k in range(2):
        ev=sum((F(r['potential_energy_interval_ohm'][k][1]) for r in result_rows),F())
        f=sum((row[k] for row in loads),F())
        dual.append(down(2*f-ev))
        g=F(pair['matrices_ohm']['upper'][k][k])-F(dual[-1])
        if g<0:raise ValueError('canonical potential dual contradicts current upper')
        global_gap.append(upward(g))
        api_gap.append(upward(F(pair['matrices_ohm']['upper'][k][k])-F(capture['potential_lower_ohm'][k][k])))
    for r in result_rows:
        r['mismatch_interval_ohm']=[mismatch_interval(r['current_energy_interval_ohm'][k],
            r['potential_energy_interval_ohm'][k],r['work_interval_ohm'][k],global_gap[k]) for k in range(2)]
    for k in range(2):check_complete_mismatch([r['mismatch_interval_ohm'][k] for r in result_rows],global_gap[k])
    result={'status':'CONDITIONAL NOMINAL COMPLETE-REGION MISMATCH BOUNDS; no physical/common admission',
        'input_sha256':{**capture['input_sha256'],**own},'regions':result_rows,
        'global_canonical_mismatch_upper_ohm':global_gap,'api_variational_gap_upper_ohm':api_gap,
        'independent_canonical_dual_lower_ohm':dual,'source_functionals':load_receipts,
        'base_current_correction_energy_upper_ohm':base_c,
        'original_current_correction_components':pair['raw_to_conserved'],
        'local_potential_coefficient_and_contraction_audit':arithmetic_audit,
        'balanced_collar_shift_energy_upper_ohm':[upward(x) for x in projection],
        'combined_trace_difference_energy_upper_ohm':trace_c,
        'foil_extension_energy_upper_ohm':[[upward(x) for x in row] for row in test_energy],
        'scope':['Complete4foils+195barrels; no private diagonal subtraction or changed source/copper/restriction.',
            'Green foil source work is included once, with the same whole-foil centering constant.',
            'Reference uses old repaired shell plus balanced collar; no identification of rebuilt and old current bases.',
            'Whole outer-cell energy is upper; only guarded whole cells inside inner copper contribute a lower.',
            'Excluded/crossing-cell upper energy is not claimed as physical copper error.',
            'No new global solve; unchanged local barrel bases reconstructed by existing API.',
            'Region intervals bound constitutive mismatch, not exact regional solution error or target acceptance.'],
        'runtime_sec':time.monotonic()-started}
    verify();out.mkdir(parents=True);(out/'localization.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({'localization':str(out/'localization.json'),'sha256':sha(out/'localization.json'),
                     'runtime_sec':result['runtime_sec'],'global_mismatch_upper_ohm':global_gap}),flush=True)
    return result


if __name__=='__main__':
    import argparse
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--capture',required=True);p.add_argument('--output',required=True)
    a=p.parse_args();analyze(a.capture,a.output)
