import copy
import math
import unittest
import stage14_paths as s

class Paths(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        names=['stage13/package-report.json','stage10/interfaces-report.json','stage10/electrical-report.json',
               'stage10/mechanical-report.json','stage10/inventory-report.json','stage10/interface-input.json',
               'stage11/support-report.json','stage11/electrical-report.json']
        cls.inputs=[s.read(n) for n in names]
        cls.graph,cls.paths,cls.report=s.analyze(*cls.inputs)

    def test_exact_nodes_edges(self):
        self.assertEqual(self.report['counts']['power_return_endpoints'],106)
        self.assertEqual({r['edge_index'] for r in self.report['incident_edge_deltas']},{238,264,265,293,294})
        self.assertEqual(len(self.report['changed_pad_nodes']),4)

    def test_all_walks_independently_sum(self):
        for name,startkey,metric in [('signal_net_paths','from','complete_net_pad_path_allocation_mm'),
                                    ('local_endpoint_paths','from','complete_net_pad_path_allocation_mm'),
                                    ('power_and_return_endpoint_paths','source_boundary','allocated_developed_mm')]:
            for row in self.paths[name]:
                here=row[startkey];total=0
                for i in row['edge_indices']:
                    edge=self.graph['edges'][i]
                    self.assertEqual(edge['net'],row['net']);self.assertIn(here,(edge['from'],edge['to']))
                    here=edge['to'] if here==edge['from'] else edge['from']
                    total+=edge['allocated_developed_mm']
                self.assertEqual(here,row['to']);self.assertAlmostEqual(total,row[metric])

    def test_all_edges_use_actual_geometry(self):
        for edge in self.graph['edges']:
            if edge['kind'] in ('GH_harness','DIN_mated_pair','permanent_terminal_wire','LED_local_copper'):continue
            a=self.graph['nodes'][edge['from']]['pad_xyz_mm'];b=self.graph['nodes'][edge['to']]['pad_xyz_mm']
            dx,dy=sorted([abs(a[0]-b[0]),abs(a[1]-b[1])])
            self.assertAlmostEqual(edge['allocated_developed_mm'],1.15*(dy-dx+math.sqrt(2)*dx)+7+abs(a[2]-b[2]))
            self.assertIsNone(edge['routed_mm'])

    def test_signal_crossings_unchanged_but_raw_local_changed(self):
        self.assertEqual(self.report['path_deltas']['signal_net_paths'],[])
        local=self.report['path_deltas']['local_endpoint_paths']
        self.assertIn('U7104:3',{r['to'] for r in local})
        self.assertIn('U7101:6',{r['to'] for r in local})

    def test_domains_preserved(self):
        old={r['to']:r for r in s.read('stage12/budget-report.json')['resistance_endpoint_mapping']}
        for row in self.report['resistance_endpoint_mapping']:
            self.assertEqual(row['original_plane_requirement'],old[row['to']]['original_plane_requirement'])
            self.assertEqual(row['expanded_architecture_comparison'],old[row['to']]['expanded_architecture_comparison'])
            self.assertIsNone(row['complete_transfer_error_V'])

    def test_strap_suffix_rebound(self):
        self.assertEqual(len(self.report['unselected_strap_endpoint_paths']),26)
        self.assertEqual(len(self.report['unselected_strap_unchanged_front_targets']),80)
        for row in self.report['unselected_strap_endpoint_paths']:
            expected=sum(e['allocation_mm'] for e in row['new_segments'])+sum(self.graph['edges'][i]['allocated_developed_mm'] for i in row['retained_suffix_edge_indices'])
            self.assertAlmostEqual(expected,row['complete_boundary_to_pad_allocation_mm'])
            self.assertIsNone(row['complete_source_to_pad_resistance_ohm'])

    def test_full_endpoint_set(self):
        inv=self.inputs[4]
        expected={(f'{ref}:{pin}',net) for ref,p in inv['packages'].items() for pin,net in p['pins'].items() if net in ('AGND','+12V','-12V','+5V')}
        self.assertEqual({(r['to'],r['net']) for r in self.report['resistance_endpoint_mapping']},expected)

    def test_wrong_pad_net_rejected(self):
        args=copy.deepcopy(self.inputs);args[0]['placements']['C7101']['pins']['1']='AGND'
        with self.assertRaises(ValueError):s.analyze(*args)

    def test_missing_invalidation_rejected(self):
        args=copy.deepcopy(self.inputs);args[0]['endpoint_delta_and_invalidation']['changed_source_pads'][0]['invalidated_incident_graph_edges']=[]
        with self.assertRaises(ValueError):s.analyze(*args)

    def test_unrelated_move_rejected(self):
        args=copy.deepcopy(self.inputs);args[0]['placements']['C7107']['pads_xyz_mm']['1'][0][0]+=1
        with self.assertRaises(ValueError):s.analyze(*args)

    def test_missing_endpoint_rejected(self):
        args=copy.deepcopy(self.inputs);args[2]['power_and_return_endpoint_paths'].pop()
        with self.assertRaises(ValueError):s.analyze(*args)

    def test_changed_baseline_topology_rejected(self):
        args=copy.deepcopy(self.inputs);args[1]['edges'][238]['to']='C7107:1'
        with self.assertRaises(ValueError):s.analyze(*args)

if __name__=='__main__':unittest.main()
