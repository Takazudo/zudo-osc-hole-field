#!/usr/bin/env python3
"""Compose retained E16 deltas and write disposable, unfilled KiCad sources.

No routing, solving, native call or acceptance occurs here. t2 and KB P1 remain
separate records. Original candidate05 bytes are preserved except insertion
before the root closing parenthesis. Process requirements remain a sidecar.
"""
import argparse
import copy
import gzip
import hashlib
import json
import math
import re
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = next((p for p in HERE.parents if (p / 'circuit/WORKFLOW.md').is_file()), HERE)
LAYERS = ['F.Cu', 'In1.Cu', 'In2.Cu', 'In3.Cu', 'In4.Cu', 'B.Cu']
NET_LAYER = {'AGND': 'In1.Cu', '+5V': 'In2.Cu', '-12V': 'In3.Cu', '+12V': 'In4.Cu'}
OFFSET = [100., 50.]
SEALS = {'input_sha256', 'parent_sha256', 'output_sha256', 'elapsed_seconds', 'peak_KiB', 'graph_sha256'}
NS = uuid.UUID('e16acce5-0000-5000-8000-000000000242')
UUID_RE = re.compile(r'\(uuid\s+"([^"]+)"\)')


def need(condition, message):
    if not condition:
        raise ValueError(message)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'), allow_nan=False)


def digest(value):
    return hashlib.sha256(canonical(value).encode()).hexdigest()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    path = Path(path)
    return json.loads(gzip.decompress(path.read_bytes()) if path.suffix == '.gz' else path.read_text())


def identity(value):
    need(isinstance(value, str), 'identity must be a UUID string')
    need(str(uuid.UUID(value)) == value, 'noncanonical UUID')
    return value


def number(value, positive=False):
    need(type(value) in (int, float) and math.isfinite(value), 'finite numeric geometry required')
    need(not positive or value > 0, 'positive geometry required')
    return value


def xy(point):
    need(isinstance(point, list) and len(point) == 2, 'two-dimensional point required')
    return ' '.join(f'{number(v) + d:.9f}' for v, d in zip(point, OFFSET))


def validate_addition(obj, pads, epoch):
    allowed = {'id', 'kind', 'net', 'layers', 'access_for_pad', 'epoch', 'method',
               'path_mm', 'width_mm', 'center_mm', 'diameter_mm', 'drill_mm',
               'process', 'via_in_pad', 'pilot_start_object', 'pilot_end_object', 'via_type', 'transition_id'}
    need(set(obj) <= allowed, 'unsupported addition fields: ' + ','.join(sorted(set(obj) - allowed)))
    identity(obj['id'])
    need(obj.get('epoch') == epoch, 'addition epoch mismatch')
    need(obj.get('net') in NET_LAYER, 'addition is not on a reviewed rail')
    pad = pads.get(obj.get('access_for_pad'))
    need(pad is not None and pad['net'] == obj['net'], 'exact same-net access pad required')
    need(not any(k in obj for k in ('source_span', 'padstack', 'remove_unused_layers', 'keep_end_layers')), 'unsupported copper-stack policy')
    if obj['kind'] == 'segment':
        need(obj['layers'] in (['F.Cu'], ['B.Cu']), 'reviewed access segment must use one outer face')
        pts = obj['path_mm']
        need(isinstance(pts, list) and len(pts) == 2, 'one straight segment required')
        for p in pts:
            xy(p)
        need(pts[0] != pts[1], 'zero-length segment')
        number(obj['width_mm'], positive=True)
    elif obj['kind'] == 'via':
        need(epoch == 'E16', 'P1 may only add face segments')
        need(obj['layers'] == LAYERS and obj.get('via_type', 'through') == 'through', 'only standard through vias supported')
        xy(obj['center_mm'])
        number(obj['diameter_mm'], positive=True)
        number(obj['drill_mm'], positive=True)
        need(obj['diameter_mm'] > obj['drill_mm'], 'via requires positive annulus')
    else:
        raise ValueError('unsupported addition kind ' + str(obj['kind']))


def compose(board, normalized, spans, reference, pilot=None):
    """Each retained span exactly once; original normalized objects stay an exact prefix."""
    need(board in ('KA', 'KB') and normalized.get('board') == board, 'board mismatch')
    need(normalized.get('schema') == 'e16-normalized-board-v1', 'normalized epoch mismatch')
    need(normalized.get('coordinate_offset_mm') == OFFSET, 'coordinate offset mismatch')
    base = normalized['objects']
    stripped = {k: v for k, v in normalized.items() if k not in SEALS}
    actual = {'objects': len(base), 'loads': len(normalized['loads']), 'content_sha256': digest(stripped)}
    need(actual == reference, 'normalized base differs from retained content lock')
    ids = [o['id'] for o in base]
    need(len(ids) == len(set(ids)), 'duplicate base identity')
    seen = set(ids)
    pads = {o['id']: o for o in base if o['kind'] == 'pad'}
    additions = []
    need(len(spans) == 2, 'exactly r1-r3 and r4-t2 spans required')
    for span in spans:
        need(isinstance(span, list) and span, 'empty or malformed retained delta')
        for obj in span:
            validate_addition(obj, pads, 'E16')
            need(obj['id'] not in seen, 'duplicate or reused addition identity')
            seen.add(obj['id'])
            additions.append(copy.deepcopy(obj))
    byid = {o['id']: o for o in base + additions}
    for obj in additions:
        if 'transition_id' in obj:
            transition = byid.get(obj['transition_id'])
            need(transition is not None and transition['kind'] in ('via', 'pad') and transition['net'] == obj['net'],
                 'transition must bind exact same-net existing copper')
    out = {k: copy.deepcopy(v) for k, v in normalized.items() if k != 'objects' and k not in SEALS}
    out['objects'] = copy.deepcopy(base) + additions
    if pilot is not None:
        need(board == 'KB' and len(pilot) == 3, 'only the separately labeled three-segment KB P1 is supported')
        for obj in pilot:
            validate_addition(obj, pads, 'E16-P1')
            need(obj['id'] not in seen, 'duplicate P1 identity')
            seen.add(obj['id'])
            out['objects'].append(copy.deepcopy(obj))
    return out


def serialize_object(obj):
    ident, net = identity(obj['id']), json.dumps(obj['net'])
    if obj['kind'] == 'segment':
        a, b = obj['path_mm']
        return f'(segment (start {xy(a)}) (end {xy(b)}) (width {obj["width_mm"]:.9f}) (layer {json.dumps(obj["layers"][0])}) (net {net}) (uuid "{ident}"))'
    return f'(via (at {xy(obj["center_mm"])}) (size {obj["diameter_mm"]:.9f}) (drill {obj["drill_mm"]:.9f}) (layers "F.Cu" "B.Cu") (net {net}) (uuid "{ident}"))'


def serialize_zones(board, outline):
    """Unfilled solid-connection zones; native fill and obstacle policy are separate checks."""
    need(isinstance(outline, list) and len(outline) >= 3, 'reviewed outline polygon required')
    pts = ' '.join(f'(xy {xy(p)})' for p in outline)
    rows = []
    for net, layer in NET_LAYER.items():
        ident = str(uuid.uuid5(NS, f'materialize:{board}:E16:zone:{net}:{layer}'))
        text = (f'(zone (net {json.dumps(net)}) (layer "{layer}") (uuid "{ident}") '
                '(hatch edge .5) (connect_pads yes (clearance .25)) (min_thickness .25) '
                '(fill yes (thermal_gap .25) (thermal_bridge_width .25)) '
                f'(polygon (pts {pts})))')
        rows.append((ident, text))
    return rows


def materialize(board, candidate, base, composed, outline):
    need(composed['objects'][:len(base['objects'])] == base['objects'], 'source prefix changed')
    need(candidate.lstrip().startswith('(kicad_pcb'), 'not a KiCad PCB')
    end = re.search(r'\)\s*$', candidate)
    need(end is not None, 'missing root closing parenthesis')
    old_ids = UUID_RE.findall(candidate)
    need(len(old_ids) == len(set(old_ids)), 'candidate UUIDs collide')
    for net in NET_LAYER:
        need(f'(net {json.dumps(net)})' in candidate, 'candidate lacks reviewed net ' + net)
    for layer in LAYERS:
        need(re.search(r'\(\d+\s+' + re.escape(json.dumps(layer)) + r'\s+signal\)', candidate), 'candidate lacks required copper layer ' + layer)
    additions = composed['objects'][len(base['objects']):]
    zones = serialize_zones(board, outline)
    new_ids = [o['id'] for o in additions] + [i for i, _ in zones]
    need(len(new_ids) == len(set(new_ids)) and not set(new_ids) & set(old_ids), 'native UUID collision')
    blocks = [serialize_object(o) for o in additions] + [s for _, s in zones]
    text = candidate[:end.start()] + '\n' + '\n'.join(blocks) + '\n' + candidate[end.start():]
    # The exact byte regions prove preservation of all original footprints,
    # retained copper, rule areas, edge cuts, layers and setup without reserialization.
    need(text[:end.start()] == candidate[:end.start()] and text.endswith(candidate[end.start():]), 'candidate bytes changed')
    metadata = {
        'candidate05_sha256': hashlib.sha256(candidate.encode()).hexdigest(),
        'preserved_native_uuid_content_sha256': digest(sorted(old_ids)),
        'preserved_source_objects_content_sha256': digest(base['objects']),
        'materialized_source_objects_content_sha256': digest(composed['objects']),
        'preserved_candidate_uuid_count': len(old_ids), 'added_objects': len(additions),
        'added_identity_map': [{'normalized_id': o['id'], 'native_uuid': o['id'], 'kind': o['kind'],
                                'access_for_pad': o['access_for_pad']} for o in additions],
        'unfilled_zone_ids': [i for i, _ in zones], 'coordinate_offset_mm': OFFSET,
        'terminal_identity_map': [{'normalized_id': o['id'], 'native_pad_uuid': o['source_pad_uuid'], 'source_ref': o.get('source_ref')}
                                  for o in base['objects'] if o.get('source_pad_uuid')],
        'rail_physical_pad_map': [{'source_id': o['id'], 'native_pad_uuid': o.get('source_pad_uuid', o['id']),
                                  'ref': o.get('source_ref') or o.get('ref'), 'pad': o.get('pad') or '1', 'net': o['net']}
                                 for o in base['objects'] if o['kind'] == 'pad' and o['net'] in NET_LAYER],
        'process_requirements': [{'id': o['id'], **{k: o[k] for k in ('process', 'via_in_pad') if k in o}}
                                 for o in composed['objects'] if o['kind'] == 'via' and ('process' in o or o.get('via_in_pad'))],
        'limits': ['Unfilled zones are not electrical conductance or native connectivity evidence.',
                   'Filled/capped lands and via-in-pad process qualification is not encoded by standard via geometry.',
                   'Native refill need not equal the analytic clipped sheets; all differences remain evidence.',
                   'No selective unused-layer annulus removal or staged/blind/buried via is supported.'],
        'native_calls': 0, 'accepted': False,
    }
    return text, metadata


def authenticated_pilot(ev):
    pilot = load(ev / 'pilot/KB-p1/pilot-result.json')
    seal_path = ev / 'pilot/KB-seal.json'
    seal = load(seal_path)
    preflight = ev / 'pilot' / seal['preflight']
    need(pilot['seal_sha256'] == sha(seal_path) and seal['preflight_sha256'] == sha(preflight), 'P1 seal mismatch')
    need(seal['geometry_review']['verdict'] == 'PASS', 'P1 geometry review not PASS')
    review = ev / 'pilot' / seal['geometry_review']['record']
    need(sha(review) == seal['geometry_review']['record_sha256'], 'P1 review bytes differ')
    need(pilot['board'] == seal['board'] == 'KB' and pilot['net'] == seal['net'] == '+5V', 'P1 board/net mismatch')
    key = f'pilot-p1:KB:{seal["target"]["pad_id"]}'
    expected = [{'id': str(uuid.uuid5(NS, f'{key}:{n}')), 'kind': 'segment', 'net': seal['net'],
                 'layers': [seal['face']], 'path_mm': [u, v], 'width_mm': seal['width_mm'],
                 'access_for_pad': seal['target']['pad_id'], 'epoch': 'E16-P1', 'method': 'pilot_orphan_component_feed',
                 'pilot_start_object': seal['start_object'], 'pilot_end_object': seal['end_object']}
                for n, (u, v) in enumerate(zip(seal['path_mm'], seal['path_mm'][1:]))]
    need(pilot['added_objects'] == expected, 'P1 geometry differs from sealed path')
    return expected, [ev / 'pilot/KB-p1/pilot-result.json', seal_path, preflight, review]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--board', choices=['KA', 'KB'], required=True)
    p.add_argument('--candidate', type=Path, required=True)
    p.add_argument('--normalized', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True, help='fresh directory outside the repository')
    p.add_argument('--evidence', type=Path, default=HERE / 'evidence/e16')
    p.add_argument('--include-kb-p1', action='store_true')
    a = p.parse_args()
    out = a.output.resolve()
    need(out.is_absolute() and not out.exists() and not out.is_relative_to(ROOT), 'fresh output outside repository required')
    need(not a.include_kb_p1 or a.board == 'KB', 'P1 is KB only')
    ev = a.evidence.resolve()
    descriptor_path = ev / 'continuation-20261013/native-descriptor.json'
    descriptor = load(descriptor_path)
    pins = descriptor['candidate']['boards'][a.board]
    index_path = ev / 'index.json'
    terminals_path = a.candidate.parent / 'terminals.json'
    need(sha(terminals_path) == load(index_path)['candidate05']['terminals.json'], 'candidate terminal process metadata hash mismatch')
    terminal_requirements = [t for t in load(terminals_path) if t['board'] == a.board]
    need(len(terminal_requirements) == 6 and all(len(t['vias']) == 25 for t in terminal_requirements), 'six capped terminal fields required')
    delta_paths = [ev / f'{a.board}-access-delta.json.gz', ev / f'{a.board}-access-delta-r4-t2.json.gz']
    need(sha(a.candidate) == pins['candidate05_pcb'], 'candidate05 PCB hash mismatch')
    for path, key in zip(delta_paths, ['retained_delta_r1_r3_gz', 'retained_delta_r4_t2_gz']):
        need(sha(path) == pins[key], 'retained delta hash mismatch')
    reference_path = ev / f'replay/20261013-r4-t2/{a.board}-replay-comparison.json'
    reference = load(reference_path)['checks']['normalized_objects']
    design_path = HERE / 'evidence/board-access-design.json'
    outline = load(design_path)['layer_construction']['outline_inset_0p6mm_polygon_mm']
    rule_paths = [ROOT / 'boards/osc-core/osc-core.kicad_pro', ROOT / 'boards/osc-core/osc-core.kicad_dru']
    watched = [a.candidate, a.normalized, descriptor_path, reference_path, design_path, Path(__file__), index_path, terminals_path, *delta_paths, *rule_paths]
    pilot = None
    if a.include_kb_p1:
        pilot, pilot_paths = authenticated_pilot(ev)
        watched += pilot_paths
    seals = {str(q.resolve()): sha(q) for q in watched}
    base = load(a.normalized)
    source = compose(a.board, base, [load(q) for q in delta_paths], reference)
    records = [('t2', source)]
    if pilot is not None:
        records.append(('p1', compose(a.board, base, [load(q) for q in delta_paths], reference, pilot)))
    rendered = [(label, obj, *materialize(a.board, a.candidate.read_text(), base, obj, outline)) for label, obj in records]
    need(all(sha(Path(q)) == h for q, h in seals.items()), 'input changed during materialization')
    out.mkdir(parents=True)
    for label, obj, pcb, metadata in rendered:
        stem = f'{a.board}-{label}'
        (out / f'{stem}-source.json').write_text(canonical(obj) + '\n')
        (out / f'{stem}.kicad_pcb').write_text(pcb)
        for rule in rule_paths:
            (out / (stem + rule.suffix)).write_bytes(rule.read_bytes())
        metadata.update(schema='e16-source-materialization-v1', board=a.board, round=label, input_sha256=seals,
                        terminal_process_requirements=terminal_requirements,
                        output_sha256={q.name: sha(q) for q in sorted(out.glob(stem + '*'))})
        (out / f'{stem}-materialization.json').write_text(json.dumps(metadata, indent=1) + '\n')
    need(all(sha(Path(q)) == h for q, h in seals.items()), 'input changed while outputs were written')
    print(canonical({'board': a.board, 'records': [r[0] for r in records], 'output': str(out), 'native_calls': 0, 'accepted': False}))


if __name__ == '__main__':
    main()
