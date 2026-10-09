"""Identity-based benchmark selection and connectivity regression gates."""
import unittest
from scripts.pcbgen.benchmark_obstacles import endpoints,splits,select
from scripts.pcbgen.route_jack_grid import promotion_gate
from scripts.pcbgen.test_grid_router import crossing_board

class BenchmarkTests(unittest.TestCase):
    def test_equal_edge_count_cannot_hide_a_different_disconnection(self):
        before=crossing_board();before['islands']={'A':[['a0','a1']], 'B':[['b0'],['b1']]}
        after={**before,'islands':{'A':[['a0'],['a1']], 'B':[['b0','b1']]}}
        self.assertEqual(splits(before,after),[{'net':'A','previously_connected_pads':['a0','a1']}])
    def test_closed_nets_omitted_from_open_table_are_protected(self):
        before=crossing_board();before['islands']={}
        after={**before,'islands':{'A':[['a0'],['a1']]}}
        self.assertEqual(splits(before,after)[0]['net'],'A')
    def test_selection_records_stable_pad_identities(self):
        b=crossing_board();selected=select(b,2)
        self.assertEqual({x['net'] for x in selected},{'A','B'})
        self.assertTrue(all(p['uuid'] and p['ref'] and p['pad'] for x in selected for g in x['islands'] for p in g))

    def test_promotion_gate_rejects_warning_and_membership_regressions(self):
        before=crossing_board();before['open_edges']=2
        after={**before,'islands':{},'open_edges':0}
        clean={'violations':[]}
        self.assertTrue(promotion_gate(before,after,clean,clean)['adopted'])
        warning={'violations':[{'type':'hole_to_hole','severity':'warning','items':[{'uuid':'v'}]}]}
        gate=promotion_gate(before,after,clean,warning)
        self.assertFalse(gate['adopted']);self.assertTrue(gate['new_warning_identities'])
        self.assertTrue(promotion_gate(before,after,warning,warning)['adopted'])

    def test_promotion_gate_rejects_native_errors_and_parity(self):
        before={**crossing_board(),'open_edges':2};after={**before,'islands':{},'open_edges':0}
        clean={'violations':[]}
        for drc in ({'violations':[{'type':'clearance','severity':'error'}]},
                    {'violations':[],'schematic_parity':[{'type':'missing_pad'}]}):
            self.assertFalse(promotion_gate(before,after,clean,drc)['adopted'])
