"""Capture the actual failed full-board potential operator without remeshing.

Run through heavy-guard with the same pinned solver environment. The original
profile function and full source basis execute unchanged through batch 160:168.
No resistance acceptance is produced by this diagnostic.
"""
import argparse
import hashlib
import inspect
import json
import pickle
import sys
from pathlib import Path

import numpy as np
from scipy.sparse import save_npz
from scripts.pcbgen.ground_volume_geometry import extract
from scripts.pcbgen.sheet_volume import SheetVolume
from scripts.pcbgen.contact_constraints import restrict_wetted_terminals


class Captured(Exception):pass


def capture(native,profile_path,mesh_path,output):
    receipt=json.loads(profile_path.read_text());hashes=receipt['model_source_sha256']
    for name,expected in hashes.items():
        path=Path(name) if name.startswith('design/') else Path('scripts/pcbgen')/name
        if hashlib.sha256(path.read_bytes()).hexdigest()!=expected:
            raise ValueError('failing operator source changed: '+str(path))
    if hashlib.sha256(native.read_bytes()).hexdigest()!=receipt['native_export_sha256']:
        raise ValueError('failing native domain changed')
    settings=(2.,.125,2,'potential',True,True,(0.,0.),True)
    expected=hashlib.sha256((receipt['native_export_sha256']+str(settings)+json.dumps(hashes,sort_keys=True)).encode()).hexdigest()
    key,sheets=pickle.loads(mesh_path.read_bytes())
    if key!=expected:raise ValueError('failing full-domain mesh cache key differs')
    rho=1.7241e-5*(1+.003947*50)
    geometry=extract(native,rho,refinement=2,include_loads=True,main_strands=True)
    mains=sorted((p for p in geometry['ports'] if p['kind']=='main'),key=lambda p:p['ref'])
    headers=sorted((p for p in geometry['ports'] if p['kind']=='GH'),key=lambda p:(p['ref'],p['pad']))
    loads=sorted((p for p in geometry['ports'] if p['kind']=='load'),key=lambda p:(p['ref'],p['pad']))
    reference=mains[0];ports=headers+loads+mains[1:]
    if [(p['ref'],p['pad']) for p in ports+[reference]]!=[(p['ref'],p['pad']) for p in receipt['profiles']]:
        raise ValueError('full failing profile order changed')
    profiles=[[(p['layer'],p['patch'],1.),(reference['layer'],reference['patch'],-1.)] for p in ports]
    print('assembling exact cached full potential operator',flush=True)
    conductor=SheetVolume(sheets,[rho/t for t in geometry['thickness']],geometry['barrels'],certificate_mode='potential')
    restriction=restrict_wetted_terminals(conductor,mains)
    function=SheetVolume.area_profile_matrix_batched
    lines,first=inspect.getsourcelines(function)
    line=first+next(i for i,s in enumerate(lines) if 'residual=max(residual,local_residual)' in s)
    output.mkdir(parents=True,exist_ok=True)
    def trace(frame,event,arg):
        if frame.f_code!=function.__code__:return None
        if event=='line' and frame.f_lineno==line and frame.f_locals['start']==160:
            values=frame.f_locals;matrix=values['matrix'];rhs=values['rhs'];field=values['field']
            save_npz(output/'matrix.npz',matrix)
            np.save(output/'rhs.npy',rhs);np.save(output/'field.npy',field)
            residual=matrix@field-rhs
            worst=np.unravel_index(np.argmax(abs(residual)),residual.shape)
            report={'status':'Captured numerical gate reproducer; not a resistance result',
                'original_profile_receipt_sha256':hashlib.sha256(profile_path.read_bytes()).hexdigest(),
                'model_source_sha256':hashes,'native_export_sha256':receipt['native_export_sha256'],
                'mesh_cache_key':key,'profiles':receipt['profiles'][160:168],
                'maximum_residual_A':float(abs(residual[worst])),
                'worst_row_and_batch_column':list(map(int,worst)),
                'gauge_row_residual_A':residual[0].tolist(),'restriction':restriction,
                'shape':list(matrix.shape),'nonzero_count':matrix.nnz,
                'artifact_sha256':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in output.iterdir() if p.suffix in ('.npz','.npy')}}
            (output/'receipt.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
            print('captured potential residual',report['maximum_residual_A'],'at',worst,flush=True)
            raise Captured()
        return trace
    sys.settrace(trace)
    try:conductor.area_profile_matrix_batched(profiles,rho,geometry['thickness'])
    except Captured:pass
    finally:sys.settrace(None)
    if not (output/'receipt.json').exists():raise ValueError('failed batch was not captured')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for field in ('native','profiles','mesh','output'):parser.add_argument(field,type=Path)
    a=parser.parse_args();capture(a.native,a.profiles,a.mesh,a.output)
