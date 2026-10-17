"""Electrical author's independent checks of separately authored package/path integration."""
import json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[3]
BASE=ROOT/'design/architecture-278/implementation'
def read(name): return json.loads((BASE/name).read_text())

class IndependentPackagePath(unittest.TestCase):
    def test_primary_pinpair_nets(self):
        old=read('stage13/package-report.json')['placements'];new=read('stage15/package-report.json')['placements']
        for network,refs in [('RN7101',['R7121','R7122','R7123','R7124']),('RN7102',['R7125','R7126'])]:
            for ref,pair in zip(refs,[('1','8'),('2','7'),('3','6'),('4','5')]):
                self.assertEqual([new[network]['pins'][k] for k in pair],[old[ref]['pins'][k] for k in ('1','2')])
            self.assertEqual(new[network]['pins']['9'],'AGND')
        self.assertTrue(all(new['RN7102']['pins'][k] is None for k in ('3','4','5','6')))

    def test_106_old_return_paths_preserved_plus_two_shields(self):
        old=read('stage14/paths-report.json')['power_and_return_endpoint_paths']
        new=read('stage15/paths-report.json')['power_and_return_endpoint_paths']
        indexed={r['to']:r for r in new}
        for r in old:self.assertEqual(indexed[r['to']],r)
        self.assertEqual(set(indexed)-{r['to'] for r in old},{'RN7101:9','RN7102:9'})

    def test_each_path_edge_continuous_same_net(self):
        graph=read('stage15/interfaces-report.json');paths=read('stage15/paths-report.json')
        for group in ('signal_net_paths','local_endpoint_paths','power_and_return_endpoint_paths'):
            for row in paths[group]:
                cursor=row.get('source_boundary',row.get('from'));total=0
                for i in row['edge_indices']:
                    e=graph['edges'][i];self.assertIn(cursor,(e['from'],e['to']));self.assertEqual(e['net'],row['net'])
                    cursor=e['to'] if cursor==e['from'] else e['from'];total+=e['allocated_developed_mm']
                self.assertEqual(cursor,row['to'])
                key='allocated_developed_mm' if group=='power_and_return_endpoint_paths' else 'complete_net_pad_path_allocation_mm'
                self.assertAlmostEqual(total,row[key])

    def test_no_actual_copper_or_unused_routes(self):
        graph=read('stage15/interfaces-report.json')
        for e in graph['edges']:
            self.assertIsNone(e['routed_mm'])
            for k in ('from','to'):self.assertNotIn(e[k],{'RN7102:3','RN7102:4','RN7102:5','RN7102:6'})

if __name__=='__main__': unittest.main()
