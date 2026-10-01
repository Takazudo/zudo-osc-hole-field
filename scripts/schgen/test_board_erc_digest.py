"""The active ERC receipt must not depend on ignored schematic experiments."""
from pathlib import Path
import tempfile
import unittest
from scripts.schgen.check_board_erc import schematic_tree_digest


class SchematicTreeDigestTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.directory = Path(self.temp.name)
        self.root = self.directory/'board.kicad_sch'
        self.child = self.directory/'child.kicad_sch'
        self.root.write_text('(kicad_sch (sheet (property "Sheetfile" "child.kicad_sch")))')
        self.child.write_text('(kicad_sch)')

    def test_unreferenced_experiments_do_not_change_digest(self):
        expected = schematic_tree_digest(self.root)
        (self.directory/'experimental.kicad_sch').write_text('unrelated local experiment')
        self.assertEqual(schematic_tree_digest(self.root), expected)
        self.child.write_text('(kicad_sch (version 20250114))')
        self.assertNotEqual(schematic_tree_digest(self.root), expected)

    def test_missing_referenced_sheet_fails(self):
        self.child.unlink()
        with self.assertRaises(FileNotFoundError):
            schematic_tree_digest(self.root)

    def test_cycle_fails(self):
        self.child.write_text('(kicad_sch (sheet (property "Sheetfile" "board.kicad_sch")))')
        with self.assertRaisesRegex(ValueError, 'cyclic'):
            schematic_tree_digest(self.root)

    def test_escaping_reference_fails(self):
        self.child.write_text('(kicad_sch (sheet (property "Sheetfile" "../other.kicad_sch")))')
        with self.assertRaisesRegex(ValueError, 'escapes'):
            schematic_tree_digest(self.root)
