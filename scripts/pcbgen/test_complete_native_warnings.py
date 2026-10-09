import tempfile
import json
import hashlib
from pathlib import Path
import unittest
from scripts.pcbgen.complete_native_warnings import append_observations, check_caps, hole_evidence


class CompleteWarningTests(unittest.TestCase):
    def test_raw_fixture_context_must_match_source_even_when_receipt_claims_it_does(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);board=root/'board.kicad_pcb';board.write_text('native source')
            folder=root/'fixture-0000';folder.mkdir()
            context={'clearance_nm':250000}
            for suffix,key in (('.kicad_pro','project_sha256'),('.kicad_dru','rules_sha256')):
                data=b'exact source context';board.with_suffix(suffix).write_bytes(data)
                (folder/board.with_suffix(suffix).name).write_bytes(data)
                context[key]=hashlib.sha256(data).hexdigest()
            holes=[]
            for uid,x in [('a',0),('b',300000)]:
                row=dict(uuid=uid,xy=[x,0],radius=150000,drill=300000,kind='via',subtype=3,layers=[0,2],net='AGND')
                row['object_key']=hashlib.sha256(json.dumps(row,sort_keys=True).encode()).hexdigest();holes.append(row)
            item=('hole_to_hole','warning',('a','b'))
            report={'violations':[dict(type=item[0],severity=item[1],items=[{'uuid':u} for u in item[2]])]}
            (folder/'drc.json').write_text(json.dumps(report))
            audit=dict(context,version='10.0.6',source_sha256=hashlib.sha256(board.read_bytes()).hexdigest(),holes=holes,covered_pairs=[[0,1]],identities=[item],object_identities=[(item[0],item[1],sorted(h['object_key'] for h in holes))],fixtures=[dict(fixture=str(folder/board.name),holes=[h['object_key'] for h in holes],identities=[item],report_sha256=hashlib.sha256((folder/'drc.json').read_bytes()).hexdigest())])
            (root/'result.json').write_text(json.dumps(audit))
            self.assertEqual(hole_evidence(root,board,report,context)[1],{item})
            (folder/'board.kicad_pro').write_text('native SaveBoard defaults')
            with self.assertRaisesRegex(ValueError,'fixture context changed'):
                hole_evidence(root,board,report,context)

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
