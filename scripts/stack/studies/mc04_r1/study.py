"""DS-135 offline room-only pilot. Never writes canonical geometry or invokes KiCad."""
import argparse
import copy
import hashlib
import json
import math
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'scripts/stack/geometry'))
import stackgeom as sg
import links_gate as lg
import links_gate_part2 as rp

PAIR = ('U4324', 'C4341')
SPEC = Path(__file__).with_name('spec.json')


class AdmissionError(ValueError):
    pass


def verify_pins(root, spec):
    for name, expected in spec['sha256'].items():
        if sg.sha256_file(root / name) != expected:
            raise AdmissionError('stale input: ' + name)


def identity_table(report):
    return {key: [r for r in report[key] if r['ref'] in PAIR]
            for key in ('physical_packages', 'package_units')}


def verify_identity(report, expected):
    actual = identity_table(report)
    if actual != expected:
        raise AdmissionError('pair identity/unit/pin-net correspondence changed')
    rows = {r['ref']: r for r in actual['physical_packages']}
    if set(rows) != set(PAIR) or rows['C4341']['decouples_ref'] != 'U4324':
        raise AdmissionError('missing/wrong declared companion')


def transformed(fp, row):
    out = copy.deepcopy(fp)
    dx, dy = row['shift_mm']
    def move(rect):
        if row['turned']:
            rect = rp.turn(rect, fp['origin'])
        return [round(v, 4) for v in rp.shift(rect, dx, dy)]
    if out['courtyard']:
        out['courtyard'] = move(out['courtyard'])
    for p in out['pads']:
        p['bbox'] = move(p['bbox'])
        # Center is only metadata after reconstruction; derive from the transformed bbox.
        p['center'] = sg.centre(p['bbox'])
    out['origin'] = [round(fp['origin'][0] + dx, 4), round(fp['origin'][1] + dy, 4)]
    out['side'] = row['new_face']
    out['angle'] = (fp['angle'] - (90 if row['turned'] else 0)) % 360
    if out['origin'] != row['new'] or out['courtyard'] != row['new_courtyard']:
        raise AdmissionError('accepted transformation does not reproduce ' + fp['ref'])
    return out


def reconstruct(boards, rows, expected_rows):
    if rows != expected_rows:
        raise AdmissionError('missing/changed accepted move or unresolved liability')
    out = copy.deepcopy(boards)
    by = {(b, f['ref']): f for b, fps in out.items() for f in fps}
    if len(by) != sum(map(len, out.values())):
        raise AdmissionError('duplicate footprint identity')
    for fp in by.values():
        geometry = [fp['origin']] + ([fp['courtyard']] if fp['courtyard'] else []) + [p['bbox'] for p in fp['pads']]
        if not all(math.isfinite(v) for r in geometry for v in r):
            raise AdmissionError('nonfinite source geometry')
        if any(r[0] >= r[2] or r[1] >= r[3] for r in geometry[1:]):
            raise AdmissionError('invalid rectangle')
    accepted = []
    for row in rows:
        key = row['board'], row['ref']
        if key not in by:
            raise AdmissionError('missing source footprint: ' + str(key))
        fp = by[key]
        if fp['origin'] != row['old'] or fp['side'] != row['face'] or fp['lib'] != row['package']:
            raise AdmissionError('source placement disagrees: ' + str(key))
        if row['new'] is not None:
            moved = transformed(fp, row)
            fp.clear()
            fp.update(moved)
            accepted.append(key)
    return out, accepted


def rectangles(fp):
    if not fp['courtyard'] or not fp['pads']:
        raise AdmissionError('incomplete courtyard/pads for ' + fp['ref'])
    return [fp['courtyard']] + [p['bbox'] for p in fp['pads']]


def obstacle_rect(rect, growth):
    """Match retained Obstacles._add / Field.add four-decimal storage exactly.

    This is the existing geometry grid, not an extra clearance epsilon. Keep
    candidate-to-link screens on their unchanged retained Field predicates.
    """
    return [round(value, 4) for value in sg.grow(rect, growth)]


class Scene:
    """Reuse retained outline/circle/link predicates; include every own-face pad too.

    Only the named pair can be excluded. Each indexed footprint has an explicit
    owner, so auditing an accepted move excludes itself and nothing else.
    """
    def __init__(self, ctx, inp, links):
        self.field = rp.Field(ctx, inp, links, set())
        self.model = ctx.model
        self.bodies = {(b, f['ref']): f for b, fps in inp['ci']['boards'].items() for f in fps}
        # Replace only footprint entries with complete body/pad envelopes. Keep
        # every source forbidden region and retained link field verbatim.
        for key, ix in self.field.idx.items():
            clean = sg.RectIndex()
            for rect, payload in ix.items:
                if payload[0] != 'fp':
                    clean.add(rect, payload)
            self.field.idx[key] = clean
        om = inp['ci']['parameters']['obstacle_model']
        for board in rp.SCOPE_BOARDS:
            # Preserve exact retained hole, through-hole and courtyard growth.
            obs = sg.Obstacles(inp['ci']['boards'][board], om,
                               drop=frozenset(self.model.dropped.get(board, ())))
            for face in 'FB':
                for rect, (ref, kind) in obs.index[face].items:
                    self.field.idx[(board, face)].add(rect, ('body', (board, ref), kind))
            # Complete own-face pads are additional conservative blockers,
            # including pads beyond a courtyard and footprints without one.
            for fp in inp['ci']['boards'][board]:
                if fp['ref'] in self.model.dropped.get(board, ()):
                    continue
                for p in fp['pads']:
                    self.field.idx[(board, fp['side'])].add(obstacle_rect(p['bbox'], self.field.gap),
                        ('body', (board, fp['ref']), 'own-face pad'))

    def violations(self, fp, dx, dy, exclude):
        if not set(exclude) <= set(PAIR):
            raise AdmissionError('unrelated obstacle removal')
        return self._violations('K', fp, dx, dy, {('K', r) for r in exclude})

    def _violations(self, board, fp, dx, dy, exclude):
        hits = set()
        if math.hypot(dx, dy) > 25.0001:
            hits.add('displacement cap')
        own = [[round(v, 4) for v in rp.shift(r, dx, dy)] for r in rectangles(fp)]
        other = [[round(v, 4) for v in rp.shift(p['bbox'], dx, dy)] for p in fp['pads']
                 if p['type'] in ('thru_hole', 'np_thru_hole')]
        for face, rects in ((fp['side'], own), ('F' if fp['side'] == 'B' else 'B', other)):
            for rect in rects:
                if not self.model.inside(board, rect, self.field.margin):
                    hits.add('outline')
                for obstacle, payload in self.field.idx[(board, face)].near(rect):
                    if payload[0] == 'body' and payload[1] in exclude:
                        continue
                    if payload[0] == 'circle':
                        if sg.circle_rect_depth(*payload[1], rect) > 1e-9:
                            hits.add(payload[2])
                    elif sg.inter(rect, obstacle):
                        hits.add(payload[2] + (':' + payload[1][1] if payload[0] == 'body' else ''))
                grown = sg.grow(rect, self.field.gap if face == fp['side'] else self.field.pad_gap)
                index = self.field.links.get((board, face))
                if index:
                    for obstacle, label in index.near(grown):
                        if sg.inter(grown, obstacle):
                            hits.add(label)
        return sorted(hits)

    def audit(self, accepted):
        errors = []
        for key in accepted:
            hits = self._violations(*key[:1], self.bodies[key], 0, 0, {key})
            if hits:
                errors.append({'board': key[0], 'ref': key[1], 'violations': hits})
        return errors


def mutual_conflict(pair, gap):
    a, b = pair
    return a['side'] == b['side'] and any(sg.inter(r, obstacle_rect(s, gap))
        for r in rectangles(a) for s in rectangles(b))


def search(scene, pair, offsets=None):
    """Cheap cause first, then at most one finite pair pass. No unchanged retry."""
    if tuple(f['ref'] for f in pair) != PAIR:
        raise AdmissionError('wrong pair')
    if mutual_conflict(pair, scene.field.gap):
        return {'status': 'INCONSISTENT_PAIR', 'causal_count': 0, 'group_count': 0}
    offsets = rp.ring_offsets(.25, 24, 25) if offsets is None else list(offsets)
    causal = []
    tally = {}
    count = 0
    for radius, dx, dy in offsets:
        if radius > 25 or math.hypot(dx, dy) > 25.0001:
            raise AdmissionError('candidate exceeds 25 mm')
        count += 1
        without = scene.violations(pair[0], dx, dy, PAIR)
        with_companion = scene.violations(pair[0], dx, dy, (PAIR[0],))
        for hit in without:
            tally[hit] = tally.get(hit, 0) + 1
        if not without and with_companion:
            causal.append((radius, dx, dy))
    result = {'status': 'NO_NEW_OPPORTUNITY', 'causal_count': count,
              'causal_opportunities': len(causal), 'group_count': 0, 'violations': tally}
    if not causal:
        return result
    # The full rigid domain is evaluated once only after causal novelty is shown.
    for radius, dx, dy in offsets:
        result['group_count'] += 1
        hits = sorted(set(h for f in pair for h in scene.violations(f, dx, dy, PAIR)))
        for hit in hits:
            tally[hit] = tally.get(hit, 0) + 1
        if not hits:
            result.update(status='ROOM_WITNESS_ONLY', displacement_mm=[dx, dy], radius_mm=radius,
                          positions={f['ref']: {'old': f['origin'],
                          'new': [round(f['origin'][0]+dx,4), round(f['origin'][1]+dy,4)],
                          'face': f['side'], 'angle': f['angle']} for f in pair})
            return result
    result['status'] = 'NO_RIGID_PAIR_FIT'
    return result


def liability_ledger(scene, rows, spec):
    """Name every canonical unresolved package; distinguish the 25 frozen peers."""
    entries = []
    for row in rows:
        if row['new'] is not None:
            continue
        key = row['board'], row['ref']
        entries.append({'board': key[0], 'ref': key[1],
                        'disposition': 'room-only target; still canonically unresolved' if key == ('K', PAIR[0])
                                       else 'frozen unresolved obstacle',
                        'geometry': copy.deepcopy(scene.bodies[key]),
                        'provenance': {'engineering_commit': spec['engineering_commit'],
                                       'replacement_path': 'design/stack/geometry/links/link-gate.json',
                                       'replacement_sha256': spec['sha256']['design/stack/geometry/links/link-gate.json'],
                                       'source_board_path': sg.BOARD_FILES[key[0]],
                                       'source_board_sha256': spec['sha256'][sg.BOARD_FILES[key[0]]]},
                        'retained_replacement': copy.deepcopy(row)})
    return entries


def run(root=ROOT):
    spec = json.loads(SPEC.read_text())
    verify_pins(root, spec)
    report = json.loads((root / 'design/reports/io-partition.json').read_text())
    verify_identity(report, spec['identity'])
    doc = json.loads((root / 'design/stack/geometry/links/link-gate.json').read_text())
    inp = lg.load_inputs(root)
    inp['ci']['boards'], accepted = reconstruct(inp['ci']['boards'], doc['replacement']['footprints'], spec['replacement'])
    if len(accepted) != 412 or len(spec['replacement']) - len(accepted) != 26:
        raise AdmissionError('accepted/unresolved count changed')
    model = lg.GateModel(inp, lg.gate_sites(inp))
    ctx = SimpleNamespace(model=model, opts=inp['opts'])
    scene = Scene(ctx, inp, doc['links'])
    # Frozen overlaps remain a conservative union, not an assembled-layout claim.
    overlaps = scene.audit(accepted)
    result = search(scene, [scene.bodies['K', r] for r in PAIR])
    result['frozen_accepted_overlap_observations'] = overlaps
    result['canonical_unresolved_ledger'] = liability_ledger(scene, spec['replacement'], spec)
    result['frozen_other_unresolved'] = [{'board': r['board'], 'ref': r['ref']}
        for r in result['canonical_unresolved_ledger'] if r['disposition'] == 'frozen unresolved obstacle']
    verify_pins(root, spec)
    result.update(engineering_commit=spec['engineering_commit'], inputs_sha256=spec['sha256'],
                  accepted_moves=len(accepted), unresolved_liabilities=26,
                  scope='Room-only candidate; not routing, electrical acceptance, Gate A, adoption or manufacturing')
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    # Results stay in the local ignored cache; never replace canonical output.
    cache = (ROOT / '.circuit-cache').resolve()
    if not args.output.resolve().is_relative_to(cache):
        parser.error('output must be inside this worktree .circuit-cache')
    if args.output.exists() or args.output.is_symlink():
        parser.error('output already exists; refusing to consume an attempt')
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Reserve exclusively BEFORE analysis, including protection against a race.
    with args.output.open('x') as stream:
        try:
            result = run()
        except Exception as exc:
            json.dump({'status': 'ADMISSION_OR_EXECUTION_FAILED', 'error': str(exc)}, stream)
            stream.write('\n')
            raise
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(result['status'])
    return 0 if result['status'] in ('ROOM_WITNESS_ONLY', 'NO_NEW_OPPORTUNITY', 'NO_RIGID_PAIR_FIT') else 1


if __name__ == '__main__':
    sys.exit(main())
