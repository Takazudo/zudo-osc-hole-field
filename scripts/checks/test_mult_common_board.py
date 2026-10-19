"""Source-only MULT capacity/identity/rejection checks, meaningful under -O."""
import hashlib,importlib.util,json
from pathlib import Path
import unittest
ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/'design/architecture-278/implementation/stage38/mult-common-board'
spec=importlib.util.spec_from_file_location('mult_common',HERE/'generate.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
class MultCommon(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.p=m.build()
    def test_deterministic_artifacts(self):
        self.assertEqual(self.p,json.loads((HERE/'layout.json').read_text()))
        self.assertEqual(m.svg(self.p),(HERE/'layout.svg').read_text())
        self.assertEqual(m.bom_csv(self.p),(HERE/'assembly-target.csv').read_text())
        for f,h in self.p['source_sha256'].items():self.assertEqual(hashlib.sha256((ROOT/f).read_bytes()).hexdigest(),h)
    def test_full_packages_pins_and_unknown_mpn(self):
        p=self.p['packages_B1'];self.assertEqual(len(p),36)
        self.assertEqual([r for r,q in p.items() if not q['mpn']],['R3102','R3104','R3114'])
        self.assertEqual([u['unit'] for u in p['U3102']['units']],[1,2,3,4,5])
        self.assertEqual(len(p['U3102']['pins']),14)
        self.assertEqual(len([q for q in p.values() if q['mpn']=='RC1210FR-07499RL']),6)
        for q in p.values():
            self.assertEqual(q['pins'],{p['pin']:p['net'] for p in q['pads']})
            self.assertEqual(len(q['pins']),sum(len(u['pins']) for u in q['units']))
    def test_exact_translation_all_pads_and_panel_markers(self):
        for r,a in self.p['packages_B1'].items():
            b=self.p['translation_B2'][r]
            self.assertEqual(b['box'],m.shift(a['box'],34))
            for p,q in zip(a['pads'],b['pads']):
                self.assertEqual(p['net'],q['net']);self.assertAlmostEqual(q['xy'][0]-p['xy'][0],34);self.assertEqual(p['xy'][1],q['xy'][1])
        marks=self.p['fixed_markers'];self.assertEqual(len(marks),10)
        for p in marks:
            if p['block']=='B1':q=self.p['packages_B1'][p['ref']]
            else:q=next(v for v in self.p['translation_B2'].values() if v['ref']==p['ref'])
            self.assertEqual(q['origin'],[p['x_mm'],p['y_mm']])
        self.assertEqual(self.p['outline_B2'],m.shift(self.p['outline_B1'],34))
    def test_mirror_known_pin_coordinates_and_clearance(self):
        p='footprints/kicad/zudo-osc-hole-field.pretty/TSSOP-14_4.4x5mm_P0.65mm.kicad_mod'
        _,f=m.shape(p,[0,0]);_,b=m.shape(p,[0,0],True)
        for a,z in zip(f,b):self.assertEqual(a['pin'],z['pin']);self.assertEqual(a['xy'],[-z['xy'][0],z['xy'][1]])
        for key,value in self.p['source_screens'].items():self.assertFalse(value,key)
    def test_boundary_rejection_not_unknown_reservation(self):
        rows=self.p['boundary_failures'];self.assertEqual(len(rows),4)
        self.assertEqual({r['foreign_tip'] for r in rows},{'J108','J208','J308','J408'})
        for r in rows:
            self.assertAlmostEqual(r['copper_gap_mm'],.62)
            self.assertEqual(r['each_edge_requirement_mm'],.5)
            self.assertAlmostEqual(r['minimum_board_overlap_mm'],.38)
            self.assertGreater(r['foreign_board_min_end_y'],r['candidate_max_start_y'])
        self.assertFalse(self.p['adopted']);self.assertTrue(self.p['verdict'].startswith('REJECT'))
        # Even a curved/notched separation cannot remove overlapping clearance sets on their common centerline.
        self.assertGreater(2*.5,.62)
    def test_connector_maps_and_first_failure_preserved(self):
        c=self.p['connector'];self.assertEqual([p['net'] for p in c['pins']],['+12V','AGND','-12V','AGND','+5V','AGND',None,None])
        for p in c['pins']:
            self.assertEqual(p['header_face_xy'][0],p['socket_face_xy'][0]);self.assertEqual(p['header_face_xy'][1],-p['socket_face_xy'][1])
            self.assertTrue(m.inside(m.grow(p['pad_box'],.5),self.p['outline_B1']))
            self.assertEqual(p['global_xy'],[c['center'][0]-p['header_face_xy'][0],c['center'][1]+p['header_face_xy'][1]])
            self.assertEqual(p['global_xy'],[c['center'][0]-p['socket_face_xy'][0],c['center'][1]-p['socket_face_xy'][1]])
        old=m.shift(c['grip_trial_xy'],0,-1)
        terminal=next(t for t in self.p['tail_keepouts'] if t['id']=='J210:T')
        self.assertTrue(m.ov(old,terminal['box']));self.assertFalse(m.ov(c['grip_trial_xy'],terminal['box']))
        lo,hi=self.p['header_y_necessary_interval_mm'];self.assertLess(lo,c['center'][1]);self.assertLess(c['center'][1],hi)
        self.assertFalse(lo<168<hi)
        self.assertIsNone(c['mated_max_height']);self.assertIsNone(c['cut_length'])
    def test_power_and_scope_counts(self):
        current=json.loads((ROOT/'design/reports/current/mult.json').read_text())
        self.assertEqual(self.p['current_report'],current)
        self.assertEqual(self.p['return_planning_sum_mA'],21.575);self.assertIsNone(self.p['return_guaranteed_mA'])
        n=self.p['counts'];self.assertEqual(n['populated_candidate_packages_each_including_header'],len(self.p['packages_B1'])+1)
        self.assertEqual(n['two_mult_main_boards'],2);self.assertEqual(n['main_unique_designs'],1)
        self.assertEqual(n['header_ends_including_distribution'],2*n['power_cables'])
        self.assertNotIn('whole_instrument_total',n)
        self.assertEqual(len(self.p['bypass_diagnostics']),6)
    def test_foreign_occupancy_not_free(self):
        self.assertEqual(len(self.p['foreign_fixed_projections']),7)
        self.assertEqual(len(self.p['selector_projection_hits']),8)
        self.assertTrue(all('UNKNOWN' in q['z'] for q in self.p['foreign_fixed_projections']))
        self.assertIn('all foreign installed heights/tails and incumbent board coexistence',self.p['unknowns'])
if __name__=='__main__':unittest.main()
