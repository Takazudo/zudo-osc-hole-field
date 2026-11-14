"""Courtyard-level screen of the 18 power-post envelopes on K and the front boards.

Reads the board files with the geometry task's plain-Python extractor (no KiCad),
lists every footprint whose courtyard (pad box when it has none) enters a post
keep-out circle on either face, and searches the nearest free position for each.
Writes `design/stack/power-posts/envelopes.json`. A planning screen only: it is
not a copper clearance, a DRC or a fit.

  python3 scripts/stack/power_posts/measure_envelopes.py
"""
import json
import math
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT / 'scripts/stack/geometry'))
import stackgeom  # noqa: E402  (read-only import of the ST-02 reader)

DESIGN = ROOT / 'design/stack/power-posts/joint-design.json'
OUT = ROOT / 'design/stack/power-posts/envelopes.json'
BOARDS = ('K', 'JL', 'JR', 'P')
STEP = 0.25
MAX_SHIFT = 12.0


def box(fp):
    if fp['courtyard']:
        return fp['courtyard']
    bxs = [p['bbox'] for p in fp['pads']]
    if not bxs:
        return None
    return [min(b[0] for b in bxs), min(b[1] for b in bxs), max(b[2] for b in bxs), max(b[3] for b in bxs)]


def circle_hits(rect, c, r):
    dx = max(rect[0] - c[0], 0, c[0] - rect[2])
    dy = max(rect[1] - c[1], 0, c[1] - rect[3])
    return math.hypot(dx, dy) < r


def is_tht(fp):
    return any(p['type'] in ('thru_hole', 'np_thru_hole') for p in fp['pads'])


def faces(fp):
    return ('F', 'B') if is_tht(fp) else (fp['side'],)


def main():
    design = json.loads(DESIGN.read_text())
    land = design['land_pattern']
    raw = stackgeom.load_raw()
    cand = json.loads((ROOT / 'design/stack/geometry/stack-candidate.json').read_text())['candidate']
    outlines = {b: cand['planes'][b]['outline'] for b in BOARDS}
    boards = stackgeom.load_boards(raw, files={b: stackgeom.BOARD_FILES[b] for b in BOARDS})
    # Keep-out circles per board: K lands use the K land, front lands the front land.
    circles = {b: [] for b in BOARDS}
    for j in design['joints']:
        circles['K'].append((j['id'], j['K_xy'], land['K']['keepout_radius_mm']))
        circles[j['front_board']].append((j['id'], j['front_xy'], land['front']['keepout_radius_mm']))
    result = {'status': 'DERIVED courtyard-level planning screen; not a copper clearance, DRC or fit',
              'method': 'footprint courtyard box (pad box when none) against keep-out circles; through-hole parts count on both faces; '
                        'nearest free position = smallest shift (0.25 mm steps, 24 directions, up to 12 mm) whose box clears every post circle '
                        'and every other same-face box on that board and stays inside the board outline',
              'input_sha256': {stackgeom.BOARD_FILES[b]: stackgeom.sha256_file(ROOT / stackgeom.BOARD_FILES[b]) for b in BOARDS},
              'boards': {}}
    for b in BOARDS:
        fps = [f for f in boards[b] if not f['ref'].startswith('TP9900') and box(f)]
        per = []
        for jid, c, r in circles[b]:
            for f in fps:
                bx = box(f)
                if not circle_hits(bx, c, r):
                    continue
                per.append({'joint': jid, 'ref': f['ref'], 'lib': f['lib'], 'faces': list(faces(f)),
                            'origin': f['origin'], 'box': bx, 'tht': is_tht(f)})
        # nearest free positions
        moved_refs = {m['ref'] for m in per}
        for m in per:
            others = [box(f) for f in fps if f['ref'] != m['ref'] and set(faces(f)) & set(m['faces'])]
            best = None
            for k in range(1, int(MAX_SHIFT / STEP) + 1):
                d = k * STEP
                for a in range(0, 360, 15):
                    dx, dy = d * math.cos(math.radians(a)), d * math.sin(math.radians(a))
                    nb = [m['box'][0] + dx, m['box'][1] + dy, m['box'][2] + dx, m['box'][3] + dy]
                    if any(circle_hits(nb, c, r) for _, c, r in circles[b]):
                        continue
                    if any(stackgeom.inter(nb, o) for o in others):
                        continue
                    if not stackgeom.rect_inside_poly(nb, outlines[b], 0.3):
                        continue
                    best = (round(d, 2), [round(m['origin'][0] + dx, 3), round(m['origin'][1] + dy, 3)])
                    break
                if best:
                    break
            m['nearest_free_shift_mm'] = best[0] if best else None
            m['nearest_free_origin'] = best[1] if best else None
            m['box'] = [round(v, 3) for v in m['box']]
        by_face = {'F': sorted({m['ref'] for m in per if 'F' in m['faces']}),
                   'B': sorted({m['ref'] for m in per if 'B' in m['faces']})}
        result['boards'][b] = {'hits': per, 'refs_by_face': by_face, 'count_unique': len(moved_refs)}
    OUT.write_text(json.dumps(result, indent=1) + '\n')
    for b in BOARDS:
        r = result['boards'][b]
        print(b, 'F', len(r['refs_by_face']['F']), 'B', len(r['refs_by_face']['B']),
              'no free position', sum(1 for m in r['hits'] if m['nearest_free_shift_mm'] is None))


if __name__ == '__main__':
    main()
