"""Checker of the ruled fixing list (ST-08 a2 part 1): recomputes every rule from the board files, the pinned
inputs and the ruled list, and fails on any finding of its own.

Rules (one finding class each):
  ruled     the active sleeves are exactly the ruled ones (id, site, board, length) and keep the kind
            `sleeve added`; the 18 posts are active; the twelve sites of DS-45 are inactive
  spacing   a sleeve has another active fixing of K within 70 mm (DS-66)
  site      a sleeve on locked panel hardware (panel-side and pad tests), on a fixed hole, on a tab, an adapter, a
            kept selector or a sub toggle, outside a board, or facing another board than ruled
  moves     a movable footprint inside a sleeve keep-out, or a ceramic of 0805 or larger within 5 mm of a fixing,
            without a listed move; a listed free position that does not clear the fixings; a part without a free
            position that no decision row assigns elsewhere
  stale     a pinned file, object, decision row or review section differs from the provenance

  python3 scripts/stack/fixings/fixings_check.py     # exit 1 on any finding
"""
import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fixings as fx  # noqa: E402

EPS = fx.EPS


def check(doc, inp):
    """List of (rule, message)."""
    errs = []
    prm = fx.parameters(inp)
    cand, ruled = inp['cand'], inp['ruled']
    ol = fx.outlines(cand)
    fcls = fx.footprint_classes(inp)
    spacing = fx.val(prm['sleeve_min_spacing_mm'])
    fixings = doc['fixings']
    active = [f for f in fixings if f['active']]
    sleeves = [f for f in active if f['kind'] != 'post']

    # stale
    now = fx.pins(inp['root'])
    for group, items in now.items():
        kept = doc['provenance']['pins'].get(group, {})
        for k in sorted(set(items) | set(kept)):
            if items.get(k) != kept.get(k):
                errs.append(('stale', '%s %s: retained %s, now %s' % (group, k, str(kept.get(k))[:12], str(items.get(k))[:12])))

    # ruled
    want = {s['id']: s for s in ruled['sleeves']}
    got = {f['id']: f for f in sleeves}
    for sid in sorted(set(want) | set(got)):
        s, f = want.get(sid), got.get(sid)
        if s is None or f is None:
            errs.append(('ruled', '%s: %s' % (sid, 'not ruled but active' if s is None else 'ruled but not active')))
            continue
        if f['kind'] != 'sleeve added' or [float(v) for v in s['xy']] != f['xy'] or s['front_board'] != f['front_board'] \
                or s['length_class'] != f['length_class']:
            errs.append(('ruled', '%s: kind, site, board or length differs from the ruled list' % sid))
    if sum(1 for f in active if f['kind'] == 'post') != len(inp['joints']['joints']):
        errs.append(('ruled', 'not every post is active'))
    for f in cand['fixings']:
        if f['kind'] == 'kept support' and any(x['id'] == f['id'] and x['active'] for x in fixings):
            errs.append(('ruled', '%s of DS-45 is active' % f['id']))

    # spacing: every sleeve against every other active fixing
    for s in sleeves:
        for o in active:
            if o['id'] != s['id'] and math.dist(s['xy'], o['xy']) < spacing - EPS:
                errs.append(('spacing', '%s is %.3f mm from %s' % (s['id'], math.dist(s['xy'], o['xy']), o['id'])))

    # site
    for s in sleeves:
        front = fx.front_board_at(s['xy'], ol)
        if front != s['front_board']:
            errs.append(('site', '%s: facing board %s, listed %s' % (s['id'], front, s['front_board'])))
            continue
        for why in fx.obstacle_reasons(s['xy'], front, ol, cand, prm):
            errs.append(('site', '%s: %s' % (s['id'], why)))
        for b in fx.pierced(s['xy'], front, ol):
            for h in fx.keepout_hits(s['xy'], b, fcls, prm):
                if h['in_keepout'] and h['class'] != 'movable':
                    errs.append(('site', '%s: %s %s on %s' % (s['id'], h['class'], h['ref'], b)))

    # moves
    decided = {(s['id'], r['board'], r['ref']) for s in ruled['sleeves'] for r in s.get('replacement_search', [])}
    free = fx.FreeSearch(fcls, ol, prm)
    for f in active:
        listed = {(m['board'], m['ref']): m for m in f.get('part_moves', [])}
        for b in f['boards']:
            for h in fx.keepout_hits(f['xy'], b, fcls, prm):
                if h['class'] != 'movable':
                    continue
                needs = h['ceramic_0805_or_larger_within_5mm'] or (f['kind'] != 'post' and h['in_keepout'])
                if needs and (b, h['ref']) not in listed:
                    errs.append(('moves', '%s: %s on %s has no listed move' % (f['id'], h['ref'], b)))
        for (b, ref), m in sorted(listed.items()):
            pos = m.get('nearest_free_origin')
            if pos is None:
                if (f['id'], b, ref) not in decided:
                    errs.append(('moves', '%s: %s on %s has no free position and no decision assigns it' % (f['id'], ref, b)))
                continue
            fp = next(x for x, _ in fcls[b] if x['ref'] == ref)
            nb = free.moved_box(fp, pos)
            for o in active:
                if b in o['boards'] and fx.box_dist(nb, o['xy']) < free.radius(fp, o['keepout_radius_mm'][b]) - EPS:
                    errs.append(('moves', '%s: the free position of %s on %s lies in the keep-out of %s' % (f['id'], ref, b, o['id'])))
    return errs


def main():
    doc = json.loads(fx.SITES_JSON.read_text())
    errs = check(doc, fx.load_inputs())
    for rule, msg in errs:
        print('FAIL [%s] %s' % (rule, msg))
    print('%d findings' % len(errs))
    return 1 if errs else 0


if __name__ == '__main__':
    sys.exit(main())
