#!/usr/bin/env python3
"""Fail closed on the joined geometry evidence; no electrical/adoption verdict."""
import argparse,hashlib,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[5]
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def need(ok,label):
 if not ok:raise ValueError(label)
def verify(candidate):
 e=HERE/'evidence';receipt=read(candidate/'receipt.json')
 for rel,h in receipt['input_sha256'].items():need(sha(ROOT/rel)==h,'construction source drift '+rel)
 need(receipt['mechanical_solids']==204 and receipt['terminal_count']==12,'complete current construction')
 sweep=read(e/'sweep-05.json');ends=read(e/'ends-05.json');solids=read(e/'solids-05.json');joints=read(e/'joints-05.json')
 for kind in ['sweep','solids']:
  execution=read(e/(kind+'-05.receipt.json'));need(execution['returncode']==0 and execution['native_calls']==0,'bounded source execution')
  need(execution['output_sha256']==sha(e/(kind+'-05.json')),'report hash '+kind)
  for name,h in execution['input_sha256'].items():
   path=Path(name)
   if '/zudo-osc-hole-field/' in name:path=ROOT/name.split('/zudo-osc-hole-field/',1)[1]
   elif path.parent.name=='feed-v2-candidate-05':path=candidate/path.name
   need(sha(path)==h,'execution source seal '+str(path))
 need(sweep['static']['status']=='CLEAR','static geometry')
 c=sweep['continuous'];need(c['gap_cells']==100 and c['curve_cells']==416 and c['enclosed_centerline_cells']==249600,'complete continuous grid')
 need(c['source_minimum'][0]>=.70 and c['carrier_minimum'][0]>=.60 and c['pair_minimum_mm']>=.85 and c['enclosure_minimum_mm']>=.35,'complete continuous lower bounds')
 need(not c['carrier_findings_first300'],'free-curve findings')
 need(ends['status']=='CONSERVATIVE_END_VOLUME_SCREEN_CLEAR' and ends['end_count']==12 and ends['finite_contact_supports_checked']==228,'complete finite ends')
 need(not ends['findings_first1000'] and ends['source_objects']==4669,'end findings/source completeness')
 for name,h in ends['input_sha256'].items():
  p=Path(name)
  if p.name in ['receipt.json','terminals.json','contacts.json.gz','mechanical.json.gz']:p=candidate/p.name
  elif p.name=='feed-v2-exit-proof-durable.json':p=e/'exit-proof.json'
  elif '/zudo-osc-hole-field/' in name:p=ROOT/name.split('/zudo-osc-hole-field/',1)[1]
  need(sha(p)==h,'end source seal '+str(p))
 need(solids['solid_count']==204 and solids['retained_trimmer_tool_columns']==100 and solids['source_obstacle_count']==4669,'solid source completeness')
 need(not solids['source_findings'] and not solids['cross_carrier_findings'],'solid service findings')
 need(min(x['after_0p35_closure_mm'] for x in solids['enclosure'])>=0,'enclosure closure')
 need(joints['input_mechanical_sha256']==sha(candidate/'mechanical.json.gz'),'joint geometry seal')
 need(joints['candidate_receipt_sha256']==sha(candidate/'receipt.json') and joints['support_bindings_sha256']==sha(candidate/'support-bindings.json') and joints['helper_sha256']==sha(HERE/'check_joints.py'),'joint evidence seals')
 need(joints['joint_status_counts']=={'PROVED_GEOMETRIC_INTERFACE':90,'REQUIRES_AXIAL_STACK_NOT_SHAFT_RADIAL_CONTACT':4},'joint coverage')
 need(sum(x['status']=='PROVED_COAXIAL_SHAFT_CLEARANCE' for x in joints['fastener_checks'])==8,'complete cap-shaft clearance')
 allowed={'POSITIVE_AREA_ANALYTIC_BEARING','POSITIVE_AREA_PATCH','AXIAL_BEARING_PLANES_COINCIDE','SOURCE_PLANE_BOND_PATCH','NO_INTERIOR_WITNESS','PROVED_COAXIAL_SHAFT_CLEARANCE','DEDICATED_CLEARANCE_BORE_PRESENT','POSITIVE_VOLUME_METAL_JOIN','SOURCE_PLANE_ANNULAR_PATCH'}
 need(all(x['status'] in allowed for x in joints['fastener_checks']),'unexpected joint status')
 need(len(joints['fastener_checks'])==132 and sum(x['status']=='AXIAL_BEARING_PLANES_COINCIDE' for x in joints['fastener_checks'])==12,'complete fastener stack coverage')
 return {'status':'JOINED_SOURCE_GEOMETRY_SCREEN_PASS_CONDITIONAL','input_receipt_sha256':sha(candidate/'receipt.json'),'free_curve_carrier_lower_mm':c['carrier_minimum'][0],'end_carrier_lower_mm':ends['minima']['carrier'][0],'rigid_wall_residual_mm':min(x['after_0p35_closure_mm'] for x in solids['enclosure']),'solid_count':204,'contact_supports':228,'source_obstacles':4669,'trimmer_columns':100,'native_calls':0,'electrical_acceptance':False,'physical_qualification':False,'adopted':False,'qualification':'Engineering floating bounds with explicit source/process/datum/C0-C1-C2 hypotheses. Joint contact is not strength; tool reservations are not baseline physical access qualification.'}
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--candidate',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args();result=verify(a.candidate);a.output.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
