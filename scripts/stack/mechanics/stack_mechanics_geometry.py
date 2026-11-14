"""Derive the stack-mechanics geometry block from the retained partition sources.

Every value here is DERIVED from repository files whose SHA256 is recorded next to it.
The result is stored in design/stack/mechanics/stackups.json under "geometry"; the
calculator reads only that JSON, and the tests re-derive this block to prove it is
not stale.
"""
from pathlib import Path
import hashlib
import json
import math

ROOT = Path(__file__).resolve().parents[3]
SOURCES = {
    'partition': 'design/partition/partition.json',
    'mechanical_candidate': 'design/partition/mechanical-candidate.json',
    'placements_lock': 'design/grid/placements.lock.json',
    'stage_optical': 'design/partition/stage-optical-candidate.json',
}

# Plan-page facts that the partition does not hold yet (doc/src/content/docs/decisions/osc-direct-stack-plan.mdx).
SUB_PAIR_CENTRES = [[31.5, 180.5], [65.5, 180.5]]
P_POWER_TAB_Y = 175.0
MATED_HEIGHT = {'JL': 12.9, 'JR': 12.9, 'P': 11.1, 'O1': 6.9, 'O3': 6.9, 'O5': 6.9, 'EL': 7.2}
FRONT_FACE_Z = {'JL': -10.0, 'JR': -10.0, 'P': -11.8, 'O1': -16.0, 'O3': -16.0, 'O5': -16.0, 'EL': -4.2}
UNIT_ORDER = ['JL', 'JR', 'P', 'O1', 'O3', 'O5', 'EL']
BOARD_KEY = {'osc-jack-left': 'JL', 'osc-jack-right': 'JR', 'osc-control': 'P', 'osc-core': 'K',
             'osc-stage-optical': 'EL', 'osc-octave-1': 'O1', 'osc-octave-3': 'O3', 'osc-octave-5': 'O5'}


def sha256(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def load(name):
    return json.loads((ROOT / SOURCES[name]).read_text())


def r4(value):
    return round(float(value), 4)


def dist(a, b):
    return math.hypot(a[0] - b[0], a[1] - b[1])


def bbox(points):
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    return [min(xs), min(ys), max(xs), max(ys)]


def positions_per_pair(contacts_today, unit):
    """Rigid-pair widths from the plan's interconnect table."""
    if unit == 'EL':
        return 6
    return {3: 3, 7: 5, 8: 6}[contacts_today]


def derive():
    part = load('partition')
    mech = load('mechanical_candidate')
    lock = load('placements_lock')
    optical = load('stage_optical')
    headers = {c['id']: c for c in part['connectors']}

    pairs = {u: [] for u in UNIT_ORDER}
    for h in part['harnesses']:
        boards = tuple(h['boards'])
        ends = {headers[i]['board']: headers[i] for i in h['header_ids']}
        if 'O2' in boards or 'O4' in boards:
            continue
        if boards == ('JL', 'P'):
            # Pass-through: a new JL-to-K 1x3 at the JL end and a new P-to-K 1x3 at the P end.
            pairs['JL'].append({'xy': ends['JL']['center_mm'], 'positions': 3})
            pairs['P'].append({'xy': ends['P']['center_mm'], 'positions': 3})
            continue
        if boards == ('EL', 'K'):
            # EL mates a P tab (EL-to-P 1x6) and P passes to K at K's EL site (P-to-K 1x6).
            pairs['EL'].append({'xy': ends['EL']['center_mm'], 'positions': 6})
            pairs['P'].append({'xy': ends['K']['center_mm'], 'positions': 6})
            continue
        front = [b for b in boards if b != 'K'][0]
        hdr = ends[front]
        if front.startswith('O'):
            pairs[front].append({'xy': hdr['center_mm'], 'positions': 5})
        else:
            pairs[front].append({'xy': hdr['center_mm'], 'positions': positions_per_pair(hdr['contacts'], front)})
    for xy in SUB_PAIR_CENTRES:
        pairs['P'].append({'xy': xy, 'positions': 3})

    posts = {'JL': [], 'JR': [], 'P': []}
    for pad in mech['factory_load_power_pads']:
        if pad['board'] in posts:
            x, y = pad['center_mm']
            if pad['board'] == 'P' and x in (142, 159, 176, 193):
                y = P_POWER_TAB_Y  # four lands moved onto the power tab, coaxial with K
            posts[pad['board']].append([x, y])
    el_posts = [s['position_mm'] for s in part['supports'] if s['board'] == 'EL']
    posts['EL'] = el_posts
    for o in ('O1', 'O3', 'O5'):
        posts[o] = []

    outlines = {BOARD_KEY[b['id']]: b['outline'] for b in part['boards'] if b['id'] in BOARD_KEY}

    hardware = {u: [] for u in UNIT_ORDER}
    for p in lock['placements']:
        dom = p['domain']
        kind = p['kind']
        xy = [p['x_mm'], p['y_mm']]
        if kind == 'octave':
            if p.get('assembly_pcb_z_mm') == -29:
                hardware['P'].append({'uid': p['uid'], 'class': 'sub_toggle', 'xy': xy})
            else:
                key = 'O' + p['block'][-1]
                hardware[key].append({'uid': p['uid'], 'class': 'selector', 'xy': xy})
            continue
        cls = {'jack': 'jack', 'pot': 'pot', 'switch': 'toggle', 'button': 'button', 'led': 'indicator'}[kind]
        if dom in hardware:
            hardware[dom].append({'uid': p['uid'], 'class': cls, 'xy': xy})
    passages = [{'uid': q['uid'], 'class': 'el_passage_' + q['kind'], 'xy': q['center_mm'],
                 'diameter_mm': q['diameter_mm']} for q in optical['passages']]

    all_posts = [xy for u in ('JL', 'JR', 'P') for xy in posts[u]]
    units = {}
    for u in UNIT_ORDER:
        outline = outlines[u]
        box = bbox(outline)
        width, height = box[2] - box[0], box[3] - box[1]
        diag = math.hypot(width, height)
        pts = [p['xy'] for p in pairs[u]] + [h['xy'] for h in hardware[u]]
        corner = [box[0], box[1]]
        r_corner = max(dist(corner, q) for q in pts)
        entry = {
            'pairs': len(pairs[u]),
            'positions': sum(p['positions'] for p in pairs[u]),
            'mated_height_mm': MATED_HEIGHT[u],
            'front_face_z_mm': FRONT_FACE_Z[u],
            'outline_bbox_mm': [r4(v) for v in box],
            'longest_side_mm': r4(max(width, height)),
            'diagonal_mm': r4(diag),
            'hardware_count': len(hardware[u]),
            'posts': len(posts[u]),
            'diag_pins_r_max_mm': r4(r_corner),
        }
        if posts[u]:
            pp = sorted(posts[u])
            prim, sec = pp[0], pp[-1]
            entry['post_locator_span_mm'] = r4(dist(prim, sec))
            entry['post_locator_r_max_mm'] = r4(max(dist(prim, q) for q in pts))
            entry['pair_to_nearest_post_max_mm'] = r4(max(min(dist(p['xy'], q) for q in posts[u]) for p in pairs[u]))
        if u in ('JL', 'JR', 'P'):
            entry['pair_to_nearest_stack_post_on_K_max_mm'] = r4(max(min(dist(p['xy'], q) for q in all_posts) for p in pairs[u]))
        units[u] = entry

    k_box = bbox(outlines['K'])
    k_pairs = [p['xy'] for u in ('JL', 'JR', 'P', 'O1', 'O3', 'O5') for p in pairs[u]]
    units_k = {
        'outline_bbox_mm': [r4(v) for v in k_box],
        'longest_side_mm': r4(max(k_box[2] - k_box[0], k_box[3] - k_box[1])),
        'pairs': len(k_pairs),
        'positions': sum(units[u]['positions'] for u in ('JL', 'JR', 'P', 'O1', 'O3', 'O5')),
        'pair_to_nearest_post_max_mm': r4(max(min(dist(p, q) for q in all_posts) for p in k_pairs)),
    }
    jl_xs = [x for x, _ in posts['JL']]
    jr_xs = [x for x, _ in posts['JR']]
    p_rows = sorted({y for _, y in posts['P']})
    j_row = sorted({y for _, y in posts['JL'] + posts['JR']})
    class_counts = {}
    for u in UNIT_ORDER:
        for h in hardware[u]:
            class_counts.setdefault(h['class'], {}).setdefault(u, 0)
            class_counts[h['class']][u] += 1
    for q in passages:
        class_counts.setdefault(q['class'], {}).setdefault('EL', 0)
        class_counts[q['class']]['EL'] += 1
    return {
        'status': 'DERIVED',
        'formula': 'scripts/stack/mechanics/stack_mechanics_geometry.py derive()',
        'sources': {k: {'path': v, 'sha256': sha256(v)} for k, v in SOURCES.items()},
        'units': units,
        'K': units_k,
        'posts_mm': {u: posts[u] for u in ('JL', 'JR', 'P')},
        'el_post_count': len(el_posts),
        'j_post_row_y_mm': j_row,
        'p_post_rows_y_mm': p_rows,
        'j_to_p_post_row_spacing_mm': [r4(min(p_rows) - max(j_row)), r4(max(p_rows) - max(j_row))],
        'jl_jr_inner_post_span_mm': r4(min(jr_xs) - max(jl_xs)),
        'hardware_class_counts': class_counts,
        'el_passage_diameters_mm': sorted({(q['class'], q['diameter_mm']) for q in passages}),
    }


if __name__ == '__main__':
    print(json.dumps(derive(), indent=1))
