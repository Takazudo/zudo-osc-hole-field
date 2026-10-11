"""Pinned-KiCad fixture load, render, reload and conservative clearance check.

Run only in an admitted global native slot:
  bash scripts/kicad/run.sh python3 scripts/pcbgen/trimmer_labels_native_regression.py
"""
import json
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.pcbgen.trimmer_labels import apply, digest
from scripts.pcbgen.uuid_tools import stable_uuid


def _box(item, pcbnew):
    b = item.GetBoundingBox()
    return tuple(pcbnew.ToMM(v) for v in (b.GetLeft(), b.GetTop(), b.GetRight(), b.GetBottom()))


def _overlap(a, b, gap=.15):
    return a[0] < b[2]+gap and a[2]+gap > b[0] and a[1] < b[3]+gap and a[3]+gap > b[1]


def main():
    import pcbnew
    if pcbnew.GetBuildVersion() != '10.0.6':
        raise ValueError('pinned KiCad 10.0.6 required')
    fixture = ROOT/'scripts/pcbgen/fixtures/trimmer-labels/two-face.kicad_pcb'
    inventory_path = ROOT/'design/service/trimmer-inventory.json'
    rows = {r['ref']:r for r in json.loads(inventory_path.read_text())['trimmers']}
    entries = []
    for ref, x, y in (('RV1601',141,265),('RV2107',191,168)):
        row = rows[ref]
        entries.append(dict(ref=ref,block=row['block'],role=row['role'],face=row['placement']['side'],
                            x_mm=x,y_mm=y,angle_deg=0))
    with tempfile.TemporaryDirectory(prefix='trimmer-labels-native-') as tmp:
        tmp = Path(tmp)
        policy = tmp/'policy.json'
        policy.write_text(json.dumps(dict(schema_version=1,board_id='osc-core',
                            input_board_sha256=digest(fixture.read_bytes()),
                            inventory_sha256=digest(inventory_path.read_bytes()),labels=entries)))
        candidate = tmp/'candidate.kicad_pcb'
        apply(fixture,policy,candidate)
        board = pcbnew.LoadBoard(str(candidate))
        if board is None:
            raise ValueError('KiCad failed to load candidate')
        owned_ids = {stable_uuid('osc-core','trimmer-labels-v1',e['ref']) for e in entries}
        labels = [d for d in board.GetDrawings() if d.m_Uuid.AsString() in owned_ids]
        if len(labels) != 2:
            raise ValueError('native label count differs')
        if {fp.GetReference() for fp in board.GetFootprints()} != {'RV1601','RV2107'}:
            raise ValueError('native references changed')
        for label in labels:
            side = label.GetLayer()
            if side not in (pcbnew.F_SilkS,pcbnew.B_SilkS):
                raise ValueError('wrong native silk layer')
            if label.IsMirrored() != (side == pcbnew.B_SilkS):
                raise ValueError('backside mirror differs')
            rect = _box(label,pcbnew)
            obstacles = []
            for fp in board.GetFootprints():
                if fp.GetLayer() == (pcbnew.F_Cu if side == pcbnew.F_SilkS else pcbnew.B_Cu):
                    obstacles.append(('body '+fp.GetReference(),_box(fp,pcbnew)))
                for pad in fp.Pads():
                    if pad.GetLayerSet().Contains(pcbnew.F_Mask if side == pcbnew.F_SilkS else pcbnew.B_Mask):
                        obstacles.append(('mask/pad '+fp.GetReference(),_box(pad,pcbnew)))
            for other in board.GetDrawings():
                if other.m_Uuid.AsString() == label.m_Uuid.AsString():
                    continue
                if other.GetLayer() in (side,pcbnew.Edge_Cuts):
                    obstacles.append(('text/artwork/edge',_box(other,pcbnew)))
            conflicts = [name for name,other in obstacles if _overlap(rect,other)]
            if conflicts:
                raise ValueError('unresolved native clearance '+label.GetText()+': '+', '.join(conflicts))
        reload_path = tmp/'native-reload.kicad_pcb'
        pcbnew.SaveBoard(str(reload_path),board)
        again = pcbnew.LoadBoard(str(reload_path))
        if again is None or len([d for d in again.GetDrawings() if d.m_Uuid.AsString() in owned_ids]) != 2:
            raise ValueError('native reload lost labels')
        for layer,name in ((pcbnew.F_SilkS,'front'),(pcbnew.B_SilkS,'back')):
            controller = pcbnew.PLOT_CONTROLLER(board)
            options = controller.GetPlotOptions()
            options.SetOutputDirectory(str(tmp))
            options.SetPlotFrameRef(False)
            options.SetPlotReference(True)
            options.SetPlotInvisibleText(False)
            controller.SetLayer(layer)
            controller.OpenPlotfile(name,pcbnew.PLOT_FORMAT_SVG,'Trimmer label fixture')
            if not controller.PlotLayer():
                raise ValueError('SVG rendering failed: '+name)
            controller.ClosePlot()
        if len(list(tmp.glob('*.svg'))) != 2:
            raise ValueError('front/back SVGs missing')
        print(json.dumps({'status':'PASS pinned KiCad 10.0.6 fixture only',
                          'candidate_sha256':digest(candidate.read_bytes()),
                          'native_reload_sha256':digest(reload_path.read_bytes()),
                          'fixture_sha256':digest(fixture.read_bytes())},indent=2))


if __name__ == '__main__':
    main()
