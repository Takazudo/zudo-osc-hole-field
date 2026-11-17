"""E5 diagnostic attribution only: all blockers, no placement or exchange search."""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[4]
SPEC = Path(__file__).with_name('spec.json')
R1 = ROOT / 'scripts/stack/studies/mc04_r1/study.py'
module = importlib.util.spec_from_file_location('reviewed_r1_scene', R1)
r1 = importlib.util.module_from_spec(module)
module.loader.exec_module(r1)
sg, rp, lg = r1.sg, r1.rp, r1.lg
TARGETS = ('U4524', 'U4526', 'U4527')


def body_category(key, accepted, unresolved, fixed):
    if key in fixed:
        return 'fixed_hardware', 'FIXED_NONEXCHANGEABLE'
    if key in accepted:
        return 'accepted_body', 'UNKNOWN; accepted source placement is not permission to move'
    if key in unresolved:
        return 'unresolved_body', 'UNKNOWN; original body retained as conservative liability'
    return 'stationary_body', 'UNKNOWN; stationary is not permission to move'


def blocker_kind(label):
    if label.startswith('slot of '):
        return 'fixed_slot'
    if label.startswith(('front field of ', 'K field of ')):
        return 'fixed_link_field'
    if 'tail' in label:
        return 'fixed_tail'
    if label.startswith('latch margin of '):
        return 'fixed_latch'
    if label.startswith('fixing keep-out'):
        return 'fixed_fixing'
    return 'fixed_constraint'


class DiagnosticScene:
    def __init__(self, source_scene, accepted, unresolved, fixed):
        self.scene = source_scene
        self.accepted, self.unresolved, self.fixed = set(accepted), set(unresolved), set(fixed)
        self.registry = {}

    def register(self, record):
        encoded = json.dumps(record, sort_keys=True, separators=(',', ':'))
        key = hashlib.sha256(encoded.encode()).hexdigest()
        if key in self.registry and self.registry[key] != record:
            raise ValueError('blocker identity collision')
        self.registry[key] = record
        return key

    def blockers(self, board, fp, dx, dy):
        if board != 'K' or fp['ref'] not in TARGETS:
            raise ValueError('only the three admitted targets may be queried')
        if not all(math.isfinite(v) for v in (dx, dy)) or math.hypot(dx, dy) > 25.0001:
            raise ValueError('diagnostic offset outside retained 25mm domain')
        hits = set()
        scene, field = self.scene, self.scene.field
        own = [[round(v, 4) for v in rp.shift(rect, dx, dy)] for rect in r1.rectangles(fp)]
        other = [[round(v, 4) for v in rp.shift(p['bbox'], dx, dy)] for p in fp['pads']
                 if p['type'] in ('thru_hole', 'np_thru_hole')]
        for face, rects in ((fp['side'], own), ('F' if fp['side'] == 'B' else 'B', other)):
            for rect in rects:
                if not scene.model.inside(board, rect, field.margin):
                    hits.add(self.register({'class': 'fixed_outline', 'board': board, 'face': face,
                        'label': 'retained board outline and margin', 'movability': 'FIXED_NONEXCHANGEABLE'}))
                for obstacle, payload in field.idx[(board, face)].near(rect):
                    if payload[0] == 'body' and payload[1] == (board, fp['ref']):
                        continue  # Exactly one queried body, never its two unresolved peers.
                    collision = (sg.circle_rect_depth(*payload[1], rect) > 1e-9
                                 if payload[0] == 'circle' else sg.inter(rect, obstacle))
                    if not collision:
                        continue
                    record = {'board': board, 'face': face, 'rectangle_mm': obstacle, 'label': payload[2]}
                    if payload[0] == 'body':
                        kind, movable = body_category(payload[1], self.accepted, self.unresolved, self.fixed)
                        record.update({'class': kind, 'ref': payload[1][1], 'movability': movable})
                    else:
                        record.update({'class': blocker_kind(payload[2]), 'movability': 'FIXED_NONEXCHANGEABLE'})
                        if payload[0] == 'circle':
                            record['circle_mm'] = list(payload[1])
                    hits.add(self.register(record))
                grown = sg.grow(rect, field.gap if face == fp['side'] else field.pad_gap)
                index = field.links.get((board, face))
                if index:
                    for obstacle, label in index.near(grown):
                        if sg.inter(grown, obstacle):
                            hits.add(self.register({'class': blocker_kind(label), 'board': board, 'face': face,
                                'rectangle_mm': obstacle, 'label': label, 'movability': 'FIXED_NONEXCHANGEABLE'}))
        return sorted(hits)


def accepted_only_obstruction(hits, registry):
    """Predicate attribution, NOT permission or proof of a legal exchange."""
    records = [registry[key] for key in hits]
    if not records or any(r['class'] != 'accepted_body' for r in records):
        return None
    return sorted({r['ref'] for r in records})


def audit(scene, targets, offsets):
    points = []
    for fp in targets:
        for number, (radius, dx, dy) in enumerate(offsets):
            if radius < 0 or radius > 25:
                raise ValueError('diagnostic radius outside retained domain')
            hits = scene.blockers('K', fp, dx, dy)
            points.append({'target': fp['ref'], 'offset_index': number, 'radius_mm': radius,
                'diagnostic_offset_mm': [dx, dy], 'blocker_ids': hits,
                'all_obstructions_are_named_accepted_bodies': accepted_only_obstruction(hits, scene.registry)})
    return {'diagnostic_points': points, 'blockers': scene.registry,
            'selected_placements': [], 'adopted_placements': [],
            'accepted_body_attribution_scope': 'If non-null, listed bodies account for all current predicate hits at this diagnostic point. Their removal is not performed, authorized, or shown jointly placeable; no improvement over the historical search is implied.'}


def run(root=ROOT):
    spec = json.loads(SPEC.read_text())
    r1.verify_pins(root, spec)
    frozen = json.loads((root / 'scripts/stack/studies/mc04_r1/spec.json').read_text())
    gate = json.loads((root / 'design/stack/geometry/links/link-gate.json').read_text())
    inp = lg.load_inputs(root)
    inp['ci']['boards'], accepted = r1.reconstruct(inp['ci']['boards'], gate['replacement']['footprints'], frozen['replacement'])
    unresolved = {(r['board'], r['ref']) for r in frozen['replacement'] if r['new'] is None}
    if len(accepted) != 412 or len(unresolved) != 26 or not {('K', r) for r in TARGETS} <= unresolved:
        raise ValueError('retained accepted/unresolved target inventory changed')
    model = lg.GateModel(inp, lg.gate_sites(inp))
    source_scene = r1.Scene(SimpleNamespace(model=model, opts=inp['opts']), inp, gate['links'])
    # Identity-backed hardware classification; never infer exchangeability from other categories.
    locked = {r['ref'] for r in inp['raw']['lock']['placements']}
    fixed = {key for key in source_scene.bodies if key[1] in locked}
    for board, refs in model.panel.items():
        fixed.update((board, ref) for ref in refs)
    diag = DiagnosticScene(source_scene, accepted, unresolved, fixed)
    targets = [source_scene.bodies['K', ref] for ref in TARGETS]
    if any(fp['side'] != 'B' for fp in targets):
        raise ValueError('target source face changed')
    companions = {ref: source_scene.bodies['K', ref] for ref in ('C4541', 'C4543', 'C4544')}
    if companions['C4544']['origin'] != [189.2026, 136.8974] or companions['C4544']['side'] != 'B':
        raise ValueError('retained accepted C4544 transform changed')
    if any(('K', ref) in set(accepted) | unresolved for ref in ('C4541', 'C4543')):
        raise ValueError('C4541/C4543 stationary source assumption changed')
    logic = json.loads((root / spec['logic_receipt']).read_text())
    if logic['packages'] != list(TARGETS) or sum(len(v) for v in logic['external_contacts'].values()) != 45:
        raise ValueError('E5 external-contact receipt differs')
    offsets = rp.ring_offsets(.25, 24, 25)
    if len(offsets) != 2401 or len(set(offsets)) != 2401:
        raise ValueError('retained diagnostic domain differs')
    result = audit(diag, targets, offsets)
    result.update({'status': 'BLOCKER_ATTRIBUTION_ONLY', 'source_commit': spec['source_commit'],
        'inputs_sha256': spec['sha256'], 'accepted_transform_count': len(accepted), 'unresolved_liability_count': len(unresolved),
        'target_source_geometry': targets, 'stationary_companion_geometry': companions,
        'external_contacts': logic['external_contacts'], 'logic_receipt': spec['logic_receipt'],
        'comparison_scope': 'Current conservative union includes all 412 accepted transforms and 26 unresolved originals. Each query excludes only its own target; the other two E5 targets remain. Historical replace_all removed all 438 initially, then cumulatively added accepted moves in order. This diagnostic is not that historical search state; removing these three originals alone cannot demonstrate new freedom over that earlier removal baseline.',
        'limits': 'Exactly 3*2401 own-face/own-orientation diagnostic points; no rotations, face flips, link/panel movement, candidate adoption, joint exchange search, routing, native, timing acceptance, DRC/fill or manufacturing.'})
    r1.verify_pins(root, spec)
    return result


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output.exists() or args.output.is_symlink():
        parser.error('output already exists; no attempt consumed')
    if not args.output.resolve().is_relative_to((ROOT / '.circuit-cache').resolve()):
        parser.error('output must be in this worktree ignored cache')
    args.output.parent.mkdir(parents=True, exist_ok=True)
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


if __name__ == '__main__':
    main()
