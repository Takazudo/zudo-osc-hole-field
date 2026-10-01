"""Bounded iterative-refinement diagnostic on the retained failing operator."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.sparse import load_npz
from scipy.sparse.linalg import splu
from scripts.pcbgen.potential_refinement import refine


def diagnose(directory):
    receipt=json.loads((directory/'receipt.json').read_text())
    for name,expected in receipt['artifact_sha256'].items():
        if hashlib.sha256((directory/name).read_bytes()).hexdigest()!=expected:
            raise ValueError('captured operator artifact changed')
    K=load_npz(directory/'matrix.npz');rhs=np.load(directory/'rhs.npy');field=np.load(directory/'field.npy')
    extended=K.astype(np.longdouble);target=rhs.astype(np.longdouble)
    factor=splu(K[1:,1:].tocsc());rows=[];original=field.copy()
    corrected,implementation=refine(K,rhs,factor,extended,initial=original)
    for iteration,field in enumerate((original,corrected)):
        double=K@field-rhs;accurate=extended@field.astype(np.longdouble)-target
        worst=np.unravel_index(np.argmax(abs(double)),double.shape)
        absolute=abs(K.getrow(worst[0]))@abs(field[:,worst[1]])
        row={'iteration':iteration,'double_residual_A':float(np.max(abs(double))),
             'long_double_residual_A':float(np.max(abs(accurate))),
             'gauge_residual_A':float(np.max(abs(accurate[0]))),
             'worst_double_row_column':list(map(int,worst)),
             'absolute_dot_at_worst_A':float(absolute[0])}
        rows.append(row);print(row,flush=True)
    result={'status':'Saved-system diagnostic; unchanged 1e-8 A gate, no full-board certificate',
            'capture_receipt_sha256':hashlib.sha256((directory/'receipt.json').read_bytes()).hexdigest(),
            'implementation':implementation,
            'refinement_source_sha256':hashlib.sha256(Path('scripts/pcbgen/potential_refinement.py').read_bytes()).hexdigest(),
            'rows':rows,'maximum_matrix_coefficient_S':float(np.max(abs(K.data)))}
    (directory/'refinement-implementation.json').write_text(json.dumps(result,indent=2)+'\n')
    if rows[0]['long_double_residual_A']<=1e-8 or rows[-1]['double_residual_A']>=1e-8 or rows[-1]['long_double_residual_A']>=1e-8:
        raise ValueError('exact captured failure did not recover below the unchanged gate')


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('directory',type=Path);a=p.parse_args();diagnose(a.directory)
