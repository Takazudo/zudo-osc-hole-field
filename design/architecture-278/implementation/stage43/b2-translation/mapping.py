"""Read-only native proof of exact poses and source-semantic pin/net translation."""
from pathlib import Path
import json,sys
import pcbnew
from prepare import BASE,BASE_HASH,ROOT
from identity_guard import digest
from native_guard import check_native
from translation import translated

def verify(directory):
    path=directory/BASE.name;raw=path.read_text();original=BASE.read_text()
    if digest(original)!=BASE_HASH:raise ValueError('accepted Stage42 baseline changed')
    b=pcbnew.LoadBoard(str(path));check_native(b,raw)
    old=pcbnew.LoadBoard(str(BASE));check_native(old,original)
    fp={f.GetReference():f for f in b.GetFootprints()};oldfp={f.GetReference():f for f in old.GetFootprints()}
    planpath=ROOT/'design/architecture-278/implementation/stage40/mult-copper-plan/plan.json'
    plan=json.loads(planpath.read_text());receipt=json.loads((directory/'receipt.json').read_text())
    refs={r:v['B2_ref'] for r,v in plan['candidate_B1'].items()}
    if receipt['mapping']!=refs:raise ValueError('ref mapping differs from plan')
    logical={r['logical']:r['native'] for r in plan['net_mapping']}
    nets={v:logical['B2:'+k[3:]] for k,v in logical.items() if k.startswith('B1:')}
    nc={(r['ref'],r['pin']):r['native_net'] for r in plan['NC_equivalence']}
    for (r,p),n in nc.items():
        if r in refs:nets[n]=nc[refs[r],p]
    if receipt['net_mapping']!=nets:raise ValueError('native map differs from source semantic map')
    rows=[];deviations=[]
    for a,c in refs.items():
        f,g=oldfp[a],fp[c]
        if f.GetLayer()!=g.GetLayer() or f.GetOrientationDegrees()!=g.GetOrientationDegrees():raise ValueError('face/angle translation')
        delta=(g.GetPosition().x-f.GetPosition().x,g.GetPosition().y-f.GetPosition().y)
        if delta!=(34000000,0):deviations.append({'B1':a,'B2':c,'kind':'origin','delta_nm':list(delta)})
        ap={p.GetNumber():p for p in f.Pads()};bp={p.GetNumber():p for p in g.Pads()}
        if ap.keys()!=bp.keys():raise ValueError('pin-set translation')
        for pin,p in ap.items():
            q=bp[pin]
            pd=(q.GetPosition().x-p.GetPosition().x,q.GetPosition().y-p.GetPosition().y)
            if pd!=(34000000,0):deviations.append({'B1':a,'B2':c,'kind':'pad','pin':pin,'delta_nm':list(pd)})
            if q.GetNetname()!=nets[p.GetNetname()]:raise ValueError('pad net mapping')
            owners={z.GetReference() for z in old.GetFootprints() for t in z.Pads() if t.GetNetname()==q.GetNetname()}
            if q.GetNetname() not in {'AGND','+12V','-12V','+5V'} and not owners<=set(refs.values()):raise ValueError('foreign private-net owner')
        rows.append({'B1':a,'B2':c,'pads':len(ap),'translation_nm':list(delta),'native_angle':g.GetOrientationDegrees(),'layer':b.GetLayerName(g.GetLayer())})
    evidence=ROOT/'design/architecture-278/implementation/stage42/full-b1/evidence'
    expected=[]
    for name in ('power-proposal.json','signal-proposal.json'):expected.extend(translated(r,nets) for r in json.loads((evidence/name).read_text())['copper'])
    if json.loads((directory/'proposal.json').read_text())['copper']!=expected:raise ValueError('routing not exact translation')
    output={'baseline_sha256':BASE_HASH,'candidate_sha256':digest(raw),'exact_translation_verified':not deviations,'pose_deviations':deviations,'packages':rows,'pad_count':sum(r['pads'] for r in rows),'copper_count':len(expected),'source_sha256':{str(p.resolve().relative_to(ROOT)):digest(p.read_text()) for p in (planpath,evidence/'prepare-receipt.json',evidence/'power-proposal.json',evidence/'signal-proposal.json',directory/'receipt.json',directory/'proposal.json')}}
    (directory/'mapping-audit.json').write_text(json.dumps(output,indent=2)+'\n');print(json.dumps({'packages':len(rows),'pads':output['pad_count'],'copper':len(expected),'strict_pose_translation':not deviations,'deviations':deviations}))
    if deviations:raise SystemExit(1)
if __name__=='__main__':verify(Path(sys.argv[1]))
