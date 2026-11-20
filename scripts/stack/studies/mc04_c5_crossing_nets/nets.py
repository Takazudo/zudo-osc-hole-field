"""Task C step 5a: classify the nets that would newly cross JR-K and JL-K if the step 4 blocks moved to K.

Reads the combined step 4 result (pinned by hash), and for each newly crossing net records: the moving block, the
partition members on each side, whether the partition lists it as a local raw-sensitive net or a forbidden crossing,
a name-based kind (protected input, isolation midpoint, indicator LED, other), and the coupling class the retained
classifier (links_gate.classify with the link-electrical class rules) gives it with no partition kind. Paper only:
no allocation, no coupling ratio, no canonical write."""
import argparse
import collections
import hashlib
import json
import re
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'scripts/stack/geometry'))
import links_gate as lg  # noqa: E402

SRC = ROOT / 'scripts/stack/studies/mc04_c4_blocks/result.json'


def kind_of(net):
    if 'PROTECTED' in net:
        return 'protected input node'
    if 'ISO_MID' in net:
        return 'isolation midpoint'
    if re.search(r'LED', net):
        return 'indicator LED drive'
    return 'other'


def run():
    step = json.loads(SRC.read_text())
    part = json.loads((ROOT / 'design/reports/io-partition.json').read_text())
    rules = json.loads((ROOT / 'design/stack/link-electrical/inputs.json').read_text())['classes']['rules']
    sensitive = {x['net'] for x in part['local_raw_sensitive_nets']}
    forbidden = {x['net'] if isinstance(x, dict) else x for x in part['forbidden_crossings']}
    refs = collections.defaultdict(set)
    for u in part['package_units']:
        for n in (u.get('pins') or {}).values():
            if n:
                refs[n].add(u['ref'])
    out = []
    for c in step['all_on_K_together']:
        if c['from'] == c['to']:
            continue
        owner = {m: b['ic'] for b in c['blocks'] for m in b['members']}
        for n in c['nets_newly_crossing']:
            out.append({'net': n, 'from': c['from'], 'blocks': sorted({owner[r] for r in refs[n] if r in owner}),
                        'moving_refs': sorted(r for r in refs[n] if r in owner),
                        'staying_refs': sorted(r for r in refs[n] if r not in owner),
                        'kind': kind_of(n), 'raw_sensitive': n in sensitive, 'forbidden': n in forbidden,
                        'retained_class_without_kind': lg.classify(n, {}, rules)})
    tally = collections.Counter((r['from'], r['kind']) for r in out)
    return {'status': 'TASK_C_STEP_5A_CROSSING_NETS', 'source_sha256': hashlib.sha256(SRC.read_bytes()).hexdigest(),
            'nets': out, 'tally': {'%s %s' % k: v for k, v in sorted(tally.items())},
            'raw_sensitive_or_forbidden': [r['net'] for r in out if r['raw_sensitive'] or r['forbidden']],
            'classes': dict(collections.Counter(r['retained_class_without_kind'] for r in out)),
            'scope': 'Paper classification only; the partition kind of a new crossing must be ruled before allocation.'}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path)
    a = ap.parse_args()
    text = json.dumps(run(), indent=1) + '\n'
    if a.output:
        with a.output.open('x') as f:
            f.write(text)
    else:
        print(text, end='')
