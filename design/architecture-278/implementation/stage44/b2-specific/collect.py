"""Export compact, hash-bound study evidence; leave large native artifacts ignored."""
from pathlib import Path
import hashlib,json,shutil
from collections import Counter
ROOT=Path(__file__).resolve().parents[5]
HERE=Path(__file__).resolve().parent
CACHE=ROOT/'.circuit-cache'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def put(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
def collect():
    out=HERE/'evidence';out.mkdir(exist_ok=True)
    copies={
      'branches.json':CACHE/'stage44/branches.json',
      'receipt.json':CACHE/'stage44-b2-routed/receipt.json',
      'adjustments.json':CACHE/'stage44/adjustments-v2.json',
      'power-proposal.json':CACHE/'stage44-b2-placement-v2/power-proposal.json',
      'power-paths.json':CACHE/'stage44-b2-placement-v2/power-proposal-paths.json',
      'anchor-proposal.json':CACHE/'stage44-b2-power/anchor-proposal.json',
      'signals-proposal.json':CACHE/'stage44-b2-anchor/signals-priority-proposal.json',
      'settlement.json':CACHE/'stage44/settlement.json',
      'reuse.json':CACHE/'stage44/reuse.json',
    }
    for dst,src in copies.items():shutil.copy2(src,out/dst)
    for label,folder,names in [
      ('pass1','stage44-b2-routed',['drc-routed.json','connectivity-comparison-pass1.json','power-connections-pass1.json','identity-audit-pass1.json']),
      ('pass2','stage44-b2-routed',['drc-pass2.json','comparison-pass2.json','power-pass2.json','identity-pass2.json']),
      ('pass3','stage44-b2-routed',['drc-pass3.json','comparison-pass3.json','power-pass3.json','identity-pass3.json']),
      ('fresh','stage44-b2-fresh',['drc-passfresh.json','comparison-passfresh.json','power-passfresh.json','identity-passfresh.json'])]:
        dest=out/label;dest.mkdir(exist_ok=True)
        for name in names:shutil.copy2(CACHE/folder/name,dest/name)
        shutil.copy2(CACHE/folder/(names[0]+'.execution.json'),dest/(names[0]+'.execution.json'))
    attempts=[]
    for folder,name in [('stage44-b2-placement-v1','drc-placement.json'),('stage44-b2-placement-v2','drc-placement.json'),('stage44-b2-power','drc-power.json'),('stage44-b2-anchor','drc-anchor.json')]:
        p=CACHE/folder/name;d=read(p)
        attempts.append({'path':str(p.relative_to(ROOT)),'sha256':sha(p),'board_sha256':sha(p.with_name('osc-jack-left.kicad_pcb')),'errors':[v for v in d['violations'] if v['severity']=='error'],'warnings':dict(Counter(v['type'] for v in d['violations'] if v['severity']=='warning')),'opens':len(d['unconnected_items']),'parity':len(d['schematic_parity'])})
    for name in ('signals-proposal-search.json','signals-priority-proposal-search.json'):
        p=CACHE/'stage44-b2-anchor'/name;d=read(p)
        attempts.append({'path':str(p.relative_to(ROOT)),'sha256':sha(p),'links':len(d['results']),'failed_links':[r for r in d['results'] if not r['path']],'new_objects':d['new_objects'],'resolution_mm':d['resolution_mm'],'priority_net':d['priority_net']})
    put(out/'attempts.json',attempts)
    files=set()
    for pattern in ('stage44/*','stage44-b2-*/*','stage42-full-b1-fresh/*'):
        files.update(p for p in CACHE.glob(pattern) if p.is_file())
    put(out/'local-artifact-bindings.json',{str(p.relative_to(ROOT)):{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(files)})
    drivers=out/'commands';drivers.mkdir(exist_ok=True)
    for p in (CACHE/'stage44').glob('*.sh'):shutil.copy2(p,drivers/p.name)
    print(json.dumps({'exported_files':sum(p.is_file() for p in out.rglob('*')),'local_bound_artifacts':len(files)}))
if __name__=='__main__':collect()
