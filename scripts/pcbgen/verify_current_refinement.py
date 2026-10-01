"""Verify the new helper on the exact captured full current operator/batch.

This is a guarded bounded reproducer, not a whole-profile certificate. It
checks every represented operator coefficient, RHS entry and physical source
array before allowing the new current helper to evaluate its corrected trial.
"""
import argparse
import hashlib
import json
import pickle
from pathlib import Path
from unittest.mock import patch
import numpy as np
import shapely
from scipy.sparse import load_npz
from scripts.pcbgen.ground_volume_geometry import extract
from scripts.pcbgen.sheet_volume import SheetVolume
from scripts.pcbgen import current_trial_matrix


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def run(capture,mesh_path):
    receipt_path=capture/'receipt.json';receipt_hash=digest(receipt_path)
    old=json.loads(receipt_path.read_text());native=Path(old['native_path'])
    source_snapshot={}
    for name,expected in old['model_source_sha256'].items():
        path=Path(name) if name.startswith('design/') else Path('scripts/pcbgen')/name
        if name=='solve_conductor_volume.py':
            retained=capture/'driver-before-current-refinement.py'
            if digest(retained)!=expected:raise ValueError('original driver snapshot differs from captured source')
        elif digest(path)!=expected:raise ValueError('captured physical/model dependency changed: '+name)
        source_snapshot[str(path)]=digest(path)
    for path in ('scripts/pcbgen/current_trial_matrix.py',__file__):source_snapshot[str(path)]=digest(path)
    for name,expected in old['artifact_sha256'].items():
        if digest(capture/name)!=expected:raise ValueError('saved current artifact changed: '+name)
    if digest(native)!=old['native_export_sha256'] or digest(mesh_path)!=old['mesh_sha256']:
        raise ValueError('saved native domain or current mesh changed')
    key,sheets=pickle.loads(mesh_path.read_bytes())
    if key!=old['mesh_cache_key']:raise ValueError('saved full mesh key changed')
    rho=1.7241e-5*(1+.003947*50)
    geometry=extract(native,rho,refinement=2,include_loads=True,main_strands=True)
    mains=sorted((p for p in geometry['ports'] if p['kind']=='main'),key=lambda p:p['ref']);reference=mains[0]
    lookup={(p['ref'],p['pad']):p for p in geometry['ports']}
    profiles=[]
    for row in old['profiles']:
        port=lookup[row['ref'],row['pad']]
        if port['layer']!=row['layer'] or port['kind']!=row['kind'] or port['patch'].wkt!=row['patch_wkt']:
            raise ValueError('captured physical source support changed')
        profiles.append([(port['layer'],port['patch'],1.),(reference['layer'],reference['patch'],-1.)])
    conductor=SheetVolume(sheets,[rho/t for t in geometry['thickness']],geometry['barrels'],certificate_mode='current')
    saved=load_npz(capture/'matrix.npz').tocsr();saved.sort_indices()
    actual=conductor.hybrid_matrix.tocsr();actual.sort_indices()
    if saved.shape!=actual.shape or any(not np.array_equal(getattr(saved,k),getattr(actual,k)) for k in ('indptr','indices','data')):
        raise ValueError('new helper uses a different full current operator')
    del saved,actual
    rhs_saved=np.load(capture/'rhs.npy');sources=[np.load(capture/('source-'+str(k)+'.npy')) for k in range(len(sheets))]
    original_refine=current_trial_matrix.refine;original_current=conductor.hybrid_current
    checked_sources=set();checked_rhs=[]
    def verify_rhs(matrix,rhs,*args,**kwargs):
        if not np.array_equal(rhs,rhs_saved):raise ValueError('new helper changed exact captured RHS')
        checked_rhs.append(True);return original_refine(matrix,rhs,*args,**kwargs)
    def verify_source(layer,field,source):
        if not np.array_equal(source,sources[layer]):raise ValueError('new helper changed a physical foil source')
        checked_sources.add(layer);return original_current(layer,field,source)
    with patch.object(current_trial_matrix,'refine',side_effect=verify_rhs),patch.object(conductor,'hybrid_current',side_effect=verify_source):
        result=current_trial_matrix.current_matrix(conductor,profiles,rho,geometry['thickness'])
    if checked_sources!=set(range(len(sheets))) or checked_rhs!=[True]:raise ValueError('current equivalence gates were not exercised')
    energy=result.pop('energy');result['upper_matrix_ohm']=energy.tolist()
    if old['before']['combined_gate_A']<=1e-8 or result['maximum_equation_residual_A']>=1e-8:
        raise ValueError('captured failure did not pass the unchanged current/KCL gate')
    report={'status':'PASS - exact captured-operator/source trial-improvement regression only; no whole-board acceptance',
        'original_capture_receipt_sha256':receipt_hash,'exact_full_operator_and_rhs_match':True,
        'every_physical_foil_source_array_equal':True,'source_sha256':source_snapshot,'result':result}
    if digest(receipt_path)!=receipt_hash or digest(native)!=old['native_export_sha256'] or digest(mesh_path)!=old['mesh_sha256']:
        raise ValueError('capture inputs changed during verification')
    for path,expected in source_snapshot.items():
        if digest(path)!=expected:raise ValueError('verification source changed: '+path)
    for name,expected in old['artifact_sha256'].items():
        if digest(capture/name)!=expected:raise ValueError('saved current artifact changed during verification')
    (capture/'current-helper-verification.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(report['status'],result['maximum_equation_residual_A'],'work',result['maximum_residual_work_allowance_ohm'],flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('capture',type=Path);parser.add_argument('mesh',type=Path);args=parser.parse_args()
    run(args.capture,args.mesh)
