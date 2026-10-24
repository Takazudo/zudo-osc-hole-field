"""Read-only scalar orientation/pin-location comparison, not PCB routing or a solver."""
import argparse,copy,hashlib,json
from pathlib import Path
from revision_electrical import PACK,compare_front_banks

def build():
    names=('interface-contract.json','revision-mechanical-report.json','revision-electrical-report.json')
    contract,mechanical,electrical=[json.loads((PACK/n).read_text()) for n in names]
    pinout=electrical['rear_connector_pinout'];links=electrical['functional_front_links']
    cases=[];experiments=[]
    for instance in ('O1','O2'):
        for angle in (0,90,180,270):
            paths=[p for p in compare_front_banks(contract,mechanical,pinout,links,{instance:angle}) if p.get('instance')==instance and 'total_mm' in p]
            failures=[p for p in paths if not p['within_300mm']]
            wipers=[p for p in paths if '_W' in p['net']]
            cases.append({'instance':instance,'angle_deg':angle,'tile_extent_mm':[115,103] if angle in (90,270) else [103,115],'exceeding_paths':len(failures),'max_complete_allocation_mm':max(p['total_mm'] for p in paths),'max_wiper_allocation_mm':max(p['total_mm'] for p in wipers),'failures':[{'net':p['net'],'total_mm':p['total_mm']} for p in failures]})
            if instance!='O2' or angle not in (0,270):continue
            for net in sorted({p['net'] for p in failures}):
                costs=[]
                for slot in pinout:
                    trial=copy.deepcopy(pinout)
                    for p in trial:
                        if p['net']==net:p['pin']=slot['pin']
                    rows=compare_front_banks(contract,mechanical,trial,links,{instance:angle})
                    costs.append((max(p['total_mm'] for p in rows if p.get('instance')==instance and p.get('net')==net and 'total_mm' in p),slot['pin']))
                best,pin=min(costs)
                experiments.append({'instance':instance,'angle_deg':angle,'net':net,'best_contact_position':pin,'best_complete_allocation_mm':best,'positions_examined':len(pinout),'adopted':False})
    return {'status':'design comparison only; no CAD/physical qualification','source_sha256':{**{n:hashlib.sha256((PACK/n).read_bytes()).hexdigest() for n in names},'orientation_sweep.py':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'revision_electrical.py':hashlib.sha256(Path(__file__).with_name('revision_electrical.py').read_bytes()).hexdigest()},'cases':cases,'independent_pin_experiments':experiments,'experiment_limit':'Each signal moved independently through all96 positions; ignores mutual exclusivity and return pairing. Optimistic rejected bound, not an assignable pinout. All package/connector coordinates transform together. Whole-card relative local feedback geometry preserved.','recommendation':'Retain0degree populated candidate for current pinout minimax comparison;270O2 improves raw control lengths but worsens maximum full path. No orientation closes every path; independent pin choice also leaves specific paths over300mm. Circuit-aware whole-cluster placement still required.'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();out=json.dumps(build(),indent=2,sort_keys=True)+'\n';path=PACK/'revision-orientation-report.json'
    if a.check:
        if not path.exists() or path.read_text()!=out:raise SystemExit('stale orientation comparison')
    else:path.write_text(out)
    print('PASS scalar orientation/pin comparison reproduction; no orientation closes all paths; physical NOT RUN')
if __name__=='__main__':main()
