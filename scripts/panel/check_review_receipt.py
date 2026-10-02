#!/usr/bin/env python3
"""Reject stale retained native panel review evidence; never regenerate hashes."""
from __future__ import annotations
import hashlib
import json
import math
from pathlib import Path
import re
import struct

ROOT = Path(__file__).resolve().parents[2]
RECEIPT = 'boards/panel/reports/native-review.json'
INPUTS = ('boards/panel/panel.kicad_pcb', 'boards/panel/panel.kicad_pro',
          'design/panel/panel-params.json', 'design/grid/placements.lock.json',
          'scripts/kicad/pin.env', 'scripts/kicad/run.sh', 'scripts/panel/check_panel.py')
ABSENT_INPUTS = ('boards/panel/panel.kicad_dru',)
OUTPUTS = ('boards/panel/reports/drc.json', 'boards/panel/reports/feature-table.json',
           'boards/panel/reports/panel-top.png',
           'doc/public/assets/osc-hole-field/panel-kicad-top.png')
VERSION = '10.0.6'
COMMANDS = {
    'version': ['bash', 'scripts/kicad/run.sh', 'kicad-cli', 'version'],
    'features': ['bash', 'scripts/kicad/run.sh', 'python3', 'scripts/panel/check_panel.py',
                 '--output', '.circuit-cache/panel-review-refresh/features.json'],
    'drc': ['bash', 'scripts/kicad/run.sh', 'kicad-cli', 'pcb', 'drc', '--format', 'json',
            '--severity-all', '--output', '.circuit-cache/panel-review-refresh/drc.json',
            'boards/panel/panel.kicad_pcb'],
    'render': ['bash', 'scripts/kicad/run.sh', 'kicad-cli', 'pcb', 'render', '--width', '2384',
               '--height', '2240', '--side', 'top', '--quality', 'high', '--background', 'opaque',
               '--use-board-stackup-colors', '--output',
               '.circuit-cache/panel-review-refresh/panel-top-opaque.png',
               'boards/panel/panel.kicad_pcb'],
}


def verify(root: Path = ROOT):
    receipt_bytes = (root / RECEIPT).read_bytes()
    receipt = json.loads(receipt_bytes)
    if (not isinstance(receipt, dict) or type(receipt.get('schema_version')) is not int
            or receipt['schema_version'] != 1 or receipt.get('commands') != COMMANDS):
        raise ValueError('native panel receipt schema/command mismatch')
    if receipt.get('absent_inputs') != list(ABSENT_INPUTS):
        raise ValueError('native panel receipt missing custom-rule absence declaration')
    def absent():
        return all(not (root / p).exists() and not (root / p).is_symlink() for p in ABSENT_INPUTS)
    if not absent():
        raise ValueError('native panel custom-rule absence changed; fresh source capture required')
    snapshots = {}
    for group, paths in (('inputs', INPUTS), ('outputs', OUTPUTS)):
        records = receipt.get(group)
        if not isinstance(records, dict) or set(records) != set(paths):
            raise ValueError(f'native panel receipt incomplete {group}')
        for path in paths:
            record = records[path]
            data = (root / path).read_bytes(); snapshots[path] = data
            if (not isinstance(record, dict) or set(record) != {'sha256', 'bytes'}
                    or not isinstance(record['sha256'], str)
                    or re.fullmatch('[0-9a-f]{64}', record['sha256']) is None
                    or type(record['bytes']) is not int or record['bytes'] <= 0):
                raise ValueError(f'invalid native panel receipt metadata: {path}')
            if record['sha256'] != hashlib.sha256(data).hexdigest() or record['bytes'] != len(data):
                raise ValueError(f'stale native panel review evidence: {path}; rerun native DRC/render and review')
    pin = re.search(r"^KICAD_IMAGE='([^']+)'", snapshots['scripts/kicad/pin.env'].decode(), re.M)
    if not pin or receipt.get('oracle') != {'kicad_version': VERSION, 'image': pin.group(1)}:
        raise ValueError('native panel oracle identity mismatch')
    params = json.loads(snapshots['design/panel/panel-params.json'])
    required = params['artwork']['copper_min_clearance_to_hole_or_edge_mm']
    settings = json.loads(snapshots['boards/panel/panel.kicad_pro'])['board']['design_settings']
    if (type(required) not in (int, float) or not math.isfinite(required) or required < .2
            or settings['drc_exclusions']):
        raise ValueError('native panel DRC source rule floor/exclusions mismatch')
    for rule, severity in (('min_copper_edge_clearance', 'copper_edge_clearance'),
                           ('min_hole_clearance', 'hole_clearance')):
        value = settings['rules'][rule]
        if (type(value) not in (int, float) or not math.isfinite(value) or value < required
                or settings['rule_severities'][severity] != 'error'):
            raise ValueError('native panel DRC source rule floor/exclusions mismatch')
    drc = json.loads(snapshots[OUTPUTS[0]])
    if (not isinstance(drc, dict)
            or drc.get('$schema') != 'https://schemas.kicad.org/drc.v1.json'
            or drc.get('coordinate_units') != 'mm'
            or drc.get('kicad_version') != VERSION or drc.get('source') != 'panel.kicad_pcb'
            or not isinstance(drc.get('included_severities'), list)
            or not all(isinstance(x, str) for x in drc['included_severities'])
            or len(drc['included_severities']) != 3
            or set(drc['included_severities']) != {'error', 'warning', 'exclusion'}):
        raise ValueError('native panel DRC scope/version mismatch')
    for key in ('violations', 'unconnected_items', 'schematic_parity'):
        if not isinstance(drc.get(key), list) or drc[key]:
            raise ValueError(f'native panel DRC incomplete or nonzero: {key}')
    features = json.loads(snapshots[OUTPUTS[1]])
    summary = {key: features[key] for key in
               ('features', 'drilled_holes', 'undrilled_optical_windows')}
    summary['octave_diameters_mm'] = [row['diameter_mm'] for row in features['rows']
                                      if row['kind'] == 'octave']
    if receipt.get('feature_summary') != summary or receipt.get('render_requested_pixels') != [2384, 2240]:
        raise ValueError('native panel receipt summary differs from native table/command')
    png = snapshots[OUTPUTS[2]]
    if png != snapshots[OUTPUTS[3]]:
        raise ValueError('published panel image differs from native render')
    if len(png) < 24 or png[:8] != b'\x89PNG\r\n\x1a\n' or png[12:16] != b'IHDR':
        raise ValueError('native panel render is not a PNG')
    size = list(struct.unpack('>II', png[16:24]))
    if min(size) <= 0 or receipt.get('render_actual_pixels') != size:
        raise ValueError('native panel render pixel dimensions mismatch')
    # Hash checks consume exactly the bytes parsed above, not a later read.
    if (not absent() or (root / RECEIPT).read_bytes() != receipt_bytes
            or any((root / path).read_bytes() != data for path, data in snapshots.items())):
        raise ValueError('native panel review inputs changed during verification')
    print('PASS: retained panel native DRC/render hashes match current inputs and published image')


if __name__ == '__main__':
    verify()
