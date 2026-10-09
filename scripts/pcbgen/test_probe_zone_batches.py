import unittest
from scripts.pcbgen.probe_zone_batches import batch_text, identities, ZONE


class ZoneBatchProbeTests(unittest.TestCase):
    def test_union_preserves_selected_and_common_bytes_in_original_order(self):
        parts = [(None, 'header'), ('b', 'B'), (None, 'zone'), ('a', 'A'), ('c', 'C'), (None, 'end')]
        self.assertEqual(batch_text(parts, ['a', 'b']), 'headerBzoneAend')
        self.assertEqual(batch_text(parts, ['a']), 'headerzoneAend')

    def test_empty_duplicate_or_unknown_selection_rejects(self):
        for selected in ([], ['a', 'a'], ['missing']):
            with self.subTest(selected=selected), self.assertRaises(ValueError):
                batch_text([(None, 'context'), ('a', 'A')], selected)

    def test_native_version_and_caps_fail_closed_even_without_zone_findings(self):
        with self.assertRaisesRegex(ValueError, 'version'):
            identities({'kicad_version': '9.0.2', 'violations': []})
        for kind in ('silk_overlap', 'silk_over_copper'):
            report = {'kicad_version': '10.0.6', 'violations':
                      [{'type': kind, 'items': [], 'severity': 'warning'}] * 199}
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, 'cap'):
                identities(report)

    def test_zone_findings_preserve_type_severity_and_full_item_identity(self):
        finding = {'type': 'silk_overlap', 'severity': 'warning',
                   'items': [{'uuid': 'text'}, {'uuid': ZONE}]}
        unrelated = {'type': 'silk_overlap', 'severity': 'warning',
                     'items': [{'uuid': 'text'}, {'uuid': 'other'}]}
        report = {'kicad_version': '10.0.6', 'violations': [finding, unrelated]}
        self.assertEqual(identities(report), {('silk_overlap', 'warning', tuple(sorted([ZONE, 'text'])))})


if __name__ == '__main__':
    unittest.main()
