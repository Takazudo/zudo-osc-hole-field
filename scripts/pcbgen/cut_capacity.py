#!/usr/bin/env python3
"""Cut-line routability bound for a board from a grid_dump.py JSON.

For each vertical and horizontal line across the board, demand is the number
of signal nets whose pads lie on both sides (each must cross it). Capacity per
layer is the number of track centrelines at the given pitch that fit in the
line's free runs after existing pads, drills, tracks, vias and keepouts. This
is an ideal-packing upper bound; real routers reach well below it. A ratio
under 1 proves the layers cannot carry the crossing nets.
"""
from __future__ import annotations
import argparse,collections,json,sys
from pathlib import Path
import numpy as np
from scipy import ndimage

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.pcbgen.grid_router import LAYERS,Raster

PLANE_NETS=('AGND','+12V','-12V','+5V')


def line_capacity(free_line,res,pitch):
    lab,n=ndimage.label(free_line)
    if not n:return 0
    runs=ndimage.sum(free_line,lab,range(1,n+1))
    return int(sum(int((r-1)*res/pitch+1e-9)+1 for r in runs))


def scan(dump,res=0.1,width=0.2,clearance=0.2,step_mm=0.5,exclude=PLANE_NETS):
    raster=Raster(dump,res,{t['uuid'] for t in dump['tracks'] if t['net'] in exclude})
    free=[]
    for li in range(4):
        occupied=raster.label[li]!=0
        free.append((ndimage.distance_transform_edt(~occupied)*res>=clearance+width/2)&(raster.d_edge>=width/2)
                    &(raster.d_keep_track[li]>=width/2))
    nets=collections.defaultdict(list)
    for p in dump['pads']:
        if p['net'] and p['net'] not in exclude:nets[p['net']].append(p['xy'])
    spans=np.array([(min(q[0] for q in v),max(q[0] for q in v),min(q[1] for q in v),max(q[1] for q in v)) for v in nets.values() if len(v)>1])
    pitch=width+clearance;stride=max(1,int(round(step_mm/res)));rows=[]
    for axis,count,origin in (('x',raster.w,raster.x0),('y',raster.h,raster.y0)):
        for i in range(stride,count-stride,stride):
            c=origin+i*raster.step
            demand=int(((spans[:,0]<c)&(c<spans[:,1])).sum() if axis=='x' else ((spans[:,2]<c)&(c<spans[:,3])).sum()) if len(spans) else 0
            caps=[line_capacity(f[:,i] if axis=='x' else f[i,:],res,pitch) for f in free]
            rows.append({'axis':axis,'position_mm':round(c/1e6,2),'demand':demand,'capacity':dict(zip(LAYERS,caps))})
    return rows


def summarize(rows,signal_layers=('F.Cu','B.Cu'),worst=10):
    scored=[]
    for r in rows:
        if not r['demand']:continue
        cap=sum(r['capacity'][l] for l in signal_layers);total=sum(r['capacity'].values())
        scored.append({**r,'signal_layer_capacity':cap,'all_layer_capacity':total,
                       'signal_ratio':round(cap/r['demand'],3),'all_layer_ratio':round(total/r['demand'],3)})
    scored.sort(key=lambda r:r['signal_ratio'])
    return {'scope':'Ideal-packing cut-line bound; not a routing result','signal_layers':list(signal_layers),
            'max_demand':max((r['demand'] for r in rows),default=0),'worst_lines':scored[:worst]}


def main():
    p=argparse.ArgumentParser(description=__doc__.splitlines()[0]);p.add_argument('dump',type=Path);p.add_argument('--output',type=Path)
    p.add_argument('--width',type=float,default=0.2);p.add_argument('--clearance',type=float,default=0.2)
    p.add_argument('--signal-layers',default='F.Cu,B.Cu');p.add_argument('--res',type=float,default=0.1)
    a=p.parse_args()
    summary=summarize(scan(json.loads(a.dump.read_text()),a.res,a.width,a.clearance),tuple(a.signal_layers.split(',')))
    text=json.dumps(summary,indent=1)+'\n'
    if a.output:a.output.write_text(text)
    print(f"max demand {summary['max_demand']}")
    for r in summary['worst_lines']:
        print(f"{r['axis']}={r['position_mm']} demand {r['demand']} signal-layer capacity {r['signal_layer_capacity']} ({r['signal_ratio']}x) all-layer {r['all_layer_capacity']} ({r['all_layer_ratio']}x)")
if __name__=='__main__':main()
