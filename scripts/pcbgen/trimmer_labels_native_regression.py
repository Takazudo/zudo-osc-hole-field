"""Retained pinned-KiCad front/back fixture regression for issue #249.

Only run in an admitted native slot:
  bash scripts/kicad/run.sh python3 scripts/pcbgen/trimmer_labels_native_regression.py \
    --evidence-dir /work/<retained-evidence>/trimmer-labels-249-a1
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
import traceback
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.pcbgen.trimmer_labels import _owned, _strip_owned, apply, digest
from scripts.pcbgen.uuid_tools import stable_uuid

FIXTURE = ROOT/'scripts/pcbgen/fixtures/trimmer-labels/two-face.kicad_pcb'
INVENTORY = ROOT/'design/service/trimmer-inventory.json'
REFS = ('RV1601', 'RV2107')


def _xy(point):
    return point.x, point.y


def _box(item, pcbnew):
    box = item.GetBoundingBox()
    return tuple(pcbnew.ToMM(v) for v in (box.GetLeft(), box.GetTop(), box.GetRight(), box.GetBottom()))


def _text(item):
    return (item.m_Uuid.AsString().lower(), item.GetText(), item.GetLayer(),
            _xy(item.GetPosition()), item.GetTextAngle().AsDegrees(),
            item.IsMirrored(), _xy(item.GetTextSize()), item.GetTextThickness())


def _owned_native(board, ids):
    result = {}
    for item in board.GetDrawings():
        uid = item.m_Uuid.AsString().lower()
        if uid in ids:
            if uid in result or not hasattr(item, 'GetText'):
                raise ValueError('duplicate or non-text owned native UUID '+uid)
            result[uid] = _text(item)
    if set(result) != ids:
        raise ValueError('owned native UUID inventory differs')
    return result


def _expected_owned(pcbnew):
    rows = {row['ref']: row for row in json.loads(INVENTORY.read_text())['trimmers']}
    result = {}
    for ref, x, y, layer, mirror in (
        ('RV1601', 141, 265, pcbnew.F_SilkS, False),
        ('RV2107', 191, 168, pcbnew.B_SilkS, True),
    ):
        uid = stable_uuid('osc-core', 'trimmer-labels-v1', ref)
        result[uid] = (uid, rows[ref]['label'], layer,
                       (pcbnew.FromMM(x), pcbnew.FromMM(y)), 0.0, mirror,
                       (pcbnew.FromMM(1), pcbnew.FromMM(1)), pcbnew.FromMM(.15))
    return result


def _other_native(board, pcbnew, ids):
    footprints = []
    for fp in board.GetFootprints():
        pads = []
        for pad in fp.Pads():
            pads.append((pad.m_Uuid.AsString().lower(), pad.GetNumber(), pad.GetNetname(),
                         _xy(pad.GetPosition()), _xy(pad.GetSize()), int(pad.GetShape()),
                         tuple(pad.GetLayerSet().Contains(layer) for layer in
                               (pcbnew.F_Cu, pcbnew.B_Cu, pcbnew.F_Mask, pcbnew.B_Mask))))
        fields = tuple(sorted((_text(field), field.IsVisible()) for field in fp.GetFields()))
        graphics = tuple(sorted((item.m_Uuid.AsString().lower(), item.GetClass(),
                                 item.GetLayer(), _box(item, pcbnew)) for item in fp.GraphicalItems()))
        footprints.append((fp.m_Uuid.AsString().lower(), fp.GetReference(), fp.GetValue(),
                           fp.GetLayer(), _xy(fp.GetPosition()), fp.GetOrientation().AsDegrees(),
                           fields, graphics, tuple(sorted(pads))))
    drawings = []
    for item in board.GetDrawings():
        uid = item.m_Uuid.AsString().lower()
        if uid not in ids:
            drawings.append((uid, item.GetClass(), item.GetLayer(), _box(item, pcbnew),
                             item.GetText() if isinstance(item, pcbnew.PCB_TEXT) else None))
    return tuple(sorted(footprints)), tuple(sorted(drawings)), len(list(board.GetTracks())), len(list(board.Zones()))


def _policy(labels):
    rows = {row['ref']: row for row in json.loads(INVENTORY.read_text())['trimmers']}
    entries = []
    for ref, x, y in (('RV1601', 141, 265), ('RV2107', 191, 168)):
        row = rows[ref]
        entries.append(dict(ref=ref, block=row['block'], role=row['role'],
                            face=row['placement']['side'], x_mm=x, y_mm=y, angle_deg=0))
    return dict(schema_version=1, board_id='osc-core', input_board_sha256=digest(FIXTURE.read_bytes()),
                inventory_sha256=digest(INVENTORY.read_bytes()), base_board='input.kicad_pcb',
                labels=entries if labels else [])


def prepare_source_evidence(directory: Path):
    """Create retained input, policy, candidate, repeat and removal evidence."""
    directory = Path(directory)
    directory.mkdir(parents=False, exist_ok=False)
    shutil.copyfile(FIXTURE, directory/'input.kicad_pcb')
    shutil.copyfile(INVENTORY, directory/'inventory.json')
    policy = directory/'policy.json'
    policy.write_text(json.dumps(_policy(True), indent=2, sort_keys=True)+'\n')
    candidate = directory/'candidate.kicad_pcb'
    apply(directory/'input.kicad_pcb', policy, candidate)
    repeated = directory/'second-apply.kicad_pcb'
    apply(candidate, policy, repeated)
    if repeated.read_bytes() != candidate.read_bytes():
        raise ValueError('second application differs')
    removal = directory/'removal-policy.json'
    removal.write_text(json.dumps(_policy(False), indent=2, sort_keys=True)+'\n')
    removed = directory/'removed.kicad_pcb'
    apply(candidate, removal, removed)
    if removed.read_bytes() != (directory/'input.kicad_pcb').read_bytes():
        raise ValueError('owned removal changed non-annotation bytes')
    stripped = _strip_owned(candidate.read_text(), _owned(candidate.read_text(), 'osc-core')[0])
    if stripped != (directory/'input.kicad_pcb').read_text():
        raise ValueError('candidate changed non-annotation bytes')
    return candidate


def _overlap(a, b, gap=.15):
    return a[0] < b[2]+gap and a[2]+gap > b[0] and a[1] < b[3]+gap and a[3]+gap > b[1]


def _check_clearances(board, labels, pcbnew):
    for label in labels:
        side = label.GetLayer()
        if side not in (pcbnew.F_SilkS, pcbnew.B_SilkS):
            raise ValueError('wrong native silk layer')
        if label.IsMirrored() != (side == pcbnew.B_SilkS):
            raise ValueError('backside mirror differs')
        rect = _box(label, pcbnew)
        obstacles = []
        for fp in board.GetFootprints():
            if fp.GetLayer() == (pcbnew.F_Cu if side == pcbnew.F_SilkS else pcbnew.B_Cu):
                obstacles.append(('body '+fp.GetReference(), _box(fp, pcbnew)))
            for pad in fp.Pads():
                mask = pcbnew.F_Mask if side == pcbnew.F_SilkS else pcbnew.B_Mask
                if pad.GetLayerSet().Contains(mask):
                    obstacles.append(('mask/pad '+fp.GetReference(), _box(pad, pcbnew)))
        for other in board.GetDrawings():
            if other.m_Uuid.AsString() != label.m_Uuid.AsString() and other.GetLayer() in (side, pcbnew.Edge_Cuts):
                obstacles.append(('text/artwork/edge', _box(other, pcbnew)))
        conflicts = [kind for kind, bounds in obstacles if _overlap(rect, bounds)]
        if conflicts:
            raise ValueError('unresolved native clearance '+label.GetText()+': '+', '.join(conflicts))


def _plot(board, directory, pcbnew):
    for layer, name in ((pcbnew.F_SilkS, 'front'), (pcbnew.B_SilkS, 'back')):
        controller = pcbnew.PLOT_CONTROLLER(board)
        options = controller.GetPlotOptions()
        options.SetOutputDirectory(str(directory))
        options.SetPlotFrameRef(False)
        options.SetPlotReference(True)
        options.SetPlotInvisibleText(False)
        controller.SetLayer(layer)
        controller.OpenPlotfile(name, pcbnew.PLOT_FORMAT_SVG, 'Trimmer label fixture')
        try:
            if controller.PlotLayer() is False:
                raise ValueError('SVG rendering failed: '+name)
        finally:
            controller.ClosePlot()
    svgs = list(directory.glob('*.svg'))
    if len(svgs) != 2 or any(path.stat().st_size <= 100 for path in svgs):
        raise ValueError('front/back SVGs missing')


def _receipt(directory, status, error=None):
    files = {p.relative_to(directory).as_posix(): digest(p.read_bytes())
             for p in sorted(directory.rglob('*')) if p.is_file() and p.name != 'receipt.json'}
    result = dict(status=status, native_version_required='10.0.6',
                  fixture_sha256=digest(FIXTURE.read_bytes()), files_sha256=files,
                  scope='two-face fixture only; production clearance and fit remain open')
    if error is not None:
        result['error'] = error
    (directory/'receipt.json').write_text(json.dumps(result, indent=2, sort_keys=True)+'\n')
    return result


def run(directory: Path, pcbnew_module=None):
    """Always retain a hash receipt and failure traceback in a fresh directory."""
    directory = Path(directory).resolve()
    directory.mkdir(parents=True, exist_ok=False)
    try:
        candidate = prepare_source_evidence(directory/'source')
        if pcbnew_module is None:
            import pcbnew as pcbnew_module
        pcbnew = pcbnew_module
        if pcbnew.GetBuildVersion() != '10.0.6':
            raise ValueError('pinned KiCad 10.0.6 required')
        board = pcbnew.LoadBoard(str(candidate))
        if board is None:
            raise ValueError('KiCad failed to load candidate')
        source = pcbnew.LoadBoard(str(directory/'source/input.kicad_pcb'))
        if source is None:
            raise ValueError('KiCad failed to load retained input')
        ids = {stable_uuid('osc-core', 'trimmer-labels-v1', ref) for ref in REFS}
        before_owned = _owned_native(board, ids)
        before_other = _other_native(board, pcbnew, ids)
        (directory/'candidate-semantics.json').write_text(json.dumps(
            {'owned': before_owned, 'nonannotation': before_other}, indent=2, sort_keys=True)+'\n')
        if before_owned != _expected_owned(pcbnew):
            raise ValueError('native candidate differs from reviewed UUID/text/layer/position/angle/mirror/size/stroke')
        if before_other != _other_native(source, pcbnew, ids):
            raise ValueError('candidate changed native reference or non-annotation semantics')
        if {fp.GetReference() for fp in board.GetFootprints()} != set(REFS):
            raise ValueError('native reference inventory changed')
        labels = [d for d in board.GetDrawings() if d.m_Uuid.AsString().lower() in ids]
        _check_clearances(board, labels, pcbnew)
        reload_path = directory/'native-reload.kicad_pcb'
        pcbnew.SaveBoard(str(reload_path), board)
        reloaded = pcbnew.LoadBoard(str(reload_path))
        if reloaded is None:
            raise ValueError('native reload failed')
        after_owned = _owned_native(reloaded, ids)
        after_other = _other_native(reloaded, pcbnew, ids)
        (directory/'reload-semantics.json').write_text(json.dumps(
            {'owned': after_owned, 'nonannotation': after_other}, indent=2, sort_keys=True)+'\n')
        if after_owned != before_owned:
            raise ValueError('owned UUID/text/layer/position/angle/mirror/size/stroke changed on reload')
        if after_other != before_other:
            raise ValueError('reference or non-annotation semantics changed on reload')
        _plot(board, directory, pcbnew)
        return _receipt(directory, 'PASS pinned KiCad fixture only')
    except Exception as exc:
        (directory/'failure.txt').write_text(traceback.format_exc())
        _receipt(directory, 'FAIL / NATIVE ACCEPTANCE NOT ESTABLISHED', str(exc))
        raise


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--evidence-dir', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(run(args.evidence_dir), indent=2, sort_keys=True))
