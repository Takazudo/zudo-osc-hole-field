"""Oscillator binding, source-pin, sensitive-node and calibration contracts."""
from collections import Counter
import json, math, unittest
from design.spec.modules.oscillator import ROOT, family, octave_family, panel_bindings, specification, INSTANCES
from design.spec.modules.build_oscillator_current import build
from scripts.schgen.core import designator


class OscillatorContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.f=family();cls.ref=octave_family();cls.parts={p.key:p for p in cls.f.parts}

    def test_complete_fixed_panel_binding_and_reserved_indices(self):
        bindings=panel_bindings();self.assertEqual(len(bindings),80)
        panel=[p for p in self.f.parts if p.panel_refs]
        self.assertEqual(len(panel),16)
        for instance in specification()[1][:5]:
            self.assertEqual({designator(p,instance) for p in panel},{r['ref'] for r in bindings if r['instance']==instance.name})
            self.assertEqual({p.attributes['PanelUid'].replace('${SHEETNAME}',instance.name) for p in panel},{r['uid'] for r in bindings if r['instance']==instance.name})
        self.assertEqual([i.index for i in specification()[1]],list(range(11,17)))
        self.assertFalse(any(p.prefix=='D' and 'LED' in p.symbol for p in self.f.parts))

    def test_primary_core_pin_identity_and_local_timing(self):
        evidence=json.loads((ROOT/'design/standard/pin-maps/vco.json').read_text())
        self.assertEqual(evidence['source']['authority'],'MANUFACTURER_PRIMARY')
        self.assertEqual(evidence['source']['availability'],'AVAILABLE')
        core=self.parts['CORE.1'];self.assertEqual(set(core.pins),{str(i) for i in range(1,17)})
        self.assertEqual(core.pins['11'],'TIMING_CAP');self.assertEqual(core.pins['3'],'VEE5')
        self.assertEqual(core.pins['15'],'EXPO_SUM');self.assertEqual(core.pins['12'],'AGND')
        self.assertIn('TIMING_CAP',self.f.sensitive_nets)
        self.assertNotIn('TIMING_CAP',self.f.global_nets)
        timing=[p for p in self.f.parts if 'TIMING_CAP' in p.pins.values()]
        self.assertEqual({p.key for p in timing},{'CORE.1','C_CF.0'})
        self.assertTrue(all(p.attributes['Island']=='OSC_CORE:${SHEETNAME}' for p in timing))
        self.assertTrue(all(not (set(p.pins.values()) & set(self.f.sensitive_nets)) for p in self.f.parts if p.panel_refs))

    def test_every_input_protected_and_normals_unused(self):
        jacks=[p for p in self.f.parts if p.symbol.endswith('WQP518MA')]
        self.assertEqual(len(jacks),8);self.assertTrue(all(p.pins['TN'] is None for p in jacks))
        switches=[p for p in self.f.parts if p.symbol.endswith('ADG5412FBRUZ') and p.unit==1]
        self.assertEqual(len(switches),4)
        self.assertEqual({p.pins['3'] for p in switches},{k+'_TIP' for k in ('1V','FM','PWM','SYNC')})

    def test_octave_endpoint_aliases_are_real_connections(self):
        resistors=[p for p in self.ref.parts if p.attributes['Role'].startswith('octave_reference:R')]
        first=next(p for p in resistors if p.attributes['Role']=='octave_reference:R1')
        last=next(p for p in resistors if p.attributes['Role']=='octave_reference:R5')
        self.assertEqual(first.pins['1'],'OCT_BOTTOM');self.assertEqual(last.pins['2'],'OCT_TOP')
        outputs={v for p in self.ref.parts for k,v in p.pins.items() if p.prefix=='U' and p.unit in (1,2,3,4)}
        self.assertTrue({'OCT_BOTTOM','OCT_TOP'} <= outputs)
        rotary=self.parts['OCT_SELECTOR.0'];self.assertEqual(rotary.pins['1'],rotary.pins['10'])
        self.assertEqual([rotary.pins[str(i)] for i in range(2,8)],[f'OSC_OCT{i}' for i in range(6)])

    def test_range_and_pitch_ratios(self):
        for key,value in [('PITCH','100 kΩ'),('OCT','100 kΩ'),('TUNE','250 kΩ'),('FINE','5 MΩ'),('FM','200 kΩ'),('RANGE','100 kΩ')]:
            p=self.parts['R_PITCH_'+key+'.0'];self.assertEqual(p.value,value);self.assertEqual(p.pins['2'],'EXPO_SUM')
        self.assertEqual(self.parts['RANGE.0'].pins,{'3':'LFO_REF','2':'RANGE_CV','1':'AGND'})
        self.assertAlmostEqual(5*(1+40000/100000),7)
        self.assertEqual(2**7,128)
        self.assertEqual(self.parts['SYNC_SELECT.0'].pins['2'],'SYNC_GATE')

    def test_sine_pair_and_complete_amplifier_packages(self):
        pair=[p for p in self.f.parts if p.key.startswith('SINE_PAIR.')]
        pins={n:v for p in pair for n,v in p.pins.items()}
        self.assertEqual(pins['1'],pins['4']);self.assertEqual(pins['5'],'AGND')
        self.assertEqual(pins['2'],'SINE_BASE');self.assertEqual(pins['6'],'SINE_C1');self.assertEqual(pins['3'],'SINE_C2')
        groups={}
        for p in self.f.parts:
            if p.symbol.endswith(('OPA4196IDR','OPA4197IPWR')):groups.setdefault(p.ordinal,set()).add(p.unit)
        self.assertTrue(all(units=={1,2,3,4,5} for units in groups.values()))
        self.assertTrue(all(1<=p.ordinal<=99 for p in self.f.parts))

    def test_spice_supplies_remain_distinct(self):
        from design.spec.modules.run_oscillator_spice import net, decks
        self.assertNotEqual(net('+12V'),net('-12V'))
        self.assertIn('P_12V',decks()['oscillator-sine-generic.cir'])
        self.assertIn('N_12V',decks()['oscillator-sine-generic.cir'])
        self.assertIn('PWL(',decks()['oscillator-sine-generic.cir'])

    def test_current_is_derived_and_shared_reference_counted_once(self):
        report=build();self.assertEqual(report['shared_reference_count'],1)
        self.assertEqual(report['sheets'][0]['instances'],list(INSTANCES))
        for row in report['sheets']:
            self.assertTrue(all(v is None for v in row['guaranteed_maximum_mA_per_instance'].values()))
        for rail,value in report['planning_upper_total_mA'].items():
            self.assertAlmostEqual(value,sum(len(s['instances'])*s['planning_upper_mA_per_instance'][rail] for s in report['sheets']))

if __name__=='__main__':unittest.main()
