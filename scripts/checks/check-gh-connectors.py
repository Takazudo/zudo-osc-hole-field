#!/usr/bin/env python3
"""Independent GH drawing/asset and fixed selector copper comparison."""
import hashlib
import json
import math
from pathlib import Path
import sys

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/libgen'))
from gen_courtyards import parse,node_name,courtyard_box  # noqa: E402

def children(node,key): return [x for x in node[1:] if isinstance(x,list) and node_name(x)==key]
def coords(node,key): return [float(x) for x in children(node,key)[0][1:]]
def close(a,b): assert math.isclose(a,b,abs_tol=0.011),(a,b)

def main():
    d=json.loads((ROOT/'design/connectors/jst-gh.json').read_text())
    source=ROOT/d['source']['path']
    assert hashlib.sha256(source.read_bytes()).hexdigest()==d['source']['sha256']
    selector=json.loads((ROOT/'design/mechanical/selector-assembly.json').read_text())
    assert selector['drawing']['mount_holes_xy_mm']==[[-8,-1.1],[8,-1.1]]
    assert selector['drawing']['mount_pad_diameter_mm']==2.6
    inner=8-2.6/2
    close(inner,d['selector_gh7_check']['mount_pad_inner_copper_edge_x_mm'])
    for item in d['sizes']:
        n=item['positions'];a=(n-1)*1.25;b=a+4.5
        close(item['header_body_width_mm'],b)
        close(item['housing_width_mm'],a+2.5)
        assert item['housing_mpn']==f'GHR-{n:02d}V-S'
        assert item['header_mpn']==f'BM{n:02d}B-GHS-TBT(LF)(SN)'
        assert item['contact_mpn']=='SSHL-002T-P0.2'
        assert item['orientation'].startswith('top entry')
        fp=ROOT/f'footprints/kicad/zudo-osc-hole-field.pretty/JST_GH{n}_BM_TopEntry.kicad_mod'
        tree=parse(fp.read_text())
        pads=children(tree,'pad'); assert len(pads)==n+2
        assert [p[1] for p in pads]==[str(i) for i in range(1,n+1)]+['MP1','MP2']
        assert not any(children(p,'drill') for p in pads)
        for i,p in enumerate(pads[:n],1):
            x,y=coords(p,'at')[:2];sx,sy=coords(p,'size')[:2]
            close(x,(n+1-2*i)*0.625);close(y,0);close(sx,0.6);close(sy,1.7)
        for i,p in enumerate(pads[n:]):
            x,y=coords(p,'at')[:2];sx,sy=coords(p,'size')[:2]
            close(x,(-1 if i==0 else 1)*(b/2-0.4));close(y,3.35);close(sx,1);close(sy,2.8)
        x1,y1,x2,y2=courtyard_box(fp.read_text())
        for got,expected in zip((x1,y1,x2,y2),item['header_courtyard_xy_mm']):close(got,expected)
        assert item['rated_current_A_per_contact']==1 and item['rated_voltage_V_ac_dc']==50
        assert item['cable_bend_access_mm'] is None and item['assembled_derating_A_per_contact'] is None
    by_size={i['positions']:i for i in d['sizes']}
    gap=inner-by_size[7]['header_courtyard_xy_mm'][2]
    overlap=by_size[8]['header_courtyard_xy_mm'][2]-inner
    close(gap,0.35);close(overlap,0.27)
    print(f'PASS: JST GH3/GH7/GH8 drawing geometry, pads, pin 1, mates; GH7 gap {gap:.2f} mm; GH8 overlap {overlap:.2f} mm; physical fit NOT RUN')
if __name__=='__main__':main()
