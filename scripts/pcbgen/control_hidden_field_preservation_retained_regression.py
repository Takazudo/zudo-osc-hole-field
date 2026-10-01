import unittest
from pathlib import Path
from scripts.pcbgen.control_hidden_field_preservation import restore
from scripts.pcbgen.verify_local_links import blocks


class HiddenFieldPreservationTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.original = blocks(Path('boards/osc-control/osc-control-ground-bare-v2.kicad_pcb'))['footprint']
        cls.candidate = Path('boards/osc-control/osc-control-ground-feasibility-v2.kicad_pcb').read_text()

    def test_actual_three_hidden_deltas_restore_every_original_footprint(self):
        corrected, receipts = restore(self.candidate, self.original)
        self.assertEqual({row['ref'] for row in receipts}, {'U3303', 'U3403', 'U4611'})
        from scripts.pcbgen.uuid_tools import top_level_spans, REF_RE
        after = {REF_RE.search(corrected[a:b])[1]: corrected[a:b] for a, b in top_level_spans(corrected)
                 if corrected[a:b].startswith('(footprint ')}
        self.assertEqual(after, self.original)
        # A second pass is an exact no-op, rather than another style rewrite.
        second, changes = restore(corrected, self.original)
        self.assertEqual(second, corrected)
        self.assertFalse(changes)

    def test_changed_value_visible_style_or_other_geometry_is_not_hidden(self):
        # Modify the actual hidden-field insertion, not an unrelated first
        # font in the file. Any different thickness or field value must fail.
        marker = '(property "LogicalCellKey" "general_output_J_X1_IN_A_SELECTED__A.1"'
        start = self.candidate.index(marker)
        position = self.candidate.index('(thickness 0.15)', start)
        changed = self.candidate[:position]+self.candidate[position:].replace('(thickness 0.15)', '(thickness 0.2)', 1)
        with self.assertRaisesRegex(ValueError, 'not solely'):
            restore(changed, self.original)
        changed = self.candidate[:start]+self.candidate[start:].replace('general_output_J_X1_IN_A_SELECTED__A.1', 'different source value', 1)
        with self.assertRaisesRegex(ValueError, 'not solely'):
            restore(changed, self.original)
        changed = self.candidate[:start]+self.candidate[start:].replace('(hide yes)', '(hide no)', 1)
        with self.assertRaisesRegex(ValueError, 'not solely'):
            restore(changed, self.original)


if __name__ == '__main__':
    unittest.main()
