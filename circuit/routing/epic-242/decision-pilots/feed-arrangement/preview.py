#!/usr/bin/env python3
"""Deterministic source SVG, not an assembly drawing or physical qualification."""
import argparse
import json
from html import escape
from pathlib import Path
import numpy as np
import offset as o

HERE = Path(__file__).resolve().parent
COLORS = ['#b32636', '#3260ae', '#986000', '#148273', '#6d48a7', '#a33b80']


def build():
    data = json.loads((HERE/'offset-proposal.json').read_text())
    out = ['<svg xmlns="http://www.w3.org/2000/svg" width="1150" height="1550" viewBox="0 0 1150 1550">',
           '<rect width="1150" height="1550" fill="#f6f7fa"/>',
           '<style>text{font-family:monospace;fill:#263244} .title{font-size:19px;font-weight:bold}.small{font-size:12px}</style>',
           '<text x="28" y="32" class="title">Conditional split-row feed · fixed-tangent withdrawal</text>',
           '<text x="28" y="55" class="small">SOURCE ONLY / face choice pending / no canonical CAD changes / dimensions in mm</text>']
    for panel, travel in enumerate((0, 5, 10)):
        ox, oy, scale = 35, 100+panel*450, 7.8
        out.append(f'<text x="{ox}" y="{oy-15}" class="title">{travel} mm KB withdrawal — XY projection</text>')
        out.append(f'<rect x="{ox-2*scale}" y="{oy-2*scale}" width="{117*scale}" height="{52*scale}" fill="white" stroke="#c4ccd8"/>')
        def xy(p): return ox+float(p[0])*scale, oy+float(p[1])*scale
        for rail in data.get('clamps', {}).get('solids', []):
            q=rail.get('box')
            if q:
                x,y=xy(q[:3]);out.append(f'<rect x="{x:.3f}" y="{y:.3f}" width="{(q[3]-q[0])*scale:.3f}" height="{(q[4]-q[1])*scale:.3f}" fill="#9aa6b8" opacity=".4"/>')
        for i in range(6):
            start=np.array(data['construction']['terminals'][i]['free_tail_start_xyz_mm'])
            p=o.control(21.4+travel,o.handle(21.4+travel))
            curve=np.vstack([-o.BRIDGE*o.V0, np.zeros(3),o.position(p,np.linspace(0,1,151)),
                             [o.OFFSET,0,-21.4-travel],np.array([o.OFFSET,0,-21.4-travel])+o.BRIDGE*o.V1])
            curve=curve*np.array([1,o.SIGNS[i],1])+start
            coords=' '.join(f'{xy(v)[0]:.3f},{xy(v)[1]:.3f}' for v in curve)
            out.append(f'<polyline points="{coords}" fill="none" stroke="{COLORS[i]}" stroke-width="{2.5908*scale:.3f}" opacity=".28"/>')
            out.append(f'<polyline points="{coords}" fill="none" stroke="{COLORS[i]}" stroke-width="1.3"/>')
            for term in (data['construction']['terminals'][i],data['construction']['terminals'][i+6]):
                x,y=xy(term['land_center_xyz_mm'])
                out.append(f'<rect x="{x-2*scale:.3f}" y="{y-2*scale:.3f}" width="{4*scale}" height="{4*scale}" fill="none" stroke="{COLORS[i]}"/>')
        out.append(f'<text x="965" y="{oy+18}" class="small">KA B.Cu → KB F.Cu</text>')
        out.append(f'<text x="965" y="{oy+38}" class="small">gap {24.4+travel:.1f} mm</text>')
    out.extend(['<text x="28" y="1480" class="small">Wire tubes and lands shown. XY projections may overlap when separated in Z; use numeric 3D bounds.</text>',
                '<text x="28" y="1503" class="small">No retention, solder, fastener, stiffness, thermal or 100-adjustment-access qualification is implied.</text>'])
    for i,label in enumerate(('+12V','−12V','+5V','AGND-1','AGND-2','AGND-3')):
        out.append(f'<text x="{28+i*175}" y="1532" class="small" style="fill:{COLORS[i]}">W{i+1} {escape(label)}</text>')
    return '\n'.join(out+['</svg>'])+'\n'


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args()
    text=build();path=HERE/'preview.svg'
    if args.check:
        if path.read_text()!=text:raise ValueError('preview drift')
    else:path.write_text(text)
    print('PASS: deterministic source preview')
