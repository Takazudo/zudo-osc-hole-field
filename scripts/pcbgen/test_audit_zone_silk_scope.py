import unittest
from scripts.pcbgen.audit_zone_silk_scope import zone_metadata


class ZoneScopeTests(unittest.TestCase):
    def test_fill_changes_do_not_hide_outline_or_context_changes(self):
        def board(fill,outline='(xy 0 0)',net='AGND'):
            return f'(kicad_pcb (zone (uuid "00000000-0000-4000-8000-000000000001") (net "{net}") (layer "F.Cu") (polygon (pts {outline})) {fill}))'
        before=zone_metadata(board('(filled_polygon (pts (xy 1 1)))'))
        self.assertEqual(before,zone_metadata(board('(filled_polygon (pts (xy 2 2))) \n (filled_polygon (pts (xy 3 3)))')))
        self.assertNotEqual(before,zone_metadata(board('',outline='(xy 1 0)')))
        self.assertNotEqual(before,zone_metadata(board('',net='-12V')))

    def test_ambiguous_zone_identity_rejects(self):
        zone='(zone (uuid "00000000-0000-4000-8000-000000000001") (layer "F.Cu"))'
        with self.assertRaisesRegex(ValueError,'ambiguous'):
            zone_metadata('(kicad_pcb '+zone+zone+')')


if __name__=='__main__':unittest.main()
