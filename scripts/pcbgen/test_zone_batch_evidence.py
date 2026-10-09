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

if __name__=='__main__':unittest.main()
