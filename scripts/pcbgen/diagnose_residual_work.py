"""Bounded saved-operator diagnosis; no refactor or new physical solve."""
import argparse
import hashlib
import json
from pathlib import Path
import numpy as np
from scipy.sparse import load_npz
from scripts.pcbgen.residual_work import ResidualWork


if __name__ == '__main__':
    parser=argparse.ArgumentParser();parser.add_argument('capture',type=Path);parser.add_argument('output',type=Path)
    args=parser.parse_args()
    matrix=load_npz(args.capture/'matrix.npz')
    field=np.load(args.capture/'field.npy');rhs=np.load(args.capture/'rhs.npy')
    absolute=abs(matrix)@abs(field)
    old_gamma=(64+max(np.diff(matrix.indptr)))*np.finfo(float).eps
    old=old_gamma*np.sum(absolute,axis=0)
    bound,report=ResidualWork(matrix).one_norm(field,rhs)
    actual_nongauge=np.sum(abs(matrix@field-rhs)[1:],axis=0)
    result={'status':'SAVED OPERATOR NUMERICAL DIAGNOSIS ONLY; source coefficient error and full 1176-profile work matrix not recomputed here',
        'capture_sha256':{name:hashlib.sha256((args.capture/name).read_bytes()).hexdigest() for name in ('receipt.json','matrix.npz','field.npy','rhs.npy')},
        'model_sha256':{name:hashlib.sha256((Path('scripts/pcbgen')/name).read_bytes()).hexdigest() for name in ('residual_work.py','diagnose_residual_work.py')},
        'matrix_shape':matrix.shape,'matrix_nnz':matrix.nnz,'old_global_operation_count':int(64+max(np.diff(matrix.indptr))),
        'old_matvec_roundoff_L1_A':old.tolist(),'evaluated_nongauge_residual_L1_A':actual_nongauge.tolist(),
        'new_residual_plus_roundoff_L1_A':bound.tolist(),'row_bound':report}
    args.output.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if not k.endswith('sha256')},indent=2))
