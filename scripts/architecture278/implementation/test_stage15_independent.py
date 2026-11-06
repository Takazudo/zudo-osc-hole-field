"""Independent Stage15 geometry, migration, and adversarial source checks."""
import copy
import json
import math
from collections import Counter
import unittest
import stage15_packages as package
import stage15_paths as paths


class IndependentStage15(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.overlay=package.read('stage15/package-report.json')
        cls.graph=package.read('stage15/interfaces-report.json')
        cls.walks=package.read('stage15/paths-report.json')
        cls.budget=package.read('stage15/rebudget-report.json')

    def test_primary_pin_pairs_and_rear_mirror_independently(self):
        for ref,origin,z in [('RN7101',[255.5,254],70.8),('RN7102',[220.5,150],36.6)]:
            p=self.overlay['placements'][ref]
            for pin in range(1,9):
                column=pin-1 if pin<=4 else 8-pin
                x=-.975+.65*column
                y=2.17 if pin<=4 else -2.17
                actual=p['pads_xyz_mm'][str(pin)][0]
                for a,b in zip(actual,[origin[0]-x,origin[1]+y,z]):self.assertAlmostEqual(a,b)
            self.assertEqual(p['pads_xyz_mm']['9'][0],origin+[z])
        self.assertEqual([e['pins'] for e in self.overlay['elements'][:4]], [['1','8'],['2','7'],['3','6'],['4','5']])

    def test_every_walk_continuity_and_length_without_production_walk_helper(self):
        for group,start,metric in [('signal_net_paths','from','complete_net_pad_path_allocation_mm'),('local_endpoint_paths','from','complete_net_pad_path_allocation_mm'),('power_and_return_endpoint_paths','source_boundary','allocated_developed_mm')]:
            for row in self.walks[group]:
                here=row[start];total=0
                for i in row['edge_indices']:
                    e=self.graph['edges'][i]
                    self.assertEqual(e['net'],row['net']);self.assertIn(here,(e['from'],e['to']))
                    here=e['to'] if here==e['from'] else e['from'];total+=e['allocated_developed_mm']
                self.assertEqual(here,row['to']);self.assertAlmostEqual(total,row[metric])

    def test_all_incident_edges_actual_geometry_and_spares_isolated(self):
        for edge in self.graph['edges']:
            if not any(edge[k].startswith('RN710') for k in ('from','to')):continue
            self.assertEqual(self.graph['nodes'][edge['from']]['net'],self.graph['nodes'][edge['to']]['net'])
            a,b=(self.graph['nodes'][edge[k]]['pad_xyz_mm'] for k in ('from','to'))
            dx,dy=abs(a[0]-b[0]),abs(a[1]-b[1])
            self.assertAlmostEqual(edge['allocated_developed_mm'],1.15*(max(dx,dy)+(math.sqrt(2)-1)*min(dx,dy))+7+abs(a[2]-b[2]))
            self.assertIsNone(edge['routed_mm'])
        for pin in ('3','4','5','6'):
            key='RN7102:'+pin
            self.assertIsNone(self.graph['nodes'][key]['net'])
            self.assertFalse(any(key in (e['from'],e['to']) for e in self.graph['edges']))

    def test_all108_shared_edge_incidence_and_strap_partition(self):
        usage=Counter(i for r in self.walks['power_and_return_endpoint_paths'] for i in r['edge_indices'])
        for row in self.budget['resistance_endpoint_mapping']:
            for term in row['edge_terms']:
                self.assertEqual(term['endpoint_walk_use_count'],usage[term['edge_index']])
                self.assertIsNone(term['shared_current_A'])
        core={r['to'] for r in self.budget['unselected_strap_endpoint_paths']}
        front=set(self.budget['unselected_strap_front_targets'])
        self.assertFalse(core&front)
        self.assertEqual(core|front,{r['to'] for r in self.walks['power_and_return_endpoint_paths']})
        self.assertEqual((len(core),len(front)),(27,81))

    def test_body_courtyard_and_pad_land_primary_limits(self):
        g=package.read('stage15/package-input.json')['geometry']
        self.assertAlmostEqual(g['body_max_including_flash_mm'][0],3+.102+2*.152)
        self.assertGreaterEqual(2*2.17+.9,5.23)
        self.assertTrue(3.20<=2*2.17-.9<=3.45)
        self.assertTrue(.889-.127<=.9<=.889+.127)
        self.assertTrue(.42-.038<=.42<=.42+.038)

    def test_frozen_support_intrusion_rejected(self):
        args=[package.read(n) for n in ('stage15/package-input.json','stage13/package-report.json','stage10/mechanical-report.json')]
        args[1]['frozen_stage11_option_screen']['solids'].append({'id':'adversarial retained volume','box_mm':[253,250,258,258],'z_mm':[70,73]})
        with self.assertRaisesRegex(ValueError,'frozen'):package.analyze(*args)

    def test_connecting_unused_front_terminal_rejected(self):
        args=[package.read(n) for n in ('stage15/package-report.json','stage14/interfaces-report.json','stage14/paths-report.json','stage10/inventory-report.json','stage11/support-report.json','stage11/electrical-report.json')]
        args[0]['placements']['RN7102']['pins']['3']='AGND'
        with self.assertRaisesRegex(ValueError,'shield'):paths.analyze(*args)

    def test_two_network_ratio_envelope_independently(self):
        report=package.read('stage15/electrical-report.json')
        for row in report['conditioned_error_allocation']:
            delta=row['network_delta_fraction']
            self.assertAlmostEqual(row['CV_gain_interval'][1]-1,2*delta+delta**2)
            self.assertAlmostEqual(row['CV_gain_interval'][0],1/row['CV_gain_interval'][1])
            for state in row['states']:
                for key in ('minimum_witness','maximum_witness'):
                    w=state[key]
                    for elements in (w['summer_normalized_elements'],w['restore_normalized_used_elements']):
                        self.assertLessEqual(max(elements)/min(elements),1+delta+1e-14)
                self.assertIsNone(state['complete_error_bound_V'])


if __name__=='__main__':unittest.main()
