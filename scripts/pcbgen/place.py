#!/usr/bin/env python3
"""Deterministic region-constrained placement of generator-owned free footprints.

Run through scripts/kicad/run.sh. This is a draft placement/checking tool, not
an autorouter or a mechanical qualification.
"""
from __future__ import annotations
import argparse,collections,json,math,sys
from dataclasses import dataclass
from pathlib import Path
import pcbnew
sys.dont_write_bytecode=True
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT))
from scripts.geometry.panel_frame import to_kicad
from scripts.pcbgen.definition import load_definition,load_lock,selected_hardware
from scripts.pcbgen.netlist import read_netlist
from scripts.pcbgen.uuid_tools import stable_uuid,normalize_file

GRID=0.5
POWER={'GND','AGND','+12V','-12V','+5V','VCC','VDD','VSS'}

@dataclass(frozen=True)
class Box:
 x0:float;y0:float;x1:float;y1:float
 @property
 def area(self):return max(0,self.x1-self.x0)*max(0,self.y1-self.y0)
 def shift(self,dx,dy):return Box(self.x0+dx,self.y0+dy,self.x1+dx,self.y1+dy)
 def intersects(self,other,gap=0):
  return self.x0<other.x1+gap and self.x1>other.x0-gap and self.y0<other.y1+gap and self.y1>other.y0-gap
 def overlap_area(self,other):
  return max(0,min(self.x1,other.x1)-max(self.x0,other.x0))*max(0,min(self.y1,other.y1)-max(self.y0,other.y0))

@dataclass(frozen=True)
class Region:
 instance:str;family:str;rect:Box;side:str;edge:float;mounting:float

class PlacementFailure(Exception):
 def __init__(self,instance,region,reason,needed,available):
  super().__init__(reason)
  self.instance=instance;self.region=region;self.reason=reason;self.needed=needed;self.available=available

def panel_box(raw):return Box(*map(float,raw))
def regions_for(definition):
 out={}
 for raw in definition.regions:
  r=Region(raw['instance'],raw['family'],panel_box(raw['rect']),raw['side'],float(raw['edge_clearance_mm']),float(raw['mounting_clearance_mm']))
  out.setdefault(r.instance,[]).append(r)
 return out

def mm(v):return pcbnew.ToMM(v)
def board_box(raw):return Box(mm(raw.GetLeft())-100,mm(raw.GetTop())-50,mm(raw.GetRight())-100,mm(raw.GetBottom())-50)
def fp_courtyard(fp):
 layer=pcbnew.F_CrtYd if fp.GetLayer()==pcbnew.F_Cu else pcbnew.B_CrtYd
 shape=fp.GetCourtyard(layer)
 if shape.OutlineCount()==0:raise ValueError(f'{fp.GetReference()}: missing {fp.GetLayerName()} courtyard')
 return board_box(shape.BBox())
def offsets(fp):
 box=fp_courtyard(fp);pos=fp.GetPosition();x=mm(pos.x)-100;y=mm(pos.y)-50
 return Box(box.x0-x,box.y0-y,box.x1-x,box.y1-y)
def is_through(pad):return pad.GetAttribute() in (pcbnew.PAD_ATTRIB_PTH,pcbnew.PAD_ATTRIB_NPTH)
def item_uuid(item):return item.m_Uuid.AsString()
def owned(board_id,fp):return item_uuid(fp)==stable_uuid(board_id,'footprint:'+fp.GetReference(),'root')
def normalize_block(c):
 value=dict(c.fields).get('Block','')
 if value in ('','${SHEETNAME}'):value=c.sheetname
 return value.strip('/')
def normalize_island(c,block):return dict(c.fields).get('Island','').replace('${SHEETNAME}',block)
def role(c):return dict(c.fields).get('Role','')

def point_in_polygon(x,y,poly):
 inside=False
 for i,(x1,y1) in enumerate(poly):
  x2,y2=poly[(i+1)%len(poly)]
  if ((y1>y)!=(y2>y)) and x<(x2-x1)*(y-y1)/(y2-y1)+x1:inside=not inside
 return inside

def point_segment_distance(x,y,a,b):
 ax,ay=a;bx,by=b;dx=bx-ax;dy=by-ay
 t=max(0,min(1,((x-ax)*dx+(y-ay)*dy)/(dx*dx+dy*dy))) if dx*dx+dy*dy else 0
 return math.hypot(x-(ax+t*dx),y-(ay+t*dy))

def inside_outline(box,outline,clearance):
 corners=((box.x0,box.y0),(box.x1,box.y0),(box.x1,box.y1),(box.x0,box.y1))
 for x,y in corners:
  if not point_in_polygon(x,y,outline):return False
  if min(point_segment_distance(x,y,outline[i],outline[(i+1)%len(outline)]) for i in range(len(outline)))<clearance-1e-6:return False
 # A concave cut through a box is rejected even when its four corners lie inside.
 for a,b in zip(outline,outline[1:]+outline[:1]):
  if max(a[0],b[0])>box.x0 and min(a[0],b[0])<box.x1 and max(a[1],b[1])>box.y0 and min(a[1],b[1])<box.y1:
   if point_in_polygon((a[0]+b[0])/2,(a[1]+b[1])/2,[(box.x0,box.y0),(box.x1,box.y0),(box.x1,box.y1),(box.x0,box.y1)]):return False
 return True

def candidate_centres(region,shape,target):
 minx=region.rect.x0+region.edge-shape.x0;maxx=region.rect.x1-region.edge-shape.x1
 miny=region.rect.y0+region.edge-shape.y0;maxy=region.rect.y1-region.edge-shape.y1
 if minx>maxx or miny>maxy:return []
 def axis(lo,hi):
  a=math.ceil((lo-1e-9)/GRID);b=math.floor((hi+1e-9)/GRID)
  return [i*GRID for i in range(a,b+1)]
 points=[(x,y) for x in axis(minx,maxx) for y in axis(miny,maxy)]
 points.sort(key=lambda xy:(round((xy[0]-target[0])**2+(xy[1]-target[1])**2,8),xy[1],xy[0]))
 return points

def obstacles(board,eligible):
 out=[]
 for fp in board.GetFootprints():
  if fp.GetReference() in eligible:continue
  side='F.Cu' if fp.GetLayer()==pcbnew.F_Cu else 'B.Cu'
  try:out.append((fp_courtyard(fp),side,'courtyard:'+fp.GetReference(),False))
  except ValueError:
   if fp.GetReference().startswith('MH_'):pass
   else:raise
  for pad in fp.Pads():
   if is_through(pad):out.append((board_box(pad.GetBoundingBox()),'both','through-pad:'+fp.GetReference(),True))
 return out

def is_clear(box,side,region,definition,obs):
 if not (box.x0>=region.rect.x0+region.edge-1e-6 and box.x1<=region.rect.x1-region.edge+1e-6 and box.y0>=region.rect.y0+region.edge-1e-6 and box.y1<=region.rect.y1-region.edge+1e-6):return False
 if not inside_outline(box,list(definition.outline),region.edge):return False
 for hole in definition.mounting_holes:
  x,y=hole['center'];r=hole['diameter_mm']/2+region.mounting
  if box.intersects(Box(x-r,y-r,x+r,y+r)):return False
 for keepout in definition.keepouts:
  if side not in keepout['layers']:continue
  xs=[p[0] for p in keepout['polygon']];ys=[p[1] for p in keepout['polygon']]
  if box.intersects(Box(min(xs),min(ys),max(xs),max(ys))):return False
 for other,other_side,_,through in obs:
  if other_side in (side,'both') and box.intersects(other,region.mounting if through else .25):return False
 return True

def region_available(region,obs):
 usable=Box(region.rect.x0+region.edge,region.rect.y0+region.edge,region.rect.x1-region.edge,region.rect.y1-region.edge)
 if usable.x1<=usable.x0 or usable.y1<=usable.y0:return 0.0
 occupied=sum(usable.overlap_area(b) for b,side,_,_ in obs if side in (region.side,'both'))
 return round(max(0,usable.area-occupied),4)

def component_keys(components):
 groups={}
 for c in sorted(components,key=lambda c:(role(c),c.footprint,c.ref)):
  base=(role(c),c.footprint);rank=groups.get(base,0);groups[base]=rank+1
  yield (base[0],base[1],rank),c

def cluster_order(components,pin_nets):
 by_ref={c.ref:c for c in components}
 ics=[c for c in components if c.ref.startswith('U')]
 net_refs=collections.defaultdict(set)
 for (ref,_),net in pin_nets.items():
  if ref in by_ref:net_refs[net].add(ref)
 owner={}
 for c in components:
  if c in ics:owner[c.ref]=c.ref;continue
  attached=dict(c.fields).get('DecouplingOf','')
  if attached:
   matches=[ic for ic in ics if role(ic)==attached or ic.ref==attached]
   if len(matches)==1:owner[c.ref]=matches[0].ref;continue
  scores=collections.Counter()
  for (ref,_),net in pin_nets.items():
   if ref!=c.ref or net.split('/')[-1] in POWER:continue
   for other in net_refs[net]:
    if other!=ref and other in {ic.ref for ic in ics}:scores[other]+=1
  if scores:owner[c.ref]=sorted(scores,key=lambda x:(-scores[x],x))[0]
 def order(c):
  island=bool(dict(c.fields).get('Island'))
  ic=c.ref.startswith('U');decouple='decoupl' in role(c).lower()
  sensitive=bool(dict(c.fields).get('Sensitive',''))
  return (0 if island else 1,owner.get(c.ref,'~'),0 if ic else 1 if decouple else 2 if sensitive else 3,role(c),c.footprint,c.ref)
 return sorted(components,key=order),owner

def place(board_id,board_path=None,netlist_path=None,report_path=None):
 definition=load_definition(ROOT/'design/boards'/f'{board_id}.json')
 if not definition.regions:raise ValueError(f'{board_id}: no placement regions')
 board_path=Path(board_path) if board_path else ROOT/'boards'/board_id/f'{board_id}.kicad_pcb'
 netlist_path=Path(netlist_path) if netlist_path else ROOT/definition.netlist
 report_path=Path(report_path) if report_path else board_path.parent/'reports/placement.json'
 report_path.parent.mkdir(parents=True,exist_ok=True)
 board=pcbnew.LoadBoard(str(board_path));board.SetFileName(str(board_path))
 components,pin_nets=read_netlist(netlist_path)
 metadata={c.ref:c for c in components}
 lock=load_lock(ROOT/'design/grid/placements.lock.json')
 fixed={p['ref']:p for p in selected_hardware(definition,lock)}
 board_refs={fp.GetReference():fp for fp in board.GetFootprints()}
 for ref,p in fixed.items():
  fp=board_refs.get(ref)
  if fp is None or not fp.IsLocked():raise ValueError(f'{ref}: fixed hardware missing/unlocked')
  x,y=to_kicad(p['x_mm'],p['y_mm'])
  if abs(mm(fp.GetPosition().x)-x)>1e-6 or abs(mm(fp.GetPosition().y)-y)>1e-6:raise ValueError(f'{ref}: fixed hardware moved from lockfile')
 regions=regions_for(definition)
 free=collections.defaultdict(list);preserved=[]
 for ref,c in metadata.items():
  if ref in fixed:continue
  fp=board_refs.get(ref)
  if fp is None:raise ValueError(f'{ref}: board footprint missing')
  source_origin=dict(c.fields).get('FootprintOriginMm','')
  if source_origin:
   sx,sy=(float(v) for v in source_origin.split(','))
   pos=fp.GetPosition()
   if abs(mm(pos.x)-100-sx)>1e-5 or abs(mm(pos.y)-50-sy)>1e-5:raise ValueError(f'{ref}: board differs from source footprint origin')
   source_side=dict(c.fields).get('BoardSide','')
   if source_side and str(fp.GetLayerName())!=source_side:raise ValueError(f'{ref}: board differs from source footprint face')
   source_angle=dict(c.fields).get('KiCadOrientationDeg','')
   if source_angle and abs((fp.GetOrientationDegrees()-float(source_angle)+180)%360-180)>1e-5:
    raise ValueError(f'{ref}: board differs from source footprint angle')
  if fp.IsLocked() or not owned(board_id,fp):preserved.append(ref);continue
  block=normalize_block(c)
  if block not in regions:raise ValueError(f'{ref}: Block {block!r} has no region')
  free[block].append(c)
  region_sides={r.side for r in regions[block]}
  requested=dict(c.fields).get('BoardSide','')
  if len(region_sides)>1 and not requested:raise ValueError(f'{ref}: mixed-side cluster requires explicit BoardSide')
  if requested and requested not in region_sides:raise ValueError(f'{ref}: BoardSide conflicts with region')
  selected_side=requested or next(iter(region_sides))
  target=pcbnew.F_Cu if selected_side=='F.Cu' else pcbnew.B_Cu
  if fp.GetLayer()!=target:fp.Flip(fp.GetPosition(),False)
 eligible=set(c.ref for cs in free.values() for c in cs)
 obs=obstacles(board,eligible)
 fixed_obstacles=list(obs)
 report={'schema_version':1,'board_id':board_id,'status':'DRAFT','board':str(board_path),'regions':[],'clusters':[],'placements':[],'preserved_refs':sorted(preserved),'overflow':[],'checks':{'courtyard_overlap':'PENDING KICAD DRC','schematic_parity':'PENDING KICAD DRC'},'notes':['Fixed hardware positions came only from design/grid/placements.lock.json.','Axis-aligned courtyard boxes are conservative; KiCad DRC remains required.']}
 groups=collections.defaultdict(list)
 for instance,rs in regions.items():
  if instance in free:groups[rs[0].family].append(instance)
 placed={}
 try:
  for family in sorted(groups):
   instances=sorted(groups[family],key=lambda i:(regions[i][0].rect.x0,regions[i][0].rect.y0,i))
   base=instances[0];base_regions=regions[base]
   base_keys=dict(component_keys(free[base]))
   if len(base_keys)!=len(free[base]):raise ValueError(f'{base}: duplicate component placement key')
   ordered,owners=cluster_order(free[base],pin_nets)
   key_by_ref={c.ref:k for k,c in base_keys.items()}
   template={}
   for instance in instances:
    current_regions=regions[instance];current_keys=dict(component_keys(free[instance]))
    if set(current_keys)!=set(base_keys):raise PlacementFailure(instance,current_regions[0],'repeated family component signature differs',sum(fp_courtyard(board_refs[c.ref]).area for c in free[instance]),current_regions[0].rect.area)
    if len(current_regions)!=len(base_regions):raise PlacementFailure(instance,current_regions[0],'repeated family region count differs',0,current_regions[0].rect.area)
    dx=current_regions[0].rect.x0-base_regions[0].rect.x0;dy=current_regions[0].rect.y0-base_regions[0].rect.y0
    for before,after in zip(base_regions,current_regions):
     if before.family!=after.family or before.side!=after.side or abs((after.rect.x0-before.rect.x0)-dx)>1e-6 or abs((after.rect.y0-before.rect.y0)-dy)>1e-6 or abs((after.rect.x1-before.rect.x1)-dx)>1e-6 or abs((after.rect.y1-before.rect.y1)-dy)>1e-6:
      raise PlacementFailure(instance,after,'repeated family region is not a translation',0,after.rect.area)
    reference_map={key_by_ref[c.ref]:current_keys[key_by_ref[c.ref]] for c in ordered} if instance==base else {k:current_keys[k] for k in base_keys}
    local=[]
    for base_c in ordered:
     key=key_by_ref[base_c.ref];c=reference_map[key];fp=board_refs[c.ref]
     own=owners.get(base_c.ref)
     anchor_ref=reference_map[key_by_ref[own]].ref if own and own in key_by_ref else None
     island=normalize_island(c,instance)
     source_origin=dict(c.fields).get('FootprintOriginMm','')
     if source_origin:
      target_xy=tuple(float(v) for v in source_origin.split(','))
     elif island:
      if island not in lock or island not in definition.placement_uids:raise ValueError(f'{c.ref}: Island {island!r} is not selected locked hardware')
      target_xy=(lock[island]['x_mm'],lock[island]['y_mm'])
     elif anchor_ref and anchor_ref in placed:
      target_xy=placed[anchor_ref][:2]
     else:
      first=current_regions[0].rect;target_xy=((first.x0+first.x1)/2,(first.y0+first.y1)/2)
     if source_origin:
      x,y=(float(v) for v in source_origin.split(','));box=offsets(fp).shift(x,y)
      chosen=next((ri for ri,region in enumerate(current_regions) if region.side==dict(c.fields).get('BoardSide') and is_clear(box,region.side,region,definition,obs)),None)
      if chosen is None:
       region=current_regions[0];needed=sum(offsets(board_refs[item.ref]).area for item in free[instance])
       raise PlacementFailure(instance,region,f'{c.ref}: source courtyard/origin violates region or obstacle',needed,region_available(region,obs))
      ri=chosen;region=current_regions[ri]
     elif instance==base:
      shape=offsets(fp);chosen=None
      for ri,region in enumerate(current_regions):
       if region.side != (dict(c.fields).get('BoardSide','') or region.side):continue
       for x,y in candidate_centres(region,shape,target_xy):
        box=shape.shift(x,y)
        if is_clear(box,region.side,region,definition,obs):chosen=(x,y,ri,box);break
       if chosen:break
      if chosen is None:
       region=current_regions[0];needed=sum((offsets(board_refs[x.ref]).area for x in free[instance]))
       raise PlacementFailure(instance,region,f'{c.ref}: no legal courtyard position',needed,region_available(region,obs))
      x,y,ri,box=chosen;template[key]=(x-base_regions[ri].rect.x0,y-base_regions[ri].rect.y0,ri)
     else:
      tx,ty,ri=template[key];region=current_regions[ri];x=region.rect.x0+tx;y=region.rect.y0+ty;box=offsets(fp).shift(x,y)
      if not is_clear(box,region.side,region,definition,obs):
       needed=sum(offsets(board_refs[x.ref]).area for x in free[instance])
       raise PlacementFailure(instance,region,f'{c.ref}: translated template collides or leaves region',needed,region_available(region,obs))
     placed[c.ref]=(x,y,ri,box,region.side)
     obs.append((box,region.side,'placed:'+c.ref,False));local.append((c.ref,key,ri,box.area))
    clusters=collections.defaultdict(list)
    current_key_by_ref={component.ref:key for key,component in current_keys.items()}
    for c in free[instance]:
     key=current_key_by_ref[c.ref]
     base_owner=owners.get(base_keys[key].ref)
     owner=current_keys[key_by_ref[base_owner]].ref if base_owner else None
     island=normalize_island(c,instance)
     cluster='island:'+island if island else 'ic:'+owner if owner else 'unassigned'
     clusters[cluster].append(c.ref)
    for name,refs in sorted(clusters.items()):report['clusters'].append({'instance':instance,'cluster':name,'refs':sorted(refs)})
    for ri,region in enumerate(current_regions):
     region_items=[x for x in local if x[2]==ri];area=sum(x[3] for x in region_items)
     report['regions'].append({'instance':instance,'family':family,'index':ri,'side':region.side,'rect':[region.rect.x0,region.rect.y0,region.rect.x1,region.rect.y1],'area_available_mm2':region_available(region,fixed_obstacles),'courtyard_area_mm2':round(area,4),'utilisation_percent':round(100*area/region.rect.area,3),'component_count':len(region_items)})
 except PlacementFailure as e:
  report['status']='OVERFLOW'
  report['overflow'].append({'instance':e.instance,'region':[e.region.rect.x0,e.region.rect.y0,e.region.rect.x1,e.region.rect.y1],'reason':e.reason,'area_needed_mm2':round(e.needed,4),'area_available_mm2':round(e.available,4)})
  report_path.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
  raise
 # A successful plan moves only generator-owned unlocked free footprints.
 for ref,(x,y,ri,box,side) in sorted(placed.items()):
  board_refs[ref].SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x+100),pcbnew.FromMM(y+50)))
  report['placements'].append({'ref':ref,'block':normalize_block(metadata[ref]),'region_index':ri,'side':side,'x_mm':x,'y_mm':y,'courtyard_mm':[round(box.x0,4),round(box.y0,4),round(box.x1,4),round(box.y1,4)]})
 report['status']='PLACED DRAFT'
 owned_refs={ref for ref,fp in board_refs.items() if owned(board_id,fp)}
 pcbnew.SaveBoard(str(board_path),board)
 owned_zone_ids={item_uuid(z) for z in board.Zones() if z.GetZoneName().startswith(f'pcbgen:{board_id}:')}
 normalize_file(board_path,board_id,owned_refs,{},False,owned_zone_ids)
 report_path.write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
 print(f'{board_id}: placed {len(placed)} free footprints in {len(report["regions"])} regions; {len(preserved)} locked/unowned preserved; draft')
 return report

def main():
 parser=argparse.ArgumentParser();parser.add_argument('board_id');parser.add_argument('--board',type=Path);parser.add_argument('--netlist',type=Path);parser.add_argument('--report',type=Path)
 args=parser.parse_args()
 try:place(args.board_id,args.board,args.netlist,args.report)
 except PlacementFailure as exc:
  print(f'placement overflow in {exc.instance}: {exc.reason}; needed {exc.needed:.3f} mm², available {exc.available:.3f} mm²',file=sys.stderr)
  return 1
 return 0
if __name__=='__main__':raise SystemExit(main())
