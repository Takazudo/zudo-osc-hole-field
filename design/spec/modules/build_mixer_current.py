"""Per-instance rail planning for the captured MIX5 and MIX4 VCA proposals.

Planning upper numbers are budget allowances, not guaranteed maxima.
"""
from collections import Counter
import json
from design.spec.modules.mixer_common import RAILS
from design.spec.modules.mix5 import family as mix5_family, INSTANCES as MIX5
from design.spec.modules.mix4_vca import family as mix4_family, INSTANCES as MIX4
from design.spec.cells._builder import ROOT

SUPPLIES=('+12V','-12V','+5V')
LOADS={x['id']:x for x in json.loads((ROOT/'design/standard/rail-budget-preliminary.json').read_text())['loads']}


def build_one(name,family,instances):
    f=family();packages={p.key.rsplit('.',1)[0]:p.symbol.split(':')[-1] for p in f.parts if p.prefix=='U'}
    counts=Counter(packages.values());rows=[];typ=dict.fromkeys(SUPPLIES,0.0);plan=typ.copy()
    def add(label,qty,lo,hi,basis):
        a=dict(zip(SUPPLIES,lo));b=dict(zip(SUPPLIES,hi))
        rows.append({'load':label,'count':qty,'typical_unit_mA':a,'planning_unit_mA':b,'basis':basis})
        for rail in SUPPLIES:typ[rail]+=qty*a[rail];plan[rail]+=qty*b[rail]
    for symbol,id in [('OPA4196IDR','opamp_audio'),('OPA4197IPWR','opamp_precision'),('ADG5412FBRUZ','fault_switches'),('LM393BIDR','comparators'),('LM13700M_NOPB','ota')]:
        if not counts[symbol]:continue
        x=LOADS[id]
        add(symbol,counts[symbol],[x['typical_unit_mA'][r] for r in SUPPLIES],
            [x['planning_unit_mA'][r] for r in SUPPLIES],x['basis'])
    for label,count,id in [('magnitude indicators',6,'magnitude_leds'),('pre-level clip LED',1,'clip_leds'),('SUM external load',1,'output_loads')]:
        x=LOADS[id]
        add(label,count,[x['typical_unit_mA'][r] for r in SUPPLIES],
            [x['planning_unit_mA'][r] for r in SUPPLIES],x['basis'])
    input_count=5 if name=='mix5' else 4
    add('reference, signal pots, summer feedback, servo and trims',1,
        (3,3,0),(8,8,0),
        'Engineering allowance for REF5050 supply/load and resistor networks; no complete source-backed worst-case network bound. Includes OTA servo for MIX4.')
    add('fault-switch enable feeds',input_count,
        (0,0,.05),(0,0,.1),
        'Each +5 V / ~101 kΩ enable feed is ~0.05 mA. Planning reserve includes input current and tolerance; no guaranteed maximum.')
    if name=='mix4_vca':
        add('ATTEN fault-switch enable feed',1,(0,0,.05),(0,0,.1),'Same ADG enable network as each audio input.')
    return {'schema_version':1,'module':name,'authority':'PROPOSAL (planning, unvalidated)',
            'status':'Captured package count and preliminary per-rail budget; not a hardware maximum',
            'IC_packages_per_instance':dict(sorted(counts.items())),'breakdown':rows,
            'instances':[{'instance':i,'planning_typical_mA':{r:round(typ[r],4) for r in SUPPLIES},
                          'planning_upper_mA':{r:round(plan[r],4) for r in SUPPLIES},
                          'guaranteed_maximum_mA':{r:None for r in SUPPLIES}} for i in instances],
            'planning_upper_total_mA':{r:round(len(instances)*plan[r],4) for r in SUPPLIES},
            'guaranteed_maximum_status':'NOT ESTABLISHED: reference load, LED waveform, signal swings, OTA bias/servo, temperature, startup and faults need measurement.',
            'decoupling_nF_per_instance':100*sum('_C_DEC_' in p.key for p in f.parts),
            'note':'Packages include all physical amplifier channels and local 100 nF supply bypasses; no bulk capacitor or short-circuit allowance. Whole-instrument closure belongs to the power budget.'}


def build():
    return {'mix5':build_one('mix5',mix5_family,MIX5),
            'mix4_vca':build_one('mix4_vca',mix4_family,MIX4)}


def main(check=False):
    for name,report in build().items():
        target=ROOT/'design/reports/current'/f'{name}.json';body=json.dumps(report,indent=2)+'\n'
        if check:assert target.read_text()==body,name+' current report drift'
        else:target.write_text(body)
        print(name,report['planning_upper_total_mA'])

if __name__=='__main__':
    import sys
    main('--check' in sys.argv)
