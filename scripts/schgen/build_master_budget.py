#!/usr/bin/env python3
"""Sum authored module current worksheets without promoting estimates to maxima."""
from __future__ import annotations
import argparse,json
from pathlib import Path
import sys
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from design.spec.instrument import specification

RAILS=('+12V','-12V','+5V')
REPORTS={x:ROOT/'design/reports/current'/f'{x}.json' for x in
         ('sample_hold','oscillator','filter','noise','envelope','mult',
          'manual_ab','mix5','mix4_vca','wavefolder','offset')}
TYPICAL=('planning_typical_mA','typical_mA_per_rail','known_typical_mA')
UPPER=('planning_upper_mA','planning_maximum_mA_per_rail','known_planning_upper_mA')


def first(record,keys):
    for key in keys:
        if key in record:return record[key],key
    raise ValueError(f'none of {keys} in {record.keys()}')


def build():
    source=json.loads((ROOT/'design/power/rail-budget-input.json').read_text())
    modules={}
    for module,path in REPORTS.items():
        data=json.loads(path.read_text());rows={}
        if module=='oscillator':
            for sheet in data['sheets']:
                for name in sheet['instances']:
                    rows[name]={'instance':name,'planning_typical_mA':sheet['planning_typical_mA_per_instance'],
                                'planning_upper_mA':sheet['planning_upper_mA_per_instance'],
                                'guaranteed_maximum_mA':sheet['guaranteed_maximum_mA_per_instance']}
        else:rows={r['instance']:r for r in data['instances']}
        modules[module]=(path,rows)
    _,instances=specification();records=[]
    for inst in instances:
        if inst.name=='POWER':continue
        module='oscillator' if inst.family=='octave_reference' else inst.family
        path,rows=modules[module]
        if inst.name not in rows:raise ValueError(f'missing current row {inst.name} in {path}')
        row=rows[inst.name];typ,typ_key=first(row,TYPICAL);upper,upper_key=first(row,UPPER)
        for r in RAILS:
            if r not in typ or r not in upper:raise ValueError(f'missing {r} current in {path}: {inst.name}')
        maximum=next((row[k] for k in ('guaranteed_maximum_mA','guaranteed_maximum_mA_per_rail','complete_total_maximum_mA') if k in row),None)
        if maximum is not None and (not isinstance(maximum,dict) or any(maximum[r] is not None for r in RAILS)):
            raise ValueError(f'unexpected established maximum; review source {path}: {inst.name}')
        records.append({'instance':inst.name,'family':inst.family,'source':str(path.relative_to(ROOT)),
                        'typical_subtotal_mA':typ,'planning_upper_subtotal_mA':upper,
                        'guaranteed_maximum_mA':{r:None for r in RAILS},
                        'partial':inst.family=='sample_hold',
                        'source_fields':{'typical':typ_key,'planning_upper':upper_key}})
    if len(records)!=34 or len({x['instance'] for x in records})!=34:
        raise ValueError('expected 33 modules plus one shared octave reference current row')
    inlet=source['synth_inlet']['nominal_bleeder_current_mA']
    totals={kind:{r:round(sum(x[key][r] for x in records)+inlet[r],6) for r in RAILS}
            for kind,key in [('known_typical_subtotal_mA','typical_subtotal_mA'),
                             ('known_planning_upper_subtotal_mA','planning_upper_subtotal_mA')]}
    ceilings={r:source['rails'][r]['design_ceiling_80_percent'] for r in RAILS}
    margin={r:round(ceilings[r]-totals['known_planning_upper_subtotal_mA'][r],6) for r in RAILS}
    contributors={r:sorted([{'instance':x['instance'],'mA':x['planning_upper_subtotal_mA'][r]}
                            for x in records],key=lambda x:(-x['mA'],x['instance']))[:10] for r in RAILS}
    return {'schema_version':2,'status':'UNVALIDATED DRAFT - summed known/report planning subtotals; complete typical and guaranteed maxima NOT ESTABLISHED',
            'source_lock':source['source_lock'],'units':'mA','rails':source['rails'],
            'current_sources':[str(p.relative_to(ROOT)) for p in REPORTS.values()],
            'synth_inlet':source['synth_inlet'],'module_instance_count':33,
            'shared_reference_count':1,'power_sheet_count':1,
            'instances':records,'known_typical_subtotal_mA':totals['known_typical_subtotal_mA'],
            'known_planning_upper_subtotal_mA':totals['known_planning_upper_subtotal_mA'],
            'guaranteed_maximum_mA':{r:None for r in RAILS},
            'design_ceiling_mA':ceilings,'planning_subtotal_margin_to_ceiling_mA':margin,
            'planning_subtotal_overshoot_mA':{r:round(max(0,-margin[r]),6) for r in RAILS},
            'largest_planning_contributors':contributors,
            'incomplete_sources':['sample_hold H1/H2 0 mA known +5 V subtotal excludes REF5050, HC14/HC221 and dynamic/pull-up demand',
                                  'NOISE2 current is an estimate, not a source-backed maximum',
                                  'all module reports leave guaranteed maxima unresolved',
                                  'power inlet TVS/capacitor leakage, startup, faults and external cable loads lack a complete bound'],
            'preliminary_model':source['preliminary_model'],
            'note':'No overlap removed without connectivity evidence. Planning upper is not a guaranteed or measured maximum; #34 owns rail closure and any overshoot resolution.'}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true');args=parser.parse_args()
    out=ROOT/'design/power/rail-budget.json';body=json.dumps(build(),indent=2,ensure_ascii=False)+'\n'
    if args.check:
        if out.read_text()!=body:raise ValueError('rail-budget.json drift')
    else:out.write_text(body)
    report=build();print('Known planning upper subtotal:',report['known_planning_upper_subtotal_mA'])
    print('Planning subtotal overshoot:',report['planning_subtotal_overshoot_mA'])

if __name__=='__main__':main()
