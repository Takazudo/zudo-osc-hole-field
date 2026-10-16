"""Independent numerical identities and adversarial evidence/source boundaries."""
import copy
import math
import unittest
import stage22_requirements as s


class Physics(unittest.TestCase):
    def test_static_budget_drift_and_approval_promotion(self):
        original = {'static_target_V': .002, 'new_criteria_approved': False}
        s.validate_criteria(original)
        for change in ({'static_target_V': .01}, {'new_criteria_approved': True}):
            with self.assertRaisesRegex(ValueError, 'retained static criterion'):
                s.validate_criteria(original | change)

    def test_enable_is_divider_not_patch_load(self):
        d=s.divider(5,1000,100000)
        self.assertAlmostEqual(d['current_A'],5/101000)
        self.assertAlmostEqual(d['power_top_W'],2.4507401235e-6)
        self.assertLess(d['power_top_W'],3e-6)
        self.assertAlmostEqual(s.power(5,1000,.001),.025025025025)

    def test_grounded_sense_and_rail_spanning_LED_differ(self):
        self.assertAlmostEqual(s.power(24,22100,.001),.02608943785)
        self.assertAlmostEqual(s.power(12,5600,.001),.02574002574)
        self.assertAlmostEqual(s.power(24,5600,.001),4*s.power(12,5600,.001))

    def test_wiper_matches_direct_kcl(self):
        for a in (0,.1,.3,.5,.8,1):
            d=s.wiper(a,-5,5,100000,1000,1e7,1e-8)
            kcl=(d['loaded_V']-d['unloaded_V'])/d['thevenin_ohm']+d['loaded_V']/1e7
            self.assertAlmostEqual(kcl,0,places=15)
        mid=s.wiper(.5,-5,5,100000,1000,1e7,1e-8)
        self.assertEqual(mid['loaded_V'],0)
        self.assertAlmostEqual(mid['tau_s'],.000259325753)

    def test_worst_loading_is_interior_not_midpoint(self):
        a=s.bipolar_worst_loading(100000,1000,1e7)
        self.assertGreater(a,.5);self.assertLess(a,1)
        worst=abs(s.wiper(a,-5,5,100000,1000,1e7,1e-8)['loading_error_V'])
        for i in range(1001):
            self.assertLessEqual(abs(s.wiper(i/1000,-5,5,100000,1000,1e7,1e-8)['loading_error_V']),worst+1e-12)
        self.assertGreater(worst,.005)

    def test_attenuator_dc_and_frequency_limits(self):
        self.assertEqual(s.attenuation(0,0,1e5,1e-11),-1)
        self.assertEqual(s.attenuation(.5,0,1e5,1e-11),0)
        self.assertEqual(s.attenuation(1,20000,1e5,1e-11),1)
        x=2*math.pi*20000*1e5*1e-11
        self.assertAlmostEqual(abs(s.attenuation(.5,20000,1e5,1e-11)),.5*x/math.sqrt(1+x*x))
        self.assertGreater(abs(s.attenuation(.5,20000,1e5,1e-11)),.06)

    def test_physical_domains(self):
        for v in (0,-1,float('inf'),float('nan'),True):
            with self.assertRaises(ValueError):s.power(5,v)
        with self.assertRaises(ValueError):s.attenuation(.5,-1,1000,1e-8)
        with self.assertRaises(ValueError):s.wiper(1.1,-5,5,1e5,1000,1e7,1e-8)


class Audit(unittest.TestCase):
    def setUp(self):
        self.packages=s.read(s.ROOT/s.REL/'stage16/inputs-report.json')['packages']
        self.standard=s.read(s.ROOT/'design/standard/electrical-standard.json')
        self.prior=s.read(s.ROOT/s.REL/'stage21/inventory-input.json')
        self.assumptions=s.read(s.OUT/'assumptions.json')
        self.evidence=s.read(s.OUT/'evidence.json')

    def analyze(self):return s.analyze(self.packages,self.standard,self.prior,self.assumptions)

    def test_all_roles_covered_without_acceptance(self):
        result=self.analyze();self.assertEqual(len(result['references']),19)
        self.assertFalse(result['electrical_acceptance'])
        self.assertFalse(result['attenuverter_AC']['closed_loop_stability_proven'])
        self.assertAlmostEqual(result['reference_ratio_error_max_V_at_5V'],.010010010010)

    def test_missing_changed_or_rewired_unit(self):
        for key in ('pins','unit_records','canonical'):
            old=copy.deepcopy(self.packages['C7104']);self.packages['C7104'][key]={}
            with self.assertRaisesRegex(ValueError,'source topology'):self.analyze()
            self.packages['C7104']=old

    def test_adjacent_divider_value_not_silently_changed(self):
        self.packages['R7104']['unit_records'][0]['value']='1000 Ω'
        with self.assertRaisesRegex(ValueError,'adjacent'):self.analyze()

    def test_no_assumption_promotion(self):
        self.assumptions['owner_approved']=True
        with self.assertRaisesRegex(ValueError,'owner approval'):self.analyze()

    def test_wrong_nominal_rails(self):
        self.standard['signals']['rails_V']['+12V']=13.2
        with self.assertRaisesRegex(ValueError,'nominal/fault'):self.analyze()

    def test_correct_mirrored_drawing_views(self):
        s.validate_evidence(self.evidence)
        f=s.drawing_coordinates(self.evidence['DIN']['female']);m=s.drawing_coordinates(self.evidence['DIN']['male'])
        self.assertEqual(len(f),96);self.assertEqual(len(m),96)
        self.assertEqual(f['a1'],[39.37,2.54]);self.assertEqual(m['a1'],[39.37,-2.54])
        self.assertEqual(f['c32'],[-39.37,-2.54])

    def test_mirrored_label_substitution(self):
        self.evidence['DIN']['male']['top_to_bottom']=['a','b','c']
        with self.assertRaisesRegex(ValueError,'handedness'):s.validate_evidence(self.evidence)

    def test_missing_contacts_or_other_termination_drill(self):
        original=copy.deepcopy(self.evidence)
        for key,value in [('holes',95),('hole_diameter_mm',1.15)]:
            self.evidence=copy.deepcopy(original);self.evidence['DIN']['female'][key]=value
            with self.assertRaises(ValueError):s.validate_evidence(self.evidence)

    def test_no_invented_male_PCB_fixing_hole(self):
        self.evidence['DIN']['male']['fixing_board_holes']={'diameter_mm':2.55}
        with self.assertRaisesRegex(ValueError,'not PCB'):s.validate_evidence(self.evidence)

    def test_wrong_family_derating(self):
        self.evidence['RT_derating']['zero_power_temperature_C']=125
        with self.assertRaisesRegex(ValueError,'RT0603'):s.validate_evidence(self.evidence)

    def test_no_supplier_code_or_stock_substitution(self):
        source=self.evidence['sources']['digikey-C0603C100J5GACTU']
        source['stock_quantity']=0
        with self.assertRaisesRegex(ValueError,'not stock'):s.validate_evidence(self.evidence)
        source['stock_quantity']=None;source['supplier_code_cut_tape']='C12345'
        with self.assertRaisesRegex(ValueError,'SKU'):s.validate_evidence(self.evidence)

    def test_manufacturer_receipt_substitution(self):
        self.evidence['sources']['female-pcb']['sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'exact primary'):s.validate_evidence(self.evidence)


if __name__=='__main__':unittest.main()
