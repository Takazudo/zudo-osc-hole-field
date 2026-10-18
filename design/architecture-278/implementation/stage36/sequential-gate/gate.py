"""Bounded necessary screens for J-PWR local only; no hardware dimensions invented."""
import hashlib,json,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[5]
sys.path.insert(0,str(ROOT/'scripts/architecture278/implementation'))
import stage35_cover_service as s
O=Path(__file__).parent

def run():
 D,P,T,rules,c=s.context();g=s.s34.rg34(c,P,T);p=g['J-PWR'];post=s.s34.post_prism(c,g,D['input'])
 a,b=p['exit_z_mm']['local'],p['exit_z_mm']['middle'];Z=s.exact_top(149,p['f']['D'],a,b,12,14.6);fan=p['fan_in_mm'];entry=p['block_entry_z_mm']['local']
 obs=s.occupied_obstacles(c,250)+[post]+[v for l in s.s34.LINKS for v in g[l]['parts'] if v.get('removable_for')!='local' or l!='J-PWR']
 # Fixed projection family, NOT finger dimensions: preserves entire4-wire row
 # at maximum source OD1.0, broad faces +/-v, all t in[0,15].
 w=(4-1)*1.25+1.0
 def audit(part):
  rows=[]
  for ob in obs:
   if s.s34.own(ob,'J-PWR','local'):continue
   cross=not ob['id'].startswith(s.s34.REAR)
   st=s.s34.stack_for(ob['id'],P,T,rules,p['bow_mm'],cross)
   stack=st['worst_case_mm']-st['contributors'].get('registration_allowance_mm',0)+(math.sqrt(3) if cross else 0)
   spare=s.s34.prism_dist(part,ob)-.5-stack
   rows.append({'obstacle':ob['id'],'kind':ob['kind'],'spare_mm':spare})
  rows.sort(key=lambda x:x['spare_mm']);return {'pairs':len(rows),'minimum':rows[:3],'blocking_count':sum(x['spare_mm']<.15 for x in rows),'meets_K4':all(x['spare_mm']>=.15 for x in rows)}
 def box(x0,x1,y0,y1,z0,z1):return {'poly':[[x0,y0],[x1,y0],[x1,y1],[x0,y1]],'z':[z0,z1]}
 def grip(side,depth,height):
  v0,v1=(.5,.5+depth) if side=='plus_v' else (-.5-depth,-.5)
  return box(226-w/2,226+w/2,173+v0,173+v1,a+fan,a+fan+height+15)
 def maximum(side):
  zero=audit(grip(side,0,0))
  if not zero['meets_K4']:return {'status':'NO_CERTIFIED_NONNEGATIVE_DEPTH_IN_THIS_FAMILY','max_depth_mm':None,'zero_thickness_probe':zero}
  lo,hi=0.,25.
  for _ in range(28):
   mid=(lo+hi)/2
   if audit(grip(side,mid,0))['meets_K4']:lo=mid
   else:hi=mid
  return {'status':'NECESSARY_ONLY_ZERO_AXIAL_HEIGHT','max_depth_mm':lo,'upper_search_mm':25,'at_limit':audit(grip(side,lo,0))}
 # Continuous free-span outer bound: at t=0 longest exposed chord. For t>0
 # selected exit rises and upper entry remains fixed; each shorter-chord ellipse
 # lies in this t=0 ellipse when residual slack is unchanged.
 board=next(o for o in s.occupied_obstacles(c,250) if o['id']=='board:A01-middle:0')
 def span_spare(slack):
  sp=s.s34.spheroid([226,173],a,entry,entry-a+slack,p['r']+.3+1+.1+.1)
  error=math.pi*max(sp['A'],sp['B'])/40000
  st=s.s34.stack_for(board['id'],P,T,rules,p['bow_mm'],False)['worst_case_mm']-.1-.1
  return s.s34.spheroid_prism_dist(sp,board)-error-.5-st
 lo,hi=0.,.5
 for _ in range(32):
  mid=(lo+hi)/2
  if span_spare(mid)>=.15:lo=mid
  else:hi=mid
 sleeve=next(v for v in p['parts'] if v.get('removable_for')=='local')
 old=json.loads((ROOT/s.REL/'stage35/analysis.json').read_text())
 historical=next(x for x in old['support']['tracking_former_proposal']['span_bounds'] if x['link']=='J-PWR' and x['side']=='local')
 return {'verdict':'UNKNOWN_NOT_SOURCE_FEASIBLE_HARD_STOP','scope':'J-PWR local only; no other endpoints advanced; no mechanism selected','lengths_mm':{'J-PWR':149,'J-SIG':133},'radius_mm':12,'planning_angle_deg':15,'cover_inner_z_mm':105,'core_extraction_mm':40,'margin_mm':.5,'K4_mm':.15,
 'local_frame':{'origin_mm':[226,173,43.9],'u_pitch':[1,0,0],'v_broad_face_normal':[0,1,0],'w_withdrawal':[0,0,1],'latch_side_sign':'UNCONFIRMED exact part orientation; inspect actual top-entry part'},
 'continuous':{'t_mm':[0,15],'top_z_mm':[Z,Z+7.5],'historical_polyline_top_delta_mm':p['Z0']-Z,'former_relative_rise_mm':[0,7.5],'local_straight_mm':[Z-12-a,Z-12-a-7.5],'opposite_straight_mm':[Z-12-b,Z-12-b+7.5],'fan_in_mm':fan,'fixed_former_released_slack_mm':[0,15],'residual_slack_equation':'delta_set + 2*max(0,t/2-y(t)); y(t)>t/2 risks tension and is not permitted by this length model; no friction or clamp credited','reverse':'same swept family with t decreasing; support must precede sleeve removal and remain until sleeve closed'},
 'open_span':{'historical_stage35_bound_mm':historical['tightest'][0]['robust_spare_lower_bound_mm'],'recomputed_same_bound_mm':span_spare(.5),'K4_deficit_mm':.15-span_spare(.5),'necessary_max_total_residual_mm_for_middle_board_only':lo,'not_a_global_slack_pass':True,'unknowns_retained':True},
 'grip':{'family':'full4-wire pitch-row reference projection; not measured wire shape or finger','row_width_mm':w,'row_depth_mm':1,'nominal_axial_height_cap_mm':entry-(a+fan+15),'height_condition':'H+q <= cap; q>=0 offset above fan-in; cap omits tolerances and hand approach, so necessary only','plus_v':maximum('plus_v'),'minus_v':maximum('minus_v'),'both_faces_required':True,'force_or_friction_credit':False,'angle_scope':'depth limits are zero-angle axis-aligned necessary screens, not full15deg orientation or approach clearance','full_15deg_translation_only_outer_bound':{side:audit(box(226-w/2-15*math.tan(math.radians(15)),226+w/2+15*math.tan(math.radians(15)),173+(.5 if side=='plus_v' else -.5)-15*math.tan(math.radians(15)),173+(.5 if side=='plus_v' else -.5)+15*math.tan(math.radians(15)),a+fan,a+fan+15)) for side in ('plus_v','minus_v')}},
 'sleeve':{'closed_local_coordinate_corners':[[x-226,y-173,z-a] for x,y in sleeve['poly'] for z in sleeve['z']],'opening_axis_hinge_angle_and_wall_geometry':None,'zero_motion_outer_prism_audit':audit(sleeve),'maximum_certified_opening_travel_mm':None,'reason':'closed occupancy screen and absent split/hinge profile do not establish a collision-free opening; no direction is invented'},
 'latch':{'tool_tip_width_depth_height_mm':None,'stroke_mm':None,'maximum_certified_envelope_mm':None,'reason':'protrusion known qualitatively; exact position, side, travel and approach missing; housing outline is not latch datum'},
 'support_handoff':{'separate_former_reaction_to_carrier':'REQUIRED_UNDEFINED','retention_of_both_bends_before_sleeve_open':'REQUIRED_UNDEFINED','opposite_sleeve_retained':True,'operator_arch_support_credit':False,'housing_crimp_structural_credit':False},'physical':'NOT_RUN','native':'NOT_RUN'}

def main():
 body=json.dumps(run(),indent=2,sort_keys=True,allow_nan=False)+'\n';p=O/'gate.json'
 if '--check' in sys.argv:
  if p.read_text()!=body:raise ValueError('gate drift')
 else:p.write_text(body)
 print('PASS source reproduction; UNKNOWN_NOT_SOURCE_FEASIBLE_HARD_STOP')
if __name__=='__main__':main()
