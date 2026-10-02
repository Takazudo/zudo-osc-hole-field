"""Pilot module source, binding, and storage-node contract tests."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from design.spec.modules.sample_hold import family,panel_bindings,specification,ROOT
from design.spec.modules import build_sample_hold_current as current_module
from design.spec.modules.build_sample_hold_current import build as current_report
from scripts.schgen.core import designator

class SampleHoldContract(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.family=family();cls.instances=specification()[1]
  cls.parts=cls.family.parts
 def test_two_instances_share_source_but_have_distinct_panel_bindings(self):
  rows=panel_bindings()
  self.assertEqual(len(rows),16)
  self.assertEqual(len({r['uid'] for r in rows}),16)
  self.assertEqual((self.instances[0].name,self.instances[1].name),('H1','H2'))
  panel=[p for p in self.parts if p.panel_refs]
  self.assertEqual(len(panel),8)
  for instance in self.instances:
   self.assertEqual({designator(p,instance) for p in panel},{r['ref'] for r in rows if r['instance']==instance.name})
  self.assertEqual(len({(i.name,p.attributes['PanelUid'].replace('${SHEETNAME}',i.name)) for i in self.instances for p in panel}),16)
 def test_storage_nodes_are_distinct_sensitive_and_not_global(self):
  f=self.family
  self.assertIn('HOLD_CAP',f.sensitive_nets)
  self.assertIn('SLEW_STORAGE',f.sensitive_nets)
  self.assertNotIn('RAW_HELD',f.global_nets)
  hold=next(p for p in self.parts if p.key=='LF398.1')
  self.assertEqual(hold.pins['8'],'HOLD_CAP')
  self.assertEqual(hold.pins['7'],'RAW_HELD')
  self.assertNotEqual(hold.pins['8'],hold.pins['7'])
  lag=next(p for p in self.parts if p.key.endswith('__RV.0'))
  self.assertEqual(lag.pins['2'],'SLEW_STORAGE')
  self.assertEqual(lag.pins['3'],'SLEW_STORAGE')
  self.assertEqual(lag.attributes['Island'],'C:${SHEETNAME}.SLEW')
 def test_one_shot_positive_edge_and_lf398_sample_polarity(self):
  shot=next(p for p in self.parts if p.key=='ONE_SHOT.1')
  self.assertEqual((shot.pins['1'],shot.pins['2'],shot.pins['3']),('AGND','TRIGGER_OR','+5V'))
  self.assertEqual((shot.pins['4'],shot.pins['14'],shot.pins['15']),('SAMPLE_PULSE','TIMING_C','TIMING_RCX'))
  lf=next(p for p in self.parts if p.key=='LF398.1')
  self.assertEqual((lf.pins['10'],lf.pins['11']),('AGND','SAMPLE_PULSE'))
  self.assertAlmostEqual(.7*10000*10e-9,70e-6)
 def test_hold_alternative_is_dnp_and_output_is_only_slewed_jack(self):
  alt=next(p for p in self.parts if p.key=='C_HOLD_ALT')
  self.assertTrue(alt.dnp)
  self.assertEqual(alt.attributes['MPN'],'')
  self.assertEqual((alt.pins['1'],alt.pins['2']),('HOLD_CAP','AGND'))
  jacks=[p for p in self.parts if p.symbol.endswith('WQP518MA')]
  self.assertEqual(len(jacks),3)
  self.assertEqual(next(p for p in jacks if p.key=='J_OUT').pins['T'],'OUT_TIP')
  self.assertFalse(any(p.pins.get('T')=='RAW_HELD' for p in jacks))
 def test_current_totals_are_partial_for_each_instance(self):
  report=current_report();self.assertEqual(len(report['instances']),2)
  self.assertEqual(report['instances'][0]['known_typical_mA'],report['instances'][1]['known_typical_mA'])
  for row in report['instances']:
   self.assertIsNone(row['complete_total_maximum_mA'])
   self.assertIn('NOT ESTABLISHED',row['maximum_status_by_rail']['+5V'])
 def test_committed_current_report_matches_current_capture(self):
  current_module.main(check=True)
 def test_obsolete_led_population_is_rejected_by_report_check(self):
  report=current_report()
  selected={p.symbol.split(':')[-1] for p in self.parts
            if p.attributes.get('PanelUid','').startswith('L:')}
  self.assertEqual(len(selected),1)
  symbol=selected.pop()
  self.assertNotEqual(symbol,'0603Whitelight_C2290')
  with tempfile.TemporaryDirectory() as directory:
   out=Path(directory)/'sample_hold.json'
   with patch.object(current_module,'OUT',out):
    out.write_text(json.dumps(report,indent=2)+'\n')
    current_module.main(check=True)
    count=report['fitted_package_count_per_instance'].pop(symbol)
    self.assertEqual(count,3)
    report['fitted_package_count_per_instance']['0603Whitelight_C2290']=count
    out.write_text(json.dumps(report,indent=2)+'\n')
    with self.assertRaisesRegex(SystemExit,'current report drift'):
     current_module.main(check=True)
 def test_local_decoupling_and_bulk_reservations(self):
  caps=[p for p in self.parts if p.key.startswith('C_DEC_')]
  bulk=[p for p in self.parts if p.key.startswith('C_BULK_')]
  self.assertEqual(len(caps),33)
  self.assertTrue(all(not p.dnp and p.value=='100 nF' and p.attributes.get('Decouples') and p.attributes['BoardRegion'] == next(q.attributes['BoardRegion'] for q in self.parts if q.key.rsplit('.',1)[0] == p.attributes['Decouples']) for p in caps))
  self.assertEqual(len(bulk),3)
  self.assertTrue(all(p.dnp and p.attributes['Island']=='BULK_TBD' for p in bulk))
 def test_nonpanel_diodes_cannot_collide_with_locked_panel_references(self):
  internal=[p for p in self.parts if p.prefix=='DH']
  panel_leds=[p for p in self.parts if p.panel_refs and p.prefix=='D']
  self.assertTrue(internal)
  self.assertTrue(panel_leds)
  self.assertFalse([p for p in self.parts if p.prefix=='D' and not p.panel_refs])
  locked_refs={row['ref'] for row in json.loads((ROOT/'design/grid/placements.lock.json').read_text())['placements']}
  conflicts=[]
  for instance in self.instances:
   for part in self.parts:
    if not part.panel_refs:
     ref=designator(part,instance)
     if ref in locked_refs:conflicts.append((ref,instance.name,part.key))
  self.assertEqual(conflicts,[])
if __name__=='__main__':unittest.main()
