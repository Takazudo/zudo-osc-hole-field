"""Whole-device service regressions: omitted returns must never become one-sided loads."""
import copy
import math
import unittest

import load_ledger as ll

TYP='normal-typ-v1'

class DeviceService(unittest.TestCase):
 @classmethod
 def setUpClass(cls):
  cls.ledger=ll.build()
  cls.rows=[r for r in cls.ledger['records'] if r['scenario_id']==TYP]
  cls.all_pads={r['pad_id'] for r in cls.rows}
  cls.full=ll.device_service(cls.ledger,TYP,cls.all_pads)
  cls.opa=next(d for d in cls.full['devices'] if d['symbol']=='OPA4197IPWR')
  cls.logic=next(d for d in cls.full['devices'] if d['symbol']=='SN74HC14DR')
 def device(self,result,ref):
  return next(d for d in result['devices'] if d['ref']==ref)
 def test_supported_population_and_all_signed_package_pairs(self):
  self.assertEqual(self.full['summary'],{'supported':231,'partial':0,'unserved':0,'unmapped':194})
  self.assertEqual(len(self.full['eligible_pad_ids']),462)
  self.assertEqual(self.full['included_global_residual_A'],0)
  for d in self.full['devices']:
   if d['eligible_for_solve']:
    self.assertEqual(len(d['required_pins']),2)
    self.assertTrue(all(p['current_mapped'] and p['served'] for p in d['required_pins']))
    self.assertEqual(d['signed_package_residual_A'],0)
 def test_missing_negative_supply_excludes_both_opamp_pins(self):
  pins=self.opa['required_pins'];negative=next(p['pad_id'] for p in pins if p['net']=='-12V')
  result=ll.device_service(self.ledger,TYP,self.all_pads-{negative});d=self.device(result,self.opa['ref'])
  self.assertEqual(d['service_status'],'partial');self.assertFalse(d['eligible_for_solve'])
  self.assertTrue({p['pad_id'] for p in pins}.isdisjoint(result['eligible_pad_ids']))
  self.assertTrue({p['pad_id'] for p in pins}<=set(result['excluded_pad_ids']))
  self.assertEqual(result['included_global_residual_A'],0)
 def test_missing_logic_return_excludes_vcc_too(self):
  ground=next(p['pad_id'] for p in self.logic['required_pins'] if p['net']=='AGND')
  result=ll.device_service(self.ledger,TYP,self.all_pads-{ground});d=self.device(result,self.logic['ref'])
  self.assertEqual(d['service_status'],'partial');self.assertEqual(d['evidence_status'],'conditional')
  self.assertFalse(d['eligible_for_solve']);self.assertEqual(result['included_global_residual_A'],0)
 def test_all_supplies_absent_is_unserved(self):
  required={p['pad_id'] for p in self.opa['required_pins']}
  result=ll.device_service(self.ledger,TYP,self.all_pads-required)
  self.assertEqual(self.device(result,self.opa['ref'])['service_status'],'unserved')
 def test_unmapped_ic_never_becomes_supported_from_connectivity(self):
  d=next(d for d in self.full['devices'] if d['symbol']=='AS3340D')
  self.assertEqual(d['service_status'],'unmapped');self.assertFalse(d['eligible_for_solve'])
  self.assertTrue(any(p['net'] not in ll.NETS for p in d['required_pins']))
  self.assertTrue(d['reasons'])
 def test_unknown_or_omitted_coverage_and_legacy_census_are_refused(self):
  with self.assertRaisesRegex(ValueError,'explicit all-net'):ll.device_service(self.ledger,TYP,None)
  with self.assertRaisesRegex(ValueError,'unknown pads'):ll.device_service(self.ledger,TYP,self.all_pads|{'invented-pad'})
  with self.assertRaisesRegex(ValueError,'unknown service scenario'):ll.device_service(self.ledger,'unknown',self.all_pads)
  ledger=copy.deepcopy(self.ledger);del ledger['census']['fitted_ics']['devices'][0]['supply_pins']
  with self.assertRaisesRegex(ValueError,'lacks required supply'):ll.device_service(ledger,TYP,self.all_pads)
 def test_missing_duplicate_or_unmapped_supply_row_excludes_whole_device(self):
  for corruption in ('missing','duplicate','null','provenance','wrong_net','wrong_sign','kcl','nan','bool','extra_current'):
   with self.subTest(corruption=corruption):
    ledger=copy.deepcopy(self.ledger)
    row=next(r for r in ledger['records'] if r['scenario_id']==TYP and r['ref']==self.opa['ref'] and r['net']=='+12V' and r['pad_class']=='ic_supply_pin')
    if corruption=='missing':ledger['records'].remove(row)
    elif corruption=='duplicate':ledger['records'].append(dict(row))
    elif corruption=='null':row['current_A']=None
    elif corruption=='provenance':row['provenance']='unmapped_allowance'
    elif corruption=='wrong_net':row['net']='AGND'
    elif corruption=='wrong_sign':row['current_A']=-row['current_A']
    elif corruption=='kcl':row['current_A']+=0.001
    elif corruption=='nan':row['current_A']=float('nan')
    elif corruption=='bool':row['current_A']=True
    elif corruption=='extra_current':ledger['records'].append(dict(row,pad='extra',pad_id='extra-current',current_A=0.001))
    coverage={r['pad_id'] for r in ledger['records'] if r['scenario_id']==TYP}
    result=ll.device_service(ledger,TYP,coverage);d=self.device(result,self.opa['ref'])
    self.assertEqual(d['service_status'],'unmapped');self.assertFalse(d['eligible_for_solve'])
    self.assertTrue(d['reasons']);self.assertTrue({p['pad_id'] for p in self.opa['required_pins']}.isdisjoint(result['eligible_pad_ids']))
 def test_actual_t2_service_preserves_global_and_board_package_balance(self):
  for scenario,service in self.ledger['device_service'].items():
   self.assertEqual(sum(service['summary'].values()),425)
   self.assertGreater(service['summary']['partial'],0)
   self.assertGreater(service['summary']['unserved'],0)
   self.assertEqual(service['included_global_residual_A'],0)
   for board,nets in service['included_board_net_sum_A'].items():self.assertAlmostEqual(math.fsum(nets.values()),0,places=12,msg=(scenario,board))
   for d in service['devices']:
    ids={p['pad_id'] for p in d['required_pins'] if p['pad_id']}
    eligible=ids.intersection(service['eligible_pad_ids'])
    self.assertTrue(not eligible or eligible==ids)

if __name__=='__main__':unittest.main()
