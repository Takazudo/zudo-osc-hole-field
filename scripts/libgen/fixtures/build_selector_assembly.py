#!/usr/bin/env python3
"""Build rejected coplanar and selected 3+2 adapter fixtures with pinned pcbnew."""
from pathlib import Path
import json
import pcbnew
ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/'.circuit-cache/selector-fixture'
LIB=ROOT/'footprints/kicad/zudo-osc-hole-field.pretty'
A=json.loads((ROOT/'design/mechanical/selector-assembly.json').read_text())
P={p['uid']:p for p in json.loads((ROOT/'design/grid/placements.lock.json').read_text())['placements']}
OUT.mkdir(parents=True,exist_ok=True)
def point(x,y):return pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(y))
def outline(b,points):
    for a,c in zip(points,points[1:]+points[:1]):
        edge=pcbnew.PCB_SHAPE(b);edge.SetShape(pcbnew.SHAPE_T_SEGMENT)
        edge.SetStart(point(*a));edge.SetEnd(point(*c));edge.SetLayer(pcbnew.Edge_Cuts)
        edge.SetWidth(pcbnew.FromMM(.05));b.Add(edge)
def build(name,instances,separate):
    b=pcbnew.BOARD();measure=[]
    for item in instances:
        p=P[item['uid']];x,y=p['x_mm'],p['y_mm']
        fp=pcbnew.FootprintLoad(str(LIB),'SRBV160803');assert fp
        fp.SetReference(p['ref']);fp.SetPosition(point(x,y));fp.SetOrientationDegrees(item['rotation_deg'])
        fp.Reference().SetVisible(False);b.Add(fp)
        # Tongue always points toward the upper carrier rail, independent of body rotation.
        if separate:
            w=A['adapter']['width_mm']/2;h=A['adapter']['length_mm']/2;t=A['adapter']['tongue_width_mm']/2
            outline(b,[(x-w,y-h),(x-t,y-h),(x-t,y-14),(x+t,y-14),(x+t,y-h),(x+w,y-h),(x+w,y+h),(x-w,y+h)])
        measure.append({'uid':item['uid'],'shaft_xy_mm':[x,y],'rotation_deg':fp.GetOrientationDegrees(),
                        'pcb_z_mm':item['pcb_z_mm'],'pads':{pad.GetNumber():{'xy_mm':[pcbnew.ToMM(pad.GetPosition().x),pcbnew.ToMM(pad.GetPosition().y)],
                        'diameter_mm':pcbnew.ToMM(pad.GetSize().x),'drill_mm':pcbnew.ToMM(pad.GetDrillSize().x),'attribute':int(pad.GetAttribute())} for pad in fp.Pads()}})
    if not separate:outline(b,[(2,169),(96,169),(96,198),(2,198)])
    pcbnew.SaveBoard(str(OUT/f'{name}.kicad_pcb'),b)
    (OUT/f'{name}-measurements.json').write_text(json.dumps({'kicad_version':pcbnew.GetBuildVersion(),'instances':measure},indent=2)+'\n')
for name in ('front','rear'):
    build(name,[i for i in A['instances'] if i['adapter_group']==name],True)
build('rejected-alternating-coplanar',A['instances'],False)
# The original fixture is retained as a regression explaining why same-orientation bores fail.
same=[dict(i,rotation_deg=0) for i in A['instances']]
build('rejected-same-coplanar',same,False)
print('Generated five-up assembly as front (3) and rear (2) adapter islands; PCB x/y exactly equal panel lock. All are unvalidated drafts.')
