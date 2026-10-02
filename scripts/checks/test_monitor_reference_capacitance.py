"""Capacitance/source/topology admission and failed-source mutation regressions."""
import copy
from fractions import Fraction as F
import json
import math
from pathlib import Path
import tempfile
import unittest
from unittest import mock
from scripts.checks import monitor_reference_capacitance as check


def load():
    return {key:json.loads((check.ROOT/path).read_bytes()) for key,path in check.INPUTS.items()}


class ReferenceCapacitanceTests(unittest.TestCase):
    def setUp(self):
        self.data = load()

    def test_exact_interval_and_narrow_admission_scope(self):
        result = check.calculate(self.data)
        lo,hi = map(F,result['exact_interval_F'])
        self.assertEqual((lo,hi),(F(296109,10**12),F(303909,10**12)))
        self.assertLessEqual(F.from_float(result['capacitance_interval_F'][0]),lo)
        self.assertGreaterEqual(F.from_float(result['capacitance_interval_F'][1]),hi)
        self.assertTrue(result['capacitance_value_range_admitted'])
        for key in ('qualification_accepted','canonical_protection_implemented',
                    'common_accuracy_timing_condition_matched',
                    'installed_reference_stability_qualified','precision_reference_validity_qualified'):
            self.assertFalse(result[key],key)

    def test_strict_range_rejects_one_cap_and_upper_boundary(self):
        for count in (1,100):
            bounds=check.bank_interval(count,1e-7,.01,30e-6,25,[-40,125])
            with self.assertRaisesRegex(ValueError,'strictly inside'):
                check.require_range(bounds,[1e-7,1e-5])
        for bounds in ((F('1e-7'),F('2e-7')),(F('2e-7'),F('1e-5'))):
            with self.assertRaises(ValueError):check.require_range(bounds,[1e-7,1e-5])

    def test_physical_domains_reject_invalid_arithmetic(self):
        baseline=[3,1e-7,.01,30e-6,25,[-40,125]]
        for index,values in ((0,[0,-1,True,1.5]),(1,[0,-1,math.nan,math.inf,True]),
                             (2,[-.1,1,math.nan]),(3,[-.1,.1,math.inf]),(4,[math.nan])):
            for value in values:
                with self.subTest(index=index,value=value):
                    args=copy.deepcopy(baseline);args[index]=value
                    with self.assertRaises(ValueError):check.bank_interval(*args)
        with self.assertRaises(ValueError):check.bank_interval(3,1e-7,.01,30e-6,25,[125,-40])

    def test_source_conditions_cannot_be_reinterpreted(self):
        for suffix in check.FACT_LOCKS:
            data=copy.deepcopy(self.data)
            fact=next(f for f in data['facts']['facts'] if f['fact_id']==check.FACT_PREFIX+suffix)
            fact['conditions']='Unconditional system qualification'
            with self.assertRaises(ValueError):check.calculate(data)
        for suffix,value in [('tolerance',-1),('temperature-coefficient',math.nan),
                             ('voltage-change',False),('aging',True)]:
            data=copy.deepcopy(self.data)
            next(f for f in data['facts']['facts'] if f['fact_id']==check.FACT_PREFIX+suffix)['value']=value
            with self.assertRaises(ValueError):check.calculate(data)

    def test_removing_or_declassifying_source_support_fails(self):
        sid=check.SOURCE_PREFIX+'land'
        for field,value in [('sha256','0'*64),('authority_class','PROJECT_GENERATOR'),
                            ('availability','SOURCE UNAVAILABLE')]:
            data=copy.deepcopy(self.data)
            next(s for s in data['sources']['sources'] if s['source_id']==sid)[field]=value
            with self.assertRaises(ValueError):check.calculate(data)
        data=copy.deepcopy(self.data)
        rec=next(r for r in data['manifest']['records'] if r['record_id']==check.RECORD)
        rec['fact_ids'].remove(check.FACT_PREFIX+'voltage-change')
        with self.assertRaises(ValueError):check.calculate(data)
        data=copy.deepcopy(self.data)
        data['sources']['sources']=[s for s in data['sources']['sources'] if s['source_id']!=sid]
        with self.assertRaises((KeyError,ValueError)):check.calculate(data)

    def test_wrong_identity_value_and_ref_connectivity_fail(self):
        for field,value in [('mpn','C0603C104K5RACTU'),('value',1e-8),
                            ('pins',{'1':'+5V','2':'AGND'}),('pins',{'1':'REF','2':'OTHER_GND'})]:
            data=copy.deepcopy(self.data)
            next(p for p in data['spec']['components'] if p['ref']=='C104')[field]=value
            with self.assertRaises(ValueError):check.calculate(data)
        data=copy.deepcopy(self.data)
        data['spec']['components'].append(copy.deepcopy(data['spec']['components'][-1]))
        with self.assertRaises(ValueError):check.calculate(data)

    def test_extra_ref_capacitor_and_population_changes_fail(self):
        data=copy.deepcopy(self.data)
        cap=copy.deepcopy(next(p for p in data['spec']['components'] if p['ref']=='C104'))
        cap['ref']='C111';data['spec']['components'].append(cap)
        with self.assertRaisesRegex(ValueError,'coverage'):check.calculate(data)
        data=copy.deepcopy(self.data)
        next(p for p in data['spec']['components'] if p['ref']=='C104')['dnp']=True
        with self.assertRaises(ValueError):check.calculate(data)
        data=copy.deepcopy(self.data)
        next(p for p in data['inventory']['lines'] if p['mpn']==check.MPN)['dnp']=False
        with self.assertRaisesRegex(ValueError,'population'):check.calculate(data)

    def test_rated_voltage_and_dc_applicability_cannot_be_changed(self):
        for suffix,field,value in [
                ('rated-voltage','value',3),
                ('rated-voltage','conditions','Qualified at every fault voltage'),
                ('voltage-change','value',.1),
                ('voltage-change','conditions','No change at any applied voltage')]:
            data=copy.deepcopy(self.data)
            next(f for f in data['facts']['facts'] if f['fact_id']==check.FACT_PREFIX+suffix)[field]=value
            with self.assertRaises(ValueError):check.calculate(data)

    def test_nonpolar_pin_reversal_and_json_order_do_not_change_bounds(self):
        before=check.calculate(self.data)['exact_interval_F']
        next(p for p in self.data['spec']['components'] if p['ref']=='C104')['pins']={'2':'REF','1':'AGND'}
        self.assertEqual(check.calculate(self.data)['exact_interval_F'],before)

    def test_ref_range_and_qualification_cannot_be_weakened(self):
        next(f for f in self.data['facts']['facts'] if f['fact_id']==check.REF_FACT)['value']['minimum']=1e-9
        with self.assertRaises(ValueError):check.calculate(self.data)
        data=load();data['spec']['qualification_accepted']=True
        with self.assertRaises(ValueError):check.calculate(data)

    def test_frozen_input_mutation_cannot_rebind_old_parameters(self):
        with tempfile.TemporaryDirectory() as folder:
            root=Path(folder)
            for key,path in check.INPUTS.items():
                p=root/path;p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(self.data[key]))
            frozen={root/p:(root/p).read_bytes() for p in check.INPUTS.values()}
            report=root/'report.json';original=check.calculate
            def mutate(data):
                result=original(data)
                p=root/check.INPUTS['spec'];p.write_bytes(p.read_bytes()+b' ')
                return result
            with mock.patch.object(check,'ROOT',root),mock.patch.object(check,'REPORT',report),\
                 mock.patch.object(check,'snapshot',return_value=frozen),mock.patch.object(check,'calculate',side_effect=mutate):
                with self.assertRaisesRegex(ValueError,'changed during'):check.run()
            self.assertFalse(report.exists())


if __name__=='__main__':unittest.main()
