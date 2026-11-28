"""Review corrections of 2026-11-28 (reviews/mc04-s16-result-review-20261128.md, findings 1, 4 and 5).

Read-only over the recorded run: reads the cache and the checkpoints, writes only
checkpoints/review-corrections-20261128.json. `replan.py` does not import this file; nothing here re-runs a
replay, a judgement or an oracle. ROWS-LEVEL EVIDENCE ONLY, STUDY, NOT ADOPTED, UNVALIDATED DRAFT."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
BULK = ROOT / '.circuit-cache' / 'mc04-s16'
CK = HERE / 'checkpoints'
OUT = CK / 'review-corrections-20261128.json'
POOL_SPOTS = 20
PER_STRUCTURE_REPLAYS = 12
JUDGED = [1, 0, 33, 36, 16]

REVIEWER_A8_A9 = {
    'source': 'reviews/mc04-s16-result-review-20261128.md, table "Stage 3 failures are real"; reviewer '
              'measurements, not recomputed here',
    'A8_U8413': 'U8413 row unchanged; its decoupler C8443 gets a new row. E1 block holding P-K-E3: C8443 on face F, '
                '1.493 mm from the IC on face B. E1 block holding P-K-E2: C8443 stays on face B at 16.672 mm, '
                'against 5.690 mm at the base. All 5 judged scenes.',
    'A9_R7213': 'R7213 gets a new row, 49.858 mm (one block) or 50.567 mm (two blocks) from U7204, against '
                '49.159 mm at the base. All 5 judged scenes.',
    'all_24_without_S8': 'Reviewer evidence, not a result of the recorded run: all 24 passing scenes, judged with '
                         'judge_replan and no S8 search, fail A8 at U8413 (12 face F, 12 at 16.672 mm) and A9 at '
                         'R7213 (8 at 49.858 mm, 16 at 50.567 mm).',
}


def j(p):
    return json.loads(Path(p).read_text())


def main():
    if not BULK.exists():
        raise SystemExit('the cache %s is absent; this extraction needs it' % BULK)
    blocks = {}
    for f in sorted((BULK / 'stage1').glob('*.json')):
        surv = j(f).get('survivors', [])
        if surv:
            blocks[f.stem] = {'survivors': len(surv), 'spots': len({tuple(e['spot']) for e in surv})}
    binding = sorted(b for b, v in blocks.items() if v['spots'] > POOL_SPOTS)

    summ = j(CK / 'stage2b' / 'summary.json')
    rows = summ['structures']
    cut = [r['index'] for r in rows
           if j(BULK / 'stage2b' / ('%04d.json' % r['index'])).get('discarded_replays_after_global_cap')]
    per_cap = [r['index'] for r in rows if not r['passed'] and not r['exhausted']
               and r['replays'] >= PER_STRUCTURE_REPLAYS]
    exhausted = [r['index'] for r in rows if r['exhausted']]
    passed = [r['index'] for r in rows if r['passed']]
    short = [r['index'] for r in rows if not r['passed'] and not r['exhausted']
             and r['replays'] < PER_STRUCTURE_REPLAYS and r['index'] not in cut]

    plans = {r['id']: r for r in j(BULK / 'stage2a' / 'structures.json')['structures']}

    def scene(i):
        lg = j(BULK / 'stage2b' / ('%04d.json' % i))
        rp = [r for r in lg['replays'] if r['n'] == lg['passed']][0]
        sid = lg['id']
        st = plans[sid]
        bl = rp['blocks']
        return {'stage2b_index': i, 'structure': sid, 'replay': rp['n'], 'vector': rp['vector'],
                'digest': rp['digest'],
                'blocks': [{'block': b['block'], 'slot_centre': b['slot_centre'], 'direction': b['direction'],
                            'dist_mm': round(b['dist'], 4), 'cost': round(b['cost'], 4)} for b in bl],
                'ride_plan': st['plan'], 'rides': st['rides']}

    judged = [dict(scene(i), rank=k + 1) for k, i in enumerate(JUDGED)]
    family = [scene(i) for i in passed]
    e1 = [[b for b in s['blocks'] if 'P-K-E1' in b['block']][0] for s in family]
    second = [b for s in family if len(s['blocks']) == 2 for b in s['blocks'] if 'P-K-E1' not in b['block']]
    e1_unsearched = sum(1 for r in plans.values() if r['live'] and any(b == ['P-K-E1'] for b in r['blocks'])
                        and not any(x['id'] == r['id'] for x in rows))
    e1_alone = blocks.get('S16-B[P-K-E1]')

    out = {
        'status': 'ROWS-LEVEL EVIDENCE ONLY, STUDY, NOT ADOPTED, UNVALIDATED DRAFT',
        'review': 'reviews/mc04-s16-result-review-20261128.md',
        'kept_reading': 'a kept scene is a scene that passes stage 3; none does. The 5 scenes taken to stage 3 are '
                        '"judged", not "kept"',
        'bounds_added': [
            '12 rows-only replays per structure, reached in %d structures' % len(per_cap),
            '; '.join('structure %d cut at %d kept replays by the 1200 cap (%d computed replays discarded; the worker '
                      'reached 12 with no pass)' % (i, [r['replays'] for r in rows if r['index'] == i][0],
                                                    j(BULK / 'stage2b' / ('%04d.json' % i))
                                                    ['discarded_replays_after_global_cap']) for i in cut),
            'one scene judged per passing structure (first pass)',
            'pool: cheapest survivor per spot; the 20-spot limit binds on %d of the %d blocks with survivors'
            % (len(binding), len(blocks)),
        ],
        'stage2b_outcomes': {'searched': len(rows), 'searched_to_a_per_structure_end': len(rows) - len(cut),
                             'per_structure_cap_no_pass': len(per_cap),
                             'cut_by_global_cap': cut, 'exhausted': len(exhausted), 'passed': len(passed),
                             'other_short_no_pass': short},
        'pool': {'limit': POOL_SPOTS, 'blocks_with_survivors': len(blocks), 'binding': binding,
                 'per_block': blocks},
        'judged_scenes': judged,
        'passing_slot_family_from_logs': {
            'passing_structures': len(passed),
            'p_k_e1_block_slots': sorted({(b['slot_centre'][0], b['slot_centre'][1], b['direction']) for b in e1}),
            'second_block_slots': sorted({(b['slot_centre'][0], b['slot_centre'][1], b['direction'])
                                          for b in second}),
            'two_link_scenes': sum(1 for s in family if len(s['blocks']) == 2),
            'S16-B[P-K-E1]': e1_alone,
            'live_structures_with_P-K-E1_unsearched': e1_unsearched,
        },
        'reviewer_A8_A9': REVIEWER_A8_A9,
    }
    OUT.write_text(json.dumps(out, indent=1, ensure_ascii=False) + '\n')
    print(json.dumps({k: out[k] for k in ('bounds_added', 'stage2b_outcomes')}, indent=1))
    print(json.dumps(out['passing_slot_family_from_logs'], indent=1, default=str)[:1500])
    for s in judged:
        print(s['rank'], s['stage2b_index'], s['structure'], s['ride_plan'],
              [(b['block'], b['slot_centre'], b['direction']) for b in s['blocks']])


if __name__ == '__main__':
    sys.exit(main())
