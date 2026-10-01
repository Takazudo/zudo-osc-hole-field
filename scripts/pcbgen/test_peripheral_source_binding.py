import hashlib
import shutil
import tempfile
import unittest
from pathlib import Path
from scripts.pcbgen.peripheral_source_binding import retain_sources,require_fresh_outputs
from scripts.pcbgen.prerequisite_package_fields import project


class PeripheralSourceBindingTests(unittest.TestCase):
    def test_actual_projection_then_sheet_mutation_is_not_rebound(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);board=root/'board'
            shutil.copytree(Path('boards/osc-octave-1/sheets'),board/'sheets')
            projection=project(Path('schematic/boards/osc-octave-1.net'),board)
            sources=projection['source_sheet_sha256'];paths=[Path(n) for n in sources]
            retained=retain_sources(root,paths,[sources])
            self.assertEqual(len(retained),len(sources))
            changed=paths[0];old=changed.read_bytes();changed.write_bytes(old+b'\n')
            with self.assertRaisesRegex(ValueError,'changed before native entry'):
                retain_sources(root,paths,[sources])
            self.assertEqual(sources[str(changed)],hashlib.sha256(old).hexdigest())

    def test_every_stale_companion_and_pcb_remains_byte_exact(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);output=root/'candidate.kicad_pcb';cache=root/'cache'
            for suffix in ('.kicad_pcb','.kicad_pro','.kicad_sch','.kicad_dru'):
                existing=output.with_suffix(suffix);data=b'original owned bytes\n';existing.write_bytes(data)
                with self.subTest(suffix=suffix),self.assertRaisesRegex(ValueError,'fresh native stem'):
                    require_fresh_outputs(output,cache)
                self.assertEqual(existing.read_bytes(),data);existing.unlink()
            output.with_suffix('.kicad_pro').symlink_to(root/'absent')
            with self.assertRaisesRegex(ValueError,'fresh native stem'):require_fresh_outputs(output,cache)
            output.with_suffix('.kicad_pro').unlink();cache.mkdir()
            with self.assertRaisesRegex(ValueError,'fresh native stem'):require_fresh_outputs(output,cache)


if __name__=='__main__':unittest.main()
