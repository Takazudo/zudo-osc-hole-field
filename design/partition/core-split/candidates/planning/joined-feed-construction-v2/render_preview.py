#!/usr/bin/env python3
"""Review drawing from actual emitted solids and frozen curve; no acceptance role."""
import argparse,html,json
from pathlib import Path
import numpy as np
from scipy.spatial import ConvexHull
import check_geometry as ck

def render(candidate,out):
 m=ck.read(candidate/'mechanical.json.gz');terms=ck.read(candidate/'terminals.json');F=ck.rc.Family();v0=np.array(F.direction);v1=v0*[1,-1,1];bridge=2/-v0[2]
 parts=['<svg xmlns="http://www.w3.org/2000/svg" width="1200" height="830" viewBox="0 0 1200 830">','<rect width="1200" height="830" fill="#f5f4ef"/>','<style>text{font:14px sans-serif;fill:#213743}.title{font-size:23px;font-weight:bold}.small{font-size:12px}</style>','<text class="title" x="28" y="34">CS247 joined feed — disposable source construction</text>','<text x="28" y="59">Fixed 58 mm offset • 66 mm free curve • three rail wires + three separate AGND returns</text>','<text x="28" y="82">Conditional geometry; physical process, native closure and whole-network acceptance remain open.</text>']
 colors=['#d25d36','#8958b3','#b38c19','#277b69','#26799d','#565f93']
 views=[('Feed region XY, installed (cropped)',28,115,8,lambda p:(p[0],p[1]),(0,0),0),('Feed region XZ, installed and 10.1 mm service',28,480,8,lambda p:(p[0],-p[2]),(0,90),0)]
 for title,ox,oy,scale,proj,offset,travel in views:
  parts.append(f'<text x="{ox}" y="{oy-12}">{title}</text>')
  def xy(p):
   a,b=proj(p);return (ox+scale*(a-offset[0]),oy+scale*(b-offset[1]))
  for s in m['solids']:
   v=np.asarray(s['vertices_xyz_mm']);pp=np.asarray([xy(p) for p in v]);u=np.unique(np.round(pp,5),axis=0)
   if len(u)<3:continue
   try:idx=ConvexHull(u).vertices
   except Exception:continue
   poly=' '.join(f'{u[j,0]:.2f},{u[j,1]:.2f}' for j in idx);fill='#99b3be' if s['board']=='KA' else '#d1b38e'
   parts.append(f'<polygon points="{poly}" fill="{fill}" fill-opacity=".22" stroke="{fill}" stroke-width=".5"><title>{html.escape(s["id"])}</title></polygon>')
  for travel in ([0.] if title.startswith('Feed region XY') else [0.,10.1]):
   gap=20.4+travel;ctrl=ck.rc.control(F,gap,ck.rc.handle(F,gap,66));end=np.array([58,0,-gap]);paths=[np.linspace(-bridge*v0,2.5*v0,12),ck.rc.position(ctrl,np.linspace(0,1,200)),np.linspace(end-2.5*v1,end+bridge*v1,12)]
   for i,sgn in enumerate([1,-1,1,1,-1,1]):
    pts=np.concatenate(paths)*[1,sgn,1]+[23+17*(i%3),15.5+9*(i//3),-103.6];poly=' '.join(f'{a:.2f},{b:.2f}' for a,b in map(xy,pts));dash='stroke-dasharray="5 3"' if travel else ''
    parts.append(f'<polyline points="{poly}" fill="none" stroke="{colors[i]}" stroke-width="3" {dash}><title>W{i+1}, service {travel} mm</title></polyline>')
  if title.startswith('Feed region XY'):
   for t in terms:
    x,y=xy(t['center_xyz_mm']);parts.append(f'<rect x="{x-16:.2f}" y="{y-16:.2f}" width="32" height="32" fill="none" stroke="{colors[t["wire"]-1]}"/><text class="small" x="{x+19:.2f}" y="{y:.2f}">{t["board"]} W{t["wire"]}</text>')
 parts+=['<rect x="1040" y="110" width="160" height="660" fill="#f5f4ef"/>','<text class="small" x="28" y="808">Projection drawing; occlusion and boolean holes omitted from this view. Exact solids and holes are retained in mechanical.json.gz.</text>','</svg>'];out.write_text('\n'.join(parts)+'\n')
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();render(a.candidate,a.output)
