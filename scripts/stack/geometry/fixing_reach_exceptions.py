#!/usr/bin/env python3
"""MC04-S7 Revision 11: the pinned fixing_reach misses of check.py.

Writes design/stack/geometry/fixing-reach-exceptions.json:
- the 108 pairs that missed the declared-fixing reach before stage 7 (the check report of the source commit);
- the four stage 7 pairs ruled interim-GH reach exceptions (option (c) of the Revision 10 stop), each with its worst
  distance and nearest declared fixing from the committed check report;
- option (b), declaring the stack sleeves as fixings, recorded as a Gate A candidate and NOT applied.
The reach limits, the fixing list and the declared flags are unchanged. test_fixing_reach_exceptions.py fails when
check.py's declared misses are any other set. --check verifies the record."""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / 'design/stack/geometry/fixing-reach-exceptions.json'
REPORT = 'design/stack/geometry/check-report.json'
BASELINE_COMMIT = '22da400e~1'  # HEAD before the stage 7 stack candidate regeneration
RULED = ('JL-K-26', 'JL-K-27', 'JR-K-28', 'JR-K-29')
SLEEVES = 'design/stack/fixings/ruled-list.json'


def git_bytes(rev, path):
    return subprocess.run(['git', '-C', str(ROOT), 'show', f'{rev}:{path}'], capture_output=True, check=True).stdout


def declared(report):
    return report['checks']['fixing_reach']['detail']['runs']['declared']


def build():
    raw = git_bytes(BASELINE_COMMIT, REPORT)
    commit = subprocess.run(['git', '-C', str(ROOT), 'rev-parse', '--short=8', BASELINE_COMMIT], capture_output=True,
                            check=True, text=True).stdout.strip()
    base = sorted(m['pair'] for m in declared(json.loads(raw))['missed_pairs'])
    cur = {m['pair']: m for m in declared(json.loads((ROOT / REPORT).read_text()))['missed_pairs']}
    detail = json.loads((ROOT / REPORT).read_text())['checks']['fixing_reach']['detail']
    rows = []
    for pid in RULED:
        m = cur[pid]
        rows.append({'pair': pid, 'xy': m['xy'], 'worst_mm': m['worst_mm'], 'K_side_nearest': m['K_side_nearest'],
                     'front_side_nearest': m['front_side_nearest'],
                     'band': 'between reach and exception reach' if m['worst_mm'] <= detail['exception_reach_mm']
                     else 'beyond the exception reach'})
    slv = {s['id']: s for s in json.loads((ROOT / SLEEVES).read_text())['sleeves']}['SLV-U2']
    option_b = {'status': 'GATE A CANDIDATE, NOT APPLIED (MC04-S7 Revision 11)',
                'proposal': 'declare the ruled stack sleeves (%s) as fixings for the reach check' % SLEEVES,
                'figure': {'sleeve': 'SLV-U2', 'xy': slv['xy'],
                           'distances_mm': {pid: round(math.hypot(cur[pid]['xy'][0] - slv['xy'][0],
                                                                  cur[pid]['xy'][1] - slv['xy'][1]), 3)
                                            for pid in ('JR-K-28', 'JR-K-29')}},
                'note': 'JR-K-29 would pass the 40 mm reach; JR-K-28 would stay beyond the 50 mm exception reach'}
    return {'schema_version': 1,
            'status': 'RULED (MC04-S7 Revision 11, option (c)): interim-GH reach exceptions; GH headers are the interim '
                      'interconnect that Gate A replaces',
            'generator': 'scripts/stack/geometry/fixing_reach_exceptions.py',
            'limits': {'reach_mm': detail['reach_mm'], 'exception_reach_mm': detail['exception_reach_mm'],
                       'declared_fixings': declared(json.loads((ROOT / REPORT).read_text()))['fixings']},
            'baseline': {'commit': commit, 'path': REPORT, 'sha256': hashlib.sha256(raw).hexdigest(),
                         'misses': len(base), 'pairs': base},
            'interim_gh_exceptions': rows,
            'passes': {'JR-K-30': 'within the 40 mm reach of JR-SUP-1'},
            'option_b_gate_a_candidate': option_b}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    text = json.dumps(build(), indent=1) + '\n'
    if a.check:
        if not OUT.exists() or OUT.read_text() != text:
            raise SystemExit('fixing reach exception record drift')
    else:
        OUT.write_text(text)
    d = json.loads(text)
    print('baseline misses', d['baseline']['misses'], 'ruled', [r['pair'] for r in d['interim_gh_exceptions']])


if __name__ == '__main__':
    main()
