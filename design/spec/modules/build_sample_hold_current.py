"""Reproducible partial rail worksheet for the H1/H2 pilot."""
from collections import Counter
from pathlib import Path
import json
from .sample_hold import ROOT,family
BUDGET=json.loads((ROOT/'design/standard/rail-budget-preliminary.json').read_text())
LOADS={x['id']:x for x in BUDGET['loads']}
RAILS=('+12V','-12V','+5V')
OUT=ROOT/'design/reports/current/sample_hold.json'
ROLE_BY_SYMBOL={
 'OPA4196IDR':'opamp_audio','OPA4197IPWR':'opamp_precision','ADG5412FBRUZ':'fault_switches','LF398M_NOPB':'sample_hold','LM393BIDR':'comparators'
}

def build():
 f=family();packages={p.key.rsplit('.',1)[0]:p.symbol.split(':')[-1] for p in f.parts if not p.dnp}
 count=Counter(packages.values());typ={r:0.0 for r in RAILS};upper={r:0.0 for r in RAILS};breakdown=[]
 for symbol,role in ROLE_BY_SYMBOL.items():
  qty=count[symbol]
  if not qty:continue
  load=LOADS[role];a=dict(load['typical_unit_mA']);b=dict(load['planning_unit_mA'])
  if symbol=='LM393BIDR':a['-12V']=0;b['-12V']=0 # gate comparator uses +12V/GND
  for rail in RAILS:typ[rail]+=qty*a[rail];upper[rail]+=qty*b[rail]
  breakdown.append({'symbol':symbol,'whole_packages':qty,'budget_load_id':role,'typical_unit_mA':a,'planning_unit_mA':b})
 for role,qty in (('magnitude_leds',3),('output_loads',1)):
  load=LOADS[role]
  for rail in RAILS:typ[rail]+=qty*load['typical_unit_mA'][rail];upper[rail]+=qty*load['planning_unit_mA'][rail]
  breakdown.append({'dynamic_load':role,'count':qty,'typical_unit_mA':load['typical_unit_mA'],'planning_unit_mA':load['planning_unit_mA']})
 rows=[]
 for instance in ('H1','H2'):
  rows.append({'instance':instance,'known_typical_mA':{r:round(typ[r],6) for r in RAILS},'known_planning_upper_mA':{r:round(upper[r],6) for r in RAILS},'complete_total_typical_mA':None,'complete_total_maximum_mA':None,'maximum_status_by_rail':{r:'NOT ESTABLISHED - incomplete device/dynamic load data' for r in RAILS},'plus_5V_note':'The 0 mA known +5 V subtotal is not a zero-current claim. HC14, HC221, pull-up and switching demand are unquantified. REF5050 input is on +12 V and is also absent from that rail subtotal.','basis':'Per-instance whole-package count from generated family plus the preliminary per-package/LED/output-load worksheet. This is a planning subtotal, not guaranteed maximum demand.','unquantified':['REF5050 input and buffered reference loads on +12 V','SN74HC14 and CD74HC221 quiescent/dynamic current on +5 V','gate comparator and button pull-up switching duty','fault-switch enable feed and fault current','actual LF398 acquisition and hold drive','capacitor charge, output contention and cable load','factory population/allocation and package sharing']})
 return {'schema_version':1,'module':'sample_hold','authority':'OSC-ES-1 PROPOSAL (planning, owner-delegated)','status':'Unvalidated partial current worksheet; no complete typical or maximum per rail','source':'design/standard/rail-budget-preliminary.json','fitted_package_count_per_instance':dict(sorted(count.items())),'dnp_alternatives_per_instance':[p.key for p in f.parts if p.dnp],'breakdown':breakdown,'instances':rows,'whole_instrument_warning':'The preliminary whole-instrument estimate is superseded by design/power/rail-budget.json; the S&H +12 V reference and +5 V logic draft allowances are recorded separately in design/power/rail-ledger.json. Guaranteed maxima remain unestablished.'}

def main(check=False):
 body=json.dumps(build(),indent=2)+'\n'
 if check:
  if not OUT.is_file() or OUT.read_text()!=body:raise SystemExit('sample-hold current report drift')
 else:OUT.parent.mkdir(parents=True,exist_ok=True);OUT.write_text(body)
 print('Sample-hold current: two per-instance partial planning rail worksheets current')
if __name__=='__main__':
 import sys
 main('--check' in sys.argv)
