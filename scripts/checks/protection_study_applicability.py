"""Prove the limited current applicability of three retained protection studies.

Historical report/model bytes and tests are replayed unchanged by frozen_studies.
This live bridge compares the exact consumed audit projection, every other bound
input and all current arithmetic outputs. It grants no current population saving
or hardware claim to the historical 110-ADG sensitivity.
"""
from pathlib import Path
from functools import lru_cache
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[2]
BASE = '433c88b27b2e49284fe1a717b47ba4226c829dd3'
AUDIT = 'design/power/protection58-audit.json'
PROJECTION = ('output_count', 'precision_count', 'outputs', 'reference_receivers')
REPORTS = ('design/power/fast-disconnect-candidate-report.json',
           'design/power/integrated-output-candidate-report.json',
           'design/power/precision-output-cell-report.json',
           'design/power/precision-output-cell-model.json')


def demand(condition, message):
    if not condition:
        raise ValueError(message)


@lru_cache(maxsize=None)
def historical(path):
    return subprocess.check_output(['git', 'show', f'{BASE}:{path}'], cwd=ROOT)


def projection_matches(before, current):
    for key in PROJECTION:
        demand(before[key] == current[key], f'Protection obligation changed: {key}')


def verify_bound_inputs(report, current_bytes, historical_bytes):
    """Only the whole-audit hash changes; its consumed projection is checked separately."""
    for path, expected in report['input_sha256'].items():
        demand(hashlib.sha256(historical_bytes(path)).hexdigest() == expected,
               f'Historical input binding mismatch: {path}')
        if path != AUDIT:
            demand(hashlib.sha256(current_bytes(path)).hexdigest() == expected,
                   f'Current study input changed; reassess applicability: {path}')


def verify():
    current_bytes = lambda p: (ROOT / p).read_bytes()
    current = json.loads(current_bytes(AUDIT))
    projection_matches(json.loads(historical(AUDIT)), current)
    reports = {}
    for path in REPORTS:
        raw = current_bytes(path)
        demand(raw == historical(path), f'Retained report was rewritten: {path}')
        report = json.loads(raw)
        verify_bound_inputs(report, current_bytes, historical)
        reports[path] = report
    # Recompute every arithmetic field against current input bytes. No oracle,
    # report rewrite, hash substitution or omitted numeric assertion is involved.
    from scripts.checks import fast_disconnect_candidate as fast
    from scripts.checks import integrated_output_candidate as integrated
    from scripts.checks import precision_output_cell as precision
    for producer in (fast, integrated, precision):
        spec = json.loads(producer.SPEC.read_text())
        calculated = producer.calculate(spec)
        retained = reports[str(producer.REPORT.relative_to(ROOT))]
        expected = {k: v for k, v in retained.items() if k != 'input_sha256'}
        demand(calculated == expected, f'Current arithmetic differs: {producer.__name__}')
    population = current['current_switch_population']
    counts = {g['mpn']: g['count'] for g in population['groups']}
    demand(counts == {'TMUX7412FRRPR': 98, 'TMUX6112PWR': 12},
           'Adopted switch population changed; reassess historical sensitivity applicability')
    demand(population['guaranteed_project_total_mA'] is None
           and all(g['guaranteed_project_current_mA'] is None for g in population['groups']),
           'Unsupported project current guarantee')
    return {'historical_base': BASE, 'projection_fields': list(PROJECTION),
            'retained_reports': list(REPORTS), 'current_switch_counts': counts,
            'status': 'PASS: unchanged diagnostic arithmetic and obligations only; historical ADG savings are not current',
            'hardware_protection': 'OPEN; physical qualification NOT RUN'}


if __name__ == '__main__':
    print(json.dumps(verify(), indent=2))
