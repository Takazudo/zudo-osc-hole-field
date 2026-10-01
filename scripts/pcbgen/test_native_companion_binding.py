import hashlib
import tempfile
import unittest
from pathlib import Path
from scripts.pcbgen.native_companion_binding import verify


class NativeCompanionBindingTests(unittest.TestCase):
    def test_each_destination_mutation_before_or_during_validation_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            board = Path(directory)/'candidate.kicad_pcb'
            original = {str(board.with_suffix(suffix)): ('retained source '+suffix).encode()
                        for suffix in ('.kicad_pro', '.kicad_sch', '.kicad_dru')}
            expected = {path: hashlib.sha256(value).hexdigest() for path, value in original.items()}
            retained = dict(expected)
            for path, value in original.items():
                Path(path).write_bytes(value)
            verify(expected)
            for name in original:
                for stage in ('before native validation', 'during native validation'):
                    with self.subTest(companion=Path(name).suffix, stage=stage):
                        # The caller performs the same retained binding gate
                        # both before the oracle and after all native checks.
                        verify(expected)
                        Path(name).write_bytes(('changed '+stage).encode())
                        with self.assertRaisesRegex(ValueError, 'retained source authority'):
                            verify(expected)
                        self.assertEqual(expected, retained)
                        Path(name).write_bytes(original[name])

    def test_omitted_companion_or_wrong_destination_stem_rejected(self):
        with self.assertRaisesRegex(ValueError, 'Exact project'):
            verify({'candidate.kicad_pro': 'x'})
        with self.assertRaisesRegex(ValueError, 'same candidate stem'):
            verify({'one.kicad_pro': 'x', 'one.kicad_sch': 'x', 'two.kicad_dru': 'x'})


if __name__ == '__main__':
    unittest.main()
