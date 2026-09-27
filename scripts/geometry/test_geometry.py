"""Stdlib unit and golden geometry tests for the placement pipeline."""

from __future__ import annotations

from collections import Counter
import copy
from pathlib import Path
import tempfile
import unittest

from build_placements import StaleLockError, build_lock, lock_bytes, write_or_check
from panel_frame import (
    HOLE_DIAMETERS_MM,
    PANEL_H,
    PANEL_W,
    REPO_ROOT,
    board_domain,
    cell_center,
    net_name,
    reference_designator,
    slug_uid,
    to_kicad,
)
from verify_geometry import GeometryMismatch, verify_geometry


class PanelFrameTests(unittest.TestCase):
    def test_frame_constants_and_reference_centres(self) -> None:
        self.assertEqual((PANEL_W, PANEL_H), (318.0, 298.0))
        self.assertEqual(cell_center("jacks", 0, 0), (14.5, 29.0))
        self.assertEqual(cell_center("jacks", 17, 9), (303.5, 155.0))
        self.assertEqual(cell_center("controls", 0, 0), (14.5, 185.0))
        self.assertEqual(cell_center("controls", 7, 6), (133.5, 269.0))
        self.assertEqual(cell_center("controls", 14, 3), (252.5, 227.0))

    def test_kicad_conversion_is_translation_only(self) -> None:
        self.assertEqual(to_kicad(14.5, 29.0), (114.5, 79.0))
        self.assertEqual(to_kicad(14.5, 283.0), (114.5, 333.0))

    def test_slug_maps_every_special_character(self) -> None:
        self.assertEqual(slug_uid("C:O1.VCO/LFO±"), "C_O1_VCO-LFOPM")

    def test_key_not_display_label_drives_net_name(self) -> None:
        self.assertEqual(net_name({"key": "VCO/LFO", "label": "RANGE"}), "VCO/LFO")
        self.assertEqual(net_name({"key": "LEVEL", "label": "SUM GAIN"}), "LEVEL")
        self.assertEqual(net_name({"key": "1V", "label": "1V/OCT"}), "1V")

    def test_domain_and_hole_proposals(self) -> None:
        cases = (
            ("jacks", "O1", "jack", "J"),
            ("controls", "O1", "octave", "O"),
            ("controls", "O1", "switch", "OS"),
            ("controls", "O1", "pot", "OP"),
            ("controls", "E1", "switch", "ES"),
            ("controls", "E1", "button", "ET"),
            ("controls", "E1", "pot", "EP"),
            ("controls", "A01", "pot", "EP"),
            ("controls", "H1", "pot", "UP"),
            ("controls", "H1", "button", "UT"),
            ("controls", "X1", "switch", "US"),
            ("controls", "M5A", "pot", "MP"),
        )
        for field, block, kind, expected in cases:
            with self.subTest(block=block, kind=kind):
                self.assertEqual(board_domain(field, block, kind), expected)
        self.assertEqual(
            HOLE_DIAMETERS_MM,
            {"jack": 6.2, "pot": 6.3, "octave": 6.3, "switch": 5.2, "button": 5.0},
        )

    def test_cell_coded_references_and_duplicate_led_slot(self) -> None:
        self.assertEqual(reference_designator("jacks", "jack", 0, 0), "J101")
        self.assertEqual(reference_designator("controls", "pot", 7, 6), "RV807")
        self.assertEqual(reference_designator("controls", "button", 2, 3), "SW304")
        self.assertEqual(
            reference_designator("jacks", "led", 8, 5, led_type="mag"), "D906"
        )
        self.assertEqual(
            reference_designator("jacks", "led", 8, 5, led_type="clip"), "D906A"
        )
        self.assertEqual(
            reference_designator("controls", "led", 8, 5, led_type="stage"), "D10906"
        )


class PlacementLockTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.lock = build_lock(REPO_ROOT)
        cls.placements = cls.lock["placements"]

    def test_complete_feature_counts_and_unique_identifiers(self) -> None:
        records = self.placements
        self.assertEqual(len(records), 438)
        self.assertEqual(
            Counter(record["kind"] for record in records),
            Counter({"jack": 180, "pot": 101, "octave": 5, "switch": 30, "button": 8, "led": 114}),
        )
        self.assertEqual(
            Counter(record["led_type"] for record in records if record["kind"] == "led"),
            Counter({"mag": 92, "clip": 10, "stage": 12}),
        )
        for field in ("uid", "slug", "ref"):
            values = [record[field] for record in records]
            self.assertEqual(len(values), len(set(values)), f"duplicate {field}")

    def test_sample_coordinates_labels_domains_and_holes(self) -> None:
        records = {record["uid"]: record for record in self.placements}
        self.assertEqual(
            (records["J:O1.1V"]["x_mm"], records["J:O1.1V"]["y_mm"]),
            (14.5, 29.0),
        )
        self.assertEqual(records["J:O1.1V"]["label"], "1V/OCT")
        self.assertEqual(records["J:O1.1V"]["domain"], "J")
        self.assertEqual(records["J:O1.1V"]["hole_d_mm"], 6.2)
        self.assertEqual(records["J:O1.1V"]["hole_status"], "PROPOSAL")
        self.assertEqual(records["C:H1.SLEW"]["domain"], "UP")
        self.assertEqual(records["C:H1.SLEW"]["hole_d_mm"], 6.3)
        self.assertEqual(records["L:M5A.SUM.mag"]["parent"], "J:M5A.SUM")
        self.assertEqual(records["L:M5A.SUM.clip"]["parent"], "J:M5A.SUM")
        self.assertEqual(records["L:E1.RISE.stage"]["label"], "RISE")

    def test_sort_order_is_field_cell_family_then_uid(self) -> None:
        keys = [
            (
                record["field"],
                record["col"],
                record["row"],
                record["family"],
                record["uid"],
            )
            for record in self.placements
        ]
        self.assertEqual(keys, sorted(keys))

    def test_building_twice_produces_identical_bytes(self) -> None:
        self.assertEqual(lock_bytes(build_lock(REPO_ROOT)), lock_bytes(build_lock(REPO_ROOT)))

    def test_check_mode_detects_missing_and_stale_output(self) -> None:
        expected = lock_bytes(self.lock)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "placements.lock.json"
            with self.assertRaises(StaleLockError):
                write_or_check(path, self.lock, check=True)
            path.write_bytes(expected)
            self.assertFalse(write_or_check(path, self.lock, check=True))
            path.write_text("{}\n", encoding="utf-8")
            with self.assertRaises(StaleLockError):
                write_or_check(path, self.lock, check=True)

    def test_golden_svg_matches_all_438_centres(self) -> None:
        hardware, leds = verify_geometry(
            self.lock,
            REPO_ROOT / "project/osc-hole-field/workbench/panels/panel.svg",
        )
        self.assertEqual((hardware, leds), (324, 114))

    def test_golden_svg_rejects_a_moved_hardware_feature(self) -> None:
        changed = copy.deepcopy(self.lock)
        feature = next(record for record in changed["placements"] if record["kind"] == "jack")
        feature["x_mm"] += 0.25
        with self.assertRaises(GeometryMismatch):
            verify_geometry(
                changed,
                REPO_ROOT / "project/osc-hole-field/workbench/panels/panel.svg",
            )


if __name__ == "__main__":
    unittest.main()
