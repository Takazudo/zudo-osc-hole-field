#!/usr/bin/env python3
"""Serialize reviewed source access into disposable, explicitly unfilled PCBs.

Clipped hole-bearing polygons remain the companion conductor model. Native
refill, connectivity, process qualification and adoption are never inferred.
"""
import argparse,hashlib,json,re,resource,sys,uuid
from pathlib import Path
import staged_caps
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[5]
sys.path.insert(0,str(ROOT))
from scripts.pcbgen.uuid_tools import top_level_spans
LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
NS=uuid.UUID('a51b1f21-91d3-5e06-a242-b532f6430001')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def digest(s):return hashlib.sha256(s.encode()).hexdigest()
def uid(s):return str(uuid.uuid5(NS,s))
def need(c,m):
 if not c:raise ValueError(m)
def q(s):return json.dumps(s,ensure_ascii=False)
def xy(p):return f'{p[0]+100:.9f} {p[1]+50:.9f}'

def stack():
 rows=[];depth=0.;lines=['(stackup']
 for i,layer in enumerate(LAYERS):
  rows.append({'layer':layer,'depth_band_mm':[depth,depth+.07],'copper_thickness_mm':.07});depth+=.07
  lines.append(f'(layer {q(layer)} (type "copper") (thickness .07))')
  if i<5:
   thickness=[.05,.05,.98,.05,.05][i]
   rows.append({'layer':f'dielectric {i+1}','depth_band_mm':[depth,depth+thickness],'thickness_mm':thickness});depth+=thickness
   lines.append(f'(layer "dielectric {i+1}" (type "dielectric") (thickness {thickness}) (material "UNSELECTED conditional staged dielectric"))')
 need(abs(depth-1.6)<1e-12,'six-layer sum differs from fixed1.6mm')
 return '\n'.join(lines+[')']),rows

def add_stack(text):
 blocks=[(a,b,text[a:b]) for a,b in top_level_spans(text)]
 enabled=[s for _,_,s in blocks if s.startswith('(layers')]
 need(len(enabled)==1 and re.findall(r'\(\d+\s+"([^"]+\.Cu)"',enabled[0])==LAYERS,'enabled six-layer order')
 general=[s for _,_,s in blocks if s.startswith('(general')]
 need(len(general)==1 and float(re.search(r'\(thickness\s+([\d.]+)\)',general[0])[1])==1.6,'fixed board thickness')
 setups=[(a,b,s) for a,b,s in blocks if s.startswith('(setup')];need(len(setups)==1,'unique setup')
 a,b,s=setups[0];need(not any(s[x:y].startswith('(stackup') for x,y in top_level_spans(s)),'unexpected prior physical stack')
 fragment,rows=stack();return text[:a]+s.replace('(setup','(setup\n'+fragment,1)+text[b:],rows

def serialize_new(o):
 net=q(o['net']);identity=uid(o['id']);kind=o['kind'];layers=o['layers']
 if kind=='segment':
  need(len(layers)==1 and len(o['path_mm'])==2,'single straight access segment')
  return f'(segment (start {xy(o["path_mm"][0])}) (end {xy(o["path_mm"][1])}) (width {o["width_mm"]}) (layer {q(layers[0])}) (net {net}) (uuid "{identity}"))'
 if kind=='via':
  kind=o.get('via_type','through');kind={'microvia':'micro','buried_via':'buried'}.get(kind,kind);need(kind in ('through','micro','blind','buried'),'known via type')
  need(all(x in LAYERS for x in layers) and len(layers)>=2,'explicit via layer path')
  endpoints=sorted([layers[0],layers[-1]],key=LAYERS.index)
  if kind=='through':need(set(layers)==set(LAYERS),'through via spans all layers')
  if kind=='micro':need(abs(LAYERS.index(endpoints[0])-LAYERS.index(endpoints[1]))==1,'adjacent microvia foils')
  token='' if kind=='through' else kind
  process=' (capping yes) (filling yes)' if o.get('filled_and_capped_required') else ''
  return f'(via {token} (at {xy(o["center_mm"])}) (size {o["diameter_mm"]}) (drill {o["drill_mm"]}) (layers {q(endpoints[0])} {q(endpoints[1])}) (net {net}) (uuid "{identity}"){process})'
 if kind=='zone':
  need(len(layers)==1 and o.get('new_source_polygon_unfilled'),'explicit unfilled source plane')
  pts=' '.join(f'(xy {xy(p)})' for p in o['polygon_mm'])
  return f'(zone (net {net}) (layer {q(layers[0])}) (uuid "{identity}") (hatch edge .5) (connect_pads yes (clearance .25)) (min_thickness .01) (fill yes (thermal_gap .25) (thermal_bridge_width .25)) (polygon (pts {pts})))'
 raise ValueError('unreviewed new object '+kind)

def build(candidate,normalized,design_path,out):
 need(not out.exists(),'fresh output directory required')
 need(out.is_absolute() and not out.is_relative_to(ROOT),'disposable path outside repository required')
 original=ROOT/'boards/osc-core/osc-core.kicad_pcb';source=original.read_text();receipt=json.loads((candidate/'receipt.json').read_text())
 need(sha(original)==receipt['input_sha256']['boards/osc-core/osc-core.kicad_pcb'],'canonical source drift')
 design=json.loads(design_path.read_text());seals={str(p):sha(p) for p in normalized+[original,design_path,candidate/'receipt.json',candidate/'terminals.json',Path(__file__),Path(staged_caps.__file__)]};outputs={}
 for path in normalized:
  d=json.loads(path.read_text());board=d['board'];need(board in ('KA','KB') and board not in outputs,'one of each board')
  staged_caps.validate(d)
  base=candidate/(board+'.kicad_pcb');seals[str(base)]=sha(base);need(sha(base)==receipt['boards'][board]['sha256'],'candidate PCB drift')
  text=base.read_text()
  # The original global fabrication defaults remain unchanged. Only the300
  # newly authored terminal transfers receive their explicit process override.
  terminal_vias={v['uuid'] for t in json.loads((candidate/'terminals.json').read_text()) if t['board']==board for v in t['vias']}
  changed=[]
  for a,b in top_level_spans(text):
   raw=text[a:b]
   if not raw.startswith('(via'):continue
   match=re.search(r'\(uuid "([^"]+)"\)',raw)
   if match and match[1] in terminal_vias:changed.append((a,b,raw[:-1]+' (capping yes) (filling yes))'))
  need(len(changed)==150,'exact150new terminal transfers perboard')
  for a,b,new in reversed(changed):text=text[:a]+new+text[b:]
  seen=set(re.findall(r'\(uuid "([^"]+)"\)',text));extra=[];mapping=[];new_mapping=[];replays=set(d['source_ownership']['single_owner_rail_replay_keys']);found=set()
  for o in d['objects']:
   if o['id'] in replays:
    a,b=o['source_span'];raw=source[a:b];need(digest(raw)==o['source_sha256'],'replay source span/hash mismatch');need(o['id']==f'{a}:{b}:{digest(raw)}','replay key mismatch')
    found.add(o['id']);old=o['source_uuid'];new=old;need(re.findall(r'\(uuid "([^"]+)"\)',raw)==[old],'exact replay UUID binding')
    if old in seen:
     new=uid(board+'/replay/'+o['id']);need(new not in seen,'UUID collision');need(raw.count(f'(uuid "{old}")')==1,'single replay UUID');raw=raw.replace(f'(uuid "{old}")',f'(uuid "{new}")')
    seen.add(new);extra.append(raw);mapping.append({'source_key':o['id'],'source_uuid':old,'output_uuid':new,'geometry_and_net_unchanged':True})
   elif 'source_pad_uuid' in o or o.get('new_source_polygon_unfilled'):
    extra.append(serialize_new(o));new_mapping.append({'source_id':o['id'],'output_uuid':uid(o['id']),'kind':o['kind']})
  need(found==replays,'missing authenticated replay objects')
  zones=[o for o in d['objects'] if o.get('new_source_polygon_unfilled')]
  if not any(o['net']=='+5V' for o in zones):
   plane={'id':board+'-NEW-In2.Cu-+5V','kind':'zone','net':'+5V','layers':['In2.Cu'],'polygon_mm':design['layer_construction']['outline_inset_0p6mm_polygon_mm'],'new_source_polygon_unfilled':True}
   extra.append(serialize_new(plane));new_mapping.append({'source_id':plane['id'],'output_uuid':uid(plane['id']),'kind':'zone'})
  text,bands=add_stack(text);end=text.rfind(')');text=text[:end]+'\n'+'\n'.join(extra)+'\n'+text[end:]
  uuids=re.findall(r'\(uuid "([^"]+)"\)',text);need(len(uuids)==len(set(uuids)),'duplicate output UUID')
  need(len(extra)==len(mapping)+len(new_mapping),'all appended objects mapped')
  outputs[board]={'text':text,'replay_mapping':mapping,'new_object_mapping':new_mapping,'terminal_process_overrides':sorted(terminal_vias),'appended_blocks':len(extra),'stack':bands,'normalized_input_sha256':sha(path),'staged_access':d.get('staged_access')}
  outputs[board]['staged_cap_solids']=d.get('staged_cap_solids')
 need(set(outputs)=={'KA','KB'},'complete two-board input')
 for p,h in seals.items():need(sha(Path(p))==h,'input changed during serialization')
 out.mkdir(parents=True)
 for board,d in outputs.items():
  p=out/(board+'.kicad_pcb');p.write_text(d.pop('text'));d.update(path=p.name,sha256=sha(p),bytes=p.stat().st_size)
 result={'status':'SOURCE_ACCESS_SERIALIZATION_NATIVE_UNRUN','input_sha256':seals,'boards':outputs,'native_calls':0,'acceptance':False,'clipped_polygon_scope':'Separate exact hole-bearing source geometry; these PCB zones have no fabricated native fills and supply no native connectivity credit.','process_scope':'New required filled/capped vias and300terminaltransfers have explicit per-via flags; original global defaults and old copper remain unchanged. Flags declare manufacturing requirements, never process qualification.','serialization_reference':'https://github.com/KiCad/kicad-source-mirror/blob/10.0/pcbnew/pcb_io/kicad_sexpr/pcb_io_kicad_sexpr.cpp'}
 (out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({b:{k:d[k] for k in ['sha256','bytes','appended_blocks']} for b,d in outputs.items()}))

if __name__=='__main__':
 resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--ka',type=Path,required=True);p.add_argument('--kb',type=Path,required=True);p.add_argument('--design',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();build(a.candidate,[a.ka,a.kb],a.design,a.output)
