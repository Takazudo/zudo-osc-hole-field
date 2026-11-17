from collections import Counter
import copy
import json
from pathlib import Path
import tempfile
import unittest
from types import SimpleNamespace
from unittest import mock
import generate as g
import native_check as n


class FixtureTests(unittest.TestCase):
    def test_four_exact_counts_and_nominal_land_chain(self):
        for count in g.COUNTS:
            pads=g.pads(count);signal=pads[:count];tabs=pads[count:]
            self.assertEqual([p['number'] for p in signal],[str(i) for i in range(1,count+1)])
            self.assertEqual([p['number'] for p in tabs],['',''])
            self.assertEqual({tuple(p['size_mm']) for p in signal},{('0.3','1.3')})
            self.assertEqual({tuple(p['size_mm']) for p in tabs},{('1.8','2.2')})
            self.assertEqual({p['xy_mm'][1] for p in tabs},{'3.25'})
            positions=[n.nm(p['xy_mm'][0]) for p in signal]
            self.assertEqual(positions[0],-250000*(count-1))
            self.assertTrue(all(b-a==500000 for a,b in zip(positions,positions[1:])))
    def test_no_invented_courtyard_body_model_nets_or_apertures(self):
        text=g.render(8)
        for token in ('CrtYd','(model','(fp_line','(fp_poly','(net','AGND','F.Paste','F.Mask'):
            self.assertNotIn(token,text)
        self.assertIn(g.LABEL,text)
        self.assertEqual(text,g.render(8))
        self.assertEqual(text.count('(pad ""'),2)
    def test_wrong_variant_rejected(self):
        with self.assertRaises(ValueError):g.render(10)
    def test_exact_matrix_known_asymmetric_mounting_tab(self):
        # 8-way right tab at(3.65,3.25), origin(0,0).
        for face,angle,xy in [('F',0,(3650000,3250000)),('B',0,(3650000,-3250000)),
                              ('F',90,(3250000,-3650000)),('B',90,(-3250000,-3650000)),
                              ('F',180,(-3650000,-3250000)),('B',270,(3250000,3650000))]:
            self.assertIn(('',*xy,1800000,2200000,angle%180),n.expected_rows(8,face,angle,(0,0)))
        with self.assertRaises(ValueError):n.expected_rows(8,'F',45)
    def test_independent_literal_selected_variant_table(self):
        # Independently transcribed EDC sheet5 A/F/G, not generator output.
        for count,A,F,G in ((8,'3.5','5.5','9.1'),(14,'6.5','8.5','12.1'),
                            (26,'12.5','14.5','18.1'),(40,'19.5','21.5','25.1')):
            pads=g.pads(count);signals=pads[:count];left,right=pads[-2:]
            self.assertEqual(n.nm(signals[-1]['xy_mm'][0])-n.nm(signals[0]['xy_mm'][0]),n.nm(A))
            self.assertEqual(n.nm(right['xy_mm'][0])+900000-(n.nm(left['xy_mm'][0])-900000),n.nm(G))
            self.assertEqual(n.nm(right['xy_mm'][0])-900000-(n.nm(left['xy_mm'][0])+900000),n.nm(F))

    def test_native_checker_rejects_wrong_orientation_layers_or_scope(self):
        pcb=SimpleNamespace(F_Cu=0,B_Cu=31,PAD_ATTRIB_SMD=1,PAD_SHAPE_RECT=2)
        rows=list(n.expected_rows(8,'F',90).elements());pads=[]
        for number,x,y,w,h,angle in rows:
            pads.append(SimpleNamespace(GetNumber=lambda value=number:value,
                GetPosition=lambda x=x,y=y:SimpleNamespace(x=x,y=y),
                GetSize=lambda w=w,h=h:SimpleNamespace(x=w,y=h),GetOrientationDegrees=lambda value=angle:value,
                GetNetCode=lambda:0,GetNetname=lambda:'',GetLayerSet=lambda:SimpleNamespace(Seq=lambda:[0]),
                GetAttribute=lambda:1,GetShape=lambda:2))
        fp=SimpleNamespace(Pads=lambda:pads,GetLayer=lambda:0,GetOrientationDegrees=lambda:90,
            GetLibDescription=lambda:g.DESCRIPTION,GraphicalItems=lambda:[],Models=lambda:[])
        self.assertEqual(n.check_footprint(pcb,fp,8,'F',90)['contacts'],8)
        with mock.patch.object(pads[0],'GetOrientationDegrees',return_value=0):
            with self.assertRaisesRegex(ValueError,'mismatch'):n.check_footprint(pcb,fp,8,'F',90)
        with mock.patch.object(pads[0],'GetLayerSet',return_value=SimpleNamespace(Seq=lambda:[0,31])):
            with self.assertRaisesRegex(ValueError,'layer'):n.check_footprint(pcb,fp,8,'F',90)
        with mock.patch.object(pads[0],'GetNetCode',return_value=1):
            with self.assertRaisesRegex(ValueError,'net'):n.check_footprint(pcb,fp,8,'F',90)
        wrong=SimpleNamespace(x=rows[0][1]+1000000,y=rows[0][2])
        with mock.patch.object(pads[0],'GetPosition',return_value=wrong):
            with self.assertRaisesRegex(ValueError,'contacts=8 face=F angle=90.*mismatch') as caught:n.check_footprint(pcb,fp,8,'F',90)
            self.assertIn('unexpected',str(caught.exception))
            self.assertIn('missing',str(caught.exception))
            self.assertLess(len(str(caught.exception)),1500)
        for description in ('approved', ''):
            with mock.patch.object(fp,'GetLibDescription',return_value=description):
                with self.assertRaisesRegex(ValueError,'contacts=8 face=F angle=90.*description'):n.check_footprint(pcb,fp,8,'F',90)
        del fp.GetLibDescription
        # Missing supported API fails closed; never fall back to a different field.
        fp.GetDescription=lambda:g.DESCRIPTION
        with self.assertRaises(AttributeError):n.check_footprint(pcb,fp,8,'F',90)

    def test_native_oracle_independent_of_generator_geometry(self):
        before=n.expected_rows(8,'B',90)
        with mock.patch.object(g,'pads',return_value=[{'number':'1','xy_mm':['999','999'],'size_mm':['1','1']}]) as pads:
            self.assertEqual(n.expected_rows(8,'B',90),before)
            pads.assert_not_called()

    def test_fresh_output_and_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);target=root/'.circuit-cache/fixture';source={'fixture':'source'}
            with mock.patch.object(g,'verify_source',return_value=source):
                receipt=g.generate(target,root)
                self.assertEqual(g.verify_fixture(target,root),receipt)
                self.assertEqual(receipt['native_validation'],'NOT_RUN')
                with self.assertRaisesRegex(ValueError,'fresh'):g.generate(target,root)
                p=target/receipt['footprints'][0]['path'];p.write_text(p.read_text().replace('(pad "1"','(pad "99"'))
                with self.assertRaisesRegex(ValueError,'bytes changed'):g.verify_fixture(target,root)
    def test_scope_promotion_or_checker_drift_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);target=root/'.circuit-cache/fixture'
            with mock.patch.object(g,'verify_source',return_value={'source':'fixture'}):
                receipt=g.generate(target,root);path=target/'fixture.json'
                for key,value in [('status','APPROVED'),('native_validation','PASS'),('endpoint_bindings',['endpoint']),('native_checker_sha256','0'*64)]:
                    changed=copy.deepcopy(receipt);changed[key]=value;path.write_text(json.dumps(changed))
                    with self.assertRaises(ValueError):g.verify_fixture(target,root)
    def test_output_outside_cache_and_symlink_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);cache=root/'.circuit-cache';cache.mkdir()
            with self.assertRaises(ValueError):g.safe_target(root/'production.pretty',root)
            link=cache/'dangling';link.symlink_to(cache/'absent')
            with self.assertRaises(ValueError):g.safe_target(link,root)
    def test_missing_source_pin_fails_before_output_creation(self):
        with tempfile.TemporaryDirectory() as directory:
            root=Path(directory);target=root/'.circuit-cache/fixture'
            with mock.patch.object(g,'verify_source',side_effect=ValueError('source pin changed')):
                with self.assertRaises(ValueError):g.generate(target,root)
            self.assertFalse(target.exists())
    def test_native_work_directory_collision_precedes_pcbnew_import(self):
        with tempfile.TemporaryDirectory() as directory:
            target=Path(directory);(target/'native-results').mkdir()
            with mock.patch.object(g,'verify_fixture',return_value={}):
                with self.assertRaises(FileExistsError):n.run(target)
    def test_actual_source_metadata_pins(self):
        source=g.verify_source()
        self.assertEqual(source['pdf_sha256'],g.PDF_SHA)


if __name__=='__main__':unittest.main()
