import unittest
from scripts.pcbgen.copper_identity import reject_new_uuid_collisions,retention


class CopperIdentityTests(unittest.TestCase):
    def test_retention_counts_distinct_geometry_with_same_uuid(self):
        a={'uuid':'duplicate','net':'AGND','xy':[1,2]};b={**a,'xy':[3,4]}
        before={'tracks':[a,b],'vias':[]};after={'tracks':[b,a],'vias':[]}
        r=retention(before,after)
        self.assertEqual((r['before'],r['identical'],r['before_unique_uuids']),(2,2,1))
        self.assertEqual(r['changed_existing_uuids'],[])
        r=retention(before,{'tracks':[b],'vias':[]})
        self.assertEqual(r['removed_objects'],1);self.assertEqual(r['changed_existing_uuids'],['duplicate'])

    def test_new_ids_cannot_alias_existing_or_each_other(self):
        for existing,rows in ((['a'],[{'uuid':'a'}]),([],[{'uuid':'a'},{'uuid':'a'}])):
            with self.assertRaises(ValueError):reject_new_uuid_collisions(existing,rows)
        reject_new_uuid_collisions(['a','a'],[{'uuid':'b'}])  # unchanged legacy copper stays
