"""Audit exported netlist/placement/drill/Gerbers; render the supported Gerber primitives.

This intentionally rejects arcs, regions and unknown geometry instead of silently
rendering an approximation. It is a review aid, not a general CAM validator.
"""
from pathlib import Path
import csv, hashlib, json, re, sys, xml.etree.ElementTree as ET
from PIL import Image, ImageDraw
OUT=Path(__file__).resolve().parent
R=OUT/'review-only'
ROOT=OUT.parents[4]
sys.path.insert(0,str(ROOT))
from scripts.schgen.core import parse,tokens,children
def one(n,k):return children(n,k)[0]
b,end=parse(tokens((OUT/'gh4-coupon.kicad_pcb').read_text()))
fps={one(f,'property')[2]:f for f in children(b,'footprint')}
assert len(fps)==11
assert [float(x) for x in one(fps['J1'],'at')[1:3]]==[40,50]
for i in range(1,5):
    j=next(z for z in children(fps['J1'],'pad') if z[1]==str(i))
    assert one(j,'net')[-1]==f'GH{i}'
    tp=children(fps[f'TP{i}'],'pad')[0]
    assert one(tp,'net')[-1]==f'GH{i}'
    assert 'F.Paste' not in one(tp,'layers')
assert all(not children(z,'net') or one(z,'net')[-1] in ('0','') for z in children(fps['J1'],'pad') if z[1]=='MP')
tracks=children(b,'segment')
assert len(tracks)==12 and all(one(t,'width')[1]=='0.25' and one(t,'layer')[1]=='F.Cu' for t in tracks)
netlist=ET.parse(R/'netlist.xml').getroot()
actual={n.attrib['name']:{(x.attrib['ref'],x.attrib['pin']) for x in n.findall('node')} for n in netlist.findall('nets/net')}
assert actual=={f'GH{i}':{('J1',str(i)),(f'TP{i}','1')} for i in range(1,5)},actual
rows=list(csv.DictReader((R/'placement-native.csv').open()))
assert len(rows)==1 and rows[0]['Ref']=='J1' and rows[0]['Side']=='top'
assert [float(rows[0][x]) for x in ['PosX','PosY','Rot']]==[40,-50,0]
drill=(R/'drill/gh4-coupon-NPTH.drl').read_text()
assert 'T1C2.000' in drill
assert set(re.findall(r'^X([^Y]+)Y([^\n]+)$',drill,re.M))=={('15.0','-5.0'),('65.0','-5.0'),('15.0','-95.0')}
assert not re.findall(r'^X', (R/'drill/gh4-coupon-PTH.drl').read_text(),re.M)
with (R/'bom-review-only.csv').open('w',newline='') as f:
    w=csv.writer(f);w.writerow(['Reference','Quantity_per_board','Manufacturer','MPN','Supplier_code','Status']);w.writerow(['J1',1,'JST','BM04B-GHS-TBT(LF)(SN)','C161692','REVIEW ONLY - NOT RELEASED'])

def gerber(path):
    data=path.read_text();aps={};ops=[];pos=None;ap=None
    assert '%FSLAX46Y46*%' in data and '%MOMM*%' in data
    assert not re.search(r'^G(?:02|03|36|37)',data,re.M)
    for n,kind,params in re.findall(r'%ADD(\d+)([^,*]+),([^*]+)\*%',data):
        a=list(map(float,params.split('X')))
        if kind=='C':spec=('circle',a[0],a[0],a[0]/2)
        elif kind=='R':spec=('rect',a[0],a[1],0)
        elif kind=='RoundRect':
            r=a[0];xs=a[1:9:2];ys=a[2:9:2];assert a[9]==0
            spec=('roundrect',max(xs)-min(xs)+2*r,max(ys)-min(ys)+2*r,r)
        else:raise ValueError('Unsupported aperture '+kind)
        aps[int(n)]=spec
    for s in data.splitlines():
        if re.fullmatch(r'D\d+\*',s):ap=int(s[1:-1]);continue
        m=re.fullmatch(r'X(-?\d+)Y(-?\d+)D0([123])\*',s)
        if m:
            xy=(int(m[1])/1e6,-int(m[2])/1e6);code=int(m[3])
            if code==1:
                assert pos is not None and aps[ap][0]=='circle'
                ops.append(('line',pos,xy,aps[ap]))
            elif code==3:ops.append(('flash',xy,xy,aps[ap]))
            pos=xy
        elif s.startswith(('X','Y')):raise ValueError('Unsupported coordinate '+s)
    return ops
ops={p.name:gerber(p) for p in (R/'gerbers').glob('*') if p.suffix!='.gbrjob'}
paste=ops['gh4-coupon-F_Paste.gtp']
assert len(paste)==6 and all(o[0]=='flash' for o in paste)
assert set(o[1] for o in paste)=={(38.125,51.95),(39.375,51.95),(40.625,51.95),(41.875,51.95),(36.275,48.6),(43.725,48.6)}
assert not ops['gh4-coupon-B_Paste.gbp'] and not ops['gh4-coupon-B_Cu.gbl']
assert len(ops['gh4-coupon-Edge_Cuts.gm1'])==4
assert all(o[0]=='line' for o in ops['gh4-coupon-Edge_Cuts.gm1'])
fcu=ops['gh4-coupon-F_Cu.gtl'];mask=ops['gh4-coupon-F_Mask.gts']
assert len([x for x in fcu if x[0]=='flash'])==13 # 6 header +4 TP +3 fiducials
for xy in [(5,5),(75,5),(5,95)]:
    assert any(o[0]=='flash' and o[1]==xy and abs(o[3][1]-2)<1e-6 for o in mask)
def draw_ops(im,items,color,box,scale,offset=(0,0)):
    d=ImageDraw.Draw(im)
    def xy(p):return ((p[0]-box[0])*scale+offset[0],(p[1]-box[1])*scale+offset[1])
    for kind,a,z,spec in items:
        if kind=='line':
            width=max(1,round(spec[1]*scale));d.line([xy(a),xy(z)],fill=color,width=width)
        else:
            x,y=xy(a);w,h,r=[u*scale for u in spec[1:]];rect=(x-w/2,y-h/2,x+w/2,y+h/2)
            if spec[0]=='circle':d.ellipse(rect,fill=color)
            else:d.rounded_rectangle(rect,radius=r,fill=color)
im=Image.new('RGB',(1200,1200),'#16232b');d=ImageDraw.Draw(im)
d.text((20,10),'ACTUAL GERBER REVIEW - NOT RELEASED',fill='white')
for name,color in [('gh4-coupon-F_Mask.gts','#48646a'),('gh4-coupon-F_Cu.gtl','#e3ad57'),('gh4-coupon-F_Silkscreen.gto','white'),('gh4-coupon-Edge_Cuts.gm1','#c7dddd'),('gh4-coupon-V-CUT-REVIEW.gbr','#55b9e9')]:
    draw_ops(im,ops[name],color,(0,0,80,100),10,(25,50))
for x,y in [(15,5),(65,5),(15,95)]:d.ellipse((25+x*10-10,50+y*10-10,25+x*10+10,50+y*10+10),fill='#020508',outline='white')
d.text((865,80),'J1 paste detail',fill='white')
draw_ops(im,paste,'#e298f4',(35,46,45,55),30,(850,110))
d.text((865,440),'Six apertures only',fill='white')
d.text((865,470),'J1 pin 1 is left',fill='white')
im.save(R/'gerber-review.png')
summary={'status':'PASS_NATIVE_EXPORT_AUDIT_REVIEW_ONLY','schematic_nets':{k:sorted(v) for k,v in actual.items()},'placement_native':rows,'npth_count':3,'paste_apertures':6,'top_copper_flash_count':13,'pairwise_distinct_nets':6,'tool':'KiCad 10.0.6; explicit limited Gerber parser','native_hashes':{p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.glob('gh4-coupon.kicad_*') if p.suffix != '.kicad_prl'}}
(R/'audit.json').write_text(json.dumps(summary,indent=2)+'\n')
print(json.dumps(summary,indent=2))
