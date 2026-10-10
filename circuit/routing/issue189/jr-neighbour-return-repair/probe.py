"""Bounded additive repairs of exact new native split groups; no cut or movement."""
import argparse,copy,hashlib,json,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];sys.path.insert(0,str(ROOT))
from scripts.pcbgen.grid_router import route,copper_rows
from scripts.pcbgen.route_jack_grid import connected_pad_groups,LAYER_COST,RAILS,neck_kwargs
HERE=Path(__file__).parent
p=argparse.ArgumentParser();p.add_argument('native_root',type=Path);a=p.parse_args();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();bid='osc-jack-right'
base=a.native_root/(bid+'-grid-189-local-base/dump.json');candidate=a.native_root/(bid+'-grid-189-jr134-post-adoption-neighbours/dump.json');before=json.loads(base.read_text());d=json.loads(candidate.read_text())
assert before['board_sha256']=='35b52972dd70b4186cf3f3b7ee2ac3d70432f3476c2f56c9fcf9c1c4d7d4d445' and d['board_sha256']=='e2cd1e974ff1fd2353cd6c9b09e50c4d044ac8268373de80ca2294c0d06c1866'
old=connected_pad_groups(before);new=connected_pad_groups(d);pads={p['uuid']:p for p in d['pads']};obligations=[]
for net in ('-12V','AGND'):
 for group in old.get(net,[]):
  pieces=[set(group)&set(g) for g in new.get(net,[])];pieces=[g for g in pieces if g]
  if len(pieces)<2:continue
  pieces.sort(key=lambda g:(len(g),sorted(g)));main=pieces[-1]
  main_group=next(g for g in d['islands'][net] if main<=set(g))
  for piece in pieces[:-1]:obligations.append(dict(net=net,pads=sorted(piece),source=next(g for g in d['islands'][net] if piece<=set(g)),goal=main_group))
assert len(obligations)==4 and sum(o['net']=='-12V' for o in obligations)==1
rows=[];added=[];started=time.monotonic();current=copy.deepcopy(d)
for index,o in enumerate(obligations):
 pts=[pads[u]['xy'] for u in o['pads']];bounds=[min(p[0] for p in pts)/1e6-6,min(p[1] for p in pts)/1e6-6,max(p[0] for p in pts)/1e6+6,max(p[1] for p in pts)/1e6+6]
 for mode in ('direct','plane'):
  trial=copy.deepcopy(current);trial['islands'][o['net']]=[o['source'],o['goal']] if mode=='direct' else [o['source']];events=[];then=time.monotonic()
  result,removed=route(trial,[o['net']],planes={o['net']:'In1.Cu' if o['net']=='AGND' else 'In3.Cu'} if mode=='plane' else None,allowed_layers=['F.Cu','B.Cu'],layer_cost=LAYER_COST,rail_nets=RAILS+['AGND'],clearance=.25,rail_width=.3,via_diameter=.6,signal_width=.2,signal_via_diameter=.6,res=.025,grow={n:.05 for n in RAILS+['AGND']},window_mm=6,max_expansions=300000,bounds_mm=bounds,fill_guards={'-12V':'In3.Cu'},diagnostics=events,**neck_kwargs(bid))
  assert not removed;copper,_=copper_rows(result,bid,'issue189-native-return-'+str(index)+'-'+mode);complete=bool(copper) and bool(result) and all(r['path'] for r in result)
  row=dict(index=index,net=o['net'],pads=o['pads'],pad_names=[pads[u]['ref']+'.'+pads[u]['pad'] for u in o['pads']],mode=mode,bounds_mm=bounds,complete_raster_transaction=complete,elapsed_seconds=time.monotonic()-then,diagnostics=events,results=result,copper=copper);rows.append(row)
  print(index,row['pad_names'],mode,complete,flush=True)
  if complete:
   added+=copper
   for c in copper:
    if c['kind']=='segment':current['tracks'].append(dict(uuid=c['uuid'],net=c['net'],layer=c['layer'],a=c['start_nm'],b=c['end_nm'],width=c['width_nm']))
    else:current['vias'].append(dict(uuid=c['uuid'],net=c['net'],xy=c['at_nm'],diameter=c['diameter_nm'],drill=c['drill_nm'],layers=c['layers']))
   break
 result=dict(status='BOUNDED NATIVE-SPLIT RESTORATION SCREEN; NO CANONICAL CHANGE; NATIVE NOT RUN',input_dump_sha256=sha(candidate),candidate_board_sha256=d['board_sha256'],original_board_sha256=before['board_sha256'],obligations=obligations,trials=rows,elapsed_seconds=time.monotonic()-started)
 (HERE/'result.json').write_text(json.dumps(result,indent=2)+'\n')
complete=len({r['index'] for r in rows if r['complete_raster_transaction']})==len(obligations)
result['all_four_have_raster_restoration']=complete
if complete:
 source=json.loads((HERE.parent/'jack-post-adoption-neighbours/proposal.json').read_text());source['copper']+=added;(HERE/'proposal.json').write_text(json.dumps(source,indent=2)+'\n');result['proposal_sha256']=sha(HERE/'proposal.json')
(HERE/'result.json').write_text(json.dumps(result,indent=2)+'\n')
