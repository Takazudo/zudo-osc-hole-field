"""Pinned native K ground-only prerequisite with every source footprint fixed.

This is not the #43 PCB implementation. Full rail/signal routing and actual
joined electrical acceptance remain OPEN. Run through heavy-guard.
"""
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
import pcbnew
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.pcbgen.sync import sync,fp_dir
from scripts.pcbgen.footprint_attributes import source_rotation_degrees,capture_template_digests,verify_template_digest
from scripts.pcbgen.prepare_source_planes import prepare
from scripts.pcbgen.native_stack import apply as apply_stack
from scripts.pcbgen.uuid_tools import stable_uuid,normalize_file
from scripts.pcbgen.extract_power_geometry import extract
from scripts.pcbgen.ratsnest import inspect
from scripts.pcbgen.definition import load_definition
from scripts.pcbgen.netlist import read_netlist
from scripts.pcbgen.core_ground_inventory import audit as audit_inventory
from scripts.pcbgen.core_package_fields import native_field_projection,apply_native_fields
from scripts.pcbgen.core_terminal_access import apply as apply_access,rules as access_rules,source_entries
from scripts.pcbgen.core_stitch_ownership import validate as validate_stitches


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build(proposal_path,definition_path,output,cache):
    if output.exists() or output.name=='osc-core.kicad_pcb':raise ValueError('fresh disposable K prototype filename required')
    if load_definition(definition_path).board_id!='osc-core':raise ValueError('K feasibility definition required')
    proposal=json.loads(proposal_path.read_text());definition=json.loads(definition_path.read_text())
    manifest=json.loads(definition_path.with_suffix('.receipt.json').read_text())
    if manifest['proposal_sha256']!=digest(proposal_path) or manifest['definition_sha256']!=digest(definition_path):
        raise ValueError('K feasibility source definition is stale')
    plan_path=Path(proposal['main_via_plan']);plan=json.loads(plan_path.read_text())
    if manifest['main_via_plan_sha256']!=digest(plan_path):raise ValueError('K finite main via plan is stale')
    stitch_path=Path(proposal['header_stitch_plan']);stitch=json.loads(stitch_path.read_text())
    if manifest['header_stitch_plan_sha256']!=digest(stitch_path) or stitch['unresolved']:raise ValueError('K header stitch plan is stale or unresolved')
    basis_paths=[Path(p) for p in stitch['source_sha256'] if p.endswith('ground-feasibility-geometry.json')]
    if len(basis_paths)!=1 or digest(basis_paths[0])!=stitch['source_sha256'][str(basis_paths[0])]:raise ValueError('K header stitch native basis changed')
    basis=json.loads(basis_paths[0].read_text())
    stitch_ownership=validate_stitches(stitch,manifest,basis)
    projected=native_field_projection(proposal['source_netlist'])
    entries=source_entries(definition,manifest['all_K_main_lands'])
    if definition_path.with_suffix('.kicad_dru').read_text()!=access_rules(entries):raise ValueError('K own-land native rule differs from source')
    paths=[proposal_path,definition_path,definition_path.with_suffix('.receipt.json'),Path(proposal['canonical_definition']),
           Path(proposal['source_netlist']),Path(proposal['source_partition']),Path('design/grid/placements.lock.json'),
           plan_path,stitch_path,basis_paths[0],definition_path.with_suffix('.kicad_dru'),Path('design/reports/io-partition.json')]
    paths.extend(Path(p) for p in projected['source_sheet_sha256'])
    paths.extend(ROOT/'scripts/pcbgen'/n for n in ('build_core_ground_feasibility.py','sync.py','prepare_source_planes.py',
        'native_stack.py','uuid_tools.py','extract_power_geometry.py','ratsnest.py','definition.py','footprint_attributes.py',
        'core_ground_inventory.py','source_contact_inventory.py','core_package_fields.py','core_terminal_access.py','core_stitch_ownership.py','netlist.py'))
    hashes={str(p):digest(p) for p in paths};cache.mkdir(parents=True,exist_ok=True)
    components,pin_nets=read_netlist(Path(proposal['source_netlist']))
    template_paths=[]
    for component in components:
        if not dict(component.fields).get('KiCadOrientationDeg'):
            library,name=component.footprint.split(':',1)
            template_paths.append(fp_dir(library)/(name+'.kicad_mod'))
    template_hashes=capture_template_digests(template_paths)
    hashes.update(template_hashes)  # Once, before sync can read any template.
    for suffix in ('.kicad_pro','.kicad_sch'):
        original=ROOT/'boards/osc-core'/('osc-core'+suffix);hashes[str(original)]=digest(original)
        shutil.copyfile(original,output.with_suffix(suffix))
    shutil.copyfile(definition_path.with_suffix('.kicad_dru'),output.with_suffix('.kicad_dru'))
    with tempfile.TemporaryDirectory(prefix='core-ground-',dir=cache) as directory:
        bare=Path(directory)/'source.kicad_pcb';sync('osc-core',bare,Path(proposal['source_netlist']))
        board=pcbnew.LoadBoard(str(bare));fps={f.GetReference():f for f in board.GetFootprints()};arrays=[]
        source_origins=[]
        for component in components:
            fp=fps[component.ref];fields=dict(component.fields)
            xy=[float(v) for v in fields['FootprintOriginMm'].split(',')]
            actual=[pcbnew.ToMM(fp.GetPosition().x)-100,pcbnew.ToMM(fp.GetPosition().y)-50]
            if max(abs(a-b) for a,b in zip(xy,actual))>1.001e-6 or board.GetLayerName(fp.GetLayer())!=fields['BoardSide']:
                raise ValueError('K fixed source footprint origin/face changed: '+component.ref)
            template_angle=None
            if not fields.get('KiCadOrientationDeg'):
                library,name=component.footprint.split(':',1);library_path=fp_dir(library)
                template_path=library_path/(name+'.kicad_mod');verify_template_digest(template_path,template_hashes)
                template=pcbnew.FootprintLoad(str(library_path),name)
                verify_template_digest(template_path,template_hashes)
                if template is None:raise ValueError('missing source library orientation')
                target_layer=pcbnew.F_Cu if fields['BoardSide']=='F.Cu' else pcbnew.B_Cu
                if template.GetLayer()!=target_layer:template.Flip(template.GetPosition(),False)
                template_angle=template.GetOrientationDegrees()
            expected_angle=source_rotation_degrees(fields,template_angle)
            if abs((fp.GetOrientationDegrees()-expected_angle+180)%360-180)>1e-6:
                raise ValueError('K fixed source footprint rotation changed: '+component.ref)
            source_origins.append({'ref':component.ref,'uuid':fp.m_Uuid.AsString(),'source_xy_mm':xy,'native_side':fields['BoardSide'],
                'native_rotation_deg':fp.GetOrientationDegrees(),'expected_source_rotation_deg':expected_angle,
                'rotation_basis':'Explicit KiCadOrientationDeg' if template_angle is None else 'Actual native library footprint after source face application'})
            for pad in fp.Pads():
                if pad.GetNetname()!=pin_nets.get((component.ref,pad.GetNumber()),''):
                    raise ValueError('K source/native pad net differs: '+component.ref+':'+pad.GetNumber())
        apply_native_fields(board,projected)
        # New metadata fields introduce native child UUIDs. Normalize them as
        # part of this fresh generated source, before any preservation receipt.
        projected_path=Path(directory)/'projected.kicad_pcb';pcbnew.SaveBoard(str(projected_path),board)
        normalize_file(projected_path,'osc-core',set(fps),{},False)
        board=pcbnew.LoadBoard(str(projected_path));fps={f.GetReference():f for f in board.GetFootprints()}
        access_receipt=apply_access(board,entries)
        planned={r['ref']:r for r in plan['rows']}
        for land in manifest['all_K_main_lands']:
            fp=fps[land['reference']];pads=list(fp.Pads())
            if len(pads)!=1:raise ValueError('K load terminal has changed pad count')
            pad=pads[0];expected=[land['center_mm'][0]+100,land['center_mm'][1]+50]
            position=pad.GetPosition();actual=[pcbnew.ToMM(position.x),pcbnew.ToMM(position.y)]
            if max(abs(a-b) for a,b in zip(actual,expected))>1e-6 or fp.GetLayer()!=pcbnew.F_Cu or pad.GetNetname()!=land['net']:
                raise ValueError('K fixed load terminal origin/face/net changed')
            if [pcbnew.ToMM(pad.GetSize().x),pcbnew.ToMM(pad.GetSize().y)]!=[4,4]:raise ValueError('K main land must remain4x4mm')
            ids=[]
            if planned[land['reference']]['net']!=land['net'] or not planned[land['reference']]['legal_sites']:
                raise ValueError('K main lacks explicit same-net finite vias')
            for site in planned[land['reference']]['legal_sites']:
                    dx=site['xy_mm'][0]-actual[0];dy=site['xy_mm'][1]-actual[1]
                    ix=round(dx/proposal['main_array_pitch_mm'])+2;iy=round(dy/proposal['main_array_pitch_mm'])+2
                    if not (0<=ix<5 and 0<=iy<5) or max(abs(dx-(ix-2)*.7),abs(dy-(iy-2)*.7))>1.001e-6:
                        raise ValueError('K source via moved off its original fixed grid')
                    if site['uuid']!=stable_uuid('osc-core','load-array:'+land['net'],land['reference']+':'+str(ix)+':'+str(iy)):
                        raise ValueError('K finite main via source UUID differs')
                    if max(abs(dx),abs(dy))+proposal['via_diameter_mm']/2>1.75+1e-9:raise ValueError('K array exceeds existing finite land margin')
                    via=pcbnew.PCB_VIA(board);via.SetViaType(pcbnew.VIATYPE_THROUGH);via.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu)
                    via.SetPosition(pcbnew.VECTOR2I(position.x+pcbnew.FromMM(dx),position.y+pcbnew.FromMM(dy)))
                    via.SetWidth(pcbnew.FromMM(proposal['via_diameter_mm']));via.SetDrill(pcbnew.FromMM(proposal['via_drill_mm']))
                    via.SetNetCode(pad.GetNetCode());uid=site['uuid']
                    via.SetUuid(pcbnew.KIID(uid));board.Add(via);ids.append(uid)
            arrays.append({'ref':land['reference'],'net':land['net'],'via_uuids':ids})
        headers={}
        for port in manifest['selected_K_ground_ports']:headers.setdefault(port['header_id'],set()).add((port['ref'],port['pad']))
        counts={h:0 for h in headers};stitch_bindings=[]
        for row in stitch['added']:
            header=row['header_id'];index=counts[header];counts[header]+=1
            if {(p['ref'],p['pad']) for p in row['ports']}!=headers[header] or row['uuid']!=stable_uuid('osc-core','ground-stitch:'+header,str(index)):
                raise ValueError('K header stitch source ownership differs')
            if row['net']!='AGND' or row['diameter_mm']!=.7 or row['drill_mm']!=.3 or row['layers']!=['F.Cu','B.Cu']:
                raise ValueError('K stitch geometry class changed')
            bindings=[]
            for source_pad in row['ports']:
                pad=next(p for p in fps[source_pad['ref']].Pads() if p.GetNumber()==source_pad['pad'])
                xy=[pcbnew.ToMM(pad.GetPosition().x),pcbnew.ToMM(pad.GetPosition().y)]
                if pad.GetNetname()!='AGND' or not pad.IsOnLayer(pcbnew.F_Cu) or xy!=source_pad['native_xy_mm']:
                    raise ValueError('K stitch fixed native source contact changed')
                bindings.append({**source_pad,'native_pad_uuid':pad.m_Uuid.AsString()})
            via=pcbnew.PCB_VIA(board);via.SetViaType(pcbnew.VIATYPE_THROUGH);via.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu)
            via.SetPosition(pcbnew.VECTOR2I(*(pcbnew.FromMM(v) for v in row['xy_mm'])))
            via.SetWidth(pcbnew.FromMM(.7));via.SetDrill(pcbnew.FromMM(.3));via.SetNetCode(pad.GetNetCode())
            via.SetUuid(pcbnew.KIID(row['uuid']));board.Add(via)
            stitch_bindings.append({**row,'physical_source_bindings':bindings})
        if set(counts)!=set(headers) or any(v!=2 for v in counts.values()):raise ValueError('K requires exactly two stitches per selected header')
        arrays_path=Path(directory)/'arrays.kicad_pcb';pcbnew.SaveBoard(str(arrays_path),board)
        prepare('osc-core',arrays_path,output,cache/'owned-ground-planes.json',definition_path)
    updated,stack=apply_stack(output.read_text(),definition);output.write_text(updated);board_hash=digest(output)
    drc_path=cache/'ground-feasibility-drc.json'
    command=['kicad-cli','pcb','drc','--schematic-parity','--refill-zones','--format','json','--severity-all','-o',str(drc_path),str(output)]
    subprocess.run(command,check=True)
    drc=json.loads(drc_path.read_text());errors=[v for v in drc['violations'] if v['severity']=='error']
    if drc['kicad_version']!='10.0.6':raise ValueError('wrong native K oracle')
    geometry_path=cache/'ground-feasibility-geometry.json';extract('osc-core',output,geometry_path,definition_path)
    geometry=json.loads(geometry_path.read_text());main=set(geometry['main_rail_members']['AGND'])
    def physical_pads(data):return {(i['ref'],i['pad']):{k:v for k,v in i.items() if k!='uuid'} for i in data['items'] if 'ref' in i}
    if physical_pads(geometry)!=physical_pads(basis):raise ValueError('K metadata/stitch candidate changed existing physical pads')
    if any(row['uuid'] not in main for row in stitch_bindings):raise ValueError('K source stitch is disconnected from main AGND')
    inventory=audit_inventory(geometry,manifest,json.loads(Path(proposal['source_partition']).read_text()),
        json.loads(Path('design/reports/io-partition.json').read_text()),require_connected=False)
    pads={(i['ref'],i['pad']):i for i in geometry['items'] if 'ref' in i}
    ports=[]
    for row in manifest['selected_K_ground_ports']:
        pad=pads[row['ref'],row['pad']]
        ports.append({**row,'uuid':pad['uuid'],'native_xy_mm':pad['xy_mm'],'native_main_connected':pad['uuid'] in main})
    ground_lands=[{'ref':row['ref'],'native_main_connected':pads[row['ref'],'1']['uuid'] in main} for row in arrays if row['net']=='AGND']
    rats=inspect(output);rats_path=cache/'ground-feasibility-ratsnest.json';rats_path.write_text(json.dumps(rats,indent=2,sort_keys=True)+'\n')
    if digest(output)!=board_hash or any(digest(p)!=expected for p,expected in hashes.items()):raise ValueError('K prototype source/native bytes changed during checks')
    report={'status':'UNSELECTED K ground-conductor prerequisite; #43 implementation and electrical/physical acceptance OPEN',
        'source_sha256':hashes,'board_sha256':board_hash,'stack':stack,'arrays':arrays,'new_array_via_count':sum(len(a['via_uuids']) for a in arrays),
        'source_footprint_origins':source_origins,'source_ground_inventory':inventory,
        'representative_package_fields':projected,'native_own_land_via_rules':access_receipt,
        'header_stitches':stitch_bindings,'existing_native_pad_geometry_net_face_position_exact':True,
        'header_stitch_source_ownership':stitch_ownership,
        'rule_error_count':len(errors),'schematic_parity_count':len(drc['schematic_parity']),
        'warning_count':sum(v['severity']=='warning' for v in drc['violations']),
        'selected_K_ground_ports':ports,'selected_K_ground_ports_connected':sum(p['native_main_connected'] for p in ports),
        'all_K_main_ground_lands':ground_lands,'full_named_open_edges':rats['native_unconnected_edges'],
        'scope':'Full exact source footprint/pad/drill/exclusion geometry; only explicit ground pours and all main arrays. Signal/rail routing deliberately absent in this prerequisite, not waived for actual #43. A disconnected selected ground port blocks its model.',
        'artifacts_sha256':{str(p):digest(p) for p in (drc_path,geometry_path,rats_path,cache/'owned-ground-planes.json')}}
    (cache/'ground-feasibility-native-receipt.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print('K source prototype: rules',len(errors),'parity',len(drc['schematic_parity']),'selected GH connected',sum(p['native_main_connected'] for p in ports),'/',len(ports),'main grounds',ground_lands,flush=True)
    if errors or drc['schematic_parity']:raise ValueError('K source prototype has actual native geometry/parity failures')
    if inventory['selected_disconnected']:raise ValueError('K selected GH/main ground contacts are disconnected')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('proposal','definition','output','cache'):parser.add_argument(name,type=Path)
    a=parser.parse_args();build(a.proposal,a.definition,a.output,a.cache)
