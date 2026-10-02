"""Pinned native source/pin/pose and connectivity gate for five draft adapters."""
import hashlib
import json
import math
import subprocess
import tempfile
import shutil
import sys
from pathlib import Path
import pcbnew
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.pcbgen.definition import load_definition,load_lock,selected_hardware
from scripts.pcbgen.netlist import read_netlist
from scripts.pcbgen.ratsnest import inspect
from scripts.pcbgen.route import drc_summary
from scripts.pcbgen.pose import source_pose
from scripts.pcbgen.octave_project import verify_project,TEMPLATE
from scripts.pcbgen.octave_geometry import verify_geometry


def check(bid,folder=None):
    if bid not in {f'osc-octave-{i}' for i in range(1,6)}:raise ValueError('unknown adapter')
    folder=Path(folder) if folder is not None else ROOT/'boards'/bid
    board_path=folder/(bid+'.kicad_pcb')
    definition_path=ROOT/'design/boards'/(bid+'.json')
    definition_bytes=definition_path.read_bytes()
    definition=load_definition(definition_path)
    paths=[board_path,definition_path,ROOT/definition.netlist,folder/(bid+'.kicad_pro'),
        ROOT/'design/grid/placements.lock.json',ROOT/'design/partition/octave-routing.json',
        ROOT/'design/reports/board-net-tokens.json',ROOT/'scripts/kicad/pin.env',ROOT/'scripts/kicad/run.sh',
        Path(__file__),ROOT/'scripts/pcbgen/ratsnest.py',ROOT/'scripts/pcbgen/netlist.py',
        ROOT/'scripts/pcbgen/definition.py',ROOT/'scripts/pcbgen/pose.py']
    paths+=sorted(folder.rglob('*.kicad_sch'))
    netlist_bytes=(ROOT/definition.netlist).read_bytes()
    with tempfile.TemporaryDirectory() as temporary:
        snapshot=Path(temporary)/'source.net';snapshot.write_bytes(netlist_bytes)
        components,pins=read_netlist(snapshot)
    paths += [ROOT/TEMPLATE,folder/'fp-lib-table',folder/'sym-lib-table',ROOT/'symbols/zudo-osc-hole-field.kicad_sym']
    paths += [Path(module.__file__).resolve() for module in list(sys.modules.values())
              if getattr(module,'__file__',None) and str(Path(module.__file__).resolve()).startswith(str(ROOT)+'/')
              and Path(module.__file__).suffix=='.py']
    for component in components:
        paths.append(ROOT/'footprints/kicad/zudo-osc-hole-field.pretty'/(component.footprint.split(':')[1]+'.kicad_mod'))
    frozen={str(p.relative_to(ROOT)):p.read_bytes() for p in paths}
    if frozen[str(definition_path.relative_to(ROOT))]!=definition_bytes or frozen[definition.netlist]!=netlist_bytes:
        raise ValueError('source changed during snapshot')
    verify_geometry(frozen[str(board_path.relative_to(ROOT))],definition)
    custom=folder/(bid+'.kicad_dru')
    absent=[custom,ROOT/'fp-lib-table']
    if any(p.exists() or p.is_symlink() for p in absent):raise ValueError('undeclared custom rules or root library table')
    board=pcbnew.LoadBoard(str(board_path));fps=list(board.GetFootprints())
    actual={f.GetReference():f for f in fps}
    if len(fps)!=3 or set(actual)!={c.ref for c in components}:raise ValueError('adapter footprint inventory differs')
    hardware={r['ref']:r for r in selected_hardware(definition,load_lock(ROOT/'design/grid/placements.lock.json'))}
    if len(hardware)!=1 or board.GetCopperLayerCount()!=2 or abs(pcbnew.ToMM(board.GetDesignSettings().GetBoardThickness())-definition.thickness_mm)>1e-6:
        raise ValueError('adapter stack or hardware differs')
    rows=[]
    for component in components:
        fp=actual[component.ref];fields=dict(component.fields)
        pose=source_pose(fields,hardware[component.ref]['rot_deg'] if component.ref in hardware else None)
        xy=tuple(float(x) for x in fields['FootprintOriginMm'].split(','))
        if len(xy)!=2 or not all(math.isfinite(v) for v in xy) or pose.side is None or pose.orientation is None:raise ValueError('incomplete source pose')
        if component.ref in hardware and xy!=(hardware[component.ref]['x_mm'],hardware[component.ref]['y_mm']):raise ValueError('fixed source origin differs from lockfile')
        actual_xy=(pcbnew.ToMM(fp.GetPosition().x)-100,pcbnew.ToMM(fp.GetPosition().y)-50)
        if any(abs(a-b)>1e-6 for a,b in zip(xy,actual_xy)) or fp.GetLayerName()!=pose.side or abs((fp.GetOrientationDegrees()-pose.orientation+180)%360-180)>1e-6 or not fp.IsLocked():raise ValueError('native source pose/lock differs: '+component.ref)
        if fp.GetValue()!=component.value or str(fp.GetFPID().GetLibNickname())+':'+str(fp.GetFPID().GetLibItemName())!=component.footprint:raise ValueError('native part identity differs')
        expected={pad:net for (ref,pad),net in pins.items() if ref==component.ref}
        pads=list(fp.Pads());mapping={pad.GetNumber():pad.GetNetname() for pad in pads}
        if len(mapping)!=len(pads) or mapping!=expected:raise ValueError('complete native pin mapping differs: '+component.ref)
        rows.append({'reference':component.ref,'xy_mm':list(xy),'side':pose.side,'angle_deg':pose.orientation,'pins':mapping})
    project=json.loads(frozen[str((folder/(bid+'.kicad_pro')).relative_to(ROOT))])
    verify_project(project,frozen[str(TEMPLATE)],definition.routing)
    drc_path=folder/'reports/drc.json';drc_path.parent.mkdir(parents=True,exist_ok=True)
    command=['kicad-cli','pcb','drc','--schematic-parity','--refill-zones','--format','json','--severity-all','-o',str(drc_path),str(board_path)]
    drc_path.unlink(missing_ok=True)
    subprocess.run(command,check=True)
    drc_bytes=drc_path.read_bytes();raw_drc=json.loads(drc_bytes)
    if raw_drc.get('source')!=board_path.name or raw_drc.get('kicad_version')!='10.0.6':raise ValueError('fresh DRC oracle/source differs')
    if raw_drc.get('$schema')!='https://schemas.kicad.org/drc.v1.json' or raw_drc.get('coordinate_units')!='mm':raise ValueError('fresh DRC schema/units differ')
    severities=raw_drc.get('included_severities')
    if not isinstance(severities,list) or len(severities)!=3 or set(severities)!={'error','warning','exclusion'}:raise ValueError('fresh DRC severity scope differs')
    drc=drc_summary(raw_drc)
    if any(raw_drc[key] for key in ('violations','unconnected_items','schematic_parity')):raise ValueError('native DRC incomplete')
    native=inspect(board_path)
    if native['native_unconnected_edges'] or native['native_open_net_count'] or native['multi_pad_candidate_net_count']!=8:raise ValueError('native connected copper incomplete')
    if drc_path.read_bytes()!=drc_bytes:raise ValueError('DRC output changed during native check')
    if any((ROOT/path).read_bytes()!=data for path,data in frozen.items()):raise ValueError('source changed during native check')
    if any(p.exists() or p.is_symlink() for p in absent):raise ValueError('custom rules/library table appeared during check')
    result={'status':'CONNECTED UNVALIDATED DRAFT','board_id':bid,'source_sha256':{p:hashlib.sha256(raw).hexdigest() for p,raw in sorted(frozen.items())},
        'absent_inputs':[str(p.relative_to(ROOT)) for p in absent],'custom_rules':'ABSENT','drc_sha256':hashlib.sha256(drc_bytes).hexdigest(),'drc_command':command,'oracle':'KiCad 10.0.6 pinned container','drc':drc,'native_connectivity':native,'components':rows,
        'physical_fit':'NOT RUN #55/#65','electrical_performance':'NOT RUN; no ground-material/model qualification or protection acceptance'}
    (folder/'reports/source-parity.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(bid+': exact3-part/30-pad pose/source parity;8 functional nets connected; physical qualification NOT RUN')

if __name__=='__main__':
    if sys.argv[1:] not in ([],['--disposable']):raise SystemExit('Usage: check_octave.py [--disposable]')
    for number in range(1,6):
        bid=f'osc-octave-{number}'
        if sys.argv[1:]:
            with tempfile.TemporaryDirectory(prefix='octave-check-',dir=ROOT/'.circuit-cache') as temporary:
                folder=Path(temporary)
                shutil.copytree(ROOT/'boards'/bid,folder,dirs_exist_ok=True,ignore=shutil.ignore_patterns('routing-work','*.kicad_prl'))
                check(bid,folder)
        else:check(bid)
