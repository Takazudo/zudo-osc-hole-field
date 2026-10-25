#!/usr/bin/env python3
"""Normalize one disposable candidate PCB into the E16 source-object epoch.

Replaces the uncommitted V15 helper (/tmp/feed-v2-board-access.py, SHA-256
18b4daeb...) whose bytes were never retained. E16 is a new epoch: its counts
are recomputed and are not comparable to V15 receipts.
"""
import argparse,hashlib,json,math,re,resource,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
RAILS={'AGND','+12V','-12V','+5V'}
# board_context.xy() serializes normalized coordinates with this fixed offset.
OFFSET=(100.,50.)
TOKEN=re.compile(r'"((?:[^"\\]|\\.)*)"|([()])|([^\s()"]+)')
def need(c,m):
 if not c:raise ValueError(m)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def parse(text):
 stack=[[]]
 for m in TOKEN.finditer(text):
  s,b,a=m.groups()
  if b=='(':stack.append([])
  elif b==')':x=stack.pop();stack[-1].append(x)
  else:stack[-1].append(('S',s) if s is not None else a)
 need(len(stack)==1 and len(stack[0])==1,'unbalanced s-expression');return stack[0][0]
def val(x):return x[1] if isinstance(x,tuple) else x
def kids(node,name):return [c for c in node if isinstance(c,list) and c and c[0]==name]
def one(node,name):
 found=kids(node,name);need(len(found)<=1,'repeated '+name);return found[0] if found else None
def at(node):
 a=one(node,'at');return float(a[1]),float(a[2]),(float(a[3]) if len(a)>3 else 0.)
def cu_layers(node):
 names=[val(x) for x in one(node,'layers')[1:]]
 if '*.Cu' in names or 'F&B.Cu' in names:return list(LAYERS)
 picked=[l for l in LAYERS if l in names]
 if len(picked)==2 and one(node,'drill') is not None and node[0]=='via':
  a,b=LAYERS.index(picked[0]),LAYERS.index(picked[1]);picked=LAYERS[a:b+1]
 return picked
def norm(x,y):return [round(x-OFFSET[0],9),round(y-OFFSET[1],9)]
def rot(x,y,deg):
 # KiCad stores clockwise-positive angles in a y-down frame.
 r=math.radians(deg);c,s=math.cos(r),math.sin(r);return x*c+y*s,-x*s+y*c
def pad_outline(shape,w,h,rratio):
 if shape=='circle':
  r=w/2;return [[r*math.cos(2*math.pi*i/64),r*math.sin(2*math.pi*i/64)] for i in range(64)]
 if shape in ('rect','roundrect','oval'):
  rad=min(w,h)/2 if shape=='oval' else (min(w,h)*rratio if shape=='roundrect' else 0.)
  if rad<=1e-9:return [[-w/2,-h/2],[w/2,-h/2],[w/2,h/2],[-w/2,h/2]]
  pts=[]
  for cx,cy,start in [(w/2-rad,h/2-rad,0),(-w/2+rad,h/2-rad,90),(-w/2+rad,-h/2+rad,180),(w/2-rad,-h/2+rad,270)]:
   for i in range(9):
    t=math.radians(start+90*i/8);pts.append([cx+rad*math.cos(t),cy+rad*math.sin(t)])
  return pts
 raise ValueError('unreviewed pad shape '+shape)
def net(node):
 n=one(node,'net');return val(n[-1]) if n else ''
def uid(node):return val(one(node,'uuid')[1])
def normalize(board_id,tree,terminals,ports):
 objects=[];term_by_pad={t['pad_uuid']:t for t in terminals if t['board']==board_id}
 for fp in kids(tree,'footprint'):
  fx,fy,frot=at(fp)
  ref=next(val(p[2]) for p in kids(fp,'property') if val(p[1])=='Reference')
  for pad in kids(fp,'pad'):
   number,kind,shape=val(pad[1]),pad[2],pad[3]
   px,py,prot=at(pad);dx,dy=rot(px,py,frot);cx,cy=fx+dx,fy+dy
   size=one(pad,'size');w,h=float(size[1]),float(size[2])
   rr=one(pad,'roundrect_rratio');outline=pad_outline(shape,w,h,float(rr[1]) if rr else 0.)
   # Pad angle in the file already includes the footprint rotation.
   poly=[norm(cx+a,cy+b) for a,b in (rot(x,y,prot) for x,y in outline)]
   drill=one(pad,'drill');d=float(val(drill[1])) if drill else 0.
   need(not drill or all(not isinstance(x,list) or x[0]!='offset' for x in drill),'drill offset unsupported')
   if kind=='np_thru_hole':
    objects.append({'id':'NPTH:'+uid(pad),'kind':'keepout','net':'','layers':list(LAYERS),'center_mm':norm(cx,cy),'drill_mm':d,'ref':ref,'pad':number});continue
   layers=cu_layers(pad);need(layers,'copper pad without copper layers '+uid(pad))
   row={'id':uid(pad),'kind':'pad','net':net(pad),'ref':ref,'pad':number,'layers':layers,'polygon_mm':poly,'center_mm':norm(cx,cy),'footprint_uuid':uid(fp)}
   if d>0:row['drill_mm']=d
   t=term_by_pad.get(row['id'])
   if t:row.update(id=f'CS247-{board_id}-W{t["id"].split("/W")[1]}',source_pad_uuid=row['id'],source_ref=ref,ref=None,pad=None)
   objects.append(row)
 for seg in kids(tree,'segment'):
  s,e=one(seg,'start'),one(seg,'end')
  objects.append({'id':uid(seg),'kind':'segment','net':net(seg),'layers':[val(one(seg,'layer')[1])],'path_mm':[norm(float(s[1]),float(s[2])),norm(float(e[1]),float(e[2]))],'width_mm':float(one(seg,'width')[1])})
 need(not kids(tree,'arc'),'track arcs are not reviewed by this normalizer')
 for via in kids(tree,'via'):
  need(len(via)>1 and isinstance(via[1],list),'typed vias are not part of the source candidate')
  x,y,_=at(via)
  objects.append({'id':uid(via),'kind':'via','net':net(via),'layers':cu_layers(via),'center_mm':norm(x,y),'diameter_mm':float(one(via,'size')[1]),'drill_mm':float(one(via,'drill')[1])})
 for zone in kids(tree,'zone'):
  keep=one(zone,'keepout');need(keep is not None,'only rule-area zones are expected in the unfilled candidate')
  lay=one(zone,'layers') or one(zone,'layer');layers=[l for l in LAYERS if l in [val(x) for x in lay[1:]]]
  pts=[[float(p[1]),float(p[2])] for p in kids(one(one(zone,'polygon'),'pts'),'xy')]
  rules={val(r[0]):val(r[1]) for r in keep[1:] if isinstance(r,list)}
  objects.append({'id':uid(zone),'kind':'rule_area','net':'','layers':layers,'polygon_mm':[norm(x,y) for x,y in pts],'rules':rules})
 ids=[o['id'] for o in objects];need(len(ids)==len(set(ids)),'duplicate normalized identity')
 pads={o['id']:o for o in objects if o['kind']=='pad' and o['net'] in RAILS}
 rows=[p for p in ports if p['board']==board_id]
 expected={p['id'] for p in rows}
 need(set(pads)==expected,f'physical rail pad set differs from reviewed mandatory ports: {len(set(pads)^expected)}')
 loads=[{'pad_id':p['id'],'net':p['net'],'ref':p['ref'],'pad':p['pad']} for p in rows if p['source_direct_load_member']]
 for l in loads:need(pads[l['pad_id']]['net']==l['net'],'load net mismatch')
 return {'schema':'e16-normalized-board-v1','board':board_id,'coordinate_offset_mm':list(OFFSET),'objects':objects,'loads':loads}
def main():
 resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3))
 p=argparse.ArgumentParser();p.add_argument('--board-id',choices=['KA','KB'],required=True);p.add_argument('--pcb',type=Path,required=True);p.add_argument('--terminals',type=Path,required=True)
 p.add_argument('--ports',type=Path,default=HERE/'evidence/mandatory-physical-ports-review.json');p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 need(not a.output.exists(),'fresh output required');start=time.monotonic()
 seals={str(q.resolve()):sha(q) for q in [a.pcb,a.terminals,a.ports,Path(__file__)]}
 out=normalize(a.board_id,parse(a.pcb.read_text()),json.loads(a.terminals.read_text()),json.loads(a.ports.read_text())['mandatory_ports'])
 need(all(sha(Path(q))==h for q,h in seals.items()),'input changed')
 out['input_sha256']=seals;a.output.write_text(json.dumps(out,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n')
 kinds={}
 for o in out['objects']:kinds[o['kind']]=kinds.get(o['kind'],0)+1
 print(json.dumps({'board':a.board_id,'objects':kinds,'loads':len(out['loads']),'elapsed_seconds':round(time.monotonic()-start,2),'peak_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'output_sha256':sha(a.output)}))
if __name__=='__main__':main()
