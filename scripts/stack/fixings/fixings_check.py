"""Checker of the fixing list (ST-08 a1 part 1): recomputes each rule from the boards and the inputs.

Rules (one error class each):
  spacing   a sleeve, kept or added, has another fixing of K within 70 mm (DS-66)
  coverage  a node of the 1 mm grid over K lies farther than 90 mm from every fixing (DS-66)
  site      a sleeve on locked panel hardware, on a fixed hole, on a tab, an adapter, a kept selector or a sub
            toggle, or outside a board (the sleeve for an added site, the bore for a given site)
  moves     a footprint inside a keep-out of a sleeve, or a ceramic of 0805 or larger within 5 mm of any fixing,
            without a listed move; or a listed free position that does not clear the fixings
  stale     an input or program hash differs from the files

  python3 scripts/stack/fixings/fixings_check.py     # check the retained fixing-sites.json
"""
import json
import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import fixings as fx  # noqa: E402


def check(doc, inp):
    """List of (rule, message) for a fixing list."""
    errs = []
    prm = fx.parameters(inp)
    cand = inp['cand']
    ol = fx.outlines(cand)
    fcls = fx.footprint_classes(inp)
    spacing, cover = fx.val(prm['sleeve_min_spacing_mm']), fx.val(prm['coverage_max_mm'])
    active = [f for f in doc['fixings'] if f['kind'] != 'sleeve dropped']
    sleeves = [f for f in active if f['kind'] != 'post']

    # staleness
    now = fx.input_hashes(inp['root'])
    for p, h in sorted(doc['provenance']['input_sha256'].items()):
        if now.get(p) != h:
            errs.append(('stale', '%s: retained %s, file %s' % (p, h[:12], (now.get(p) or 'missing')[:12])))
    for p in sorted(set(now) - set(doc['provenance']['input_sha256'])):
        errs.append(('stale', '%s: not in the provenance' % p))

    # spacing
    for s in sleeves:
        for o in active:
            if o['id'] != s['id'] and math.dist(s['xy'], o['xy']) < spacing - 1e-9:
                errs.append(('spacing', '%s is %.2f mm from %s' % (s['id'], math.dist(s['xy'], o['xy']), o['id'])))

    # coverage
    grid = fx.k_grid(cand, fx.val(prm['grid_mm']))
    d, at = fx.farthest(grid, [f['xy'] for f in active])
    if d > cover + 1e-9:
        errs.append(('coverage', 'farthest node %s is %.3f mm from a fixing' % (at, d)))

    # site
    hole_edge = fx.val(prm['sleeve_bore_mm']) / 2 + fx.val(prm['board_edge_margin_mm'])
    for s in sleeves:
        front = fx.front_board_at(s['xy'], ol)
        if front is None or front != s['front_board']:
            errs.append(('site', '%s: facing board %s, listed %s' % (s['id'], front, s['front_board'])))
            continue
        edge = None if s['kind'] == 'sleeve added' else hole_edge
        for why in fx.obstacle_reasons(s['xy'], front, ol, cand, prm, edge=edge):
            errs.append(('site', '%s: %s' % (s['id'], why)))
        for b in fx.pierced(s['xy'], front, ol):
            for h in fx.keepout_hits(s['xy'], b, fcls, prm):
                if h['in_keepout'] and h['class'] != 'movable':
                    errs.append(('site', '%s: %s %s on %s at %.2f mm' % (s['id'], h['class'], h['ref'], b, h['distance_mm'])))

    # moves
    rc = fx.val(prm['ceramic_radius_mm'])
    for f in active:
        listed = {(m['board'], m['ref']): m for m in f.get('part_moves', [])}
        for b in f['boards']:
            for h in fx.keepout_hits(f['xy'], b, fcls, prm):
                if h['class'] != 'movable':
                    continue
                needs = h['ceramic_0805_or_larger_within_5mm'] or (f['kind'] != 'post' and h['in_keepout'])
                if needs and (b, h['ref']) not in listed:
                    errs.append(('moves', '%s: %s on %s inside the keep-out has no listed move' % (f['id'], h['ref'], b)))
        for (b, ref), m in listed.items():
            pos = m.get('nearest_free_origin')
            if m['class'] != 'movable' or pos is None:
                continue
            fp = next(x for x, _ in fcls[b] if x['ref'] == ref)
            dx, dy = pos[0] - fp['origin'][0], pos[1] - fp['origin'][1]
            bx = fx.box(fp)
            nb = [bx[0] + dx, bx[1] + dy, bx[2] + dx, bx[3] + dy]
            for o in active:
                if b not in o['boards']:
                    continue
                r = o['keepout_radius_mm'][b]
                if fx.ceramic_at_least(fp, fx.val(prm['ceramic_min_case'])):
                    r = max(r, rc)
                if fx.box_dist(nb, o['xy']) < r - 1e-6:
                    errs.append(('moves', '%s: the free position of %s on %s lies inside the keep-out of %s'
                                 % (f['id'], ref, b, o['id'])))
    return errs


def main():
    doc = json.loads(fx.SITES_JSON.read_text())
    inp = fx.load_inputs()
    errs = check(doc, inp)
    for rule, msg in errs:
        print('FAIL [%s] %s' % (rule, msg))
    expected = [tuple(e) for e in doc.get('checker_findings', [])]
    print('%d findings; %d recorded in the retained list as open' % (len(errs), len(expected)))
    return 0 if errs == expected else 1


if __name__ == '__main__':
    sys.exit(main())
