"""Exact failed current-batch capture and same-operator refinement diagnosis.

Whole-board capture must run through heavy-guard. No paired energy matrix or
physical acceptance is produced. Original current construction remains intact.
"""
import argparse
import ast
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
from scripts.pcbgen.potential_refinement import refine


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()
class Captured(Exception):pass


def run(native,mesh_path,output,batch_start):
    if output.exists():raise ValueError('capture directory already exists')
    driver=Path('scripts/pcbgen/solve_conductor_volume.py')
    tree=ast.parse(driver.read_text())
    assignment=next(n for n in ast.walk(tree) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='source_hashes' for t in n.targets))
    names=ast.literal_eval(assignment.value.generators[0].iter)
    hashes={name:digest(Path('scripts/pcbgen')/name) for name in names}
    for name in ('design/partition/contact-transfer-proposal.json','design/reports/io-partition.json'):hashes[name]=digest(name)
    native_hash=digest(native);mesh_hash=digest(mesh_path)
    settings=(2.,.125,2,'current',True,True,(0.,0.),True)
    expected=hashlib.sha256((native_hash+str(settings)+json.dumps(hashes,sort_keys=True)).encode()).hexdigest()
    key,sheets=pickle.loads(mesh_path.read_bytes())
    if key!=expected:raise ValueError('failed current mesh key differs from exact native/driver/source parameters')
    rho=1.7241e-5*(1+.003947*50)
    geometry=extract(native,rho,refinement=2,include_loads=True,main_strands=True)
    if geometry['geometry_export_sha256']!=native_hash or digest(native)!=native_hash:raise ValueError('native capture input changed')
    mains=sorted((p for p in geometry['ports'] if p['kind']=='main'),key=lambda p:p['ref'])
    headers=sorted((p for p in geometry['ports'] if p['kind']=='GH'),key=lambda p:(p['ref'],p['pad']))
    loads=sorted((p for p in geometry['ports'] if p['kind']=='load'),key=lambda p:(p['ref'],p['pad']))
    reference=mains[0];ports=headers+loads+mains[1:]
    profiles=[[(p['layer'],p['patch'],1.),(reference['layer'],reference['patch'],-1.)] for p in ports]
    print('assembling exact cached full current operator for',len(profiles),'profiles',flush=True)
    conductor=SheetVolume(sheets,[rho/t for t in geometry['thickness']],geometry['barrels'],certificate_mode='current')
    function=SheetVolume.area_profile_matrix_batched;lines,first=inspect.getsourcelines(function)
    line=first+next(i for i,s in enumerate(lines) if 'residual=max(residual,local_residual)' in s)
    output.mkdir(parents=True)
    def reconstruct(field,sources,rhs):
        continuity=np.zeros_like(field);cell_residual=0.;barrel_residual=0.
        for layer,(source,(indices,C,m,reciprocal)) in enumerate(zip(sources,conductor.hybrid_cells)):
            current=conductor.hybrid_current(layer,field,source)
            cell_residual=max(cell_residual,float(abs(current.sum(axis=1)-source).max()))
            np.add.at(continuity,indices.ravel(),current.reshape(-1,field.shape[1]))
        for G,Y,(faces,local) in zip(conductor.barrel_face_maps,conductor.barrel_field_admittances,conductor.barrel_local_maps):
            current=-Y@(local@field[faces]);barrel_residual=max(barrel_residual,float(abs(current.sum(axis=0)).max()))
            conductor.add_barrel_continuity(continuity,G,current)
        operator=conductor.hybrid_matrix@field-rhs
        worst=np.unravel_index(np.argmax(abs(continuity)),continuity.shape)
        return {'operator_residual_A':float(abs(operator).max()),'sheet_source_balance_A':cell_residual,
            'barrel_balance_A':barrel_residual,'shared_face_continuity_A':float(abs(continuity).max()),
            'worst_continuity_row_column':list(map(int,worst)),
            'combined_gate_A':max(float(abs(operator).max()),cell_residual,barrel_residual,float(abs(continuity).max()))}
    def trace(frame,event,arg):
        if frame.f_code!=function.__code__:return None
        if event=='line' and frame.f_lineno==line and frame.f_locals['start']==batch_start:
            v=frame.f_locals;matrix=v['matrix'];rhs=v['rhs'];field=v['field'];sources=v['batch_sources']
            save_npz(output/'matrix.npz',matrix);np.save(output/'rhs.npy',rhs);np.save(output/'field.npy',field)
            for layer,source in enumerate(sources):np.save(output/('source-'+str(layer)+'.npy'),source)
            before=reconstruct(field,sources,rhs)
            extended=matrix.astype(np.longdouble)
            before['long_double_operator_residual_A']=float(abs(extended@field.astype(np.longdouble)-rhs.astype(np.longdouble)).max())
            corrected,implementation=refine(matrix,rhs,conductor.hybrid_factor,extended,initial=field)
            after=reconstruct(corrected,sources,rhs)
            after['long_double_operator_residual_A']=float(abs(extended@corrected.astype(np.longdouble)-rhs.astype(np.longdouble)).max())
            np.save(output/'corrected.npy',corrected)
            report={'status':'EXACT current failure capture and trial-improvement diagnostic only',
                'native_path':str(native),'native_export_sha256':native_hash,'model_source_sha256':hashes,
                'capture_source_sha256':digest(__file__),'mesh_sha256':mesh_hash,'mesh_cache_key':key,
                'basis_scope':'Full original finite-profile basis/order and source projection, same hash-bound native domain and mesh; original driver delays final profile publication, so profiles are reconstructed from identical hashed extraction code.',
                'profiles':[{'ref':p['ref'],'pad':p['pad'],'kind':p['kind'],'layer':p['layer'],'patch_wkt':p['patch'].wkt} for p in ports[batch_start:batch_start+8]],
                'shape':list(matrix.shape),'nonzeros':matrix.nnz,'captured_original_combined_gate_A':v['local_residual'],
                'before':before,'after':after,'refinement':implementation,
                'artifact_sha256':{p.name:digest(p) for p in output.iterdir() if p.suffix in ('.npz','.npy')}}
            (output/'receipt.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
            print(json.dumps({'before':before,'after':after,'refinement':implementation},indent=2),flush=True)
            raise Captured()
        return trace
    sys.settrace(trace)
    try:conductor.area_profile_matrix_batched(profiles,rho,geometry['thickness'])
    except Captured:pass
    finally:sys.settrace(None)
    if not (output/'receipt.json').exists():raise ValueError('failed current batch was not captured')
    for name,expected_hash in hashes.items():
        path=Path(name) if name.startswith('design/') else Path('scripts/pcbgen')/name
        if digest(path)!=expected_hash:raise ValueError('capture source changed: '+name)
    if digest(native)!=native_hash or digest(mesh_path)!=mesh_hash:raise ValueError('capture artifact changed')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('native','mesh','output'):parser.add_argument(name,type=Path)
    parser.add_argument('--batch-start',type=int,default=104);args=parser.parse_args()
    run(args.native,args.mesh,args.output,args.batch_start)
