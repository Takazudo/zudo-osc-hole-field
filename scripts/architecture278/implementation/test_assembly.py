"""Source invariants and negative tests; never assert routed or physical success."""
import copy
import json
import unittest
from collections import Counter
import assembly as a

class AssemblyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report=json.loads((a.OUT/'assembly-report.json').read_text())
        cls.contract=a.c.read('interface-contract.json')
        cls.config=a.c.read('implementation/assembly.json')
    def test_every_endpoint_and_nc(self):
        a.validate_inventory(self.report['endpoint_inventory'],self.contract)
        self.assertEqual(806,len(self.report['endpoint_inventory']))
        self.assertEqual(38,sum(e['net'] is None for e in self.report['endpoint_inventory']))
        self.assertEqual(171,len(self.report['local_net_nodes']))
        self.assertEqual(249,self.report['placed_physical_package_count'])
    def remove_endpoint(self,predicate):
        rows=copy.deepcopy(self.report['endpoint_inventory']);rows.remove(next(e for e in rows if predicate(e)))
        with self.assertRaises(ValueError):a.validate_inventory(rows,self.contract)
    def test_missing_local_feedback_endpoint(self):self.remove_endpoint(lambda e:e['ref']=='R1122')
    def test_missing_shared_receiver(self):self.remove_endpoint(lambda e:e['net']=='OSC_REF5' and e['owner']=='rear-core')
    def test_missing_return_endpoint(self):self.remove_endpoint(lambda e:e['net']=='AGND')
    def test_missing_nc(self):self.remove_endpoint(lambda e:e['net'] is None)
    def test_missing_source_package(self):
        ps=a.c.packages(self.contract)
        with self.assertRaises(ValueError):a.endpoint_inventory(ps,{})
    def test_gh_exact_manufacturer_geometry(self):
        for n in (2,4):
            h=a.header({'id':'test','pins':{str(i):'n'+str(i) for i in range(1,n+1)}})
            self.assertEqual(n+2,len(h['pads']))
            self.assertAlmostEqual((n-1)*1.25/2,h['pads']['1'][0][0])
            self.assertEqual([1.85+(n-1)*1.25/2,3.35],h['pads']['MP2'][0])
    def test_mirrored_pad_and_inverse(self):
        s=a.header({'id':'test','pins':{'1':'x','2':'AGND'}})
        t=a.face_shape(s,'rear')
        self.assertEqual(-s['pads']['1'][0][0],t['pads']['1'][0][0])
        self.assertEqual(s,a.face_shape(t,'rear'))
    def test_locked_selector_rotation_all_five(self):
        lock=json.loads((a.ROOT/'design/grid/placements.lock.json').read_text())['placements']
        for instance,pp in self.report['front_instances'].items():
            p=next(p for p in pp if p['ref']=='SW101');datum=next(d for d in lock if d['uid']==f'C:{instance}.OCT')
            self.assertEqual([datum['x_mm'],datum['y_mm']],p['origin_mm'])
            self.assertEqual(datum['rot_deg'],90*p['quarter_turn'])
    def test_wire_has_tolerance_and_service_slack(self):
        self.assertEqual(270,len(self.report['wire_checks']))
        self.assertTrue(all(w['minimum_remaining_slack_mm']>=10 for w in self.report['wire_checks']))
        self.assertGreater(len({w['front_depth_mm'] for w in self.report['wire_checks']}),1)
    def test_paths_include_shared_nets_and_arithmetic(self):
        for alt in self.report['alternatives'].values():
            self.assertTrue(set(self.report['shared_driver_endpoints']).issubset({p['net'] for p in alt['paths']}))
            for p in alt['paths']:
                self.assertAlmostEqual(sum(p['segments'].values()),p['total_mm'])
                self.assertAlmostEqual(300-p['total_mm'],p['margin_mm'])
                self.assertIsNone(p['capacitance_pF'])
            self.assertEqual(26,len(set(alt['DIN_signal_labels'].values())))
            self.assertTrue(alt['overlength_endpoint_paths']>0)
    def test_duplicate_reference_branch_coverage(self):
        for alt in self.report['alternatives'].values():
            expected={(i,h['id'],p,n) for i in alt['origins_mm'] for h in a.c.read('implementation/candidate-report.json')['front_links'] for p,n in h['pins'].items() if n!='AGND'}
            self.assertEqual(expected,{(r['instance'],r['link'],r['link_pin'],r['net']) for r in alt['paths'] if 'link' in r})
    def test_return_and_supply_unknowns_stay_open(self):
        for s in self.report['supply_graph'].values():
            self.assertIsNone(s['common_distribution_resistance_mOhm'])
            self.assertIsNone(s['parallel_return_solution'])
        for alt in self.report['alternatives'].values():
            self.assertTrue(alt['returns'])
            self.assertTrue(all(r['resistance_mOhm'] is None for r in alt['returns']))
    def test_supply_graph_uses_compact_endpoint_inventory(self):
        inventory={(e['ref']+':'+e['pin'],e['net']):e['xy_mm'][0] for e in self.report['endpoint_inventory'] if e['physical']}
        for net,graph in self.report['supply_graph'].items():
            for e in graph['physical_endpoints']:self.assertEqual(inventory[e['ref'],net],e['xy_mm'])
    def test_every_path_has_geometric_floor(self):
        for alt in self.report['alternatives'].values():
            for p in alt['paths']:self.assertAlmostEqual(a.math.dist(p['front_pad_mm'],p['other_pad_mm']),p['pad_separation_lower_bound_mm'])
    def test_no_relaxation_of_reservations(self):
        for key in ('route_factor','route_extra_mm','endpoint_tolerance_mm','wire_nominal_mm','wire_cut_tolerance_mm','minimum_service_slack_mm','GH_pair_developed_mm','DIN_developed_mm'):
            s=copy.deepcopy(self.config);s[key]=0
            with self.assertRaises(ValueError):a.build(s)
    def test_nonfinite_input_rejected(self):
        s=copy.deepcopy(self.config);s['route_factor']=float('nan')
        with self.assertRaises(ValueError):a.build(s)
    def test_bypass_association_conservation(self):
        expected=Counter(u['ref'] for u in self.contract['parts'] if u['attributes'].get('Decouples'))+Counter(a.SHARED_BYPASS.keys())
        self.assertEqual(expected,Counter(p['capacitor'] for p in self.report['bypass_associations']))

if __name__=='__main__':unittest.main()
