"""Independent geometry and source-identity checks for the ST-07 candidate."""
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(HERE))
import generate as gen
sg = gen.sg


def validate(plan):
    errors = []
    raw = sg.load_raw()
    boards = sg.load_boards(raw)
    gate = json.loads((ROOT / gen.SOURCES[0]).read_text())
    stack = json.loads((ROOT / 'design/stack/geometry/stack-candidate.json').read_text())['candidate']
    for path in gen.SOURCES:
        # Routing-only board changes are allowed; the extracted geometry digest is the board lock.
        if path != 'boards/osc-core/osc-core.kicad_pcb' and plan['source_sha256'].get(path) != gen.sha(path):
            errors.append('stale source: ' + path)
    if plan.get('canonical_geometry_digest') != sg.canonical_digest(sg.canonical_inputs(raw, boards)):
        errors.append('stale canonical geometry')
    if plan.get('source_counts') != {'replacement_footprints': 438, 'link_count': 61,
                                      'fixing_keepouts': 22}:
        errors.append('source count changed')
    transformed = gen.transformed_inventory(boards, gate)
    actual = {f['ref']: f for f in transformed['K'] if 'TC33X' in f['lib'] or f['lib'].startswith('TestPad')}
    rows = plan.get('records', [])
    refs = [r.get('ref') for r in rows]
    if len(rows) != 104 or len(set(refs)) != 104 or set(refs) != set(actual):
        errors.append('missing/duplicate adjustment')
    if sum('TC33X' in f['lib'] and f['side'] == 'F' for f in actual.values()) != 45:
        errors.append('front inventory changed')
    moving = {ref for ref, f in actual.items() if f['side'] == 'F'}
    ci = {'parameters': raw['parameters'], 'partition': raw['partition'], 'boards': transformed}
    obs = gen.obstacles(ci, gate, moving)
    outline = stack['planes']['K']['outline']
    margin = raw['parameters']['board_edge_margin_mm']
    row_by_ref = {r.get('ref'): r for r in rows}
    order = plan.get('search', {}).get('order', [])
    if len(order) != len(moving) or set(order) != moving:
        errors.append('search order does not cover front inventory')
    for ref, f in actual.items():
        row = row_by_ref.get(ref)
        if row is None:
            continue
        if row.get('after_link_projection') != {
            'face': f['side'], 'xy_mm': f['origin'], 'courtyard_mm': f['courtyard'],
            'replacement_step': next((x.get('step') for x in gate['replacement']['footprints']
                                      if x['board'] == 'K' and x['ref'] == ref), None),
        }:
            errors.append(ref + ': transformed source mismatch')
        if f['side'] == 'B' and row.get('proposal') is not None:
            errors.append(ref + ': rear item has move')
    for ref in order:
        row = row_by_ref.get(ref)
        if row is None:
            continue
        f = actual[ref]
        p = row.get('proposal')
        if p is None:
            if row.get('verdict') != 'NO_COURTYARD_POSITION_WITHIN_30MM_NEEDS_DESIGN':
                errors.append(ref + ': missing candidate verdict')
            if gen.place(f, obs, outline, margin, gen.offsets()) is not None:
                errors.append(ref + ': available courtyard position omitted')
            continue
        xy, rect = p.get('xy_mm'), p.get('courtyard_mm')
        if p.get('face') != 'B' or not isinstance(xy, list) or not isinstance(rect, list) or len(xy) != 2 or len(rect) != 4:
            errors.append(ref + ': malformed placement')
            continue
        if not all(isinstance(v, (float, int)) and math.isfinite(v) for v in xy + rect):
            errors.append(ref + ': nonfinite placement')
            continue
        dx, dy = xy[0] - f['origin'][0], xy[1] - f['origin'][1]
        expect = [round(f['courtyard'][i] + (dx if i % 2 == 0 else dy), 4) for i in range(4)]
        if any(abs(a - b) > 0.0002 for a, b in zip(expect, rect)):
            errors.append(ref + ': courtyard/position mismatch')
        distance = math.hypot(dx, dy)
        if distance > gen.SEARCH_RADIUS_MM + 1e-6 or abs(distance - p.get('distance_mm', -1)) > 0.0002:
            errors.append(ref + ': exceeds assumed search radius or wrong distance')
        if not sg.rect_inside_poly(rect, outline, margin):
            errors.append(ref + ': outside K outline')
        hits = obs.hits('B', rect)
        if hits:
            errors.append(ref + ': collides with ' + ', '.join(str(h) for h in hits[:3]))
        obs._add('B', sg.grow(rect, 0.35), ref, 'candidate courtyard')
    return errors


if __name__ == '__main__':
    plan = json.loads(gen.OUT.read_text())
    errs = validate(plan)
    if errs:
        print('\n'.join(errs))
        raise SystemExit(1)
    print('PASS ST-07 candidate: 104 adjustments; 45 front trimmers, 2 front pads; geometry only')
