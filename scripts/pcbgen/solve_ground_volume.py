"""Nominal full-native four-foil potential/current trial diagnostic.

Run whole-board work through heavy-guard. This caller deliberately does not
accept the electrical contract: real contact classes, manufacturing envelopes,
all-load profiles and allocation/convergence remain separate explicit gates.
"""
import argparse
import gc
import hashlib
import json
import pickle
import time
from pathlib import Path

import numpy as np
import shapely
from scripts.pcbgen.ground_volume_geometry import extract
from scripts.pcbgen.sheet_mesh import Sheet,make_cells,make_adaptive_cells
from scripts.pcbgen.sheet_volume import SheetVolume


def solve(source,output,coarse,fine,refinement,port_limit,include_loads=False,adaptive=False,origin=(0.,0.),main_strands=False):
    started=time.monotonic();rho=1.7241e-5*(1+.003947*50)
    source_hashes={name:hashlib.sha256(Path('scripts/pcbgen',name).read_bytes()).hexdigest() for name in
        ('solve_ground_volume.py','ground_volume_geometry.py','solve_ground_interfaces.py','copper_envelope.py','propose_rail_transfers.py','sheet_mesh.py','sheet_flux.py','shared_interface.py','sheet_volume.py','sheet_conservation.py','conserved_flow.py','trial_energy.py','barrel_volume.py','contact_transfer.py','contact_constraints.py','potential_refinement.py','positive_energy_bound.py')}
    source_hashes['design/partition/contact-transfer-proposal.json']=hashlib.sha256(Path('design/partition/contact-transfer-proposal.json').read_bytes()).hexdigest()
    source_hashes['design/reports/io-partition.json']=hashlib.sha256(Path('design/reports/io-partition.json').read_bytes()).hexdigest()
    geometry=extract(source,rho,refinement=refinement,include_loads=include_loads,main_strands=main_strands)
    mains=sorted((p for p in geometry['ports'] if p['kind']=='main'),key=lambda p:p['ref'])
    headers=sorted((p for p in geometry['ports'] if p['kind']=='GH'),key=lambda p:(p['ref'],p['pad']))
    if port_limit:
        selected=np.linspace(0,len(headers)-1,port_limit,dtype=int)
        headers=[headers[i] for i in selected]
    reference=mains[0]
    loads=sorted((p for p in geometry['ports'] if p['kind']=='load'),key=lambda p:(p['ref'],p['pad']))
    ports=headers+loads+mains[1:]
    profiles=[[(p['layer'],p['patch'],1.),(reference['layer'],reference['patch'],-1.)] for p in ports]
    profile_receipt={'native_export_sha256':geometry['geometry_export_sha256'],
        'model_source_sha256':source_hashes,
        'profiles':[{'ref':p['ref'],'pad':p['pad'],'layer':p['layer'],'kind':p['kind'],
                     'patch_geojson':shapely.geometry.mapping(p['patch'])} for p in ports+[reference]]}
    output.with_name(output.stem+'-profiles.json').write_text(json.dumps(profile_receipt,indent=2)+'\n')
    patches=[p['patch'] for p in geometry['ports']]
    features=shapely.union_all([p['patch'].buffer(.2 if adaptive else .3) for p in geometry['ports'] if adaptive or p['kind'] in ('main','GH')])
    bounds=shapely.Polygon(geometry['data']['outline_mm']).bounds
    cells=(make_adaptive_cells if adaptive else make_cells)(bounds,coarse,fine,features,origin)
    matrices={};counts={}
    for mode,envelope,key in (('current','inner','upper'),('potential','outer','lower')):
        cache=output.with_name(output.stem+'-'+mode+'-mesh.pickle')
        cache_key=hashlib.sha256((geometry['geometry_export_sha256']+
            str((coarse,fine,refinement,mode,include_loads,adaptive,origin,main_strands))+
            json.dumps(source_hashes,sort_keys=True)).encode()).hexdigest()
        if cache.exists():
            stored_key,sheets=pickle.loads(cache.read_bytes())
            if stored_key!=cache_key:sheets=None
        else:sheets=None
        if sheets is None:
            sheets=[]
            for layer,(copper,t) in enumerate(zip(geometry[envelope],geometry['thickness'])):
                layer_patches=[p['patch'] for p in geometry['ports'] if p['layer']==layer]
                print(mode,'meshing',layer,'cells',len(cells),flush=True)
                sheet=Sheet(copper,cells,rho/t,source_patches=layer_patches,
                            interfaces=[{'relative':b.interface_polygon(),'centre':c} for b,c in geometry['barrels']])
                print('nodes',len(sheet.xy),'triangles',len(sheet.triangles),flush=True)
                sheets.append(sheet)
            cache.write_bytes(pickle.dumps((cache_key,sheets),protocol=5))
        else:print(mode,'reusing hash-bound local mesh',flush=True)
        counts[mode]={'nodes':[len(s.xy) for s in sheets],'triangles':[len(s.triangles) for s in sheets]}
        print(mode,'assembling/factoring full conductor',flush=True)
        conductor=SheetVolume(sheets,[rho/t for t in geometry['thickness']],geometry['barrels'],certificate_mode=mode)
        if mode=='potential' and main_strands:
            from scripts.pcbgen.contact_constraints import restrict_wetted_terminals
            counts[mode]['wetted_terminal_trial_restriction']=restrict_wetted_terminals(conductor,mains)
        print(mode,'solving finite profiles',len(profiles),flush=True)
        result=conductor.area_profile_matrix_batched(profiles,rho,geometry['thickness'])
        matrices[key]=result['energy']
        counts[mode]['maximum_equation_residual_A']=result['maximum_equation_residual_A']
        counts[mode]['maximum_residual_work_allowance_ohm']=result['maximum_residual_work_allowance_ohm']
        counts[mode]['numerical_current_allowance']=result['numerical_current_allowance']
        counts[mode]['conservation_correction']=result['conservation_correction']
        counts[mode]['potential_refinement']=result['potential_refinement']
        counts[mode]['maximum_interface_projection_mm']=max(s.maximum_interface_projection_mm for s in sheets)
        counts[mode]['maximum_sheet_metric_factor']=max(float(max(s.metric_factors)) for s in sheets)
        del result,conductor,sheets;gc.collect()
    gap=matrices['upper']-matrices['lower']
    if np.linalg.eigvalsh(gap)[0]<-1e-9:raise ValueError('native inner/outer trial brackets are inconsistent')
    receipt={'status':'NOT ACCEPTED: nominal finite-profile full-native diagnostic only',
        'board_sha256':geometry['data']['board_sha256'],'native_export_sha256':geometry['geometry_export_sha256'],
        'model_source_sha256':source_hashes,
        'reference_main':reference['ref'],'ports':[{k:v for k,v in p.items() if k not in ('patch','maximum_wetting')} for p in ports],
        'matrices_ohm':{k:v.tolist() for k,v in matrices.items()},'counts':counts,
        'physical_barrels':len(geometry['barrels']),'all_native_AGND_pad_component_mapping':geometry['all_native_ground_pad_component_mapping'],
        'barrel_ownership':geometry['barrel_ownership'],'unused_native_AGND_copper_uuids':geometry['unused_native_AGND_copper_uuids'],
        'native_zone_authority_audits':geometry['native_zone_authority_audits'],
        'computational_envelope_audits':geometry['computational_envelope_audits'],
        'physical_contact_classes':'NOT ACCEPTED: uniform numerical patches are not a real solder/lead guarantee',
        'manufacturing_envelope':'NOT ACCEPTED: exact nominal stack/Cu/rho only; max/min dimensions/conductivity and registration/etch class required',
        'all_load_profile_transfer_matrix':('NOMINAL finite profiles only: real lead/solder class unresolved' if include_loads else 'NOT RUN: GH and main profiles only'),
        'common_private_K_current_allocation':'NOT RUN','coarse_mm':coarse,'fine_mm':fine,'refinement':refinement,
        'adaptive_all_contact_regions':adaptive,'grid_origin_mm':origin,
        'main_strands':main_strands,
        'runtime_sec':time.monotonic()-started}
    output.write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
    print('NOMINAL profiles',len(profiles),'largest self upper mOhm',float(np.diag(matrices['upper']).max()*1000),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('source',type=Path);parser.add_argument('output',type=Path)
    parser.add_argument('--coarse-mm',type=float,default=2.);parser.add_argument('--fine-mm',type=float,default=.25)
    parser.add_argument('--refinement',type=int,default=1);parser.add_argument('--port-limit',type=int,default=3)
    parser.add_argument('--include-loads',action='store_true')
    parser.add_argument('--main-strands',action='store_true')
    parser.add_argument('--adaptive',action='store_true');parser.add_argument('--origin-x',type=float,default=0.);parser.add_argument('--origin-y',type=float,default=0.)
    args=parser.parse_args();solve(args.source,args.output,args.coarse_mm,args.fine_mm,args.refinement,args.port_limit,args.include_loads,args.adaptive,(args.origin_x,args.origin_y),args.main_strands)
