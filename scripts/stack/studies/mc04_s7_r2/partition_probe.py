"""MC04-S7 Revision 2, Part A step 3 probe: what the io-partition checker says when the moved block members are
assigned to the core region (K).

It reads the moved members from a blocks result (every front-to-K block of all_on_K_together) and evaluates
scripts/checks/io_partition60.build twice on the current source: with the source regions, and with those members
assigned to core. It reports the new errors apart from the expected source-versus-assigned region mismatch, the new
forbidden crossings with their reason, and the new allowed crossings. Region derived islands (IO_<REGION>) would be
renamed by a source change; cell-defined islands would not. No source or record is changed."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / 'scripts/checks'))
import io_partition60 as io  # noqa: E402


def run(src):
    blocks = json.loads(src.read_text())
    moved = {}
    for c in blocks['all_on_K_together']:
        if c['from'] != c['to']:
            for b in c['blocks']:
                moved[b['ic']] = b['members']
    refs = {r for v in moved.values() for r in v}
    packages, _, _, _ = io.source_data()
    base = [{'ref': r, 'region': p['regions'][0]} for r, p in sorted(packages.items())]
    unknown = sorted(refs - set(packages))
    if unknown:
        raise ValueError('members not in the source: %s' % unknown)
    moved_asg = [{'ref': r['ref'], 'region': 'core' if r['ref'] in refs else r['region']} for r in base]
    r0, r1 = io.build(assignments=base), io.build(assignments=moved_asg)
    new = sorted(set(r1['errors']) - set(r0['errors']))
    expected = [e for e in new if e.startswith('split/swapped package region')]
    islands = {}
    for e in new:
        if e.startswith('split island '):
            islands[e[len('split island '):].rsplit(': [', 1)[0]] = e
    island_rows = []
    for row in r1['islands']:
        if row['island_id'] in islands:
            label = row['island_id'].split('/', 1)[1]
            island_rows.append({'island': row['island_id'], 'regions': row['regions'],
                                'region_derived': label.startswith('IO_'),
                                'moved_refs': sorted(set(row['refs']) & refs),
                                'staying_refs': sorted(set(row['refs']) - refs)})
    f0 = {x['net'] for x in r0['forbidden_crossings']}
    a0 = {x['net'] for x in r0['allowed_crossings']}
    owner = {m: ic for ic, ms in moved.items() for m in ms}
    forbidden = [{'net': x['net'], 'reason': x['reason'], 'regions': x['regions'],
                  'moved_ics': sorted({owner[m['ref']] for m in x['members'] if m['ref'] in owner})}
                 for x in r1['forbidden_crossings'] if x['net'] not in f0]
    allowed = [{'net': x['net'], 'kind': x['kind'], 'moved_ics': sorted({owner[m['ref']] for m in x['members'] if m['ref'] in owner})}
               for x in r1['allowed_crossings'] if x['net'] not in a0]
    other = [e for e in new if e not in expected and not e.startswith('split island ')]
    return {'status': 'MC04_S7_R2_PARTITION_PROBE', 'source_sha256': hashlib.sha256(src.read_bytes()).hexdigest(),
            'moved_members': moved, 'errors_before': len(r0['errors']),
            'expected_region_mismatch_errors': len(expected), 'split_islands': island_rows,
            'new_forbidden_crossings': forbidden, 'new_allowed_crossings': allowed, 'other_new_errors': other,
            'scope': 'Checker evaluation with an assignment override; no source change.'}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--source', type=Path, required=True)
    ap.add_argument('--output', type=Path)
    a = ap.parse_args()
    text = json.dumps(run(a.source), indent=1) + '\n'
    if a.output:
        with a.output.open('x') as f:
            f.write(text)
    else:
        print(text, end='')
