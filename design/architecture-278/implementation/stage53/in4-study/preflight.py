"""Read-only endpoint screen before any Stage53 search; no routing acceptance."""
from pathlib import Path
import hashlib,importlib.util,json,sys
from shapely.geometry import Point,LineString
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[4]
def load(name,path):
 s=importlib.util.spec_from_file_location(name,path);m=importlib.util.module_from_spec(s);s.loader.exec_module(m);return m
s=load('stage53_sites',ROOT/'design/architecture-278/implementation/stage52/layer-bridges/sites.py')
e=load('stage53_seed',ROOT/'design/architecture-278/implementation/stage51/f3-sense/escape.py')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def run():
 dump=ROOT/'.circuit-cache/stage51/dump.json';base=ROOT/'.circuit-cache/stage49-fresh/connectivity-passfresh.json';seed=ROOT/'.circuit-cache/stage51-seed/connectivity-seed.json'
 d=json.loads(dump.read_text());old=json.loads(base.read_text());new=json.loads(seed.read_text())
 if old['board_sha256']!=s.BASE or d['board_sha256']!=s.BASE:raise ValueError('baseline')
 for net,groups in old['groups'].items():
  retained=set(old['objects']);projected={frozenset(set(g)&retained) for g in new['groups'][net]}
  if projected!={frozenset(g) for g in groups}:raise ValueError('seed partition drift '+net)
 if any(new['objects'].get(k)!=v for k,v in old['objects'].items()):raise ValueError('seed retained object drift')
 screen=s.Screen(d);track,via=e.seed();xy=[v/1e6 for v in via['at_nm']]
 margin,obstacle=screen.margin(Point(xy),.3,d['layers'],True)
 tm,to=screen.margin(LineString([[v/1e6 for v in track[k]] for k in ('start_nm','end_nm')]),.1,['B.Cu'])
 if min(margin,tm)<0:raise ValueError('seed clearance')
 group=next(g for g in old['groups'][s.NET] if len(g)==50)
 ids={old['objects'][k]['uuid'] for k in group if 'uuid' in old['objects'][k]}
 exits=[v for v in d['vias'] if v['net']==s.NET and v['uuid'] in ids]
 if len(exits)!=6 or list(map(len,old['groups']['+12V']))!=[1025]:raise ValueError('exit/rail baseline')
 return dict(baseline_sha256=s.BASE,bindings={str(p.relative_to(ROOT)):sha(p) for p in [dump,base,seed]},entry=via,entry_clearance_surplus_mm=margin,entry_nearest=obstacle,seed_track_clearance_surplus_mm=tm,seed_nearest=to,exits=exits,baseline_plus12_groups=[1025],seed_retained_partitions_unchanged=True,limits='Prior seed diagnostic has no target closure. Existing exit vias need no added hole. In4 carries +12V; corridor continuity, thermal necks and all-net partitions must be checked after native refill. Assembly body/process/tolerances unresolved; no physical clearance inferred.')
if __name__=='__main__':
 text=json.dumps(run(),indent=2,sort_keys=True)+'\n';out=HERE/'preflight.json'
 if '--check' in sys.argv:
  if out.read_text()!=text:raise ValueError('preflight drift')
 else:out.write_text(text)
 print('PASS endpoint screen only; In4 plane preservation still unestablished')
