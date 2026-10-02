"""Native fixed-only placement rejection controls; disposable board copies."""
import json
import shutil
import sys
import tempfile
from dataclasses import replace
from unittest.mock import patch
from pathlib import Path
import pcbnew
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from scripts.pcbgen.place import place
from scripts.pcbgen.netlist import read_netlist


def run():
    bid='osc-octave-1'
    source=ROOT/'boards'/bid/(bid+'.kicad_pcb')
    with tempfile.TemporaryDirectory(prefix='fixed-only-',dir=ROOT/'.circuit-cache') as folder:
        folder=Path(folder)
        board_path=folder/(bid+'.kicad_pcb');report_path=folder/'placement.json'
        count=0
        for mutation in ('none','unlock','extra','origin','face','angle','fixed-face','fixed-angle','fixed-origin'):
            shutil.copyfile(source,board_path)
            board=pcbnew.LoadBoard(str(board_path))
            fps={p.GetReference():p for p in board.GetFootprints()}
            header=fps['J900114'];fixed=fps['SW101']
            if mutation=='unlock':header.SetLocked(False)
            elif mutation=='extra':
                extra=pcbnew.FOOTPRINT(header);extra.SetReference('EXTRA');extra.SetLocked(False);board.Add(extra)
            elif mutation=='origin':header.Move(pcbnew.VECTOR2I(pcbnew.FromMM(.1),0))
            elif mutation=='face':header.Flip(header.GetPosition(),False)
            elif mutation=='angle':header.SetOrientationDegrees(header.GetOrientationDegrees()+1)
            elif mutation=='fixed-face':fixed.Flip(fixed.GetPosition(),False)
            elif mutation=='fixed-angle':fixed.SetOrientationDegrees(1)
            elif mutation=='fixed-origin':fixed.Move(pcbnew.VECTOR2I(pcbnew.FromMM(.1),0))
            if mutation!='none':pcbnew.SaveBoard(str(board_path),board)
            before=board_path.read_bytes()
            if mutation=='none':
                result=place(bid,board_path,report_path=report_path)
                assert result['status']=='PLACED DRAFT' and result['placements']==[] and result['regions']==[]
                first=report_path.read_bytes()
                place(bid,board_path,report_path=report_path)
                assert first==report_path.read_bytes()
            else:
                try:place(bid,board_path,report_path=report_path)
                except ValueError:pass
                else:raise AssertionError('accepted mutation '+mutation)
            assert board_path.read_bytes()==before,mutation+' changed board bytes'
            count+=1
        components,pin_nets=read_netlist(ROOT/'schematic/boards'/f'{bid}.net')
        for field,value in [('FootprintOriginMm','nan,179.55'),('FootprintOriginMm','14.5,inf'),
                ('KiCadOrientationDeg','nan'),('KiCadOrientationDeg',''),('BoardSide','')]:
            shutil.copyfile(source,board_path)
            before=board_path.read_bytes()
            changed=[]
            for component in components:
                if component.ref=='J900114':
                    fields=dict(component.fields);fields[field]=value
                    component=replace(component,fields=tuple(fields.items()))
                changed.append(component)
            with patch('scripts.pcbgen.place.read_netlist',return_value=(changed,pin_nets)):
                try:place(bid,board_path,report_path=report_path)
                except ValueError:pass
                else:raise AssertionError('accepted source mutation '+field+'='+value)
            assert board_path.read_bytes()==before,'source failure changed board bytes'
            count+=1
        print(f'PASS: {count} native fixed-only placement cases; failures preserve board bytes')

if __name__=='__main__':run()
