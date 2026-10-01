"""Conserved current Gram with bounded same-operator trial refinement.

Finite profiles, RT/barrel reconstruction and conservation correction follow
the retained SheetVolume implementation. Only field improvement and row-wise
residual-work enclosure differ; the full operator and physical KCL gates stay.
"""
from fractions import Fraction
import numpy as np
import shapely
from scipy.sparse import coo_matrix,diags
from scripts.pcbgen.potential_refinement import refine
from scripts.pcbgen.residual_work import ResidualWork
from scripts.pcbgen.sheet_conservation import SheetConservation
from scripts.pcbgen.trial_energy import residual_work_diagonal,conserving_upper


def current_matrix(conductor,profiles,rho,thicknesses,batch_size=8):
    if conductor.certificate_mode!='current':raise ValueError('explicit current certificate mode required')
    unique=[];lookup={};wr=[];wc=[];wv=[]
    for column,profile in enumerate(profiles):
        if sum((Fraction(float(current)) for layer,patch,current in profile),Fraction())!=0:
            raise ValueError('finite source profile is not balanced')
        for layer,patch,current in profile:
            key=(layer,patch.wkb)
            if key not in lookup:lookup[key]=len(unique);unique.append((layer,patch))
            wr.append(lookup[key]);wc.append(column);wv.append(current)
    W=coo_matrix((wv,(wr,wc)),shape=(len(unique),len(profiles))).tocsc()
    offsets=np.cumsum([0]+[len(s.triangles) for s in conductor.sheets])
    sr=[];sc=[];sv=[]
    for column,(layer,patch) in enumerate(unique):
        source=conductor.trials[layer].area_current(patch,1.)
        active=np.flatnonzero(source)
        sr.extend(active+offsets[layer]);sc.extend([column]*len(active));sv.extend(source[active])
    S=coo_matrix((sv,(sr,sc)),shape=(offsets[-1],len(unique))).tocsc()@W
    hr=[];hc=[];hv=[];reciprocals=[]
    for layer,(indices,C,m,reciprocal) in enumerate(conductor.hybrid_cells):
        hr.extend(indices.ravel());hc.extend(np.repeat(np.arange(offsets[layer],offsets[layer+1]),3));hv.extend(m.ravel())
        reciprocals.extend(reciprocal)
    H=coo_matrix((hv,(hr,hc)),shape=(conductor.hybrid_matrix.shape[0],offsets[-1])).tocsc()
    basis=H@S;energy=(S.T@diags(reciprocals)@S).toarray()
    # Same one-face source-lift Gram, including overlapping supports and the
    # shared main-contact cross terms. Real external F/B faces remain distinct.
    gr=[];gc=[];gv=[]
    for layer in range(len(conductor.sheets)):
        ids=[i for i,(l,p) in enumerate(unique) if l==layer]
        if not ids:continue
        patches=[unique[i][1] for i in ids];tree=shapely.STRtree(patches)
        for local,a in enumerate(patches):
            for other in tree.query(a,predicate='intersects'):
                if other<local:continue
                b=patches[other];area=a.intersection(b).area
                if area<=0:continue
                value=rho*thicknesses[layer]/3*area/(a.area*b.area)
                gr.append(ids[local]);gc.append(ids[other]);gv.append(value)
                if local!=other:gr.append(ids[other]);gc.append(ids[local]);gv.append(value)
    lift=W.T@coo_matrix((gv,(gr,gc)),shape=(len(unique),len(unique))).tocsc()@W
    energy+=lift.toarray()
    matrix=conductor.hybrid_matrix;extended=matrix.astype(np.longdouble)
    work_bound=ResidualWork(conductor.current_energy_matrix)
    source_gamma=(8+int(np.max(np.diff(basis.indptr))))*np.finfo(float).eps
    if conductor.conservation_repair is None:conductor.conservation_repair=SheetConservation(conductor)
    count=len(profiles);field_max=np.zeros(count);norm=np.zeros(count);correction_energy=np.zeros(count)
    residual=0.;correction_receipts=[];refinements=[];work_receipts=[];gate_receipts=[]
    for start in range(0,count,batch_size):
        stop=min(count,start+batch_size);rhs=basis[:,start:stop].toarray()
        field,refinement=refine(matrix,rhs,conductor.hybrid_factor,extended)
        refinements.append({'start':start,'stop':stop,**refinement})
        energy[:,start:stop]+=basis.T@field
        field_max[start:stop]=np.max(abs(field),axis=0)
        norm[start:stop],work=work_bound.one_norm(field,rhs,2*source_gamma)
        work_receipts.append({'start':start,'stop':stop,**work})
        # The energy matrix includes formation enclosures and is not the
        # hybrid solve matrix. Its work residual never substitutes for KCL.
        operator_residual=float(np.max(abs(matrix@field-rhs)))
        continuity=np.zeros_like(field);sheet_balance=0.;barrel_balance=0.
        sources=[]
        for layer,(indices,C,m,reciprocal) in enumerate(conductor.hybrid_cells):
            source=S[offsets[layer]:offsets[layer+1],start:stop].toarray();sources.append(source)
            current=conductor.hybrid_current(layer,field,source)
            sheet_balance=max(sheet_balance,float(np.max(abs(current.sum(axis=1)-source))))
            np.add.at(continuity,indices.ravel(),current.reshape(-1,stop-start))
        for G,Y,(faces,local) in zip(conductor.barrel_face_maps,conductor.barrel_field_admittances,conductor.barrel_local_maps):
            current=-Y@(local@field[faces]);barrel_balance=max(barrel_balance,float(np.max(abs(current.sum(axis=0)))))
            conductor.add_barrel_continuity(continuity,G,current)
        shared_face=float(np.max(abs(continuity)))
        local_residual=max(operator_residual,sheet_balance,barrel_balance,shared_face)
        gate_receipts.append({'start':start,'stop':stop,'operator_residual_A':operator_residual,
            'sheet_source_balance_A':sheet_balance,'barrel_balance_A':barrel_balance,'shared_face_continuity_A':shared_face})
        correction,receipt=conductor.conservation_repair.correction_energy(field,sources)
        correction_energy[start:stop]=correction;correction_receipts.append(receipt)
        residual=max(residual,local_residual)
        if local_residual>1e-8:
            raise ValueError(f'batched current envelope residual {local_residual:.12g} exceeds numerical gate at profiles {start}:{stop}')
        print('current profiles',stop,'/',count,'residual',local_residual,flush=True)
    if not np.allclose(energy,energy.T,rtol=1e-7,atol=1e-10):
        raise ValueError('native profile energy matrix violates reciprocity')
    work=residual_work_diagonal(field_max,norm)
    energy=(energy+energy.T)/2+np.diag(work)
    energy,numerical=conserving_upper(energy,correction_energy)
    return {'energy':energy,'maximum_equation_residual_A':residual,
        'unique_finite_patches':len(unique),'batch_size':batch_size,
        'maximum_residual_work_allowance_ohm':float(max(work)),
        'residual_work_allowance_by_profile_ohm':work.tolist(),
        'field_maximum_by_profile_ohm':field_max.tolist(),'residual_work_one_norm_by_profile_A':norm.tolist(),
        'numerical_current_allowance':numerical,'conservation_correction':correction_receipts,
        'potential_refinement':[],'current_refinement':refinements,
        'current_residual_work':work_receipts,'physical_gate_components':gate_receipts}
