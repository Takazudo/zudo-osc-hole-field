"""Adversarial checks for the bounded owner scope and exact candidate inventory."""
import copy
import unittest
import stage26_acceptance as s

class AcceptanceTests(unittest.TestCase):
    def setUp(self):
        self.scope=s.read(s.OUT/'acceptance.json');self.checks=s.read(s.OUT/'functional-checks.json')
        self.units=s.read(s.ROOT/s.REL/'stage18/compatibility-report.json')['unit_metadata']
        self.packages=s.read(s.ROOT/s.REL/'stage16/inputs-report.json')['packages']
        self.patch=s.read(s.ROOT/s.REL/'stage23/candidate-selection.patch.json')
        self.osc=s.read(s.OUT/'oscillator-calibration.json');self.net=s.read(s.ROOT/s.REL/'candidate-netlist.json')
    def test_valid_scope(self):s.validate_scope(self.scope,self.checks)
    def test_scope_negative_cases(self):
        mutations=[('scope_modules',['A01']),('scope_modules',s.MODULES+['O1']),('new_numeric_accuracy_limit',.01),
                   ('hardware_acceptance',True),('precision_pitch_cv_service_claim',True)]
        for key,value in mutations:
            with self.subTest(key=key,value=value):
                x=copy.deepcopy(self.scope);x[key]=value
                with self.assertRaises(ValueError):s.validate_scope(x,self.checks)
    def test_authority_and_removed_obligations_bound(self):
        for key,value in [('owner_quote_ja','modified '+self.scope['owner_quote_ja']),('removed_obligations',[])]:
            x=copy.deepcopy(self.scope);x[key]=value
            with self.assertRaises(ValueError):s.validate_scope(x,self.checks)
    def test_missing_gap_cannot_be_hidden(self):
        self.osc['actual_missing_items']=['','']
        with self.assertRaises(ValueError):s.validate_oscillator(self.osc,self.net)
    def test_retired_not_passed(self):
        for key in self.scope['retired_criteria']:
            x=copy.deepcopy(self.scope);x['retired_criteria'][key]['disposition']='PASS'
            with self.assertRaises(ValueError):s.validate_scope(x,self.checks)
    def test_safety_omission_and_false_pass(self):
        for key in self.checks:
            for action in ('omit','pass'):
                x=copy.deepcopy(self.checks)
                if action=='omit':del x[key]
                else:x[key]['accepted']=True
                with self.assertRaises(ValueError):s.validate_scope(self.scope,x)
    def test_pot_and_dielectric_exception(self):
        for group,key,value in [('pot_disposition','nominal_ohm',10000),('filter_exception','global_c_small_policy_changed',True),('filter_exception','ref','C7104')]:
            x=copy.deepcopy(self.scope);x[group][key]=value
            with self.assertRaises(ValueError):s.validate_scope(x,self.checks)
    def test_precision_paths_unchanged(self):
        standard=s.read(s.ROOT/'design/standard/electrical-standard.json')
        for module in ('O1','O5','MULT','S&H','A010','A07','MASTER_REFERENCE'):
            self.assertEqual(s.resolve(module,self.scope,standard)['calibration'],standard['calibration'])
        for module in s.MODULES:self.assertIsNone(s.resolve(module,self.scope,standard)['static_limit_V'])
    def test_materialization(self):
        result=s.materialize(self.units,self.packages,self.patch,self.scope)
        self.assertEqual(result['counts'],dict(references=118,pins=561,unit_UUIDs=154,selected_passives=19))
    def test_omitted_selection(self):
        self.patch['operations'].pop()
        with self.assertRaises(ValueError):s.materialize(self.units,self.packages,self.patch,self.scope)
    def test_supplier_substitution(self):
        self.patch['operations'][0]['proposed']['supplier_order_code']='C000'
        with self.assertRaises(ValueError):s.materialize(self.units,self.packages,self.patch,self.scope)
    def test_all_unit_metadata_protected(self):
        result=s.materialize(self.units,self.packages,self.patch,self.scope)
        for key,unit in self.units.items():
            for field in unit:
                after=copy.deepcopy(result['source_units']);after[key][field]=None
                with self.subTest(unit=key,field=field),self.assertRaises(ValueError):
                    s.validate_materialization(self.units,after,result['selections'])
    def test_rewire_nc_short_missing_unit(self):
        result=s.materialize(self.units,self.packages,self.patch,self.scope)
        for key,unit in self.units.items():
            if unit['pins']:
                after=copy.deepcopy(result['source_units']);pin=next(iter(unit['pins']));after[key]['pins'][pin]='WRONG_NET'
                with self.assertRaises(ValueError):s.validate_materialization(self.units,after,result['selections'])
        nc_cases=[(key,pin) for key,row in self.units.items() for pin,net in row['pins'].items() if net is None]
        self.assertTrue(nc_cases)
        for key,pin in nc_cases:
            after=copy.deepcopy(result['source_units']);after[key]['pins'][pin]='AGND'
            with self.assertRaises(ValueError):s.validate_materialization(self.units,after,result['selections'])
        after=copy.deepcopy(result['source_units']);after.pop(next(iter(after)))
        with self.assertRaises(ValueError):s.validate_materialization(self.units,after,result['selections'])
        with self.assertRaises(ValueError):s.summarize_units(after)
    def test_oscillator_valid(self):s.validate_oscillator(self.osc,self.net)
    def test_oscillator_role_confusion(self):
        for key in ('base_pitch_trim_fixes_scale','upstream_quantizer_fixes_downstream_tracking','global_tracking_numeric_targets_changed','new_controls_required_by_source_review'):
            x=copy.deepcopy(self.osc);x[key]=True
            with self.assertRaises(ValueError):s.validate_oscillator(x,self.net)
    def test_oscillator_missing_trim_or_substitution(self):
        for role in self.osc['inspected_trim_packages']:
            x=copy.deepcopy(self.osc);del x['inspected_trim_packages'][role]
            with self.assertRaises(ValueError):s.validate_oscillator(x,self.net)
        x=copy.deepcopy(self.osc);x['inspected_trim_packages']['HF_TRIM']['attributes']['MPN']='TC33X-2-103E'
        with self.assertRaises(ValueError):s.validate_oscillator(x,self.net)
    def test_oscillator_unearned_qualification(self):
        for key,value in [('actual_range_qualification','PASS'),('physical_calibration','PASS'),('new_controls_added',1),('VCO_1V_per_oct_requirement_preserved',False)]:
            x=copy.deepcopy(self.osc);x[key]=value
            with self.assertRaises(ValueError):s.validate_oscillator(x,self.net)

if __name__=='__main__':unittest.main()
