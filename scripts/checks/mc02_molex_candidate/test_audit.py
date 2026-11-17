import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest import mock
import audit as a

class CandidateTests(unittest.TestCase):
    def setUp(self):
        self.e=json.loads((a.HERE/'evidence.json').read_text())
        self.links=json.loads((a.ROOT/a.GATE).read_text())['links']
    def test_exact_table_and_links(self):
        self.assertEqual(len(a.validate(self.e,self.links)),28)
        self.assertEqual(self.e['binding']['mpn'],'150200075')
    def test_wrong_mpn_type_or_reference(self):
        for k,v in [('mpn','150200175'),('type','D'),('sheet',2),('contacts',16),('revision','A')]:
            e=copy.deepcopy(self.e);e['binding'][k]=v
            with self.assertRaisesRegex(ValueError,'binding'):a.validate(e,self.links)
    def test_width_thickness_swap(self):
        self.e['dimensions']['tail_thickness']=self.e['dimensions']['conductor_width']
        with self.assertRaisesRegex(ValueError,'semantic'):a.validate(self.e,self.links)
    def test_wrong_units(self):
        self.e['dimensions']['total_width']['unit']='inch'
        with self.assertRaisesRegex(ValueError,'mm'):a.validate(self.e,self.links)
    def test_nominal_cannot_be_interval(self):
        self.e['nominal_layers']['tolerance']='0'
        with self.assertRaisesRegex(ValueError,'nominal'):a.validate(self.e,self.links)
    def test_wrong_or_duplicate_link_set(self):
        self.e['candidate_link_ids'][0]=self.e['candidate_link_ids'][1]
        with self.assertRaisesRegex(ValueError,'28'):a.validate(self.e,self.links)
    def test_changed_receipt(self):
        self.e['prior_51mm_result_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'receipt'):a.validate(self.e,self.links)
    def test_closed_boundary_and_real_interval_excess(self):
        self.assertEqual(a.compare(self.e['dimensions']['tail_thickness'],{'unit':'mm','lower':'0.25','upper':'0.35'})['relation'],'CONTAINED')
        row=a.compare(self.e['dimensions']['total_width'],{'unit':'mm','lower':'4.43','upper':'4.57'})
        self.assertEqual((row['lower_shortfall_mm'],row['upper_excess_mm']),('0.03','0.03'))
    def test_changed_source_bytes_rejected(self):
        with mock.patch.object(a,'digest',return_value='0'*64):
            with self.assertRaisesRegex(ValueError,'source pin changed'):a.audit()

    def test_missing_source_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaises(FileNotFoundError):a.audit(Path(directory))
    def test_actual_source_comparison_never_qualifies(self):
        r=a.audit();rows={x['field']:x for x in r['comparisons']}
        self.assertEqual(rows['tail_thickness']['comparator_class'],'requirement')
        self.assertEqual(rows['exposed_length']['lower_shortfall_mm'],'0.30')
        self.assertEqual(rows['support_length']['comparison_scope'],'CONDITIONAL_DATUM_MAPPING')
        self.assertIsNone(rows['support_length']['actual_datum_mapping'])
        self.assertIsNone(r['stiffener']['guaranteed_interval_mm'])
        self.assertEqual(r['length']['candidate_interval_mm'],['49','53'])
        self.assertEqual(r['material_comparison']['candidate_copper_nominal_mm'],'0.10')
        self.assertEqual(r['material_comparison']['existing_model_copper_mm'],0.035)
        self.assertEqual(r['physical_compatibility'],'NOT_ESTABLISHED')
        self.assertEqual(r['terminal_positional_datum_conformity']['status'],'NOT_ASSESSED')
        self.assertEqual(r['finish']['plating_qualification'],'NOT_ESTABLISHED')

if __name__=='__main__':unittest.main()
