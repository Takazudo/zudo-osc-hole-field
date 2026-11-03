"""No-active-function-loss and accounting adversarial controls; source only."""
from pathlib import Path
from dataclasses import replace
from functools import lru_cache
import copy,hashlib,importlib.util,json,sys,unittest
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
def load(name,file):
 s=importlib.util.spec_from_file_location(name,HERE/file);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
p=load('stage54_proposal','proposal.py');a=load('stage54_accounting','accounting.py');n=load('stage54_native','native.py')
@lru_cache(None)
def fixture():return p.specification()
class CleanupTests(unittest.TestCase):
 def altered(self,fn):
  fs,ins=fixture();f=next(f for f in fs if f.name=='sample_hold');new=fn(f)
  return tuple(new if x.name==f.name else x for x in fs),ins
 def target(self,f):return next(x for x in f.parts if p.designator(x,next(i for i in fixture()[1] if i.name=='H1'))=='U116' and x.unit==1)
 def test_exact_scope_and_survivors(self):
  fs,ins=fixture();after,r=p.prepare(fs,ins);self.assertEqual(set(r['removed_refs']),set(p.TARGET)|p.CAPS)
  self.assertEqual(len(r['removed_private_nets']),48);self.assertEqual(r['before_pin_count']-r['retained_pin_count'],216)
  old=next(f for f in fs if f.name=='sample_hold');new=next(f for f in after if f.name=='sample_hold')
  self.assertEqual(new.parts,tuple(x for x in old.parts if x.key not in r['removed_family_part_keys']))
 def test_active_input_rejects(self):
  def mutate(f):
   x=self.target(f);return replace(f,parts=tuple(replace(q,pins={**q.pins,'3':'IN_BUFFERED'}) if q.key==x.key else q for q in f.parts))
  with self.assertRaisesRegex(ValueError,'idle follower'):p.prepare(*self.altered(mutate))
 def test_external_feedback_user_rejects(self):
  def mutate(f):
   x=self.target(f);r=next(q for q in f.parts if q.prefix=='R');extra=replace(r,key='EXTRA',prefix='RX',ordinal=98,pins={'1':x.pins['1'],'2':'AGND'})
   return replace(f,parts=f.parts+(extra,))
  with self.assertRaisesRegex(ValueError,'external follower-net user'):p.prepare(*self.altered(mutate))
 def test_missing_channel_rejects(self):
  def mutate(f):return replace(f,parts=tuple(q for q in f.parts if q.key!=self.target(f).key))
  with self.assertRaisesRegex(ValueError,'complete package'):p.prepare(*self.altered(mutate))
 def test_role_rejects(self):
  def mutate(f):
   x=self.target(f);return replace(f,parts=tuple(replace(q,attributes={**q.attributes,'LogicalCellKey':'ACTIVE'}) if q.key==x.key else q for q in f.parts))
  with self.assertRaisesRegex(ValueError,'active role'):p.prepare(*self.altered(mutate))
 def test_wrong_bypass_owner_rejects(self):
  def mutate(f):
   stem=self.target(f).key.rsplit('.',1)[0];cap=next(x for x in f.parts if x.attributes.get('Decouples')==stem)
   return replace(f,parts=tuple(replace(q,attributes={**q.attributes,'Decouples':'WRONG'}) if q.key==cap.key else q for q in f.parts))
  with self.assertRaisesRegex(ValueError,'bypass ownership'):p.prepare(*self.altered(mutate))
 def test_wrong_bypass_value_rejects(self):
  def mutate(f):
   stem=self.target(f).key.rsplit('.',1)[0];cap=next(x for x in f.parts if x.attributes.get('Decouples')==stem)
   return replace(f,parts=tuple(replace(q,value='1 uF') if q.key==cap.key else q for q in f.parts))
  with self.assertRaisesRegex(ValueError,'exact bypass'):p.prepare(*self.altered(mutate))
 def test_native_projection_and_negative_controls(self):
  old={('IDLE','1'):'private',('ACTIVE','1'):'signal'};new={('ACTIVE','1'):'signal'}
  self.assertTrue(n.compare(old,new,old,new,{'IDLE'}))
  with self.assertRaisesRegex(ValueError,'native retained'):n.compare(old,{},old,{}, {'IDLE'})
  with self.assertRaisesRegex(ValueError,'candidate native'):n.compare(old,{('ACTIVE','1'):'wrong'},old,new,{'IDLE'})
 def test_proposal_replay(self):p.run(None,True)
class AccountingTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.result,cls.sh=a.build()
 def test_accounting_replays(self):self.assertEqual(self.result,json.loads((HERE/'accounting.json').read_text()));self.assertEqual(self.sh,json.loads((HERE/'sample-hold-proposed.json').read_text()))
 def test_iq_only(self):
  self.assertEqual(self.result['removed_Iq_mA']['planning_Iq'],{'+12V':42,'-12V':42,'+5V':0})
  self.assertEqual(self.result['removed_counts_by_mpn'],{'OPA4197IPWR':6,'OPA4196IDR':6})
  self.assertEqual(self.result['physical_IC_count_proposed'],638)
 def test_clip_typical_not_planning(self):
  c=self.result['clip_comparator_accounting'];self.assertEqual(len(c['packages']),20);self.assertEqual(c['negative_typical_correction_mA'],10);self.assertEqual(c['planning_correction_mA'],0)
 def test_reserves_not_removed_or_added_twice(self):
  self.assertEqual(self.result['coarse_reserve_mA_per_analog_rail'],233);self.assertEqual(self.result['reserve_rebate_booked_mA'],0)
  self.assertEqual(len(self.result['verified_nominal_trim_branches']),26);self.assertTrue(all(x['included_in_reserve_not_extra'] for x in self.result['verified_nominal_trim_branches']))
 def test_complete_ota_feed_inventory(self):
  rows=self.result['OTA_bias_overlap_branches'];self.assertEqual(len(rows),26)
  self.assertEqual(a.Counter(x['instance'] for x in rows),a.Counter({**{f'F{i}':4 for i in range(1,4)},**{f'E{i}':2 for i in range(1,7)},'M4A':1,'M4B':1}))
  self.assertTrue(all(any(n and 'IABC' in n for n in x['pins'].values()) for x in rows))
  off=self.result['OTA_unused_bias_off_branches'];self.assertEqual({x['ref'] for x in off},{'R8379','R8479'});self.assertTrue(all('UNUSED_BIAS_OFF' in x['key'] for x in off))
 def test_unknowns_remain_unknown(self):
  for k in ('guaranteed_whole_instrument_maximum_mA','complete_typical_mA','measured_source_capacity_mA'):self.assertEqual(self.result[k],{r:None for r in a.RAILS})
  self.assertTrue(self.result['unknown_reasons_preserved']);self.assertTrue(self.result['source_not_proven_preserved'])
 def test_source_requirements_not_reduced(self):self.assertEqual(self.result['source_minimum_continuous_mA_UNCHANGED'],{'+12V':1700,'-12V':1600,'+5V':300});self.assertEqual(self.result['source_minimum_transient_mA_UNCHANGED'],{'+12V':2000,'-12V':1900,'+5V':400})
 def test_simultaneous_iq_power_not_half(self):self.assertEqual(self.result['simultaneity']['Iq_allowance_power_reduction_at_nominal_plusminus12_W'],2*12*.042);self.assertTrue(self.result['simultaneity']['aggregate_rail_maxima_are_not_simultaneous_power'])
 def test_optional_refinement_not_booked(self):
  x=self.result;self.assertEqual(x['EXT_normal_with_allowances_after_Iq_mA']['+12V'],1492.819166);self.assertEqual(x['EXT_normal_with_allowances_after_Iq_mA']['-12V'],1393.56866);self.assertEqual(x['grouped_input_protection_savings_booked_mA'],0)
class EvidenceTests(unittest.TestCase):
 def test_native_audit(self):
  x=json.loads((HERE/'native-audit.json').read_text());self.assertTrue(x['all_surviving_native_pin_nets_unchanged']);self.assertEqual(x['removed_pin_count'],216);self.assertEqual(len(x['removed_native_pin_nets']),36)
  for name in ('canonical','candidate'):
   r=json.loads((HERE/'evidence'/f'{name}-native.execution.json').read_text());self.assertEqual(r['returncode'],0);self.assertIn(r['output_sha256'],x['export_sha256'].values())
 def test_source_bindings(self):
  d=json.loads((HERE/'sources.json').read_text())
  for path,digest in d['source_sha256'].items():self.assertEqual(p.sha(p.ROOT/path),digest,path)
  for row in d['primary_Iq_sources']:self.assertEqual(p.sha(p.ROOT/row['path']),row['sha256'])
 def test_review_bindings(self):
  for path,digest in json.loads((HERE/'review-bindings.json').read_text())['sha256'].items():self.assertEqual(p.sha(p.ROOT/path),digest,path)
if __name__=='__main__':unittest.main()
