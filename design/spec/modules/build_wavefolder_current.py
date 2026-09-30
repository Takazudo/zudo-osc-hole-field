"""Wavefolder captured-package and explicit branch current planning worksheet."""
from collections import Counter
import json
from design.spec.modules.wavefolder import ROOT,family,INSTANCES
from design.spec.modules.run_oscillator_spice import number
RAILS=('+12V','-12V','+5V')
LOADS={r['id']:r for r in json.loads((ROOT/'design/standard/rail-budget-preliminary.json').read_text())['loads']}

def build():
 f=family();counts=Counter({p.key.rsplit('.',1)[0]:p.symbol.split(':')[-1] for p in f.parts if p.prefix=='U'}.values());rows=[];typ=dict.fromkeys(RAILS,0.);upper=typ.copy()
 def add(label,count,a,z,basis):
  a=dict(zip(RAILS,a));z=dict(zip(RAILS,z))
  for r in RAILS:typ[r]+=count*a[r];upper[r]+=count*z[r]
  rows.append({'load':label,'count':count,'typical_unit_mA':a,'planning_unit_mA':z,'basis':basis})
 for sym,key in [('OPA4196IDR','opamp_audio'),('OPA4197IPWR','opamp_precision'),('ADG5412FBRUZ','fault_switches'),('LM13700M_NOPB','ota')]:
  r=LOADS[key];add(sym,counts[sym],[r['typical_unit_mA'][v] for v in RAILS],[r['planning_unit_mA'][v] for v in RAILS],r['basis'])
 add('REF5050 allocation',1,(.8,0,0),(1.2,0,0),'Local reference supply allocation, not an established full-temperature maximum; buffer quads counted above.')
 add('Three magnitude LEDs',3,(.25,.25,0),(1.25,1.25,0),'OSC-ES-1 brightness/load envelope; no output indicator.')
 add('Offset trim track',1,(1,1,0),(1,1,0),'10V across10k =1mA drawn through each buffered reference rail.')
 add('Manual control tracks',1,(.15,.1,0),(.15,.1,0),'FOLD5V/100k plus BIAS10V/100k; nominal references, no allowance for resistor tolerance.')
 add('FOLD depth track/harness drive',1,(.25,.25,0),(1,1,0),'Up to10V differential across10k; local buffered harness stages already counted.')
 add('LEVEL track/harness drive',1,(.2,.2,0),(1,1,0),'Up to10V peak across10k planning envelope; no simultaneous fault claim.')
 add('PNP bias/command branch',1,(.2,.2,0),(1,1,0),'Nominal fullscale403uA;1mA reserve covers soft-clamp/reverse-BE command branch. Conservative overlap with OTA bias allowance retained.')
 add('Four diode clamp feeds',4,(.2,.2,0),(1,1,0),'Per stage10k feed: |drive|<=10V gives<=1mA in the passive clamp under the stated normal headroom envelope.')
 add('Four fold feedback paths',4,(.02,.02,0),(.2,.2,0),'At most20V differential/100k =0.2mA per feedback resistor; conservative planning condition, not amplifier short limit.')
 auxiliary=[p for p in f.parts if p.attributes.get('Role','').startswith('wavefolder:R_') and any(p.attributes['Role']=='wavefolder:R_'+k for k in ('CONTROL_MANUAL','CONTROL_DEPTH','CONTROL_FB','CONTROL_INV_IN','CONTROL_INV_FB','REF25_TOP','REF25_BOTTOM','TARGET_IN','TARGET_FB','INPUT_ATTEN_TOP','OFFSET_FEED','DRIVE_SIGNAL','DRIVE_BIAS_MANUAL','DRIVE_BIAS_BUFFER','DRIVE_FB','DRIVE_INV_IN','DRIVE_INV_FB','OUTPUT_RF','OUTPUT_RG','PRE_GAIN_FIXED','AC_RETURN'))]
 bound=sum(20/number(p.value)*1000 for p in auxiliary)
 add('Other local signal/control resistor paths',1,(bound/8,bound/8,0),(bound,bound,0),'Sum20V/R over explicit captured resistor list, applied conservatively to both rails; typical allocation uses one eighth of this envelope. Does not include startup/fault currents.')
 add('Command clamp resistor',1,(.02,.02,0),(1.1,1.1,0),'10k with up to11V differential under bounded normal amplifier/reference envelope.')
 add('Offset/input low-side divider loads',1,(.02,.02,0),(.05,.05,0),'Low-side200ohm input divider and1k offset return are driven through their large upper resistors; separate small reserve avoids assuming20V across them.')
 add('External output load',1,(.05,.05,0),(.5,.5,0),'5V into100k typical/10k planning. Output shorts and control-step peaks unqualified.')
 add('Input isolation enables',1,(0,0,.15),(0,0,.25),'Three approximately5V/101k enable feeds plus digital-input reserve.')
 return {'schema_version':1,'module':'wavefolder','authority':'PROPOSAL (planning, owner-delegated)','status':'Captured current planning; not a guaranteed maximum or hardware measurement','IC_packages_per_instance':dict(sorted(counts.items())),'breakdown':rows,'auxiliary_resistors':[{'role':p.attributes['Role'],'value_ohm':number(p.value)} for p in auxiliary],'instances':[{'instance':i,'planning_typical_mA':{r:round(typ[r],6) for r in RAILS},'planning_upper_mA':{r:round(upper[r],6) for r in RAILS},'guaranteed_maximum_mA':dict.fromkeys(RAILS,None)} for i in INSTANCES],'planning_upper_total_mA':{r:round(2*upper[r],6) for r in RAILS},'guaranteed_maximum_status':'NOT ESTABLISHED - actual device corners, dynamic controls, startup, output faults and physical board unqualified','decoupling_nF_per_instance':100*sum('_C_DEC_' in p.key for p in f.parts),'audio_coupling_nominal_nF_per_instance':1000,'note':'One active OTA section but whole dual package charged. Internal branch estimates replace a single preliminary lumped allowance. #33/#34 owns full-instrument current closure; no new module bulk.'}

def main(check=False):
 p=ROOT/'design/reports/current/wavefolder.json';s=json.dumps(build(),indent=2)+'\n'
 if check:assert p.read_text()==s,'wavefolder current report drift'
 else:p.write_text(s)
 print(build()['instances'][0]);print('Both wavefolders:',build()['planning_upper_total_mA'])
if __name__=='__main__':
 import sys
 main('--check' in sys.argv)
