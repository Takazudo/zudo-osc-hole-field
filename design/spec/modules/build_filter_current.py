"""Per-instance captured filter rail planning counts; no guaranteed maxima."""
from collections import Counter
import json
from design.spec.modules.filter import ROOT,family,INSTANCES
RAILS=('+12V','-12V','+5V')
LOADS={x['id']:x for x in json.loads((ROOT/'design/standard/rail-budget-preliminary.json').read_text())['loads']}


def build():
    f=family();packages={p.key.rsplit('.',1)[0]:p.symbol.split(':')[-1] for p in f.parts if p.prefix=='U'}
    counts=Counter(packages.values());rows=[];typ=dict.fromkeys(RAILS,0.0);upper=typ.copy()
    def add(label,qty,a,z,basis):
        a=dict(zip(RAILS,a));z=dict(zip(RAILS,z))
        for r in RAILS:typ[r]+=qty*a[r];upper[r]+=qty*z[r]
        rows.append({'load':label,'count':qty,'typical_unit_mA':a,'planning_unit_mA':z,'basis':basis})
    for symbol,id in [('OPA4196IDR','opamp_audio'),('OPA4197IPWR','opamp_precision'),('ADG5412FBRUZ','fault_switches'),('LM13700M_NOPB','ota')]:
        x=LOADS[id];add(symbol,counts[symbol],[x['typical_unit_mA'][r] for r in RAILS],[x['planning_unit_mA'][r] for r in RAILS],x['basis'])
    add('Four magnitude indicators',4,(.25,.25,0),(1.25,1.25,0),'OSC-ES-1 brightness envelope; per-rail peaks need not coincide.')
    add('Four external output loads',4,(.05,.05,0),(.5,.5,0),'5 V into 100k typical / 10k planning load; no simultaneous-short guarantee.')
    add('Reference/control/expo/feedback reserve',1,(7,7,0),(12,12,0),'Includes REF5050, four +/-5V offset trim tracks (4mA/rail), manual pots, signal pots, current converters/mirror and feedback networks. Conservative overlap with inherited OTA bias allowance is not subtracted. Replace with actual operating-point/bench bounds.')
    add('Input-isolator enable feeds',1,(0,0,.2),(0,0,.3),'Four enable feeds approximately 5V/101k each, plus digital input-current allowance; no other +5V consumer in this family.')
    return {'schema_version':1,'module':'filter','authority':'PROPOSAL (planning, owner-delegated)','status':'Captured package planning worksheet; not hardware or a guaranteed maximum','IC_packages_per_instance':dict(sorted(counts.items())),'breakdown':rows,'instances':[{'instance':i,'planning_typical_mA':{r:round(typ[r],6) for r in RAILS},'planning_upper_mA':{r:round(upper[r],6) for r in RAILS},'guaranteed_maximum_mA':{r:None for r in RAILS}} for i in INSTANCES],'planning_upper_total_mA':{r:round(3*upper[r],6) for r in RAILS},'guaranteed_maximum_status':'NOT ESTABLISHED - actual bias, signal, temperature, converter, startup and fault loads unqualified','decoupling_nF_per_instance':100*sum('_C_DEC_' in p.key for p in f.parts),'note':'Two dual-OTA packages provide four actual OTA sections; whole amplifier packages and unused followers are charged. No per-module bulk allocation. #33/#34 owns whole-instrument closure.'}


def main(check=False):
    p=ROOT/'design/reports/current/filter.json';text=json.dumps(build(),indent=2)+'\n'
    if check:assert p.read_text()==text,'filter current report drift'
    else:p.write_text(text)
    print('Filter current planning total:',build()['planning_upper_total_mA'])
if __name__=='__main__':
    import sys
    main('--check' in sys.argv)
