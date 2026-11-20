"""Task C step 2b: move one covering link at a time and re-place what the move displaces.

For each link whose field, slot, tail or latch margin covers one of the 26 unresolved ICs, the retained
search (links_gate.search, class-distance accept, retained 24 mm radius) collects the cheapest legal
candidates. Each candidate replaces the link's geometry in the cumulative MC04-R1 scene (412 accepted
moves, unresolved bodies frozen). Parts the moved link now covers are re-placed one by one with the
retained ring pattern (0.25 mm, 24 directions, 25 mm cap; own face first, then the other face for
surface-mount parts), each accepted position becoming an obstacle. The outcome counts freed unresolved
ICs against parts left without a place. Room only: no routing, electrical review or canonical write."""
import argparse
import copy
import json
import math
from pathlib import Path
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(ROOT / 'scripts/stack/geometry'))
sys.path.insert(0, str(ROOT / 'scripts/stack/studies/mc04_r1'))
import links_gate as lg  # noqa: E402
import links_gate_part2 as p2  # noqa: E402
import stackgeom as sg  # noqa: E402
import study as r1  # noqa: E402

CANDIDATES = 6
GRIDS = (2.0, 0.5)


def cumulative_inputs():
    spec = json.loads(r1.SPEC.read_text())
    r1.verify_pins(ROOT, spec)
    doc = json.loads((ROOT / 'design/stack/geometry/links/link-gate.json').read_text())
    inp = r1.lg.load_inputs(ROOT)
    inp['ci']['boards'], accepted = r1.reconstruct(inp['ci']['boards'], doc['replacement']['footprints'], spec['replacement'])
    model = lg.GateModel(inp, lg.gate_sites(inp))
    unresolved = [(row['board'], row['ref']) for row in spec['replacement'] if row['new'] is None]
    if len(accepted) != 412 or len(unresolved) != 26:
        raise ValueError('cumulative scene changed')
    return doc, inp, r1.SimpleNamespace(model=model, opts=inp['opts']), unresolved


def panel_hardware(model):
    return {(b, p[2].split()[-1]) for (b, f), ix in model.forb.items() for _, p in ix.items
            if len(p) > 2 and isinstance(p[2], str) and p[2].startswith('panel hardware')}


def movable(scene, key, fixed):
    return (key[0] in p2.SCOPE_BOARDS and key[1] not in scene.model.dropped.get(key[0], ())
            and key not in fixed and complete(scene.bodies[key]))


def link_hits(hits, lid):
    return [h for h in hits if h.endswith(' of ' + lid)]


def covering_links(scene, unresolved, links):
    out = {}
    for key in unresolved:
        for h in scene._violations(key[0], scene.bodies[key], 0, 0, {key}):
            if ' of ' in h:
                out.setdefault(h.rsplit(' of ', 1)[1], set()).add(key)
    return out


def avoiding(base_accept, targets, bodies, front, latch, gap=0.35):
    """Retained class accept plus: the candidate must clear the courtyards of the unresolved ICs it covered."""
    def accept(geo):
        why = base_accept(geo)
        if why:
            return why
        for b, ref in targets:
            cy = sg.grow(bodies[(b, ref)]['courtyard'], gap)
            if b == front:
                rects = [geo['front_connector'], geo['front_tail'], geo['slot']]
            else:
                rects = [geo['K_connector'], geo['K_tail'], geo['slot'], sg.grow(geo['K_connector'], latch)]
            if any(sg.inter(r, cy) for r in rects):
                return 'still covers ' + ref
        return None
    return accept


def geo_clash(ga, gb, fa, fb):
    def rects(g, f):
        return [(f, g['front_connector']), (f, g['front_tail']), (f, g['slot']), ('K', g['K_connector']),
                ('K', g['K_tail']), ('K', g['slot'])]
    return any(ba == bb and sg.inter(ra, rb) for ba, ra in rects(ga, fa) for bb, rb in rects(gb, fb))


def evaluate(ctx_cum, inp_cum, links, moves, targets, already, unresolved, fixed, offsets):
    """Apply link geometries, re-place what they newly cover plus blockers of uncovered targets, count the result."""
    trial = copy.deepcopy(links)
    for x in trial:
        if x['id'] in moves:
            x['geometry'] = moves[x['id']]
    scene = r1.Scene(ctx_cum, inp_cum, trial)
    unres = set(unresolved)
    newly = [k for k, fp in scene.bodies.items()
             if movable(scene, k, fixed) and k not in unres and k not in already
             and any(link_hits(scene._violations(k[0], fp, 0, 0, {k}), lid) for lid in moves)]
    blockers = set()
    for t in sorted(targets):
        hits = scene._violations(t[0], scene.bodies[t], 0, 0, {t})
        if any(' of ' in h for h in hits):
            continue
        refs = {(t[0], h.split(':', 1)[1]) for h in hits if ':' in h}
        if hits and all(':' in h for h in hits) and all(movable(scene, k, fixed) and k not in unres for k in refs):
            blockers |= refs
    placed, failed = replace_parts(scene, sorted(set(newly) | blockers), offsets)
    freed = [t for t in sorted(unres) if not scene._violations(t[0], scene.bodies[t], 0, 0, {t} | set(placed))]
    return {'freed_unresolved': sorted('%s %s' % k for k in freed), 'newly_covered': len(newly),
            'blockers_moved': sorted('%s %s' % k for k in blockers), 'replaced': len(placed),
            'left_without_place': sorted('%s %s' % k for k in failed),
            'net_unresolved_change': len(failed) - len(freed)}


def has_tht(fp):
    return any(p['type'] in ('thru_hole', 'np_thru_hole') for p in fp['pads'])


def replace_parts(scene, keys, offsets):
    """Greedy re-placement; accepted positions are added as obstacles under a new owner key."""
    moving = set(keys)
    order = sorted(keys, key=lambda k: (not k[1].startswith('U'), -area(scene.bodies[k]), k))
    placed, failed = {}, []
    for key in order:
        fp = scene.bodies[key]
        faces = [fp['side']] + ([] if has_tht(fp) else ['F' if fp['side'] == 'B' else 'B'])
        hit = None
        for face in faces:
            f2 = dict(fp, side=face)
            for radius, dx, dy in offsets:
                if not scene._violations(key[0], f2, dx, dy, moving):
                    hit = (face, radius, dx, dy, f2); break
            if hit:
                break
        if hit is None:
            failed.append(key); continue
        face, radius, dx, dy, f2 = hit
        placed[key] = {'face': face, 'moved_mm': round(radius, 3), 'dx': round(dx, 3), 'dy': round(dy, 3)}
        for rect in r1.rectangles(f2):
            scene.field.idx[(key[0], face)].add(r1.obstacle_rect(p2.shift(rect, dx, dy), 0.0),
                                                ('body', (key[0], key[1] + '@new'), 'replaced ' + key[1]))
    return placed, failed


def complete(fp):
    try:
        r1.rectangles(fp)
        return True
    except r1.AdmissionError:
        return False


def area(fp):
    c = fp.get('courtyard') or [0, 0, 0, 0]
    return (c[2] - c[0]) * (c[3] - c[1])


def run(limit_links=None):
    t0 = time.time()
    doc, inp_cum, ctx_cum, unresolved = cumulative_inputs()
    links = doc['links']
    base = r1.Scene(ctx_cum, inp_cum, links)
    cover = covering_links(base, unresolved, links)
    fixed = panel_hardware(base.model)
    inp0 = lg.load_inputs(sg.ROOT)
    sites, model, ctx, out, s, refs = lg.gate_run(inp0, {})
    site_by = {x['id']: x for x in sites}
    limits = p2.limits_of(ctx.gopts)
    live = [r for r in links if not r.get('gone')]
    offsets = p2.ring_offsets(.25, 24, 25)
    results, alreadies = {}, {}
    for lid in sorted(cover)[:limit_links]:
        r = next(x for x in live if x['id'] == lid)
        placed_ix = lg.placed_index(live, skip=(lid,))
        size, own = lg.rec_size(ctx, r), lg.rec_own(r)
        cands = []
        for g in GRIDS:
            ctx.model.memo_for(None)
            found, _ = lg.search(ctx, placed_ix, r['front_board'], r['centre'], size, own,
                                 offsets=ctx.grid(g, radius=ctx.radius), collect=CANDIDATES,
                                 accept=avoiding(p2.class_accept(r, site_by, limits), cover[lid], base.bodies,
                                                 r['front_board'], base.field.latch))
            cands = found
            if cands:
                break
        already = {k for k, fp in base.bodies.items() if movable(base, k, fixed)
                   and link_hits(base._violations(k[0], fp, 0, 0, {k}), lid)}
        if not cands:
            alreadies[lid] = already
            results[lid] = {'covers': sorted('%s %s' % k for k in cover[lid]), 'recorded_cost': r['cost'],
                            'candidates': [], 'best': None, 'note': 'no candidate within the retained radius clears its covered ICs'}
            print(lid, None, round(time.time() - t0), file=sys.stderr, flush=True)
            continue
        rows = []
        for cost, key, geo, disp, d, slot, dist in cands:
            ev = evaluate(ctx_cum, inp_cum, links, {lid: geo}, cover[lid], already, unresolved, fixed, offsets)
            rows.append(dict({'cost': round(cost, 3), 'slot': list(slot), 'dist_mm': round(dist, 2)}, **ev,
                             geometry=geo))
        alreadies[lid] = already
        best = min(rows, key=lambda x: (x['net_unresolved_change'], x['cost'])) if rows else None
        results[lid] = {'covers': sorted('%s %s' % k for k in cover[lid]), 'recorded_cost': r['cost'],
                        'candidates': rows, 'best': best}
        print(lid, best and best['net_unresolved_change'], round(time.time() - t0), file=sys.stderr, flush=True)
    chosen = {lid: v['best']['geometry'] for lid, v in results.items()
              if v['best'] and v['best']['net_unresolved_change'] < 0}
    clash = [[a, b] for a in sorted(chosen) for b in sorted(chosen) if a < b and geo_clash(chosen[a], chosen[b],
             next(x for x in live if x['id'] == a)['front_board'], next(x for x in live if x['id'] == b)['front_board'])]
    combined = evaluate(ctx_cum, inp_cum, links, chosen, set().union(*(cover[l] for l in chosen)) if chosen else set(),
                        set().union(*(alreadies[l] for l in chosen)) if chosen else set(), unresolved, fixed, offsets)
    combined.update(links=sorted(chosen), link_clashes=clash)
    print('combined', combined['net_unresolved_change'], round(time.time() - t0), file=sys.stderr, flush=True)
    return {'status': 'TASK_C_STEP_2B_LINK_SHIFT_WITH_REPLACEMENT', 'combined_improving_moves': combined, 'links_covering_unresolved': len(cover),
            'candidates_per_link': CANDIDATES, 'results': results,
            'scope': ('One link moved at a time against the cumulative scene; candidates from the retained search '
                      'within the retained radius that clear the courtyards (grown 0.35 mm) of the unresolved ICs the link covered; greedy re-placement with the retained ring pattern and 25 mm cap '
                      '(panel hardware stays fixed: lg.search already applies the tail rule to it; dropped footprints and parts the recorded link already covers are not counted; own face first, then the other face for surface-mount parts; flipped footprints not mirrored); '
                      'parts that block an uncovered target IC in its original place are re-placed too; net change = parts left without a place minus unresolved ICs freed. Room only.')}


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--output', type=Path)
    ap.add_argument('--limit-links', type=int)
    a = ap.parse_args()
    text = json.dumps(run(a.limit_links), indent=1) + '\n'
    if a.output:
        with a.output.open('x') as f:
            f.write(text)
    else:
        print(text, end='')
