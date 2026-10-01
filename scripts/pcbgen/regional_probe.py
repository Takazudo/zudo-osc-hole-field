"""Two-column, hash-bound nominal P regional diagnostic; never hardware admission.

Existing solvers and native prerequisites are called unchanged. The public
conservation_repair hook records fields and the exact-tree correction envelope.
Raw spatial trials are explicitly NOT declared conserved. Their local physical
cross products are enclosed before charging the correction norm. All PCB copper
is common; no private diagonal is subtracted.
"""
from __future__ import annotations

import argparse
from fractions import Fraction
import gc
import hashlib
import json
import math
from pathlib import Path
import pickle
import time

from scripts.pcbgen.observation_support_bound import rational, sqrt_upper, upward


def down(x):
    return -upward(-x)


def corrected_region(raw, correction):
    """Enclose one exact conserved trial pair from a raw physical pair.

    correction bounds the squared COMPLETE norm of each raw-to-conserved
    difference. It may safely be reused for a region; charge it only once for
    a union. Independently valid local upper bounds need not sum below U_global.
    All quantities are ohms for normalized unit-current columns [b,s].
    """
    a, b = [rational(v, 'raw energy', True) for v in raw['energy_upper']]
    ca, cb = [rational(v, 'correction energy', True) for v in correction]
    lo, hi = [rational(v, 'cross') for v in raw['cross_interval']]
    if lo > hi:
        raise ValueError('inverted physical cross interval')
    radius = sqrt_upper(a*cb)+sqrt_upper(b*ca)+sqrt_upper(ca*cb)
    return {'energy_upper': [upward((sqrt_upper(a)+sqrt_upper(ca))**2),
                              upward((sqrt_upper(b)+sqrt_upper(cb))**2)],
            'cross_interval': [down(lo-radius), upward(hi+radius)],
            'correction_cross_radius_upper': upward(radius)}


def regional_solution_interval(trial, upper, lower):
    """Regional error theorem, without imposing additivity of local UPPERS."""
    u = [rational(x, 'whole upper', True) for x in upper]
    gap = [a-rational(b, 'whole lower') for a,b in zip(u,lower)]
    if len(gap) != 2 or min(gap) < 0:
        raise ValueError('two nonnegative complete trial gaps required')
    a,b = [rational(x, 'regional upper', True) for x in trial['energy_upper']]
    err=sqrt_upper(a*gap[1])+sqrt_upper(b*gap[0])+sqrt_upper(gap[0]*gap[1])
    lo,hi=[rational(x,'regional cross') for x in trial['cross_interval']]
    return {'transfer_interval_ohm':[down(lo-err),upward(hi+err)],
            'solution_error_radius_upper_ohm':upward(err)}


def polarization_interval(upper_gram, lower_gram):
    """Exact-rational 2x2 two-sided metric enclosure, including signed cross.

    Premise: lower_gram <= physical_gram <= upper_gram in Loewner order.
    Only the 2x2 projected matrices are needed. PSD checks reject invalid input.
    """
    U=[[rational(x,'upper Gram') for x in row] for row in upper_gram]
    L=[[rational(x,'lower Gram') for x in row] for row in lower_gram]
    if any(len(x)!=2 for x in U+L) or len(U)!=2 or len(L)!=2:
        raise ValueError('two by two Gram matrices required')
    D=[[U[i][j]-L[i][j] for j in range(2)] for i in range(2)]
    for M in (U,L,D):
        if M[0][1]!=M[1][0] or min(M[0][0],M[1][1])<0 or M[0][0]*M[1][1]<M[0][1]**2:
            raise ValueError('metric matrices or difference are not symmetric PSD')
    center=(U[0][1]+L[0][1])/2
    radius=sqrt_upper(D[0][0]*D[1][1])/2
    return {'energy_upper':[upward(U[0][0]),upward(U[1][1])],
            'cross_interval':[down(center-radius),upward(center+radius)]}


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as stream:
        for chunk in iter(lambda:stream.read(1<<20),b''):h.update(chunk)
    return h.hexdigest()


def verify_hashes(rows):
    for name,expected in rows.items():
        if sha(name)!=expected:raise ValueError('changed diagnostic input: '+name)


def sum_raw(rows):
    result={'energy_upper':[0.,0.],'cross_interval':[0.,0.]}
    for key in result:
        for i in range(2):
            total=sum((Fraction(float(row[key][i])) for row in rows),Fraction())
            result[key][i]=down(total) if key=='cross_interval' and i==0 else upward(total)
    return result


def metric_cross(local_flux, mass_upper, mass_lower):
    """Evaluate local RT metric bounds with explicit contraction roundoff.

    Inputs are physical per-cell Loewner metric bounds, not terminal Gram
    off-diagonals. Long-double contractions include a gamma allowance based on
    all absolute terms, outward conversion, and a double-coefficient allowance.
    Lower metric may be zero. Clamp only a lower energy to zero, never a cross.
    """
    import numpy as np
    q=np.asarray(local_flux,dtype=np.longdouble)
    hi=np.asarray(mass_upper,dtype=np.longdouble)
    lo=np.asarray(mass_lower,dtype=np.longdouble)
    if q.ndim!=3 or q.shape[-1]!=2 or hi.shape!=lo.shape or hi.shape!=q.shape[:2]+(q.shape[1],):
        raise ValueError('incompatible two-column cell metric dimensions')
    # Bound each evaluated Gram entry. Formation of retained physical metric
    # coefficients uses the existing geometry envelopes; this additional term
    # encloses contractions and double coefficient conversions in this exporter.
    n=max(1,q.shape[0]*q.shape[1]**2)
    eps=np.longdouble(np.finfo(np.longdouble).eps)
    gamma=64*np.finfo(float).eps+8*n*eps/(1-8*n*eps)
    if 8*n*eps>=.01:raise ValueError('contraction too large for stated rounding envelope')
    def contract(M):
        G=np.einsum('tia,tij,tjb->ab',q,M,q)
        A=np.einsum('tia,tij,tjb->ab',abs(q),abs(M),abs(q))
        return G,gamma*A
    H,eh=contract(hi);L,el=contract(lo)
    # A signed metric difference has nonnegative diagonal energy; endpoint
    # rounding may otherwise create an artificial negative width.
    diff=np.maximum(0,np.diag(H-L)+np.diag(eh+el))
    center=(H[0,1]+L[0,1])/2
    center_err=(eh[0,1]+el[0,1])/2
    radius=np.sqrt(diff[0]*diff[1])/2+center_err
    return {'energy_upper':[float(np.nextafter(float(H[i,i]+eh[i,i]),np.inf)) for i in range(2)],
            'cross_interval':[float(np.nextafter(float(center-radius),-np.inf)),
                              float(np.nextafter(float(center+radius),np.inf))],
            'contraction_roundoff_cross_ohm':float(center_err)}


def barrel_lower_mass(barrel, inner_radius, refinement):
    """Same local RT reference cells, analytical componentwise metric minima.

    No condensed upper off-diagonal is treated as physical cross energy.
    Construction follows retained BarrelVolume's u/r/z traversal and rejects
    an epoch with a different cell count. Annular collars are handled separately.
    """
    import numpy as np
    d=barrel.flange_radius;n=barrel.polygon_sides;sub=barrel.angular_subdivisions
    if sub!=refinement:raise ValueError('barrel refinement identity changed')
    chord=2*d*math.tan(math.pi/n)
    r=np.r_[np.linspace(inner_radius,inner_radius+.025,refinement+1),
            np.linspace(inner_radius+.025,d,refinement+1)[1:]]
    height=max(b for a,b in barrel.foil_bands)
    boundaries=sorted({0.,height,*[x for band in barrel.foil_bands for x in band]})
    z=[]
    for a,b in zip(boundaries,boundaries[1:]):
        inside=any(lo<=(a+b)/2<=hi for lo,hi in barrel.foil_bands)
        z.extend(np.linspace(a,b,(refinement if inside else 2*refinement)+1)[:-1])
    z=np.r_[z,height];ratios=[]
    for iu in range(n*sub):
        s0=(iu%sub)*chord/sub-chord/2;s1=s0+chord/sub
        near=0. if s0<=0<=s1 else min(abs(s0),abs(s1))
        tmin=d/(d*d+max(abs(s0),abs(s1))**2);tmax=d/(d*d+near**2)
        for ir in range(len(r)-1):
            for za,zb in zip(z,z[1:]):
                band=any(a<(za+zb)/2<b for a,b in barrel.foil_bands)
                if ir>=refinement and not band:continue
                ratio=r[ir]*tmin/(r[ir+1]*tmax)
                ratios.append(ratio*(1-128*np.finfo(float).eps))
    if len(ratios)!=len(barrel.rt_mass):raise ValueError('barrel physical cell traversal changed')
    return barrel.rt_mass*np.asarray(ratios)[:,None,None]


def source_lift_region(profiles, layer, rho, thickness):
    """Exact rational lift Gram for this probe's rectilinear 1-pm profiles.

    Arbitrary curved/non-grid intersections are deliberately refused. The
    production source projector uses the same grid-area convention. Intersecting
    axis-aligned grid polygons preserves that convention exactly.
    """
    import shapely
    from scripts.pcbgen.sheet_flux import grid_area_twice
    def area(patch):
        for part in shapely.get_parts(patch):
            if part.is_empty:continue
            for ring in [part.exterior,*part.interiors]:
                points=[tuple(round(float(v)*1e9) for v in p) for p in ring.coords]
                if any(a[0]!=b[0] and a[1]!=b[1] for a,b in zip(points,points[1:])):
                    raise ValueError('probe lift requires rectilinear source profiles')
        return F(grid_area_twice(patch),2*10**18)
    F=Fraction
    gram=[[F(0) for _ in range(2)] for _ in range(2)]
    for i,p in enumerate(profiles):
        for j,q in enumerate(profiles):
            for la,a,ia in p:
                for lb,b,ib in q:
                    if la==lb==layer:
                        overlap=a.intersection(b)
                        if overlap.area>0:
                            gram[i][j]+=F(float(rho))*F(float(thickness))/3*F(float(ia))*F(float(ib))*area(overlap)/(area(a)*area(b))
    return polarization_interval(gram,gram)


def collect_regions(volume, field, sources, geometry, profiles, rho, raw_dir):
    """Raw sheet and barrel/collar pieces; return extra barrel repair energy."""
    import numpy as np
    rows=[];saved={'hybrid_field':field};internal_correction=[Fraction(0),Fraction(0)]
    from scripts.pcbgen.positive_energy_bound import positive_quadratic_energy
    for layer,(trial,sheet,source) in enumerate(zip(volume.trials,volume.sheets,sources)):
        q=volume.hybrid_current(layer,field,source)
        saved['sheet_flux_'+str(layer)]=q;saved['sheet_sources_'+str(layer)]=source
        low=trial.mass/sheet.metric_factors[:,None,None]**2
        raw=metric_cross(q,trial.mass,low)
        # Same one-face lift including shared-main and overlapping source terms.
        # Physical F/B faces remain separate; these source components are all
        # on the single external face chosen by the immutable profile epoch.
        lift=source_lift_region(profiles,layer,rho,geometry['thickness'][layer])
        raw=sum_raw([raw,lift]);raw['id']='foil:'+geometry['active_sheet_layers'][layer]
        rows.append(raw)
    # The shell+flange RT cells and circle-to-polygon collar are disjoint from
    # sheet copper. Each full object remains common, including main arrays.
    lower_cache={}
    for ib,((barrel,centre),operator,(faces,local),Y,owner) in enumerate(zip(
            volume.barrels,volume.operators,volume.barrel_local_maps,
            volume.barrel_field_admittances,geometry['barrel_ownership'])):
        # Match the UNCHANGED evaluated port used by SheetConservation's
        # raw-to-corrected norm bound. Rebalancing here could cancel a term
        # already combined in that bound and change its reference field.
        port=-Y@(local@field[faces])
        saved['barrel_port_'+str(ib)]=port
        flux=operator['current_basis_flux']@port
        q=barrel.signs[:,:,None]*flux[barrel.cell_faces]
        if id(barrel) not in lower_cache:
            lower_cache[id(barrel)]=barrel_lower_mass(barrel,owner['finished_drill_mm']/2,geometry['_probe_refinement'])
        raw=metric_cross(q,barrel.rt_mass,lower_cache[id(barrel)])
        # Collar current metric is diagonal and nonnegative; retained analytic
        # supremum gives 0 <= M_actual <= M_upper. Polarization encloses cross.
        collar=np.diag(operator['collar_current_diagonal'])
        raw=sum_raw([raw,metric_cross(port[None,:,:],collar[None,:,:],np.zeros_like(collar)[None,:,:])])
        raw['id']='barrel:'+owner['uuid'];rows.append(raw)
        # Barrel basis has its OWN exact-tree repair, additional to the global
        # sheet/port repair. Bound arbitrary coefficient combinations by triangle
        # inequality. Include the evaluated basis contraction's roundoff norm.
        # The retained scalar was summed in long double then rounded to
        # double. Enclose both that positive sum and its final conversion;
        # one final ULP cannot cover all earlier operations.
        ce=operator['current_correction_energy_upper_ohm']
        operations=4*barrel.rt_matrix.nnz*barrel.port_count+16
        ce_gamma=Fraction(int(operations))*Fraction(float(np.finfo(np.longdouble).eps))
        if ce_gamma>=Fraction(1,100):raise ValueError('barrel repair sum exceeds envelope')
        ce_upper=[Fraction(float(np.nextafter(x,np.inf)))/(1-ce_gamma) for x in ce]
        norm=[sum((sqrt_upper(c)*Fraction(abs(float(a))) for c,a in zip(ce_upper,port[:,k])),Fraction()) for k in range(2)]
        # Forward error of this exporter's dense basis contraction. Bound the
        # positive abs(basis)*abs(port) contraction itself before applying gamma.
        basis=operator['current_basis_flux'];n=basis.shape[1]
        eps=np.finfo(float).eps;gamma=(2*n+8)*eps
        tiny=np.nextafter(0.,1.)
        product=abs(basis)@abs(port)
        positive_upper=np.nextafter((product.astype(np.longdouble)+(2*n+8)*np.longdouble(tiny))/(1-np.longdouble(gamma)),np.longdouble(np.inf))
        ferr=np.nextafter(np.asarray(positive_upper*np.longdouble(gamma)/(1-np.longdouble(gamma))+(2*n+8)*np.longdouble(tiny),dtype=float),np.inf)
        eval_energy=positive_quadratic_energy(barrel.rt_mass,ferr[barrel.cell_faces])
        for k in range(2):internal_correction[k]+=(norm[k]+sqrt_upper(Fraction(float(eval_energy[k]))))**2

    np.savez_compressed(raw_dir/'current-fields.npz',**saved)
    return rows,np.asarray([upward(x) for x in internal_correction])


def run(manifest_path, output):
    import numpy as np
    import shapely
    from scripts.pcbgen import control_model_entry
    from scripts.pcbgen.ground_volume_geometry import extract
    from scripts.pcbgen.ground_reference import ordered_profiles
    from scripts.pcbgen.sheet_volume import SheetVolume
    from scripts.pcbgen.sheet_conservation import SheetConservation
    from scripts.pcbgen.current_trial_matrix import current_matrix
    from scripts.pcbgen.potential_trial_matrix import potential_matrix
    from scripts.pcbgen.contact_constraints import restrict_wetted_terminals
    started=time.monotonic();manifest_path=Path(manifest_path);m=json.loads(manifest_path.read_text())
    output=Path(output)
    if output.exists():raise ValueError('probe output exists; use a fresh directory')
    if not output.resolve().is_relative_to(Path('.circuit-cache').resolve()):
        raise ValueError('large probe outputs must remain in ignored .circuit-cache')
    verify_hashes(m['input_sha256'])
    old=json.loads(Path(m['receipt']).read_text())
    model={str(Path(k) if k.startswith('design/') else Path('scripts/pcbgen')/k):v for k,v in old['model_source_sha256'].items()}
    verify_hashes(model)
    native=Path(m['native']);data=native.read_bytes()
    prerequisite=control_model_entry.enter(native,data,m['native_receipt'],m['native_manifest'],True,0)
    rho=1.7241e-5*(1+.003947*50)
    geometry=extract(native,rho,refinement=old['refinement'],include_loads=True,main_strands=True)
    control_model_entry.select_ports(geometry,prerequisite)
    mains,reference,ports,all_profiles,identity=ordered_profiles(geometry,0)
    if identity!=old['reference_contact'] or [reference['ref'],reference['pad']]!=m['reference'] or len(all_profiles)!=343:
        raise ValueError('full native function basis/reference changed')
    wanted=[tuple(m['observation']),tuple(m['source'])]
    keys=[(p['ref'],p['pad']) for p in ports]
    indices=[keys.index(key) for key in wanted]
    if indices!=m['matrix_indices']:raise ValueError('selected column ordering changed')
    profiles=[all_profiles[i] for i in indices]
    retained=json.loads(Path(m['profiles']).read_text())['profiles']
    if len(retained)!=len(ports)+1:raise ValueError('retained finite profile count changed')
    for p,q in zip(ports+[reference],retained):
        if (p['ref'],p['pad'],p['layer'],p['kind'])!=(q['ref'],q['pad'],q['layer'],q['kind']) or not p['patch'].equals_exact(shapely.geometry.shape(q['patch_geojson']),0):
            raise ValueError('finite profile differs from retained epoch')
    geometry['_probe_refinement']=old['refinement']
    own={str(manifest_path):sha(manifest_path),str(Path(__file__)):sha(__file__)}
    def verify():
        verify_hashes(m['input_sha256']);verify_hashes(model);verify_hashes(own)
        control_model_entry.verify_unchanged(prerequisite)
    verify();output.mkdir(parents=True)
    class Recorder(SheetConservation):
        def correction_energy(self,field,sources):
            result,receipt=super().correction_energy(field,sources)
            self.regions,self.internal=collect_regions(self.volume,field,sources,geometry,profiles,rho,output)
            self.correction=result;return result,receipt
    results={};rows=None;correction=None
    for mode in ('current','potential'):
        print('probe',mode,'load hash-bound mesh and assemble/factor; columns',indices,flush=True)
        cache_key,sheets=pickle.loads(Path(m[mode+'_mesh']).read_bytes())
        if cache_key!=m[mode+'_cache_key']:raise ValueError('mesh cache epoch key changed')
        conductor=SheetVolume(sheets,[rho/t for t in geometry['thickness']],geometry['barrels'],certificate_mode=mode)
        if mode=='current':
            recorder=Recorder(conductor);conductor.conservation_repair=recorder
            result=current_matrix(conductor,profiles,rho,geometry['thickness'],batch_size=2)
            rows=recorder.regions
            correction=[upward((sqrt_upper(Fraction(float(a)))+sqrt_upper(Fraction(float(b))))**2)
                        for a,b in zip(recorder.correction,recorder.internal)]
            correction_detail={'global_sheet_port_energy_upper_ohm':recorder.correction.tolist(),
                               'barrel_internal_energy_upper_ohm':recorder.internal.tolist(),
                               'combined_energy_upper_ohm':correction}
            # Release reference cycle before the potential factorization.
            recorder.volume=None;conductor.conservation_repair=None;del recorder
        else:
            restrict_wetted_terminals(conductor,mains)
            result=potential_matrix(conductor,profiles,batch_size=2)
        results[mode]=result
        del conductor,sheets;gc.collect();verify()
    U=results['current']['energy'];L=results['potential']['energy'];gap=U-L
    if np.linalg.eigvalsh(gap)[0]<-1e-12:raise ValueError('two-column Loewner gap is not PSD')
    union=corrected_region(sum_raw(rows),correction)
    union.update(regional_solution_interval(union,np.diag(U),np.diag(L)))
    for row in rows:
        row['conserved_trial']=corrected_region(row,correction)
        row['solution']=regional_solution_interval(row['conserved_trial'],np.diag(U),np.diag(L))
    # Whole-domain Loewner enclosure is sharper than applying regional Cauchy
    # to the complete domain. Keep both, without claiming either is the original
    # joined J/P+K common allocation or a manufactured-process certificate.
    whole=polarization_interval(U.tolist(),L.tolist())
    receipt={'status':'NOMINAL TWO-COLUMN DIAGNOSTIC ONLY; no physical/common acceptance',
        'epoch':'preserved P control-feasibility-v4 native/model/profile epoch',
        'input_sha256':{**m['input_sha256'],**model,**own},
        'native_prerequisite':prerequisite,'selected_columns':wanted,'reference_contact':identity,
        'matrix_indices':indices,'regions':rows,'all_pcb_common':union,
        'whole_transfer_interval_ohm':whole['cross_interval'],
        'matrices_ohm':{'upper':U.tolist(),'lower':L.tolist(),'gap':gap.tolist()},
        'raw_to_conserved':correction_detail,
        'solver_receipts':{k:{a:b for a,b in v.items() if a!='energy'} for k,v in results.items()},
        'raw_field_artifacts':{'current-fields.npz':sha(output/'current-fields.npz')},
        'private_regions':[], 'common_region_ids':[r['id'] for r in rows],
        'scope':['All PCB foil, main spreading, shared necks, barrels and collars are common.',
                 'External wire/contact/solder are outside this board diagnostic, not zero.',
                 'Source vertical lift is charged in its foil region, orthogonal to in-plane current.',
                 'Raw fields are not conserved; exact-tree correction energy is charged explicitly.',
                 'Regional uppers are independent; they need not sum below a tighter whole upper.',
                 'Potential lower and current upper are existing gated two-column APIs.',
                 'No source/material/contact class, private allocation, or issue38 target is admitted.'],
        'runtime_sec':time.monotonic()-started}
    verify();(output/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps({'receipt':str(output/'receipt.json'),'sha256':sha(output/'receipt.json'),
                      'whole_transfer_interval_ohm':whole['cross_interval'],
                      'regional_common_interval_ohm':union['transfer_interval_ohm']}),flush=True)
    return receipt


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',default='design/partition/common-region-probe.json')
    parser.add_argument('--output',required=True)
    args=parser.parse_args();run(args.manifest,args.output)
