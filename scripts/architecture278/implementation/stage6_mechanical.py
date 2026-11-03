"""Drawing-registered conservative DIN/GH exclusion; source only, never fit acceptance."""
import argparse,hashlib,itertools,json,math
from pathlib import Path
from stage3_reservations import overlap
from stage4_mechanical import tail_circle_overlap
import stage6_rebudget
ROOT=Path(__file__).resolve().parents[3];OUT=ROOT/'design/architecture-278/implementation/stage6'
def transform(point,matrix,origin):
 return [origin[i]+sum(matrix[i][j]*point[j]for j in range(2))for i in range(2)]
def register(candidate,spec,official):
 assert candidate['connector_turn_deg']==180,'drawing registration supports only selected180degree arrangement'
 assert spec['female_A_to_global_xy_matrix']==[[0,-1],[1,0]],'female drawing view/handedness changed'
 assert spec['male_B_to_global_xy_matrix']==[[0,1],[1,0]],'male mating mirror changed'
 assert spec['female_row_v_mm']=={'a':-2.54,'b':0,'c':2.54}and spec['male_row_v_mm']=={'a':2.54,'b':0,'c':-2.54},'row registration changed'
 assert spec['pitch_mm']==2.54 and spec['pin1_u_mm']==39.37,'exact96position grid changed'
 assert spec['female_flange_v_mm']==-.3 and spec['female_flange_v_tolerance_mm']==.1,'signed female flange datum changed'
 assert all(math.isclose(a,b)for a,b in zip(sorted([-spec['female_flange_v_mm']-spec['female_flange_v_tolerance_mm'],-spec['female_flange_v_mm']+spec['female_flange_v_tolerance_mm']]),official['female_row_b_flange_axis_offset_mm'])),'flange offset evidence mismatch'
 assert spec['female_flange_span_mm']==sum(official['female_flange_spacing_mm'])/2==90,'flange spacing mismatch'
 assert math.isclose(spec['female_flange_span_tolerance_mm'],(official['female_flange_spacing_mm'][1]-official['female_flange_spacing_mm'][0])/2),'flange tolerance mismatch'
 diameter=spec['proposed_contact_pad_diameter_mm'];drill=max(official['contact_drill_diameter_mm']);pos=official['contact_true_position_diameter_mm']/2
 assert math.isfinite(diameter) and diameter>drill,'pad must exceed maximum drill'
 assert math.isclose(spec['middle_female_mount_surface_z_mm']-spec['pcb_thickness_mm'],spec['middle_GH_opposite_surface_z_mm']),'opposite board surface mismatch'
 assert math.isclose(spec['rear_male_mount_surface_z_mm']-spec['middle_female_mount_surface_z_mm'],19.2),'mating surface separation changed'
 contacts=[];flanges=[]
 for instance,xy in candidate['origins_mm'].items():
  origin=[xy[i]+candidate['connector_centre_mm'][i]for i in range(2)]
  for row in 'abc':
   for n in range(1,33):
    u=spec['pin1_u_mm']-(n-1)*spec['pitch_mm'];f=transform([u,spec['female_row_v_mm'][row]],spec['female_A_to_global_xy_matrix'],origin);m=transform([u,spec['male_row_v_mm'][row]],spec['male_B_to_global_xy_matrix'],origin)
    assert f==m,'named mating contacts do not coincide'
    contacts.append({'id':instance+':'+row+str(n),'instance':instance,'label':row+str(n),'point_mm':f,'male_point_mm':m,'radius_mm':diameter/2+pos,'kind':'proposed annular pad plus official position tolerance'})
  radius=max(official['female_flange_hole_diameter_mm'])/2+math.hypot(spec['female_flange_v_tolerance_mm'],spec['female_flange_span_tolerance_mm']/2)
  for sign in[-1,1]:
   point=transform([sign*spec['female_flange_span_mm']/2,spec['female_flange_v_mm']],spec['female_A_to_global_xy_matrix'],origin)
   flanges.append({'id':instance+':flange'+str(sign),'point_mm':point,'radius_mm':radius,'kind':'female flange drilling plus signed datum tolerance; fasteners UNKNOWN'})
 bykey={(p['instance'],p['label']):p for p in contacts}
 for row in candidate['paths']:
  if row['DIN_pad_mm']is not None:
   expected=bykey[row['instance'],candidate['common_DIN_signal_labels'][row['net']]]['point_mm']
   assert all(math.isclose(a,b,abs_tol=1e-9)for a,b in zip(expected,row['DIN_pad_mm'])),'electrical DIN pad mismatches registered drawing'
 return contacts,flanges

def screen(headers,holes):
 return [{'header':h['instance']+':'+h['ref'],'DIN':p['id'],'point_mm':p['point_mm'],'exclusion_radius_mm':p['radius_mm']}for h in headers for p in holes if tail_circle_overlap(*p['point_mm'],h['box_mm'],p['radius_mm'])]
def build():
 names=['design/architecture-278/implementation/stage6/candidate-report.json','design/architecture-278/implementation/stage6/mechanical-input.json','design/architecture-278/implementation/stage5/din-evidence.json','design/architecture-278/implementation/stage5/candidate-report.json','design/architecture-278/implementation/stage5/mechanical-report.json','design/architecture-278/implementation/stage4/occupied-report.json','design/connectors/jst-gh.json','design/connectors/sources/jst-gh.pdf','design/architecture-278/implementation/front-evidence.json']
 raw={n:(ROOT/n).read_bytes()for n in names};report,spec,official,prior,prior_screen,occupied=[json.loads(raw[n])for n in names[:6]];c=report['candidate']
 assert json.loads(json.dumps(stage6_rebudget.build()))==report,'rebudget report differs from current source'
 contacts,flanges=register(c,spec,official);holes=contacts+flanges;headers=c['middle_header_placements_all_instances'];assert len(headers)==85 and len(contacts)==480 and len(flanges)==10
 gh=json.loads(raw[names[6]]);front=json.loads(raw[names[8]]);widths={p['header_mpn']:p['header_body_width_mm']for p in gh['sizes']}
 widths.update({p['header_mpn']:p['header_table_B_mm']for p in front['candidate_JST_2_4_derived']})
 for h in headers:
  assert h['quarter_turn']==0 and h['side']=='panel','unsupported GH mounting view'
  x,y=h['origin_mm'];w=widths[h['header_mpn']];b=h['box_mm']
  assert b[0]<=x-w/2 and b[2]>=x+w/2 and b[1]<=y+spec['GH_reference_body_local_y_mm'][0] and b[3]>=y+spec['GH_reference_body_local_y_mm'][1],'GH courtyard does not contain reference body'
 findings=screen(headers,holes);old_findings=screen(prior['candidate']['middle_header_placements_all_instances'],holes)
 pairs=[{'a':a['instance']+':'+a['ref'],'b':b['instance']+':'+b['ref']}for a,b in itertools.combinations(headers,2)if overlap(a['box_mm'],b['box_mm'])]
 shared=[dict(p['new_candidate_placement'],instance='shared',ref=p['ref'])for p in occupied['rows']if p['population_group']=='OCTAVE_REF'];shared_hits=screen(shared,holes)
 oldkeys={(p['header'],p['DIN'])for p in prior_screen['opposite_face_GH_courtyard_hole_projections_UNKNOWN']};newkeys={(p['header'],p['DIN'])for p in findings}
 resolution=[{'header':h,'DIN':d,'status':'SOURCE_EXCLUSION_RESOLVED_BY_WHOLE_HEADER_MOVE'if(h,d)not in newkeys else'UNRESOLVED'}for h,d in sorted(oldkeys)]
 pos=official['contact_true_position_diameter_mm']/2;diameter=spec['proposed_contact_pad_diameter_mm'];drill=max(official['contact_drill_diameter_mm'])
 hashes={n:hashlib.sha256(b).hexdigest()for n,b in raw.items()}
 for p in [Path(__file__),*[Path(__file__).with_name(n)for n in ['test_stage6_mechanical.py','stage6_rebudget.py','stage5_rebudget.py','stage3_reservations.py','stage4_mechanical.py']]]:hashes[str(p.relative_to(ROOT))]=hashlib.sha256(p.read_bytes()).hexdigest()
 hashes.update(report['source_sha256'])
 return {'status':'TWELVE SOURCE PROJECTIONS REMOVED; FULL MECHANICAL ACCEPTANCE OPEN','source_sha256':hashes,'header_count':len(headers),'contact_count':len(contacts),'flange_count':len(flanges),'registered_contact_grid':contacts,'signed_female_flange_holes':flanges,'stage5_twelve_resolution':resolution,'stage5_under_stronger_annular_envelope':old_findings,'remaining_GH_courtyard_exclusions':findings,'same_face_header_courtyard_conflicts':pairs,'shared_middle_hole_or_pad_conflicts':shared_hits,'proposed_annular_design':{'diameter_mm':diameter,'minimum_ring_before_manufacturing_tolerance_mm':(diameter-drill)/2-pos,'nominal_adjacent_pad_gap_mm':spec['pitch_mm']-diameter,'gap_after_opposed_true_position_mm':spec['pitch_mm']-diameter-2*pos,'status':'PROPOSED copper geometry; manufacturing etch/drill/plating and clearance-rule qualification OPEN'},'conditional_Z':{'middle_PCB_mm':[spec['middle_GH_opposite_surface_z_mm'],spec['middle_female_mount_surface_z_mm']],'female_tail_tip_range_mm':[spec['middle_female_mount_surface_z_mm']-v for v in reversed(spec['female_tail_length_range_mm'])],'GH_reference_body_z_mm':[spec['middle_GH_opposite_surface_z_mm']-spec['GH_reference_body_height_mm'],spec['middle_GH_opposite_surface_z_mm']-spec['GH_reference_standoff_mm']],'interpretation':'Tail and GH body Z envelopes overlap at nominal1.6PCB; therefore XY exclusion is necessary, not an opposite-face clearance assumption. Lower-body cavities/solder/fasteners are not inferred.'},'rebudget':{'maximum_path_mm':c['maximum_mm'],'overlength_count':c['overlength_count'],'minimum_wire_slack_mm':c['tolerance_service']['wire_minimum_slack_mm'],'counts':[len(c['paths']),len(c['returns']),len(c['wire_checks'])]},'remaining_unknown':spec['unknown'],'physical_acceptance':False,'native':'NOT RUN','physical':'NOT RUN','simulation':'NOT RUN'}
def main():
 ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args();r=build();s=json.dumps(r,indent=2,sort_keys=True)+'\n';p=OUT/'mechanical-report.json'
 if args.check:assert p.read_text()==s,'stale Stage6 mechanical report'
 else:p.write_text(s)
 print('Stage6',len(r['stage5_twelve_resolution']),'prior projections;',len(r['remaining_GH_courtyard_exclusions']),'remaining; native/physical NOT RUN')
if __name__=='__main__':main()
