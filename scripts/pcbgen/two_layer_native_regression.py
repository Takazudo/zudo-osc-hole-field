"""Pinned native enabled-foil/reference export fixture, not a PCB acceptance."""
import hashlib
import json
import shutil
import sys
from pathlib import Path
import pcbnew

ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT))
from scripts.pcbgen.extract_power_geometry import extract,enabled_copper_layers
from scripts.pcbgen.native_stack import apply


def run(folder):
    folder.mkdir(parents=True,exist_ok=False)
    inputs=[Path(__file__),ROOT/'scripts/pcbgen/extract_power_geometry.py',
        ROOT/'scripts/pcbgen/native_stack.py',ROOT/'scripts/pcbgen/foil_stack.py',
        ROOT/'scripts/pcbgen/definition.py',ROOT/'design/boards/osc-stage-optical.json',
        ROOT/'boards/osc-jack-left/osc-jack-left.kicad_pro',ROOT/'design/reports/io-partition.json']
    retained={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
    (folder/'startup-source.json').write_text(json.dumps(retained,indent=2)+'\n')
    if pcbnew.GetBuildVersion()!='10.0.6':raise ValueError('wrong native oracle')
    board=pcbnew.BOARD();board.SetCopperLayerCount(2)
    board.GetDesignSettings().SetBoardThickness(pcbnew.FromMM(.4))
    def vec(x,y):return pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y))
    nets={}
    for name in ('AGND','+12V'):
        nets[name]=pcbnew.NETINFO_ITEM(board,name);board.Add(nets[name])
    ids={}
    for ref,number,net,x,through in [('J900379','2','AGND',110,False),
        ('J900381','2','AGND',112,True),('U101','4','+12V',114,True)]:
        fp=pcbnew.FOOTPRINT(board);fp.SetReference(ref);fp.SetPosition(vec(x,60))
        if not through:fp.SetLayer(pcbnew.B_Cu)
        pad=pcbnew.PAD(fp);pad.SetNumber(number);pad.SetPosition(vec(x,60))
        pad.SetShape(pcbnew.PAD_SHAPE_CIRCLE if through else pcbnew.PAD_SHAPE_RECT)
        pad.SetSize(vec(1,1));pad.SetNet(nets[net])
        if through:
            pad.SetAttribute(pcbnew.PAD_ATTRIB_PTH);pad.SetDrillSize(vec(.3,.3));pad.SetLayerSet(pcbnew.LSET.AllCuMask())
        else:
            pad.SetAttribute(pcbnew.PAD_ATTRIB_SMD);mask=pcbnew.LSET();mask.AddLayer(pcbnew.B_Cu);pad.SetLayerSet(mask)
        fp.Add(pad);board.Add(fp);ids[ref]=pad.m_Uuid.AsString()
    via=pcbnew.PCB_VIA(board);via.SetViaType(pcbnew.VIATYPE_THROUGH)
    via.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);via.SetPosition(vec(111,60))
    via.SetWidth(pcbnew.FromMM(.7));via.SetDrill(pcbnew.FromMM(.3));via.SetNet(nets['AGND']);board.Add(via)
    track=pcbnew.PCB_TRACK(board);track.SetStart(vec(110,60));track.SetEnd(vec(112,60))
    track.SetWidth(pcbnew.FromMM(.3));track.SetLayer(pcbnew.B_Cu);track.SetNet(nets['AGND']);board.Add(track)
    corners=[(108,58),(116,58),(116,62),(108,62)]
    for a,b in zip(corners,corners[1:]+corners[:1]):
        edge=pcbnew.PCB_SHAPE(board);edge.SetShape(pcbnew.SHAPE_T_SEGMENT);edge.SetLayer(pcbnew.Edge_Cuts)
        edge.SetStart(vec(*a));edge.SetEnd(vec(*b));edge.SetWidth(pcbnew.FromMM(.05));board.Add(edge)
    definition=json.loads((ROOT/'design/boards/osc-stage-optical.json').read_text())
    definition['stackup']=[{'layer':'F.Cu','copper_thickness_mm':.035,'nominal_midplane_depth_mm':.0175},
        {'layer':'dielectric-1','thickness_mm':.33},
        {'layer':'B.Cu','copper_thickness_mm':.035,'nominal_midplane_depth_mm':.3825}]
    spec=folder/'osc-stage-optical.json';spec.write_text(json.dumps(definition,indent=2)+'\n')
    path=folder/'fixture.kicad_pcb';pcbnew.SaveBoard(str(path),board)
    path.write_text(apply(path.read_text(),definition)[0])
    # EL's canonical project is schematic-only at this stage. This disposable
    # API fixture needs an explicit PCB rule block; retain an existing complete
    # project and alter only its filename. No DRC acceptance is inferred.
    project=json.loads((ROOT/'boards/osc-jack-left/osc-jack-left.kicad_pro').read_text())
    project['meta']['filename']=path.with_suffix('.kicad_pro').name
    path.with_suffix('.kicad_pro').write_text(json.dumps(project,indent=2)+'\n')
    output=folder/'geometry.json';extract('osc-stage-optical',path,output,spec,('J900379','2'))
    data=json.loads(output.read_text())
    if data['enabled_copper_layers']!=['F.Cu','B.Cu']:raise ValueError('phantom physical foil')
    for item in data['items']:
        if set(item['copper'])-{'F.Cu','B.Cu'}:raise ValueError('inactive PTH annulus exported')
    if any(h['copper_layers']!=['F.Cu','B.Cu'] for h in data['holes']):raise ValueError('hole span differs')
    if set(data['main_rail_members']):raise ValueError('named reference invented a main land')
    if not {ids['J900379'],ids['J900381'],via.m_Uuid.AsString()}.issubset(data['ground_reference_members']):
        raise ValueError('named actual component is incomplete')
    rails=[c for c in data['clusters'] if c['net']=='+12V']
    if not rails or any(c['fed'] is not None for c in rails):raise ValueError('main-free rail was falsely classified')
    for expected in (('F.Cu','In1.Cu','In2.Cu','B.Cu'),('B.Cu','F.Cu')):
        try:enabled_copper_layers(board,expected)
        except ValueError:pass
        else:raise ValueError('wrong source layer contract was accepted')
    try:extract('osc-stage-optical',path,folder/'invalid.json',spec,('U101','4'))
    except ValueError:pass
    else:raise ValueError('foreign rail reference was accepted')
    wrong=json.loads(spec.read_text());wrong['thickness_mm']=1.6
    wrong['stackup'][1]['thickness_mm']=1.53
    wrong['stackup'][2]['nominal_midplane_depth_mm']=1.5825
    (folder/'wrong-depth').mkdir()
    wrong_path=folder/'wrong-depth/osc-stage-optical.json';wrong_path.write_text(json.dumps(wrong))
    try:extract('osc-stage-optical',path,folder/'wrong-depth-export.json',wrong_path,('J900379','2'))
    except ValueError as error:
        if 'native board thickness differs' not in str(error):raise
    else:raise ValueError('wrong physical native thickness was accepted')
    if (folder/'wrong-depth-export.json').exists():raise ValueError('wrong depth published an export')
    legacy=ROOT/'design/boards/osc-stage-optical.json'
    legacy_output=folder/'legacy-geometry.json'
    extract('osc-stage-optical',path,legacy_output,legacy,('J900379','2'))
    legacy_data=json.loads(legacy_output.read_text())
    if legacy_data['stack_metadata_scope']['mode']!='legacy copper-weight labels only':
        raise ValueError('legacy export invented physical foil bands')
    if legacy_data['stackup']!=json.loads(legacy.read_text())['stackup']:
        raise ValueError('legacy copper-weight source labels changed')
    partial=json.loads(legacy.read_text());partial['stackup'][0]['copper_thickness_mm']=.035
    (folder/'partial-stack').mkdir()
    partial_path=folder/'partial-stack/osc-stage-optical.json';partial_path.write_text(json.dumps(partial))
    try:extract('osc-stage-optical',path,folder/'partial-export.json',partial_path,('J900379','2'))
    except (ValueError,KeyError):pass
    else:raise ValueError('partially specified physical stack was accepted')
    if (folder/'partial-export.json').exists():raise ValueError('partial stack published an export')
    if any(hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=value for name,value in retained.items()):
        raise ValueError('native fixture source changed during execution')
    receipt={'status':'PASS: native two-layer export fixture only; no board DRC/physical acceptance',
        'source_sha256':retained,
        'kicad_version':pcbnew.GetBuildVersion(),'enabled_copper_layers':data['enabled_copper_layers'],
        'ground_reference':data['ground_reference'],'unclassified_rail_clusters':len(rails),
        'physical_holes':len(data['holes']),
        'sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in
            (path,path.with_suffix('.kicad_pro'),spec,output,Path(__file__),
             ROOT/'scripts/pcbgen/extract_power_geometry.py',ROOT/'scripts/pcbgen/native_stack.py',ROOT/'scripts/pcbgen/foil_stack.py')}}
    (folder/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(receipt['status'],flush=True)


if __name__=='__main__':run(Path(sys.argv[1]).resolve())
