"""A populated failed native export cannot become a K electrical input."""
import unittest
import tempfile
import hashlib
from pathlib import Path
from scripts.pcbgen.core_model_gate import require_native_prerequisite,path_in_worktree,verify_native_companions,ROOT


class CoreModelGateTests(unittest.TestCase):

    def test_only_repository_or_pinned_container_paths_are_accepted(self):
        self.assertEqual(path_in_worktree('/work/scripts/pcbgen/sync.py'),ROOT/'scripts/pcbgen/sync.py')
        with self.assertRaisesRegex(ValueError,'outside'):path_in_worktree('/etc/passwd')
        with self.assertRaisesRegex(ValueError,'outside'):path_in_worktree('../other-repo/file')

    def test_wrong_board_drc_and_changed_copied_schematic_or_rules_reject(self):
        (ROOT/'.circuit-cache').mkdir(exist_ok=True)
        with tempfile.TemporaryDirectory(dir=ROOT/'.circuit-cache') as directory:
            board=Path(directory)/'candidate.kicad_pcb'
            contents={'.kicad_pcb':b'original board','.kicad_pro':b'original project',
                '.kicad_sch':b'original schematic','.kicad_dru':b'original rules'}
            for suffix,data in contents.items():board.with_suffix(suffix).write_bytes(data)
            sha=lambda b:hashlib.sha256(b).hexdigest()
            native={'board_sha256':sha(contents['.kicad_pcb']),'project_sha256':sha(contents['.kicad_pro'])}
            sources={str(ROOT/'boards/osc-core/osc-core.kicad_sch'):sha(contents['.kicad_sch']),
                str(ROOT/'design/partition/core-ground-feasibility/osc-core.kicad_dru'):sha(contents['.kicad_dru'])}
            retained=dict(sources);drc={'source':board.name}
            verify_native_companions(board,native,sources,drc)
            with self.assertRaisesRegex(ValueError,'different native board'):
                verify_native_companions(board,native,sources,{'source':'other.kicad_pcb'})
            for suffix in ('.kicad_sch','.kicad_dru'):
                board.with_suffix(suffix).write_bytes(b'changed after native DRC')
                with self.subTest(suffix=suffix),self.assertRaisesRegex(ValueError,'copied companion changed'):
                    verify_native_companions(board,native,sources,drc)
                board.with_suffix(suffix).write_bytes(contents[suffix])
            self.assertEqual(sources,retained)


if __name__=='__main__':unittest.main()
