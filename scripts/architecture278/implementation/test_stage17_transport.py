import copy
import json
import unittest
import stage17_transport as m


class Transport(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.inp=json.loads((m.assets.previous.OUT/'inputs-report.json').read_text())
        cls.files,cls.bindings,cls.rows=m.build_transport(cls.inp)

    def test_all270nodes_once(self):
        ids=[v for row in self.rows.values() for v in row['source_nodes'].values()]
        self.assertEqual(len(ids),270);self.assertEqual(len(set(ids)),270)
        self.assertEqual(set(ids),{k for k,v in self.inp['transport_contract']['nodes'].items()if v['kind']!='source'})
        self.assertEqual(len(self.rows),32)

    def test_exact_din_identities_and_no_footprint_guess(self):
        for ref,mpn in [('J17909','09032966824'),('J17910','09031966922')]:
            row=self.rows[ref];self.assertEqual(row['selected_mpn'],mpn)
            self.assertEqual(len(row['pins']),96)
            self.assertEqual(row['pins'],self.inp['transport_contract']['DIN_pinmap'])
            self.assertEqual(self.bindings[ref]['footprint_lib_id'],'')
            self.assertEqual(row['footprint_status'],'UNBOUND_SCHEMATIC_ONLY')

    def test_gh_mp_pins_are_preserved_nc(self):
        for ref in ['J'+str(n)for n in range(17901,17909)]:
            row=self.rows[ref];self.assertIsNone(row['pins']['MP1']);self.assertIsNone(row['pins']['MP2'])
            self.assertTrue(row['in_bom']);self.assertTrue(row['on_board'])
            self.assertTrue(self.bindings[ref]['footprint_lib_id'].startswith('A01Candidate:'))

    def test_land_annotations_not_parts_or_inferred_mpn(self):
        tails=[row for row in self.rows.values() if row['ref'].startswith('TP')]
        self.assertEqual(len(tails),22)
        for row in tails:
            self.assertFalse(row['in_bom']);self.assertFalse(row['on_board']);self.assertIsNone(row['selected_mpn'])
            self.assertEqual(len(row['pins']),1)
            self.assertEqual(self.bindings[row['ref']]['footprint_lib_id'],'')

    def test_exact_attribute_mapping_and_passive_pins(self):
        for ref,row in self.rows.items():
            self.assertEqual(json.loads(row['unit_records'][0]['attributes']['SourceGraphNodes']),row['source_nodes'])
            self.assertTrue(all(p['electrical_type']=='passive'for p in self.bindings[ref]['pins'].values()))
            self.assertEqual(self.bindings[ref]['symbol_units'],[1])

    def test_graph_pin_net_corruption_rejected(self):
        for mutation in ('net','pin'):
            inp=copy.deepcopy(self.inp);inp['transport_contract']['nodes']['DIN:rear:c1'][mutation]='WRONG'
            with self.assertRaises(ValueError):m.build_transport(inp)

    def test_unrepresented_transport_node_rejected(self):
        inp=copy.deepcopy(self.inp);inp['transport_contract']['nodes']['extra']={'kind':'EXTRA','pin':'1','net':None}
        with self.assertRaises(ValueError):m.build_transport(inp)


if __name__=='__main__':unittest.main()
