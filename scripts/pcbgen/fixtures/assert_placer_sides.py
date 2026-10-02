#!/usr/bin/env python3
"""Native face/anchor regressions using disposable copies of the six fixture."""
from dataclasses import replace
import json
from pathlib import Path
import shutil
import sys
import tempfile
from unittest.mock import patch
import pcbnew
ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from scripts.pcbgen import place as placer


def main():
    board_id='fixture-place-six'
    folder=ROOT/'.circuit-cache/placer/six'
    original=folder/(board_id+'.kicad_pcb')
    definition=placer.load_definition(ROOT/'design/boards'/(board_id+'.json'))
    components,nets=placer.read_netlist(folder/(board_id+'.net'))
    with tempfile.TemporaryDirectory(prefix='face-anchors-',dir=folder) as temporary:
        work=Path(temporary)
        path=work/'trial.kicad_pcb'
        shutil.copyfile(original,path)
        board=pcbnew.LoadBoard(str(path))
        # Explicitly request F.Cu only on the second repeat. Both F/B regions
        # exist, so initial side selection is legal; the base B template is not.
        mixed=tuple(r for region in definition.regions for r in (region,{**region,'side':'F.Cu'}))
        rows=[]
        for component in components:
            fields=dict(component.fields)
            fields['BoardSide']='F.Cu' if placer.normalize_block(component)=='S2' else 'B.Cu'
            rows.append(replace(component,fields=tuple(fields.items())))
        before=path.read_bytes()
        report=work/'failure.json'
        with patch.object(placer,'load_definition',return_value=replace(definition,regions=mixed)), \
             patch.object(placer,'read_netlist',return_value=(rows,nets)), \
             patch.object(placer.pcbnew,'LoadBoard',return_value=board):
            try:
                placer.place(board_id,path,folder/(board_id+'.net'),report)
            except placer.PlacementFailure as failure:
                assert 'face' in failure.reason, failure.reason
            else:
                raise AssertionError('opposite native face accepted under repeated B.Cu template')
        assert path.read_bytes()==before, 'failed side plan changed board bytes'
        actual=next(fp.GetLayerName() for fp in board.GetFootprints() if fp.GetReference()=='U202')
        assert actual=='F.Cu', actual
        failed=json.loads(report.read_text())
        assert failed['status']=='OVERFLOW' and failed['overflow'][0]['instance']=='S2'
        print('PASS: actual F.Cu repeat rejected under B.Cu template; failed board bytes unchanged')

        # Explicit anchors take precedence over search. A base anchor must
        # nevertheless seed the template for repeats without an explicit anchor.
        board=pcbnew.LoadBoard(str(path))
        anchored=next(fp for fp in board.GetFootprints() if fp.GetReference()=='R103')
        position=anchored.GetPosition()
        xy=(pcbnew.ToMM(position.x)-100,pcbnew.ToMM(position.y)-50)
        rows=[]
        for component in components:
            fields=dict(component.fields)
            if component.ref=='R103':
                fields.update(FootprintOriginMm=f'{xy[0]},{xy[1]}',BoardSide='B.Cu')
            rows.append(replace(component,fields=tuple(fields.items())))
        report=work/'anchored.json'
        with patch.object(placer,'read_netlist',return_value=(rows,nets)):
            first=placer.place(board_id,path,folder/(board_id+'.net'),report)
            saved=path.read_bytes()
            placer.place(board_id,path,folder/(board_id+'.net'),report)
            assert path.read_bytes()==saved, 'anchored template rerun changed board'
        by_ref={p['ref']:p for p in first['placements']}
        assert (by_ref['R103']['x_mm'],by_ref['R103']['y_mm'])==xy
        assert abs(by_ref['R203']['x_mm']-xy[0]-17)<1e-6
        assert abs(by_ref['R203']['y_mm']-xy[1])<1e-6
        result=pcbnew.LoadBoard(str(path))
        assert all(fp.GetLayerName()=='B.Cu' for fp in result.GetFootprints()
                   if fp.GetReference() in by_ref)
        print('PASS: source-anchored base seeds translated template; all actual faces B.Cu; rerun byte stable')


if __name__=='__main__':
    main()
