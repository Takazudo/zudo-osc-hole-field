import unittest
from scripts.pcbgen.control_reference_layout import reference_fields, transplant


class ReferenceByteOwnershipTests(unittest.TestCase):
    def test_native_defaults_and_nonreference_edits_are_not_copied(self):
        before = '''(kicad_pcb (setup (stackup (layer "dielectric 1" (thickness 1.2))))
 (footprint "lib:part" (at 20 30) (property "Reference" "R1" (at 1 2))
  (property "Role" "quoted (text)" (effects (font (size 1 1))))
  (pad "1" thru_hole circle (at 0 0) (net 1 "AGND"))))'''
        native = before.replace('(at 1 2)', '(at 3 4 90)').replace(
            '(thickness 1.2)', '(thickness 1.2) (epsilon_r 4.5)').replace(
            '(size 1 1)', '(size 1 1) (thickness .15)').replace(
            '(net 1 "AGND")', '(net 2 "WRONG")')
        self.assertEqual(transplant(before, native, {'R1'}),
                         before.replace('(at 1 2)', '(at 3 4 90)'))

    def test_nonselected_reference_is_byte_preserved(self):
        before = '''(kicad_pcb
 (footprint "x" (property "Reference" "R1" (at 1 2)))
 (footprint "support" (property "Reference" "MH_1" (hide yes))))'''
        native = before.replace('(at 1 2)', '(at 3 4)').replace('(hide yes)', '(hide no)')
        self.assertEqual(transplant(before, native, {'R1'}),
                         before.replace('(at 1 2)', '(at 3 4)'))

    def test_missing_duplicate_or_extra_footprint_is_rejected(self):
        one = '(footprint "x" (property "Reference" "R1"))'
        with self.assertRaisesRegex(ValueError, 'unique'):
            reference_fields('(kicad_pcb '+one+one+')')
        before = '(kicad_pcb '+one+')'
        with self.assertRaisesRegex(ValueError, 'inventory'):
            transplant(before, '(kicad_pcb)', {'R1'})
        with self.assertRaisesRegex(ValueError, 'inventory'):
            transplant(before, before, {'R2'})
        with self.assertRaisesRegex(ValueError, 'inventory'):
            transplant(before, before[:-1]+one.replace('R1', 'R2')+')', {'R1'})


if __name__ == '__main__':
    unittest.main()
