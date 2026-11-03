import copy
from collections import Counter
import unittest
import candidate as c
from check_source import validate_paths

class CandidateTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec=c.read('implementation/candidate.json')
        cls.report,cls.netlist=c.build()
    def reject(self,change):
        spec=copy.deepcopy(self.spec);change(spec)
        with self.assertRaises(ValueError):c.build(spec)
    def test_endpoint_parity(self):
        expected=Counter((p['ref'],str(p['unit']),pin,net,p['proposed_owner']) for p in c.read('interface-contract.json')['parts'] for pin,net in p['pins'].items())
        self.assertEqual(expected,Counter(tuple(e) for e in self.netlist['endpoints']))
        self.assertEqual(38,len(self.netlist['NC_endpoints']))
    def test_all_source_units_and_physical_core(self):
        self.assertEqual(329,sum(len(p['units']) for p in self.netlist['packages']))
        self.assertEqual(154,len(self.report['rear_placements']))
        self.assertEqual(6,len(self.report['mechanical_model']['trim_axes']))
    def test_adjacent_pin_returns_and_exclusivity(self):
        pins={p['pin']:p for p in self.report['rear_connector_pinout']}
        self.assertEqual(96,len(pins))
        for pin,p in pins.items():
            if p['net'] and p['net']!='AGND':self.assertEqual('AGND',pins['b'+pin[1:]]['net'])
        self.assertEqual(26,sum(p['net']=='AGND' for p in pins.values()))
    def test_transport_preserves_duplicate_returns(self):
        actual=Counter(n for h in self.report['front_links'] for n in h['pins'].values())
        original=Counter(n for h in c.read('interface-contract.json')['harnesses'] for n in h['faces'][0]['pin_map'].values())
        self.assertEqual(Counter({'/O1/LOCAL_REF5':2,'/O1/LOCAL_REFN5':1}),actual-original)
        self.assertFalse(original-actual)
        self.assertEqual((17,54,108),tuple(self.report['transport_subtotal'][k] for k in ('harnesses','conductors','crimps')))
    def test_route_arithmetic_not_acceptance(self):
        self.assertFalse(self.report['overlength_paths'])
        for r in self.report['paths']:
            total=sum(r[k] for k in ('front_trace_allocation_mm','front_flex_mm','middle_allocation_mm','connector_allocation_mm','rear_pad_allocation_mm'))
            self.assertAlmostEqual(total,r['total_mm'])
            self.assertIsNone(r['capacitance_pF'])
        self.assertIn('NOT ACCEPTED',self.report['status'])
        self.assertEqual(9,len(self.report['unmodeled_shared_middle_nets']))
    def test_missing_package(self):self.reject(lambda s:s['clusters'][0]['refs'].pop())
    def test_duplicated_package(self):self.reject(lambda s:s['clusters'][0]['refs'].append('U1112'))
    def test_feedback_moved_to_other_cluster(self):
        def mutate(s):s['clusters'][0]['refs'].remove('R1122');s['clusters'][1]['refs'].append('R1122')
        self.reject(mutate)
    def test_bypass_moved(self):
        def mutate(s):s['clusters'][0]['refs'].remove('C1142');s['clusters'][1]['refs'].append('C1142')
        self.reject(mutate)
    def test_nonfinite_geometry(self):self.reject(lambda s:s.update(front_flex_mm=float('nan')))
    def test_boolean_geometry(self):self.reject(lambda s:s.update(front_flex_mm=True))
    def test_weakened_limit(self):self.reject(lambda s:s.update(limit_mm=301))
    def test_shortened_connector_allocation(self):self.reject(lambda s:s.update(connector_path_mm=19.2))
    def test_cluster_overlap(self):self.reject(lambda s:s['clusters'][1].update(box_mm=s['clusters'][0]['box_mm']))
    def test_override_breaks_local_cluster(self):self.reject(lambda s:s['local_overrides_mm'].update(R1123=[90,145]))
    def test_missing_support(self):self.reject(lambda s:s['mechanical']['supports_mm'].pop())
    def test_missing_power_strap(self):self.reject(lambda s:s['mechanical']['power_boxes_mm'].pop())
    def test_connector_geometry_mismatch(self):self.reject(lambda s:s['connector'].update(centre_mm=[80,75]))
    def test_neighbor_collision(self):self.reject(lambda s:s['origins_mm'].update(O2=[100,122]))
    def test_off_panel(self):self.reject(lambda s:s['origins_mm'].update(O2=[250,122]))
    def test_cover_collision(self):self.reject(lambda s:s['mechanical'].update(cover_depth_mm=75))
    def test_stack_tolerance(self):self.reject(lambda s:s['mechanical'].update(stack_tolerance_mm=2))
    def test_short_withdrawal(self):self.reject(lambda s:s['mechanical'].update(withdrawal_mm=10))
    def test_understated_height(self):self.reject(lambda s:s['mechanical'].update(rear_height_bound_mm=1))
    def test_source_scope_guard(self):
        validate_paths(['design/architecture-278/implementation/candidate.json'])
        for p in ['boards/a','design/boards/a','design/grid/placements.lock.json','design/architecture-278/GATE.md','scripts/architecture278/extract.py','decision.json']:
            with self.assertRaises(ValueError):validate_paths([p])
    def test_unknown_maxima_retained(self):
        for path in self.report['preserved_power_paths']:
            self.assertTrue(all(v is None for v in path['state_maxima_mA'].values()))
        self.assertEqual(.5,self.report['whole_path_limits']['return_mOhm'])
        self.assertEqual(25,self.report['five_receiver_dynamics']['initial_all5_current_mA'])

if __name__=='__main__':unittest.main()
