"""Occurrence-safe normalization observations; NEVER grants warning acceptance."""
import collections,hashlib,json
from pathlib import Path
from scripts.pcbgen.copper_identity import copper_objects,load_board_text,verify_normalization

def fingerprint(value):return json.dumps(value,sort_keys=True,separators=(',',':'))
def nm(value):
 from decimal import Decimal
 n=Decimal(str(value))*1000000
 if n!=n.to_integral_value():raise ValueError('noninteger native coordinate')
 return int(n)
def signature(row):
 g=row['geometry'];kind=row['kind']
 if kind=='segment':shape=[g['start'],g['end'],g['width']]
 elif kind=='via':shape=[g['at'],g['size'],g['drill']]
 else:raise ValueError('unsupported native arc binding; retain gate unresolved')
 def convert(v):return [convert(x) for x in v] if isinstance(v,list) else nm(v)
 return fingerprint([row['uuid'],kind,row['net'],sorted(row['layers']),convert(shape)])
def mapping(before,after,manifest):
 verify_normalization(before,after,manifest)
 a,b=copper_objects(before),copper_objects(after)
 maps=[]
 for rows in (a,b):
  result={}
  for i,row in enumerate(rows):
   key=signature(row)
   if key in result:raise ValueError('indistinguishable source occurrences; native binding unresolved')
   result[key]='copper:'+str(i)
  maps.append(result)
 return maps

def bind_native(rows,expected):
 result={}
 for row in rows:
  key=fingerprint(row['signature'])
  if key not in expected:raise ValueError('unknown native copper occurrence')
  token=expected[key]
  if token in result:raise ValueError('duplicate native occurrence')
  result[token]=row
 if set(result)!=set(expected.values()):raise ValueError('missing native occurrence')
 return result

def validate(observations):
 if set(observations)!={'before','after','before_fresh','after_fresh'}:raise ValueError('four exact phases required')
 base=observations['before']
 for name,row in observations.items():
  if row['native_version']!='10.0.6' or row['phase']!=name:raise ValueError('phase/oracle mismatch')
  for key in ('mapping_sha256','producer_sha256','context_sha256'):
   if row[key]!=base[key]:raise ValueError('source/context drift:'+key)
  if row['input_sha256']!=base['input_sha256']:raise ValueError('original pair binding drift')
  for key in ('copper_tokens','pads','zones','islands','open_edges'):
   if row[key]!=base[key]:raise ValueError('native equality failed:'+key)
 return {'status':'PARTIAL NATIVE OCCURRENCE/CONNECTIVITY EQUALITY ONLY',
  'warning_complete':False,'adopted':False,'remaining':['settled three-pass protocol receipts','full native noncopper/context serialization','complete occurrence-bound warning-domain evidence; duplicate UUID internal dedup not waived']}

def warning_compare(before_drc,after_drc,maps):
 """Only uncapped, unambiguous raw native domains can close here. No geometry waiver."""
 results=[]
 for drc,aliases in zip((before_drc,after_drc),maps):
  if drc.get('kicad_version')!='10.0.6' or drc.get('schematic_parity'):raise ValueError('native parity/oracle failed')
  rows=drc['violations']
  if any(r['severity']=='error' for r in rows):raise ValueError('native errors')
  counts=collections.Counter(r['type'] for r in rows if r['severity']=='warning')
  if any(n>=199 for n in counts.values()):return {'complete':False,'reason':'capped native domain requires complete occurrence-bound fixtures; no invariance waiver'}
  ids=collections.defaultdict(list)
  for sig,token in aliases.items():ids[json.loads(sig)[0]].append(token)
  observed=[]
  for row in rows:
   identity=[]
   for item in row['items']:
    uid=item.get('uuid')
    if not uid:raise ValueError('native warning item missing UUID')
    choices=ids.get(uid)
    if choices and len(choices)!=1:return {'complete':False,'reason':'ambiguous legacy occurrence in native warning; require native fixture disambiguation'}
    identity.append(choices[0] if choices else 'unchanged-noncopper:'+uid)
   if not identity:raise ValueError('warning without item identity')
   observed.append((row['type'],row['severity'],tuple(sorted(identity))))
  results.append(collections.Counter(observed))
 if results[0]!=results[1]:raise ValueError('native warning multiplicity/identity changed')
 return {'complete':True,'scope':'Uncapped raw native report equality under unambiguous occurrence mapping only; noncopper/native protocol acceptance separate'}

def serialized_capture(text,expected):
 """Full native serialization, with ONLY mapped copper UUID tokens abstracted."""
 from scripts.pcbgen.uuid_tools import top_level_spans
 copper={};noncopper=collections.Counter()
 for obj in copper_objects(text):
  key=signature(obj)
  if key not in expected:raise ValueError('serialized native object outside source map')
  token=expected[key]
  if token in copper:raise ValueError('duplicate serialized occurrence')
  a,b=obj['span'];u,v=obj['uuid_span']
  block=text[a:u]+'<MAPPED-COPPER-UUID>'+text[v:b]
  copper[token]=hashlib.sha256(block.encode('latin1')).hexdigest()
 if set(copper)!=set(expected.values()):raise ValueError('missing serialized occurrence')
 for a,b in top_level_spans(text):
  block=text[a:b]
  if block.split(None,1)[0] not in ('(segment','(via','(arc'):
   noncopper[hashlib.sha256(block.encode('latin1')).hexdigest()]+=1
 return {'native_copper_blocks':copper,'native_noncopper_blocks':dict(sorted(noncopper.items()))}

SHAPE_KEYS=('copper_tokens','pads','zones','islands','open_edges','native_copper_blocks','native_noncopper_blocks')
def settled(rows):
 if len(rows)<3:return False
 return all(all(row[k]==rows[-1][k] for k in SHAPE_KEYS) for row in rows[-3:])
def validate_protocol(phases):
 if set(phases)!={'before','after','before_fresh','after_fresh'}:raise ValueError('four phases required')
 finals={}
 for phase,rounds in phases.items():
  if not 3<=len(rounds)<=6 or not settled(rounds):raise ValueError('phase did not establish three consecutive equal native states')
  for row in rounds:
   if row['phase']!=phase:raise ValueError('phase witness mismatch')
  finals[phase]=rounds[-1]
 result=validate(finals)
 for row in finals.values():
  for key in SHAPE_KEYS:
   if row[key]!=finals['before'][key]:raise ValueError('fresh/cross-side native serialization or connectivity differs:'+key)
 result['status']='FOUR SETTLED NATIVE PHASES EQUAL; WARNING GATE SEPARATE'
 result['remaining']=['complete occurrence-bound warning-domain evidence; duplicate UUID internal dedup not waived']
 return result
