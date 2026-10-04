#!/usr/bin/env python3
"""Source-derived courtyard capacity proposal. Produces no KiCad board or fit pass."""
from __future__ import annotations
import argparse
from functools import lru_cache
from collections import Counter, defaultdict
import json
import math
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.checks.partition35_json import dumps
from scripts.partition.model import JACK_BOARDS
from scripts.checks.connector_packing35 import board_for,pads
from scripts.checks.partition35_diagnostic import footprint_geometry
from scripts.pcbgen.netlist import TOKEN, parse, many, one
from scripts.checks.jack_locality import place_jack_locality
from scripts.checks.core_locality import spread_module_homes
OUT=ROOT/'design/partition/floorplan-candidate.json'
SCALE=4


class Grid:
    """Conservative 0.25 mm occupancy cells, using bit rows for rectangle search."""
    def __init__(self,board,side,outline):
        self.scale=10 if board in JACK_BOARDS else SCALE
        self.board=board;self.side=side;self.width=318*self.scale;self.height=298*self.scale
        self.full=(1<<self.width)-1;self.rows=[0]*self.height
        def inside(x,y):
            # Rectangular source outlines with one orthogonal notch each.
            if board in JACK_BOARDS:
                xs=[p[0] for p in outline];return min(xs)+.30<=x<=max(xs)-.30 and 20.30<=y<=163.70
            if board=='P':return 1.30<=x<=316.70 and 176.30<=y<=291.70 and (x>=94.30 or y>=194.30)
            return 4.30<=x<=313.70 and 8.30<=y<=291.70 and (x<=257.70 or y<=245.70)
        for y in range(self.height):
            for x in range(self.width):
                if not inside(x/self.scale,y/self.scale):self.rows[y]|=1<<x
    def fill(self,b,gap=.35):
        SCALE=self.scale
        x0,y0,x1,y1=b;x0=max(0,math.floor((x0-gap)*SCALE));x1=min(self.width,math.ceil((x1+gap)*SCALE));y0=max(0,math.floor((y0-gap)*SCALE));y1=min(self.height,math.ceil((y1+gap)*SCALE));mask=((1<<(x1-x0))-1)<<x0
        for y in range(y0,y1):self.rows[y]|=mask
    def place(self,box):
        SCALE=self.scale
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


def turn(point, angle):
    x,y=point
    for _ in range((angle%360)//90):x,y=-y,x
    return x,y


def oriented_box(box, side, angle):
    pts=[turn((-x if side=='B.Cu' else x,y),angle) for x in (box[0],box[2]) for y in (box[1],box[3])]
    return [min(x for x,y in pts),min(y for x,y in pts),max(x for x,y in pts),max(y for x,y in pts)]


@lru_cache(maxsize=None)
def footprint_pads(footprint):
    tree,_=parse(TOKEN.findall((ROOT/'footprints/kicad/zudo-osc-hole-field.pretty'/(footprint.split(':')[1]+'.kicad_mod')).read_text()))
    return {p[1]:tuple(map(float,one(p,'at')[1:3])) for p in many(tree,'pad')}


@lru_cache(maxsize=None)
def through_hole(footprint):
    return 'thru_hole' in (ROOT/'footprints/kicad/zudo-osc-hole-field.pretty'/(footprint.split(':')[1]+'.kicad_mod')).read_text()


def bypass_cells(parent,caps,side,shapes,pin_nets,horizontal=False):
    """Rigid IC plus capacitors, each capacitor aligned to its actual supply pad."""
    icbox=oriented_box(shapes[parent['footprint']],side,0)
    ipads=footprint_pads(parent['footprint']);cells=[(parent,0,(0,0))]
    for cap in caps:
        # A local supply such as a regulated VEE also counts as the decoupled rail.
        rail=next(n for n in pin_nets[cap['ref']].values() if n!='AGND' and n in pin_nets[parent['ref']].values())
        supply=next(pin for pin,n in pin_nets[parent['ref']].items() if n==rail)
        sx,sy=ipads[supply];sx=-sx if side=='B.Cu' else sx
        cpads=footprint_pads(cap['footprint']);cpin=next(pin for pin,n in pin_nets[cap['ref']].items() if n==rail)
        cx,cy=cpads[cpin];cx=-cx if side=='B.Cu' else cx
        angle=(180 if cx*sx>0 else 0) if horizontal else 90
        cx,cy=turn((cx,cy),angle)
        box=oriented_box(shapes[cap['footprint']],side,angle)
        x=icbox[2]+.35-box[0] if sx>0 else icbox[0]-.35-box[2]
        cells.append((cap,angle,(x,sy-cy)))
    return cells


def check_bypasses(parts,placements,pin_nets):
    errors=[]
    limit=json.loads((ROOT/'design/partition/bypass-placement-evidence.json').read_text())['proposal']['maximum_supply_pad_to_capacitor_rail_pad_mm']
    byref={p['ref']:p for p in placements};bypass=[]
    for p in parts:
        if not p['decouples_ref'] or board_for(p) not in JACK_BOARDS:continue
        if p['ref'] not in byref or p['decouples_ref'] not in byref:continue
        c=byref[p['ref']];u=byref[p['decouples_ref']]
        rail=next(n for n in pin_nets[p['ref']].values() if n in ('+12V','-12V','+5V'))
        def point(ref,net):
            item=byref[ref];part=next(q for q in parts if q['ref']==ref);pin=next(k for k,n in pin_nets[ref].items() if n==net);x,y=footprint_pads(part['footprint'])[pin]
            x,y=turn((-x if item['side']=='B.Cu' else x,y),item['rotation_deg'])
            return [x+item['x_mm'],y+item['y_mm']]
        distance=math.dist(point(p['ref'],rail),point(p['decouples_ref'],rail))
        if c['side']!=u['side'] or distance>limit:errors.append('bypass supply-pad proximity failed '+p['ref'])
        bypass.append({'capacitor':p['ref'],'IC':p['decouples_ref'],'rail':rail,'board':c['board'],'same_face':c['side']==u['side'],'supply_pad_centre_distance_mm':distance})
    return bypass,errors



def build():
    source=json.loads((ROOT/'design/partition/partition-input.json').read_text())
    io=json.loads((ROOT/'design/reports/io-partition.json').read_text());lock={p['uid']:p for p in json.loads((ROOT/'design/grid/placements.lock.json').read_text())['placements']}
    connector=json.loads((ROOT/'design/partition/connector-packing-candidate.json').read_text())
    parts=io['physical_packages'];shapes={};pin_nets=defaultdict(dict)
    for unit in io['package_units']:pin_nets[unit['ref']].update(unit['pins'])
    for p in parts:
        if p['footprint'] not in shapes:shapes[p['footprint']]=footprint_geometry(ROOT/'footprints/kicad/zudo-osc-hole-field.pretty'/(p['footprint'].split(':')[1]+'.kicad_mod'))['courtyard_bbox_mm']
    placements=[];errors=[];grids={};available={}
    for board in (*JACK_BOARDS,'P','K'):
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
            available[board+' '+side]=sum(g.width-row.bit_count() for row in g.rows)/(g.scale*g.scale)
        free=sorted((p for p in parts if board_for(p)==board and not p['panel_uid']),key=lambda p:(-p['courtyard']['area_mm2'],p['ref']))
        if board in JACK_BOARDS:
            anchors=defaultdict(list)
            for p in parts:
                if board_for(p)!=board or not p['panel_uid']:continue
                point=lock[p['panel_uid']];angle=math.radians(point['rot_deg']);co,si=math.cos(angle),math.sin(angle)
                for pin,(x,y) in footprint_pads(p['footprint']).items():
                    net=pin_nets[p['ref']].get(pin)
                    if net:anchors[net].append((point['x_mm']+x*co-y*si,point['y_mm']+x*si+y*co))
            for h in connector['headers']:
                if h['board']==board:
                    for net in h['pin_map'].values():
                        if net not in (None,'NC'):anchors[net].append(tuple(h['center_mm']))
            homes=defaultdict(list)
            for p in parts:
                if board_for(p)==board and p['panel_uid']:homes[p['instance']].append((lock[p['panel_uid']]['x_mm'],lock[p['panel_uid']]['y_mm']))
            instance_anchor={k:(sum(x for x,_ in v)/len(v),sum(y for _,y in v)/len(v)) for k,v in homes.items()}
            placements.extend(place_jack_locality(board,free,grids,shapes,pin_nets,anchors,
                lambda parent,caps,side,horizontal:bypass_cells(parent,caps,side,shapes,pin_nets,horizontal),turn,oriented_box,instance_anchor))
            free=[]
        if board=='K':
            # Core locality (#43): the core has no panel hardware, so its headers anchor
            # each net and each module is pulled toward the headers that carry its nets.
            anchors=defaultdict(list);net_instances=defaultdict(set);homes=defaultdict(list)
            for p in free:
                for net in pin_nets[p['ref']].values():net_instances[net].add(p['instance'])
            for h in connector['headers']:
                if h['board']!=board:continue
                for net in h['pin_map'].values():
                    if net in (None,'NC'):continue
                    anchors[net].append(tuple(h['center_mm']))
                    if net not in ('AGND','+12V','-12V','+5V'):
                        for instance in net_instances[net]:homes[instance].append(h['center_mm'])
            instance_anchor={k:(sum(x for x,_ in v)/len(v),sum(y for _,y in v)/len(v)) for k,v in homes.items()}
            # Header homes crowd ~1300 packages into one corner; spread the module homes so each
            # module gets contiguous room, then legalize module by module (#43 congestion review).
            areas=defaultdict(float)
            for p in free:
                b=shapes[p['footprint']];areas[p['instance']]+=(b[2]-b[0]+.35)*(b[3]-b[1]+.35)
            notch=[spec['outline'][3][0],spec['outline'][3][1],spec['outline'][2][0],spec['outline'][4][1]]
            instance_anchor=spread_module_homes(instance_anchor,areas,(4.3,8.3,313.7,291.7),holes=[notch],fill=.45)
            placements.extend(place_jack_locality(board,free,grids,shapes,pin_nets,anchors,
                lambda parent,caps,side,horizontal:bypass_cells(parent,caps,side,shapes,pin_nets,horizontal),turn,oriented_box,instance_anchor,
                lambda part:through_hole(part['footprint']),module_order=True,swaps=True))
            free=[]
        for p in free:
            location=grids[board,'B.Cu'].place(shapes[p['footprint']])
            if location is None and board in JACK_BOARDS:location=grids[board,'F.Cu'].place(shapes[p['footprint']])
            if location is None:errors.append('courtyard first-fit overflow '+board+' '+p['ref']);continue
            placements.append({'ref':p['ref'],'board':board,'fixed':False,**location})
    optical=json.loads((ROOT/'design/partition/stage-optical-candidate.json').read_text())
    placements.extend({**p,'board':'EL','side':'F.Cu'} for p in optical['placement_proposal'])
    for p in parts:
        if not p['panel_uid'] or board_for(p)=='EL':continue
        point=lock[p['panel_uid']]
        placements.append({'ref':p['ref'],'board':board_for(p),'fixed':True,'x_mm':point['x_mm'],'y_mm':point['y_mm'],'rotation_deg':point['rot_deg'],'side':'F.Cu','courtyard_mm':transformed(shapes[p['footprint']],point)})
    from scripts.checks.control_locality import apply_locality
    locality_source=json.loads((ROOT/'design/partition/control-locality.json').read_text())
    optical_source=json.loads((ROOT/'design/partition/stage-optical-input.json').read_text())
    placements,locality=apply_locality(placements,io,source,connector,lock,shapes,locality_source,optical_source)
    from scripts.checks.control_bypass_locality import apply_bypass_locality
    bypass_source=json.loads((ROOT/'design/partition/control-bypass-locality.json').read_text())
    placements,control_bypasses=apply_bypass_locality(placements,io,source,connector,lock,shapes,bypass_source,optical_source,locality_source)
    from scripts.checks.control_debounce_locality import apply_debounce_locality
    debounce_source=json.loads((ROOT/'design/partition/control-debounce-locality.json').read_text())
    placements,control_debounce=apply_debounce_locality(placements,io,source,connector,lock,shapes,debounce_source,optical_source)
    for row in placements:row['kicad_orientation_deg']=((180 if row['side']=='B.Cu' else 0)-row['rotation_deg'])%360
    if Counter(p['ref'] for p in placements)!=Counter(p['ref'] for p in parts):errors.append('package roster mismatch')
    bypass,bypass_errors=check_bypasses(parts,placements,pin_nets);errors.extend(bypass_errors)
    return {'schema_version':1,'status':'FAIL' if errors else 'PASS - conservative courtyard capacity proposal only',
            'errors':errors,'control_slew_locality':{'source':'design/partition/control-locality.json','status':'SOURCE GEOMETRY ONLY; native/routed/physical checks required','groups':locality},'grid_mm_by_board':{b:(.1 if b in JACK_BOARDS else .25) for b in source['boards']},'courtyard_gap_mm':.35,'drawn_edge_margin_mm':.30,'native_cached_inflation_ceiling_mm':.05,'native_free_clearance_lower_bound_mm':.25,'placements':placements,
            'control_bypass_locality':{'source':'design/partition/control-bypass-locality.json',**control_bypasses},
            'control_debounce_locality':{'source':'design/partition/control-debounce-locality.json',**control_debounce},
            'bypass_proximity':{'status':'DERIVED geometry only; routed loop #38 NOT RUN','evidence':'design/partition/bypass-placement-evidence.json','project_pad_distance_limit_mm':json.loads((ROOT/'design/partition/bypass-placement-evidence.json').read_text())['proposal']['maximum_supply_pad_to_capacitor_rail_pad_mm'],'pairs':bypass,'maximum_supply_pad_distance_mm':max((r['supply_pad_centre_distance_mm'] for r in bypass),default=0)},
            'usable_grid_area_after_exclusions_mm2':available,
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
