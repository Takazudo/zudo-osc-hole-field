"""Reject stale clean DRC, changed physical pads and weakened project rules."""
import json
import shutil
import sys
import tempfile
from pathlib import Path
import pcbnew
ROOT=Path(__file__).resolve().parents[3];sys.path.insert(0,str(ROOT))
from scripts.pcbgen.check_octave import check

bid='osc-octave-1';source=ROOT/'boards'/bid
for case in ('none','short-with-clean-report','changed-drill','ignored-short','extra-assignment','shifted-outline','extra-cutout','zone-clearance'):
    with tempfile.TemporaryDirectory(prefix='octave-gate-',dir=ROOT/'.circuit-cache') as temporary:
        folder=Path(temporary);shutil.copytree(source,folder,dirs_exist_ok=True,ignore=shutil.ignore_patterns('routing-work','*.kicad_prl'))
        pcb=folder/(bid+'.kicad_pcb');project=folder/(bid+'.kicad_pro')
        board=pcbnew.LoadBoard(str(pcb));fps={p.GetReference():p for p in board.GetFootprints()}
        print('Native FPID:',repr(fps['SW101'].GetFPID().GetLibItemName()),str(fps['SW101'].GetFPID().GetLibNickname())+':'+str(fps['SW101'].GetFPID().GetLibItemName()))
        if case=='short-with-clean-report':
            pads={p.GetNumber():p for p in fps['SW101'].Pads()}
            track=pcbnew.PCB_TRACK(board);track.SetStart(pads['2'].GetPosition());track.SetEnd(pads['3'].GetPosition());track.SetWidth(pcbnew.FromMM(.2));track.SetLayer(pcbnew.F_Cu);track.SetNetCode(pads['2'].GetNetCode());board.Add(track);pcbnew.SaveBoard(str(pcb),board)
        elif case=='changed-drill':
            pad=next(p for p in fps['SW101'].Pads() if p.GetNumber()=='2');pad.SetDrillSize(pcbnew.VECTOR2I(pcbnew.FromMM(.8),pcbnew.FromMM(.8)));pcbnew.SaveBoard(str(pcb),board)
        elif case=='shifted-outline':
            for item in board.GetDrawings():
                if item.GetLayer()==pcbnew.Edge_Cuts:item.Move(pcbnew.VECTOR2I(pcbnew.FromMM(.01),0))
            pcbnew.SaveBoard(str(pcb),board)
        elif case=='extra-cutout':
            item=pcbnew.PCB_SHAPE(board);item.SetLayer(pcbnew.Edge_Cuts);item.SetShape(pcbnew.SHAPE_T_CIRCLE)
            item.SetCenter(pcbnew.VECTOR2I(pcbnew.FromMM(114.5),pcbnew.FromMM(222.5)));item.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(115),pcbnew.FromMM(222.5)));item.SetWidth(pcbnew.FromMM(.05));board.Add(item);pcbnew.SaveBoard(str(pcb),board)
        elif case=='zone-clearance':
            next(iter(board.Zones())).SetLocalClearance(pcbnew.FromMM(.01));pcbnew.SaveBoard(str(pcb),board)
        elif case in ('ignored-short','extra-assignment'):
            data=json.loads(project.read_bytes())
            if case=='ignored-short':data['board']['design_settings']['rule_severities']['shorting_items']='ignore'
            else:data['net_settings']['netclass_assignments']={'AGND':'Default'}
            project.write_text(json.dumps(data))
        before=pcb.read_bytes()
        if case=='none':check(bid,folder)
        else:
            try:check(bid,folder)
            except ValueError as error:print('Expected rejection',case,str(error))
            else:raise AssertionError('accepted '+case)
        assert pcb.read_bytes()==before,'check mutated PCB'
print('PASS:8 native octave gate controls; stale DRC and rule/physical drift reject')
