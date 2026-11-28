import sys, math, json
sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from lib import *
HEAD='80569b5375087df519b79ead67d1bf56c16301e6'
sc=json.load(open(__import__('os').path.join(__import__('os').environ.get('OSC_REVIEW_OUT','/tmp'),'scenes.json')))
fpl={(p['board'],p['ref']):p for p in gjson(HEAD,'design/partition/floorplan-candidate.json')['placements']}
orig={(p['board'],p['ref']):p for p in gjson('6093081c','design/partition/floorplan-candidate.json')['placements']}
la={a['ref']:a for a in gjson(HEAD,'design/partition/locality-acceptances.json')['acceptances']}
print('locality-acceptances same at 6e5716e7:', gshow('6e5716e7','design/partition/locality-acceptances.json')==gshow(HEAD,'design/partition/locality-acceptances.json'))
io=gjson(HEAD,'design/reports/io-partition.json')
netpins={}
for u in io['package_units']:
    for pin,n in u['pins'].items():
        if n: netpins.setdefault(n,set()).add((u['ref'],pin))
def hp(pts):
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]; return (max(xs)-min(xs)+max(ys)-min(ys)) if len(pts)>1 else 0.0
print('## IC distances from 6093081c baseline')
for ref in ['U5113','U5112','U4646','U4417','U4526']:
    a=la[ref]; b=a['board']; o=orig[b,ref]
    out=[]
    for s in('pre','gate','cand'):
        pos,face,src,_=sc[s][f'{b}/{ref}']
        out.append((s,pos,face,src,round(math.dist((o['x_mm'],o['y_mm']),pos),4)))
    print(ref,'baseline',(o['x_mm'],o['y_mm']),'recorded pose',a['pose'],'recorded',a['distance_mm'],out)
# when did the U5113 gate row appear?
G='design/stack/geometry/links/link-gate.json'
for sha in ['6093081c','8243acdf','6e5716e7','32580f77']:
    try:
        rr={(f['board'],f['ref']):f for f in gjson(sha,G)['replacement']['footprints']}
        print(sha,'gate rows:',{r:(rr.get((b,r)) or {}).get('new') for b,r in [('JL','U5113'),('JL','R5108'),('JL','R5112'),('JR','D4601'),('JR','R4612')]})
    except Exception as e: print(sha,'ERR',str(e)[:80])
print('## grown nets (footprint origins, 1.5x(HPWL-HPWL paper))')
for ic in ['U4417','U4526']:
    a=la[ic]; b=a['board']
    for run in a['grown_nets']:
        n=run['net']; refs=sorted({r for r,p in netpins[n] if f'{b}/{r}' in sc['cand']})
        old=hp([(fpl[b,r]['x_mm'],fpl[b,r]['y_mm']) for r in refs])
        res={}
        for s in('pre','gate','cand'):
            L=1.5*hp([sc[s][f'{b}/{r}'][0] for r in refs])
            res[s]=(round(L-1.5*old,2),round(L*0.2,2))
        ch=[r for r in refs if sc['pre'][f'{b}/{r}'][:2]!=sc['cand'][f'{b}/{r}'][:2] or sc['pre'][f'{b}/{r}'][:2]!=sc['gate'][f'{b}/{r}'][:2]]
        print(ic,n,'recorded',(run['added_run_estimate_mm'],run['capacitance_estimate_pF']),'pre',res['pre'],'cand(overlay)',res['cand'],'cand(withheld)',res['gate'],'changed in S10:',ch)
print('## input runs (pad centres, 1.5xHPWL)')
boards={'JL':'osc-jack-left','JR':'osc-jack-right'}
def rot90(p,k):
    x,y=p
    for _ in range(int(k)//90): x,y=-y,x
    return x,y
for ic in ['U5112','U4646']:
    a=la[ic]; b=a['board']
    fps,_,_,_,_=board(open(f'{REPO}/boards/{boards[b]}/{boards[b]}.kicad_pcb').read())
    # board offset
    f=fps[ic]; off=(round(f['at'][0]-fpl[b,ic]['x_mm'],3),round(f['at'][1]-fpl[b,ic]['y_mm'],3)); print(b,'board offset',off)
    def pad(s,ref,pin):
        pos,face,src,turn=sc[s][f'{b}/{ref}']; f=fps[ref]; px,py,_=f['pads'][pin][0]
        dx,dy=px-f['at'][0],py-f['at'][1]
        if face!=f['layer'][0]: dx=-dx
        dx,dy=rot90((dx,dy),turn); return pos[0]+dx,pos[1]+dy
    for run in a['input_runs']:
        n=run['net']; pins=sorted(netpins[n]); miss=[p for p in pins if p[0] not in fps]
        pins=[p for p in pins if p[0] in fps]
        for s in('pre','cand'):
            pts={p:pad(s,*p) for p in pins}
            L=1.5*hp(list(pts.values())); icp=[xy for (r,_),xy in pts.items() if r==ic][0]
            d={r:round(math.dist(icp,xy),1) for (r,_),xy in pts.items() if r!=ic}
            print(ic,n,s,'run',round(L,1),'pF',round(L*0.2,1),d,'| recorded',run['routed_estimate_mm'],run['capacitance_estimate_pF'],run['input_passives_to_buffer_mm'],'missing',miss, {r:sc[s][f'{b}/{r}'][2] for r,_ in pins})
