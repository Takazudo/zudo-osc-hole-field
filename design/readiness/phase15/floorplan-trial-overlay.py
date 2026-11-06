# Phase-15 floorplan trial overlay. Run ONLY in a scratch worktree: python3 floorplan-trial-overlay.py <worktree> soic|rexact|soic+rexact <pristine io-partition.json>
# It rewrites design/reports/io-partition.json there, then scripts/checks/partition35_floorplan.py is run.
import json,sys,copy
from pathlib import Path
W=Path(sys.argv[1]);mode=sys.argv[2]
orig=json.loads(Path(sys.argv[3]).read_text())
io=copy.deepcopy(orig)
fp='zudo-osc-hole-field:SOIC-14_3.9x8.7mm_P1.27mm'
soic=next(x for x in io['physical_packages'] if x['mpn']=='OPA4196IDR')['courtyard']
CONTROL={'U102','U202','U3303','U3403'}
n_soic=n_add=0
if 'soic' in mode:
    for x in io['physical_packages']:
        if x['mpn']=='OPA4197IPWR' and x['ref'] not in CONTROL:
            x['footprint']=fp;x['courtyard']=dict(soic);n_soic+=1
if 'rexact' in mode:
    # series pairs: one extra placement per instance, except PITCH_FINE (+4)
    extra={'oscillator:R_SAW_IN':1,'envelope:R_RISE_DRIVE_TOP':1,'envelope:R_FALL_DRIVE_TOP':1,'oscillator:R_PITCH_TUNE':1,
           'oscillator:R_TRI_BIAS_TOP':1,'envelope:R_FLOOR_TOP':1,'oscillator:R_RT':1,'oscillator:R_PWM_FB':1,
           'oscillator:R_SAW_BIAS_TOP':1,'oscillator:R_LINEAR_REFERENCE':1,'oscillator:R_PWM_OFFSET':1,
           'oscillator:R_PITCH_FINE':4,'wavefolder:R_OUTPUT_RF':1}
    pk={x['ref']:x for x in io['physical_packages']}
    seq=9000
    for u in list(io['package_units']):
        k=extra.get(u['role'])
        if not k: continue
        for i in range(k):
            seq+=1;ref=f'R{seq}'
            nu=copy.deepcopy(u);nu['ref']=ref;nu['pins']={'1':u['pins'].get('1'),'2':f"{u['pins'].get('2')}__SERIES{i}"} if isinstance(u['pins'],dict) else u['pins']
            io['package_units'].append(nu)
            np_=copy.deepcopy(pk[u['ref']]);np_['ref']=ref;io['physical_packages'].append(np_);n_add+=1
(W/'design/reports/io-partition.json').write_text(json.dumps(io,indent=1,ensure_ascii=False)+'\n')
print('soic',n_soic,'added',n_add)
