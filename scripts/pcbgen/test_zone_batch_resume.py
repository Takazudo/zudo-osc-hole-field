import copy,hashlib,json,tempfile,unittest
from pathlib import Path
from scripts.pcbgen.zone_batch_resume import completed_prefix,validate_source,verified_report

class ResumeTests(unittest.TestCase):
    def test_only_exact_ordered_prefix_in_same_scope(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);scope={'selected_item_uuids':['a','b','c']};batches=[['a','b'],['c']]
            (root/'zone-z-scope.json').write_text(json.dumps(scope))
            rows=[dict(stage=0,batch_index=0,item_uuids=['a','b']),dict(stage=0,batch_index=1,item_uuids=['c'])]
            progress=root/'zone-z-progress.jsonl'
            progress.write_text('\n'.join(map(json.dumps,rows)))
            self.assertEqual(set(completed_prefix(root,'z',scope,batches)),{(0,0),(0,1)})
            for bad in (rows[::-1],rows+[rows[0]],[rows[1]],[dict(rows[0],stage=False)],[dict(rows[0],item_uuids=['x'])]):
                progress.write_text('\n'.join(map(json.dumps,bad)))
                with self.assertRaises(ValueError):completed_prefix(root,'z',scope,batches)
            with self.assertRaises(ValueError):completed_prefix(root,'z',{},batches)

    def test_source_version_and_existing_destination_reject(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);a=root/'a';b=root/'b';a.write_bytes(b'a');b.write_bytes(b'b')
            result=dict(version='10.0.6',before_sha256=hashlib.sha256(b'a').hexdigest(),after_sha256=hashlib.sha256(b'b').hexdigest())
            (root/'result.json').write_text(json.dumps(result))
            self.assertEqual(validate_source(root,a,b,16,root/'new'),root)
            for size in (1,True,8,4.0):
                with self.assertRaises(ValueError):validate_source(root,a,b,size,root/'new')
            with self.assertRaises(ValueError):validate_source(root,a,b,16,root)
            a.write_bytes(b'changed')
            with self.assertRaises(ValueError):validate_source(root,a,b,16,root/'new')

    def test_reuse_preserves_findings_and_rejects_altered_bindings(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d);saved=root/'zone-z/0-batch-0000';saved.mkdir(parents=True)
            current=root/'new/board.kicad_pcb';current.parent.mkdir();current.write_bytes(b'fixture')
            (saved/current.name).write_bytes(current.read_bytes())
            for s in ('.kicad_pro','.kicad_dru'):
                current.with_suffix(s).write_bytes(s.encode());(saved/current.with_suffix(s).name).write_bytes(s.encode())
            finding=dict(type='silk_over_copper',severity='warning',items=[{'uuid':'z'},{'uuid':'a'}])
            report=dict(kicad_version='10.0.6',included_severities=['error','warning','exclusion'],violations=[finding])
            data=json.dumps(report).encode();(saved/'drc.json').write_bytes(data)
            sha=lambda x:hashlib.sha256(x).hexdigest()
            row=dict(fixture_sha256=sha(b'fixture'),report_sha256=sha(data),native_geometry_sha256='geometry',identities=[['silk_over_copper','warning',['a','z']]])
            self.assertEqual(verified_report(root,'z','0-batch-0000',current,row,'geometry'),data)
            for key,value in [('fixture_sha256','wrong'),('report_sha256','wrong'),('native_geometry_sha256','wrong'),('identities',[])]:
                with self.subTest(key=key),self.assertRaises(ValueError):verified_report(root,'z','0-batch-0000',current,dict(row,**{key:value}),'geometry')
            for change in ({'kicad_version':'9.0.2'},{'included_severities':['warning']},{'violations':[finding]*199}):
                changed=json.dumps(dict(report,**change)).encode();(saved/'drc.json').write_bytes(changed)
                with self.assertRaises(ValueError):verified_report(root,'z','0-batch-0000',current,dict(row,report_sha256=sha(changed)),'geometry')
            (saved/'drc.json').write_bytes(data)
            current.with_suffix('.kicad_pro').write_bytes(b'changed')
            with self.assertRaises(ValueError):verified_report(root,'z','0-batch-0000',current,row,'geometry')
