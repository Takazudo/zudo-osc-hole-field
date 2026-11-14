"""Derive the stack-mechanics geometry block (XY only) from retained sources.

XY of pairs, posts, tabs and outlines comes from the ST-02 geometry candidate
(design/stack/geometry/stack-candidate.json). Support coordinates and the panel
size come from partition.json and hardware centres from the placement lock,
because the candidate does not carry them. Heights, gaps and planes are NOT read
here: the calculator takes them from the DA-01 parameter block in stackups.json,
and the height notes compare the two.

The fixing sets (kept supports and provisional tie sites) are read from
stackups.json, because they are this task's dispositions and DA-01's decisions.
"""
from collections import Counter
from pathlib import Path
import hashlib
import json
import math

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / 'design/stack/mechanics/stackups.json'
SOURCES = {
    'stack_candidate': 'design/stack/geometry/stack-candidate.json',
    'partition': 'design/partition/partition.json',
    'placements_lock': 'design/grid/placements.lock.json',
}
ROUND = 4


def sha256(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def load_json(path):
    return json.loads((ROOT / path).read_text())


def r(value):
    return round(float(value), ROUND)


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def bbox(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return [min(xs), min(ys), max(xs), max(ys)]


def seg_dist(pt, a, b):
    ax, ay = a
    dx, dy = b[0] - ax, b[1] - ay
    length2 = dx * dx + dy * dy
    u = 0.0 if length2 == 0 else max(0.0, min(1.0, ((pt[0] - ax) * dx + (pt[1] - ay) * dy) / length2))
    return math.hypot(pt[0] - ax - u * dx, pt[1] - ay - u * dy)


def boundary_dist(pt, poly):
    return min(seg_dist(pt, poly[i], poly[(i + 1) % len(poly)]) for i in range(len(poly)))


def inside(pt, poly, eps=1e-9):
    """Point in polygon, independent of the outline's orientation; a point on the boundary counts as inside."""
    if boundary_dist(pt, poly) <= eps:
        return True
    x, y = pt
    hit = False
    for i in range(len(poly)):
        x1, y1 = poly[i]
        x2, y2 = poly[(i + 1) % len(poly)]
        if (y1 > y) != (y2 > y) and x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
            hit = not hit
    return hit


def grid(outline, step):
    x0, y0, x1, y1 = bbox(outline)
    nx, ny = int(round((x1 - x0) / step)), int(round((y1 - y0) / step))
    for j in range(ny + 1):
        for i in range(nx + 1):
            pt = (x0 + i * step, y0 + j * step)
            if inside(pt, outline):
                yield pt


def largest_inscribed_bay(outline, points, step):
    """Largest circle that lies inside the outline and holds no fixing (grid search)."""
    best = (0.0, None)
    for pt in grid(outline, step):
        d = min(boundary_dist(pt, outline), min(dist(pt, q) for q in points))
        if d > best[0]:
            best = (d, pt)
    return best


def farthest_in_region(outline, points, step, keep):
    """Point of the region (outline points where keep(pt) holds) farthest from every fixing."""
    best = (0.0, None)
    for pt in grid(outline, step):
        if not keep(pt):
            continue
        d = min(dist(pt, q) for q in points)
        if d > best[0]:
            best = (d, pt)
    return best


BAY_GRID_STEP_MM = 1.0  # grid of the bay and free-edge searches on K


def k_regions(outline, fixings):
    """Bay and free-edge spans of K for one fixing set (attempt a4 item 1)."""
    pts = [f['xy'] for f in fixings]
    rows = sorted({f['xy'][1] for f in fixings if f['kind'] == 'post'})
    radius, centre = largest_inscribed_bay(outline, pts, BAY_GRID_STEP_MM)
    out = {'interior_bay': {'radius_mm': r(radius), 'centre_xy': [r(c) for c in centre]}}
    for name, keep in (('edge_region_low_y', lambda p: p[1] < rows[0]), ('edge_region_high_y', lambda p: p[1] > rows[-1])):
        span, pt = farthest_in_region(outline, pts, BAY_GRID_STEP_MM, keep)
        out[name] = {'span_mm': r(span), 'point_xy': [r(c) for c in pt]}
    out['post_rows_y_mm'] = [r(y) for y in rows]
    return out


def derive_a3(cand):
    """K on the 30 declared fixings (DS-43), the sleeves (DS-45) and the six adapter pairs."""
    fx = [f for f in cand['fixings'] if f['declared'] and f['kind'] in ('post', 'kept support')]
    posts = [f for f in fx if f['kind'] == 'post']
    k_outline = cand['planes']['K']['outline']
    sleeves = []
    for f in fx:
        if f['kind'] != 'kept support':
            continue
        near = min((g for g in fx if g['id'] != f['id']), key=lambda g: dist(f['xy'], g['xy']))
        sleeves.append({'id': f['id'], 'board': f['front_board'], 'xy': [r(c) for c in f['xy']],
                        'nearest_fixing': near['id'], 'd_fixing_mm': r(dist(f['xy'], near['xy']))})
    adapters = []
    for p in cand['pairs']:
        board = p['sites']['front']['board']
        if not board.startswith('O'):
            continue
        xy = p['sites']['front']['center']
        near = min(fx, key=lambda g: dist(xy, g['xy']))
        near_post = min(posts, key=lambda g: dist(xy, g['xy']))
        adapters.append({'id': p['id'], 'board': board, 'xy': [r(c) for c in xy], 'positions': p['positions'],
                         'nearest_fixing': near['id'], 'd_fixing_mm': r(dist(xy, near['xy'])),
                         'nearest_post': near_post['id'], 'd_post_mm': r(dist(xy, near_post['xy']))})
    counts = Counter((f['kind'], f['front_board']) for f in fx)
    return {
        'fixing_counts': {f'{k} {b}': n for (k, b), n in sorted(counts.items())},
        'k_regions': {'posts_and_sleeves': k_regions(k_outline, fx), 'posts_only': k_regions(k_outline, posts)},
        'sleeves': sleeves,
        'adapter_pairs': adapters,
    }


def derive(stackups=None):
    st = stackups if stackups is not None else json.loads(DATA.read_text())
    cand = load_json(SOURCES['stack_candidate'])['candidate']
    part = load_json(SOURCES['partition'])
    lock = load_json(SOURCES['placements_lock'])
    support_xy = {s['id']: s['position_mm'] for s in part['supports']}
    outlines = {k: v['outline'] for k, v in cand['planes'].items()}

    fixings = {'posts': [], 'kept_supports': [], 'provisional': []}
    for p in cand['posts']:
        fixings['posts'].append({'id': p['id'], 'board': p['front_board'], 'xy': p['K_land']})
    for sid, board in st['fixings']['kept_supports'].items():
        fixings['kept_supports'].append({'id': sid, 'board': board, 'xy': support_xy[sid]})
    for site in st['fixings']['provisional_tie_sites']:
        board = [b for b in ('JL', 'JR', 'P') if inside(site['xy'], outlines[b])]
        fixings['provisional'].append({'id': site['id'], 'board': board[0] if board else None, 'xy': site['xy']})

    def nearest(xy, board, sets):
        pool = [f for s in sets for f in fixings[s]]
        same = [f for f in pool if f['board'] == board]
        d_front = min(dist(xy, f['xy']) for f in same) if same else None
        d_k = min(dist(xy, f['xy']) for f in pool)
        return d_front, d_k

    base_sets = ('posts', 'kept_supports')
    plus_sets = ('posts', 'kept_supports', 'provisional')
    pairs = []
    for p in cand['pairs']:
        front = p['sites']['front']
        board = front['board']
        joint = {'JL': 'JL', 'JR': 'JR', 'P': 'P', 'EL': 'EL'}.get(board, 'O')
        entry = {'id': p['id'], 'family': p['family'], 'board': board, 'joint': joint, 'xy': front['center'],
                 'positions_candidate': p['positions']}
        if joint in ('JL', 'JR', 'P'):
            for tag, sets in (('base', base_sets), ('plus', plus_sets)):
                d_front, d_k = nearest(front['center'], board, sets)
                entry['d_front_' + tag] = r(d_front)
                entry['d_K_' + tag] = r(d_k)
        pairs.append(entry)

    k_pairs = [p for p in pairs if p['joint'] != 'EL']
    bays = {}
    for tag in ('base', 'plus'):
        worst = max((p for p in k_pairs if 'd_K_' + tag in p), key=lambda p: p['d_K_' + tag])
        radius = worst['d_K_' + tag]
        bays[tag] = {'centre_pair': worst['id'], 'centre_xy': worst['xy'], 'radius_mm': radius,
                     'pairs_inside': sorted(q['id'] for q in k_pairs if dist(q['xy'], worst['xy']) <= radius)}

    tab_el = [t for t in cand['tabs'] if t['id'] == 'TAB-EL'][0]
    tab_posts = [support_xy[s] for s in tab_el['pass_through_supports']]
    el_sites = [p['xy'] for p in pairs if p['joint'] == 'EL']
    el_overhang = max(min(abs(x - q[0]) for q in tab_posts) for x, _ in el_sites)
    el_post_pitch = sorted({round(q[0], 4) for q in tab_posts})
    el_post_pitch = min(b - a for a, b in zip(el_post_pitch, el_post_pitch[1:]))

    hardware = {}
    for h in lock['placements']:
        hardware.setdefault(h['kind'], 0)
        hardware[h['kind']] += 1

    jl_x = [f['xy'][0] for f in fixings['posts'] if f['board'] == 'JL']
    jr_x = [f['xy'][0] for f in fixings['posts'] if f['board'] == 'JR']
    j_rows = sorted({f['xy'][1] for f in fixings['posts'] if f['board'] in ('JL', 'JR')})
    p_rows = sorted({f['xy'][1] for f in fixings['posts'] if f['board'] == 'P'})
    return {
        'status': 'DERIVED',
        'formula': 'scripts/stack/mechanics/stack_mechanics_geometry.py derive()',
        'sources': {k: {'path': v, 'sha256': sha256(v)} for k, v in SOURCES.items()},
        'candidate_heights_mm': cand['stack']['mated_heights_mm'],
        'candidate_K_face_z_mm': cand['stack']['K_face_z_mm'],
        'panel_size_mm': [part['panel']['width_mm'], part['panel']['height_mm']],
        'outlines': {k: {'bbox_mm': [r(v) for v in bbox(o)], 'longest_side_mm': r(max(bbox(o)[2] - bbox(o)[0], bbox(o)[3] - bbox(o)[1]))}
                     for k, o in outlines.items()},
        'fixings': fixings,
        'pairs': pairs,
        'largest_bay': bays,
        'el_tab_post_pitch_mm': r(el_post_pitch),
        'el_outer_site_overhang_mm': r(el_overhang),
        'j_post_rows_y_mm': j_rows,
        'p_post_rows_y_mm': p_rows,
        'j_to_p_post_row_spacing_mm': [r(min(p_rows) - max(j_rows)), r(max(p_rows) - max(j_rows))],
        'jl_jr_inner_post_span_mm': r(min(jr_x) - max(jl_x)),
        'hardware_kind_counts': hardware,
        'a3': derive_a3(cand),
    }


if __name__ == '__main__':
    print(json.dumps(derive(), indent=1)[:4000])
