#!/usr/bin/env python3
"""Native negative controls for fixed panel feature verification."""
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
import uuid
import pcbnew

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.panel.check_panel import check, PARAMS
from scripts.pcbgen.uuid_tools import top_level_spans, UUID_RE
SOURCE = ROOT / 'boards/panel/panel.kicad_pcb'


def duplicate_feature(text):
    spans = list(top_level_spans(text))
    a, b = next((a, b) for a, b in spans if text[a:b].startswith('(footprint '))
    block = text[a:b]
    old_id = UUID_RE.search(block).group(1)
    ids = {}
    def fresh(match):
        ids[match.group(1)] = str(uuid.uuid4())
        return '(uuid "' + ids[match.group(1)] + '")'
    duplicate = UUID_RE.sub(fresh, block)
    for a, b in spans:
        part = text[a:b]
        if part.startswith('(group "panelgen:geometry"'):
            part = part.replace('(members', '(members "' + ids[old_id] + '"', 1)
            text = text[:a] + part + text[b:]
            break
    else:
        raise ValueError('geometry group absent')
    return text.rstrip()[:-1] + duplicate + '\n)\n'


class PanelFeatureTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = SOURCE.read_bytes()

    @classmethod
    def tearDownClass(cls):
        if SOURCE.read_bytes() != cls.original:
            raise AssertionError('native fixture changed the source board')

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'panel.kicad_pcb'
        self.board = pcbnew.LoadBoard(str(SOURCE))

    def pad(self, prefix):
        footprint = next(fp for fp in self.board.GetFootprints()
                         if fp.GetReference().startswith(prefix))
        return next(iter(footprint.Pads()))

    def verify(self, **kwargs):
        pcbnew.SaveBoard(str(self.path), self.board)
        with redirect_stdout(io.StringIO()):
            check(self.path, **kwargs)

    def test_original_features_pass(self):
        self.verify()

    def test_duplicate_reference_is_not_hidden_by_dictionary(self):
        self.path.write_text(duplicate_feature(self.original.decode()))
        loaded = pcbnew.LoadBoard(str(self.path))
        self.assertEqual(len(list(loaded.GetFootprints())), 439)
        with self.assertRaisesRegex(ValueError, 'feature references differ'):
            check(self.path)

    def test_wrong_optical_window_diameter_is_rejected(self):
        self.pad('PW_').SetSize(pcbnew.VECTOR2I(pcbnew.FromMM(3), pcbnew.FromMM(3)))
        with self.assertRaisesRegex(ValueError, 'diameter differs'):
            self.verify()

    def test_wrong_hole_mask_diameter_is_rejected(self):
        self.pad('PH_').SetSize(pcbnew.VECTOR2I(3000000, 3000000))
        with self.assertRaisesRegex(ValueError, 'diameter differs'):
            self.verify()

    def test_rectangular_window_is_rejected(self):
        self.pad('PW_').SetShape(pcbnew.PAD_SHAPE_RECT)
        with self.assertRaisesRegex(ValueError, 'circular pad'):
            self.verify()

    def test_copper_or_missing_mask_layer_is_rejected(self):
        for layers in ((pcbnew.F_Mask,), (pcbnew.F_Mask, pcbnew.B_Mask, pcbnew.F_Cu)):
            with self.subTest(layers=layers):
                layer_set = pcbnew.LSET()
                for layer in layers:
                    layer_set.AddLayer(layer)
                self.pad('PW_').SetLayerSet(layer_set)
                with self.assertRaisesRegex(ValueError, 'both mask layers'):
                    self.verify()

    def test_window_report_follows_source_parameter(self):
        params = json.loads(PARAMS.read_text())
        params['indicator_window']['diameter_mm'] = 1.8
        params_path = Path(self.temp.name) / 'params.json'
        params_path.write_text(json.dumps(params))
        for fp in self.board.GetFootprints():
            if fp.GetReference().startswith('PW_'):
                next(iter(fp.Pads())).SetSize(pcbnew.VECTOR2I(1800000, 1800000))
        report = Path(self.temp.name) / 'features.json'
        self.verify(output=report, params_path=params_path)
        windows = [r for r in json.loads(report.read_text())['rows'] if r['kind'] == 'led']
        self.assertEqual(len(windows), 114)
        self.assertEqual({r['diameter_mm'] for r in windows}, {1.8})

    def shape(self, layer, footprint=None):
        owner = footprint or self.board
        item = pcbnew.PCB_SHAPE(owner)
        item.SetShape(pcbnew.SHAPE_T_CIRCLE)
        item.SetLayer(layer)
        item.SetCenter(pcbnew.VECTOR2I(104000000, 54000000))
        item.SetEnd(pcbnew.VECTOR2I(105000000, 54000000))
        item.SetWidth(pcbnew.FromMM(.05))
        owner.Add(item)
        return item

    def test_extra_via_drill_is_rejected(self):
        via = pcbnew.PCB_VIA(self.board)
        via.SetPosition(pcbnew.VECTOR2I(104000000, 54000000))
        via.SetWidth(pcbnew.FromMM(.6)); via.SetDrill(pcbnew.FromMM(.3))
        via.SetViaType(pcbnew.VIATYPE_THROUGH)
        via.SetLayerPair(pcbnew.F_Cu, pcbnew.B_Cu)
        self.board.Add(via)
        with self.assertRaisesRegex(ValueError, 'extra drilled via'):
            self.verify()

    def test_extra_cutout_on_board_or_footprint_is_rejected(self):
        for embedded in (False, True):
            with self.subTest(embedded=embedded):
                self.board = pcbnew.LoadBoard(str(SOURCE))
                fp = next(iter(self.board.GetFootprints())) if embedded else None
                self.shape(pcbnew.Edge_Cuts, fp)
                with self.assertRaisesRegex(ValueError, 'outline differs'):
                    self.verify()

    def test_missing_or_relayered_outline_is_rejected(self):
        for remove in (False, True):
            with self.subTest(remove=remove):
                self.board = pcbnew.LoadBoard(str(SOURCE))
                edge = next(item for item in self.board.GetDrawings()
                            if item.GetLayer() == pcbnew.Edge_Cuts)
                if remove:
                    self.remove_grouped_item(edge)
                else:
                    edge.SetLayer(pcbnew.F_SilkS)
                with self.assertRaisesRegex(ValueError, 'outline differs'):
                    self.verify()

    def test_arc_shape_and_stroke_must_match_source(self):
        for change in ('midpoint', 'width'):
            with self.subTest(change=change):
                self.board = pcbnew.LoadBoard(str(SOURCE))
                edge = next(item for item in self.board.GetDrawings()
                            if item.GetLayer() == pcbnew.Edge_Cuts
                            and item.GetShape() == pcbnew.SHAPE_T_ARC)
                if change == 'midpoint':
                    mid = edge.GetArcMid()
                    edge.SetArcGeometry(edge.GetStart(),
                                        pcbnew.VECTOR2I(mid.x + 200000, mid.y),
                                        edge.GetEnd())
                else:
                    edge.SetWidth(pcbnew.FromMM(.1))
                with self.assertRaisesRegex(ValueError, 'outline differs'):
                    self.verify()

    def test_thickness_matches_source_parameter(self):
        self.board.GetDesignSettings().SetBoardThickness(pcbnew.FromMM(1.6))
        with self.assertRaisesRegex(ValueError, 'thickness differs'):
            self.verify()
        params = json.loads(PARAMS.read_text())
        params['thickness_mm'] = 1.6
        path = Path(self.temp.name) / 'params.json'
        path.write_text(json.dumps(params))
        self.verify(params_path=path)

    def test_changed_source_outline_requires_matching_native_geometry(self):
        for key, value in (('width_mm', 320), ('height_mm', 300),
                           ('corner_radius_mm', 4)):
            with self.subTest(key=key):
                params = json.loads(PARAMS.read_text()); params[key] = value
                path = Path(self.temp.name) / 'params.json'
                path.write_text(json.dumps(params))
                with self.assertRaisesRegex(ValueError, 'outline differs|locked frame'):
                    self.verify(params_path=path)

    def remove_grouped_item(self, item):
        # KiCad groups retain native pointers: detach before removing an item.
        for group in self.board.Groups():
            if any(member.m_Uuid == item.m_Uuid for member in group.GetItems()):
                group.RemoveItem(item)
        self.board.Remove(item)

    def replace_outline(self, params):
        from scripts.pcbgen.geometry import outline_segments
        from scripts.pcbgen.uuid_tools import stable_uuid
        # Update the existing native items as the generator does; preserve
        # their identities and ownership-group membership in the fixture.
        edges = {item.m_Uuid.AsString(): item for item in self.board.GetDrawings()
                 if item.GetLayer() == pcbnew.Edge_Cuts}
        outline = [(0, 0), (params['width_mm'], 0),
                   (params['width_mm'], params['height_mm']), (0, params['height_mm'])]
        for index, segment in enumerate(outline_segments(outline, params['corner_radius_mm'])):
            item = edges[stable_uuid('panel', 'outline', str(index))]
            points = [pcbnew.VECTOR2I(pcbnew.FromMM(x + 100), pcbnew.FromMM(y + 50))
                      for x, y in segment[1:]]
            if segment[0] == 'arc':
                item.SetShape(pcbnew.SHAPE_T_ARC); item.SetArcGeometry(*points)
            else:
                item.SetShape(pcbnew.SHAPE_T_SEGMENT)
                item.SetStart(points[0]); item.SetEnd(points[1])

    def test_source_shrink_cannot_cut_through_locked_hardware(self):
        params = json.loads(PARAMS.read_text()); params['width_mm'] = 100
        self.replace_outline(params)
        self.assertAlmostEqual(pcbnew.ToMM(self.board.GetBoardEdgesBoundingBox().GetWidth()), 100.05)
        path = Path(self.temp.name) / 'params.json'
        path.write_text(json.dumps(params))
        with self.assertRaisesRegex(ValueError, 'locked frame'):
            self.verify(params_path=path)

    def test_source_corner_cannot_cut_through_locked_hardware(self):
        params = json.loads(PARAMS.read_text()); params['corner_radius_mm'] = 148
        self.replace_outline(params)
        path = Path(self.temp.name) / 'params.json'
        path.write_text(json.dumps(params))
        with self.assertRaisesRegex(ValueError, 'intersects a locked feature'):
            self.verify(params_path=path)

    def test_native_corner_geometry_follows_source_radius(self):
        params = json.loads(PARAMS.read_text()); params['corner_radius_mm'] = 4
        self.replace_outline(params)
        path = Path(self.temp.name) / 'params.json'
        path.write_text(json.dumps(params))
        self.verify(params_path=path)

    def test_invalid_physical_source_parameters_are_rejected(self):
        path = Path(self.temp.name) / 'params.json'
        for key in ('width_mm', 'height_mm', 'thickness_mm', 'corner_radius_mm'):
            for value in (True, -1, float('nan'), float('inf')):
                with self.subTest(key=key, value=value):
                    params = json.loads(PARAMS.read_text()); params[key] = value
                    path.write_text(json.dumps(params))
                    with self.assertRaisesRegex(ValueError, 'invalid panel source'):
                        self.verify(params_path=path)

    def test_undrilled_owner_copper_and_art_remain_allowed(self):
        self.shape(pcbnew.F_Cu)
        self.shape(pcbnew.F_SilkS)
        track = pcbnew.PCB_TRACK(self.board)
        track.SetStart(pcbnew.VECTOR2I(104000000, 54000000))
        track.SetEnd(pcbnew.VECTOR2I(105000000, 54000000))
        track.SetWidth(pcbnew.FromMM(.2)); track.SetLayer(pcbnew.F_Cu)
        self.board.Add(track)
        self.verify()

    def test_rejection_preserves_owner_geometry_bytes(self):
        self.shape(pcbnew.Edge_Cuts)
        self.shape(pcbnew.F_SilkS)
        pcbnew.SaveBoard(str(self.path), self.board)
        original = self.path.read_bytes()
        with self.assertRaisesRegex(ValueError, 'outline differs'):
            check(self.path)
        self.assertEqual(self.path.read_bytes(), original)

    def test_invalid_source_diameter_is_rejected(self):
        params = json.loads(PARAMS.read_text())
        params_path = Path(self.temp.name) / 'params.json'
        for value in (0, True, float('nan')):
            with self.subTest(value=value):
                params['indicator_window']['diameter_mm'] = value
                params_path.write_text(json.dumps(params))
                with self.assertRaisesRegex(ValueError, 'invalid source diameter'):
                    self.verify(params_path=params_path)


if __name__ == '__main__':
    if not re.match(r'^10\.0\.6(?:[-+ ]|$)', pcbnew.GetBuildVersion()):
        raise RuntimeError('pinned KiCad 10.0.6 oracle required')
    unittest.main(verbosity=2)
