#!/usr/bin/env python3
"""Predeclare and preflight the one authorized KA long-B residual alternative.

No construction or native calls. Independent review/sealing and full geometry
reevaluation are required before any structural credit. KB P1 stays separate.
"""
import argparse
import copy
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import resource
import signal
import time

HERE=Path(__file__).resolve().parent
TARGET={'ref':'U2314','pad':'11','pad_id':'b0f9dbc5-d3f3-5380-a8d2-0fe230e28db0'}
LIMITS={'window_margin_mm':20.,'max_length_mm':30.,'max_segments':20,
        'pitch_mm':.05,'widths_mm':[.2],'clearance_mm':.25,'hole_clearance_mm':.25,
        'unit_seconds':180,'unit_address_space_GiB':2}
METHODS=('residual_closure.py','pilot_preflight.py','fragments.py','construct_access.py','connectivity.py')
HISTORY='evidence/e16/pilot/KA-pilot-outcome.json'

def need(condition,message):
 if not condition:raise ValueError(message)
def sha(path):
 h=hashlib.sha256()
 with Path(path).open('rb') as f:
  for block in iter(lambda:f.read(1024*1024),b''):h.update(block)
 return h.hexdigest()
def read(path):
 p=Path(path);b=p.read_bytes()
 return json.loads(gzip.decompress(b) if p.suffix=='.gz' else b)
def write_new(path,data):
 with Path(path).open('x') as f:json.dump(data,f,indent=1);f.write('\n')
def method_hashes():return {m:sha(HERE/m) for m in METHODS}

def declaration(paths):
 """Cheap immutable input/method binding; does not search geometry."""
 need(set(paths)=={'source','planes_net','graph','census'},'exact four input roles required')
 return {'schema':'e16-residual-closure-declaration-v1','candidate_id':'KA-U2314-11-longB',
         'board':'KA','net':'-12V','target':dict(TARGET),'faces':['B.Cu'],
         'limits':copy.deepcopy(LIMITS),'inputs':{k:str(Path(v).resolve()) for k,v in paths.items()},
         'input_sha256':{k:sha(v) for k,v in paths.items()},'method_sha256':method_hashes(),
         'history':{'path':HISTORY,'sha256':sha(HERE/HISTORY)},
         'authorization_scope':'One previously documented additive long-B alternative; no expanded search after failure.',
         'native_adapter_gap':'Source model cannot prove native per-layer nonfunctional annulus removal; that option is not selected.',
         'construction':'NOT RUN; no new drill, removed copper, moved part or changed layer is authorized here.',
         'kb_p1':'Separate six-pad structural credit, KB480; its copper-resistance failure remains open.',
         'constructed':False,'credited':False,'native_calls':0}

def validate_declaration(d):
 need(d.get('schema')=='e16-residual-closure-declaration-v1','declaration schema')
 need(d.get('candidate_id')=='KA-U2314-11-longB' and d.get('board')=='KA' and d.get('net')=='-12V','candidate identity')
 need(d.get('target')==TARGET and d.get('faces')==['B.Cu'],'target/face differs from fixed scope')
 need(d.get('limits')==LIMITS,'limits differ from fixed predeclaration')
 need(d.get('method_sha256')==method_hashes(),'method changed after predeclaration')
 need(d.get('history')=={'path':HISTORY,'sha256':sha(HERE/HISTORY)},'historical alternative changed')
 need(set(d['inputs'])=={'source','planes_net','graph','census'},'input roles')
 need(d['input_sha256']=={k:sha(v) for k,v in d['inputs'].items()},'input changed after predeclaration')

def isolated_engine():
 """Fresh function globals per call; never modify imported pilot_preflight globals."""
 spec=importlib.util.spec_from_file_location('_e16_longb_preflight',HERE/'pilot_preflight.py')
 module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
 module.LIMITS=copy.deepcopy(LIMITS);module.FACES=('B.Cu',)
 return module

def bounded_preflight(source,planes,graph,census,engine=None):
 need(source.get('board')=='KA','source board must be KA')
 need(graph.get('board')=='KA' and census.get('board')=='KA','graph/census board must be KA')
 pads=[o for o in source['objects'] if o['id']==TARGET['pad_id']]
 need(len(pads)==1 and pads[0].get('ref')==TARGET['ref'] and pads[0].get('pad')==TARGET['pad'] and pads[0].get('net')=='-12V','exact target identity')
 need(any(u['pad_id']==TARGET['pad_id'] for u in census['unresolved']),'target no longer residual')
 api=isolated_engine() if engine is None else engine
 need(api.FACES==('B.Cu',) and api.LIMITS==LIMITS,'engine scope mismatch')
 out=api.preflight(source,planes,graph,census,TARGET['pad_id'])
 need(out['board']=='KA' and out['net']=='-12V' and out['target']==TARGET,'returned target mismatch')
 need(all(a['face']=='B.Cu' for a in out['attempts']),'unexpected face attempt')
 proposal=out.get('proposal')
 if proposal:
  pts=proposal['path_mm'];length=sum(math.dist(a,b) for a,b in zip(pts,pts[1:]))
  need(proposal['face']=='B.Cu' and proposal['width_mm']==.2,'proposal face/width')
  need(len(pts)>=2 and len(pts)-1==proposal['segments']<=20,'segment bound')
  need(length<=30. and proposal['length_mm']<=30.,'length bound')
  need(abs(length-proposal['length_mm'])<1e-4,'reported length differs from path')
 need(bool(proposal)==bool(out['legal']),'legal/proposal disagreement')
 return out

def main():
 parser=argparse.ArgumentParser(description=__doc__);sub=parser.add_subparsers(dest='command',required=True)
 d=sub.add_parser('declare')
 for key in ('source','planes','graph','census','output'):d.add_argument('--'+key,required=True)
 p=sub.add_parser('preflight');p.add_argument('--declaration',required=True);p.add_argument('--output',required=True)
 args=parser.parse_args()
 if args.command=='declare':
  out=declaration({'source':args.source,'planes_net':args.planes,'graph':args.graph,'census':args.census})
 else:
  d=read(args.declaration);validate_declaration(d)
  def timeout(*_):raise TimeoutError('predeclared 180-second preflight limit exceeded')
  signal.signal(signal.SIGALRM,timeout);signal.alarm(LIMITS['unit_seconds'])
  resource.setrlimit(resource.RLIMIT_AS,(2*1024**3,2*1024**3));started=time.monotonic()
  data={k:read(v) for k,v in d['inputs'].items()}
  out=bounded_preflight(data['source'],data['planes_net'],data['graph'],data['census'])
  validate_declaration(d)
  need(read(args.declaration)==d,'declaration changed during preflight')
  out.update(schema='e16-pilot-preflight-v1',candidate_id=d['candidate_id'],limits=copy.deepcopy(LIMITS),
             input_sha256=d['input_sha256'],method_sha256=d['method_sha256'],declaration_sha256=sha(args.declaration),
             rules=d['construction'],constructed=False,credited=False,native_calls=0,
             elapsed_seconds=round(time.monotonic()-started,2),peak_KiB=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss)
  signal.alarm(0)
 write_new(args.output,out)
 print(json.dumps({k:out[k] for k in ('schema','candidate_id','constructed','credited','native_calls')}|{'legal':out.get('legal')}))
if __name__=='__main__':main()
