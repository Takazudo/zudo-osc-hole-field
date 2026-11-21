"""MC04-S7 Part A0 case (b): the unchanged link gate with JL-K-JL-L02 held at its retained slot (121.5, 80) +x.

Every other rule of the gate is unchanged: search() and candidate() are wrapped only for the JL-L02 search (front JL,
centre (133.5, 80)), where every slot but the retained one is refused. The DA-03 c6 pass is skipped because its pin
refuses any changed pre-c6 record; c6 reorders P-K positions only and freezes placement and displaced footprints, so
the displacement record (the unresolved list) does not depend on it. Writes a summary; the committed gate is not
touched. Paper only."""
import argparse
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'scripts/stack/geometry'))
import links_gate as lg  # noqa: E402
import links_gate_c6 as c6  # noqa: E402
from links import DIR_NAMES  # noqa: E402

LINK, CENTRE, SLOT, DIRECTION = 'JL-K-JL-L02', (133.5, 80.0), (121.5, 80.0), '+x'


def held(fn_search, fn_candidate, flag):
    def search(ctx, placed, front, centre, *a, **k):
        prev = flag['on']
        flag['on'] = front == 'JL' and abs(centre[0] - CENTRE[0]) < 1e-6 and abs(centre[1] - CENTRE[1]) < 1e-6
        try:
            return fn_search(ctx, placed, front, centre, *a, **k)
        finally:
            flag['on'] = prev

    def candidate(ctx, placed, front, size, own, sx, sy, d, *a, **k):
        if flag['on']:
            flag['calls'] += 1
            if (sx, sy) != SLOT or DIR_NAMES[d] != DIRECTION:
                return ('held at the retained slot', None), None
            flag['kept'] += 1
        return fn_candidate(ctx, placed, front, size, own, sx, sy, d, *a, **k)
    return search, candidate


def unresolved(doc):
    return sorted(r['board'] + ':' + r['ref'] for r in doc['replacement']['footprints'] if r['new'] is None)


def run():
    flag = {'on': False, 'calls': 0, 'kept': 0}
    saved = lg.search, lg.candidate, c6.apply
    lg.search, lg.candidate = held(lg.search, lg.candidate, flag)
    c6.apply = lambda doc, inp=None: doc
    try:
        doc = lg.generate()
    finally:
        lg.search, lg.candidate, c6.apply = saved
    cur = json.loads(lg.LINK_GATE.read_text())
    if doc['provenance']['input_sha256'] != cur['provenance']['input_sha256']:
        raise ValueError('the committed gate is stale against its inputs')
    rec = next(x for x in doc['links'] if x['id'] == LINK)
    if rec['slot_centre'] != list(SLOT) or rec['direction'] != DIRECTION:
        raise ValueError('JL-L02 not at the retained slot')
    cur_rec = next(x for x in cur['links'] if x['id'] == LINK)
    a, b = unresolved(cur), unresolved(doc)
    return {'status': 'MC04_S7_A0_CASE_B_RETAINED_JL_L02_SLOT',
            'gate_sha256': hashlib.sha256(lg.LINK_GATE.read_bytes()).hexdigest(),
            'inputs_sha256': doc['provenance']['input_sha256'],
            'held_link': {'id': LINK, 'slot_centre': rec['slot_centre'], 'direction': rec['direction'],
                          'cost': rec['cost'], 'displaced': rec['displaced'],
                          'retained_slot_evaluations': flag['kept'], 'refused_evaluations': flag['calls'] - flag['kept']},
            'current_link': {'slot_centre': cur_rec['slot_centre'], 'direction': cur_rec['direction'],
                             'cost': cur_rec['cost'], 'displaced': cur_rec['displaced']},
            'other_links_with_a_different_slot': sorted(x['id'] for x, y in zip(cur['links'], doc['links'])
                                                        if x['id'] != LINK and (x.get('slot_centre'), x.get('direction'))
                                                        != (y.get('slot_centre'), y.get('direction'))),
            'placed_links': sum(1 for x in doc['links'] if x.get('placed') and not x.get('gone')),
            'unresolved_current': a, 'unresolved_held': b,
            'only_held': sorted(set(b) - set(a)), 'only_current': sorted(set(a) - set(b)),
            'scope': 'Gate rule unchanged except the JL-L02 slot; c6 position pass skipped (does not move links or '
                     'footprints); summary only; no canonical write.'}


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
