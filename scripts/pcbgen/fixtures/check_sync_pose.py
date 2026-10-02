#!/usr/bin/env python3
"""Persisted-board pose regressions; run through the pinned KiCad oracle."""
import json
from pathlib import Path
import re
import sys
import tempfile
import unittest
import pcbnew

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT))
from scripts.pcbgen.sync import sync
from scripts.pcbgen.definition import load_lock
from scripts.geometry.panel_frame import to_kicad


class SyncPoseTests(unittest.TestCase):
    def setUp(self):
        cache = ROOT / '.circuit-cache/pcbgen-pose'
        cache.mkdir(parents=True, exist_ok=True)
        self.tmp = tempfile.TemporaryDirectory(dir=cache)
        self.addCleanup(self.tmp.cleanup)
        self.directory = Path(self.tmp.name)
        self.board = self.directory / 'pose.kicad_pcb'
        self.netlist = self.directory / 'pose.net'
        self.hardware = next(p for p in load_lock(ROOT / 'design/grid/placements.lock.json').values()
                             if p['ref'] == 'J101')
        self.write_netlist()
        self.run_sync()

    def write_netlist(self, free_footprint='R0603', hardware_fields=None, free_fields=None):
        def component(ref, footprint, uid, fields):
            properties = ''.join(f'(property (name {json.dumps(k)}) (value {json.dumps(v)}))'
                                 for k, v in (fields or {}).items())
            return (f'(comp (ref "{ref}") (value "POSE FIXTURE") '
                    f'(footprint "zudo-osc-hole-field:{footprint}") '
                    '(sheetpath (names "/POSE") (tstamps "/11111111-1111-4111-8111-111111111111/")) '
                    f'(tstamps "{uid}") {properties})')
        components = component('J101', 'Jack_3.5mm_QingPu_WQP518MA',
                               '22222222-2222-4222-8222-222222222222', hardware_fields)
        components += component('R9001', free_footprint,
                                '33333333-3333-4333-8333-333333333333', free_fields)
        self.netlist.write_text('(export (components ' + components + ') '
                               '(nets (net (name "RETURN") (node (ref "J101") (pin "S")) '
                               '(node (ref "R9001") (pin "1")))))')

    def run_sync(self):
        sync('fixture-jacks', self.board, self.netlist)

    def footprint(self, ref):
        # Keep the board alive while using its SWIG-owned footprint.
        self.loaded = pcbnew.LoadBoard(str(self.board))
        return next(fp for fp in self.loaded.GetFootprints() if fp.GetReference() == ref)

    def set_free_pose(self, locked):
        fp = self.footprint('R9001')
        fp.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(123.4), pcbnew.FromMM(156.7)))
        if fp.GetLayer() != pcbnew.B_Cu:
            fp.Flip(fp.GetPosition(), False)
        fp.SetOrientationDegrees(37)
        fp.SetLocked(locked)
        pcbnew.SaveBoard(str(self.board), self.loaded)

    def assert_free_pose(self, side, angle, locked):
        fp = self.footprint('R9001')
        self.assertEqual(fp.GetLayer(), side)
        self.assertAlmostEqual(fp.GetOrientationDegrees(), angle)
        self.assertEqual(fp.IsLocked(), locked)
        self.assertEqual((fp.GetPosition().x, fp.GetPosition().y),
                         (pcbnew.FromMM(123.4), pcbnew.FromMM(156.7)))
        return fp

    def assert_repeat_identity(self):
        before = self.board.read_bytes()
        self.run_sync()
        self.assertEqual(self.board.read_bytes(), before)

    def test_fixed_hardware_returns_to_front_lock_pose(self):
        for fields in ({}, {'BoardSide': 'F.Cu', 'KiCadOrientationDeg': '360'}):
            with self.subTest(fields=fields):
                fp = self.footprint('J101')
                if fp.GetLayer() != pcbnew.B_Cu:
                    fp.Flip(fp.GetPosition(), False)
                fp.SetPosition(pcbnew.VECTOR2I(0, 0))
                fp.SetOrientationDegrees(73)
                fp.SetLocked(False)
                pcbnew.SaveBoard(str(self.board), self.loaded)
                self.write_netlist(hardware_fields=fields)
                self.run_sync()
                fp = self.footprint('J101')
                self.assertEqual(fp.GetLayer(), pcbnew.F_Cu)
                x, y = to_kicad(self.hardware['x_mm'], self.hardware['y_mm'])
                self.assertEqual((fp.GetPosition().x, fp.GetPosition().y),
                                 (pcbnew.FromMM(x), pcbnew.FromMM(y)))
                self.assertAlmostEqual(fp.GetOrientationDegrees(), self.hardware['rot_deg'])
                self.assertTrue(fp.IsLocked())
                self.assert_repeat_identity()

    def test_conflicting_fixed_pose_preserves_board_bytes(self):
        for fields in ({'BoardSide': 'B.Cu'}, {'KiCadOrientationDeg': '90'},
                       {'KiCadOrientationDeg': 'nan'}):
            with self.subTest(fields=fields):
                self.write_netlist(hardware_fields=fields)
                before = self.board.read_bytes()
                with self.assertRaises(ValueError):
                    self.run_sync()
                self.assertEqual(self.board.read_bytes(), before)

    def test_replacement_preserves_side_angle_position_and_both_lock_states(self):
        for locked, replacement in ((True, 'R_0805_2012Metric'), (False, 'R0603')):
            with self.subTest(locked=locked):
                self.set_free_pose(locked)
                self.write_netlist(free_footprint=replacement)
                self.run_sync()
                fp = self.assert_free_pose(pcbnew.B_Cu, 37, locked)
                self.assertEqual(str(fp.GetFPID().GetLibItemName()), replacement)
                self.assert_repeat_identity()

    def test_explicit_free_source_pose_overrides_preserved_replacement_pose(self):
        self.set_free_pose(True)
        self.write_netlist(free_footprint='R_0805_2012Metric',
                           free_fields={'BoardSide': 'F.Cu', 'KiCadOrientationDeg': '71'})
        self.run_sync()
        self.assert_free_pose(pcbnew.F_Cu, 71, True)
        self.assert_repeat_identity()

    def test_source_origin_can_lock_previously_unlocked_replacement(self):
        self.set_free_pose(False)
        self.write_netlist(free_footprint='R_0805_2012Metric',
                           free_fields={'FootprintOriginMm': '23.4,106.7'})
        self.run_sync()
        self.assert_free_pose(pcbnew.B_Cu, 37, True)
        self.assert_repeat_identity()

    def test_existing_field_stroke_is_preserved(self):
        self.write_netlist(free_fields={'Role': 'fixture'})
        self.run_sync()
        fp = self.footprint('R9001')
        fp.GetField('Role').SetTextThickness(pcbnew.FromMM(.23))
        pcbnew.SaveBoard(str(self.board), self.loaded)
        self.run_sync()
        self.assertEqual(self.footprint('R9001').GetField('Role').GetTextThickness(),
                         pcbnew.FromMM(.23))
        self.assert_repeat_identity()


if __name__ == '__main__':
    if not re.match(r'^10\.0\.6(?:[-+ ]|$)', pcbnew.GetBuildVersion()):
        raise RuntimeError('pinned KiCad 10.0.6 oracle required')
    unittest.main(verbosity=2)
