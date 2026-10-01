"""Bounded pinned O ground candidates and bare EL authority; no model dispatch."""
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
from scripts.pcbgen.netlist import read_netlist
from scripts.pcbgen.definition import load_definition,load_lock,selected_hardware
from scripts.pcbgen.footprint_attributes import capture_template_digests
from scripts.pcbgen.prerequisite_package_fields import project,apply_native_fields
from scripts.pcbgen.native_stack import apply as apply_stack
from scripts.pcbgen.uuid_tools import normalize_file
from scripts.pcbgen.extract_power_geometry import extract
from scripts.pcbgen.ratsnest import inspect
from scripts.pcbgen.prepare_source_planes import prepare
from scripts.pcbgen.verify_local_links import blocks
from scripts.pcbgen.native_companion_binding import verify as verify_companions
from scripts.pcbgen.peripheral_project_source import derive,fresh_sync_project
from scripts.pcbgen.peripheral_ground_inventory import audit
from scripts.pcbgen.generate_peripheral_ground import generate
from scripts.pcbgen.peripheral_source_binding import retain_sources,require_fresh_outputs
from scripts.pcbgen.route_kicad import apply_classes
from scripts.pcbgen.peripheral_stack_serialization import serialize as serialize_stack
from scripts.pcbgen.peripheral_ground_bridge import insert as insert_ground_bridge


def digest(path):return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def build(proposal_path,definition_path,output,cache):
    proposal_path,definition_path,output,cache=map(Path,(proposal_path,definition_path,output,cache))
    require_fresh_outputs(output,cache)
    manifest_path=definition_path.with_suffix('.receipt.json')
    entry_paths=[proposal_path,definition_path,manifest_path,Path(__file__)]
    entry_bytes={str(p.resolve().relative_to(ROOT)):p.read_bytes() for p in entry_paths}
    frozen_dir=tempfile.TemporaryDirectory(prefix='peripheral-native-source-')
    frozen_definition=Path(frozen_dir.name)/definition_path.name
    definition_bytes=entry_bytes[str(definition_path.resolve().relative_to(ROOT))]
    frozen_definition.write_bytes(definition_bytes)
    definition=load_definition(frozen_definition);bid=definition.board_id
    if output.exists() or cache.exists() or output.parent.resolve()!=ROOT/'boards'/bid or output.name==bid+'.kicad_pcb':
        raise ValueError('fresh disposable native/cache paths in the actual board directory required')
    if (ROOT/'boards'/bid/(bid+'.kicad_pcb')).exists():
        raise ValueError('a canonical PCB now exists; explicit owner-preserving baseline required')
    proposal=json.loads(entry_bytes[str(proposal_path.resolve().relative_to(ROOT))])
    manifest=json.loads(entry_bytes[str(manifest_path.resolve().relative_to(ROOT))])
    if manifest['board_id']!=bid or manifest['definition_sha256']!=digest(definition_path) or manifest['native_rule_sha256']!=digest(definition_path.with_suffix('.kicad_dru')):
        raise ValueError('peripheral generated source is stale')
    for name,value in manifest['source_sha256'].items():
        if digest(name)!=value:raise ValueError('peripheral definition dependency changed: '+name)
    regenerated=Path(frozen_dir.name)/'regenerated'/definition_path.name
    expected_manifest=generate(proposal_path,bid,regenerated)
    if regenerated.read_bytes()!=definition_bytes or expected_manifest!=manifest:
        raise ValueError('peripheral definition/manifest differs from exact source regeneration')
    netlist=ROOT/definition.netlist;netlist_bytes=netlist.read_bytes()
    if hashlib.sha256(netlist_bytes).hexdigest()!=manifest['source_sha256'][definition.netlist]:raise ValueError('native netlist differs from retained source')
    frozen_netlist=Path(frozen_dir.name)/'source.net';frozen_netlist.write_bytes(netlist_bytes)
    components,pin_nets=read_netlist(frozen_netlist)
    if len(components)!=len(manifest['source_packages']):raise ValueError('peripheral complete package count differs')
    projection=project(frozen_netlist,ROOT/'boards'/bid)
    paths=[proposal_path,definition_path,manifest_path,definition_path.with_suffix('.kicad_dru'),
        ROOT/'boards'/bid/(bid+'.kicad_pro'),ROOT/'boards'/bid/(bid+'.kicad_sch')]
    paths += [Path(n) for n in manifest['source_sha256']]
    paths += [Path(n) for n in projection['source_sheet_sha256']]
    helpers=['build_peripheral_ground','generate_peripheral_ground','peripheral_project_source','peripheral_ground_inventory','peripheral_source_binding','peripheral_stack_serialization','peripheral_ground_bridge',
        'sync','definition','netlist','footprint_attributes','prerequisite_package_fields','core_package_fields',
        'native_stack','foil_stack','uuid_tools','extract_power_geometry','ratsnest','prepare_source_planes',
        'route_kicad','source_zones','source_copper','verify_local_links','native_companion_binding','geometry']
    paths += [ROOT/'scripts/pcbgen'/(n+'.py') for n in helpers]
    paths += [ROOT/'scripts/geometry/panel_frame.py']
    hashes=retain_sources(ROOT,paths,[manifest['source_sha256'],
        {name:hashlib.sha256(data).hexdigest() for name,data in entry_bytes.items()},
        projection['source_sheet_sha256']])
    templates=[]
    for component in components:
        library,name=component.footprint.split(':',1)
        if library!='zudo-osc-hole-field':raise ValueError('peripheral source has an unreviewed external footprint library')
        templates.append(fp_dir(library)/(name+'.kicad_mod'))
    for name,value in capture_template_digests(templates).items():hashes[str(Path(name).relative_to(ROOT))]=value
    template=(ROOT/proposal['project_template']).read_bytes()
    canonical=(ROOT/'boards'/bid/(bid+'.kicad_pro')).read_bytes()
    expected_project,project_receipt=derive(template,canonical,definition_bytes,output.with_suffix('.kicad_pro').name)
    expected_sync_project=fresh_sync_project(expected_project,template)
    project_receipt['expected_fresh_sync_project_sha256']=hashlib.sha256(expected_sync_project).hexdigest()
    project_receipt['intermediate_scope']='Exact pinned fresh Default-only constructor stage; final declared classes must be applied and original final expectation restored by source class application before native validation.'
    cache.mkdir(parents=True)
    (cache/'startup-source.json').write_text(json.dumps(hashes,indent=2)+'\n')
    expected={str(output.with_suffix('.kicad_pro')):hashlib.sha256(expected_project).hexdigest(),
        str(output.with_suffix('.kicad_sch')):hashes['boards/'+bid+'/'+bid+'.kicad_sch'],
        str(output.with_suffix('.kicad_dru')):manifest['native_rule_sha256']}
    for suffix,data in [('.kicad_pro',expected_project),
        ('.kicad_sch',(ROOT/'boards'/bid/(bid+'.kicad_sch')).read_bytes()),
        ('.kicad_dru',definition_path.with_suffix('.kicad_dru').read_bytes())]:
        with output.with_suffix(suffix).open('xb') as handle:handle.write(data)
    verify_companions(expected)
    sync(bid,output,frozen_netlist)
    sync_expected={**expected,str(output.with_suffix('.kicad_pro')):hashlib.sha256(expected_sync_project).hexdigest()}
    verify_companions(sync_expected)
    board=pcbnew.LoadBoard(str(output));fps={f.GetReference():f for f in board.GetFootprints()}
    if len(fps)!=len(list(board.GetFootprints())):raise ValueError('duplicate peripheral footprint reference')
    expected_refs={c.ref for c in components}|{'MH_'+h['id'] for h in definition.mounting_holes}
    if set(fps)!=expected_refs:raise ValueError('native peripheral footprint/mount inventory differs from source')
    mounting=[]
    for hole in definition.mounting_holes:
        fp=fps['MH_'+hole['id']];pads=list(fp.Pads())
        if len(pads)!=1 or pads[0].GetAttribute()!=pcbnew.PAD_ATTRIB_NPTH or pads[0].GetNetname():
            raise ValueError('source mounting/optical hole changed plating or net')
        pad=pads[0];xy=[pcbnew.ToMM(pad.GetPosition().x),pcbnew.ToMM(pad.GetPosition().y)]
        drill=[pcbnew.ToMM(pad.GetDrillSize().x),pcbnew.ToMM(pad.GetDrillSize().y)]
        if max(abs(a-b) for a,b in zip(xy,[hole['center'][0]+100,hole['center'][1]+50]))>1.001e-6 or max(abs(d-hole['diameter_mm']) for d in drill)>1e-9:
            raise ValueError('source mounting/optical hole position or diameter differs')
        mounting.append({'id':hole['id'],'ref':fp.GetReference(),'pad_uuid':pad.m_Uuid.AsString(),'native_xy_mm':xy,'drill_mm':drill})
    hardware=selected_hardware(load_definition(ROOT/'design/boards'/(bid+'.json')),load_lock(ROOT/'design/grid/placements.lock.json'))
    if hardware!=manifest['fixed_hardware']:raise ValueError('fixed peripheral hardware source differs')
    for row in hardware:
        fp=fps[row['ref']]
        expected_xy=[row['x_mm']+100,row['y_mm']+50]
        actual_xy=[pcbnew.ToMM(fp.GetPosition().x),pcbnew.ToMM(fp.GetPosition().y)]
        if not fp.IsLocked() or max(abs(a-b) for a,b in zip(expected_xy,actual_xy))>1.001e-6:
            raise ValueError('fixed peripheral hardware lock or position differs')
    origins=[]
    for component in components:
        fp=fps[component.ref];fields=dict(component.fields);source=list(map(float,fields['FootprintOriginMm'].split(',')))
        actual=[pcbnew.ToMM(fp.GetPosition().x)-100,pcbnew.ToMM(fp.GetPosition().y)-50]
        angle=float(fields['KiCadOrientationDeg'])
        if max(abs(a-b) for a,b in zip(source,actual))>1.001e-6 or board.GetLayerName(fp.GetLayer())!=fields['BoardSide'] or abs((fp.GetOrientationDegrees()-angle+180)%360-180)>1e-6:
            raise ValueError('peripheral source placement/face/orientation differs: '+component.ref)
        for pad in fp.Pads():
            if pad.GetNetname()!=pin_nets.get((component.ref,pad.GetNumber()),''):raise ValueError('peripheral source pin/net differs')
        origins.append({'ref':component.ref,'uuid':fp.m_Uuid.AsString(),'source_xy_mm':source,'side':fields['BoardSide'],'native_angle_deg':fp.GetOrientationDegrees()})
    apply_classes(board,definition.routing)
    apply_native_fields(board,projection);pcbnew.SaveBoard(str(output),board)
    normalize_file(output,bid,set(c.ref for c in components),{},False)
    updated,stack_receipt=apply_stack(output.read_text(),json.loads(definition_bytes))
    (cache/'before-editor-stack.kicad_pcb').write_text(updated)
    updated,editor_stack_receipt=serialize_stack(updated,definition_bytes)
    bridge_receipt=None
    if 'source_ground_bridge' in proposal:
        updated,bridge_receipt=insert_ground_bridge(updated,bid,proposal['source_ground_bridge'])
        (cache/'source-ground-bridge.json').write_text(json.dumps(bridge_receipt,indent=2,sort_keys=True)+'\n')
    output.write_text(updated)
    verify_companions(expected)
    baseline=cache/'synchronized.kicad_pcb';baseline.write_bytes(output.read_bytes())
    baseline.with_suffix('.kicad_pro').write_bytes(expected_project)
    reference=manifest['source_reference'];pair=(reference['ref'],reference['pad'])
    baseline_geometry=cache/'synchronized-geometry.json';extract(bid,baseline,baseline_geometry,definition_path,pair)
    baseline_native=json.loads(baseline_geometry.read_bytes());old=blocks(baseline)
    full=manifest['initial_stage']=='ground_candidate'
    if manifest['initial_stage'] not in ('ground_candidate','bare_source_planning'):raise ValueError('unknown native prerequisite stage')
    if full:prepare(bid,baseline,output,cache/'owned-ground-planes.json',definition_path)
    new=blocks(output)
    for kind in ('footprint','segment','via','arc'):
        if old[kind]!=new[kind]:raise ValueError('peripheral source fill altered original '+kind)
    if any(new['zone'].get(uid)!=value for uid,value in old['zone'].items()):raise ValueError('peripheral source reservation changed')
    native_hash=digest(output);drc_path=cache/'native-drc.json'
    verify_companions(expected)
    subprocess.run(['kicad-cli','pcb','drc','--schematic-parity','--refill-zones','--format','json','--severity-all','-o',str(drc_path),str(output)],check=True)
    verify_companions(expected)
    drc=json.loads(drc_path.read_bytes())
    if drc['source']!=output.name or drc['kicad_version']!='10.0.6':raise ValueError('wrong native peripheral board/oracle')
    geometry_path=cache/'native-geometry.json';extract(bid,output,geometry_path,definition_path,pair)
    native=json.loads(geometry_path.read_bytes())
    if native['project_sha256']!=expected[str(output.with_suffix('.kicad_pro'))]:raise ValueError('exported project differs from expected source')
    for key in ('items','holes'):
        if {r['uuid']:r for r in baseline_native[key]}!={r['uuid']:r for r in native[key]}:
            raise ValueError('peripheral existing pad/track/drill primitive changed')
    inventory=audit(native,manifest,json.loads((ROOT/proposal['partition']).read_bytes()),json.loads((ROOT/proposal['io']).read_bytes()),require_connected=False)
    rats=inspect(output);rats_path=cache/'native-ratsnest.json';rats_path.write_text(json.dumps(rats,indent=2,sort_keys=True)+'\n')
    errors=[r for r in drc['violations'] if r['severity']=='error'];passed=full and not errors and not drc['schematic_parity'] and not inventory['disconnected']
    if digest(output)!=native_hash or any(digest(ROOT/name)!=value for name,value in hashes.items()):raise ValueError('peripheral source/native dependency changed')
    verify_companions(expected)
    artifacts=[output,output.with_suffix('.kicad_pro'),output.with_suffix('.kicad_sch'),output.with_suffix('.kicad_dru'),cache/'before-editor-stack.kicad_pcb',baseline,baseline_geometry,drc_path,geometry_path,rats_path]
    report={'status':'NATIVE GROUND PREREQUISITE ONLY; no electrical/contact/material acceptance' if full else 'BARE SOURCE PLANNING ONLY; model entry PROHIBITED',
        'board_id':bid,'stage':manifest['initial_stage'],'native_model_prerequisite_passed':passed,'board_sha256':native_hash,
        'source_sha256':hashes,'artifacts_sha256':{str(p.resolve().relative_to(ROOT)):digest(p) for p in artifacts},
        'companion_sha256':expected,'project_source_derivation':project_receipt,'native_stack':stack_receipt,
        'native_editor_stack_serialization':editor_stack_receipt,
        'source_ground_bridge':bridge_receipt,
        'source_footprint_origins':origins,'native_footprint_count':len(fps),'source_mounting_holes':mounting,
        'fixed_hardware_count':len(hardware),'package_field_projection':projection,
        'source_ground_inventory':inventory,'rule_error_count':len(errors),'schematic_parity_count':len(drc['schematic_parity']),
        'warning_count':sum(r['severity']=='warning' for r in drc['violations']),
        'prior_physical_pad_hole_copper_and_reservations_preserved':True,
        'named_reference':native['ground_reference'],'all_rules_parity_contacts_required_before_model':True,
        'remaining_scope':'Rails/signals are prerequisite omissions with full named native edges; no downstream issue completion or electrical acceptance.'}
    (cache/'native-receipt.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
    print(bid,'stage',manifest['initial_stage'],'rules',len(errors),'parity',len(drc['schematic_parity']),'grounds',inventory['connected_count'],'/',inventory['complete_ground_count'],flush=True)
    if full and not passed:raise ValueError('peripheral full native prerequisite failed rule/parity/ground gates')


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    for name in ('proposal','definition','output','cache'):parser.add_argument(name,type=Path)
    args=parser.parse_args();build(args.proposal,args.definition,args.output,args.cache)
