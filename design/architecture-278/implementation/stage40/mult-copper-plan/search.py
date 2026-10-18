"""Optional deterministic source search; writes positions only, never native CAD.
NumPy2.3.5 used for author search. Committed positions are independently checked;
CI does not need to repeat optimization or reproduce floating-point search ties.
"""
import copy,importlib.util,json,math
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
s=importlib.util.spec_from_file_location('s39',ROOT/'design/architecture-278/implementation/stage39/mult-substrate-comparison/generate.py');m=importlib.util.module_from_spec(s);s.loader.exec_module(m);g=m.g

def edges(pk):
    e=[]
    for r,q in pk.items():
        if q['decouples']:
            owner=next(v for v in pk.values() if any(u['key'].rsplit('.',1)[0]==q['decouples'] for u in v['units']))
            for pin,net in q['pins'].items():
                if net=='AGND':continue
                target=next(p for p,n in owner['pins'].items() if n==net);e.append((r,pin,owner['ref'],target,30,'bypass'))
    nets={n for q in pk.values() for n in q['pins'].values() if n and n not in ('+12V','-12V','+5V','AGND')}
    for net in sorted(nets):
        ends=[(r,p) for r,q in pk.items() for p,n in q['pins'].items() if n==net]
        weight=80 if net.endswith('_FB') else 8 if net in ('IN_SENSE','IN_PROTECTED') else 2
        for i,(r,p) in enumerate(ends):
            for rr,pp in ends[i+1:]:
                if r!=rr:e.append((r,p,rr,pp,weight,net))
    return e

def candidates(q,blocks,back):
    rows=[];pad_offsets=[]
    for rot in (0,90,180,270):
        b,p=g.shape(q['footprint'],[0,0],back,rot)
        for y in np.arange(118.5,164,.5):
            for x in np.arange(7.5,39,.5):
                bb=np.array(b)+[x,y,x,y]
                if not g.inside(bb,[7.5,118.5,38.5,163.5]):continue
                if any(g.ov(g.grow(bb,.25),v) for v in blocks):continue
                rows.append([x,y,rot,*bb]);pad_offsets.append({z['pin']:np.array(z['xy'])+[x,y] for z in p})
    if not rows:raise ValueError('no static placement '+q['ref'])
    return np.array(rows),{pin:np.array([p[pin] for p in pad_offsets]) for pin in q['pins']}

def solve(pk,blocks,native_board):
    moving={r:q for r,q in pk.items() if not q['panel']};front={'U3102','C3106','C3107','C3101','C3102','C3103','R3107','R3110','R3113'}
    options={r:candidates(q,blocks['F.Cu' if r in front else 'B.Cu'],r not in front) for r,q in moving.items()};ee=edges(pk)
    fixed={r:q for r,q in pk.items() if q['panel']};rng=np.random.default_rng(40);best=None
    def position(q,pin):return np.array(next(p['xy'] for p in q['pads'] if p['pin']==pin))
    def fit(qs,r):
        rows,pads=options[r];valid=np.ones(len(rows),dtype=bool)
        for rr,v in qs.items():
            if rr==r or v['panel'] or (rr in front)!=(r in front):continue
            b=v['box'];valid &= ~((rows[:,3]<b[2]+.25)&(b[0]<rows[:,5]+.25)&(rows[:,4]<b[3]+.25)&(b[1]<rows[:,6]+.25))
        return valid
    def costs(qs,r):
        rows,pads=options[r];score=np.zeros(len(rows))
        for a,pa,b,pb,w,_ in ee:
            if a==r and b in qs:score+=w*np.abs(pads[pa]-position(qs[b],pb)).sum(axis=1)
            if b==r and a in qs:score+=w*np.abs(pads[pb]-position(qs[a],pa)).sum(axis=1)
        return score
    def assign(r,i):
        row=options[r][0][i];q=copy.deepcopy(pk[r]);q.update(origin=row[:2].tolist(),rotation=float(row[2]),side='front' if r in front else 'rear');q['box'],q['pads']=g.shape(q['footprint'],q['origin'],r not in front,q['rotation'])
        for p in q['pads']:p['net']=q['pins'][p['pin']]
        return q
    def score(qs):return sum(w*float(np.abs(position(qs[a],pa)-position(qs[b],pb)).sum()) for a,pa,b,pb,w,_ in ee)
    cluster_sets=[('U3102',['C3106','C3107']),('U3103',['C3108','C3109']),('U3101',['C3104','C3105'])]
    cluster_refs={r for u,cs in cluster_sets for r in [u]+cs};cluster_options=[]
    for u,cs in cluster_sets:
        opts=[];base=native_board['footprints'][u];back=u not in front
        for angle in (0,90,180,270):
            for iy in range(237,328):
                for ix in range(15,78):
                    group={}
                    for r in [u]+cs:
                        f=native_board['footprints'][r];offset=[f['origin'][j]-base['origin'][j] for j in (0,1)];origin=g.transformed(*offset,[ix/2,iy/2],False,angle)
                        rotation=((180-f['native_angle'] if back else -f['native_angle'])+angle)%360
                        q=copy.deepcopy(pk[r]);q.update(origin=origin,rotation=rotation,side='rear' if back else 'front');q['box'],q['pads']=g.shape(q['footprint'],origin,back,rotation)
                        if not g.inside(q['box'],[7.5,118.5,38.5,163.5]) or any(g.ov(g.grow(q['box'],.25),v) for v in blocks['B.Cu' if back else 'F.Cu']):break
                        for p in q['pads']:p['net']=q['pins'][p['pin']]
                        group[r]=q
                    if len(group)==3:opts.append(group)
        print('native-bypass cluster options',u,len(opts),flush=True);cluster_options.append(opts)
    order=sorted((r for r in moving if r not in cluster_refs),key=lambda r:-(lambda b:(b[2]-b[0])*(b[3]-b[1]))(g.courtyard(pk[r]['footprint'])))
    for attempt in range(1600):
        qs=copy.deepcopy(fixed)
        for opts in cluster_options:
            valid=[group for group in opts if not any(g.ov(g.grow(q['box'],.25),v['box']) for q in group.values() for v in qs.values() if not v['panel'] and q['side']==v['side'])]
            if not valid:break
            qs.update(copy.deepcopy(valid[int(rng.integers(len(valid)))]))
        if len(qs)!=len(fixed)+len(cluster_refs):continue
        for r in order:
            valid=fit(qs,r);inds=np.flatnonzero(valid)
            if not len(inds):break
            cost=costs(qs,r);cost += rng.uniform(0,80 if attempt else 0,size=len(cost))
            if r.startswith('U'):cost+=np.abs(options[r][0][:,:2]-np.array(pk[r]['origin'])).sum(axis=1)*.5
            i=inds[np.argmin(cost[inds])];qs[r]=assign(r,i)
        if len(qs)!=len(pk):continue
        for turn in range(8):
            changed=False
            for r in order if turn%2==0 else list(reversed(order)):
                valid=fit(qs,r);inds=np.flatnonzero(valid);cost=costs(qs,r)
                i=inds[np.argmin(cost[inds])];candidate=assign(r,i)
                prior=qs[r];before=score(qs);qs[r]=candidate
                if score(qs)<before-1e-7:changed=True
                else:qs[r]=prior
            if not changed:break
        total=score(qs)
        if best is None or total<best[0]:best=(total,qs);print('improved',attempt,round(total,3),flush=True)
    if best is None:raise ValueError('bounded search found no complete candidate')
    return best[1]

if __name__=='__main__':
    old=json.loads((ROOT/'design/architecture-278/implementation/stage39/mult-substrate-comparison/comparison.json').read_text())
    ns=importlib.util.spec_from_file_location('native',HERE/'native.py');native=importlib.util.module_from_spec(ns);ns.loader.exec_module(native)
    board=native.parse((ROOT/'boards/osc-jack-left/osc-jack-left.kicad_pcb').read_text())
    blocks={layer:[g.shift(row['box'],-dx) for dx in (0,34) for row in native.obstacles(board,old,layer)] for layer in ('F.Cu','B.Cu')}
    pk=solve(old['A']['packages_B1'],blocks,board)
    out={'search':'NumPy2.3.5 seed40;1600 constructions,8 coordinate-descent sweeps; rigid native IC/bypass clusters; Manhattan diagnostic only','positions':{r:{'origin':q['origin'],'rotation':q['rotation'],'side':q['side']} for r,q in pk.items()}}
    (HERE/'positions.json').write_text(json.dumps(out,indent=2)+'\n')
