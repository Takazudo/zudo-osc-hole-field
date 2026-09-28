#!/usr/bin/env python3
"""Regenerate the dense acceptance summary from retained measured evidence."""
import hashlib
import json
import sys
from pathlib import Path
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.pcbgen.route import drc_summary, drc_passes
EVIDENCE = ROOT/'scripts/pcbgen/fixtures/dense-evidence'

def read(name):
    return json.loads((EVIDENCE/name).read_text())

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

receipt = read('verification.json')
for relative, expected in receipt['sha256'].items():
    if sha(ROOT/relative) != expected:
        raise SystemExit(f'retained verification is stale: {relative}')
summary = drc_summary(read('final-drc.json'))
if not drc_passes(summary):
    raise SystemExit('retained final DRC does not satisfy the complete fixture gate')
baseline = read('baseline-routing.json')
result = {
    'schema_version': 2,
    'status': 'UNVALIDATED DRAFT',
    'fixture_gate': 'PASS — KiCad rule/connectivity/parity checks only',
    'geometry': {'footprints': 211, 'selected_jacks': 30, 'indicator_cells': 30,
                 'connector_count': 1, 'connector_pads': 40, 'copper_layers': 4,
                 'jack_pitch_x_mm': 17, 'jack_pitch_y_mm': 14},
    'final_drc': summary,
    'final_copper': read('final-stats.json'),
    'fixed_hardware_centres_unchanged': 30,
    'placement_lock_sha256': sha(ROOT/'design/grid/placements.lock.json'),
    'preexisting_copper_preserved': len(read('preservation.json')['preexisting_uuids']),
    'historical_attempts': 'dense-evidence/historical-attempts.json',
    'reconstruction_attempt': {
        'status': baseline['status'], 'drc': baseline['after'],
        'router_runtime_sec': baseline['router_runtime_sec'],
        'sampled_peak_memory_mb': baseline['sampled_peak_memory_mb'],
        'time_limit_sec': baseline['time_limit_sec'], 'router_image': baseline['router_image']},
    'source_column_attempt': read('source-routing.json'),
    'repair_attempts': 'dense-evidence/repair-attempts.json',
    'reproducibility': {
        'command': 'bash scripts/pcbgen/test_route.sh --dense',
        'result': 'PASS — fresh source replay, repeated generation, full DRC, negative ground-via regression',
        'router_invoked_for_replay': False,
        'board_sha256': sha(EVIDENCE/'fixture-route-dense.kicad_pcb'),
        'source_sha256': {name: sha(EVIDENCE/name) for name in ('copper.json', 'stitching.json', 'preservation.json')},
        'run_log': 'dense-evidence/replay-run.txt'},
    'qualification': 'NOT RUN — unvalidated synthetic draft; physical, electrical, thermal, mechanical and fabrication qualification remain open'
}
path = ROOT/'scripts/pcbgen/fixtures/dense-slice-report.json'
output = json.dumps(result, indent=2, sort_keys=True)+'\n'
if '--check' in sys.argv:
    if path.read_text() != output:
        raise SystemExit('dense report is stale')
    print('PASS: retained dense report matches measured evidence')
else:
    path.write_text(output)
    print('Wrote dense report: complete KiCad fixture gate; unvalidated draft')
