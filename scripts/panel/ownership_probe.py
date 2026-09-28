#!/usr/bin/env python3
"""Exercise owner text and edited managed artwork preservation on a scratch PCB."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile

import pcbnew

ROOT = Path(__file__).resolve().parents[2]
SOURCE_BOARD = ROOT / 'boards/panel/panel.kicad_pcb'
SOURCE_MANIFEST = ROOT / 'boards/panel/reports/generated-manifest.json'


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    manifest = json.loads(SOURCE_MANIFEST.read_text())['art']
    label_key, record = next((key, item) for key, item in manifest.items()
                             if item['source'].get('text') == '1V/OCT'
                             and item['source']['layer'] == 'F.SilkS')
    with tempfile.TemporaryDirectory(prefix='panel-owner-', dir=ROOT / '.circuit-cache/panel') as folder:
        root = Path(folder)
        board_path = root / 'panel.kicad_pcb'
        manifest_path = root / 'generated-manifest.json'
        report_path = root / 'regeneration.json'
        shutil.copyfile(SOURCE_BOARD, board_path)
        shutil.copyfile(SOURCE_MANIFEST, manifest_path)
        board = pcbnew.LoadBoard(str(board_path))
        label = next(item for item in board.GetDrawings()
                     if item.m_Uuid.AsString() == record['uuid'])
        label.SetText('OWNER 1V/OCT')
        owner = pcbnew.PCB_TEXT(board)
        owner.SetText('OWNER SILK')
        owner.SetLayer(pcbnew.F_SilkS)
        owner.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(390), pcbnew.FromMM(64)))
        owner.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(1.2), pcbnew.FromMM(1.2)))
        owner.SetTextThickness(pcbnew.FromMM(.18))
        board.Add(owner)
        pcbnew.SaveBoard(str(board_path), board)
        command = ['python3', 'scripts/panel/gen_panel.py', '--board', str(board_path),
                   '--manifest', str(manifest_path), '--report', str(report_path)]
        subprocess.check_call(command, cwd=ROOT)
        report = json.loads(report_path.read_text())
        if label_key not in report['edited_generated_artwork_preserved']:
            raise ValueError('edited managed label was not reported')
        after = pcbnew.LoadBoard(str(board_path))
        texts = [item.GetText() for item in after.GetDrawings()
                 if isinstance(item, pcbnew.PCB_TEXT)]
        if 'OWNER SILK' not in texts or 'OWNER 1V/OCT' not in texts:
            raise ValueError('owner text or edited label was lost')
        first = digest(board_path)
        subprocess.check_call(command, cwd=ROOT)
        if digest(board_path) != first:
            raise ValueError('owner-preserving rerun changed board bytes')
        print('PASS: owner-added silk and edited generated label preserved; rerun byte-identical')


if __name__ == '__main__':
    main()
