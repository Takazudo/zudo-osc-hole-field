"""MIX5/MIX4 topology, locked panel identity and current-report regression."""
from collections import Counter,defaultdict
import unittest
from scripts.schgen.core import designator
from design.spec.modules import mix5,mix4_vca
from design.spec.modules.build_mixer_current import build
from design.spec.modules.run_mixer_spice import model_failures, exit_on_model_failures, mixer4, OFFSET_WIPER_V, TIA_TRIM_OHM


class MixerContract(unittest.TestCase):
    def assert_bindings(self,module):
        f=module.family();rows=module.panel_bindings();panel=[p for p in f.parts if p.panel_refs]
        self.assertEqual(len(rows),38);self.assertEqual(len(panel),19)
        self.assertEqual(len({p.key for p in f.parts}),len(f.parts))
        for inst in module.specification()[1]:
            self.assertEqual({designator(p,inst) for p in panel},
                             {r['ref'] for r in rows if r['instance']==inst.name})
            self.assertEqual({p.attributes['PanelUid'].replace('${SHEETNAME}',inst.name) for p in panel},
                             {r['uid'] for r in rows if r['instance']==inst.name})
        self.assertEqual(set(f.global_nets),{'+12V','-12V','+5V','AGND'})
        for p in f.parts:
            self.assertTrue(set(f.sensitive_nets).isdisjoint(f.global_nets))
        return f

    def role(self,f,name):
        return [p for p in f.parts if p.attributes.get('Role')==name]

    def test_mix5_bindings_and_protected_summer(self):
        f=self.assert_bindings(mix5)
        self.assertEqual([i.index for i in mix5.specification()[1]],[81,82])
        self.assertEqual(len([p for p in f.parts if p.symbol.endswith('WQP518MA')]),6)
        self.assertTrue(all(p.symbol.endswith('PTV09A-4020F-B103') for p in f.parts if p.panel_refs and p.prefix=='RV'))
        self.assertEqual(len([p for p in f.parts if p.symbol.endswith('ADG5412FBRUZ') and p.unit==1]),5)
        self.assertEqual({p.pins['3'] for p in f.parts if p.symbol.endswith('ADG5412FBRUZ') and p.unit==1},
                         {f'{i}_TIP' for i in range(1,6)})
        for i in range(1,6):
            r=self.role(f,'mix5:R_SUM_IN_'+str(i))
            self.assertEqual((len(r),r[0].value,r[0].pins['2']),(1,'100 kΩ','SUM_NODE'))
        self.assertEqual(self.role(f,'mix5:R_SUM_FEEDBACK')[0].value,'40 kΩ')
        self.assertEqual(self.role(f,'mix5:R_RESTORE_IN')[0].pins['1'],'LEVEL_BUFFERED')
        self.assertIn('SUM_NODE',f.sensitive_nets)
        self.assertEqual(sum('SUM_PRELEVEL' in p.pins.values() for p in f.parts if p.attributes.get('Role')=='clip_detector:A'),1)

    def test_mix4_cv_only_and_ota_termination(self):
        f=self.assert_bindings(mix4_vca)
        self.assertEqual([i.index for i in mix4_vca.specification()[1]],[83,84])
        self.assertEqual(len([p for p in f.parts if p.symbol.endswith('WQP518MA')]),6)
        level=[p for p in f.parts if p.attributes.get('PanelUid')=='C:${SHEETNAME}.LEVEL']
        self.assertEqual(len(level),1);self.assertTrue(level[0].symbol.endswith('PTV09A-4020F-B104'))
        self.assertEqual({p.pins['3'] for p in f.parts if p.symbol.endswith('ADG5412FBRUZ') and p.unit==1},
                         {f'{i}_TIP' for i in range(1,5)}|{'ATTEN_TIP'})
        self.assertEqual(self.role(f,'mix4_vca:R_SUM_FEEDBACK')[0].value,'50 kΩ')
        for i in range(1,5):
            self.assertEqual(self.role(f,'mix4_vca:R_SUM_IN_'+str(i))[0].pins['1'],f'{i}_GAIN')
        self.assertTrue(all('ATTEN' not in p.pins.values() and 'CV_DEPTH' not in p.pins.values()
                            for p in self.role(f,'mix4_vca:R_SUM_IN_1')+self.role(f,'mix4_vca:R_SUM_IN_2')+
                                     self.role(f,'mix4_vca:R_SUM_IN_3')+self.role(f,'mix4_vca:R_SUM_IN_4')))
        pins={}
        for p in f.parts:
            if p.symbol.endswith('LM13700M_NOPB'):pins.update(p.pins)
        self.assertEqual((pins['1'],pins['3'],pins['4'],pins['5']),('IABC1','OTA_SIGNAL','OTA_OFFSET','OTA_CURRENT'))
        self.assertEqual((pins['13'],pins['14'],pins['16']),('AGND','AGND','IABC2'))
        self.assertIsNone(pins['12'])
        self.assertEqual(self.role(f,'mix4_vca:R_IABC_LIMIT')[0].value,'10 kΩ')
        self.assertEqual(self.role(f,'mix4_vca:R_UNUSED_BIAS_OFF')[0].pins['2'],'-12V')
        self.assertIn('OTA_CURRENT',f.sensitive_nets)
        self.assertEqual(sum('SUM_PRELEVEL' in p.pins.values() for p in f.parts if p.attributes.get('Role')=='clip_detector:A'),1)

    def test_current_worksheet_counts_and_unqualified_maxima(self):
        reports=build()
        self.assertEqual(reports['mix5']['IC_packages_per_instance']['ADG5412FBRUZ'],5)
        self.assertEqual(reports['mix4_vca']['IC_packages_per_instance']['LM13700M_NOPB'],1)
        for report in reports.values():
            self.assertEqual(len(report['instances']),2)
            self.assertTrue(all(v is None for instance in report['instances']
                                for v in instance['guaranteed_maximum_mA'].values()))
            self.assertGreater(report['decoupling_nF_per_instance'],0)

    def test_mix4_model_calibration_and_original_failure_regression(self):
        deck=mixer4(5,5)
        self.assertIn('RPOT_TOP REF5 OFFSET_W 2300',deck)
        self.assertIn('RPOT_BOTTOM OFFSET_W REFN5 7700',deck)
        self.assertIn(f'RTRIM FB_TRIM OTA_CURRENT {TIA_TRIM_OHM:g}',deck)
        self.assertIn('RFEED OFFSET_W OTA_OFFSET 1meg',deck)
        self.assertIn('IABC P_12V CURRENT_SOURCE 0',mixer4(-5,5))
        self.assertIn('R_IABC_LIMIT CURRENT_SOURCE IABC1 10k',deck)
        baseline=[{'deck':'original-5-5v','command_V':5,'input_peak_each_V':5,
                   'output_extrema_V':{'out_max':6.897454,'out_min':-11.91074}}]
        # The original report must fail the same gate as new model data.
        failures=model_failures(baseline)
        self.assertIn('full-scale output exceeds ±10 V',failures[0])
        with self.assertRaises(SystemExit):exit_on_model_failures(failures)

if __name__=='__main__':unittest.main()
