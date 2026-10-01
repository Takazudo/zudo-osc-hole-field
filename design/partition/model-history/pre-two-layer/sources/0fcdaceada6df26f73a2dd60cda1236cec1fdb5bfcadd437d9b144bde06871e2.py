"""Potential-only batch witness with row-specific residual-work enclosure.

The source projection, LU/refinement, reciprocity and full residual gate match
SheetVolume's retained potential phase. Current trial construction is unchanged.
"""
from fractions import Fraction
import numpy as np
from scipy.sparse import coo_matrix
from scripts.pcbgen.potential_refinement import refine
from scripts.pcbgen.residual_work import ResidualWork
from scripts.pcbgen.trial_energy import residual_work_diagonal


def potential_matrix(conductor, profiles, batch_size=8):
    unique=[];lookup={};wr=[];wc=[];wv=[]
    for column,profile in enumerate(profiles):
        if sum((Fraction(float(current)) for layer,patch,current in profile),Fraction())!=0:
            raise ValueError('finite source profile is not balanced')
        for layer,patch,current in profile:
            key=(layer,patch.wkb)
            if key not in lookup:lookup[key]=len(unique);unique.append((layer,patch))
            wr.append(lookup[key]);wc.append(column);wv.append(current)
    W=coo_matrix((wv,(wr,wc)),shape=(len(unique),len(profiles))).tocsc()
    rows=[];cols=[];values=[]
    for column,(layer,patch) in enumerate(unique):
        vector=conductor.projections[layer].T@conductor.trials[layer].nodal_area_current(patch,1.)
        active=np.flatnonzero(vector)
        rows.extend(active);cols.extend([column]*len(active));values.extend(vector[active])
    matrix=conductor.potential_matrix
    basis=coo_matrix((values,(rows,cols)),shape=(matrix.shape[0],len(unique))).tocsc()@W
    count=len(profiles);energy=np.zeros((count,count))
    maximum=np.zeros(count);norm=np.zeros(count);residual=0.
    work_bound=ResidualWork(matrix);extended=matrix.astype(np.longdouble)
    # Preserve the existing exact finite-profile/source projection enclosure.
    source_gamma=(8+int(np.max(np.diff(basis.indptr))))*np.finfo(float).eps
    refinements=[];work_receipts=[]
    for start in range(0,count,batch_size):
        stop=min(count,start+batch_size);rhs=basis[:,start:stop].toarray()
        field,receipt=refine(matrix,rhs,conductor.potential_factor,extended)
        refinements.append({'start':start,'stop':stop,**receipt})
        energy[:,start:stop]+=basis.T@field
        maximum[start:stop]=np.max(abs(field),axis=0)
        norm[start:stop],work=work_bound.one_norm(field,rhs,2*source_gamma)
        work_receipts.append({'start':start,'stop':stop,**work})
        local=work['full_equation_residual_A'];residual=max(residual,local)
        if local>1e-8:
            raise ValueError(f'batched potential envelope residual {local:.12g} exceeds numerical gate at profiles {start}:{stop}')
        print('potential profiles',stop,'/',count,'residual',local,flush=True)
    if not np.allclose(energy,energy.T,rtol=1e-7,atol=1e-10):
        raise ValueError('native profile energy matrix violates reciprocity')
    work=residual_work_diagonal(maximum,norm)
    energy=(energy+energy.T)/2-np.diag(work)
    return {'energy':energy,'maximum_equation_residual_A':residual,
        'maximum_residual_work_allowance_ohm':float(max(work)),
        'residual_work_allowance_by_profile_ohm':work.tolist(),
        'field_maximum_by_profile_ohm':maximum.tolist(),
        'residual_work_one_norm_by_profile_A':norm.tolist(),
        'potential_refinement':refinements,'potential_residual_work':work_receipts,
        'numerical_current_allowance':{},'conservation_correction':[]}
