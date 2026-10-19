from pathlib import Path
import ast, csv, hashlib, json, re, shutil, zipfile
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
import pypdfium2 as pdfium

STAGE=Path(__file__).resolve().parent.parent
N=STAGE/'gh4-coupon-native'
O=STAGE/'gh4-coupon-jlc-candidate'
O.mkdir(exist_ok=True)
F=O/'fabrication'; F.mkdir(exist_ok=True)
E=O/'evidence'; E.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
before={str(p.relative_to(N)):sha(p) for p in N.rglob('*') if p.is_file()}
for p in (N/'review-only/gerbers').iterdir():
    if p.suffix not in ('.gbrjob','.gbr'):shutil.copyfile(p,F/p.name)
for p in (N/'review-only/drill').glob('*.drl'):shutil.copyfile(p,F/p.name)
(F/'gh4-coupon-V-CUT-SCORE-ONLY.gm2').write_text('''G04 GH4 SUBMISSION CANDIDATE - V-SCORE ONLY - NOT ROUTING*
G04 Two full width scores; see fabrication-drawing.pdf*
G04 Same absolute metric XY frame as perimeter GM1 and drills*
%FSLAX46Y46*%
%MOMM*%
%LPD*%
%ADD10C,0.100000*%
G01*
D10*
X0Y-10000000D02*
X80000000Y-10000000D01*
X0Y-90000000D02*
X80000000Y-90000000D01*
M02*
''',encoding='ascii')
with (O/'BOM.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.writer(f);w.writerow(['Comment','Designator','Footprint','JLCPCB Part #'])
    w.writerow(['BM04B-GHS-TBT(LF)(SN)','J1','JST_GH_BM04B-GHS-TBT_1x04-1MP_P1.25mm_Vertical','C161692'])
native=list(csv.DictReader((N/'review-only/placement-native.csv').open()))
assert len(native)==1 and native[0]['Ref']=='J1'
with (O/'CPL.csv').open('w',newline='',encoding='utf-8') as f:
    w=csv.writer(f);w.writerow(['Designator','Mid X','Mid Y','Rotation','Layer'])
    r=native[0];w.writerow([r['Ref'],r['PosX'],r['PosY'],r['Rot'],r['Side']])

# Reuse only the strict parser function, never execute audit_review.py's writes.
tree=ast.parse((N/'audit_review.py').read_text())
parser=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='gerber')
ns={'re':re};exec(compile(ast.Module(body=[parser],type_ignores=[]),'gerber-parser','exec'),ns)
g=ns['gerber']; ops={p.name:g(p) for p in F.iterdir() if p.suffix!='.drl'}
profile=ops['gh4-coupon-Edge_Cuts.gm1']
assert len(profile)==4 and {p for o in profile for p in o[1:3]}=={(0,0),(80,0),(80,100),(0,100)}
scores=ops['gh4-coupon-V-CUT-SCORE-ONLY.gm2']
assert [(o[1],o[2]) for o in scores]==[((0,10),(80,10)),((0,90),(80,90))]
paste=ops['gh4-coupon-F_Paste.gtp']
expected={(38.125,51.95),(39.375,51.95),(40.625,51.95),(41.875,51.95),(36.275,48.6),(43.725,48.6)}
assert len(paste)==6 and {o[1] for o in paste}==expected
assert [float(native[0][k]) for k in ('PosX','PosY','Rot')]==[40,-50,0]
drill=(F/'gh4-coupon-NPTH.drl').read_text()
assert 'T1C2.000' in drill and set(re.findall(r'^X([^Y]+)Y([^\n]+)$',drill,re.M))=={('15.0','-5.0'),('65.0','-5.0'),('15.0','-95.0')}
for name in ['gerber-review.png','audit.json','netlist.xml','placement-native.csv']:
    shutil.copyfile(N/'review-only'/name,E/name)
for name in ['erc.rpt','drc.rpt','REVIEW.md']:
    shutil.copyfile(N/name,E/('native-'+name))

c=canvas.Canvas(str(O/'fabrication-drawing.pdf'),pagesize=A4)
c.setTitle('GH4 coupon - fabrication and assembly candidate')
W,H=A4
def txt(x,y,s,size=9):
    c.setFont('Helvetica',size);c.drawString(x,y,s)
def heading(sub,page):
    c.setFillColor(HexColor('#143549'));txt(36,H-42,'GH4 COUPON / SUBMISSION CANDIDATE',16)
    txt(36,H-62,sub,10);c.setFillColor(HexColor('#222222'))
    txt(36,26,'Source 537ab6a60272437458f1bfe923ca361c8a2ed09e | 2026-10-18 | '+str(page)+'/2',7)
heading('Fabrication drawing - top view, all dimensions in mm; do not scale',1)
sx,sy,k=100,390,3
def pt(x,y):return sx+x*k,sy+(100-y)*k
c.setStrokeColor(HexColor('#143549'));c.setLineWidth(1)
c.rect(sx,sy,80*k,100*k)
c.setFillColor(HexColor('#e8eef1'));c.rect(sx,sy,80*k,10*k,fill=1);c.rect(sx,sy+90*k,80*k,10*k,fill=1)
c.setStrokeColor(HexColor('#c53f29'));c.setDash(5,3)
for y in (10,90):c.line(*pt(0,y),*pt(80,y))
c.setDash();c.setFillColor(HexColor('#222222'))
for x,y in [(15,5),(65,5),(15,95)]:c.circle(*pt(x,y),k,fill=0)
for x,y in [(5,5),(75,5),(5,95)]:c.circle(*pt(x,y),k/2,fill=1)
for x in (2,70):
    a,b=pt(x,70);c.setDash(2,3);c.rect(a,b,8*k,40*k);c.setDash()
for i,x in enumerate((34,38,42,46),1):
    c.circle(*pt(x,72),k,fill=0);txt(pt(x,72)[0]-5,pt(x,72)[1]-15,'TP'+str(i),6)
cx,cy=pt(40,50);c.rect(cx-4.125*k,cy-1.75*k,8.25*k,4.25*k)
txt(cx-6,cy+13,'J1',8)
for x,y in sorted(expected):c.circle(*pt(x,y),1,fill=1)
txt(sx+75,sy+218,'80 x 80 functional',9)
txt(sx+75,sy+11,'10 mm rail',8);txt(sx+75,sy+281,'10 mm rail',8)
for y,label in [(10,'SCORE y=10 / Y=-10'),(90,'SCORE y=90 / Y=-90')]:
    txt(sx+80*k+8,pt(0,y)[1]-3,label,7)
txt(sx+75,sy+313,'OVERALL WIDTH 80',10)
c.saveState();c.translate(sx-28,sy+100);c.rotate(90);txt(0,0,'OVERALL HEIGHT 100',10);c.restoreState()
lines=[
'1. GM1 is the closed outer routing profile, 80 x 100. No internal routed slots.',
'2. GM2 contains exactly TWO full-span V-scores: x=0..80 at y=10 and y=90.',
'   Score from both faces as the fabricator process requires; retain rails for assembly.',
'   Score stroke width is annotation only, not a slot or cutter width.',
'3. One functional board per unit; two integral 10 mm rails. No additional array/rails.',
'4. Three NPTH tooling holes: diameter 2 at (15,5), (65,5), (15,95).',
'5. Three fiducials: diameter 1 copper / 2 mask at (5,5), (75,5), (5,95).',
'6. Dashed side boxes: clamp reservations x=2..10 / 70..78, y=30..70, both faces.',
'7. Coordinates above use upper-left origin, X right / y down. Manufacturing Y=-y.',
'8. FR-4, 2 layers, 1.6 mm, 1 oz outer copper, green mask, white silk, lead-free HASL.',
'9. Standard Assembly, TOP only; one exact JST BM04B-GHS-TBT(LF)(SN) at J1.',
'10. GM2 recognition and score interpretation must be confirmed in supplier CAM.',
'    No material, scoring tolerance or assembly acceptance is established by this PDF.'
]
for i,s in enumerate(lines):txt(36,342-i*18,s,8.2)
c.showPage();heading('Assembly datum and continuity inspection - top view',2)
c.drawImage(str(E/'gerber-review.png'),40,380,width=260,height=350,preserveAspectRatio=True,anchor='c')
txt(315,695,'CPL: J1 / top / 0 degrees',11)
for i,s in enumerate(['X = 40.000000 mm','Y = -50.000000 mm','No mirror, inversion or offset.','Pin 1 is LEFT in this view.','Signal row below header body.','MP lands above signal row.','Body center: X40, Y-49.625.','CPL uses footprint datum,','not a measured pickup point.']):txt(315,675-18*i,s,9)
lines=[
'The image above is the retained actual-Gerber review render, not a 3D assembly.',
'Its V-cut annotations come from the original review layer; candidate GM2 has only lines.',
'Signal     Gerber X / Y (mm)       Continuity endpoint (Gerber X / Y)',
'J1.1       38.125 / -51.950        TP1   34.000 / -72.000   net GH1',
'J1.2       39.375 / -51.950        TP2   38.000 / -72.000   net GH2',
'J1.3       40.625 / -51.950        TP3   42.000 / -72.000   net GH3',
'J1.4       41.875 / -51.950        TP4   46.000 / -72.000   net GH4',
'Signal lands 0.6 x 1.7; MP lands 1.0 x 2.8 at (36.275,-48.6), (43.725,-48.6).',
'Only J1 is fitted. TP/fiducial/tooling features are bare PCB features, not BOM items.',
'At upload: check exact MPN C161692, pin 1, body, both MP lands and all four signal lands.',
'If supplier model datum/rotation differs, resolve in preview; do not flip Y in isolation.',
'Unpowered only. Physical fit, soldering, continuity and durability remain untested.'
]
for i,s in enumerate(lines):txt(36,350-i*20,s,8.3)
c.save()
pdf=pdfium.PdfDocument(str(O/'fabrication-drawing.pdf'))
for i in range(len(pdf)):pdf[i].render(scale=1.5).to_pil().save(E/f'fabrication-drawing-page-{i+1}.png')

assert before=={str(p.relative_to(N)):sha(p) for p in N.rglob('*') if p.is_file()},'Original changed'
receipt={'source_commit':'537ab6a60272437458f1bfe923ca361c8a2ed09e','status':'SUBMISSION_CANDIDATE_NOT_UPLOADED','native_directory_unchanged':True,'native_files_hashed':len(before),'coordinate_transform':'identity; CSV headers only; Gerber/drills/CPL all absolute metric Y-up','CPL':{'J1':[40,-50,0,'top']},'outline_mm':[80,100],'functional_mm':[80,80],'rail_width_mm':10,'score_lines_Gerber':[[0,-10,80,-10],[0,-90,80,-90]],'paste_apertures':6,'npth_count':3,'source_native_hashes':before,'checks':['Closed four-segment outer contour','Two full-width score-only lines','Six exact J1 paste centers','Native CPL unchanged values','Three metric 2 mm NPTH coordinates','Original review-only files unchanged'],'limitations':['Strict linear/flash parser, not full CAM','Supplier GM2 recognition not tested','Supplier part model rotation/datum not tested','No upload, order or physical test']}
(E/'package-checks.json').write_text(json.dumps(receipt,indent=2)+'\n',encoding='utf-8')
print(O)

