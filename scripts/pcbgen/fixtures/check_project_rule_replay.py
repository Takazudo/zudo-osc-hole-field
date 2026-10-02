#!/usr/bin/env python3
"""A retained routing digest cannot bypass current project rule restoration."""
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile

ROOT=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(ROOT))
from scripts.pcbgen.definition import load_definition


def main():
    source=ROOT/'.circuit-cache/router/dense'
    board_id='fixture-route-dense'
    definition=load_definition(ROOT/'design/boards'/f'{board_id}.json')
    source_report=json.loads((source/'reports/replay-routing.json').read_text())
    with tempfile.TemporaryDirectory(prefix='project-rules-',dir=source.parent) as temporary:
        directory=Path(temporary)
        for name in (board_id+'.kicad_pcb',board_id+'.kicad_pro',board_id+'.kicad_sch',
                     'sym-lib-table','fp-lib-table'):
            if (source/name).exists():shutil.copyfile(source/name,directory/name)
        shutil.copytree(source/'sheets',directory/'sheets')
        board=directory/(board_id+'.kicad_pcb')
        original_board=board.read_bytes()
        project=board.with_suffix('.kicad_pro')
        data=json.loads(project.read_text())
        data['board']['design_settings']['rules']['min_track_width']=.001
        next(c for c in data['net_settings']['classes'] if c['name']=='Default')['clearance']=0
        data['owner_regression_note']='preserve unrelated project fields'
        project.write_text(json.dumps(data))
        report=directory/'reports/routing.json';report.parent.mkdir()
        report.write_text(json.dumps({'routing_spec_sha256':source_report['routing_spec_sha256']}))
        command=['bash','scripts/pcbgen/route.sh',board_id,'--board',str(board.relative_to(ROOT)),
                 '--report',str(report.relative_to(ROOT)),'--timeout-sec','1']
        subprocess.run(command,cwd=ROOT,check=True)
        result=json.loads(report.read_text())
        assert result['status']=='UPDATED DRAFT' and result['project_settings_refreshed']
        assert result['native_gate_status']=='ZERO OPEN EDGES'
        restored=json.loads(project.read_text())
        expected=next(c for c in definition.routing['net_classes'] if c['name']=='Default')
        assert next(c for c in restored['net_settings']['classes'] if c['name']=='Default')['clearance']==expected['clearance_mm']
        assert restored['board']['design_settings']['rules']['min_track_width']==definition.routing['min_track_width_mm']
        assert restored['owner_regression_note']==data['owner_regression_note']
        assert board.read_bytes()==original_board
        restored_bytes=project.read_bytes()
        subprocess.run(command,cwd=ROOT,check=True)
        second=json.loads(report.read_text())
        assert second['status']=='UNCHANGED DRAFT' and not second['project_settings_refreshed']
        assert board.read_bytes()==original_board and project.read_bytes()==restored_bytes
        assert second['native_board_sha256']==hashlib.sha256(original_board).hexdigest()
        print('PASS: current project rules restored before native DRC; unrelated settings/copper preserved; rerun byte-stable')


if __name__=='__main__':main()
