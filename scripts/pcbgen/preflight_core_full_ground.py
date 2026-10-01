"""Guarded extraction-only preflight for the complete nominal K ground basis."""
import argparse
import hashlib
import json
import sys
import tempfile
from pathlib import Path
import shapely

from scripts.pcbgen import core_model_entry
from scripts.pcbgen import contact_transfer, conserved_flow, sheet_mesh, sheet_flux
from scripts.pcbgen.ground_reference import ordered_profiles
from scripts.pcbgen.ground_volume_geometry import extract

ROOT=Path(__file__).resolve().parents[2]
SOURCES=('preflight_core_full_ground.py','core_model_entry.py','core_model_gate.py',
         'core_full_ground_inventory.py','core_ground_inventory.py',
         'source_contact_inventory.py','ground_volume_geometry.py',
         'ground_reference.py','barrel_volume.py','copper_envelope.py',
         'foil_stack.py','active_foil_domains.py','terminal_face.py',
         'contact_transfer.py','propose_rail_transfers.py',
         'solve_ground_interfaces.py','ground_access.py','ground_private.py',
         'ground_annular.py','source_copper.py')


def sha(data):return hashlib.sha256(data).hexdigest()


def run(source,receipt,manifest,output):
    source,output=Path(source),Path(output)
    if output.exists():raise ValueError('fresh preflight output required')
    source_hashes={str(ROOT/'scripts/pcbgen'/name):sha((ROOT/'scripts/pcbgen'/name).read_bytes())
                   for name in SOURCES}
    for module in list(sys.modules.values()):
        name=getattr(module,'__name__','');path=getattr(module,'__file__',None)
        if name.startswith('scripts.pcbgen.') and path and Path(path).suffix=='.py':
            file=Path(path).resolve()
            if not file.is_relative_to(ROOT/'scripts/pcbgen'):
                raise ValueError('K preflight imported helper outside source tree')
            key=str(file);value=sha(file.read_bytes())
            if key in source_hashes and source_hashes[key]!=value:
                raise ValueError('K preflight source changed during initial capture: '+key)
            source_hashes[key]=value
    proposal=ROOT/'design/partition/contact-transfer-proposal.json'
    source_hashes[str(proposal)]=sha(proposal.read_bytes())
    native_bytes=source.read_bytes();native_sha=sha(native_bytes)
    authority=core_model_entry.enter(source,native_bytes,receipt,manifest,True,0,True)
    for name,want in authority['source_sha256'].items():
        if name in source_hashes and source_hashes[name]!=want:
            raise ValueError('K preflight/native source authority conflict: '+name)
    rho=1.7241e-5*(1+.003947*50)
    with tempfile.TemporaryDirectory(prefix='core-full-native-') as temporary:
        frozen=Path(temporary)/'native.json';frozen.write_bytes(native_bytes)
        geometry=extract(frozen,rho,refinement=1,include_loads=True,main_strands=True)
        if sha(frozen.read_bytes())!=native_sha:raise ValueError('private K native snapshot changed')
    if geometry['geometry_export_sha256']!=native_sha or sha(source.read_bytes())!=native_sha:
        raise ValueError('K native changed during full extraction')
    core_model_entry.select_ports(geometry,authority)
    mains,reference,ports,profiles,identity=ordered_profiles(geometry,0)
    if len(geometry['ports'])!=2288 or len(mains)!=9 or len(ports)!=2287 or len(profiles)!=2287:
        raise ValueError('complete K balanced function count differs')
    core_model_entry.verify_unchanged(authority)
    support=[{'ref':p['ref'],'pad':p['pad'],'kind':p['kind'],
              'physical_layer':p['physical_layer'],'patch_wkb_hex':p['patch'].wkb_hex}
             for p in ports+[reference]]
    support_sha=sha(json.dumps(support,sort_keys=True,separators=(',',':')).encode())
    for name,want in source_hashes.items():
        if sha(Path(name).read_bytes())!=want:
            raise ValueError('K extraction/profile source changed during preflight: '+name)
    output.parent.mkdir(parents=True,exist_ok=True)
    report={'status':'PASS complete K nominal extraction and finite profile basis only; physical/electrical acceptance OPEN',
            'native_export_sha256':native_sha,'source_sha256':{**authority['source_sha256'],**source_hashes},
            'fitted_own_count':authority['fitted_own_count'],'GH_return_count':authority['GH_return_count'],
            'main_land_count':len(mains),'balanced_function_count':len(profiles),
            'barrel_count':len(geometry['barrels']),'reference_contact':identity,
            'profile_support_sha256':support_sha,'nominal_rho_ohm_mm':rho,
            'extract_refinement':1,'include_loads':True,'main_strands':True,'port_limit':0,
            'active_sheet_layers':geometry['active_sheet_layers'],
            'native_AGND_pad_count':len(geometry['all_native_ground_pad_component_mapping']),
            'source_DNP_omission_count':authority['source_DNP_omission_count']}
    report['runtime_environment']={'python':sys.version.split()[0],'shapely':shapely.__version__}
    with output.open('x') as handle:json.dump(report,handle,indent=2,sort_keys=True);handle.write('\n')
    print(report['status'],len(profiles),'functions',len(geometry['barrels']),'barrels',flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('source','receipt','manifest','output'):parser.add_argument(name,type=Path)
    args=parser.parse_args();run(args.source,args.receipt,args.manifest,args.output)
