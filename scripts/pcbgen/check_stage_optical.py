"""Pinned native source-pose, pin-map and connectivity gate for the stage-optical draft.

Run through scripts/kicad/run.sh. `--disposable` checks a temporary copy, so
the committed board and reports stay untouched. A pass means only: every
netlisted part sits at its source pose, every pad carries its source net, and
native KiCad 10 DRC with schematic parity reports no error, no unconnected
item and no parity issue. Warnings (silkscreen) are counted, not gated.
Physical fit and electrical performance remain NOT RUN.
"""
import json
import math
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
import pcbnew

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.pcbgen.definition import load_definition,load_lock,selected_hardware
from scripts.pcbgen.netlist import read_netlist
from scripts.pcbgen.pose import source_pose
from scripts.pcbgen.ratsnest import inspect
from scripts.pcbgen.route import drc_summary

BOARD_ID='osc-stage-optical'


def check(folder):
    board_path=folder/(BOARD_ID+'.kicad_pcb')
    definition=load_definition(ROOT/'design/boards'/(BOARD_ID+'.json'))
    components,pins=read_netlist(ROOT/definition.netlist)
    hardware={r['ref']:r for r in selected_hardware(definition,load_lock(ROOT/'design/grid/placements.lock.json'))}
    board=pcbnew.LoadBoard(str(board_path))
    if board.GetCopperLayerCount()!=definition.layers or abs(pcbnew.ToMM(board.GetDesignSettings().GetBoardThickness())-definition.thickness_mm)>1e-6:
        raise ValueError('stage-optical stack differs from its definition')
    actual={fp.GetReference():fp for fp in board.GetFootprints() if not fp.GetReference().startswith('MH_')}
    if set(actual)!={c.ref for c in components}:raise ValueError('stage-optical footprint inventory differs from the netlist')
    for component in components:
        fp=actual[component.ref];fields=dict(component.fields)
        pose=source_pose(fields,hardware[component.ref]['rot_deg'] if component.ref in hardware else None)
        xy=tuple(float(v) for v in fields['FootprintOriginMm'].split(','))
        if len(xy)!=2 or not all(math.isfinite(v) for v in xy) or pose.side is None or pose.orientation is None:raise ValueError('incomplete source pose: '+component.ref)
        if component.ref in hardware and xy!=(hardware[component.ref]['x_mm'],hardware[component.ref]['y_mm']):raise ValueError('fixed source origin differs from lockfile: '+component.ref)
        native_xy=(pcbnew.ToMM(fp.GetPosition().x)-100,pcbnew.ToMM(fp.GetPosition().y)-50)
        if (any(abs(a-b)>1e-6 for a,b in zip(xy,native_xy)) or fp.GetLayerName()!=pose.side or
                abs((fp.GetOrientationDegrees()-pose.orientation+180)%360-180)>1e-6 or (component.ref in hardware and not fp.IsLocked())):
            raise ValueError('native source pose/lock differs: '+component.ref)
        expected={pad:net for (ref,pad),net in pins.items() if ref==component.ref}
        mapping={pad.GetNumber():pad.GetNetname() for pad in fp.Pads() if pad.GetNetname()}
        if mapping!=expected:raise ValueError('native pin mapping differs: '+component.ref)
    drc_path=folder/'reports/drc.json';drc_path.parent.mkdir(parents=True,exist_ok=True);drc_path.unlink(missing_ok=True)
    subprocess.run(['kicad-cli','pcb','drc','--schematic-parity','--refill-zones','--format','json','--severity-all','-o',str(drc_path),str(board_path)],check=True)
    raw=json.loads(drc_path.read_text())
    if raw.get('kicad_version')!='10.0.6':raise ValueError('DRC oracle version differs')
    summary=drc_summary(raw)
    if summary['rule_errors'] or summary['unconnected_items'] or summary['schematic_parity_issues']:
        raise ValueError(f"native DRC gate failed: {summary['rule_errors']} errors, {summary['unconnected_items']} unconnected, {summary['schematic_parity_issues']} parity")
    native=inspect(board_path)
    if native['native_unconnected_edges'] or native['native_open_net_count']:raise ValueError('native connected copper incomplete')
    print(f"{BOARD_ID}: {len(components)} parts at source pose; DRC 0 errors / 0 unconnected / 0 parity "
          f"({summary['rule_warnings']} warnings); native open edges 0; physical and electrical qualification NOT RUN")


if __name__=='__main__':
    if sys.argv[1:] not in ([],['--disposable']):raise SystemExit('Usage: check_stage_optical.py [--disposable]')
    if sys.argv[1:]:
        (ROOT/'.circuit-cache').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='stage-optical-check-',dir=ROOT/'.circuit-cache') as temporary:
            folder=Path(temporary)
            shutil.copytree(ROOT/'boards'/BOARD_ID,folder,dirs_exist_ok=True,ignore=shutil.ignore_patterns('routing-work','*.kicad_prl'))
            check(folder)
    else:check(ROOT/'boards'/BOARD_ID)
