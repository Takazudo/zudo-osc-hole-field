"""Captured E1–E6 rail planning; guaranteed maxima remain unestablished."""
from collections import Counter
import json
from design.spec.modules.envelope import ROOT,family,INSTANCES
RAILS=('+12V','-12V','+5V')
LOADS={r['id']:r for r in json.loads((ROOT/'design/standard/rail-budget-preliminary.json').read_text())['loads']}

def build():
 f=family();counts=Counter({p.key.rsplit('.',1)[0]:p.symbol.split(':')[-1] for p in f.parts if p.prefix=='U'}.values())
 rows=[];typ=dict.fromkeys(RAILS,0.);upper=typ.copy()
 def add(name,count,a,b,basis):
  a=dict(zip(RAILS,a));b=dict(zip(RAILS,b))
  for r in RAILS:typ[r]+=count*a[r];upper[r]+=count*b[r]
  rows.append({'load':name,'count':count,'typical_unit_mA':a,'planning_unit_mA':b,'basis':basis})
 for sym,key in [('OPA4196IDR','opamp_audio'),('OPA4197IPWR','opamp_precision'),('ADG5412FBRUZ','fault_switches'),('LM13700M_NOPB','ota')]:
  r=LOADS[key];add(sym,counts[sym],[r['typical_unit_mA'][v] for v in RAILS],[r['planning_unit_mA'][v] for v in RAILS],r['basis'])
 add('LM393BIDR',counts['LM393BIDR'],(.6,0,0),(1,0,0),'Whole dual packages on +12V/AGND; inherited planning allowance, no -12V comparator current. Pullups separate.')
 for sym in ('SN74HC00DR','SN74HC74DR','SN74HC14DR','CD74HC221M96'):
  add(sym,counts[sym],(0,0,.2),(0,0,.5),'Per-package planning reserve for static and clock/Schmitt dynamic current, not a guaranteed manufacturer maximum or simulated current; includes unused gates.')
 add('Three magnitude LEDs',3,(.25,.25,0),(1.25,1.25,0),'Inherited OSC-ES-1 brightness/load allowance; buffered input monitors only.')
 add('Two stage LEDs',2,(0,0,.25),(0,0,.55),'0.5mA nominal at8V plus planning allowance; conservatively charges both although one-hot states permit only one.')
 add('Four external output loads',4,(.08,.08,0),(.8,.8,0),'8V into100k typical/10k planning applied conservatively to every output/rail. No simultaneous-short qualification.')
 add('Reference, rates, clamp and control reserve',1,(6,6,0),(12,12,0),'Includes two +/-5V offset tracks (2mA/rail), matched-pair converters, active hold/idle clamp transients and reference/feedback networks. Conservative overlap with OTA bias allowance retained; dynamic/temperature bounds unqualified.')
 add('Comparator pullups',3,(0,0,.5),(0,0,5/4.7),'Three 4.7k pullups; unused comparator output is unconnected.')
 add('Five control-contact pulls',5,(0,0,.25),(0,0,.5),'10k pulls, conservative five simultaneous contacts; includes button/toggle RC charging allowance only at nominal voltage.')
 add('Input isolation enables',1,(0,0,.15),(0,0,.25),'Three approximately5V/101k input isolator enables and input-current reserve.')
 return {'schema_version':1,'module':'envelope','authority':'PROPOSAL (planning, owner-delegated)','status':'Captured package planning worksheet; not measured current or guaranteed maximum','IC_packages_per_instance':dict(sorted(counts.items())),'breakdown':rows,'instances':[{'instance':i,'planning_typical_mA':{r:round(typ[r],6) for r in RAILS},'planning_upper_mA':{r:round(upper[r],6) for r in RAILS},'guaranteed_maximum_mA':dict.fromkeys(RAILS,None)} for i in INSTANCES],'planning_upper_total_mA':{r:round(len(INSTANCES)*upper[r],6) for r in RAILS},'guaranteed_maximum_status':'NOT ESTABLISHED - actual bias, timing, temperature, output loading, startup and faults unqualified','decoupling_nF_per_instance':100*len([p for p in f.parts if p.key.startswith('C_DEC_')]),'note':'Expanded physical logic and buffering replace the rough two-logic-IC handoff estimate. No module bulk allocation; #33/#34 must reconcile actual captured package counts and bench currents.'}

def main(check=False):
 p=ROOT/'design/reports/current/envelope.json';s=json.dumps(build(),indent=2)+'\n'
 if check:assert p.read_text()==s,'envelope current report drift'
 else:p.write_text(s)
 print(build()['instances'][0]);print('Six-envelope total:',build()['planning_upper_total_mA'])
if __name__=='__main__':
 import sys
 main('--check' in sys.argv)
