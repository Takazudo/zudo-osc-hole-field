import unittest
from pathlib import Path
from scripts.pcbgen.peripheral_stack_serialization import serialize,verify,setup_and_stack


class PeripheralStackSerializationTests(unittest.TestCase):
    def test_exact_stopped_v2_editor_delta_and_all_other_values_reject(self):
        before=Path('.circuit-cache/issue38-recovery/octave-1-prerequisite-v2/synchronized.kicad_pcb').read_text()
        stopped=Path('boards/osc-octave-1/osc-octave-1-ground-prerequisite-v2.kicad_pcb').read_text()
        definition=Path('design/partition/peripheral-ground-feasibility/osc-octave-1.json').read_bytes()
        expected,receipt=serialize(before,definition)
        self.assertEqual(setup_and_stack(expected)[1],setup_and_stack(stopped)[1])
        self.assertEqual(verify(before,expected,definition),receipt)
        for old,new in [('(thickness 1.53)','(thickness 1.52)'),
                        ('UNSELECTED conditional pressed dielectric','other material'),
                        ('(epsilon_r 4.5)','(epsilon_r 4.6)'),
                        ('(pad_to_mask_clearance 0)','(pad_to_mask_clearance 0.01)')]:
            self.assertTrue(old in expected,old)
            with self.subTest(old=old),self.assertRaisesRegex(ValueError,'undeclared'):
                verify(before,expected.replace(old,new,1),definition)
        for old,new in [('(thickness 1.53)','(thickness 1.52)'),
                        ('UNSELECTED conditional pressed dielectric','other material')]:
            with self.assertRaisesRegex(ValueError,'exact source'):
                serialize(before.replace(old,new,1),definition)


if __name__=='__main__':unittest.main()
