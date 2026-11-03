"""Independent emitted-artifact review of Stage14 path rebinding."""
import json
import math
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[3]
DATA = ROOT / 'design/architecture-278/implementation'


def read(stage, name):
    return json.loads((DATA / stage / name).read_text())


class IndependentGraphReview(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old = read('stage10', 'interfaces-report.json')
        cls.new = read('stage14', 'interfaces-report.json')
        cls.paths = read('stage14', 'paths-report.json')
        cls.report = read('stage14', 'rebudget-report.json')

    def test_exact_changed_edge_inventory_and_independent_formula(self):
        changed = {i for i, (a, b) in enumerate(zip(self.old['edges'], self.new['edges'])) if a != b}
        self.assertEqual(changed, {238, 264, 265, 293, 294})
        for i in changed:
            e = self.new['edges'][i]
            a, b = (self.new['nodes'][e[k]]['pad_xyz_mm'] for k in ('from', 'to'))
            x, y = abs(a[0]-b[0]), abs(a[1]-b[1])
            expected = 1.15*(max(x,y)+(math.sqrt(2)-1)*min(x,y))+7+abs(a[2]-b[2])
            self.assertAlmostEqual(e['allocated_developed_mm'], expected)
            self.assertIsNone(e['routed_mm'])

    def test_every_path_delta_is_exact_sum_of_incident_deltas(self):
        baseline = read('stage10', 'electrical-report.json')
        groups = [('signal_net_paths', 'complete_net_pad_path_allocation_mm'),
                  ('local_endpoint_paths', 'complete_net_pad_path_allocation_mm'),
                  ('power_and_return_endpoint_paths', 'allocated_developed_mm')]
        for group, metric in groups:
            before = {(r['net'], r['to']): r for r in baseline[group]}
            after = {(r['net'], r['to']): r for r in self.paths[group]}
            self.assertEqual(set(before), set(after))
            changed = set()
            for key, row in after.items():
                old = before[key]
                self.assertEqual(row['edge_indices'], old['edge_indices'])
                delta = sum(self.new['edges'][i]['allocated_developed_mm']-self.old['edges'][i]['allocated_developed_mm'] for i in row['edge_indices'])
                self.assertAlmostEqual(row[metric]-old[metric], delta)
                if not math.isclose(delta, 0, abs_tol=1e-10):
                    changed.add(key)
            self.assertEqual(changed, {(r['net'], r['to']) for r in self.report['path_deltas'][group]})

    def test_strap_partition_is_exact_disjoint_endpoint_inventory(self):
        all_targets = {r['to'] for r in self.paths['power_and_return_endpoint_paths']}
        strap = {r['to'] for r in self.report['unselected_strap_endpoint_paths']}
        front = set(self.report['unselected_strap_unchanged_front_targets'])
        self.assertFalse(strap & front)
        self.assertEqual(strap | front, all_targets)
        self.assertEqual((len(strap), len(front), len(all_targets)), (26, 80, 106))

    def test_mapping_carries_actual_positions_and_all_edge_allocations(self):
        mapping = self.report['resistance_endpoint_mapping']
        paths = {r['to']: r for r in self.paths['power_and_return_endpoint_paths']}
        for row in mapping:
            self.assertEqual(row['source_pad_xyz_mm'], self.new['nodes'][row['to']]['pad_xyz_mm'])
            self.assertEqual([r['edge_index'] for r in row['edge_terms']], paths[row['to']]['edge_indices'])
            for term in row['edge_terms']:
                self.assertEqual(term['allocated_mm'], self.new['edges'][term['edge_index']]['allocated_developed_mm'])
                self.assertIsNone(term['resistance_ohm'])
                self.assertIsNone(term['shared_current_A'])


if __name__ == '__main__':
    unittest.main()
