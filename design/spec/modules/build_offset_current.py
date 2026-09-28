"""Per-instance AO planning current from captured packages and standard cells."""
from collections import Counter
import json
from design.spec.modules.offset import ROOT, family, INSTANCES

RAILS=('+12V','-12V','+5V')
LOADS={x['id']:x for x in json.loads((ROOT/'design/standard/rail-budget-preliminary.json').read_text())['loads']}


def build():
    f=family()
    packages={p.key.rsplit('.',1)[0]:p.symbol.rsplit(':',1)[-1] for p in f.parts if p.prefix=='U'}
    counts=Counter(packages.values())
    rows=[];typ=dict.fromkeys(RAILS,0.0);upper=typ.copy()
    def add(label,n,a,b,basis):
        a=dict(zip(RAILS,a));b=dict(zip(RAILS,b))
        for r in RAILS:typ[r]+=n*a[r];upper[r]+=n*b[r]
        rows.append({'load':label,'count':n,'typical_unit_mA':a,'planning_unit_mA':b,'basis':basis})
    for symbol,id in [('OPA4197IPWR','opamp_precision'),('OPA4196IDR','opamp_audio'),('ADG5412FBRUZ','fault_switches'),('LM393BIDR','comparators')]:
        x=LOADS[id]
        add(symbol,counts[symbol],[x['typical_unit_mA'][r] for r in RAILS],[x['planning_unit_mA'][r] for r in RAILS],x['basis'])
    for label,id,count in [('three magnitude LEDs','magnitude_leds',3),('one clip LED','clip_leds',1),('one manual offset pot','dc_pots',1),('one external output load','output_loads',1)]:
        x=LOADS[id];add(label,count,[x['typical_unit_mA'][r] for r in RAILS],[x['planning_unit_mA'][r] for r in RAILS],x['basis'])
    add('REF5050 local generator and rail ladder',1,(2,.1,0),(3,.3,0),'Provisional reserve for reference IC supply and finite resistor/driver current; REF5050 maximum at ±12 V and rail startup are not established by this worksheet.')
    add('two input-switch enable feeds',1,(0,0,.1),(0,0,.3),'Approximately two 5 V/101 kΩ feeds plus digital-current reserve; fault and startup excluded.')
    add('internal command and feedback load',1,(.25,.25,0),(.75,.75,0),'Planning reserve for summing, feedback and level paths, not a measured operating point.')
    return {'schema_version':1,'module':'offset','authority':'PROPOSAL (planning, owner-delegated)',
            'status':'Package and cell planning worksheet; not guaranteed maxima',
            'IC_packages_per_instance':dict(sorted(counts.items())),'breakdown':rows,
            'instances':[{'instance':i,'planning_typical_mA':{r:round(typ[r],6) for r in RAILS},'planning_upper_mA':{r:round(upper[r],6) for r in RAILS},'guaranteed_maximum_mA':{r:None for r in RAILS}} for i in INSTANCES],
            'planning_upper_total_mA':{r:round(len(INSTANCES)*upper[r],6) for r in RAILS},
            'guaranteed_maximum_status':'NOT ESTABLISHED - reference, LED, output, signal, temperature, fault and startup loads unqualified',
            'note':'All whole OPA packages and both comparator packages per instance are counted. ±15 V mathematical sum exceeds available rail/output swing. #33/#34 must reconcile six-cell load with whole-instrument ceilings.'}


def main(check=False):
    p=ROOT/'design/reports/current/offset.json';s=json.dumps(build(),indent=2)+'\n'
    if check:assert p.read_text()==s,'offset current report drift'
    else:p.parent.mkdir(parents=True,exist_ok=True);p.write_text(s)
    print('AO planning upper total:',build()['planning_upper_total_mA'])
if __name__=='__main__':
    import sys
    main('--check' in sys.argv)
