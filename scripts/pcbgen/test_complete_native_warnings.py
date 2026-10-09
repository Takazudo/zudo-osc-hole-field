import tempfile
import json
from pathlib import Path
import unittest
from scripts.pcbgen.complete_native_warnings import append_observations, check_caps, hole_evidence


class CompleteWarningTests(unittest.TestCase):
    def test_append_never_removes_original_error_or_warning(self):
        error=dict(type='clearance',severity='error',items=[{'uuid':'bad'}])
        old=dict(type='hole_to_hole',severity='warning',items=[{'uuid':'a'},{'uuid':'b'}])
        raw={'violations':[error,old],'schematic_parity':[{'original':'parity'}]}
        full=append_observations(raw,{('hole_to_hole','warning',('a','b')),('hole_to_hole','warning',('c','d'))})
        self.assertEqual(full['violations'][:2],[error,old])
        self.assertEqual(len(full['violations']),3)
        self.assertEqual(full['schematic_parity'],raw['schematic_parity'])
        self.assertEqual(len(raw['violations']),2)

    def test_report_order_shift_is_resolved_by_complete_native_observations(self):
        a=('hole_to_hole','warning',('a','b'));b=('hole_to_hole','warning',('c','d'))
        def raw(item):return {'violations':[dict(type=item[0],severity=item[1],items=[{'uuid':u} for u in item[2]])]}
        before=append_observations(raw(a),{a,b});after=append_observations(raw(b),{a,b})
        from scripts.pcbgen.complete_native_warnings import identity
        self.assertEqual({identity(v) for v in before['violations']},{identity(v) for v in after['violations']})

    def test_no_other_warning_type_can_be_appended(self):
        with self.assertRaises(ValueError):append_observations({'violations':[]},{('track_dangling','warning',('a',))})

    def test_unsupported_capped_domain_blocks(self):
        report={'violations':[dict(type='track_dangling',severity='warning')]*199}
        with self.assertRaises(ValueError):check_caps(report)

    def test_stale_native_board_audit_blocks_before_using_observations(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);board=root/'board.kicad_pcb';board.write_text('changed')
            (root/'result.json').write_text(json.dumps(dict(version='10.0.6',source_sha256='stale')))
            with self.assertRaisesRegex(ValueError,'source mismatch'):hole_evidence(root,board,{'violations':[]},{})


if __name__=='__main__':unittest.main()
