#!/usr/bin/env python3
"""Deterministic disposable joined-feed construction, never native or canonical."""
import argparse,gzip,hashlib,json,math,resource,sys,time,uuid
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[5]
sys.path.insert(0,str(ROOT));sys.path.insert(0,str(HERE))
import contact
NS=uuid.UUID('24b9485b-ecfd-5313-a726-af8e0e84e242')
NETS=['+12V','-12V','+5V','AGND','AGND','AGND']
def uid(s):return str(uuid.uuid5(NS,s))
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(out,name,obj):
 b=(json.dumps(obj,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode();p=out/name;p.write_bytes(gzip.compress(b,mtime=0) if name.endswith('.gz') else b)
def load(p):return json.loads(p.read_text())
def terminals():
 rows=[];footprints={};via_blocks={};contacts=[]
 a=.5933040689317951;b=.5927989259019525;c=.5445913286478836
 for board,face,z,norm in [('KA','B.Cu',-101.6,-1),('KB','F.Cu',-126.,1)]:
  footprints[board]=[];via_blocks[board]=[]
  for i,sign in enumerate([1,-1,1,1,-1,1]):
   w=[a*(1 if board=='KA' else -1),sign*b,c];anchor=[23+17*(i%3)+(58 if board=='KB' else 0),15.5+9*(i//3),2]
   land=[anchor[j]-2/c*w[j] for j in range(3)];ref=f'TP247{(i+1+(6 if board=="KB" else 0)):03d}';name=f'{board}/W{i+1}';net=NETS[i]
   assert ref not in (ROOT/'boards/osc-core/osc-core.kicad_pcb').read_text(),ref
   world=lambda p:[land[0]+p[0],land[1]+p[1],z+norm*p[2]]
   geom=contact.endpoint_primitives(w,copper_axis_end_station_mm=2/c+2.5)
   patches=[]
   for p in geom['patches']:
    patches.append(p|{'solder_current_density_local_A_per_mm2':p['solder_current_density_vector_A_per_mm2'],'solder_current_density_world_A_per_mm2':[p['solder_current_density_vector_A_per_mm2'][0],p['solder_current_density_vector_A_per_mm2'][1],norm*p['solder_current_density_vector_A_per_mm2'][2]]}|{k.replace('_mm','_xyz_mm'):[world(q) for q in p[k]] for k in ['foil_vertices_mm','tip_vertices_mm','copper_end_vertices_mm']})
   contacts.append({'id':name,'source_endpoint_id':f"CS247-KA-KB-{'SRC' if board=='KA' else 'DST'}-{i+1}",'source_wire_id':f'CS247-KA-KB-W{i+1}','canonical_wire_direction':'KA-to-KB','canonical_incidence':1 if board=='KA' else -1,'board':board,'wire':i+1,'ref':ref,'pad':'1','pad_uuid':uid(name+'/pad'),'face':face,'land_center_xyz_mm':[land[0],land[1],z],'outgoing_axis_local':w,'foil_patches':patches,'normal_bundle_envelope_radius_mm':1.,'insulation_cut_axis_station_from_land_mm':3.75,'insulation_cut_tolerance_mm':.05,'filled_cap_copper_thickness_min_mm':.07,'current_field':{k:v for k,v in geom.items() if k!='patches'}})
   x,y=land[0]+100,land[1]+50;silk=face[0]+'.SilkS';fab=face[0]+'.Fab';court=face[0]+'.CrtYd'
   fp=f'''(footprint "epic242:CS247_CappedWireLand" (layer "{face}") (uuid "{uid(name+'/footprint')}") (at {x:.9f} {y:.9f})
 (property "Reference" "{ref}" (at 0 -3) (layer "{silk}") (effects (font (size 1 1) (thickness .15))))
 (property "Value" "CS247-{net}-W{i+1}" (at 0 3) (layer "{fab}") (effects (font (size 1 1) (thickness .15))))
 (attr smd) (solder_mask_margin .1)
 (fp_rect (start -2.5 -2.5) (end 2.5 2.5) (stroke (width .05) (type default)) (fill none) (layer "{court}") (uuid "{uid(name+'/courtyard')}"))
 (pad "1" smd rect (at 0 0) (size 4 4) (layers "{face}" "{face[0]}.Mask") (net "{net}") (uuid "{uid(name+'/pad')}")))'''
   footprints[board].append(fp);vias=[]
   for j in range(5):
    for k in range(5):
     vx=x+(j-2)*.7;vy=y+(k-2)*.7;vuid=uid(f'{name}/via/{j}/{k}')
     via_blocks[board].append(f'(via (at {vx:.9f} {vy:.9f}) (size .7) (drill .3) (layers "F.Cu" "B.Cu") (net "{net}") (uuid "{vuid}"))')
     vias.append({'uuid':vuid,'xy_mm':[vx-100,vy-50],'diameter_mm':.7,'drill_mm':.3,'barrel_wall_min_mm':.025,'process':'Filled/capped; continuous .07mm copper at finite injection patches'})
   rows.append({'id':name,'source_endpoint_id':f"CS247-KA-KB-{'SRC' if board=='KA' else 'DST'}-{i+1}",'source_wire_id':f'CS247-KA-KB-W{i+1}','canonical_wire_direction':'KA-to-KB','canonical_incidence':1 if board=='KA' else -1,'board':board,'wire':i+1,'net':net,'ref':ref,'pad':'1','pad_uuid':uid(name+'/pad'),'footprint_uuid':uid(name+'/footprint'),'face':face,'center_xyz_mm':[land[0],land[1],z],'anchor_xyz_mm':[anchor[0],anchor[1],z+norm*2],'outgoing_axis_world':[w[0],w[1],norm*w[2]],'outgoing_axis_local':w,'reserve_xy_mm':[land[0]-3,land[1]-3,land[0]+3,land[1]+3],'copper_xy_mm':[land[0]-2,land[1]-2,land[0]+2,land[1]+2],'vias':vias})
 return rows,footprints,via_blocks,contacts

def build(out):
 resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3));start=time.monotonic()
 if out.exists():raise ValueError('choose fresh output path')
 if out.is_relative_to(ROOT) and not out.is_relative_to(ROOT/'design/partition/core-split/candidates/pilots/generated'):raise ValueError('refuse tracked output')
 import mechanical
 lock=load(ROOT/'design/partition/core-split/candidates/input-lock.json')
 hashes=dict(lock['input_sha256'])
 for p in [ROOT/'scripts/partition/core_split_candidates.py',ROOT/'design/partition/core-split/candidates/two.json',HERE/'construct.py',HERE/'mechanical.py',HERE/'contact.py']:
  hashes[str(p.relative_to(ROOT))]=sha(p)
 for p,h in hashes.items():assert sha(ROOT/p)==h,p
 rows,fps,via_blocks,contacts=terminals();solids=mechanical.build()
 out.mkdir(parents=True);save(out,'terminals.json',rows);save(out,'contacts.json.gz',contacts);save(out,'mechanical.json.gz',solids)
 from scripts.partition.core_split_candidates import Inputs,RAILS,parsed
 from scripts.pcbgen.netlist import one,many
 from scripts.pcbgen.uuid_tools import replace_spans,REF_RE
 inp=Inputs();two=load(ROOT/'design/partition/core-split/candidates/two.json');inventory={tuple(r['source_span']):r for r in inp.copper};dispositions=[];boards={}
 supports=[]
 for a,b,kind in inp.blocks:
  if kind!='footprint':continue
  block=inp.text[a:b];match=REF_RE.search(block)
  if not match or not match[1].startswith('MH_K-SUP-'):continue
  node=parsed(block);at=list(map(float,one(node,'at')[1:3]))
  if at not in [[106.5,60.5],[411.5,60.5]]:continue
  pads=many(node,'pad');assert len(pads)==1 and pads[0][2]=='np_thru_hole'
  assert float(one(pads[0],'drill')[1])==2.2
  supports.append({'ref':match[1],'physical_xy_mm':at,'drill_mm':2.2,'source_footprint_sha256':hashlib.sha256(block.encode()).hexdigest()})
 assert len(supports)==2,supports
 save(out,'support-bindings.json',supports)
 for board,key in [('KA','two-A'),('KB','two-B')]:
  refs=set(two['boards'][key]['refs']);eligible={n for n,rs in inp.net_refs.items() if n not in RAILS and rs<=refs};edits=[];kept=0
  for a,b,kind in inp.blocks:
   block=inp.text[a:b]
   if kind=='footprint':
    match=REF_RE.search(block)
    if match and match[1] in inp.components and match[1] not in refs:edits.append((a,b,''))
   elif kind in ('segment','via','zone'):
    row=inventory[a,b];keep=(kind=='zone' and '(keepout' in block) or (kind!='zone' and row['net_token'] in eligible)
    dispositions.append({'board':board,'source_span':[a,b],'sha256':row['sha256'],'uuid':row['uuid'],'net':row['net_token'],'disposition':'RETAIN_EXACT_OWNED_LOCAL_OR_RULE_AREA' if keep else 'REMOVE_FROM_DISPOSABLE_CONTEXT_RECONSTRUCT_COUPLED_ACCESS' if row['net_token'] in RAILS else 'OTHER_OWNER_OR_CUT_BOUNDARY_NOT_DUPLICATED'})
    if keep:kept+=1
    else:edits.append((a,b,''))
  text=replace_spans(inp.text,edits);idx=text.rfind(')');text=text[:idx]+'\n'+'\n'.join(fps[board]+via_blocks[board])+'\n'+text[idx:]
  p=out/(board+'.kicad_pcb');p.write_text(text);boards[board]={'path':p.name,'sha256':sha(p),'bytes':p.stat().st_size,'retained_source_copper_and_rule_areas':kept,'new_lands':6,'new_vias':150,'rail_access_status':'REQUIRES_EXPLICIT_CONSTRUCTED_LAYER_OPERATOR'}
 save(out,'source-dispositions.json.gz',dispositions)
 for p,h in hashes.items():assert sha(ROOT/p)==h,p
 receipt={'status':'DISPOSABLE_PHYSICAL_SOURCE_CONSTRUCTION_NATIVE_NOT_RUN','input_sha256':hashes,'boards':boards,'terminal_count':len(rows),'contact_count':len(contacts),'mechanical_solids':len(solids['solids']),'source_dispositions':len(dispositions),'elapsed_seconds':time.monotonic()-start,'peak_memory_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'native_calls':0,'canonical_changes':0,'acceptance':False}
 save(out,'receipt.json',receipt);print(json.dumps(receipt))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);a=p.parse_args();build(a.output.resolve())
