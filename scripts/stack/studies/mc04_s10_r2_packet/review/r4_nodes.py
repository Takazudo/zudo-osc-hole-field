import sys, math, json
sys.path.insert(0,__import__('os').path.dirname(__import__('os').path.abspath(__file__)))
from lib import *
HEAD='80569b5375087df519b79ead67d1bf56c16301e6'
sc=json.load(open(__import__('os').path.join(__import__('os').environ.get('OSC_REVIEW_OUT','/tmp'),'scenes.json')))
fpl={(p['board'],p['ref']):p for p in gjson(HEAD,'design/partition/floorplan-candidate.json')['placements']}
io=gjson(HEAD,'design/reports/io-partition.json')
refpins={}; netpins={}
for u in io['package_units']:
    for pin,n in u['pins'].items():
        if n: refpins.setdefault(u['ref'],{})[pin]=n; netpins.setdefault(n,set()).add((u['ref'],pin))
fps,_,_,_,_=board(open(REPO+'/boards/osc-core/osc-core.kicad_pcb').read())
bad=[r for r,f in fps.items() if ('K',r) in fpl and (abs(f['at'][0]-100-fpl['K',r]['x_mm'])>1e-4 or abs(f['at'][1]-50-fpl['K',r]['y_mm'])>1e-4)]
print('K board footprints',len(fps),'not at floorplan pose:',len(bad),bad[:10])
def rot90(p,k):
    x,y=p
    for _ in range(int(k)//90): x,y=-y,x
    return x,y
def pad(scn,ref,pin):
    pos,face,src,turn=sc[scn]['K/'+ref]
    if pos is None: return None
    f=fps[ref]; px,py,_=f['pads'][pin][0]
    dx,dy=px-f['at'][0],py-f['at'][1]
    if face!=f['layer'][0]: dx=-dx
    dx,dy=rot90((dx,dy),turn)
    return pos[0]+dx,pos[1]+dy
def paperpad(ref,pin):
    f=fps[ref]; px,py,_=f['pads'][pin][0]; return px-100,py-50
def hp(pts):
    if any(p is None for p in pts): return None
    xs=[p[0] for p in pts]; ys=[p[1] for p in pts]; return round(max(xs)-min(xs)+max(ys)-min(ys),3)
T=[('R5249','/W1/FOLDER_SUM','U5209','9'),('R5256','/W1/F2_SUM','U5210','6'),('R8221','/M5B/Ca92eeb_W_SENSE','U8208','12'),('R8331','/M4A/C38051c_W_SENSE','U8310','5'),('R8356','/M4A/C24ce01_W_SENSE','U8311','10'),('R4238','/E2/REF9_FB','U4240','2'),
   ('R8431','/M4B/C38051c_W_SENSE',None,None),('R5148','/W2/FOLDER_SUM',None,None),('R5253','/W1/F1_SUM',None,None),('C8405','/M4B/Cfaa69a_FB',None,None)]
for ref,net,ic,icpin in T:
    np_=sorted(netpins[net]); onK=[(r,p) for r,p in np_ if r in fps]; off=[(r,p) for r,p in np_ if r not in fps]
    h=[hp([paperpad(r,p) for r,p in onK])]+[hp([pad(s,r,p) for r,p in onK]) for s in('pre','cand')]
    line=f'{ref} {net} pins={len(np_)} (offK {off}) HPWL paper/pre/cand {h}'
    if ic:
        mypin=[p for p,n in refpins[ref].items() if n==net][0]
        assert refpins[ic].get(icpin)==net,(ic,icpin,refpins[ic])
        d=[round(math.dist(paperpad(ref,mypin),paperpad(ic,icpin)),3)]+[ (round(math.dist(pad(s,ref,mypin),pad(s,ic,icpin)),3) if pad(s,ic,icpin) else None) for s in ('pre','cand')]
        line+=f' | {ref}.{mypin}->{ic}.{icpin} paper/pre/cand {d}'
    print(line); print('    members',[(r,sc['pre']['K/'+r][:3],sc['cand']['K/'+r][:3]) for r,p in onK if sc['pre']['K/'+r][:2]!=sc['cand']['K/'+r][:2]])
# F2 pads in candidate
for a,b in [(('R5257','2'),('U5210','6')),(('R5257','1'),('U5210','7'))]:
    print(a,b,'cand',round(math.dist(pad('cand',*a),pad('cand',*b)),3))
print('centre R5257-U5210 cand',math.dist(sc['cand']['K/R5257'][0],sc['cand']['K/U5210'][0]), sc['cand']['K/R5257'],sc['cand']['K/U5210'],sc['cand']['K/R5259'])
# which nets with protected suffix have ANY pad geometry change pre->cand or paper->cand
SUF=('_FB','_SUM','_SENSE')
print('\n## all protected-suffix nets on K with member pose change pre->cand')
for net in sorted(netpins):
    if not net.endswith(SUF): continue
    onK=[(r,p) for r,p in netpins[net] if r in fps and 'K/'+r in sc['cand']]
    ch=sorted({r for r,p in onK if sc['pre']['K/'+r][:2]!=sc['cand']['K/'+r][:2]})
    if ch:
        print(net,'changed',ch,'HPWL paper/pre/cand',hp([paperpad(r,p) for r,p in onK]),hp([pad('pre',r,p) for r,p in onK]),hp([pad('cand',r,p) for r,p in onK]))
