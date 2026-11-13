"""Re-study the retained protection applicability across the parts-439 identity packet.

The #317 bridge (protection_study_applicability.py) proved continued applicability
of three retained diagnostic studies at main 05b14986. The parts-439-with-324
packet (58d6b581) then changed two bytes-bound study inputs:
design/standard/electrical-standard.json (part_id identity renames) and
design/spec/cells/_builder.py (new passive identity roles). This study does not
exempt their hashes. It records each change exactly and re-derives, live, that
none reaches anything the retained studies consume:

* the complete electrical-standard delta is the recorded part_id leaf set, and
  every field the three producers read is byte-equal (canonical JSON) to base;
* the precision model's _builder-derived source projection fingerprint is equal
  at base and now (computed in a disposable base worktree and in this tree);
* every other bound input is unchanged, the #317 audit projection is unchanged,
  and each producer's complete calculate() output equals its retained report.

The ngspice model sweep is NOT RUN; nothing here is a hardware or protection claim.

  protection_study_parts439.py           write the study record
  protection_study_parts439.py --check   fail if the record differs from a fresh derivation
"""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.checks import protection_study_applicability as bridge

RECORD = ROOT / 'design/power/protection-study-parts439.json'
TRANSITION_BASE = '05b149862dbacb34af275995cc891bae18f0bb20'
TRANSITION_COMMIT = '58d6b5814186c4f3f6e0f9c18fa1b53267ed4e0c'
STANDARD = 'design/standard/electrical-standard.json'
BUILDER = 'design/spec/cells/_builder.py'
CHANGED = (STANDARD, BUILDER)
# Exact standard fields read by the three producers' calculate()/validate().
CONSUMED_STANDARD = {
    'signals': lambda s: s['signals'],
    'supply_architecture': lambda s: s['supply_architecture'],
    'cells[id=general_output]': lambda s: next(c for c in s['cells'] if c['id'] == 'general_output'),
    'cells[id=precision_output]': lambda s: next(c for c in s['cells'] if c['id'] == 'precision_output'),
}
PROJECTION_PROBE = ('from design.spec.model_contracts import current_precision_contract, fingerprint;'
                    'print(fingerprint(current_precision_contract()))')


def demand(condition, message):
    if not condition:
        raise ValueError(message)


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def canonical(value):
    return sha(json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False).encode())


def at(commit, path):
    return subprocess.check_output(['git', 'show', f'{commit}:{path}'], cwd=ROOT)


def leaf_delta(before, after, pointer=''):
    """Every differing JSON leaf; any structural change is reported as a non-leaf delta."""
    if type(before) is not type(after):
        return [{'pointer': pointer, 'kind': 'type', 'before': before, 'after': after}]
    if isinstance(before, dict):
        if set(before) != set(after):
            return [{'pointer': pointer, 'kind': 'keys', 'before': sorted(before), 'after': sorted(after)}]
        return [d for k in sorted(before) for d in leaf_delta(before[k], after[k], f'{pointer}/{k}')]
    if isinstance(before, list):
        if len(before) != len(after):
            return [{'pointer': pointer, 'kind': 'length', 'before': len(before), 'after': len(after)}]
        return [d for i, (x, y) in enumerate(zip(before, after)) for d in leaf_delta(x, y, f'{pointer}/{i}')]
    return [] if before == after else [{'pointer': pointer, 'kind': 'leaf', 'before': before, 'after': after}]


def standard_delta(before, after):
    rows = []
    for row in leaf_delta(before, after):
        parts = row['pointer'].split('/')
        demand(row['kind'] == 'leaf' and len(parts) == 6 and parts[1] == 'cells' and parts[3] == 'parts'
               and parts[5] == 'part_id', 'Electrical standard changed beyond a cell part_id: ' + row['pointer'])
        cell = before['cells'][int(parts[2])]
        part = cell['parts'][int(parts[4])]
        demand(after['cells'][int(parts[2])]['id'] == cell['id'], 'Cell identity moved: ' + row['pointer'])
        rows.append({'pointer': row['pointer'], 'cell': cell['id'], 'ref': part['ref'],
                     'before': row['before'], 'after': row['after']})
    return rows


def model_projection(checkout):
    return subprocess.check_output([sys.executable, '-B', '-c', PROJECTION_PROBE], cwd=checkout,
                                   text=True).strip()


def base_model_projection():
    with tempfile.TemporaryDirectory(prefix='osc-protection-study-base-') as temp:
        checkout = Path(temp) / 'base'
        subprocess.run(['git', 'worktree', 'add', '--quiet', '--detach', str(checkout), TRANSITION_BASE],
                       cwd=ROOT, check=True)
        try:
            return model_projection(checkout)
        finally:
            subprocess.run(['git', 'worktree', 'remove', '--force', str(checkout)], cwd=ROOT, check=True)


def derive(current_bytes=lambda p: (ROOT / p).read_bytes(), base_bytes=lambda p: at(TRANSITION_BASE, p),
           base_projection=base_model_projection, current_projection=lambda: model_projection(ROOT)):
    subprocess.run(['git', 'merge-base', '--is-ancestor', TRANSITION_COMMIT, 'HEAD'], cwd=ROOT, check=True)
    demand(subprocess.check_output(['git', 'rev-parse', TRANSITION_COMMIT + '^1'], cwd=ROOT,
                                   text=True).strip() == TRANSITION_BASE,
           'Transition base is not the first parent of the packet commit')
    # Obligation projection: unchanged from the #317 study base, exactly as the bridge requires.
    bridge.projection_matches(json.loads(bridge.historical(bridge.AUDIT)), json.loads(current_bytes(bridge.AUDIT)))
    reports, inputs = {}, {}
    for path in bridge.REPORTS:
        raw = current_bytes(path)
        demand(raw == bridge.historical(path), f'Retained report was rewritten: {path}')
        report = json.loads(raw)
        reports[path] = report
        for name, expected in report['input_sha256'].items():
            demand(sha(bridge.historical(name)) == expected, f'Historical input binding mismatch: {name}')
            inputs.setdefault(name, []).append(path)
    changed = {}
    for name, bound_by in sorted(inputs.items()):
        if name == bridge.AUDIT:
            continue
        current, base, study = sha(current_bytes(name)), sha(base_bytes(name)), sha(bridge.historical(name))
        demand(base == study, f'Input changed before the transition base; outside this study: {name}')
        if current == study:
            continue
        demand(name in CHANGED, f'Unreviewed bound input change; a new study is required: {name}')
        changed[name] = {'study_sha256': study, 'current_sha256': current, 'bound_by': bound_by}
    demand(set(changed) == set(CHANGED), 'Recorded transition inputs differ from the observed change set')

    before, after = json.loads(base_bytes(STANDARD)), json.loads(current_bytes(STANDARD))
    consumed = {}
    for key, select in CONSUMED_STANDARD.items():
        demand(canonical(select(before)) == canonical(select(after)), f'Consumed standard field changed: {key}')
        consumed[key] = canonical(select(after))
    changed[STANDARD].update(delta=standard_delta(before, after), consumed_projection_sha256=consumed,
                             consumed_by='calculate()/validate() of fast_disconnect_candidate, '
                                         'integrated_output_candidate and precision_output_cell')
    base_fp, current_fp = base_projection(), current_projection()
    demand(base_fp == current_fp, 'Precision model source projection changed; re-run the model study')
    changed[BUILDER].update(
        unified_diff_sha256=sha(subprocess.check_output(
            ['git', 'diff', '--no-color', '-U0', TRANSITION_BASE, TRANSITION_COMMIT, '--', BUILDER], cwd=ROOT)),
        consumed_by='precision-output-cell-model.json binds it by hash; the model consumes it only through '
                    'design.spec.model_contracts.current_precision_contract()',
        precision_model_source_projection_sha256={'transition_base': base_fp, 'current': current_fp})
    demand(sha(current_bytes(BUILDER)) == sha(at(TRANSITION_COMMIT, BUILDER)),
           f'{BUILDER} changed after the packet; a new study is required')

    from scripts.checks import fast_disconnect_candidate as fast
    from scripts.checks import integrated_output_candidate as integrated
    from scripts.checks import precision_output_cell as precision
    arithmetic = {}
    for producer in (fast, integrated, precision):
        calculated = producer.calculate(json.loads(producer.SPEC.read_text()))
        report_path = str(producer.REPORT.relative_to(ROOT))
        expected = {k: v for k, v in reports[report_path].items() if k != 'input_sha256'}
        demand(calculated == expected, f'Current arithmetic differs: {producer.__name__}')
        arithmetic[report_path] = {'calculated_sha256': canonical(calculated), 'equals_retained': True}
    population = json.loads(current_bytes(bridge.AUDIT))['current_switch_population']
    counts = {g['mpn']: g['count'] for g in population['groups']}
    demand(counts == {'TMUX7412FRRPR': 98, 'TMUX6112PWR': 12}, 'Adopted switch population changed')
    return {
        'schema': 'osc-protection-study-transition/1',
        'study': 'Protection study applicability across the parts-439-with-324 identity packet (#21, #324)',
        'historical_study_base': bridge.BASE,
        'transition_base': TRANSITION_BASE,
        'transition_commit': TRANSITION_COMMIT,
        'supersedes_current_check': 'scripts/checks/test_protection_study_applicability.py (frozen at transition_base)',
        'retained_reports': list(bridge.REPORTS),
        'obligation_projection': {'audit': bridge.AUDIT, 'fields': list(bridge.PROJECTION),
                                  'equals_historical_study_base': True},
        'changed_bound_inputs': changed,
        'unchanged_bound_inputs': sorted(n for n in inputs if n not in changed and n != bridge.AUDIT),
        'arithmetic': arithmetic,
        'current_switch_counts': counts,
        'not_run': ['precision-output-cell-model.json ngspice sweep (native oracle); applicability rests on the '
                    'equal source projection and unchanged deck inputs, not a re-run',
                    'physical protection qualification'],
        'status': 'PASS: identity-only input changes reach no consumed field; diagnostic arithmetic and '
                  'obligations unchanged; historical ADG savings are not current',
        'hardware_protection': 'OPEN; physical qualification NOT RUN',
    }


def body(record):
    return json.dumps(record, indent=1, ensure_ascii=False) + '\n'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--check', action='store_true')
    text = body(derive())
    if parser.parse_args(argv).check:
        demand(RECORD.is_file() and RECORD.read_text() == text,
               f'{RECORD.relative_to(ROOT)} is stale; run python3 scripts/checks/protection_study_parts439.py')
        print('PASS: ' + str(RECORD.relative_to(ROOT)) + ' equals a fresh derivation')
    else:
        RECORD.write_text(text)
        print('Wrote ' + str(RECORD.relative_to(ROOT)))


if __name__ == '__main__':
    main()
