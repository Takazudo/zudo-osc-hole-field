#!/usr/bin/env python3
"""MC04-S10 Revision 1 (DS-148): the c6 rebind check for the four S10 slot holds.

Replays the link gate (links_gate.generate) with the c6 pins of the base commit and records, against that commit's
gate record:
- the pre-c6 geometry, signal and positions digests (the signal and positions pins must not change);
- the c6 output digest under the new geometry pin;
- for each of c6's eight links, whether its output positions and riders equal the base record;
- every link whose slot or geometry changed, and the rider changes (host and distance).

Writes circuit/orchestration/campaigns/osc-stack-20261114/mc04-s10-c6-rebind-check-20261122.json; --check verifies it.
The rebind itself is the source edit of the pins in links_gate_c6.py, which this record documents."""
from __future__ import annotations
import argparse
import copy
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'scripts/stack/geometry'))
import links_gate as lg  # noqa: E402
import links_gate_c6 as c6  # noqa: E402

BASE = '8243acdf'
OUT = ROOT / 'circuit/orchestration/campaigns/osc-stack-20261114/mc04-s10-c6-rebind-check-20261122.json'
OLD = {'geometry': '466a9e4ccb00339db0e1ec87ab3d3b8e398a482b232d05816327b93273887aed',
       'signal': '70335b6d45781946dddabeb3fbdb86dcf0924c2dd79355dd4e7f08443f5c584b',
       'positions': 'f1d03b6ab6aadfc2530d6e22b0596598d51a468bdcaff978152f5ec85acd94a6'}
OLD_OUTPUT = '44cff1e4c0b377d435c46cbb7533bb58041f733d01679287f86593bdb82b2dbb'
HELD = ('P-K-P-L13.01.01.01', 'P-K-P-L13.01.01.02', 'P-K-P-L13.01.02.01', 'P-K-P-L15.02.01.01')


def replay():
    """The gate document with c6 applied under the pre-c6 geometry of this replay (signal and positions pins kept)."""
    cap = {}
    real, valid = c6.apply, c6.valid_record
    pins = (c6.SOURCE_GEOMETRY_SHA256, c6.OUTPUT_LINKS_SHA256)

    def apply(doc, inp=None):
        cap['pre'] = copy.deepcopy(doc)
        c6.SOURCE_GEOMETRY_SHA256 = c6.geometry_digest(doc)
        c6.valid_record = lambda d: True
        try:
            return real(doc, inp)
        finally:
            c6.valid_record = valid
    c6.apply = apply
    try:
        doc = lg.generate()
    finally:
        c6.apply = real
        c6.SOURCE_GEOMETRY_SHA256, c6.OUTPUT_LINKS_SHA256 = pins
    return cap['pre'], doc


def riders(link):
    return {k: sorted(((r['net'], r['site'], r.get('host') or r.get('from')), r['distance_mm']) for r in link.get(k, []))
            for k in ('riders_in', 'riders_out')}


def build():
    base = json.loads(subprocess.run(['git', '-C', str(ROOT), 'show', f'{BASE}:design/stack/geometry/links/link-gate.json'],
                                     capture_output=True, check=True, text=True).stdout)
    pre, doc = replay()
    new = {'geometry': c6.geometry_digest(pre), 'signal': c6.signal_digest(pre),
           'positions': c6.digest([x['positions'] for x in pre['links']])}
    a = {x['id']: x for x in base['links']}
    b = {x['id']: x for x in doc['links']}
    c6_links = {}
    for name in doc['c6']['changed_links']:
        c6_links[name] = {'output_positions_equal_previous': a[name]['positions'] == b[name]['positions'],
                          'riders_equal_previous': riders(a[name]) == riders(b[name])}
    changed = {}
    for k in sorted(a):
        fields = sorted(f for f in set(a[k]) | set(b[k]) if f not in ('riders_in', 'riders_out') and a[k].get(f) != b[k].get(f))
        if fields:
            changed[k] = {'fields': fields, 'held': k in HELD, 'gone': bool(a[k].get('gone')),
                          'slot_centre': [a[k].get('slot_centre'), b[k].get('slot_centre')],
                          'direction': [a[k].get('direction'), b[k].get('direction')]}
    rider_changes = {}
    for k in sorted(a):
        ra, rb = riders(a[k]), riders(b[k])
        if ra != rb:
            keys_a = {kind: [x[0] for x in v] for kind, v in ra.items()}
            keys_b = {kind: [x[0] for x in v] for kind, v in rb.items()}
            rider_changes[k] = {'same_nets_sites_and_hosts': keys_a == keys_b,
                                'distances_mm': {kind: [[list(x[0]), x[1], y[1]] for x, y in zip(ra[kind], rb[kind]) if x != y]
                                                 for kind in ra}}
    hosts_ok = all(v['same_nets_sites_and_hosts'] for v in rider_changes.values())
    via_holds = all(any(h in json.dumps(v['distances_mm']) for h in HELD) or k in HELD for k, v in rider_changes.items())
    return {'record': 'MC04-S10 Revision 1 (DS-148): c6 rebind after the four S10 slot holds',
            'historical_source': {'source_sha256': c6.SOURCE_SHA256, 'source_object_sha256': c6.SOURCE_OBJECT_SHA256},
            'base_commit': BASE, 'old_source_pins': OLD, 'new_source_pins': new,
            'signal_and_positions_unchanged': new['signal'] == OLD['signal'] and new['positions'] == OLD['positions'],
            'old_output_links_sha256': OLD_OUTPUT, 'new_output_links_sha256': c6.digest(doc['links']),
            'c6_links': c6_links, 'links_changed_against_previous_gate': changed,
            'unheld_live_links_unchanged': all(v['held'] or v['gone'] for v in changed.values()),
            'rider_changes': rider_changes, 'rider_hosts_identical': hosts_ok, 'rider_distance_changes_only_through_holds': via_holds,
            'ways_out_equal': base['ways_out'] == doc['ways_out'],
            'consolidation_dissolved_equal': base['consolidation'].get('dissolved') == doc['consolidation'].get('dissolved'),
            'consolidation_fields_changed': sorted(k for k in set(base['consolidation']) | set(doc['consolidation'])
                                                   if base['consolidation'].get(k) != doc['consolidation'].get(k)),
            'hold_errors': lg.hold_errors(lg.load_inputs()['gopts'], doc['links'])}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    text = json.dumps(build(), indent=1) + '\n'
    if a.check:
        if not OUT.exists() or OUT.read_text() != text:
            raise SystemExit('%s is stale' % OUT.name)
        print(OUT.name, 'current')
    else:
        OUT.write_text(text)
    d = json.loads(text)
    print({k: d[k] for k in ('new_source_pins', 'new_output_links_sha256', 'signal_and_positions_unchanged', 'unheld_live_links_unchanged',
                             'rider_hosts_identical', 'rider_distance_changes_only_through_holds', 'ways_out_equal',
                             'consolidation_dissolved_equal', 'consolidation_fields_changed', 'hold_errors')})
    print({k: v for k, v in d['c6_links'].items()})


if __name__ == '__main__':
    main()
