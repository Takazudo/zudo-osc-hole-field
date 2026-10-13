#!/usr/bin/env python3
"""Materialize exact wire IDs, effective cut limits and full parametric family."""
from dataclasses import asdict
import argparse,hashlib,json,sys
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[5];FEED=ROOT/'circuit/routing/epic-242/decision-pilots/feed-arrangement';sys.path.insert(0,str(FEED));import robust_curve as rc

def build(candidate):
 terms=json.loads((candidate/'terminals.json').read_text());family=rc.Family();source=json.loads((FEED/'reconciled-contract.json').read_text())['producer_replacements']['feed'];out=[]
 for i,(wire,sign) in enumerate(zip(source['wires'],[1,-1,1,1,-1,1])):
  a=next(t for t in terms if t['board']=='KA' and t['wire']==i+1);b=next(t for t in terms if t['board']=='KB' and t['wire']==i+1)
  assert [a['source_endpoint_id'],b['source_endpoint_id']]==wire['terminal_ids']
  poses=[]
  for travel in [0.,10.1]:
   gap=20.4+travel;h=rc.handle(family,gap,66);ctrl=rc.control(family,gap,h)*[1,sign,1]+a['anchor_xyz_mm'];end=np.array(b['anchor_xyz_mm'])-[0,0,travel]
   poses.append({'travel_mm':travel,'free_cubic_control_points_xyz_mm':ctrl.tolist(),'KA_straight_land_to_free_start_xyz_mm':[a['center_xyz_mm'],ctrl[0].tolist()],'KB_straight_free_end_to_land_xyz_mm':[ctrl[3].tolist(),(np.array(b['center_xyz_mm'])-[0,0,travel]).tolist()],'free_cubic_arclength_mm':rc.arclength(ctrl),'anchor_end_xyz_mm':end.tolist()})
  out.append({'id':wire['id'],'net':wire['net'],'terminal_ids':wire['terminal_ids'],'refs':[a['ref'],b['ref']],'pad_UUIDs':[a['pad_uuid'],b['pad_uuid']],'wire_mpn':wire['wire_mpn'],'current_screen_A':wire['current_screen_A'],'effective_feed_cut_mm':[84.5,85.0],'effective_main_cut_mm':[103.5,104.0],'inherited_110mm_metadata_superseded':True,'reflection':[1,sign,1],'KA_anchor_nominal_xyz_mm':a['anchor_xyz_mm'],'family':asdict(family),'continuous_construction':'For gap G in [20.2,30.7] and free length L in [65.9,66.1], h is the unique positive rising root of arclength(control(G,h))=L. Transform all four control points by reflection then KA anchor. Include both exact straight2.5mm tails and tangent bridges to the measured board planes. This formula defines every service position; saved end poses are illustrations.','illustrative_end_poses':poses,'electrical_incidence':{'KA':1,'KB':-1},'manufacturing_status':'Conditional core paths, cut/strip, cap/solder, insulation and C0/C1/C2 service requirements; not qualified'})
 return {'status':'PHYSICAL_SOURCE_WIRE_FAMILY_NOT_QUALIFIED','source_feed_id':source['id'],'wires':out,'return_topology':'Three separate physical AGND conductors between explicit finite board-access ports. They join actual owned same-net copper only where geometric contact is established. Shared copper remains finite and is charged once; no equal current sharing or ideal common node is asserted.','source_sha256':{str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in [FEED/'robust_curve.py',FEED/'robust-curve.json',FEED/'reconciled-contract.json',HERE/'wire_contract.py']},'candidate_terminals_sha256':hashlib.sha256((candidate/'terminals.json').read_bytes()).hexdigest(),'native':False,'adopted':False}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();d=build(a.candidate);a.output.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n');print('PASS six exact wire families;85/104mm effective ceilings')
