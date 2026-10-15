import copy
import json
import unittest
import stage8_assessment as a

class CriticalCorridorReviewTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((a.OUT/'locality-report.json').read_text())
        cls.mechanical=json.loads((a.OUT/'mechanical-report.json').read_text())
    def test_final_obstacle_inventory(self):
        result=a.verify_corridors(self.report,self.mechanical)
        self.assertEqual(10,result['critical_connections'])
        self.assertEqual(10,result['compatible_checked_corridors'])
    def test_omitted_connection(self):
        report=copy.deepcopy(self.report);report['corridors'].pop()
        with self.assertRaisesRegex(ValueError,'inventory'):a.verify_corridors(report,self.mechanical)
    def test_pad_endpoint_detached(self):
        report=copy.deepcopy(self.report);report['corridors'][0]['endpoints'][0]['pad_xyz_mm'][0]+=.1
        with self.assertRaisesRegex(ValueError,'detached'):a.verify_corridors(report,self.mechanical)
    def test_actual_substrate_cut_rejects_trace(self):
        report=copy.deepcopy(self.report);segment=report['corridors'][0]['segments'][0]
        x,y=segment['from_xy_mm'];report['obstacles'].append({'id':'added-cut','kind':'substrate','ref':'cut','layers':[0,1],'box_mm':[x-.1,y-.1,x+.1,y+.1]})
        mechanical=copy.deepcopy(self.mechanical);mechanical['manufacturing_sweep_bounds'].append({'id':'added-cut','board':'X1-jack','box_mm':[x-.1,y-.1,x+.1,y+.1]})
        with self.assertRaisesRegex(ValueError,'added-cut'):a.verify_corridors(report,mechanical)
    def test_missing_actual_substrate_obstacle(self):
        report=copy.deepcopy(self.report);report['obstacles']=[o for o in report['obstacles']if o['kind']!='substrate']
        with self.assertRaisesRegex(ValueError,'substrate obstacles'):a.verify_corridors(report,self.mechanical)
    def test_other_net_copper_rejects_trace(self):
        report=copy.deepcopy(self.report);segment=report['corridors'][0]['segments'][0]
        x,y=segment['from_xy_mm'];report['obstacles'].append({'id':'different-net','kind':'reserved_trace','net':'OTHER','ref':'other','layers':[segment['layer']],'box_mm':[x-.1,y-.1,x+.1,y+.1]})
        with self.assertRaisesRegex(ValueError,'reservations'):a.verify_corridors(report,self.mechanical)
    def test_via_blocks_both_faces(self):
        report=copy.deepcopy(self.report);row=next(r for r in report['corridors']if r['vias']);x,y=row['vias'][0]['xy_mm']
        report['obstacles'].append({'id':'via-conflict','kind':'reserved_via','net':'OTHER','ref':'other','layers':[0,1],'box_mm':[x-.1,y-.1,x+.1,y+.1]})
        with self.assertRaisesRegex(ValueError,'reservations'):a.verify_corridors(report,self.mechanical)
    def test_polygon_and_segment_disagreement(self):
        report=copy.deepcopy(self.report);report['corridors'][0]['segments'][0]['layer']=1-report['corridors'][0]['segments'][0]['layer']
        with self.assertRaisesRegex(ValueError,'disagreement'):a.verify_corridors(report,self.mechanical)
    def test_via_inventory_detached(self):
        report=copy.deepcopy(self.report);row=next(r for r in report['corridors']if r['vias']);row['vias'][0]['xy_mm'][0]+=.1
        with self.assertRaisesRegex(ValueError,'via positions'):a.verify_corridors(report,self.mechanical)
    def test_wrong_endpoint_face(self):
        report=copy.deepcopy(self.report);report['corridors'][0]['endpoints'][0]['layers']=[0,1]
        with self.assertRaisesRegex(ValueError,'endpoint layers'):a.verify_corridors(report,self.mechanical)
    def test_missing_other_source_pad(self):
        report=copy.deepcopy(self.report);i=next(i for i,o in enumerate(report['obstacles'])if o['kind']=='pad');report['obstacles'].pop(i)
        with self.assertRaisesRegex(ValueError,'footprint pad obstacles'):a.verify_corridors(report,self.mechanical)
    def test_missing_reserved_copper(self):
        report=copy.deepcopy(self.report);i=next(i for i,o in enumerate(report['obstacles'])if o['kind']=='reserved_trace');report['obstacles'].pop(i)
        with self.assertRaisesRegex(ValueError,'reservations'):a.verify_corridors(report,self.mechanical)
    def test_wrong_reported_length(self):
        report=copy.deepcopy(self.report);report['corridors'][0]['copper_centreline_mm']+=1
        with self.assertRaisesRegex(ValueError,'copper length'):a.verify_corridors(report,self.mechanical)

if __name__=='__main__':unittest.main()
