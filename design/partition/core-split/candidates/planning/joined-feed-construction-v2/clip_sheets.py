#!/usr/bin/env python3
"""Clip the four E16 rail sheets around every other-net copper/drill obstacle.

Unfilled source geometry only: KiCad refill, thermal spokes and DRC are not
inferred. Clearances come from boards/osc-core/osc-core.kicad_pro (Rails and
Ground net classes, min_hole_clearance) and the reviewed access design.
"""
import argparse,hashlib,json,math,resource,time
from pathlib import Path
import shapely
import selective_annulus
from shapely.geometry import Point,Polygon,LineString
from shapely.ops import unary_union
HERE=Path(__file__).resolve().parent
NET_LAYER={'AGND':'In1.Cu','+5V':'In2.Cu','-12V':'In3.Cu','+12V':'In4.Cu'}
CLEARANCE_MM=.25
HOLE_CLEARANCE_MM=.25
MIN_WIDTH_MM=.25
def need(c,m):
 if not c:raise ValueError(m)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def copper(o,layer=None):
 if o['kind']=='via':return Point(o['center_mm']).buffer(selective_annulus.diameter(o,layer)/2,quad_segs=16)
 if o['kind']=='segment':return LineString(o['path_mm']).buffer(o['width_mm']/2,quad_segs=16)
 if o['kind']=='pad':return Polygon(o['polygon_mm'])
 return None
def ring(r):return [[round(x,6),round(y,6)] for x,y in r.coords[:-1]]
def clip(source,outline):
 base=Polygon(outline);need(base.is_valid,'invalid outline');sheets={};report={}
 selective_annulus.validate_source(source)
 objects=source['objects']
 for net,layer in NET_LAYER.items():
  cuts=[]
  for o in objects:
   if layer not in o.get('layers',[]):continue
   if o['kind']=='rule_area':
    if o['rules'].get('copperpour')=='not_allowed':cuts.append(Polygon(o['polygon_mm']))
    continue
   if o.get('net')!=net:
    g=copper(o,layer)
    if g is not None:cuts.append(g.buffer(CLEARANCE_MM,quad_segs=8))
    if o.get('drill_mm',0)>0:cuts.append(Point(o['center_mm']).buffer(o['drill_mm']/2+HOLE_CLEARANCE_MM,quad_segs=16))
  sheet=base.difference(unary_union(cuts))
  # Zone fill drops copper narrower than its minimum width.
  sheet=sheet.buffer(-MIN_WIDTH_MM/2,quad_segs=8).buffer(MIN_WIDTH_MM/2,quad_segs=8).intersection(base)
  # Serialized coordinates are 1 um grid points; snap before splitting so every piece stays valid.
  sheet=shapely.set_precision(sheet,1e-6)
  parts=[g for g in getattr(sheet,'geoms',[sheet]) if g.geom_type=='Polygon' and g.area>1e-6]
  sheets[net]=[{'id':f'{source["board"]}-{net}-SHEET-{i:04d}','net':net,'layer':layer,
               'polygon_mm':ring(p.exterior),'holes_mm':[ring(r) for r in p.interiors]}
              for i,p in enumerate(sorted(parts,key=lambda p:-p.area))]
  for row in sheets[net]:need(Polygon(row['polygon_mm'],row['holes_mm']).is_valid,'invalid serialized sheet '+row['id'])
  report[net]={'layer':layer,'cut_count':len(cuts),'pieces':len(parts),'area_mm2':round(sum(p.area for p in parts),6),'largest_mm2':round(max((p.area for p in parts),default=0),6)}
 return sheets,report
def main():
 resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
 p=argparse.ArgumentParser();p.add_argument('--filtered-board',type=Path,required=True);p.add_argument('--design',type=Path,default=HERE/'evidence/board-access-design.json');p.add_argument('--output',type=Path,required=True)
 # Accepted for evaluate_access.py's step interface; clipping is this tool's only mode.
 p.add_argument('--clip-only',action='store_true');a=p.parse_args()
 need(not a.output.exists(),'fresh output required');start=time.monotonic()
 seals={'filtered_board':sha(a.filtered_board),'design':sha(a.design),'method':sha(Path(__file__)),'selective_annulus_method':sha(Path(selective_annulus.__file__))}
 source=json.loads(a.filtered_board.read_text());outline=json.loads(a.design.read_text())['layer_construction']['outline_inset_0p6mm_polygon_mm']
 sheets,report=clip(source,outline)
 need(sha(a.filtered_board)==seals['filtered_board'],'input changed')
 out={'schema':'e16-clipped-sheets-v1','board':source['board'],'input_sha256':seals,'clipped_sheets':sheets,'new_objects':[],'report':report,
      'parameters_mm':{'clearance':CLEARANCE_MM,'hole_clearance':HOLE_CLEARANCE_MM,'min_width':MIN_WIDTH_MM},
      'limits':'Unfilled source projection; no thermal relief, refill or native DRC is inferred.','native_calls':0}
 with a.output.open('w') as f:json.dump(out,f,sort_keys=True,separators=(',',':'),allow_nan=False);f.write('\n')
 print(json.dumps({'board':source['board'],'report':report,'elapsed_seconds':round(time.monotonic()-start,2),'peak_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}))
if __name__=='__main__':main()
