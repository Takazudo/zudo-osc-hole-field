"""Source-only boundaries, ownership and concrete geometry; runs under normal/-O."""
import hashlib, importlib.util, json, unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
HERE=ROOT/'design/architecture-278/implementation/stage39/mult-substrate-comparison'
s=importlib.util.spec_from_file_location('mult_substrate',HERE/'generate.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m)
class MultSubstrate(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.d=m.build();cls.old=json.loads((m.OLD/'layout.json').read_text())
    def test_determinism_and_source_bindings(self):
        self.assertEqual(self.d,json.loads((HERE/'comparison.json').read_text()))
        self.assertEqual(m.svg(self.d),(HERE/'comparison.svg').read_text())
        for p,h in self.d['source_sha256'].items():self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),h)
    def test_all_row_boundaries_preserve_first_rejection(self):
        self.assertEqual(self.d['stage38_failures'],self.old['boundary_failures'])
        self.assertEqual(len(self.d['seams']),36);self.assertEqual(sum(len(c['refs']) for c in self.d['columns']),40)
        for row in self.d['seams']:
            self.assertAlmostEqual(row['gap_mm'],.62);self.assertEqual(row['required_edges_mm'],1);self.assertAlmostEqual(row['overlap_mm'],.38)
        self.assertEqual(self.d['A']['outline'],[[4,20],[176.5,20],[176.5,164],[4,164]])
    def test_full_package_pin_identity_and_fixed_translation(self):
        a=self.d['A']['packages_B1'];self.assertEqual(set(a),set(self.old['packages_B1']))
        for r,q in a.items():
            before=self.old['packages_B1'][r]
            for key in ('pins','units','value','mpn','footprint','B2_ref'):self.assertEqual(q[key],before[key])
            self.assertEqual({p['pin']:p['net'] for p in q['pads']},q['pins'])
            if q['panel']:self.assertEqual(q['origin'],before['origin'])
        for k in self.d['fixed_markers']:
            q=a[k['ref']] if k['block']=='B1' else next(v for v in a.values() if v['B2_ref']==k['ref'])
            self.assertEqual([q['origin'][0]+(0 if k['block']=='B1' else 34),q['origin'][1]],[k['x_mm'],k['y_mm']])
    def test_A_actual_obstacle_screen_and_edge(self):
        a=self.d['A'];parts=[q for q in a['packages_B1'].values() if not q['panel']]
        blocked=[p['box'] for p in self.d['fixed_pth_reservations']]+[p['courtyard_mm'] for p in self.d['foreign_rear_placements']]+[p['box'] for p in a['source_keepouts']]+[p['tool_trial_xy'] for p in a['retained_mounts']]
        for dx in (0,34):
            for q in parts:
                self.assertFalse(any(m.g.ov(m.g.grow(m.g.shift(q['box'],dx),.25),b) for b in blocked),q['ref'])
            for q in a['packages_B1'].values():
                for p in q['pads']:self.assertTrue(m.g.inside(m.g.grow(m.g.shift(p['box'],dx),.5),[4,20,176.5,164]))
        for n,q in enumerate(parts):
            self.assertFalse(any(m.g.ov(m.g.grow(q['box'],.25),v['box']) for v in parts[n+1:]))
        self.assertEqual(a['foreign_package_hits'],[])
    def test_B_feedback_boundary_and_complete_packages(self):
        b=self.d['B'];pk=self.old['packages_B1'];front=set(b['front_refs']);rear=set(b['rear_refs'])
        self.assertEqual((len(front),len(rear)),(13,23));self.assertFalse(front&rear);self.assertEqual(front|rear,set(pk))
        self.assertIn('U3102',rear);self.assertIn('U3101',rear);self.assertIn('U3103',front)
        self.assertEqual(set(b['crossings']),{'IN_TIP','OUT_1_TIP','OUT_2_TIP','OUT_3_TIP','IN_BUFFER','+12V','-12V','AGND'})
        for n in b['crossings']:self.assertFalse(n.endswith('_FB') or n in ('IN_SENSE','IN_PROTECTED') or 'LED_' in n)
        for n in pk['D109']['pins'].values():self.assertIn(n,b['passive_crossings']);self.assertNotIn(n,b['crossings'])
        # Moving only the indicator IC rear would re-export its feedback node.
        mutated=m.crossings(pk,front-{'U3103'})
        self.assertIn(pk['U3103']['pins']['2'],mutated)
    def test_B_rear_packing_headers_and_opposing_faces(self):
        b=self.d['B'];parts=list(b['rear_packages_B1'].values())
        blockers=[s['tool_trial_xy'] for s in b['rear_supports_B1']]+[m.g.grow(p['pad_box'],.5) for c in (b['rear_signal'],b['rear_power']) for p in c['pins']]
        for n,q in enumerate(parts):
            self.assertFalse(any(m.g.ov(m.g.grow(q['box'],.25),v) for v in blockers))
            self.assertFalse(any(m.g.ov(m.g.grow(q['box'],.25),v['box']) for v in parts[n+1:]))
            for p in q['pads']:self.assertTrue(m.g.inside(m.g.grow(p['box'],.5),b['rear_outline_B1']))
        for c in (b['front_signal'],b['rear_signal'],b['rear_power']):
            for p in c['pins']:self.assertEqual(p['global_xy'],p['socket_global_xy'])
            self.assertIsNone(c['mated_max_height_mm']);self.assertIsNone(c['cable_cut_length_mm']);self.assertIsNone(c['bend_radius_mm'])
        self.assertEqual([p['net'] for p in b['front_signal']['pins']],[p['net'] for p in b['rear_signal']['pins']])
        self.assertAlmostEqual(b['front_signal']['body_max_xy'][2]-b['front_signal']['body_max_xy'][0],20.1422)
        for f,r in zip(b['front_signal']['pins'],b['rear_signal']['pins']):
            self.assertEqual(f['global_xy'][0]-23,-(r['global_xy'][0]-23))
    def test_B_failures_not_claimed_clearance(self):
        b=self.d['B'];self.assertEqual(b['front_grip_terminal_hits'],[])
        self.assertTrue(b['anchor_terminal_projections'])
        fail=[r for r in b['front_selector_reservations'] if r['status'].startswith('FAIL')]
        self.assertTrue(fail)
        self.assertTrue(all(r['ceiling_with_1mm_trial_clearance']<r['bare_header_nominal_mm'] for r in fail))
        self.assertEqual(b['additional_board_separation_mm'],30);self.assertIsNone(b['required_enclosure_depth_increase_mm'])
        self.assertTrue(all('UNKNOWN' in r['status'] for r in b['foreign_board_projections']))
    def test_counts_current_and_nonadoption(self):
        a,b=self.d['A'],self.d['B'];self.assertFalse(self.d['adopted']);self.assertTrue(self.d['recommendation'].startswith('A:'))
        self.assertEqual(a['interchangeable_mult_boards'],0);self.assertEqual(a['identical_cells'],2)
        self.assertEqual((b['assembly_board_count'],b['unique_designs'],b['identical_rear_boards']),(3,2,2))
        self.assertEqual(b['new_board_headers_total_including_distribution'],2*(b['analog_cables']+b['power_cables']))
        self.assertEqual(b['cable_sockets'],b['mating_actions']);self.assertEqual(b['new_rear_support_sites'],2*len(b['rear_supports_B1']))
        self.assertEqual(self.d['current_report'],self.old['current_report'])
if __name__=='__main__':unittest.main()
