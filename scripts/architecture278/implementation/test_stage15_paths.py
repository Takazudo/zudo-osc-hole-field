import unittest
import stage15_paths as m

class Paths(unittest.TestCase):
    def setUp(self):
        self.args=[m.read(n) for n in ('stage15/package-report.json','stage14/interfaces-report.json','stage14/paths-report.json','stage10/inventory-report.json','stage11/support-report.json','stage11/electrical-report.json')]
    def test_all_paths_and_returns(self):
        g,p,r=m.analyze(*self.args)
        self.assertEqual(r['counts']['power_return_endpoints'],108)
        self.assertEqual(r['counts']['strap_core_endpoints'],27)
        self.assertEqual(r['counts']['strap_front_endpoints'],81)
        self.assertEqual(r['counts']['nodes'],561)
        self.assertEqual(r['counts']['edges'],320)
        for row in p['local_endpoint_paths']:
            self.assertEqual(row['edge_indices'],m.interface.path_edges(g,row['from'],row['to']))
    def test_old_nodes_removed_no_phantom_connections(self):
        g,p,r=m.analyze(*self.args)
        for old,new in r['endpoint_aliases'].items():
            self.assertNotIn(old,g['nodes']);self.assertIn(new,g['nodes'])
        for pin in ('3','4','5','6'):
            key='RN7102:'+pin
            self.assertIn(key,g['NC_source_endpoints'])
            self.assertFalse(any(key in (e['from'],e['to']) for e in g['edges']))
    def test_all_old_return_requirements_retained(self):
        g,p,r=m.analyze(*self.args)
        old=m.read('stage14/rebudget-report.json')['resistance_endpoint_mapping']
        clean=lambda rows: [{k:v for k,v in x.items() if k!='edge_terms'} for x in rows]
        self.assertEqual(clean(old),clean([x for x in r['resistance_endpoint_mapping'] if not x['to'].startswith('RN')]))
    def test_wrong_net_fails(self):
        self.args[0]['placements']['RN7101']['pins']['1']='AGND'
        with self.assertRaises(ValueError):m.analyze(*self.args)
    def test_missing_mapping_fails(self):
        self.args[0]['endpoint_aliases'].pop('R7124:2')
        with self.assertRaises(ValueError):m.analyze(*self.args)
    def test_stale_old_power_path_fails(self):
        self.args[2]['power_and_return_endpoint_paths'][0]['allocated_developed_mm']+=1
        with self.assertRaises(ValueError):m.analyze(*self.args)
    def test_report_no_acceptance(self):
        for obj in m.analyze(*self.args):
            self.assertFalse(obj['hardware_acceptance']);self.assertEqual(obj['simulation'],'NOT RUN')
if __name__=='__main__':unittest.main()
