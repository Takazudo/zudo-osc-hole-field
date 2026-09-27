"""Count captured oscillator packages; retain unknown total-current bounds."""
from collections import Counter
import json
from .oscillator import ROOT, family, octave_family, INSTANCES
BUDGET=json.loads((ROOT/'design/standard/rail-budget-preliminary.json').read_text())
LOADS={x['id']:x for x in BUDGET['loads']}
RAILS=('+12V','-12V','+5V')


def sheet(f, copies):
    packages={p.key.rsplit('.',1)[0]:p.symbol.split(':')[-1] for p in f.parts if p.prefix=='U'}
    count=Counter(packages.values());typ=dict.fromkeys(RAILS,0.0);upper=typ.copy();rows=[]
    for symbol,load_id in [('OPA4196IDR','opamp_audio'),('OPA4197IPWR','opamp_precision'),('ADG5412FBRUZ','fault_switches'),('LM393BIDR','comparators')]:
        n=count[symbol]
        if not n:continue
        a=LOADS[load_id]['typical_unit_mA'].copy();z=LOADS[load_id]['planning_unit_mA'].copy()
        if symbol=='LM393BIDR':a['-12V']=z['-12V']=0
        for r in RAILS:typ[r]+=n*a[r];upper[r]+=n*z[r]
        rows.append({'symbol':symbol,'whole_packages':n,'typical_unit_mA':a,'planning_unit_mA':z,'source':'OSC-ES-1 preliminary load '+load_id})
    if f.name=='oscillator':
        # Core's negative load is sourced by a local op-amp from the -12 V rail.
        extras=[('AS3340D core',1,(5,8,0),(6.5,10,0),'ALFA v7 p4 +15 V typical table for positive current; negative current 8/10 mA remains a planning allowance at buffered -5 V, not a manufacturer maximum.'),('Four 10 kohm jack loads',4,(.05,.05,0),(.5,.5,0),'OSC-ES-1 output-load envelope, not short-circuit demand.'),('Internal resistive/reference/shaper load reserve',1,(5,5,0),(12,12,0),'Includes sine tail, feedback and 10 kohm audio pots; conservative estimate pending operating-point measurement.'),('5 V conditioning reserve',1,(0,0,3),(0,0,6),'HC14, comparator pullups and ADG enables; estimate, not a guaranteed maximum.')]
    else:extras=[('Shared reference and distribution reserve',1,(3,3,0),(8,8,0),'REF5050 and buffered tap/control loads; charged once for all five channels, excludes amplifier Iq above.')]
    for name,n,a,z,why in extras:
        ad=dict(zip(RAILS,a));zd=dict(zip(RAILS,z))
        for r in RAILS:typ[r]+=n*ad[r];upper[r]+=n*zd[r]
        rows.append({'load':name,'quantity':n,'typical_unit_mA':ad,'planning_unit_mA':zd,'basis':why})
    return {'family':f.name,'instances':copies,'fitted_IC_packages_per_instance':dict(sorted(count.items())),'breakdown':rows,'planning_typical_mA_per_instance':{r:round(typ[r],6) for r in RAILS},'planning_upper_mA_per_instance':{r:round(upper[r],6) for r in RAILS},'guaranteed_maximum_mA_per_instance':{r:None for r in RAILS},'maximum_status':'NOT ESTABLISHED - core conditions differ, dynamic/temperature/fault load bounds unqualified','startup_capacitors_nF_per_instance':100*sum(p.key.startswith('C_DEC_') for p in f.parts)}


def build():
    rows=[sheet(family(),list(INSTANCES)),sheet(octave_family(),['OCTAVE_REF'])]
    total={r:round(sum(len(x['instances'])*x['planning_upper_mA_per_instance'][r] for x in rows),6) for r in RAILS}
    return {'schema_version':1,'status':'Unvalidated planning worksheet; not measured or guaranteed maximum','module':'oscillator','authority':'PROPOSAL (planning, owner-delegated)','sheets':rows,'planning_upper_total_mA':total,'shared_reference_count':1,'note':'Actual source-derived whole packages replace the original nine-section estimate. Unused amplifier channels consume Iq. Core VEE current is charged to -12 V through its buffer, not double-counted on a fictional -5 V supply. Complete rail closure remains #33/#34.'}


def main(check=False):
    path=ROOT/'design/reports/current/oscillator.json';body=json.dumps(build(),indent=2)+'\n'
    if check:assert path.read_text()==body,'oscillator current report drift'
    else:path.write_text(body)
    print('Oscillator current report current:',build()['planning_upper_total_mA'])
if __name__=='__main__':
    import sys
    main('--check' in sys.argv)
