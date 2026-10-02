"""A selected replacement must enter ERC coverage or fail explicitly."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from scripts.libgen.fixtures import build_ic_erc_fixture as fixture


class ShortlistCoverage(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / 'design/standard').mkdir(parents=True)
        (self.root / 'symbols/src').mkdir(parents=True)
        self.patch = patch.object(fixture, 'ROOT', self.root)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def shortlist(self, mpn):
        (self.root / 'design/standard/parts-shortlist.json').write_text(
            json.dumps({'parts': [{'id': 'signal_diode', 'mpn': mpn}]}))

    def symbol(self, name, mpn):
        (self.root / 'symbols/src' / (name + '.kicad_sym')).write_text(
            f'(kicad_symbol_lib (symbol "{name}" '
            f'(property "MPN" "{mpn}") (property "Reference" "D")))')

    def test_replacement_selected_by_exact_mpn(self):
        self.symbol('Old', 'OLD,215')
        self.symbol('New', 'NEW-QX')
        self.shortlist('NEW-QX')
        self.assertEqual(fixture.shortlist_symbols(), [('New', 'D')])

    def test_missing_suffix_is_not_a_match(self):
        self.symbol('Family', 'NEW')
        self.shortlist('NEW-QX')
        with self.assertRaisesRegex(ValueError, 'expected one symbol'):
            fixture.shortlist_symbols()

    def test_duplicate_mpn_fails_instead_of_arbitrary_choice(self):
        self.symbol('First', 'NEW-QX')
        self.symbol('Second', 'NEW-QX')
        self.shortlist('NEW-QX')
        with self.assertRaisesRegex(ValueError, 'expected one symbol'):
            fixture.shortlist_symbols()


if __name__ == '__main__':
    unittest.main()
