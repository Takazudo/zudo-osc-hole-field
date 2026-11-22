#!/usr/bin/env python3
"""MC04-S7: K poses for the moved function blocks of design/partition/k-block-relocation.json, in the floorplan's
own occupancy model (scripts/checks/partition35_floorplan.Grid, jack_locality.nearest).

Obstacles on K: the outline, the source reserves, the supports, the GH header lands and K service apertures, and the
adopted K pins and every pre-move K pose of reflow-pins.json, except the pins a GH header covers, which the
floorplan re-places. Each block in turn: the IC goes to
the free pose nearest its front-board pin, on the face (F first, then B) where it lands nearer; each member then
goes with its bypass capacitors as the floorplan's own rigid bypass cluster (bypass_cells, each capacitor's rail pad on
its supply pad's row), turned to the IC's front rotation; the other members go to the free pose nearest the IC on the
same face, larger courtyards first. Rotation is kept from the front pin except for a bypass capacitor turned by its cluster.
Each placed courtyard blocks later ones with the K courtyard gap. Writes k_poses into the relocation file, or checks
them with --check. A block that does not fit fails."""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.checks.partition35_floorplan import (Grid, oriented_box, header_conflicts, through_hole, bypass_cells,  # noqa: E402
                                                  turn, GAP_MM)
from scripts.checks.partition35_diagnostic import footprint_geometry  # noqa: E402
from scripts.checks.jack_locality import nearest, occupy  # noqa: E402

RELOCATION = ROOT / 'design/partition/k-block-relocation.json'


class _Shapes(dict):
    def __missing__(self, fp):
        self[fp] = shape(fp)
        return self[fp]


def shape(fp, cache={}):
    if fp not in cache:
        path = ROOT / 'footprints/kicad/zudo-osc-hole-field.pretty' / (fp.split(':')[1] + '.kicad_mod')
        cache[fp] = footprint_geometry(path)['courtyard_bbox_mm']
    return cache[fp]


SHAPES = None


def find(grid, rel, target, gap):
    """Nearest free origin (mm) to `target` for the courtyard `rel` (relative to the origin), or None."""
    s = grid.scale
    w = math.ceil((rel[2] - rel[0] + gap) * s)
    h = math.ceil((rel[3] - rel[1] + gap) * s)
    masks = [(0, 0, w, h)]
    corner = (round((target[0] + rel[0]) * s), round((target[1] + rel[1]) * s))
    hit = nearest(grid, masks, corner)
    if hit is None:
        return None
    _, xx, yy = hit
    occupy(grid, masks, xx, yy)
    return round(xx / s - rel[0], 3), round(yy / s - rel[1], 3)


def poses():
    global SHAPES
    SHAPES = _Shapes()
    reloc = json.loads(RELOCATION.read_text())
    pins = json.loads((ROOT / 'design/partition/adopted-placement-pins.json').read_text())['pins']
    pc = json.loads((ROOT / 'design/partition/connector-packing-candidate.json').read_text())
    io = json.loads((ROOT / 'design/reports/io-partition.json').read_text())
    spec = json.loads((ROOT / 'design/partition/partition-input.json').read_text())['boards']['K']
    gap = GAP_MM.get('K', .35)
    front = {(r['board'], r['ref']): r for r in pins}
    owner = {p['ref']: p['decouples_ref'] for p in io['physical_packages'] if p.get('decouples_ref')}
    nets = {}
    for u in io['package_units']:
        nets.setdefault(u['ref'], {}).update(u['pins'])
    k_rows = {r['ref']: r for r in pins if r['board'] == 'K'}
    moved = {r for b in reloc['blocks'] for r in b['members']}
    reflow = ROOT / 'design/partition/reflow-pins.json'
    if reflow.exists():
        # MC04-S7 Revision 5: every pre-move K pose of reflow-pins.json is an obstacle (the reflow pins, the swapped
        # clusters, the evicted pins' re-placed poses and the protection diodes), in place of an evicted pin's slot
        for r in json.loads(reflow.read_text())['pins']:
            if r['board'] == 'K' and r['ref'] not in moved:
                k_rows[r['ref']] = r
    covered = header_conflicts('K', {'K': k_rows}, pc['headers'], io['physical_packages'])
    grids = {s: Grid('K', s, spec['outline']) for s in ('F.Cu', 'B.Cu')}
    for ref, r in k_rows.items():
        if ref not in covered:
            for s in (('F.Cu', 'B.Cu') if through_hole(r['footprint']) else (r['side'],)):
                grids[s].fill(r['courtyard_mm'], gap)  # the floorplan's hits() keeps the gap on every side
    for h in pc['headers']:
        if h['board'] == 'K':
            grids[h['side']].fill(h['land_courtyard_mm'], gap)
    for a in pc['K_service_apertures']:
        for g in grids.values():
            g.fill(a['box_mm'], gap)
    for x, y in spec['supports_mm']:
        for g in grids.values():
            g.fill([x - 1.6, y - 1.6, x + 1.6, y + 1.6], gap)
    for res in spec.get('reserves', []):
        for s in res['sides']:
            grids[s].fill(res['rect'], 0)
    out = {}
    pk = {p['ref']: p for p in io['physical_packages']}
    for b in reloc['blocks']:
        ic = front[(b['from_board'], b['ic'])]
        target = (ic['x_mm'], ic['y_mm'])
        rest = [m for m in b['members'] if m != b['ic']]
        bypass = sorted(m for m in rest if owner.get(m) == b['ic'])
        best = None
        # the IC and its bypass capacitors as the floorplan's rigid cluster (bypass_cells), turned to the IC's front
        # rotation; each capacitor's rail pad sits on its supply pad's row
        for side in ('F.Cu', 'B.Cu'):
            for horizontal in (False, True):
                cells = bypass_cells(pk[b['ic']], [pk[m] for m in bypass], side, SHAPES, nets, horizontal)
                theta = ic['rotation_deg']
                parts = []
                for part, angle, pt in cells:
                    px, py = turn(pt, theta)
                    rot = (angle + theta) % 360
                    box = oriented_box(shape(part['footprint']), side, rot)
                    parts.append((part['ref'], px, py, rot, [box[0] + px, box[1] + py, box[2] + px, box[3] + py]))
                env = [min(p[4][0] for p in parts), min(p[4][1] for p in parts), max(p[4][2] for p in parts), max(p[4][3] for p in parts)]
                trial = Grid.__new__(Grid)
                trial.__dict__.update(grids[side].__dict__)
                trial.rows = list(grids[side].rows)
                sc = trial.scale
                masks = []
                for _, _, _, _, bx in parts:
                    dx = math.floor((bx[0] - env[0]) * sc + 1e-8); dy = math.floor((bx[1] - env[1]) * sc + 1e-8)
                    masks.append((dx, dy, math.ceil((bx[2] - env[0] + gap) * sc - 1e-8) - dx, math.ceil((bx[3] - env[1] + gap) * sc - 1e-8) - dy))
                hit = nearest(trial, masks, (round((target[0] + env[0]) * sc), round((target[1] + env[1]) * sc)))
                if hit is None:
                    continue
                _, xx, yy = hit
                x, y = round(xx / sc - env[0], 3), round(yy / sc - env[1], 3)
                d = math.hypot(x - target[0], y - target[1])
                if best is None or d < best[0] - 1e-9:
                    occupy(trial, masks, xx, yy)
                    best = (d, side, trial, x, y, parts)
        if best is None:
            raise ValueError('K block %s: no room for the IC on K' % b['ic'])
        _, side, grid, x, y, parts = best
        grids[side] = grid
        placed = {}
        for ref, px, py, rot, _ in parts:
            placed[ref] = {'x_mm': round(x + px, 3), 'y_mm': round(y + py, 3), 'side': side}
            if ref != b['ic'] and rot != front[(b['from_board'], ref)]['rotation_deg']:
                placed[ref]['rotation_deg'] = rot
        area = lambda m: (lambda s: (s[2] - s[0]) * (s[3] - s[1]))(shape(front[(b['from_board'], m)]['footprint']))  # noqa: E731
        for m in sorted((m for m in rest if m not in bypass), key=lambda m: (-area(m), m)):
            row = front[(b['from_board'], m)]
            rel = oriented_box(shape(row['footprint']), side, row['rotation_deg'])
            q = find(grid, rel, (x, y), gap)
            if q is None:
                raise ValueError('K block %s: no room for %s on %s' % (b['ic'], m, side))
            placed[m] = {'x_mm': q[0], 'y_mm': q[1], 'side': side}
        out[b['ic']] = dict(sorted(placed.items()))
    return reloc, out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--check', action='store_true')
    a = ap.parse_args()
    reloc, out = poses()
    for b in reloc['blocks']:
        b['k_poses'] = out[b['ic']]
    text = json.dumps(reloc, indent=1) + '\n'
    if a.check:
        if RELOCATION.read_text() != text:
            raise SystemExit('K block poses drift')
    else:
        RELOCATION.write_text(text)
    for b in reloc['blocks']:
        ic = b['k_poses'][b['ic']]
        far = max(math.hypot(p['x_mm'] - ic['x_mm'], p['y_mm'] - ic['y_mm']) for p in b['k_poses'].values())
        print(b['ic'], ic, 'farthest member %.2f mm' % far)


if __name__ == '__main__':
    main()
