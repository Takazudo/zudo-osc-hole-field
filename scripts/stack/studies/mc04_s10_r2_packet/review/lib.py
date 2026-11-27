import json, subprocess, math, re
REPO=__import__('os').environ.get('OSC_REPO') or str(__import__('pathlib').Path(__file__).resolve().parents[5])
def gshow(sha,path):
    return subprocess.run(['git','-C',REPO,'show',f'{sha}:{path}'],capture_output=True,check=True).stdout
def gjson(sha,path): return json.loads(gshow(sha,path))
def sexp(text):
    tok=re.compile(r'\(|\)|"(?:\\.|[^"\\])*"|[^\s()]+')
    stack=[[]]
    for m in tok.finditer(text):
        t=m.group(0)
        if t=='(':
            n=[]; stack[-1].append(n); stack.append(n)
        elif t==')': stack.pop()
        elif t[0]=='"': stack[-1].append(t[1:-1])
        else: stack[-1].append(t)
    return stack[0][0]
def child(n,name): 
    for c in n:
        if isinstance(c,list) and c and c[0]==name: return c
def children(n,name): return [c for c in n if isinstance(c,list) and c and c[0]==name]
def board(text):
    """returns fps{ref:{at,rot,layer,pads{num:[(x,y,net)]}}}, segments, vias"""
    b=sexp(text)
    fps={}
    for f in children(b,'footprint'):
        at=child(f,'at'); x,y=float(at[1]),float(at[2]); rot=float(at[3]) if len(at)>3 else 0.0
        layer=child(f,'layer')[1]
        ref=None
        for p in children(f,'property'):
            if p[1]=='Reference': ref=p[2]
        pads={}
        for p in children(f,'pad'):
            pa=child(p,'at'); px,py=float(pa[1]),float(pa[2])
            a=math.radians(rot)
            # KiCad: pad pos in footprint frame rotated by -rot (y down)
            gx=x+px*math.cos(a)+py*math.sin(a)
            gy=y-px*math.sin(a)+py*math.cos(a)
            net=child(p,'net'); nn=net[-1] if net else None
            pads.setdefault(p[1],[]).append((gx,gy,nn))
        fps[ref]=dict(at=(x,y),rot=rot,layer=layer,pads=pads,fpname=f[1])
    segs=[];vias=[]
    for s in children(b,'segment'):
        st=child(s,'start');en=child(s,'end');net=child(s,'net')
        segs.append(((float(st[1]),float(st[2])),(float(en[1]),float(en[2])),child(s,'layer')[1],net[-1],float(child(s,'width')[1])))
    for s in children(b,'arc'):
        segs.append(('ARC',s))
    for v in children(b,'via'):
        at=child(v,'at');net=child(v,'net')
        vias.append(((float(at[1]),float(at[2])),net[-1]))
    nets={n[1]:n[2] for n in children(b,'net') if len(n)>2}
    zones=children(b,'zone')
    return fps,segs,vias,nets,zones
