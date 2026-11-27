import sys, math, json
sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from lib import *
HEAD='80569b5375087df519b79ead67d1bf56c16301e6'
G='design/stack/geometry/links/link-gate.json'; LR='design/stack/geometry/links/link-era-replacements.json'
OVP='scripts/stack/studies/mc04_s10_l13/overlay.json'
pins={(p['board'],p['ref']):p for p in gjson(HEAD,'design/partition/floorplan-candidate.json')['placements']}
pins0={(p['board'],p['ref']):p for p in gjson('6e5716e7','design/partition/floorplan-candidate.json')['placements']}
print('floorplan placements identical 6e5716e7 vs HEAD:', {k:(v['x_mm'],v['y_mm'],v['side'],v['rotation_deg']) for k,v in pins.items()}=={k:(v['x_mm'],v['y_mm'],v['side'],v['rotation_deg']) for k,v in pins0.items()})
io=gjson(HEAD,'design/reports/io-partition.json')
refpins={}; netrefs={}
for u in io['package_units']:
    for pin,n in u['pins'].items():
        if n: refpins.setdefault(u['ref'],{})[pin]=n; netrefs.setdefault(n,set()).add(u['ref'])
buf_ics={u['ref'] for u in io['package_units'] if (u.get('role') or '').startswith(('high_impedance_input','remote_buffer')) and u['ref'].startswith('U')}
SUF=('_FB','_SUM','_SENSE')
def prot(ref):
    return sorted({n for n in refpins.get(ref,{}).values() if n.endswith(SUF)})
def rows(sha): return {(f['board'],f['ref']):f for f in gjson(sha,G)['replacement']['footprints']}
R={s:rows(s) for s in ['6e5716e7','32580f77','557b5a6e',HEAD]}
strip=lambda rr:{k:(v['new'],v['new_face'],v['turned'],v['step']) for k,v in rr.items()}
print('gate rows equal 32580f77==557b5a6e:',strip(R['32580f77'])==strip(R['557b5a6e']),' ==HEAD:',strip(R['32580f77'])==strip(R[HEAD]), 'full equal', R['32580f77']==R['557b5a6e'], R['32580f77']==R[HEAD])
pre,cand=R['6e5716e7'],R['32580f77']
removed=[k for k in pre if k not in cand]; new=[k for k in cand if k not in pre]
shifted=[k for k in cand if k in pre and (pre[k]['new'],pre[k]['new_face'],pre[k]['turned'])!=(cand[k]['new'],cand[k]['new_face'],cand[k]['turned'])]
print('row changes removed/new/shifted',len(removed),len(new),len(shifted))
def rot(p,o,deg):
    a=math.radians(deg); dx,dy=p[0]-o[0],p[1]-o[1]
    return (o[0]+dx*math.cos(a)-dy*math.sin(a), o[1]+dx*math.sin(a)+dy*math.cos(a))
def scene(rr,placements):
    sc={k:([v['x_mm'],v['y_mm']],v['side'][0],'paper',0) for k,v in pins.items()}
    for k,r in rr.items():
        sc[k]=(r['new'],r['new_face'],'gate row' if r['new'] else 'no position',90 if r['turned'] else 0)
    def place(b,ic,members,pose,tag):
        if not pose: return
        o=(pins[b,ic]['x_mm'],pins[b,ic]['y_mm'])
        for ref in members:
            p=(pins[b,ref]['x_mm'],pins[b,ref]['y_mm'])
            if pose['face']!=pins[b,ic]['side'][0]: p=(2*o[0]-p[0],p[1])
            x,y=rot(p,o,pose['turn_deg'])
            same=pins[b,ref]['side']==pins[b,ic]['side']
            face=pose['face'] if same else {'F':'B','B':'F'}[pose['face']]
            sc[b,ref]=([x+pose['shift_mm'][0],y+pose['shift_mm'][1]],face,f'{ic} block',pose['turn_deg'])
    for e in placements:
        b=e['board']; place(b,e['ic'],e.get('members') or e['block'],e['pose'],e['ic'])
        for bl in e.get('blocks_moved',[]): place(b,bl['ic'],bl['members'],bl,bl['ic'])
        for m in e['passives_moved']: sc[b,m['ref']]=(m['origin'],m['face'],f"{e['ic']} displaced passive",0)
    return sc
lr_pre=gjson('6e5716e7',LR); lr_head=gjson(HEAD,LR); lr_c=gjson('32580f77',LR)
print('placed ICs pre',[p['ic'] for p in lr_pre['placed']]); print('placed ICs HEAD',[p['ic'] for p in lr_head['placed']],'at 32580f77',[p['ic'] for p in lr_c['placed']])
print('placed poses equal pre vs HEAD', [(p['ic'],p['pose']) for p in lr_pre['placed']]==[(p['ic'],p['pose']) for p in lr_head['placed']])
print('open pre',[o['ic'] for o in lr_pre['open']],'open HEAD',[o['ic'] for o in lr_head['open']], 'withheld',lr_head['s10']['withheld_overlay_ics'])
print('no position pre',sorted(k[1] for k,v in pre.items() if v['new'] is None),'cand',sorted(k[1] for k,v in cand.items() if v['new'] is None))
ov=gjson(HEAD,OVP); ovc=gjson('32580f77',OVP)
print('overlay blocks HEAD',[(b['ic'],b['pose'],b['passives_moved']) for b in ov['blocks']])
print('overlay blocks 32580f77 keys',list(ovc.keys()))
S_pre=scene(pre,lr_pre['placed'])
S_gate=scene(cand,lr_head['placed'])
S_cand=scene(cand,lr_head['placed']+ov['blocks'])
def diff(A,B):
    out=[]
    for k in sorted(B):
        a,b=A[k],B[k]
        pa,pb=a[0],b[0]
        same=(pa is None and pb is None) or (pa is not None and pb is not None and math.dist(pa,pb)<1e-9)
        if not same or a[1]!=b[1]: out.append((k,a,b,'pos'))
        elif a[3]!=b[3]: out.append((k,a,b,'turn-only'))
    return out
D=diff(S_pre,S_cand)
print('effective movements pre->cand:',len([d for d in D if d[3]=='pos']),'turn-only',[d[0] for d in D if d[3]=='turn-only'],'face changes',len([d for d in D if d[1][1]!=d[2][1]]))
print('recorded effective_movements',len(ov['effective_movements']),'face',len(ov['face_changes']))
mine={d[0][1] for d in D if d[3]=='pos'}; rec={m['ref'] for m in ov['effective_movements']}
print('set diff mine-rec',mine-rec,'rec-mine',rec-mine)
json.dump({'pre':{f'{k[0]}/{k[1]}':v for k,v in S_pre.items()},'gate':{f'{k[0]}/{k[1]}':v for k,v in S_gate.items()},'cand':{f'{k[0]}/{k[1]}':v for k,v in S_cand.items()}},open(__import__('os').path.join(__import__('os').environ.get('OSC_REVIEW_OUT','/tmp'),'scenes.json'),'w'))
print('\n## protected parts whose effective pose changes pre->cand')
def cls(k):
    if k in new: return 'NEW row'
    if k in shifted: return 'SHIFTED row'
    if k in removed: return 'row REMOVED'
    return 'overlay'
for k,a,b,kind in D:
    ref=k[1]; pn=prot(ref)
    if pn or ref in buf_ics:
        pp=pins[k]; paper=([pp['x_mm'],pp['y_mm']],pp['side'][0])
        mv=None if a[0] is None or b[0] is None else round(math.dist(a[0],b[0]),3)
        back = b[0] is not None and math.dist(b[0],paper[0])<1e-9 and b[1]==paper[1]
        print(k[1],cls(k),'buffer IC' if ref in buf_ics else pn,'paper',paper,'pre',a[:3],'cand',b[:3],'moved',mv,'-> back at paper' if back else '', kind)
