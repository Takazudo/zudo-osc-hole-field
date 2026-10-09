import unittest
from scripts.pcbgen.probe_zone_batch_controls import control_text, selected_identities, IDS, ZONE


class BatchControlTests(unittest.TestCase):
    def test_synthetic_control_scope_and_deliberate_mask_layer(self):
        zone = '(zone (layer "F.Cu") (filled_polygon (layer "F.Cu") (pts (xy 1 2))))'
        parts = [(None, '(kicad_pcb\n'), (None, zone), ('old', '(gr_text "old")'), (None, ')')]
        text = control_text(parts, [0, 2], (10., 20.))
        self.assertIn(zone.replace('"F.Cu"', '"F.Mask"'), text)
        self.assertNotIn('old', text)
        self.assertIn(IDS[0], text)
        self.assertIn(IDS[2], text)
        self.assertNotIn(IDS[1], text)
        self.assertIn('(start 1000.000000 1000.100000)', text)
        self.assertTrue(text.endswith(')'))

    def test_invalid_selection_and_native_caps_fail_closed(self):
        for selection in ([], [0, 0], [3]):
            with self.assertRaises(ValueError):
                control_text([(None, '(kicad_pcb)')], selection, (0, 0))
        with self.assertRaisesRegex(ValueError, 'version'):
            selected_identities({'kicad_version': '9.0.2', 'violations': []})
        for kind in ('silk_overlap', 'silk_over_copper'):
            with self.assertRaisesRegex(ValueError, 'cap'):
                selected_identities({'kicad_version': '10.0.6', 'violations':
                    [{'type': kind, 'severity': 'warning', 'items': []}] * 199})

    def test_positive_identity_keeps_zone_and_artwork(self):
        report = {'kicad_version': '10.0.6', 'violations': [dict(type='silk_over_copper',
            severity='warning', items=[dict(uuid=ZONE), dict(uuid=IDS[0])])]}
        self.assertEqual(selected_identities(report), {('silk_over_copper', 'warning', tuple(sorted([ZONE, IDS[0]])))})


if __name__ == '__main__':
    unittest.main()
