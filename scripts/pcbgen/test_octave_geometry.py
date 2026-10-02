import unittest
from pathlib import Path
from scripts.pcbgen.definition import load_definition
from scripts.pcbgen.octave_geometry import verify_geometry

class OctaveGeometryTests(unittest.TestCase):
    def test_current_boards_and_changed_zone_source(self):
        for n in range(1,6):
            with self.subTest(board=n):
                definition=load_definition(Path(f'design/boards/osc-octave-{n}.json'))
                raw=Path(f'boards/osc-octave-{n}/osc-octave-{n}.kicad_pcb').read_bytes()
                verify_geometry(raw,definition)
                changed=raw.replace(b'(min_thickness 0.15)',b'(min_thickness 0.14)',1)
                self.assertNotEqual(changed,raw)
                with self.assertRaisesRegex(ValueError,'zone definition'):verify_geometry(changed,definition)

if __name__=='__main__':unittest.main()
