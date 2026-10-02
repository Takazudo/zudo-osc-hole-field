"""Apply source-defined reference positions without rewriting any other PCB bytes.

This is an annotation stage for a source-bound, unrouted P candidate. It is not
an electrical or physical acceptance gate. Run with the pinned KiCad oracle.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.pcbgen.uuid_tools import REF_RE, replace_spans, top_level_spans
from scripts.pcbgen.placement_geometry import Box, inside_outline


def reference_fields(text):
    result = {}
    for start, end in top_level_spans(text):
        footprint = text[start:end]
        if not footprint.startswith('(footprint '):
            continue
        match = REF_RE.search(footprint)
        if match is None or match.group(1) in result:
            raise ValueError('One unique reference required per footprint')
        spans = [(a, b) for a, b in top_level_spans(footprint)
                 if REF_RE.match(footprint[a:b])]
        if len(spans) != 1:
            raise ValueError('Exactly one reference field required')
        a, b = spans[0]
        result[match.group(1)] = (start+a, start+b, footprint[a:b])
    return result


def transplant(original, native, selected):
    before, after = reference_fields(original), reference_fields(native)
    if set(before) != set(after) or not set(selected) <= set(before):
        raise ValueError('Reference inventory changed')
    result = replace_spans(original, [(before[r][0], before[r][1], after[r][2])
                                     for r in selected])
    def redact(text):
        fields = reference_fields(text)
        return replace_spans(text, [(fields[r][0], fields[r][1], '<REFERENCE>')
                                    for r in selected])
    if redact(result) != redact(original):
        raise ValueError('Non-reference board bytes changed')
    return result


def apply(board_path, policy_path, output, check=False):
    import pcbnew
    board_path, policy_path, output = map(Path, (board_path, policy_path, output))
    if board_path.resolve() == output.resolve():
        raise ValueError('Annotation output must be separate from the bare input')
    if output.exists() and not check:
        raise ValueError('Fresh output required; use --check to verify existing output')
    raw, policy_bytes = board_path.read_bytes(), policy_path.read_bytes()
    policy = json.loads(policy_bytes)
    sha = lambda data: hashlib.sha256(data).hexdigest()
    if type(policy['schema_version']) is not int or policy['schema_version'] != 1 or policy['board_id'] != 'osc-control':
        raise ValueError('Exact P annotation policy required')
    if sha(raw) != policy['bare_board_sha256']:
        raise ValueError('Bare board differs from the reviewed source')
    sources = {path: (ROOT/path).read_bytes() for path in policy['source_sha256']}
    if any(sha(data) != policy['source_sha256'][path] for path, data in sources.items()):
        raise ValueError('Annotation source binding changed')
    definition = json.loads(sources[policy['definition']])
    if definition['board_id'] != policy['board_id']:
        raise ValueError('Annotation definition differs')
    style = policy['style']
    if style != {'text_size_mm': 1.0, 'stroke_mm': .15,
                 'clearance_mm': .15, 'edge_clearance_mm': .25}:
        raise ValueError('Reviewed 1 mm reference style required')
    board = pcbnew.LoadBoard(str(board_path))
    def rect(native):
        return Box(pcbnew.ToMM(native.GetLeft())-100,
                   pcbnew.ToMM(native.GetTop())-50,
                   pcbnew.ToMM(native.GetRight())-100,
                   pcbnew.ToMM(native.GetBottom())-50)
    obstacles = {pcbnew.F_SilkS: [], pcbnew.B_SilkS: []}
    refs = {}
    for footprint in board.GetFootprints():
        field = footprint.Reference()
        if field.IsVisible() and field.GetLayer() in obstacles:
            refs[footprint.GetReference()] = field
        front = footprint.GetLayer() == pcbnew.F_Cu
        side = pcbnew.F_SilkS if front else pcbnew.B_SilkS
        courtyard = footprint.GetCourtyard(pcbnew.F_CrtYd if front else pcbnew.B_CrtYd)
        if courtyard.OutlineCount():
            obstacles[side].append(rect(courtyard.BBox()))
        for pad in footprint.Pads():
            for silk, mask in ((pcbnew.F_SilkS, pcbnew.F_Mask), (pcbnew.B_SilkS, pcbnew.B_Mask)):
                if pad.GetLayerSet().Contains(mask):
                    obstacles[silk].append(rect(pad.GetBoundingBox()))
        for item in footprint.GraphicalItems():
            if item.GetLayer() in obstacles:
                obstacles[item.GetLayer()].append(rect(item.GetBoundingBox()))
    for item in board.GetDrawings():
        if item.GetLayer() in obstacles:
            obstacles[item.GetLayer()].append(rect(item.GetBoundingBox()))
    if set(refs) != set(policy['references']) or len(refs) != 418:
        raise ValueError('Complete 418 visible source references required')
    for ref, pose in sorted(policy['references'].items()):
        if set(pose) != {'x_mm', 'y_mm', 'rotation_deg'} or any(
                type(value) not in (int, float) or not math.isfinite(value) for value in pose.values()):
            raise ValueError('Finite complete reference pose required')
        if pose['rotation_deg'] not in (0, 90):
            raise ValueError('Only reviewed horizontal/vertical reference orientations allowed')
        field = refs[ref]
        field.SetTextSize(pcbnew.VECTOR2I(pcbnew.FromMM(1), pcbnew.FromMM(1)))
        field.SetTextThickness(pcbnew.FromMM(.15))
        field.SetTextAngle(pcbnew.EDA_ANGLE(pose['rotation_deg'], pcbnew.DEGREES_T))
        field.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(pose['x_mm']+100),
                                         pcbnew.FromMM(pose['y_mm']+50)))
        box = rect(field.GetBoundingBox())
        if not inside_outline(box, definition['outline'], .25):
            raise ValueError('Reference crosses board edge: '+ref)
        if any(box.intersects(other, .15) for other in obstacles[field.GetLayer()]):
            raise ValueError('Reference intersects body, pad, silk or another reference: '+ref)
        obstacles[field.GetLayer()].append(box)
    with tempfile.TemporaryDirectory(prefix='control-references-') as temporary:
        native_path = Path(temporary)/'native.kicad_pcb'
        pcbnew.SaveBoard(str(native_path), board)
        result = transplant(raw.decode(), native_path.read_text(), refs).encode()
    if (board_path.read_bytes() != raw or policy_path.read_bytes() != policy_bytes or
            any((ROOT/path).read_bytes() != data for path, data in sources.items())):
        raise ValueError('Annotation source changed during generation')
    if check:
        if output.read_bytes() != result:
            raise ValueError('Reference layout differs from exact source regeneration')
    else:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_bytes(result)
    print('PASS: 418 source references, 1 mm text, body/pad/edge clearance; all other bytes preserved')
    return {'board_sha256': sha(result), 'bare_board_sha256': sha(raw),
            'policy_sha256': sha(policy_bytes), 'reference_count': len(refs),
            'scope': 'Annotation/source geometry only; routing and physical qualification remain open'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('board', 'policy', 'output'):
        parser.add_argument(name, type=Path)
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    apply(args.board, args.policy, args.output, args.check)
