"""Read-only native S-expression audit; geometric screens are conservative AABBs."""
from collections import Counter
import hashlib,math,re,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5];sys.path.insert(0,str(ROOT));sys.path.insert(0,str(ROOT/'scripts/architecture278'))
from scripts.pcbgen.uuid_tools import top_level_spans
from populated_mechanics import sexpr,field

def digest(s):return hashlib.sha256(s.encode()).hexdigest()
def box(points):return [min(p[0] for p in points),min(p[1] for p in points),max(p[0] for p in points),max(p[1] for p in points)]
def turn(x,y,angle):
    a=math.radians(angle);return [x*math.cos(a)+y*math.sin(a),-x*math.sin(a)+y*math.cos(a)]
def point(xy,origin,angle):
    x,y=turn(*xy,angle);return [round(origin[0]+x-100,6),round(origin[1]+y-50,6)]
def corners(x,y,w,h,angle):return [[x+a,y+b] for a,b in [turn(a,b,angle) for a in (-w/2,w/2) for b in (-h/2,h/2)]]
def parse(text):
    items=[];fps={};copper=[];zones=[];ids=Counter()
    for index,(start,end) in enumerate(top_level_spans(text)):
        raw=text[start:end];kind=re.match(r'\((\w+)',raw)[1]
        # Parse each item separately: filled zone polygons need no geometry tree.
        if kind=='zone':
            direct=[raw[a:b] for a,b in top_level_spans(raw)]
            definition='\n'.join(v for v in direct if not v.startswith('(filled_polygon') and not v.startswith('(filled_areas_thickness'))
            node=sexpr('(zone '+definition+')')
        else:node=sexpr(raw)
        uid=(field(node,'uuid') or [None])[0];ids[(kind,uid)]+=1
        ident={'index':index,'kind':kind,'uuid':uid,'occurrence':ids[(kind,uid)],'sha256':digest(raw)};items.append(ident)
        if kind=='footprint':
            refs=[n[2] for n in node if isinstance(n,list) and n[:2]==['property','Reference']]
            if len(refs)!=1 or refs[0] in fps:raise ValueError('missing/duplicate footprint ref')
            at=field(node,'at');origin=list(map(float,at[:2]));angle=float(at[2]) if len(at)>2 else 0;layer=field(node,'layer')[0]
            pads=[];courtyard=[]
            for p in node:
                if not isinstance(p,list) or not p:continue
                if p[0] in ('fp_line','fp_rect') and (field(p,'layer') or [''])[0].endswith('.CrtYd'):
                    a,b=[list(map(float,field(p,k))) for k in ('start','end')]
                    vertices=[a,b] if p[0]=='fp_line' else [[x,y] for x in (a[0],b[0]) for y in (a[1],b[1])]
                    courtyard.extend(point(v,origin,angle) for v in vertices)
                if p[0]!='pad':continue
                at=field(p,'at');xy=point(list(map(float,at[:2])),origin,angle);pa=float(at[2]) if len(at)>2 else 0
                w,h=map(float,field(p,'size'));net=(field(p,'net') or [None])[0]
                if p[3] not in ('rect','roundrect','oval','circle'):raise ValueError('unsupported native pad shape '+p[3])
                pads.append({'pin':p[1],'uuid':(field(p,'uuid') or [None])[0],'type':p[2],'shape':p[3],'xy':xy,'size':[w,h],'angle':pa,'box':box(corners(*xy,w,h,pa)),'layers':field(p,'layers'),'net':net})
            fps[refs[0]]={**ident,'ref':refs[0],'library':node[1],'origin':[origin[0]-100,origin[1]-50],'native_angle':angle,'layer':layer,'box':box(courtyard) if courtyard else None,'pads':pads,'locked':field(node,'locked')==['yes']}
        elif kind in ('segment','via','arc'):
            net=(field(node,'net') or [None])[0]
            if kind=='arc':raise ValueError('track arc unsupported for source intersection screen')
            if kind=='segment':
                pts=[[float(v)-d for v,d in zip(field(node,k),(100,50))] for k in ('start','end')];width=float(field(node,'width')[0]);layers=field(node,'layer')
            else:
                pts=[[float(v)-d for v,d in zip(field(node,'at'),(100,50))]];width=float(field(node,'size')[0]);layers=field(node,'layers')
            b=box(pts);b=[b[0]-width/2,b[1]-width/2,b[2]+width/2,b[3]+width/2]
            copper.append({**ident,'net':net,'points':pts,'width':width,'layers':layers,'box':b})
        elif kind=='zone':
            net=(field(node,'net') or [None])[0];layers=field(node,'layers') or field(node,'layer');poly=field(node,'polygon');pts=[]
            if poly:
                ps=field(poly,'pts')
                if ps:pts=[[float(p[1])-100,float(p[2])-50] for p in ps]
            zones.append({**ident,'net':net,'layers':layers,'is_keepout':field(node,'keepout') is not None,'outline':pts,'definition_sha256':digest(definition),'filled_polygon_count':sum(v.startswith('(filled_polygon') for v in direct)})
    return {'board_sha256':digest(text),'items':items,'footprints':fps,'copper':copper,'zones':zones,'counts':dict(Counter(i['kind'] for i in items)),'duplicate_copper_uuids':{u:n for (k,u),n in ids.items() if k in ('segment','via','arc') and n>1}}


def obstacles(n,old,layer):
    pk=old['A']['packages_B1'];owned=set(pk)|{q['B2_ref'] for q in pk.values()}
    fixed={r for r,q in pk.items() if q['panel']}|{q['B2_ref'] for q in pk.values() if q['panel']}
    def ov(a,b):return a[0]<b[2] and b[0]<a[2] and a[1]<b[3] and b[1]<a[3]
    region=[7,118,73,164];rows=[]
    for r,q in n['footprints'].items():
        if not q['box'] and region[0]-10<=q['origin'][0]<=region[2]+10 and region[1]-10<=q['origin'][1]<=region[3]+10 and not (q['pads'] and all(p['type']=='np_thru_hole' for p in q['pads'])):
            raise ValueError('unknown nearby courtyard '+r)
        if (r not in owned or r in fixed) and q['box'] and q['layer']==layer and ov(q['box'],region):rows.append({'id':r+':courtyard','box':q['box'],'source':'native footprint'})
        for pad in q['pads']:
            if pad['type'] in ('thru_hole','np_thru_hole'):
                b=pad['box'];b=[b[0]-.5,b[1]-.5,b[2]+.5,b[3]+.5]
                if ov(b,region):rows.append({'id':r+':'+pad['pin']+':terminal','box':b,'source':'native pad +0.5mm XY reservation; tail depth unknown'})
    for z in n['zones']:
        if z['is_keepout'] and (layer in z['layers'] or '*.Cu' in z['layers']) and z['outline']:
            b=box(z['outline'])
            if ov(b,region):rows.append({'id':z['uuid'],'box':b,'source':'native rule-area conservative rectangle'})
    for h in old['A']['retained_mounts']:
        if ov(h['tool_trial_xy'],region):rows.append({'id':h['id'],'box':h['tool_trial_xy'],'source':'retained mount +8mm tool trial'})
    return rows
