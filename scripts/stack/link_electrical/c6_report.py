"""Retained per-link receipt for the DA-03 c6 conductor-order pass (paper only)."""
import json
import hashlib
import copy
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path[:0] = [str(HERE), str(ROOT / 'scripts/stack/geometry')]

import ds62_table as d62
import link_electrical as le
import link_ratios as lr
import links_gate_c6 as c6

OUT = ROOT / 'design/stack/link-electrical/c6-pass.json'
SOURCE = ROOT / 'design/stack/geometry/links/link-gate-c6-source.json'


def order(link):
    return [{'pos': p['pos'], 'kind': p['kind'], **({k: p[k] for k in ('net', 'class', 'site')}
            if p['kind'] == 'signal' else {})} for p in link['positions']]


def verified_source(current, snapshot):
    """Rebuild and hash the complete historical record; its label alone is not evidence."""
    if snapshot.get('source_sha256') != c6.SOURCE_SHA256:
        raise ValueError('c6 snapshot source label differs')
    old_links = {x['id']: x for x in snapshot['links']}
    if set(old_links) != set(current['c6']['changed_links']):
        raise ValueError('c6 snapshot does not cover exactly the changed links')
    original = copy.deepcopy(current)
    original['links'] = [old_links.get(x['id'], x) for x in original['links']]
    original['provenance'] = snapshot['source_provenance']
    original['summary'] = snapshot['source_summary']
    original.pop('c6', None)
    if c6.digest(original) != c6.SOURCE_OBJECT_SHA256:
        raise ValueError('c6 historical record hash mismatch')
    return original


def build():
    old = json.loads(SOURCE.read_text())
    now = json.loads((ROOT / lr.RECORD).read_text())
    if not c6.valid_record(now):
        raise ValueError('c6 source or candidate identity changed')
    source_doc = verified_source(now, old)
    before = {x['id']: x for x in source_doc['links']}
    after = {x['id']: x for x in now['links']}
    inp = le.load_inputs()
    baseline = d62.build(inp)['baseline']
    rows = []
    for ident in now['c6']['changed_links']:
        a, b = before[ident], after[ident]
        old_ratio = lr.link_row(inp, a, baseline)['ratio']
        new_ratio = lr.link_row(inp, b, baseline)['ratio']
        if new_ratio is not None and new_ratio > 1.0:
            raise ValueError(f'{ident}: ratio above 1')
        rows.append({'id': ident, 'order_before': order(a), 'order_after': order(b),
                     'grounds_before': a['grounds'], 'grounds_after': b['grounds'],
                     'unused_before': a['unused'], 'unused_after': b['unused'],
                     'new_riders_in': [x for x in b.get('riders_in', []) if x not in a.get('riders_in', [])],
                     'new_riders_out': [x for x in b.get('riders_out', []) if x not in a.get('riders_out', [])],
                     'ratio_before': old_ratio, 'ratio_after': new_ratio,
                     'rule_errors_after': c6.order_errors(b, a)})
    if any(r['rule_errors_after'] for r in rows):
        raise ValueError('ruled pass has order errors')
    return {'task': 'DA-03 c6 and clarification; ST-02 conductor pass, ST-04 coupling rebind',
            'status': 'paper candidate; source/native/integration review pending; no measured harness or physical qualification',
            'source_sha256': c6.SOURCE_SHA256, 'candidate_sha256': hashlib.sha256((ROOT / lr.RECORD).read_bytes()).hexdigest(),
            'geometry_sha256': c6.geometry_digest(now), 'signal_sha256': c6.signal_digest(now),
            'record_projection_sha256': lr.projection_sha256(lr.load_record()),
            'links_in_use': 61, 'signals': 511, 'rows': rows, 'unsolved_links': []}


def main(argv):
    rendered = json.dumps(le.rnd(build()), indent=1, ensure_ascii=False) + '\n'
    if '--check' in argv:
        print('current' if OUT.read_text() == rendered else 'stale')
        return 0 if OUT.read_text() == rendered else 1
    OUT.write_text(rendered)
    print('wrote', OUT.relative_to(ROOT))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
