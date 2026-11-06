"""Read-only native copper plan identities and geometry; normal and -O coverage."""
import copy,hashlib,importlib.util,json,math,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/'design/architecture-278/implementation/stage40/mult-copper-plan'
s=importlib.util.spec_from_file_location('mult_copper_plan',HERE/'generate.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class MultCopperPlan(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.d=m.build()
    def test_determinism_and_source_bindings(self):
        self.assertEqual(self.d,json.loads((HERE/'plan.json').read_text()))
        self.assertEqual(m.svg(self.d),(HERE/'plan.svg').read_text())
        for p,h in self.d['source_sha256'].items():self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),h)
    def test_complete_native_occurrence_partition(self):
        d=self.d;n=d['native_board']['counts'];p=d['preservation']
        self.assertEqual((n['footprint'],n['segment'],n['via'],n['zone']),(1099,30564,2861,128))
        self.assertEqual(len(d['native_board']['duplicate_copper_uuids']),11)
        self.assertEqual(set(d['native_board']['duplicate_copper_uuids'].values()),{2})
        self.assertEqual(p['private_retirement_count']+p['remaining_copper_count'],33425)
        self.assertEqual(p['foreign_and_fixed_footprints_count'],1037)
        ids=[tuple(r[k] for k in ('index','kind','uuid','occurrence','sha256')) for r in d['private_net_retire_copper']]
        self.assertEqual(len(ids),len(set(ids)))
    def test_private_ownership_and_shared_boundary(self):
        d=self.d;owned=set(d['candidate_B1'])|{q['B2_ref'] for q in d['candidate_B1'].values()}
        private={r['native'] for r in d['net_mapping'] if r['class'].startswith('module-private')}
        for r in d['net_mapping']:
            if r['native'] in private:self.assertTrue(set(r['owners'])<=owned);self.assertNotIn(r['native'],('AGND','+12V','-12V','+5V'))
        self.assertEqual({r['net'] for r in d['private_net_retire_copper']},private)
        for r in d['shared_old_pad_contact_review']+d['preserved_new_pad_clearance_review']:self.assertNotIn(r['net'],private)
        self.assertTrue(d['shared_old_pad_contact_review']);self.assertTrue(d['preserved_new_pad_clearance_review'])
    def test_net_alias_split_merge_and_rail_identity(self):
        m.validate_aliases({'B1:AGND':'AGND','B2:AGND':'AGND','B1:FB':'X1','B2:FB':'X2'})
        for bad in ({'B1:FB':'X','B2:FB':'X'},{'B1:AGND':'X'},{'B1:FB':None},{'B1:A':'AGND','B2:AGND':'AGND'}):
            with self.assertRaises(ValueError):m.validate_aliases(bad)
    def test_fixed_and_repeated_cells(self):
        d=self.d;old=m.read('design/architecture-278/implementation/stage39/mult-substrate-comparison/comparison.json')['A']['packages_B1'];moves={r['ref']:r for r in d['moves']}
        self.assertEqual(len(moves),62);self.assertEqual(d['B2_translation_mm'],[34,0]);self.assertEqual(d['candidate_conflicts'],[]);self.assertTrue(d['stage39_native_conflicts'])
        for r,q in d['candidate_B1'].items():
            for k in ('pins','units','value','mpn','footprint','B2_ref'):self.assertEqual(q[k],old[r][k])
            if q['panel']:
                for k in ('origin','rotation','side'):self.assertEqual(q[k],old[r][k])
                self.assertNotIn(r,moves);continue
            self.assertTrue(m.g.inside(q['box'],[7.5,118.5,38.5,163.5]))
            a,b=moves[r]['proposed'],moves[q['B2_ref']]['proposed'];self.assertEqual(a['layer'],b['layer'])
            for pa,pb in zip(a['pads'],b['pads']):self.assertAlmostEqual(pb['xy'][0]-pa['xy'][0],34);self.assertEqual(pa['xy'][1],pb['xy'][1]);self.assertEqual(pa['pin'],pb['pin'])
    def test_bypass_cluster_and_locality(self):
        d=self.d
        for a,b in zip(d['metrics']['candidate']['bypass'],d['metrics']['current_native']['B1']['bypass']):
            self.assertEqual(a['capacitor'],b['capacitor']);self.assertAlmostEqual(a['rail_pad_distance_mm'],b['rail_pad_distance_mm'],places=5)
        self.assertLess(d['metrics']['candidate']['sum_feedback_mst_proxy_mm'],d['metrics']['stage39']['sum_feedback_mst_proxy_mm'])
    def test_zones_and_no_qualification_claim(self):
        d=self.d;self.assertFalse(d['adopted']);self.assertTrue(d['preservation']['no_native_file_written'])
        self.assertEqual(sum(z['is_keepout'] for z in d['zones']),123)
        filled=[z for z in d['zones'] if not z['is_keepout']];self.assertEqual(len(filled),5)
        self.assertTrue(all('refill' in z['action'] and z['filled_polygon_count']>0 for z in filled))
        for metrics in [d['metrics']['candidate'],d['metrics']['stage39'],*d['metrics']['current_native'].values()]:
            for r in metrics['bypass']:self.assertIsNone(r['return_path_length_mm'])
            for r in metrics['feedback']:self.assertIsNone(r['actual_route_length_mm']);self.assertGreaterEqual(r['three_pad_mst_proxy_mm'],r['max_pair_distance_mm'])
            self.assertIn('not a routing lower bound',metrics['scope'])
    def test_parser_rotation_quoted_text_and_duplicate_identity(self):
        fp='(footprint "lib (test)" (layer "B.Cu") (at 100 50 45) (property "Reference" "X1") (fp_rect (start -2 -1) (end 2 1) (layer "B.CrtYd")) (pad "1" smd rect (at 2 0 45) (size 2 1) (layers "B.Cu") (net "AGND")))'
        seg='(segment (start 100 50) (end 101 50) (width 0.2) (layer "F.Cu") (net "AGND") (uuid "duplicate"))'
        n=m.n.parse('(kicad_pcb '+fp+seg+seg+')');f=n['footprints']['X1']
        self.assertAlmostEqual(f['box'][0],-3/math.sqrt(2),places=5);self.assertAlmostEqual(f['box'][3],3/math.sqrt(2),places=5)
        self.assertAlmostEqual(f['pads'][0]['xy'][0],math.sqrt(2),places=5);self.assertAlmostEqual(f['pads'][0]['xy'][1],-math.sqrt(2),places=5)
        self.assertEqual([r['occurrence'] for r in n['copper']],[1,2]);self.assertNotEqual(m.manifest_hash(n['copper']),m.manifest_hash(n['copper'][:1]))
        for bad in ('(kicad_pcb (arc (uuid "x")))','(kicad_pcb '+fp.replace('smd rect','smd custom')+')'):
            with self.assertRaises(ValueError):m.n.parse(bad)
if __name__=='__main__':unittest.main()
