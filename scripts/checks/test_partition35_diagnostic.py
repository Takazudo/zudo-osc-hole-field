"""Regression checks for the diagnostic's conservative geometric accounting."""
import math
import unittest

from scripts.checks.partition35_diagnostic import ROOT, footprint_geometry, island_closure


class PartitionDiagnosticTests(unittest.TestCase):
    def test_sensitive_net_closure_propagates_between_whole_islands(self):
        islands = {('A', 'CORE'): {'a', 'b'}, ('A', 'LED'): {'c', 'd'},
                   ('B', 'CORE'): {'e', 'f'}}
        self.assertEqual(island_closure({'a'}, islands, [{'b', 'c'}]), {'a', 'b', 'c', 'd'})

    def test_instance_local_names_do_not_merge_unrelated_islands(self):
        islands = {('H1', 'HOLD_LOCAL'): {'a', 'b'}, ('H2', 'HOLD_LOCAL'): {'c', 'd'}}
        self.assertEqual(island_closure({'a'}, islands, []), {'a', 'b'})

    def test_jack_front_courtyard_and_opposite_face_copper_are_distinct(self):
        geometry = footprint_geometry(ROOT / 'footprints/kicad/zudo-osc-hole-field.pretty/Jack_3.5mm_QingPu_WQP518MA.kicad_mod')
        self.assertAlmostEqual(geometry['courtyard_bbox_area_mm2'], 9.5*13.9)
        self.assertEqual(len(geometry['through_hole_pads']), 3)
        self.assertAlmostEqual(sum(p['area_mm2'] for p in geometry['through_hole_pads']),
                               1.93*1.83 + 2*math.pi*(2.13/2)**2)


if __name__ == '__main__':
    unittest.main()
