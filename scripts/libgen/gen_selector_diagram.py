#!/usr/bin/env python3
"""Draw dimensioned nominal keepouts from the selector assembly source, not styling art."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
A=json.loads((ROOT/'design/mechanical/selector-assembly.json').read_text())
P={p['uid']:p for p in json.loads((ROOT/'design/grid/placements.lock.json').read_text())['placements']}
s=['<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="780" viewBox="0 0 1100 780">',
'<rect width="1100" height="780" fill="#fff"/>',
'<style>text{font-family:Arial,sans-serif;fill:#18222c} .label{font-size:15px} .small{font-size:13px} .title{font-size:23px;font-weight:bold} line,path{stroke:#536270;stroke-width:1.2} .front{fill:#c8e4f5;stroke:#207aa8;stroke-width:1.5} .rear{fill:#ffe1b8;stroke:#b96b09;stroke-width:1.5}</style>',
'<text x="34" y="35" class="title">SRBV160803: fixed centres, stepped 3 + 2 adapters</text>',
'<text x="34" y="61" class="label">UNVALIDATED CONDITIONAL DRAFT • conservative keepouts, not exact solids • all dimensions mm</text>']
def text(x,y,t,cls='label'):s.append(f'<text x="{x}" y="{y}" font-family="Arial,sans-serif" font-size="{13 if cls=='small' else 15}" fill="#18222c">{t}</text>')
def rect(x,y,w,h,cls):s.append(f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="{'#c8e4f5' if cls=='front' else '#ffe1b8'}" stroke="{'#207aa8' if cls=='front' else '#b96b09'}" stroke-width="1.5"/>')
def line(x1,y1,x2,y2):s.append(f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="#536270" stroke-width="1.2"/>')
scale=7
text(34,95,'FRONT PROJECTION — blue front plane / amber rear plane')
for i in A['instances']:
 p=P[i['uid']];cx=140+(p['x_mm']-14.5)*scale;cy=205
 x0,y0,x1,y1=A['drawing']['conservative_body_support_xy_mm']
 if i['rotation_deg']==180:y0,y1=-y1,-y0
 cls='front' if i['adapter_group']=='front' else 'rear'
 rect(cx+x0*scale,cy+y0*scale,(x1-x0)*scale,(y1-y0)*scale,cls)
 s.append(f'<circle cx="{cx}" cy="{cy}" r="{A['panel']['aperture_diameter_mm']/2*scale}" fill="white" stroke="#18222c"/>')
 line(cx-7,cy,cx+7,cy);line(cx,cy-7,cx,cy+7)
 text(cx-25,120,i['uid'][2:4]+' '+str(i['rotation_deg'])+'°','small')
 text(cx-22,300,'x='+str(p['x_mm']),'small')
 if p['x_mm']<82.5:
  line(cx,322,cx+17*scale,322);line(cx,317,cx,327);line(cx+119,317,cx+119,327);text(cx+47,341,'17','small')
text(760,146,'Shaft row y = 185')
text(760,172,'Front Ø7 ±0.1; carrier Ø9.5 ±0.1')
text(760,198,'Body y: −10.5 / +8 from shaft')
text(760,224,'18.2 support span retained')
text(760,250,'Adjacent XY projections overlap;')
text(760,272,'the selected Z planes separate them.')
text(34,377,'ELEVATION THROUGH SHAFT ROW — panel front z = 0, positive toward user')
yzero=485
line(60,yzero,715,yzero);text(760,yzero+5,'Panel front z = 0')
for i in A['instances']:
 p=P[i['uid']];cx=140+(p['x_mm']-14.5)*scale;z=i['pcb_z_mm'];cls='front' if i['adapter_group']=='front' else 'rear'
 rect(cx-9.1*scale,yzero-(z+7.5)*scale,18.2*scale,11.5*scale,cls)
 rect(cx-4.5*scale,yzero-(z+14.5)*scale,9*scale,7*scale,cls)
 rect(cx-3*scale,yzero-(z+22.5)*scale,6*scale,8*scale,cls)
 rect(cx-7.5*scale,yzero-(z+9.5)*scale,15*scale,2*scale,cls)
 if i['extension_length_mm']:
  rect(cx-5*scale,yzero-(z+22.5)*scale,10*scale,6.5*scale,cls)
  rect(cx-3*scale,yzero-(z+35.5)*scale,6*scale,13*scale,cls)
 rect(cx-4*scale,yzero-10*scale,8*scale,9*scale,cls)
 line(cx-10*scale,yzero-z*scale,cx+10*scale,yzero-z*scale)
text(760,523,'PCB faces: −16 / −29')
text(760,550,'Plane step: 13')
text(760,577,'Full envelope depth: 11.5')
text(760,604,'Nominal Z clearance: 1.5')
text(760,631,'Ø8 knobs; 13 mm extensions')
text(760,658,'Carrier and retention: NEEDS BENCH')
text(34,751,'Physical qualification: issue #55 • actual tolerances, indexing, loads, nearby hardware and tool access NOT RUN','small')
s.append('</svg>')
(ROOT/'doc/public/assets/osc-hole-field/selector-assembly.svg').write_text('\n'.join(s)+'\n')
print('Generated selector assembly diagram')
