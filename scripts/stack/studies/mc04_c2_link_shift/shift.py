"""Task C step 2a: can one link move so its fields free the unresolved ICs it covers, under the retained rules?

Removes the link from the final record, re-searches it with the retained engine and class-distance limits,
and rejects any candidate whose slot/connector/tail overlaps a protected IC courtyard (grown 0.35 mm).
Reports the cheapest result against the recorded one. Room/cost only; no geometry is written."""
import sys,json,math,pickle,time
sys.path.insert(0,'scripts/stack/geometry')
import links_gate as lg, links_gate_part2 as p2, stackgeom as sg
t=time.time()
inp=lg.load_inputs(sg.ROOT)
sites, model, ctx, out, s, refs = lg.gate_run(inp, {})
site_by={x['id']:x for x in sites}
doc=json.load(open('design/stack/geometry/links/link-gate.json'))
links=[r for r in doc['links'] if not r.get('gone')]
limits=p2.limits_of(ctx.gopts)
# unresolved IC geometry (original) from boards
bodies={(b,f['ref']):f for b,fps in inp['ci']['boards'].items() for f in fps}
cases={'JR-K-JR-L04':[('JR','U8314'),('JR','U8318')],'JR-K-JR-L01':[('JR','U4346'),('JR','U4347'),('K','U4324'),('K','U4341')],
 'JR-K-JR-L03':[('JR','U4348')],'JR-K-JR-L02':[('JR','U8417')],'JL-K-JL-L08':[('JL','U1416'),('JL','U1417')],
 'JL-K-JL-L02':[('JL','U1518'),('JL','U2119')],'JL-K-JL-L01':[('JL','U2218')],'JL-K-JL-L07':[('JL','U1216')],
 'JR-K-JR-L06':[('K','U4524'),('K','U4526'),('K','U4527')],'JR-K-JR-L07':[('K','U4635')]}
gap=0.35
def protect_accept(r,prot):
    base=p2.class_accept(r,site_by,limits)
    def acc(geo):
        w=base(geo)
        if w: return w
        for (b,ref) in prot:
            f=bodies[(b,ref)]; cy=sg.grow(f['courtyard'],gap)
            if b==r['front_board']:
                keys=['front_connector','front_tail','slot']
            else:
                keys=['K_connector','K_tail','slot']
            for k in keys:
                if geo.get(k) and sg.inter(geo[k],cy): return 'protected '+ref
        return None
    return acc
res={}
for lid,prot in cases.items():
    r=next(x for x in links if x['id']==lid)
    placed=lg.placed_index(links,skip=(lid,)) if 'skip' in lg.placed_index.__code__.co_varnames else None
    size=lg.rec_size(ctx,r); own=lg.rec_own(r)
    found=None
    for R in (ctx.radius, 2*ctx.radius):
        for g in (2.0,0.5):
            offs=ctx.grid(g,radius=R)
            ctx.model.memo_for(None)
            best,tally=lg.search(ctx,placed,r['front_board'],r['centre'],size,own,offsets=offs,accept=protect_accept(r,prot))
            if best:
                cost,key,geo,disp,d,slot,dist=best
                found={'radius':R,'grid':g,'cost':round(cost,3),'recorded_cost':r['cost'],'slot':slot,'dist':round(dist,2),
                       'displaced':disp,'recorded_displaced':r['displaced']}
                break
        if found: break
    res[lid]=found or {'none':True,'tally':{k:v[0] for k,v in tally.items()}}
    print(lid,flush=True)
out_path=sys.argv[1] if len(sys.argv)>1 else None
if out_path:
    with open(out_path,'x') as fh: json.dump({'status':'LINK_SHIFT_EXPERIMENT','search':'retained lg.search, class-distance accept, radius 24 then 48 mm, grids 2.0/0.5 mm, protected IC courtyards grown 0.35 mm','results':res},fh,indent=1)
print('radius',ctx.radius,time.time()-t)
