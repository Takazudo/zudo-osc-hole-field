#!/usr/bin/env python3
"""Source-derived courtyard capacity proposal. Produces no KiCad board or fit pass."""
from __future__ import annotations
import argparse
from collections import Counter
import json
import math
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.checks.partition35_json import dumps
from scripts.checks.connector_packing35 import board_for,pads
from scripts.checks.partition35_diagnostic import footprint_geometry
OUT=ROOT/'design/partition/floorplan-candidate.json'
SCALE=4


class Grid:
    """Conservative 0.25 mm occupancy cells, using bit rows for rectangle search."""
    def __init__(self,board,side,outline):
        self.board=board;self.side=side;self.width=318*SCALE;self.height=298*SCALE
        self.full=(1<<self.width)-1;self.rows=[0]*self.height
        def inside(x,y):
            # Rectangular source outlines with one orthogonal notch each.
            if board=='J':return 4.30<=x<=313.70 and 20.30<=y<=163.70
            if board=='P':return 1.30<=x<=316.70 and 176.30<=y<=291.70 and (x>=94.30 or y>=194.30)
            return 4.30<=x<=313.70 and 8.30<=y<=291.70 and (x<=257.70 or y<=245.70)
        for y in range(self.height):
            for x in range(self.width):
                if not inside(x/SCALE,y/SCALE):self.rows[y]|=1<<x
    def fill(self,b,gap=.35):
        x0,y0,x1,y1=b;x0=max(0,math.floor((x0-gap)*SCALE));x1=min(self.width,math.ceil((x1+gap)*SCALE));y0=max(0,math.floor((y0-gap)*SCALE));y1=min(self.height,math.ceil((y1+gap)*SCALE));mask=((1<<(x1-x0))-1)<<x0
        for y in range(y0,y1):self.rows[y]|=mask
    def place(self,box):
        if self.side=='B.Cu':box=[-box[2],box[1],-box[0],box[3]]
        for angle in (0,90):
            b=box if angle==0 else [-box[3],box[0],-box[1],box[2]]
            w=math.ceil((b[2]-b[0]+.35)*SCALE);h=math.ceil((b[3]-b[1]+.35)*SCALE)
            for y in range(self.height-h+1):
                available=self.full
                for row in self.rows[y:y+h]:available &= ~row
                n=w;shift=1
                while n>1:
                    step=min(shift,n-1);available &= available>>step;n-=step;shift*=2
                if not available:continue
                x=(available&-available).bit_length()-1
                self.fill([x/SCALE,y/SCALE,(x+w)/SCALE,(y+h)/SCALE],0)
                return {'x_mm':x/SCALE-b[0],'y_mm':y/SCALE-b[1],'rotation_deg':angle,'side':self.side,
                        'courtyard_mm':[x/SCALE,y/SCALE,x/SCALE+b[2]-b[0],y/SCALE+b[3]-b[1]]}
        return None


def transformed(box,p):
    angle=math.radians(p['rot_deg']);co,si=math.cos(angle),math.sin(angle)
    points=[(p['x_mm']+x*co-y*si,p['y_mm']+x*si+y*co) for x in (box[0],box[2]) for y in (box[1],box[3])]
    return [min(x for x,y in points),min(y for x,y in points),max(x for x,y in points),max(y for x,y in points)]


def build():
    source=json.loads((ROOT/'design/partition/partition-input.json').read_text())
    io=json.loads((ROOT/'design/reports/io-partition.json').read_text());lock={p['uid']:p for p in json.loads((ROOT/'design/grid/placements.lock.json').read_text())['placements']}
    connector=json.loads((ROOT/'design/partition/connector-packing-candidate.json').read_text())
    parts=io['physical_packages'];shapes={}
    for p in parts:
        if p['footprint'] not in shapes:shapes[p['footprint']]=footprint_geometry(ROOT/'footprints/kicad/zudo-osc-hole-field.pretty'/(p['footprint'].split(':')[1]+'.kicad_mod'))['courtyard_bbox_mm']
    placements=[];errors=[];grids={}
    for board in ('J','P','K'):
        spec=source['boards'][board]
        for side in ('F.Cu','B.Cu'):
            g=Grid(board,side,spec['outline']);grids[board,side]=g
            for p in parts:
                if board_for(p)!=board or not p['panel_uid']:continue
                for _,box in pads(p,lock):g.fill(box)
                if side=='F.Cu':g.fill(transformed(shapes[p['footprint']],lock[p['panel_uid']]))
            for h in connector['headers']:
                if h['board']==board and h['side']==side:g.fill(h['land_courtyard_mm'])
            if board=='K':
                for aperture in connector['K_service_apertures']:g.fill(aperture['box_mm'])
            for h in spec['supports_mm']:
                x,y=h;g.fill([x-1.6,y-1.6,x+1.6,y+1.6])
            if board=='P':
                optical=json.loads((ROOT/'design/partition/stage-optical-input.json').read_text())['support']
                for x in optical['x_mm']:
                    for y in optical['y_mm']:
                        if y>=176:g.fill([x-1.6,y-1.6,x+1.6,y+1.6])
            for reserve in spec.get('reserves',[]):
                if side in reserve['sides']:g.fill(reserve['rect'])
        free=sorted((p for p in parts if board_for(p)==board and not p['panel_uid']),key=lambda p:(-p['courtyard']['area_mm2'],p['ref']))
        for p in free:
            location=grids[board,'B.Cu'].place(shapes[p['footprint']])
            if location is None and board=='J':location=grids[board,'F.Cu'].place(shapes[p['footprint']])
            if location is None:errors.append('courtyard first-fit overflow '+board+' '+p['ref']);continue
            placements.append({'ref':p['ref'],'board':board,'fixed':False,**location})
    optical=json.loads((ROOT/'design/partition/stage-optical-candidate.json').read_text())
    placements.extend({**p,'board':'EL','side':'F.Cu'} for p in optical['placement_proposal'])
    for p in parts:
        if not p['panel_uid'] or board_for(p)=='EL':continue
        point=lock[p['panel_uid']]
        placements.append({'ref':p['ref'],'board':board_for(p),'fixed':True,'x_mm':point['x_mm'],'y_mm':point['y_mm'],'rotation_deg':point['rot_deg'],'side':'F.Cu','courtyard_mm':transformed(shapes[p['footprint']],point)})
    for row in placements:row['kicad_orientation_deg']=((180 if row['side']=='B.Cu' else 0)-row['rotation_deg'])%360
    if Counter(p['ref'] for p in placements)!=Counter(p['ref'] for p in parts):errors.append('package roster mismatch')
    return {'schema_version':1,'status':'FAIL' if errors else 'PASS - conservative courtyard capacity proposal only',
            'errors':errors,'grid_mm':1/SCALE,'courtyard_gap_mm':.35,'drawn_edge_margin_mm':.30,'native_cached_inflation_ceiling_mm':.05,'native_free_clearance_lower_bound_mm':.25,'placements':placements,
            'counts':{b:dict(Counter(p['side'] for p in placements if p['board']==b)) for b in source['boards']},
            'limits':['No PCB generated, routed, soldered or physically fitted.','First-fit failure is not an infeasibility proof; every reported successful footprint has its full courtyard.',
                      'J mixed-face local passive connections need vias, continuous inner AGND and actual loop/decoupling review under #38.',
                      'Source #59 unselected protection geometry remains reserved/conditional, not fictitious zero-area components.',
                      'Main board service slots and loom/support solids must be checked separately.']}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('--check',action='store_true');args=parser.parse_args();report=build();text=dumps(report)+'\n'
    if args.check:
        if not OUT.exists() or OUT.read_text()!=text:raise SystemExit('floorplan drift')
    else:OUT.write_text(text)
    print(report['status'],report['counts'])
    if report['errors']:raise SystemExit('\n'.join(report['errors']))

if __name__=='__main__':main()
