from dataclasses import replace
import importlib.util
from pathlib import Path
import unittest

from scripts.pcbgen.netlist import Component

PATH = Path(__file__).resolve().parents[2] / 'circuit/routing/issue189/jr-source-adoption/pilot.py'
SPEC = importlib.util.spec_from_file_location('jr_source_adoption_pilot', PATH)
PILOT = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PILOT)


class SourceAdoptionGuards(unittest.TestCase):
    def setUp(self):
        self.old = Component('RB4413', '5600', 'R_0603', '/JR/', '/s/', '/p/',
                             (('FootprintOriginMm', '1,2'), ('BoardSide', 'B.Cu')))
        self.new = replace(self.old, fields=(('FootprintOriginMm', '1,1.8'), ('BoardSide', 'B.Cu')))
        self.pins = {('RB4413', '1'): 'signal', ('RB4413', '2'): 'AGND'}

    def test_only_reviewed_origin_can_change(self):
        PILOT.check_netlists(([self.old], self.pins), ([self.new], self.pins), '1,2', '1,1.8')
        for changed in (replace(self.new, value='1000'), replace(self.new, footprint='R_0402'),
                        replace(self.new, fields=(('FootprintOriginMm', '1,1.8'), ('BoardSide', 'F.Cu')))):
            with self.subTest(changed=changed), self.assertRaisesRegex(ValueError, 'unreviewed'):
                PILOT.check_netlists(([self.old], self.pins), ([changed], self.pins), '1,2', '1,1.8')

    def test_pin_net_and_wrong_origin_changes_reject(self):
        pins = dict(self.pins); pins[('RB4413', '2')] = '-12V'
        with self.assertRaisesRegex(ValueError, 'pin/net'):
            PILOT.check_netlists(([self.old], self.pins), ([self.new], pins), '1,2', '1,1.8')
        with self.assertRaisesRegex(ValueError, 'origin'):
            PILOT.check_netlists(([self.old], self.pins), ([self.new], self.pins), '1,2', '1,1.7')

    def test_other_component_and_membership_changes_reject(self):
        other = replace(self.old, ref='R2')
        with self.assertRaisesRegex(ValueError, 'components'):
            PILOT.check_netlists(([self.old, other], self.pins), ([self.new], self.pins), '1,2', '1,1.8')
        with self.assertRaisesRegex(ValueError, 'unreviewed'):
            PILOT.check_netlists(([self.old, other], self.pins), ([self.new, replace(other, value='10')], self.pins), '1,2', '1,1.8')

    def test_native_metadata_comparison_keeps_other_geometry_and_fields(self):
        def board(origin, source, angle='180', value='5600'):
            return f'(kicad_pcb (footprint (at {origin} {angle}) (property "Reference" "RB4413") (property "FootprintOriginMm" "{source}") (property "Value" "{value}") (pad "1" (at 0 0))))'
        old = PILOT.physical(board('101 52', '1,2'), '1,2')
        self.assertEqual(old, PILOT.physical(board('101 51.8', '1,1.8'), '1,1.8'))
        self.assertNotEqual(old, PILOT.physical(board('101 51.8', '1,1.8', value='1000'), '1,1.8'))
        self.assertNotEqual(old, PILOT.physical(board('101 51.8', '1,1.8', angle='0'), '1,1.8'))
        # Pad geometry remains part of the full footprint block.
        self.assertNotEqual(old, PILOT.physical(board('101 51.8', '1,1.8').replace('(at 0 0)', '(at 1 0)'), '1,1.8'))
        with self.assertRaisesRegex(ValueError, 'source-origin'):
            PILOT.physical(board('101 51.8', '1,1.7'), '1,1.8')


if __name__ == '__main__':
    unittest.main()
