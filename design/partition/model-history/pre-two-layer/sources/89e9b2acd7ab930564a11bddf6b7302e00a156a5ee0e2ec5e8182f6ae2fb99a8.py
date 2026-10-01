"""Pinned bare P source authority for collision planning, never model entry.

All original footprints/holes/rules are exported before adding ground arrays
or planes. A successful script does not imply connected ground or a PCB gate.
"""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path
import pcbnew
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.pcbgen.sync import sync,fp_dir
from scripts.pcbgen.netlist import read_netlist
from scripts.pcbgen.definition import load_definition,load_lock,selected_hardware
from scripts.pcbgen.footprint_attributes import capture_template_digests,verify_template_digest,source_rotation_degrees
from scripts.pcbgen.prerequisite_package_fields import project,apply_native_fields
from scripts.pcbgen.prerequisite_terminal_access import source_entries,rules,apply as apply_access
from scripts.pcbgen.native_stack import apply as apply_stack
from scripts.pcbgen.uuid_tools import normalize_file
from scripts.pcbgen.extract_power_geometry import extract
from scripts.pcbgen.ratsnest import inspect
from scripts.pcbgen.apply_control_geometry import apply as apply_geometry


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build(proposal_path,definition_path,output,cache):
    if output.exists() or output.name=='osc-control.kicad_pcb':raise ValueError('fresh disposable P planning filename required')
    if load_definition(definition_path).board_id!='osc-control':raise ValueError('P definition required')
    p=json.loads(proposal_path.read_bytes());definition=json.loads(definition_path.read_bytes())
    manifest_path=definition_path.with_suffix('.receipt.json');manifest=json.loads(manifest_path.read_bytes())
    if manifest['proposal_sha256']!=digest(proposal_path) or manifest['definition_sha256']!=digest(definition_path) or manifest['native_rule_sha256']!=digest(definition_path.with_suffix('.kicad_dru')):
        raise ValueError('P generated source is stale')
    netlist=Path(p['source_netlist']);components,pin_nets=read_netlist(netlist)
    if len(components)!=418 or manifest['netlist_sha256']!=digest(netlist):raise ValueError('P exact source package inventory changed')
    projection=project(netlist,ROOT/'boards/osc-control')
    entries=source_entries(definition,manifest['all_P_main_lands'])
    if entries!=manifest['own_terminal_entries'] or rules(entries)!=definition_path.with_suffix('.kicad_dru').read_text():
        raise ValueError('P own-terminal rules differ from source')
    paths=[proposal_path,definition_path,manifest_path,definition_path.with_suffix('.kicad_dru'),netlist,
        Path(p['canonical_definition']),Path(p['source_partition']),ROOT/'design/grid/placements.lock.json',ROOT/'design/reports/io-partition.json']
    paths.extend(Path(s) for s in projection['source_sheet_sha256'])
    paths.extend(ROOT/'scripts/pcbgen'/name for name in ['build_control_ground_bare.py','generate_control_ground_feasibility.py',
        'sync.py','definition.py','netlist.py','footprint_attributes.py','prerequisite_package_fields.py','core_package_fields.py',
        'prerequisite_terminal_access.py','core_terminal_access.py','native_stack.py','uuid_tools.py','extract_power_geometry.py','ratsnest.py'])
    hashes={str(path):digest(path) for path in paths}
    for path, expected in manifest['geometry_source_sha256'].items():
        if digest(path)!=expected:raise ValueError('P geometry source is stale')
        hashes[path]=expected
    hashes[str(ROOT/'scripts/pcbgen/apply_control_geometry.py')]=digest(ROOT/'scripts/pcbgen/apply_control_geometry.py')
    templates=[]
    for component in components:
        library,name=component.footprint.split(':',1);templates.append(fp_dir(library)/(name+'.kicad_mod'))
    template_hashes=capture_template_digests(templates);hashes.update(template_hashes)
    cache.mkdir(parents=True,exist_ok=False)
    for suffix in ('.kicad_pro','.kicad_sch'):
        source=ROOT/'boards/osc-control'/('osc-control'+suffix);hashes[str(source)]=digest(source)
        shutil.copyfile(source,output.with_suffix(suffix))
    shutil.copyfile(definition_path.with_suffix('.kicad_dru'),output.with_suffix('.kicad_dru'))
    sync('osc-control',output,netlist);board=pcbnew.LoadBoard(str(output));fps={f.GetReference():f for f in board.GetFootprints()}
    hardware=selected_hardware(load_definition(Path(p['canonical_definition'])),load_lock(ROOT/'design/grid/placements.lock.json'))
    if len(hardware)!=139:raise ValueError('P fixed panel hardware inventory changed')
    origins=[]
    for component in components:
        fp=fps[component.ref];fields=dict(component.fields);xy=list(map(float,fields['FootprintOriginMm'].split(',')))
        actual=[pcbnew.ToMM(fp.GetPosition().x)-100,pcbnew.ToMM(fp.GetPosition().y)-50]
        if max(abs(a-b) for a,b in zip(xy,actual))>1.001e-6 or board.GetLayerName(fp.GetLayer())!=fields['BoardSide']:
            raise ValueError('P source native origin or face changed: '+component.ref)
        angle=None
        if not fields.get('KiCadOrientationDeg'):
            library,name=component.footprint.split(':',1);path=fp_dir(library)/(name+'.kicad_mod')
            verify_template_digest(path,template_hashes);template=pcbnew.FootprintLoad(str(fp_dir(library)),name);verify_template_digest(path,template_hashes)
            if template is None:raise ValueError('missing native fallback orientation template')
            # KiCad 10 Flip consults the board layer stack even for a library
            # template. A parentless B-face flip can crash the native oracle.
            template.SetParent(board)
            side=pcbnew.F_Cu if fields['BoardSide']=='F.Cu' else pcbnew.B_Cu
            if template.GetLayer()!=side:template.Flip(template.GetPosition(),False)
            angle=template.GetOrientationDegrees()
        expected=source_rotation_degrees(fields,angle)
        if abs((fp.GetOrientationDegrees()-expected+180)%360-180)>1e-6:raise ValueError('P source native angle changed')
        for pad in fp.Pads():
            if pad.GetNetname()!=pin_nets.get((component.ref,pad.GetNumber()),''):raise ValueError('P exact source pin/net changed')
        origins.append({'ref':component.ref,'uuid':fp.m_Uuid.AsString(),'source_xy_mm':xy,'side':fields['BoardSide'],
            'native_angle_deg':fp.GetOrientationDegrees(),'expected_source_angle_deg':expected})
    geometry_change=apply_geometry(board,json.loads(Path(p['canonical_definition']).read_bytes()),definition,manifest['explicit_geometry_change'])
    apply_native_fields(board,projection);access=apply_access(board,entries)
    pcbnew.SaveBoard(str(output),board);normalize_file(output,'osc-control',set(fps),{},False)
    updated,stack=apply_stack(output.read_text(),definition);output.write_text(updated);board_hash=digest(output)
    drc_path=cache/'bare-drc.json'
    subprocess.run(['kicad-cli','pcb','drc','--schematic-parity','--format','json','--severity-all','-o',str(drc_path),str(output)],check=True)
    drc=json.loads(drc_path.read_bytes())
    if drc['kicad_version']!='10.0.6' or drc['source']!=output.name:raise ValueError('P bare oracle identity differs')
    geometry_path=cache/'bare-geometry.json';extract('osc-control',output,geometry_path,definition_path)
    rats_path=cache/'bare-ratsnest.json';rats_path.write_text(json.dumps(inspect(output),indent=2,sort_keys=True)+'\n')
    if digest(output)!=board_hash or any(digest(path)!=h for path,h in hashes.items()):raise ValueError('P bare source/native dependency changed')
    errors=sum(v['severity']=='error' for v in drc['violations'])
    report={'status':'BARE SOURCE PLANNING ONLY; no ground arrays/pours; conductor model entry PROHIBITED',
        'stage':'bare_source_planning','board_id':'osc-control','board_sha256':board_hash,
        'source_sha256':hashes,'source_footprint_origins':origins,'fixed_panel_hardware_count':len(hardware),
        'package_field_projection':projection,'explicit_geometry_change':geometry_change,'own_terminal_exceptions':access,'native_stack':stack,
        'rule_error_count':errors,'schematic_parity_count':len(drc['schematic_parity']),
        'warning_count':sum(v['severity']=='warning' for v in drc['violations']),
        'artifacts_sha256':{str(path):digest(path) for path in (drc_path,geometry_path,rats_path)},
        'model_entry_allowed':False,'electrical_scope':'Bare contacts intentionally disconnected; only exact source/geometry authority for legal finite array screening. Native candidate connectivity and all electrical budgets remain OPEN.'}
    (cache/'bare-native-receipt.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('P bare planning exported:',len(origins),'source footprints,',len(hardware),'fixed hardware; rules',errors,'parity',len(drc['schematic_parity']),'MODEL ENTRY PROHIBITED',flush=True)


if __name__=='__main__':
    p=argparse.ArgumentParser()
    for name in ('proposal','definition','output','cache'):p.add_argument(name,type=Path)
    a=p.parse_args();build(a.proposal,a.definition,a.output,a.cache)
