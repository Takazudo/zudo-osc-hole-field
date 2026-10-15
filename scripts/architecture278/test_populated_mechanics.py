import copy, json, unittest
import populated_mechanics as m
class Populated(unittest.TestCase):
    def setUp(self): self.c=m.read('design/architecture-278/revision-mechanical-input.json')
    def test_all_packages_and_units_conserved(self):
        r=m.build(self.c);self.assertEqual(154,len(r['O1_placements'])); self.assertEqual(219,r['scope']['O1_physical_packages']);self.assertEqual(438,r['locked_panel_count']);self.assertEqual([],r['conflicts']);self.assertEqual(12,len(r['trim_access']))
        source=m.read('design/architecture-278/interface-contract.json');refs={p['ref'] for p in source['parts'] if p['instance']=='O1' and p['proposed_owner']=='rear-core' and p['footprint']};self.assertEqual(refs,{p['ref'] for p in r['O1_placements']})
    def test_capacity_failure(self):
        self.c['placement_region_mm']=[8,35,20,40]
        with self.assertRaises(ValueError):m.build(self.c)
    def test_neighbor_collision(self):
        self.c['origins_mm']['O2']=self.c['origins_mm']['O1'];self.assertTrue(any('neighbor' in s for s in m.build(self.c)['conflicts']))
    def test_tool_clearance_failure(self):
        self.c['tool_diameter_mm']=40;self.assertTrue(any('trim tool' in s for s in m.build(self.c)['conflicts']))
    def test_cover_collision(self):
        self.c['cover_depth_mm']=75;self.assertIn('cover/handle collision',m.build(self.c)['conflicts'])
    def test_source_stack_range(self):
        self.c['core_depth_mm']=80;self.assertTrue(any('DIN source stack' in s for s in m.build(self.c)['conflicts']))
    def test_workspace(self):
        self.c['external_workspace_mm']=10;self.assertIn('withdrawal workspace insufficient',m.build(self.c)['conflicts'])
    def test_no_nan(self):
        self.c['cover_depth_mm']=float('nan')
        with self.assertRaises(ValueError):m.build(self.c)
    def test_drawing_tracks_card_geometry(self):
        before=m.drawing(m.build(self.c));self.c['origins_mm']['O2'][0]+=1;self.assertNotEqual(before,m.drawing(m.build(self.c)))
    def test_nested_nan(self):
        self.c["origins_mm"]["O1"][0]=float("nan")
        with self.assertRaises(ValueError):m.build(self.c)
    def test_panel_locked(self):
        self.c["panel_mm"][0]=400
        with self.assertRaises(ValueError):m.build(self.c)
    def test_missing_mechanical_elements(self):
        for key in ['support_centres_mm','guide_centres_mm','probe_centres_mm','pull_handle_centres_mm']:
            c=copy.deepcopy(self.c);c[key]=[]
            with self.subTest(key=key),self.assertRaises(ValueError):m.build(c)
    def test_missing_card(self):
        del self.c['origins_mm']['O5']
        with self.assertRaises(ValueError):m.build(self.c)
    def test_height_collision(self):
        self.c['rear_component_height_bound_mm']=100
        self.assertIn('cover/component collision',m.build(self.c)['conflicts'])
    def test_zero_required_dimensions(self):
        for key in ['tool_diameter_mm','withdrawal_mm']:
            c=copy.deepcopy(self.c);c[key]=0
            with self.subTest(key=key),self.assertRaises(ValueError):m.build(c)
    def test_zero_sweep(self):
        self.c['trim_adjustment_degrees']=[0,0]
        with self.assertRaises(ValueError):m.build(self.c)
    def test_symmetric_guides_rejected(self):
        self.c['guide_centres_mm'][1][1]=30
        with self.assertRaises(ValueError):m.build(self.c)
    def test_power_driver_conflict(self):
        self.c['power_driver_diameter_mm']=40
        self.assertTrue(any('axial tool obstructed power' in v for v in m.build(self.c)['conflicts']))
    def test_handle_neighbor_conflict(self):
        self.c['handle_projection_mm']=8
        self.assertTrue(any('handle finger neighbor' in v for v in m.build(self.c)['conflicts']))
    def test_full_O2_mapping(self):
        r=m.build(self.c);self.assertEqual(154,len(r['O2_placements']))
        self.assertEqual({p['ref'] for p in r['O1_placements']},{p['source_O1_ref'] for p in r['O2_placements']})
        self.assertTrue(all(p['units']==[u['unit'] for u in p['unit_mapping']] for p in r['O2_placements']))
    def test_reference_cluster_complete(self):
        r=m.build(self.c);placed={p['ref']:p for p in r['O1_placements']}
        self.assertEqual([1,2,3,4,5],placed['U1110']['units'])
        self.assertEqual(15,len(self.c['reference_cluster_centres_mm']))
        for ref,xy in self.c['reference_cluster_centres_mm'].items():self.assertEqual(xy,placed[ref]['origin_mm'])
        del self.c['reference_cluster_centres_mm']['C1136']
        with self.assertRaises(ValueError):m.build(self.c)
    def test_probe_nets_exist(self):
        nets={x['net'] for x in m.read('design/architecture-278/interface-contract.json')['nets']};self.assertTrue(all(x['net'] in nets for x in m.build(self.c)['fixtures'] if x['kind']=='probe'))
    def test_inverted_and_zero_rectangles(self):
        for key,box in [('power_boxes_mm',[20,72,10,92]),('connector_box_mm',[1,11,1,26]),('placement_region_mm',[97,35,8,85])]:
            c=copy.deepcopy(self.c)
            if key=='power_boxes_mm':c[key][0]=box
            else:c[key]=box
            with self.subTest(key=key),self.assertRaises(ValueError):m.build(c)
    def test_coordinate_shapes(self):
        c=copy.deepcopy(self.c);c['origins_mm']['O1']=[2]
        with self.assertRaises(ValueError):m.build(c)
        c=copy.deepcopy(self.c);c['tile_mm']=[103,0]
        with self.assertRaises(ValueError):m.build(c)
if __name__=='__main__':unittest.main()
