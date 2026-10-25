#!/usr/bin/env python3
"""Explicit conditional closed-end copper geometry for NEW staged transfers."""
import argparse,copy,hashlib,json,resource
from pathlib import Path
BANDS={'F.Cu':[0,.07],'In1.Cu':[.12,.19],'In2.Cu':[.24,.31],
       'In3.Cu':[1.29,1.36],'In4.Cu':[1.41,1.48],'B.Cu':[1.53,1.6]}
LAYERS=list(BANDS)
def need(c,m):
 if not c:raise ValueError(m)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def staged(o):return o['kind']=='via' and o.get('via_type') in ('microvia','buried_via')
def expected(o):
 need(staged(o) and o.get('source_pad_uuid') and not o.get('source_span'),'only new authenticated pad-associated staged vias')
 need(o.get('filled_and_capped_required') is True,'explicit capped process required')
 layers=sorted(o['layers'],key=LAYERS.index)
 need(len(layers)==2 and LAYERS.index(layers[1])-LAYERS.index(layers[0])==1,'adjacent staged foils required')
 need((o['via_type']=='buried_via')==(layers==['In2.Cu','In3.Cu']),'stage type matches stack')
 need(o.get('barrel_wall_min_mm')==.025,'explicit .025 wall requirement')
 radius=o['drill_mm']/2+.025
 need(radius<o['diameter_mm']/2,'cap disk contained in capture pad with positive registration margin')
 band=[BANDS[layers[0]][1],BANDS[layers[1]][0]]
 caps=[{'id':o['id']+'-CAP-'+layer,'via_id':o['id'],'net':o['net'],'layer':layer,
        'center_mm':list(o['center_mm']),'radius_mm':radius,'z_band_mm':list(BANDS[layer]),
        'copper_thickness_mm':.07,'shape':'closed_copper_disk','process_qualified':False}
       for layer in layers]
 return caps,{'via_id':o['id'],'net':o['net'],'center_mm':o['center_mm'],
              'inner_radius_mm':o['drill_mm']/2,'outer_radius_mm':radius,
              'z_band_mm':band,'shape':'annular_copper_barrel','process_qualified':False}
def materialize(source):
 out=copy.deepcopy(source);caps=[];barrels=[]
 for o in out['objects']:
  if not staged(o):continue
  cc,bb=expected(o);caps.extend(cc);barrels.append(bb)
  prior={k:o[k] for k in ['barrel_total_height_mm','center_plane_span_mm'] if k in o}
  o['superseded_open_barrel_extent_metadata']=prior
  o.pop('center_plane_span_mm',None)
  o['barrel_total_height_mm']=bb['z_band_mm'][1]-bb['z_band_mm'][0]
  o['closed_end_cap_solid_ids']=[c['id'] for c in cc]
  o['barrel_dielectric_z_band_mm']=bb['z_band_mm']
 out['staged_cap_solids']={'schema':'closed-stage-solids-v1','foil_bands_mm':copy.deepcopy(BANDS),
   'caps':caps,'barrels':barrels,
   'process':'Filled and planarized staged bore with a continuous .07mm copper cap at each endpoint foil; bore terminates at cap face.',
   'fill_conductivity_credited':False,'process_qualified':False,'registration_qualified':False,
   'electrical_limit':'Finite cap spreading, barrel fields and trace compatibility still required. Shared cap volume must be charged once; no ideal equipotential node is implied.'}
 validate(out)
 return out

def validate(source):
 rows=[o for o in source['objects'] if staged(o)];model=source.get('staged_cap_solids')
 if not rows:
  need(not model or not model.get('caps') and not model.get('barrels'),'orphan cap solids');return {}
 need(model and model.get('schema')=='closed-stage-solids-v1','staged vias require explicit closed-cap material geometry')
 need(model.get('foil_bands_mm')==BANDS,'exact fixed six-foil depth bands')
 need(model.get('fill_conductivity_credited') is False and model.get('process_qualified') is False and model.get('registration_qualified') is False,'conditional cap qualification')
 caps={c['id']:c for c in model['caps']};barrels={b['via_id']:b for b in model['barrels']}
 need(len(caps)==len(model['caps']) and len(barrels)==len(model['barrels']),'duplicate cap/barrel identity')
 expected_caps={};expected_barrels={}
 for o in rows:
  pad=next((p for p in source['objects'] if p['id']==o['source_pad_uuid'] and p['kind']=='pad'),None)
  need(pad and pad.get('net')==o['net'],'exact same-net source pad association')
  cc,bb=expected(o);expected_caps.update({c['id']:c for c in cc});expected_barrels[o['id']]=bb
  need(o.get('closed_end_cap_solid_ids')==[c['id'] for c in cc] and o.get('barrel_dielectric_z_band_mm')==bb['z_band_mm'],'via actual solid binding')
  need(abs(o['barrel_total_height_mm']-(bb['z_band_mm'][1]-bb['z_band_mm'][0]))<1e-12,'barrel excludes copper caps')
 need(caps==expected_caps and barrels==expected_barrels,'cap/barrel geometry must exactly match authored via/stack')
 return barrels

def main():
 resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3));p=argparse.ArgumentParser();p.add_argument('--board',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 need(not a.output.exists(),'fresh output required');seals={str(q):sha(q) for q in [a.board,Path(__file__)]};source=json.loads(a.board.read_text());need('staged_cap_solids' not in source,'materialize once per source epoch')
 out=materialize(source);out['staged_cap_solids']['input_sha256']=seals
 need(all(sha(Path(q))==h for q,h in seals.items()),'input changed')
 a.output.write_text(json.dumps(out,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n')
 print(json.dumps({'board':out['board'],'caps':len(out['staged_cap_solids']['caps']),'barrels':len(out['staged_cap_solids']['barrels'])}))
if __name__=='__main__':main()
