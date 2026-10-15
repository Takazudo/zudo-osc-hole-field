"""Bind drawing-driven whole-header correction to complete paths and returns; no native work."""
import argparse
import json
import math
from pathlib import Path
import assembly as a
import direct_study as d
import stage5_rebudget as repair
import stage5_dual_metrics as metrics
OUT=a.OUT/'stage6'

def rebuild(prior,baseline,assembly,spec,mechanical):
    candidate,changes=repair.apply_moves(baseline,assembly,spec)
    gh_z=mechanical['middle_GH_opposite_surface_z_mm']
    a.c.require(math.isfinite(gh_z) and math.isclose(mechanical['middle_female_mount_surface_z_mm']-gh_z,mechanical['pcb_thickness_mm']) and mechanical['pcb_thickness_mm']>0,'middle board face datum inconsistent')
    header={(p['instance'],p['ref']):p for p in candidate['middle_header_placements_all_instances']}
    for w in candidate['wire_checks']:
        front=next(p for p in assembly['front_instances'][w['instance']] if p['ref']=='H:'+w['link'])
        middle=header[w['instance'],'M:'+w['link']]
        fp=front['pads_mm'][w['pin']][0]+[front['conditional_pcb_depth_mm']]
        mp=middle['pads_mm'][w['pin']][0]+[gh_z]
        w.update(front_pad_xyz_mm=fp,middle_pad_xyz_mm=mp)
        w['straight_pad_distance_mm']=math.dist(fp,mp)
        w['minimum_remaining_slack_mm']=57-w['straight_pad_distance_mm']
        w['within_slack_allocation']=w['minimum_remaining_slack_mm']>=10
    a.c.require(all(w['within_slack_allocation'] for w in candidate['wire_checks']),'registered middle face wire slack')
    candidate['tolerance_service']['wire_minimum_slack_mm']=min(w['minimum_remaining_slack_mm'] for w in candidate['wire_checks'])
    changes['original_50mm_reference_plane_minimum_slack_mm']=changes['minimum_wire_slack_mm']
    changes['minimum_wire_slack_mm']=candidate['tolerance_service']['wire_minimum_slack_mm']
    changes['middle_GH_pad_plane_mm']=gh_z
    a.c.require([d.identity(r) for r in candidate['paths']]==[d.identity(r) for r in prior['paths']], 'crossing identity changed')
    path_changes=[]
    for i,(old,new) in enumerate(zip(prior['paths'],candidate['paths'])):
        permitted={'middle_header_pad_mm','segments','total_mm','margin_mm'}
        a.c.require({k:v for k,v in old.items() if k not in permitted}=={k:v for k,v in new.items() if k not in permitted},'nonheader endpoint changed')
        a.c.require({k:v for k,v in old['segments'].items() if k!='middle_trace_mm'}=={k:v for k,v in new['segments'].items() if k!='middle_trace_mm'},'nonmiddle allowance changed')
        if old!=new:path_changes.append(i)
    return_changes=[]
    a.c.require(len(prior['returns'])==len(candidate['returns'])==240,'return inventory changed')
    for i,(old,new) in enumerate(zip(prior['returns'],candidate['returns'])):
        permitted={'middle_header_pad_mm','middle_return_corridors'}
        a.c.require({k:v for k,v in old.items() if k not in permitted}=={k:v for k,v in new.items() if k not in permitted},'return ownership changed')
        if 'link' not in old:a.c.require(old==new,'rear return changed')
        else:
            clean=lambda row:[{k:v for k,v in c.items() if k!='allocation_mm'} for c in row['middle_return_corridors']]
            a.c.require(clean(old)==clean(new),'middle return corridor identity changed')
        if old!=new:return_changes.append(i)
    a.c.require(candidate['shared_aggregate_capacitance']==prior['shared_aggregate_capacitance'],'shared cap obligations changed')
    summary=metrics.summarize('stage6_drawing_repair',candidate,assembly['config'],sorted(map(d.identity,prior['paths'])))
    return candidate,{'relative_to_stage5':{'changed_path_indices':path_changes,'changed_return_indices':return_changes},'relative_to_stage4':changes},summary

def build():
    inputs=[a.OUT/'stage5/candidate-report.json',a.OUT/'stage4/candidate-report.json',a.OUT/'assembly-report.json',OUT/'header-repair-input.json',OUT/'mechanical-input.json']
    prior,base,assembly,spec,mechanical=[json.loads(p.read_text()) for p in inputs]
    c,changes,summary=rebuild(prior['candidate'],base['candidate'],assembly,spec,mechanical)
    bindings=a.binding(inputs+[Path(__file__),Path(__file__).with_name('test_stage6_rebudget.py'),Path(repair.__file__),Path(metrics.__file__),Path(d.__file__),Path(a.__file__)])
    return {'status':'DRAWING CORRECTION REBUDGET; SOURCE ONLY','source_sha256':bindings,'candidate':c,'changes':changes,'dual_metrics':summary,'power_coordinate_scope':'Front/shared/rear source packages unchanged from Stage4 normalized power inventory; only explicit transport header pads change. X1 hosting is separately inventoried and not silently merged into these225OSC crossings.','combined_acceptance':'NOT QUALIFIED','native':'NOT RUN','simulation':'NOT RUN','physical':'NOT RUN'}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args();r=build();data=json.dumps(r,separators=(',',':'),sort_keys=True)+'\n';p=OUT/'candidate-report.json'
    if args.check:a.c.require(p.read_text()==data,'stale Stage6 rebudget')
    else:p.write_text(data)
    print('Stage6 rebudget',r['changes']['relative_to_stage5'],'max',r['candidate']['maximum_mm'],'strict failures',r['candidate']['overlength_count'])
if __name__=='__main__':main()
