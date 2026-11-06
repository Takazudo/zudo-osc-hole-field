"""Single constraint-motivated repair proposal; not a new permutation search.

Move the shared circuit rigidly and separate both pull grips. Remaining occupied
volumes are unknown; this proposal is never labeled a feasible assembly.
"""
import argparse
import copy
import json
import math
from pathlib import Path
import assembly as a
import direct_study as d

ROOT,OUT=a.ROOT,a.OUT/'stage4'

def translate_package(p,delta):
    q=copy.deepcopy(p)
    q['origin_mm']=a.transform(p['origin_mm'],delta,0)
    for key in ('box_mm','reserved_box_mm'):
        if key in p:q[key]=a.box_transform(p[key],delta,0)
    q['pads_mm']={pin:[a.transform(xy,delta,0)for xy in points]for pin,points in p['pads_mm'].items()}
    return q

def build():
    assembly=json.loads((a.OUT/'assembly-report.json').read_text())
    prior=json.loads((a.OUT/'direct-study-report.json').read_text())
    candidate=copy.deepcopy(prior['best_by_variant']['baseline']);delta=[6,0]
    shared=[translate_package(p,delta) for p in assembly['shared_middle_placements']]
    config=assembly['config'];changed=[]
    for r in candidate['paths']:
        if r['net'].startswith('OSC_OCT'):
            r['other_pad_mm']=a.transform(r['other_pad_mm'],delta,0)
            r['segments']['middle_trace_mm']=d.segment(r['middle_header_pad_mm'],r['other_pad_mm'],config)
        elif r['net'] in ('OSC_REF5','OSC_REFN5','OSC_GATE_REF'):
            r['front_pad_mm']=a.transform(r['front_pad_mm'],delta,0)
            r['segments']['middle_trace_mm']=d.segment(r['front_pad_mm'],r['DIN_pad_mm'],config)
        else:continue
        r.pop('nominal_interface_geometric_comparison_mm',None)
        r['total_mm']=sum(r['segments'].values());r['margin_mm']=300-r['total_mm']
        r['pad_separation_lower_bound_mm']=math.dist(r['front_pad_mm'],r['other_pad_mm'])
        changed.append(d.identity(r))
    handles=[p for p in candidate['fixtures'] if p['id'].startswith('handle')]
    a.c.require(len(handles)==2,'two supported handles required')
    for handle,x in zip(handles,(11,33)):handle['box_mm']=[x-3,231,x+3,237]
    candidate['shared_middle_placements']=shared
    candidate['shared_group_translation_mm']=delta
    candidate['maximum_mm']=max(r['total_mm']for r in candidate['paths'])
    candidate['minimum_margin_mm']=min(r['margin_mm']for r in candidate['paths'])
    candidate['overlength_count']=sum(r['total_mm']>300 for r in candidate['paths'])
    candidate['by_instance']={i:{'maximum_mm':max(r['total_mm']for r in candidate['paths']if r['instance']==i),'overlength_count':sum(r['total_mm']>300 for r in candidate['paths']if r['instance']==i)}for i in candidate['origins_mm']}
    candidate['power_distribution_coordinate_frame']='historical inventory only; stage4_power report supplies geometry-rebound endpoints, not impedance qualification'
    geometry=d.geometry(candidate['packages'],candidate['fixtures'],prior['spec'],candidate['origins_mm'])
    candidate['geometry']=geometry
    candidate['status']='SINGLE LOCAL REPAIR PROPOSAL; NOT FEASIBLE OR ADOPTED'
    a.c.require(len(candidate['paths'])==225 and len(candidate['returns'])==240,'path/return coverage')
    a.c.require(len(changed)==65,'all nine sharednets branches')
    a.c.require(len(shared)==30,'complete shared group')
    a.c.require(not geometry['proxy_errors'],'local courtyard repair broke existing clearance')
    power_path=OUT/'power-inventory-report.json'
    power=json.loads(power_path.read_text())['variants']['baseline_shared_x6']
    for row in candidate['paths']:
        for side in ('front','other'):
            endpoint=row['actual_identity'][side]
            points=power['placed_packages'][endpoint['ref']]['pads_xyz_mm'][endpoint['pin']]
            a.c.require(any(math.dist(xyz[:2],row[side+'_pad_mm'])<1e-8 for xyz in points),'power endpoint frame mismatch')
    source=[power_path,Path(__file__),Path(__file__).with_name('test_stage4_candidate.py'),Path(d.__file__),Path(a.__file__),a.OUT/'assembly-report.json',a.OUT/'direct-study-report.json']
    return {'status':candidate['status'],'source_sha256':a.binding(source),'candidate':candidate,'changed_shared_path_count':len(changed),'power_endpoint_report':{'path':str(power_path.relative_to(ROOT)),'variant':'baseline_shared_x6','binding':'all225 crossing endpoint XY independently matched to normalized placed-package XYZ; allrail/return nodes resolve through this table; unplaced remainsnull'},
        'unchanged_return_scope':'All240 front/GH/DIN/rear branch allocations remain geometrically unchanged; sharedsource AGND and rail endpoints are rebound separately, with complete impedance/topology OPEN.',
        'shared_carrier_boundary':'Actual30package courtyard union moves rigidly+6mmX. Old45mm island reservation is not a fitted carrier; new carrier/support/edge/tolerance dimensions remain conditional, no shrunken package or implicit free space.',
        'service_proposal':'Retain two independently attached pull handles and existing support/guide concept; centres11/33mm give22mm spacing. Both hands pull the retained rigid frame axially after cover removal and supported power/retainer release; no one-handle pull, hotplug or frame-strength certification. Exact guide engagement, alignment, force distribution and load-bearing frame drawings remain OPEN.',
        'acceptance_limit_interpretation':'300mm/1nF remain source acceptance limits, not demonstrated physical failure thresholds. No claim334mm is unsafe or300mm guaranteedsafe; noise/stability depend on signal and complete circuit/return/parasitics.',
        'occupied_volume':'OTHER28+POWER+services UNKNOWN_RESERVED. No further cluster/interface optimization admitted as feasible before occupied/service intersections are established.',
        'comparisons':{'split_interface':'NOT investigated further: occupied-volume certificate and specific geometric benefit absent; prior cost comparison retained only','core_only_reuse':'historical source comparison retained; no adoption'},'native':'NOT RUN','physical':'NOT RUN'}

def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');args=p.parse_args();r=build();data=json.dumps(r,sort_keys=True,indent=2)+'\n';out=OUT/'candidate-report.json'
    if args.check:a.c.require(out.read_text()==data,'stale stage4 repair')
    else:out.write_text(data)
    print('stage4 local repair',r['candidate']['maximum_mm'],'mm;',r['candidate']['overlength_count'],'overlength;225paths240returns; NOT FEASIBLE')
if __name__=='__main__':main()
