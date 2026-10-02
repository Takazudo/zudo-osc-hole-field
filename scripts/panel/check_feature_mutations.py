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
