"""Fixed panel, feed-forward reflection graph, coupling and evidence regressions."""
import hashlib,json,unittest
from design.spec.modules.wavefolder import ROOT,family,specification,panel_bindings,INSTANCES
from design.spec.modules.run_oscillator_spice import MAPS
from design.spec.modules.build_wavefolder_current import build
from scripts.schgen.core import designator


class WavefolderContract(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.f=family();cls.roles={p.attributes.get('Role'):p for p in cls.f.parts}
 def test_fixed_panel_order_and_complete_binding(self):
  rows=panel_bindings();self.assertEqual(len(rows),22)
  self.assertEqual([i.name for i in specification()[1]],['W2','W1']);self.assertEqual([i.index for i in specification()[1]],[51,52])
  panels=[p for p in self.f.parts if p.panel_refs];self.assertEqual(len(panels),11)
  for i in specification()[1]:
   self.assertEqual({designator(p,i) for p in panels},{r['ref'] for r in rows if r['instance']==i.name})
   self.assertEqual({p.attributes['PanelUid'].replace('${SHEETNAME}',i.name) for p in panels},{r['uid'] for r in rows if r['instance']==i.name})
  self.assertLess(next(r['x_mm'] for r in rows if r['uid']=='J:W2.IN'),next(r['x_mm'] for r in rows if r['uid']=='J:W1.IN'))
 def test_assembled_references_unique(self):
  from design.spec.instrument import specification as all_specs
  fs,ins=all_specs();fs={f.name:f for f in fs};seen={}
  for i in ins:
   for p in fs[i.family].parts:
    ref=designator(p,i);key=(i.name,p.key.rsplit('.',1)[0])
    self.assertTrue(ref not in seen or seen[ref]==key,(ref,key));seen[ref]=key
 def test_four_feed_forward_reflection_cells(self):
  previous='FOLDER_DRIVE'
  for i in range(1,5):
   key=f'F{i}';amp=self.roles['wavefolder:'+key];out,minus,plus=MAPS[amp.unit]
   self.assertEqual(amp.pins,{out:key+'_OUT',minus:key+'_SUM',plus:key+'_CLIP'})
   for suffix,pair,value in [('CLIP_FEED',(previous,key+'_CLIP'),'10 kΩ'),('INPUT',(previous,key+'_SUM'),'100 kΩ'),('FEEDBACK',(key+'_OUT',key+'_SUM'),'100 kΩ')]:
    p=self.roles['wavefolder:R_'+key+'_'+suffix];self.assertEqual((p.pins['1'],p.pins['2']),pair);self.assertEqual(p.value,value)
   self.assertEqual(self.roles['wavefolder:'+key+'_D_POS'].pins,{'1':'AGND','2':key+'_CLIP'})
   self.assertEqual(self.roles['wavefolder:'+key+'_D_NEG'].pins,{'1':key+'_CLIP','2':'AGND'})
   previous=key+'_OUT'
 def test_protected_inputs_and_only_three_input_indicators(self):
  isolators=[p for p in self.f.parts if p.symbol.endswith('ADG5412FBRUZ') and p.unit==1]
  self.assertEqual({p.pins['3'] for p in isolators},{x+'_TIP' for x in ('IN','FOLD','BIAS')})
  leds=[p for p in self.f.parts if p.panel_refs and p.attributes['PanelUid'].startswith('L:')]
  self.assertEqual(len(leds),3);self.assertTrue(all(p.attributes['Island']=='FOLDER_LEDS:${SHEETNAME}' for p in leds))
  self.assertTrue(all(p.pins['TN'] is None for p in self.f.parts if p.symbol.endswith('WQP518MA')))
 def test_ac_storage_and_remote_controls(self):
  caps=[p for p in self.f.parts if p.attributes.get('Role','').startswith('wavefolder:AC_BANK')]
  self.assertEqual(len(caps),10)
  self.assertTrue(all(p.value=='100 nF C0G' and p.pins=={'1':'PRE_AC','2':'AC_NODE'} for p in caps))
  self.assertIn('AC_NODE',self.f.sensitive_nets)
  self.assertTrue(all(not(set(self.f.sensitive_nets)&set(p.pins.values())) for p in self.f.parts if p.panel_refs))
  self.assertEqual(set(self.f.global_nets),{'+12V','-12V','+5V','AGND'})
  self.assertEqual(self.roles['wavefolder:R_DRIVE_BIAS_BUFFER'].value,'1 MΩ')
  self.assertEqual(self.roles['wavefolder:R_DRIVE_BIAS_MANUAL'].value,'1 MΩ')
  self.assertEqual(self.roles['wavefolder:R_BIAS_SENSE'].value,'12.4 kΩ')
  self.assertLess(-10.5+5/12400*22000,-1.0)
 def test_model_and_plot_receipts_current(self):
  report=json.loads((ROOT/'design/reports/spice/wavefolder.json').read_text())
  self.assertEqual(len(report['dc_runs']),16)
  for path,digest in report['source_sha256'].items():self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),digest)
  plots=json.loads((ROOT/'design/reports/spice/wavefolder-plots.json').read_text())
  self.assertEqual(hashlib.sha256((ROOT/'design/reports/spice/wavefolder.json').read_bytes()).hexdigest(),plots['report_sha256'])
  for path,digest in plots['images'].items():self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),digest)
 def test_current_has_no_fabricated_maximum(self):
  report=build();self.assertEqual(len(report['instances']),2);self.assertEqual(report['IC_packages_per_instance']['LM13700M_NOPB'],1)
  self.assertTrue(all(v is None for row in report['instances'] for v in row['guaranteed_maximum_mA'].values()))
  self.assertEqual(report['audio_coupling_nominal_nF_per_instance'],1000)

if __name__=='__main__':unittest.main()
