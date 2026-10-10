import tempfile
import json
import hashlib
from pathlib import Path
import unittest
from scripts.pcbgen.complete_native_warnings import append_observations, check_caps, hole_evidence, unchanged_silk_zones, zone_evidence


class CompleteWarningTests(unittest.TestCase):
    def test_native_zone_pair_warning_blocks_even_when_added_copper_is_clean(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);uid='00000000-0000-4000-8000-000000000001'
            before=root/'before.kicad_pcb';after=root/'after.kicad_pcb'
            for p,fill in [(before,'old'),(after,'new')]:p.write_text(f'(kicad_pcb (zone (uuid "{uid}") (layer "F.Cu") (filled_polygon {fill})))')
            context={key:hashlib.sha256(b'context').hexdigest() for key in ['project_sha256','rules_sha256']}
            item=('silk_overlap','warning',tuple(sorted([uid,'text'])))
            fixtures=[]
            for stage in (0,1):
                folder=root/('zone-'+uid)/f'{stage}-0000';folder.mkdir(parents=True)
                for suffix in ['.kicad_pro','.kicad_dru']:(folder/after.with_suffix(suffix).name).write_bytes(b'context')
                rows=[] if stage==0 else [dict(type=item[0],severity=item[1],items=[{'uuid':u} for u in item[2]])]
                report=folder/'drc.json';report.write_text(json.dumps({'violations':rows}))
                fixtures.append(dict(stage=stage,item_uuid='text',report_sha256=hashlib.sha256(report.read_bytes()).hexdigest(),identities=[] if stage==0 else [item]))
            result=dict(version='10.0.6',before_sha256=hashlib.sha256(before.read_bytes()).hexdigest(),after_sha256=hashlib.sha256(after.read_bytes()).hexdigest(),zone_silk_scope_complete=True,zones=[dict(uuid=uid,layer='F.Cu',native_added_shape_empty=False,native_silk_pairs=dict(selected_item_uuids=['text'],fixtures=fixtures,before_identities=[],after_identities=[item],new_identities=[item]))],new_zone_silk_identities=[item])
            (root/'result.json').write_text(json.dumps(result))
            with self.assertRaisesRegex(ValueError,'new complete native zone'):
                zone_evidence(root,before,after,context)
            pairs=result['zones'][0]['native_silk_pairs']
            pairs['artwork_batch_size']=16
            (root/'result.json').write_text(json.dumps(result))
            with self.assertRaisesRegex(ValueError,'paired batch fixture'):
                zone_evidence(root,before,after,context)
            del pairs['artwork_batch_size']
            pairs['native_geometry_method']='exact_native_coordinates_no_arcs'
            pairs['source_geometry_sha256']={'0':'a'*64,'1':'b'*64}
            for f in pairs['fixtures']:f['native_geometry_sha256']=pairs['source_geometry_sha256'][str(f['stage'])]
            pairs['fixtures'][1]['native_geometry_sha256']='c'*64
            (root/'result.json').write_text(json.dumps(result))
            with self.assertRaisesRegex(ValueError,'geometry signature mismatch'):
                zone_evidence(root,before,after,context)
            result['zone_silk_scope_complete']=False;(root/'result.json').write_text(json.dumps(result))
            with self.assertRaisesRegex(ValueError,'classification incomplete'):
                zone_evidence(root,before,after,context)

    def test_opt_in_batching_retains_all_native_audit_commands(self):
        from unittest.mock import patch
        from scripts.pcbgen.complete_native_warnings import audit_current_reports
        root=Path(__file__).resolve().parents[2]
        board=root/'boards/osc-core/osc-core.kicad_pcb'
        with tempfile.TemporaryDirectory(dir=root) as folder:
            for size in (1,16):
                with patch('scripts.pcbgen.complete_native_warnings.subprocess.run') as run,patch('scripts.pcbgen.complete_native_warnings.complete_reports',return_value=({}, {}, {})):
                    audit_current_reports(board,board,{}, {},Path(folder)/str(size),zone_batch_size=size)
                    self.assertEqual(run.call_count,4)
                    commands=[c.args[0] for c in run.call_args_list]
                    self.assertIn('scripts/pcbgen/audit_hole_pairs.py',commands[0])
                    self.assertIn('scripts/pcbgen/audit_hole_pairs.py',commands[1])
                    self.assertIn('scripts/pcbgen/audit_added_mask.py',commands[2])
                    self.assertIn('scripts/pcbgen/audit_zone_silk_scope.py',commands[3])
                    self.assertEqual('--batch-size' in commands[3],size!=1)
                    if size!=1:self.assertEqual(commands[3][-3:],['--classify','--batch-size','16'])
            with self.assertRaises(ValueError):
                audit_current_reports(board,board,{}, {},Path(folder)/'invalid',zone_batch_size=8)

    def test_new_via_audit_cannot_hide_changed_outer_zone_fill(self):
        def board(layer,fill):return f'(kicad_pcb (zone (layer "{layer}") (filled_polygon (pts {fill}))))'
        unchanged_silk_zones(board('F.Cu','old'),board('F.Cu','old'))
        unchanged_silk_zones(board('In1.Cu','old'),board('In1.Cu','new'))
        for layer in ('F.Cu','B.Cu','F.SilkS','B.Mask'):
            with self.subTest(layer=layer),self.assertRaisesRegex(ValueError,'zone fills changed'):
                unchanged_silk_zones(board(layer,'old'),board(layer,'new'))

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
