import copy
import json
from fractions import Fraction as F
from pathlib import Path
import unittest
from unittest.mock import Mock, patch
from scripts.checks import rail_monitor_candidate as monitor
from scripts.checks.rail_monitor_candidate import (
    SPEC,calculate,delay_bound,divider_bounds,isolator_state,run,validate_sources)


class RailMonitorTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.spec=json.loads(SPEC.read_text())

    def test_normal_bands_require_recovery_not_just_nominal_trip(self):
        result=calculate(self.spec)
        self.assertEqual({r['rail'] for r in result['static_divider_cases']},{'+12V','-12V','+5V'})
        for row in result['static_divider_cases']:
            self.assertTrue(row['conditional_static_recovery_covers_normal_band'])
            self.assertGreater(row['normal_recovery_lower_margin_V'],0)
            self.assertGreater(row['normal_recovery_upper_margin_V'],0)
        narrow=copy.deepcopy(self.spec);narrow['supervisor']['window_fraction']=.06
        self.assertFalse(all(r['conditional_static_recovery_covers_normal_band'] for r in calculate(narrow)['static_divider_cases']))

    def test_independent_single_corner_and_hysteresis_direction(self):
        s=self.spec;row=s['divider_candidates'][0]
        r=divider_bounds(row,s['supervisor'],s['resistor_condition'])
        # Full +125 C tolerance, worst UV recovery corner independently.
        tol=F(1,1000);drift=F(25,1000000)*100
        ru=14000*(1+tol)*(1+drift);rd=1000*(1-tol)*(1-drift)
        threshold=F(8,10)*F(93,100)*F(101,100)*F(101,100)
        expected=threshold*(1+ru/rd)+F(350,10**9)*ru
        self.assertEqual(r['UV_recover'][1],expected)
        self.assertGreater(r['UV_recover'][1],r['UV_trip'][1])
        self.assertLess(r['OV_recover'][0],r['OV_trip'][0])
        # KCL at that corner reproduces the sense threshold.
        sense=(expected/ru-F(350,10**9))/(1/ru+1/rd)
        self.assertEqual(sense,threshold)

    def test_changed_passive_envelope_changes_result(self):
        s=copy.deepcopy(self.spec)
        s['resistor_condition']['tolerance_fraction']=.02
        self.assertFalse(all(r['conditional_static_recovery_covers_normal_band'] for r in calculate(s)['static_divider_cases']))
        s=copy.deepcopy(self.spec)
        s['divider_candidates'][0]['bottom'][0]['ohm']=900
        self.assertFalse(calculate(s)['static_divider_cases'][0]['conditional_static_recovery_covers_normal_band'])
        with self.assertRaisesRegex(ValueError,'exact resistor source'):validate_sources(s)

    def test_maximum_delay_requires_all_stated_conditions(self):
        s=self.spec['supervisor']
        context={'overdrive_fraction':.10,'pullup_ohm':10000,'load_F':10e-12,'supply_V':3.3,'temperature_C':125}
        self.assertEqual(delay_bound(s,context),10e-6)
        for key,value in [('overdrive_fraction',.01),('pullup_ohm',100000),('load_F',100e-12),
                          ('supply_V',1.6),('temperature_C',126)]:
            changed=dict(context);changed[key]=value
            self.assertIsNone(delay_bound(s,changed))
        changed=dict(context);changed['temperature_C']=True
        with self.assertRaisesRegex(ValueError,'finite'):delay_bound(s,changed)
        changed=copy.deepcopy(s);changed['fixed_reset_delay_s']=.001
        self.assertIsNone(delay_bound(changed,context))

    def test_isolator_default_does_not_cover_brownout_or_dead_receiver(self):
        f=self.spec['floating_negative_trial']
        self.assertEqual(isolator_state(0,5,'OPEN',f),'LOW')
        self.assertEqual(isolator_state(3.3,5,'HIGH',f),'HIGH')
        self.assertEqual(isolator_state(3.3,5,'OPEN',f),'LOW')
        for a,b in [(0,5),(1.9,5),(3.3,1.9),(0,0),(3.3,0)]:
            self.assertEqual(isolator_state(a,b,'HIGH',f),'UNDEFINED')

    def test_floating_domain_reversal_is_not_reverse_current_blocking(self):
        report=calculate(self.spec)
        cases={r['VN_relative_AGND_V']:r for r in report['floating_negative_pin_stress']}
        self.assertFalse(cases[-11.74]['ldo_input_absolute_rating_violated'])
        self.assertTrue(cases[1]['ldo_input_absolute_rating_violated'])
        self.assertTrue(cases[12.48]['unloaded_monitor_sense_outside_absolute_rating'])
        self.assertIsNone(report['startup_maximum_s'])
        self.assertFalse(report['protection_implemented'])
        self.assertEqual(len(report['all_rail_arrival_orders_required']),6)
        self.assertTrue(report['state_sequence_validation'].startswith('NOT RUN'))

    def test_source_identity_and_forbidden_promotions(self):
        validate_sources(self.spec)
        for path,value in [(('protection_implemented',),True),
                           (('supervisor','startup_max_s'),.014),
                           (('comparison','propagation_max_s'),29e-6),
                           (('supervisor','used_channels'),[1,2]),
                           (('supervisor','adjustable_input_current_table_max_A'),0),
                           (('supervisor','delay_conditions','overdrive_fraction'),.01),
                           (('supervisor','delay_conditions','pullup_ohm'),100000),
                           (('supervisor','delay_conditions','load_F'),100e-12),
                           (('supervisor','delay_conditions','supply_V'),[1.6,6]),
                           (('supervisor','delay_conditions','temperature_C'),[-40,150]),
                           (('supervisor','delay_conditions','fixed_reset_delay_greater_than_s'),0),
                           (('floating_negative_trial','isolator_connections','3'),'NC'),
                           (('floating_negative_trial','isolator_connections','7'),'ENABLE')]:
            s=copy.deepcopy(self.spec);target=s
            for key in path[:-1]:target=target[key]
            target[path[-1]]=value
            with self.assertRaises(ValueError):validate_sources(s)

    def test_generated_report_is_current(self):
        run(check=True)

    def test_every_required_source_record_is_bound(self):
        original=json.loads(monitor.SOURCES.read_text())
        for record in original['sources']:
            for missing in (True,False):
                changed=copy.deepcopy(original)
                if missing:
                    changed['sources']=[r for r in changed['sources'] if r['id']!=record['id']]
                else:
                    next(r for r in changed['sources'] if r['id']==record['id'])['mpn']='WRONG-MPN'
                with self.subTest(source=record['id'],missing=missing), patch.object(
                        monitor,'SOURCES',Mock(read_text=lambda:json.dumps(changed))):
                    with self.assertRaisesRegex(ValueError,'required device/source'):
                        validate_sources(self.spec)

    def test_source_hash_and_size_metadata_rejected_before_byte_verification(self):
        original=json.loads(monitor.SOURCES.read_text())
        for key,value in [('sha256','z'*64),('sha256','0'*64),('bytes',0),('bytes',True)]:
            changed=copy.deepcopy(original);changed['sources'][0][key]=value
            with patch.object(monitor,'SOURCES',Mock(read_text=lambda:json.dumps(changed))):
                with self.assertRaisesRegex(ValueError,'primary metadata'):
                    validate_sources(self.spec)


if __name__=='__main__':unittest.main()
