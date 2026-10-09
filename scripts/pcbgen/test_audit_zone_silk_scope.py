import unittest
from scripts.pcbgen.audit_zone_silk_scope import zone_metadata,zone_fixture_parts,zone_fixture_text,native_zone_signature


class ZoneScopeTests(unittest.TestCase):
    def test_incomplete_arc_format_is_rejected_before_comparison(self):
        class ArcPoly:
            def ArcCount(self):return 1
            def Format(self):raise AssertionError('must not use incomplete arc serialization')
        with self.assertRaisesRegex(ValueError,'does not support arcs'):
            native_zone_signature(ArcPoly())

    def test_reusable_fixture_preserves_zone_context_artwork_bytes_and_removes_other_copper(self):
        zone='00000000-0000-4000-8000-000000000001'
        other='00000000-0000-4000-8000-000000000002'
        footprint='00000000-0000-4000-8000-000000000003'
        drawing='00000000-0000-4000-8000-000000000004'
        zone_block=f'(zone (uuid "{zone}") (layer "F.Cu") (filled_polygon (pts (xy 1 2))))'
        fp=f'(footprint (uuid "{footprint}") (property "Value" "a (quoted) value") (pad "1" smd rect))'
        art=f'(gr_text "silk" (uuid "{drawing}"))'
        source=f'(kicad_pcb\n (setup exact)\n {zone_block}\n (zone (uuid "{other}"))\n {fp}\n {art}\n (segment copper)\n (via drill)\n)'
        parts=zone_fixture_parts(source,zone,{footprint,drawing})
        for selected in (footprint,drawing):
            with self.subTest(selected=selected):
                expected=source.replace(f'(zone (uuid "{other}"))','').replace('(segment copper)','').replace('(via drill)','')
                expected=expected.replace(art,'') if selected==footprint else expected.replace(fp,'')
                expected=expected.replace('(pad "1" smd rect)','')
                self.assertEqual(zone_fixture_text(parts,selected),expected)

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
