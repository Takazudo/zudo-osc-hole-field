"""G07 truth table, actual packed logic, panel/rail/timing contracts."""
import hashlib,json,itertools,unittest
from collections import defaultdict
from design.spec.modules.envelope import family,specification,panel_bindings,INSTANCES
from design.spec.modules.envelope_logic import tick,captured_logic
from scripts.schgen.core import designator


class EnvelopeContract(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.f=family();cls.gates,cls.flops=captured_logic(cls.f.parts)
 def test_all_fixed_panel_uids_once(self):
  rows=panel_bindings();self.assertEqual(len(rows),108)
  parts=[p for p in self.f.parts if p.panel_refs];self.assertEqual(len(parts),18)
  self.assertEqual([i.index for i in specification()[1]],list(range(41,47)))
  for i in specification()[1]:
   self.assertEqual({designator(p,i) for p in parts},{r['ref'] for r in rows if r['instance']==i.name})
   self.assertEqual({p.attributes['PanelUid'].replace('${SHEETNAME}',i.name) for p in parts},{r['uid'] for r in rows if r['instance']==i.name})
 def test_entire_instrument_references_unique(self):
  from design.spec.instrument import specification as all_specs
  families,instances=all_specs();by_name={f.name:f for f in families};seen={}
  for i in instances:
   for p in by_name[i.family].parts:
    r=designator(p,i);identity=(i.name,p.key.rsplit('.',1)[0])
    self.assertTrue(r not in seen or seen[r]==identity,(r,seen.get(r),identity));seen[r]=identity
  self.assertEqual(seen['D1301'][0],'E1')
  self.assertEqual(seen['RV1306'][0],'E1')
 def test_truth_table_and_real_nand_capture(self):
  for state,mode,gate,prev,top,bottom,eoc in itertools.product(('idle','rise','sustain','fall'),('ASR','AR','LOOP'),*( (False,True) for _ in range(5))):
   start=gate and not prev or mode=='LOOP' and state=='idle' and not eoc
   if start:expected='rise'
   elif state=='idle':expected='idle'
   elif state=='rise':expected='fall' if mode=='ASR' and not gate else ('sustain' if mode=='ASR' else 'fall') if top else 'rise'
   elif state=='sustain':expected='sustain' if mode=='ASR' and gate else 'fall'
   else:expected='idle' if bottom else 'fall'
   self.assertEqual(tick(state,gate=gate,previous=prev,asr=mode=='ASR',loop=mode=='LOOP',top=top,bottom=bottom,eoc=eoc),expected)
   values={'AGND':False,'+5V':True,'RISE':state=='rise','HOLD':state=='sustain','FALL':state=='fall','GATE':gate,'GATE_PREV':prev,'ASR':mode=='ASR','LOOP':mode=='LOOP','TOP':top,'BOTTOM':bottom,'TOP_RAW':top,'BOTTOM_RAW':bottom,'EOC':eoc,'READY':True,'CURVED':False,'STAGE_FALL':False,'SIG_GATE':gate,'TRIG_ACTIVE':False}
   for k in list(values):values[k+'_N']=not values[k]
   pending=list(self.gates)
   while pending:
    ready=[x for x in pending if x[1] in values and x[2] in values];self.assertTrue(ready,pending)
    for x in ready:values[x[3]]=not(values[x[1]] and values[x[2]]);pending.remove(x)
   active=[state for state,key in [('rise','D_RISE'),('sustain','D_HOLD'),('fall','D_FALL')] if values[key]]
   self.assertEqual(active,[expected] if expected!='idle' else [])
 def test_sensitive_storage_never_reaches_panel_or_lamps(self):
  self.assertIn('ENV_STORAGE',self.f.sensitive_nets)
  self.assertEqual(set(self.f.global_nets),{'+12V','-12V','+5V','AGND'})
  contacts=[p for p in self.f.parts if 'ENV_STORAGE' in p.pins.values()]
  self.assertEqual(len(contacts),6)
  self.assertTrue(all(p.attributes['Island']=='ENV_CORE:${SHEETNAME}' and not p.panel_refs for p in contacts))
  leds=[p for p in self.f.parts if p.panel_refs and p.attributes['PanelUid'].startswith('L:')]
  self.assertEqual(len(leds),5);self.assertTrue(all(p.attributes['BoardRegion']==('stage_optical' if '.stage' in p.attributes['PanelUid'] else 'jack') for p in leds))
  self.assertTrue(all(p.pins['TN'] is None for p in self.f.parts if p.symbol.endswith('WQP518MA')))
 def test_physical_logic_domains_and_stage_masks(self):
  for p in self.f.parts:
   if any(p.symbol.endswith(n) for n in ('SN74HC00DR','SN74HC14DR','SN74HC74DR')) and '14' in p.pins:self.assertEqual(p.pins['14'],'+5V');self.assertEqual(p.pins['7'],'AGND')
   if p.symbol.endswith('LM393BIDR') and p.unit==3:self.assertEqual(p.pins,{'4':'AGND','8':'+12V'})
  masks=[p for p in self.f.parts if p.attributes.get('Role')=='stage_indicator:QMUTE']
  self.assertEqual({p.pins['1'] for p in masks},{'NOT_RISE','NOT_FALL'})
  names=[p.key for p in self.f.parts];self.assertEqual(len(names),len(set(names)))
 def test_values_and_output_scaling(self):
  roles={p.attributes.get('Role'):p for p in self.f.parts}
  self.assertEqual(roles['envelope:R_BIP_PLUS_TOP'].value,'64 kΩ')
  self.assertAlmostEqual((1+100/100+100/400)*80/(64+80),1.25)
  self.assertEqual(roles['envelope:R_BIP_REF'].value,'100 kΩ')
  self.assertEqual(roles['envelope:R_FLOOR_TOP'].value,'79 kΩ')
  self.assertEqual(roles['envelope:R_FLOOR_BOTTOM'].value,'22 kΩ')
  self.assertAlmostEqual((5*22/101*101-5)/100-1,.05)
  self.assertAlmostEqual((9*100+5)/101-1,804/101)
  for k in ('RISE','FALL'):
   self.assertEqual(roles['envelope:R_'+k+'_BIAS_LIMIT'].value,'22 kΩ')
  self.assertEqual(roles['envelope:TIMING_CAP'].value,'100 nF C0G')
  self.assertEqual(roles['envelope:TIMING_CAP'].attributes['MPN'],'1206CG104J500NT')

 def test_model_report_and_current_are_scoped(self):
  from design.spec.modules.envelope import ROOT
  from design.spec.modules.build_envelope_current import build
  report=json.loads((ROOT/'design/reports/spice/envelope.json').read_text())
  self.assertEqual(len(report['runs']),8)
  for path,digest in report['source_sha256'].items():self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),digest)
  current=build();self.assertEqual(len(current['instances']),6)
  self.assertTrue(all(v is None for row in current['instances'] for v in row['guaranteed_maximum_mA'].values()))

if __name__=='__main__':unittest.main()
