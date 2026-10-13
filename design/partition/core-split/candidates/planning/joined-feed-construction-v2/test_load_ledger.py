import copy,gzip,json,math,sys,unittest
from collections import defaultdict
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
import load_ledger as ll

TYP='normal-typ-v1'
class LoadLedger(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.L=ll.build();cls.R=cls.L['records']
 def dev(self,sc=TYP):
  d=defaultdict(dict)
  for r in self.R:
   if r['scenario_id']==sc and r['current_A']:d[(r['board'],r['ref'])][r['net']]=d[(r['board'],r['ref'])].get(r['net'],0)+r['current_A']
  return d
 def test_device_kcl_zero(self):
  for sc in ll.SCENARIOS:
   for k,v in self.dev(sc).items():self.assertAlmostEqual(math.fsum(v.values()),0,places=15,msg=k)
   self.assertEqual(self.L['kcl'][sc]['max_abs_device_residual_A'],0)
   self.assertEqual(self.L['kcl'][sc]['global_residual_A'],0)
 def test_split_rail_opamp_has_zero_agnd(self):
  ops={(r['board'],r['ref']) for r in self.R if r['physical_owner'] and r['physical_owner'].get('symbol','').startswith('OPA4')}
  self.assertEqual(len(ops),164)
  for k,v in self.dev().items():
   if k in ops:self.assertEqual(set(v),{'+12V','-12V'});self.assertGreater(v['+12V'],0);self.assertEqual(v['-12V'],-v['+12V'])
  self.assertFalse([r for r in self.R if (r['board'],r['ref']) in ops and r['net']=='AGND' and r['current_A']])
 def test_logic_agnd_is_minus_5v_draw(self):
  n=0
  for k,v in self.dev().items():
   if '+5V' in v:n+=1;self.assertEqual(set(v),{'+5V','AGND'});self.assertGreater(v['+5V'],0);self.assertEqual(v['AGND'],-v['+5V'])
  self.assertEqual(n,67)
  for b in ll.BOARDS:
   s=self.L['kcl'][TYP]['board_net_sum_A'][b];self.assertAlmostEqual(s['AGND'],-s['+5V'],places=15);self.assertEqual(self.L['kcl'][TYP]['agnd_injection_A'][b],s['AGND'])
 def test_no_row_divides_a_planning_total(self):
  inp=ll.Inputs();inv=inp.json(ll.INVENTORY)
  for r in self.R:
   if not r['current_A']:continue
   self.assertTrue(r['source'].startswith(ll.SKILLS) and '/facts.json#fact-' in r['source'])
   self.assertIn(r['provenance'],('supported_pin_current','conditional_assumption'))
   v,_=ll.supply_value(inp,inv,r['physical_owner']['symbol'],r['scenario_id']);self.assertEqual(abs(r['current_A']),v)
  self.assertFalse([a for a in self.L['allowances'] if a['pad_id'] is not None])
  self.assertFalse([r for r in self.R if r['provenance'] in ('unmapped_allowance','external_interface_demand')])
 def test_reconciliation_counts_once_and_detects_duplicates(self):
  self.assertEqual(self.L['double_count_issues'],[])
  for x in self.L['reconciliation']['per_board_net']:
   self.assertTrue(x['identity_holds']);self.assertFalse(x['over_allocated'])
   # External interface demand (EL ceiling) is not assumed to lie inside the board planning total.
   self.assertAlmostEqual(x['supported_pin_mA']+x['conditional_mA']+x['unmapped_remainder_mA'],x['planning_mA'],places=9)
   self.assertEqual(bool(x['external_interface_mA']),x['external_interface_relation'] is not None)
  m=copy.deepcopy(self.L);m['records'].append(dict(next(r for r in m['records'] if r['current_A'])))
  self.assertTrue(any('duplicate pad record' in i for i in ll.double_counts(m)))
  m=copy.deepcopy(self.L);m['allowances'].append(dict(m['allowances'][0]))
  self.assertTrue(any('duplicate allowances' in i for i in ll.double_counts(m)))
  m=copy.deepcopy(self.L);g=m['interface_demands'][0];r=next(r for r in m['records'] if r['current_A'] and r['scenario_id']==g['scenario_id']);g['pad_ids'].append(r['pad_id'])
  self.assertTrue(any('interface group' in i for i in ll.double_counts(m)))
 def test_every_rail_pad_exactly_once(self):
  ids=set()
  for b in ll.BOARDS:ids|={p['id'] for p in json.loads(gzip.decompress((ll.ROOT/ll.EV/f'e16/{b}-t2-port-graph.json.gz').read_bytes()))['physical_ports']}
  self.assertEqual(len(ids),3849);self.assertEqual(sum(i.startswith('CS247-') for i in ids),12)
  for sc in ll.SCENARIOS:
   got=[r['pad_id'] for r in self.R if r['scenario_id']==sc];self.assertEqual(len(got),3849);self.assertEqual(set(got),ids)
   self.assertTrue(self.L['census'][sc]['every_graph_pad_exactly_once'])
 def test_passive_dnp_zero_and_supports_null(self):
  for r in self.R:
   if r['mapping_status'] in ('passive_zero_dc','dnp_zero_dc','test_point_zero_dc'):self.assertEqual(r['current_A'],0.0)
   if r['pad_class']=='network_support' or r['mapping_status'].startswith('unmapped') or r['mapping_status'].startswith('interface'):self.assertIsNone(r['current_A'])
  self.assertEqual(sum(r['mapping_status']=='dnp_zero_dc' for r in self.R if r['scenario_id']==TYP),14)
 def test_scenario_nonzero_on_three_rails(self):
  self.assertEqual(self.L['status'],'CONDITIONAL_LOAD_SCENARIO');self.assertIs(self.L['full_scope_budget_acceptance'],False)
  for b in ll.BOARDS:
   s=self.L['kcl'][TYP]['board_net_sum_A'][b];self.assertGreater(s['+12V'],0);self.assertLess(s['-12V'],0);self.assertGreater(s['+5V'],0)
 def test_typical_25c_maximum_and_full_temperature_are_distinct(self):
  inp=ll.Inputs();inv=inp.json(ll.INVENTORY)
  expected={'OPA4196IDR':(.00056,.0008,.001),'OPA4197IPWR':(.004,.0052,.006)}
  for symbol,values in expected.items():
   for scenario,value in zip(('normal-typ-v1','normal-max-25c-v1','normal-max-v1'),values):
    got,meta=ll.supply_value(inp,inv,symbol,scenario);self.assertEqual(got,value)
    self.assertEqual(meta['evidence']['verdict'],'PASS - primary-source confirmed')
    self.assertEqual(meta['evidence']['source_authority'],'MANUFACTURER_PRIMARY')
  self.assertEqual(ll.SCENARIO_CONDITIONS['normal-max-25c-v1']['opa_temperature_C'],25)
  self.assertEqual(ll.SCENARIO_CONDITIONS['normal-max-v1']['opa_temperature_C'],[-40,125])
  for scenario in ll.SCENARIOS:
   _,meta=ll.supply_value(inp,inv,'SN74HC14DR',scenario)
   self.assertEqual(meta['provenance'],'conditional_assumption')
   self.assertIsNone(meta['evidence']['value_key'])
   self.assertIn('6 V',meta['evidence']['application_condition_status'])
 def test_signed_provenance_retains_exact_identity_source_and_pin_map(self):
  for row in self.R:
   if row['provenance'] not in ('supported_pin_current','conditional_assumption'):continue
   evidence=row['supply_evidence']
   self.assertEqual(evidence['manufacturer'],'Texas Instruments')
   self.assertEqual(evidence['mpn'],row['physical_owner']['symbol'])
   self.assertEqual(evidence['supply_pin_map'][row['pad']],row['net'])
   self.assertEqual(evidence['sign'],1 if row['net'] in ('+12V','+5V') else -1)
   self.assertEqual(evidence['fact_provenance'],'PRIMARY-SPEC')
   self.assertEqual(evidence['source_availability'],'AVAILABLE')
   self.assertNotEqual(evidence['source_sha256'],'0'*64)
   self.assertTrue(evidence['fact_locator']);self.assertTrue(evidence['fact_conditions'])
 def test_source_identity_authority_and_numeric_fail_closed(self):
  inv=ll.Inputs().json(ll.INVENTORY)
  class Changed(ll.Inputs):
   def __init__(self,field):super().__init__();self.field=field
   def json(self,path):
    data=super().json(path)
    if 'component-ti-opa4196idr/' not in path:return data
    if self.field=='authority' and path.endswith('/sources.json'):data['sources'][0]['authority_class']='DISTRIBUTOR_IDENTITY'
    if self.field=='availability' and path.endswith('/sources.json'):data['sources'][0]['availability']='SOURCE UNAVAILABLE'
    if self.field=='hash' and path.endswith('/sources.json'):data['sources'][0]['sha256']='0'*64
    if self.field=='identity' and path.endswith('/manifest.json'):data['records'][0]['manufacturer']='Wrong vendor'
    if self.field=='numeric' and path.endswith('/facts.json'):next(f for f in data['facts'] if f['fact_id']=='fact-op-audio-quiescent-current')['value']['typical_at_25C']=float('nan')
    if self.field=='pin' and path.endswith('/pin-map.json'):next(p for p in data['pin_maps'][0]['pins'] if p['name']=='V-')['footprint_pad']='12'
    return data
  for field in ('authority','availability','hash','identity','numeric','pin'):
   with self.subTest(field=field),self.assertRaises(ValueError):ll.supply_value(Changed(field),inv,'OPA4196IDR',TYP)
 def test_external_el_ceilings_and_unsigned_return_are_not_device_currents(self):
  groups=[g for g in self.L['interface_demands'] if g['scenario_id']==TYP]
  rails={g['net']:g for g in groups if g['net'] in ll.RAILS}
  self.assertEqual({net:g['current_A'] for net,g in rails.items()},{'+12V':.05,'-12V':-.05,'+5V':.07})
  returns=[g for g in groups if g['net']=='AGND'];self.assertEqual(len(returns),1)
  self.assertIsNone(returns[0]['current_A']);self.assertEqual(returns[0]['maximum_absolute_current_A'],.17)
  for group in groups:
   self.assertFalse(group['eligible_for_device_solve']);self.assertEqual(group['per_pad_split_status'],'UNSUPPORTED')
  self.assertEqual(self.L['external_boundaries']['EL']['signed_return_status'],'UNSUPPORTED')
 def test_all_gh_conductors_are_named_and_not_evaluated(self):
  gh=self.L['external_boundaries']['GH']
  self.assertEqual(gh['total_conductors'],380);self.assertEqual(gh['core_conductors'],376)
  self.assertEqual(len({c['id'] for c in gh['conductors']}),380)
  self.assertEqual(gh['compliance_status'],'NOT EVALUATED');self.assertEqual(gh['limit_A'],.5)
  for conductor in gh['conductors']:
   self.assertIsNone(conductor['current_A']);self.assertEqual(conductor['compliance_status'],'NOT EVALUATED')
   self.assertEqual(conductor['current_operator_status'],'UNSUPPORTED')

 def test_hash_stable(self):
  self.assertEqual(ll.build()['ledger_sha256'],self.L['ledger_sha256'])

if __name__=='__main__':unittest.main()
