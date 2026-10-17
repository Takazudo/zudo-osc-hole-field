"""Geometry identities, process exclusions and budget feasibility regressions."""
import copy
import math
import unittest
import stage24_patterns as s


class Patterns(unittest.TestCase):
    def setUp(self):
        self.d=s.read(s.OUT/'definitions.json')
        self.e=s.read(s.ROOT/s.REL/'stage22/evidence.json')
        self.inventory=s.read(s.ROOT/s.REL/'stage21/inventory-input.json')

    def din(self,sex='female'):
        ref='J17909' if sex=='female' else 'J17910'
        return s.din_pattern(self.e['DIN'][sex],self.inventory['unbound'][ref]['pins'],self.d['din'])

    def test_stencil_selection_promotion_rejected(self):
        self.d['process']['stencil_selected']=True
        with self.assertRaisesRegex(ValueError,'selection'):s.validate_process(self.d['process'])

    def test_foil_invalid_and_unreviewed_values(self):
        for values in ([-.1],[float('nan')],[0],[.2]):
            self.d['process']['stencil_thickness_sensitivity_mm']=values
            with self.assertRaises(ValueError):s.validate_process(self.d['process'])

    def test_process_threshold_weakening(self):
        self.d['process']['min_mask_to_neighbor_trace_mm']=0
        with self.assertRaisesRegex(ValueError,'threshold'):s.validate_process(self.d['process'])

    def test_source_url_substitution_and_omission(self):
        sources=s.read(s.OUT/'sources.json');sources['jlc-stencil']['url']=sources['jlc-mask']['url']
        with self.assertRaisesRegex(ValueError,'identity'):s.validate_sources(sources)
        del sources['jlc-mask']
        with self.assertRaisesRegex(ValueError,'complete'):s.validate_sources(sources)

    def test_resistor_gap_and_symmetric_masks(self):
        p=s.smd_pattern(self.d['smd']['R0603'],self.d['process'])
        self.assertAlmostEqual(p['copper_gap_mm'],.8)
        self.assertAlmostEqual(p['mask_gap_mm'],.7)
        self.assertEqual(p['pads']['1']['center_mm'],[-.85,0])
        self.assertEqual(p['pads']['2']['copper_size_mm'],[.9,.8])

    def test_capacitor_manufacturer_B_dimensions(self):
        p=s.smd_pattern(self.d['smd']['C0603'],self.d['process'])
        self.assertAlmostEqual(p['copper_gap_mm'],.65)
        self.assertAlmostEqual(p['mask_gap_mm'],.55)
        self.assertEqual(p['courtyard_mm'],[3.1,1.5])

    def test_paste_ratio_calculation(self):
        p=s.smd_pattern(self.d['smd']['R0603'],self.d['process'])
        self.assertAlmostEqual(p['stencil_sensitivities'][0]['rectangle_area_ratio'],.72/.34)
        self.assertAlmostEqual(p['stencil_sensitivities'][0]['nominal_deposit_volume_per_pad_mm3'],.072)
        self.assertFalse(p['paste_qualified'])

    def test_red_glue_not_paste(self):
        self.d['process']['paste_scale_xy']=.28
        with self.assertRaisesRegex(ValueError,'mask/paste'):s.smd_pattern(self.d['smd']['R0603'],self.d['process'])

    def test_negative_or_nan_dimensions(self):
        for n in (-1,float('nan')):
            self.d['smd']['R0603']['pad_width_mm']=n
            with self.assertRaises(ValueError):s.smd_pattern(self.d['smd']['R0603'],self.d['process'])

    def test_courtyard_cannot_cut_copper(self):
        self.d['smd']['R0603']['courtyard_mm']=[1,1]
        with self.assertRaisesRegex(ValueError,'courtyard'):s.smd_pattern(self.d['smd']['R0603'],self.d['process'])

    def test_overlapping_pads_rejected(self):
        self.d['smd']['R0603']['center_abs_x_mm']=.4
        with self.assertRaisesRegex(ValueError,'clearance'):s.smd_pattern(self.d['smd']['R0603'],self.d['process'])

    def test_din_all_contacts_and_view_rows(self):
        f,m=self.din(),self.din('male')
        self.assertEqual(len(f['pads'])+len(m['pads']),192)
        self.assertEqual(f['pads']['a1']['center_mm'],[39.37,-2.54])
        self.assertEqual(m['pads']['a1']['center_mm'],[39.37,2.54])
        self.assertEqual(f['pads']['c32']['center_mm'],[-39.37,2.54])
        self.assertEqual(m['pads']['c32']['center_mm'],[-39.37,-2.54])

    def test_coordinate_transform_is_involution(self):
        p=[39.37,-2.54];matrix=self.d['din']['component_view_xy_down_matrix']
        self.assertEqual(s.transform(s.transform(p,matrix),matrix),p)

    def test_unjustified_male_mirror_rejected(self):
        self.d['din']['component_view_xy_down_matrix']=[[-1,0],[0,-1]]
        with self.assertRaisesRegex(ValueError,'preserve x'):self.din('male')

    def test_nc_contact_is_not_omitted(self):
        pins=self.inventory['unbound']['J17909']['pins'];key=next(k for k,v in pins.items() if v is None)
        del pins[key]
        with self.assertRaisesRegex(ValueError,'96-contact'):self.din()

    def test_fixing_not_electrical_male_flange_not_board(self):
        f,m=self.din(),self.din('male')
        self.assertEqual(len(f['fixing_holes']),2)
        self.assertEqual(f['fixing_holes'][0]['center_mm'],[-45,-.3])
        self.assertEqual(m['fixing_holes'],[])
        self.assertFalse(f['fixing_holes'][0]['copper'])

    def test_no_din_paste_or_invented_drill(self):
        for k,v in [('paste',True),('manufacturing_drill_diameter_mm',1.1)]:
            original=self.d['din'][k];self.d['din'][k]=v
            with self.assertRaises(ValueError):self.din()
            self.d['din'][k]=original

    def test_no_unapproved_installation(self):
        self.d['din']['board_thickness_mm']=1.6
        with self.assertRaisesRegex(ValueError,'installation'):self.din()

    def test_hole_interval_no_nominal_solution(self):
        r=s.hole_screen(1,.13,.08,.9,1.1)
        self.assertFalse(r['any_nominal_can_guarantee'])
        self.assertAlmostEqual(r['allowed_nominal_interval_mm'][0],.98)
        self.assertAlmostEqual(r['allowed_nominal_interval_mm'][1],.97)

    def test_special_tolerance_is_only_conditional_example(self):
        self.assertTrue(s.hole_screen(1,.05,.05,.9,1.1)['nominal_passes'])
        self.assertFalse(self.din()['position_default_guarantees_drawing'])

    def test_annulus_not_hole_qualification(self):
        r=self.din();self.assertGreater(r['conservative_annular_ring_mm'],.254)
        self.assertIn('BLOCKED',r['fabrication_status'])
        self.assertFalse(r['hole_screen']['nominal_passes'])


class Budget(unittest.TestCase):
    def setUp(self):
        self.d=s.read(s.OUT/'definitions.json')['electrical']
        self.p=s.read(s.ROOT/s.REL/'stage15/electrical-input.json')
        self.r=s.read(s.ROOT/s.REL/'stage15/electrical-report.json')

    def result(self):return s.electrical(self.d,self.p,self.r)

    def test_negative_allocation_is_explicit(self):
        r=self.result();row=next(x for x in r['state_budget'] if x['state']=='manual_quarter')
        self.assertAlmostEqual(row['remaining_before_reference_and_other_errors_V'],-.002927767658873705)
        self.assertFalse(row['nonnegative_allocation_possible_without_loading_correction'])
        self.assertIsNone(r['complete_static_error_bound_V'])

    def test_reference_table_and_matched_ratio_not_independent_tolerances(self):
        r=self.result()
        self.assertAlmostEqual(r['negative_reference_independent_ratio_error_V'],.010010010010)
        self.assertEqual(r['matched_ratio_only_contribution_V'],[.0005,.000625])
        self.assertEqual(r['reference_initial_table_sensitivity_V'],.005)

    def test_spare_network_not_drop_in(self):
        r=self.result()['matched_spare_option']
        self.assertEqual(r['pairs'],{'R3':['3','6'],'R4':['4','5']})
        self.assertFalse(r['adopted'])
        self.assertAlmostEqual(r['inverting_bias_sensitivity_V_at_15nA_Rmax'][1],.0016125)

    def test_target_cannot_relax(self):
        self.d['existing_static_target_V']=.02
        with self.assertRaisesRegex(ValueError,'criterion'):self.result()

    def test_matched_bound_cannot_improve_silently(self):
        self.d['matched_ratio_sensitivities']=[.00001,.0000125]
        with self.assertRaisesRegex(ValueError,'matching'):self.result()

    def test_unapproved_behavior_or_adoption_rejected(self):
        for key in ('frequency_requirements_approved','hardware_correction_applied'):
            self.d[key]=True
            with self.assertRaisesRegex(ValueError,'promotion'):self.result()
            self.d[key]=False

    def test_symmetric_RC_cancellation_and_mismatch(self):
        for f in (0,1000,20000):self.assertEqual(s.balanced_transfer(.5,f,1e5,1e-11,1e-11),0)
        result=self.result()['ac_tradeoffs'][-1]
        self.assertGreater(result['existing_center_gain'],.06)
        self.assertGreater(result['symmetric_independent_5percent_cap_worst_center_gain'],.006)
        self.assertLess(result['symmetric_independent_5percent_cap_worst_center_gain'],.007)

    def test_cap_value_changes_settling_not_DC_loading(self):
        rows=[r for r in self.result()['control_tradeoffs'] if r['return_ohm']==1e7]
        self.assertEqual(rows[0]['worst_loading_error_V'],rows[1]['worst_loading_error_V'])
        self.assertAlmostEqual(rows[0]['center_1percent_settling_s']/rows[1]['center_1percent_settling_s'],10)

    def test_higher_return_tradeoff_not_free_accuracy(self):
        rows=[r for r in self.result()['control_tradeoffs'] if r['cap_F']==1e-8]
        self.assertGreater(abs(rows[0]['worst_loading_error_V']),abs(rows[1]['worst_loading_error_V']))
        self.assertEqual(rows[2]['open_wiper_V_per_nA'],1)


if __name__=='__main__':unittest.main()
