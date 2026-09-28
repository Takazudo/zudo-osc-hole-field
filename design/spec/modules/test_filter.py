"""Filter binding, topology, isolation and retained-model regression checks."""
from collections import defaultdict
import hashlib,json,unittest
from design.spec.modules.filter import ROOT,family,specification,panel_bindings,INSTANCES,SENSITIVE
from design.spec.modules.build_filter_current import build
from scripts.schgen.core import designator


class FilterContract(unittest.TestCase):
    @classmethod
    def setUpClass(cls):cls.f=family();cls.parts=cls.f.parts

    def role(self,name):return [p for p in self.parts if p.attributes.get('Role')==name]

    def test_all_54_fixed_panel_features_once(self):
        rows=panel_bindings();panel=[p for p in self.parts if p.panel_refs]
        self.assertEqual(len(rows),54);self.assertEqual(len(panel),18)
        self.assertEqual([i.index for i in specification()[1]],[21,22,23])
        for i in specification()[1]:
            self.assertEqual({designator(p,i) for p in panel},{r['ref'] for r in rows if r['instance']==i.name})
            self.assertEqual({p.attributes['PanelUid'].replace('${SHEETNAME}',i.name) for p in panel},{r['uid'] for r in rows if r['instance']==i.name})

    def test_four_otas_and_local_integrator_nodes(self):
        packages=defaultdict(dict)
        for p in self.parts:
            if p.symbol.endswith('LM13700M_NOPB'):packages[p.key.rsplit('.',1)[0]].update(p.pins)
        self.assertEqual(len(packages),2)
        first=next(v for k,v in packages.items() if 'INTEGRATORS' in k)
        self.assertEqual((first['5'],first['12']),('BP_INT','LP_INT'))
        self.assertEqual((first['1'],first['16']),('BP_IABC','LP_IABC'))
        for node in ('BP_INT','LP_INT'):
            self.assertIn(node,self.f.sensitive_nets);self.assertNotIn(node,self.f.global_nets)
            connected=[p for p in self.parts if node in p.pins.values()]
            self.assertTrue(all(p.attributes['Island']=='FILTER_CORE:${SHEETNAME}' for p in connected))
        self.assertTrue(all(not(set(SENSITIVE)&set(p.pins.values())) for p in self.parts if p.panel_refs))

    def test_G06_dry_gain_does_not_feed_filter_loop(self):
        group=defaultdict(dict)
        for p in self.parts:
            if p.symbol.endswith('LM13700M_NOPB'):group[p.key.rsplit('.',1)[0]].update(p.pins)
        pair=next(v for k,v in group.items() if 'GAIN_RESONANCE' in k)
        self.assertEqual(pair['16'],'DRY_IABC');self.assertEqual(pair['13'],'DRY_OTA_SIGNAL')
        dryatten=self.role('filter:R_DRY_ATTEN_TOP')[0]
        self.assertEqual(dryatten.pins['1'],'IN_BUFFER')
        for p in self.role('filter:R_HP_BP')+self.role('filter:R_HP_LP')+self.role('filter:R_HP_RES'):
            self.assertFalse(any(v and ('GAIN' in v or 'DRY' in v) for v in p.pins.values()))
        self.assertEqual(self.role('filter:R_HP_BP')[0].value,'50 kΩ')
        self.assertEqual(self.role('filter:R_HP_LP')[0].value,'100 kΩ')

    def test_input_protection_and_only_four_input_indicators(self):
        jacks=[p for p in self.parts if p.symbol.endswith('WQP518MA')];self.assertEqual(len(jacks),8)
        self.assertTrue(all(p.pins['TN'] is None for p in jacks))
        sources=[p.pins['3'] for p in self.parts if p.symbol.endswith('ADG5412FBRUZ') and p.unit==1]
        self.assertEqual(set(sources),{k+'_TIP' for k in ('IN','FREQ','RES','GAIN')})
        leds=[p for p in self.parts if p.panel_refs and p.attributes['PanelUid'].startswith('L:')]
        self.assertEqual(len(leds),4)
        self.assertTrue(all(p.attributes['Island']=='FILTER_LEDS:${SHEETNAME}' for p in leds))
        self.assertEqual(set(self.f.global_nets),{'+12V','-12V','+5V','AGND'})

    def test_current_limits_and_soft_limiter_are_populated(self):
        for role in ('BP','LP','RES','DRY'):
            key='filter:R_'+role+('_BIAS_LIMIT' if role in ('BP','LP') else '_IABC_LIMIT')
            self.assertEqual(self.role(key)[0].value,'22 kΩ')
        self.assertEqual(len([p for p in self.parts if p.attributes.get('Role','').startswith('filter:RES_LIMIT_')]),16)
        self.assertEqual(len([p for p in self.parts if p.attributes.get('Role','').endswith('_REVERSE_BE')]),2)
        # Dry current must leave collector compliance across the 22k limiter.
        self.assertEqual(self.role('filter:R_DRY_SENSE')[0].value,'12.4 kΩ')
        self.assertLess(-10.5+(5/12400)*22000,-1.0)
        self.assertEqual(self.role('filter:R_DRY_GAIN')[0].value,'68.1 kΩ')
        names={p.key for p in self.parts};self.assertEqual(len(names),len(self.parts))
        packages=defaultdict(set)
        for p in self.parts:
            if p.symbol.endswith(('OPA4196IDR','OPA4197IPWR')):packages[p.ordinal].add(p.unit)
        self.assertTrue(all(units=={1,2,3,4,5} for units in packages.values()))

    def test_current_and_vendor_source_are_honest(self):
        report=build();self.assertEqual(len(report['instances']),3)
        self.assertEqual(report['IC_packages_per_instance']['LM13700M_NOPB'],2)
        self.assertTrue(all(v is None for row in report['instances'] for v in row['guaranteed_maximum_mA'].values()))
        receipt=json.loads((ROOT/'design/spec/modules/spice/filter-model/source-receipt.json').read_text())
        self.assertEqual(hashlib.sha256((ROOT/receipt['retained_file']).read_bytes()).hexdigest(),receipt['sha256'])
        self.assertEqual(receipt['authority'],'MANUFACTURER_PRIMARY')

if __name__=='__main__':unittest.main()
