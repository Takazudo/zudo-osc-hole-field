import copy
import unittest
from scripts.pcbgen.zone_batch_evidence import validate_coverage,normalized,artwork_ids

class PairedBatchEvidenceTests(unittest.TestCase):
    def setUp(self):
        self.pairs=dict(artwork_batch_size=2,selected_item_uuids=['a','b','c'],fixtures=[
            dict(stage=stage,batch_index=i,item_uuids=ids) for stage in (0,1) for i,ids in enumerate([['a','b'],['c']])])

    def test_exact_both_stage_coverage_and_tail(self):
        self.assertEqual(len(validate_coverage(self.pairs)),4)

    def test_missing_duplicate_reordered_unknown_and_wrong_stage_reject(self):
        for kind in ('missing','duplicate','reorder','unknown','stage','boolean'):
            p=copy.deepcopy(self.pairs)
            if kind=='missing':p['fixtures'].pop()
            if kind=='duplicate':p['fixtures'][-1]=copy.deepcopy(p['fixtures'][0])
            if kind=='reorder':p['fixtures'].reverse()
            if kind=='unknown':p['fixtures'][0]['item_uuids']=['x','b']
            if kind=='stage':p['fixtures'][0]['stage']=2
            if kind=='boolean':p['fixtures'][0]['stage']=False
            with self.subTest(kind=kind),self.assertRaises(ValueError):validate_coverage(p)

    def test_invalid_sizes_duplicate_scope_and_identity_reject(self):
        for size in (1,17,True,2.5):
            p=copy.deepcopy(self.pairs);p['artwork_batch_size']=size
            with self.assertRaises(ValueError):validate_coverage(p)
        self.pairs['selected_item_uuids']=['a','a','c']
        with self.assertRaises(ValueError):validate_coverage(self.pairs)
        with self.assertRaises(ValueError):normalized([['silk_overlap','warning',['a']],['silk_overlap','warning',['a']]])

    def test_artwork_excludes_copper_and_outline_but_rejects_ambiguous_uuid(self):
        uid='00000000-0000-4000-8000-000000000001'
        text=f'(kicad_pcb (footprint (uuid "{uid}")) (gr_line (layer "Edge.Cuts")) (segment (uuid "{uid}")))'
        self.assertEqual(artwork_ids(text),{uid})
        with self.assertRaises(ValueError):artwork_ids(text[:-1]+f'(gr_text "x" (uuid "{uid}")))')


class BatchArtifactBindingTests(unittest.TestCase):
    def test_complete_artifact_binding_rejects_fixture_context_version_severity_and_caps(self):
        import contextlib,hashlib,io,json,tempfile,zipfile
        from pathlib import Path
        from unittest.mock import patch
        from scripts.pcbgen import zone_batch_evidence as evidence
        from scripts.pcbgen.audit_zone_silk_scope import zone_fixture_parts,zone_fixture_batch_text
        sha=lambda b:hashlib.sha256(b).hexdigest()
        zone='00000000-0000-4000-8000-000000000001';art='00000000-0000-4000-8000-000000000002'
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder);sources=[]
            context={'.kicad_pro':json.dumps({'board':{'design_settings':{'rules':{'min_silk_clearance':0}}}}).encode(),'.kicad_dru':b'(version 1)'}
            for stage in (0,1):
                d=root/str(stage);d.mkdir();p=d/'osc-core.kicad_pcb'
                p.write_text(f'(kicad_pcb (zone (uuid "{zone}") (layer "F.Cu") (polygon (pts (xy 0 0))) (filled_polygon (pts (xy {stage+1} 1)))) (gr_text "x" (uuid "{art}") (layer "F.SilkS")))')
                for suffix,data in context.items():p.with_suffix(suffix).write_bytes(data)
                sources.append(p)
            fixtures=[];files={};prefix='issue189-paired-zone-batches/'
            for stage,p in enumerate(sources):
                sub=f'zone-{zone}/{stage}-batch-0000/';parts=zone_fixture_parts(p.read_text(),zone,{art});pcb=zone_fixture_batch_text(parts,[art]).encode()
                report=json.dumps({'kicad_version':'10.0.6','included_severities':['error','warning','exclusion'],'violations':[]}).encode()
                files[sub+p.name]=pcb;files[sub+'drc.json']=report
                for suffix,data in context.items():files[sub+p.stem+suffix]=data
                fixtures.append(dict(stage=stage,batch_index=0,item_uuids=[art],fixture_sha256=sha(pcb),report_sha256=sha(report),native_geometry_sha256='ab'[stage]*64,identities=[]))
            pairs=dict(artwork_batch_size=16,selected_item_uuids=[art],fixtures=fixtures,conservative_margin_nm=5000000,native_geometry_method='exact_native_coordinates_no_arcs',source_geometry_sha256={'0':'a'*64,'1':'b'*64},before_identities=[],after_identities=[],new_identities=[])
            result=dict(version='10.0.6',before_sha256=sha(sources[0].read_bytes()),after_sha256=sha(sources[1].read_bytes()),zone_silk_scope_complete=True,zones=[dict(uuid=zone,layer='F.Cu',native_added_shape_empty=False,native_added_outline_count=1,native_silk_pairs=pairs)],new_zone_silk_identities=[])
            files[f'zone-{zone}-scope.json']=json.dumps(dict(zone_uuid=zone,layer='F.Cu',selected_item_uuids=[art],artwork_count=1,conservative_margin_nm=5000000,growth_boxes_nm=[[0,0,10,10]])).encode()
            for mode in ('valid','fixture','context','version','severity','cap','new-warning'):
                f=copy.deepcopy(files);r=copy.deepcopy(result);target=f'zone-{zone}/1-batch-0000/';receipt=r['zones'][0]['native_silk_pairs']['fixtures'][1]
                if mode=='fixture':
                    f[target+'osc-core.kicad_pcb']+=b'changed';receipt['fixture_sha256']=sha(f[target+'osc-core.kicad_pcb'])
                if mode=='context':f[target+'osc-core.kicad_pro']=b'changed'
                if mode in ('version','severity','cap','new-warning'):
                    report=json.loads(f[target+'drc.json'])
                    if mode=='version':report['kicad_version']='9.0.2'
                    if mode=='severity':report['included_severities']=['warning']
                    if mode=='cap':report['violations']=[dict(type='silk_overlap',severity='warning',items=[])]*199
                    if mode=='new-warning':
                        ids=sorted([zone,art]);identity=['silk_overlap','warning',ids]
                        report['violations']=[dict(type=identity[0],severity=identity[1],items=[dict(uuid=i) for i in ids])]
                        receipt['identities']=[identity]
                        for key in ('after_identities','new_identities'):r['zones'][0]['native_silk_pairs'][key]=[identity]
                        r['new_zone_silk_identities']=[identity]
                    f[target+'drc.json']=json.dumps(report).encode();receipt['report_sha256']=sha(f[target+'drc.json'])
                f['result.json']=json.dumps(r).encode();archive=root/'evidence.zip'
                with zipfile.ZipFile(archive,'w') as z:
                    for name,data in f.items():z.writestr(prefix+name,data)
                with self.subTest(mode=mode),patch.object(evidence,'BEFORE',r['before_sha256']),patch.object(evidence,'AFTER',r['after_sha256']),contextlib.redirect_stdout(io.StringIO()):
                    proof=root/('proof-'+mode)
                    for name,data in f.items():
                        path=proof/name;path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
                    from scripts.pcbgen.complete_native_warnings import zone_evidence
                    gate_context={'project_sha256':sha(context['.kicad_pro']),'rules_sha256':sha(context['.kicad_dru'])}
                    if mode in ('valid','new-warning'):
                        evidence.main(archive,sha(archive.read_bytes()),*sources,root/'receipt.json')
                        out=json.loads((root/'receipt.json').read_text());self.assertFalse(out['adopted']);self.assertTrue(out['full_paired_zone_coverage'])
                        self.assertEqual(len(out['new_zone_silk_identities']),1 if mode=='new-warning' else 0)
                        if mode=='valid':
                            self.assertEqual(zone_evidence(proof,*sources,gate_context)['zone_fixture_count'],2)
                        else:
                            with self.assertRaisesRegex(ValueError,'new complete native zone'):
                                zone_evidence(proof,*sources,gate_context)
                    else:
                        with self.assertRaises(ValueError):evidence.main(archive,sha(archive.read_bytes()),*sources,root/'receipt.json')
                        with self.assertRaises(ValueError):zone_evidence(proof,*sources,gate_context)
            # A reviewed cut never changes or skips either paired native fixture.
            cut='00000000-0000-4000-8000-000000000003'
            original=sources[0].read_text()
            sources[0].write_text(original[:-1]+f'(segment (uuid "{cut}"))'+')')
            result['before_sha256']=sha(sources[0].read_bytes())
            files['result.json']=json.dumps(result).encode()
            proof=root/'reviewed-cut-proof'
            for name,data in files.items():
                p=proof/name;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
            with self.assertRaisesRegex(ValueError,'additive'):
                zone_evidence(proof,*sources,gate_context)
            self.assertEqual(zone_evidence(proof,*sources,gate_context,reviewed_removed_uuids=[cut])['zone_fixture_count'],2)

if __name__=='__main__':unittest.main()
