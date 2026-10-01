"""Bounded potential-only repair with unchanged certified current provenance.

Run under heavy-guard. The old matrix/receipt remains untouched. Every original
model input, exact finite profile, cached mesh and represented potential
operator is checked before reusing the old current trial certificate.
"""
import argparse
import hashlib
import json
import pickle
import shutil
import time
from pathlib import Path
import numpy as np
import shapely
from scipy.sparse import load_npz
from scripts.pcbgen.ground_volume_geometry import extract
from scripts.pcbgen.sheet_volume import SheetVolume
from scripts.pcbgen.contact_constraints import restrict_wetted_terminals
from scripts.pcbgen.potential_trial_matrix import potential_matrix


def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def content_digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()


def validate_profiles(expected, ports, reference):
    actual=[{'ref':p['ref'],'pad':p['pad'],'layer':p['layer'],'kind':p['kind'],
             'patch_geojson':shapely.geometry.mapping(p['patch'])} for p in ports+[reference]]
    # Normalize tuples emitted by Shapely and lists parsed from JSON alike.
    if content_digest(actual)!=content_digest(expected):
        raise ValueError('finite profile identity, ordering or support changed; current certificate cannot be reused')


def source_path(name):
    return Path(name) if name.startswith('design/') else Path('scripts/pcbgen')/name


def recompute(original_path,native_path,operator_path,output):
    started=time.monotonic()
    if output.resolve()==original_path.resolve():raise ValueError('historical diagnostic must be preserved')
    original_hash=digest(original_path);receipt=json.loads(original_path.read_text())
    additions={name:digest(Path('scripts/pcbgen')/name) for name in
        ('recompute_ground_potential.py','potential_trial_matrix.py','residual_work.py')}
    sources=receipt['model_source_sha256']
    for name,expected in sources.items():
        if digest(source_path(name))!=expected:raise ValueError('original model dependency changed: '+name)
    if digest(native_path)!=receipt['native_export_sha256']:raise ValueError('native conductor export changed')
    profile_path=original_path.with_name(original_path.stem+'-profiles.json')
    profile_hash=digest(profile_path)
    profile=json.loads(profile_path.read_text())
    if profile['model_source_sha256']!=sources or profile['native_export_sha256']!=receipt['native_export_sha256']:
        raise ValueError('original profile receipt has different model/native authority')
    original_upper_hash=content_digest(receipt['matrices_ohm']['upper'])
    original_current_counts_hash=content_digest(receipt['counts']['current'])
    if receipt['counts']['current']['maximum_equation_residual_A']>1e-8:
        raise ValueError('original current phase did not pass its unchanged gate')
    include_loads=any(p['kind']=='load' for p in receipt['ports'])
    rho=1.7241e-5*(1+.003947*50)
    geometry=extract(native_path,rho,refinement=receipt['refinement'],include_loads=include_loads,main_strands=receipt['main_strands'])
    keys=lambda p:(p['ref'],p['pad'],p['kind'],p['layer'])
    lookup={keys(p):p for p in geometry['ports']}
    if len(lookup)!=len(geometry['ports']):raise ValueError('duplicate extracted profile identity')
    ports=[lookup[keys(p)] for p in receipt['ports']]
    mains=[p for p in geometry['ports'] if p['kind']=='main']
    reference=next(p for p in mains if p['ref']==receipt['reference_main'])
    validate_profiles(profile['profiles'],ports,reference)
    profiles=[[(p['layer'],p['patch'],1.),(reference['layer'],reference['patch'],-1.)] for p in ports]
    parameters=(receipt['coarse_mm'],receipt['fine_mm'],receipt['refinement'],'potential',
        include_loads,receipt['adaptive_all_contact_regions'],tuple(receipt['grid_origin_mm']),receipt['main_strands'])
    expected_key=hashlib.sha256((receipt['native_export_sha256']+str(parameters)+json.dumps(sources,sort_keys=True)).encode()).hexdigest()
    cache=original_path.with_name(original_path.stem+'-potential-mesh.pickle')
    cache_hash=digest(cache);key,sheets=pickle.loads(cache.read_bytes())
    if key!=expected_key:raise ValueError('potential mesh cache does not match exact original inputs')
    conductor=SheetVolume(sheets,[rho/t for t in geometry['thickness']],geometry['barrels'],certificate_mode='potential')
    restriction=restrict_wetted_terminals(conductor,mains) if receipt['main_strands'] else None
    operator_hash=digest(operator_path)
    saved=load_npz(operator_path).tocsr();saved.sort_indices()
    actual=conductor.potential_matrix.tocsr();actual.sort_indices()
    if saved.shape!=actual.shape or any(not np.array_equal(getattr(saved,k),getattr(actual,k)) for k in ('indptr','indices','data')):
        raise ValueError('represented potential operator differs from the saved full operator')
    del saved,actual
    print('Exact original native/profile/cache/current dependencies and potential operator verified',flush=True)
    result=potential_matrix(conductor,profiles)
    receipt['matrices_ohm']['lower']=result.pop('energy').tolist()
    receipt['counts']['potential'].update(result)
    if restriction is not None:receipt['counts']['potential']['wetted_terminal_trial_restriction']=restriction
    gap=np.asarray(receipt['matrices_ohm']['upper'])-np.asarray(receipt['matrices_ohm']['lower'])
    if np.linalg.eigvalsh(gap).min()<-1e-9:raise ValueError('repaired paired energy brackets are inconsistent')
    receipt['phase_provenance']={
        'current':{'original_receipt_path':str(original_path),'original_receipt_sha256':original_hash,
            'upper_matrix_content_sha256':original_upper_hash,'current_counts_content_sha256':original_current_counts_hash,
            'model_source_sha256':sources,'status':'Exact original current certificate retained; no source hash rebound'},
        'potential':{'original_model_source_sha256':sources,'additional_algorithm_source_sha256':additions,
            'exact_original_profile_sha256':profile_hash,'exact_original_mesh_sha256':cache_hash,
            'exact_saved_operator_sha256':operator_hash,'represented_operator_equal_entry_by_entry':True,
            'change':'Row-specific residual-work contraction bound and exact-zero gauge coefficient only; original source projection, finite geometry, formation terms, LU/refinement and full 1e-8 gate retained.'}}
    receipt['potential_recompute_runtime_sec']=time.monotonic()-started
    if content_digest(receipt['matrices_ohm']['upper'])!=original_upper_hash or content_digest(receipt['counts']['current'])!=original_current_counts_hash:
        raise ValueError('current certificate changed during potential-only recomputation')
    if digest(original_path)!=original_hash:raise ValueError('original diagnostic changed during recomputation')
    for path,expected in ((profile_path,profile_hash),(cache,cache_hash),(operator_path,operator_hash),
                          (native_path,receipt['native_export_sha256'])):
        if digest(path)!=expected:raise ValueError('frozen diagnostic artifact changed: '+str(path))
    for name,expected in sources.items():
        if digest(source_path(name))!=expected:raise ValueError('original model changed during recomputation: '+name)
    for name,expected in additions.items():
        if digest(Path('scripts/pcbgen')/name)!=expected:raise ValueError('potential repair algorithm changed during recomputation: '+name)
    output.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    shutil.copyfile(profile_path,output.with_name(output.stem+'-profiles.json'))
    print('Potential-only diagnostic complete; physical/source acceptance remains open',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('original','native','operator','output'):parser.add_argument(name,type=Path)
    args=parser.parse_args();recompute(args.original,args.native,args.operator,args.output)
