"""Candidate geometry and bounded budget analysis; no CAD/native execution."""
import argparse
import hashlib
import itertools
import json
import math
from pathlib import Path
import subprocess
import stage22_requirements as requirements

ROOT=Path(__file__).resolve().parents[3]
REL='design/architecture-278/implementation/'
OUT=ROOT/REL/'stage24'
BASE='d935179b9c08e0d45b69eb5e412223dd514d8117'


def need(ok,message):
    if not ok:raise ValueError(message)


def read(p):return json.loads(p.read_text())
def dump(x):return json.dumps(x,indent=2,sort_keys=True,allow_nan=False)+'\n'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()


def transform(point,matrix):
    need(matrix==[[1,0],[0,-1]],'component-view conversion must preserve x and invert display y only')
    return [point[0],-point[1]]


def validate_process(process):
    need(process['stencil_selected'] is False, 'stencil selection not approved')
    expected = {'mask_expansion_per_side_mm':.05, 'paste_scale_xy':1.,
                'min_mask_to_neighbor_trace_mm':.09, 'min_smd_copper_gap_mm':.15,
                'black_white_1oz_pad_spacing_mm':.13, 'any_color_2oz_pad_spacing_mm':.2}
    need(all(process[k] == v for k,v in expected.items()), 'reviewed mask/paste/process threshold changed')
    thicknesses=process['stencil_thickness_sensitivity_mm']
    need(thicknesses and all(type(t) in (float,int) and math.isfinite(t) and t>0 for t in thicknesses),
         'finite positive foil thickness')
    need(thicknesses==[.1,.12], 'reviewed foil sensitivities changed')


def validate_sources(sources):
    urls={'jlc-capabilities':'https://jlcpcb.com/capabilities/pcb-capabilities',
          'jlc-stencil':'https://jlcpcb.com/help/article/opening-process-standard-of-stencil',
          'jlc-mask':'https://jlcpcb.com/blog/basic-design-of-solder-mask'}
    need(set(sources)==set(urls), 'complete fabrication sources')
    for key,url in urls.items():
        need(sources[key]['url']==url and sources[key]['authority']=='FABRICATOR_PRIMARY', 'fabricator source identity')


def smd_pattern(spec,process):
    validate_process(process)
    length,width,center=(spec[k] for k in ('pad_length_mm','pad_width_mm','center_abs_x_mm'))
    need(all(type(x) in (float,int) and math.isfinite(x) and x>0 for x in (length,width,center)), 'positive pad dimensions')
    mask=process['mask_expansion_per_side_mm'];scale=process['paste_scale_xy']
    need(mask==.05 and scale==1.,'reviewed mask/paste proposal changed')
    copper_gap=2*center-length;mask_gap=copper_gap-2*mask
    need(copper_gap>=process['min_smd_copper_gap_mm'] and mask_gap>=.2,'pad or mask clearance')
    cx,cy=spec['courtyard_mm']
    need(cx>=2*center+length and cy>=width,'courtyard must contain copper')
    return {'pads':{str(i):{'center_mm':[sign*center,0], 'copper_size_mm':[length,width],
                            'mask_size_mm':[length+2*mask,width+2*mask],
                            'paste_size_mm':[length*scale,width*scale], 'hole':None}
                    for i,sign in ((1,-1),(2,1))},
            'copper_gap_mm':copper_gap,'mask_gap_mm':mask_gap,
            'courtyard_mm':spec['courtyard_mm'],
            'stencil_sensitivities':[{'thickness_mm':t,'rectangle_area_ratio':length*width/(2*t*(length+width)),
                                      'nominal_deposit_volume_per_pad_mm3':length*width*t}
                                     for t in process['stencil_thickness_sensitivity_mm']],
            'paste_qualified':False,'fabrication_qualified':False}


def hole_screen(nominal,plus,minus,required_min,required_max):
    need(all(math.isfinite(x) for x in (nominal,plus,minus,required_min,required_max)) and plus>=0 and minus>=0 and required_max>required_min,'hole interval domain')
    low=required_min+minus;high=required_max-plus
    return {'default_finished_interval_mm':[nominal-minus,nominal+plus],
            'required_interval_mm':[required_min,required_max],
            'allowed_nominal_interval_mm':[low,high],
            'any_nominal_can_guarantee':low<=high,
            'nominal_passes':nominal-minus>=required_min and nominal+plus<=required_max}


def din_pattern(drawing,pins,policy):
    coordinates=requirements.drawing_coordinates(drawing)
    need(set(coordinates)==set(pins) and len(pins)==96,'complete 96-contact identity')
    need(policy['finished_hole_nominal_mm']==1 and policy['finished_hole_tolerance_mm']==.1
         and policy['required_position_diameter_mm']==.05,'manufacturer hole/position drift')
    need(policy['paste'] is False and policy['plated_contact_holes'] is True
         and policy['manufacturing_drill_diameter_mm'] is None,'DIN solder process/drill not qualified')
    need(policy['board_installation_transform'] is None and policy['board_thickness_mm'] is None,'unapproved physical installation')
    pad=policy['pad_diameter_mm'];mask=policy['mask_expansion_per_side_mm']
    need(pad==2 and mask==.05,'reviewed DIN pad proposal')
    hole=hole_screen(1,policy['jlc_default_hole_plus_mm'],policy['jlc_default_hole_minus_mm'],.9,1.1)
    position=policy['jlc_default_position_axis_mm']
    # Conservative independent-axis interpretation is a screen, not a process guarantee.
    ring=(pad-hole['default_finished_interval_mm'][1])/2-math.sqrt(2)*position
    need(ring>=policy['annular_ring_screen_mm'],'insufficient conservative annular ring')
    pads={pin:{'center_mm':transform(point,policy['component_view_xy_down_matrix']),
               'net':pins[pin],'copper_diameter_mm':pad,'mask_diameter_mm':pad+2*mask,
               'finished_hole_mm':1,'paste':False} for pin,point in coordinates.items()}
    fixing=[]
    if drawing['view']=='A':
        need(policy['female_fixing_holes_plated'] is False,'fixing holes must not become electrical pads')
        fixing=[{'center_mm':transform([x,.3],policy['component_view_xy_down_matrix']),
                 'finished_diameter_mm':2.8,'tolerance_mm':[0,.1],'plated':False,'copper':False,'paste':False} for x in (-45,45)]
    return {'mpn':drawing['mpn'],'source_view':drawing['view'],'pads':pads,'fixing_holes':fixing,
            'component_view_matrix':policy['component_view_xy_down_matrix'],
            'installed_transform':None,'hole_screen':hole,'position_default_guarantees_drawing':False,
            'conservative_annular_ring_mm':ring,'copper_gap_mm':2.54-pad,'mask_gap_mm':2.54-pad-2*mask,
            'fabrication_status':'BLOCKED_DEFAULT_HOLE_AND_POSITION_TOLERANCE',
            'assembly_status':'THROUGH_HOLE_PROCESS_UNQUALIFIED; NOT_REFLOW_APPROVED',
            'manufacturing_drill_mm':None}


def balanced_transfer(alpha,f,r,cin,cf):
    need(0<=alpha<=1 and f>=0 and r>0 and cin>=0 and cf>=0,'transfer domain')
    ratio=(1+2j*math.pi*f*r*cin)/(1+2j*math.pi*f*r*cf)
    return alpha+(alpha-1)*ratio


def electrical(spec,prior,report):
    need(spec['existing_static_target_V']==prior['criteria']['static_target_V']==.002
         and spec['new_criteria_approved'] is False and prior['criteria']['new_criteria_approved'] is False,'retained criterion')
    need(spec['frequency_requirements_approved'] is False and spec['hardware_correction_applied'] is False,'behavior/adoption promotion')
    need(spec['independent_resistor_tolerance_fraction']==prior['retained_discrete_pairs']['individual_tolerance_fraction']==.001
         and spec['reference_initial_sensitivity_fraction']==prior['conditional_sensitivities']['reference_initial_fraction']==.001,'reference evidence drift')
    need(spec['matched_ratio_sensitivities']==[prior['matching']['ratio_error_25C_fraction'],prior['matching']['ratio_error_I_full_temperature_fraction']],'matching bound drift')
    target=spec['existing_static_target_V'];v=spec['reference_nominal_V'];t=spec['independent_resistor_tolerance_fraction']
    need(v==5,'source reference voltage')
    budget=[]
    for condition in report['conditioned_error_allocation']:
        for state in condition['states']:
            nominal=abs(state['nominal_loading_error_V'])
            budget.append({'condition':condition['network_ratio_condition'],'state':state['state'],
                           'known_nominal_loading_error_abs_V':nominal,
                           'remaining_before_reference_and_other_errors_V':target-nominal,
                           'nonnegative_allocation_possible_without_loading_correction':nominal<=target})
    need(any(not row['nonnegative_allocation_possible_without_loading_correction'] for row in budget),'expected nominal infeasibility missing')
    control=[]
    for fail,cap in itertools.product(spec['manual_return_sensitivities_ohm'],spec['filter_cap_sensitivities_F']):
        a=requirements.bipolar_worst_loading(100000,1000,fail)
        control.append({'return_ohm':fail,'cap_F':cap,'worst_loading_alpha':a,
                        'worst_loading_error_V':requirements.wiper(a,-5,5,100000,1000,fail,cap)['loading_error_V'],
                        'center_1percent_settling_s':requirements.wiper(.5,-5,5,100000,1000,fail,cap)['settling_to_1_percent_s'],
                        'open_wiper_V_per_nA':fail*1e-9})
    ac=[]
    for f in spec['ac_frequency_sensitivities_Hz']:
        ac.append({'frequency_Hz':f,'existing_center_gain':abs(balanced_transfer(.5,f,1e5,0,1e-11)),
                   'symmetric_ideal_center_gain':abs(balanced_transfer(.5,f,1e5,1e-11,1e-11)),
                   'symmetric_independent_5percent_cap_worst_center_gain':max(abs(balanced_transfer(.5,f,1e5,ci,cf)) for ci,cf in itertools.product([.95e-11,1.05e-11],repeat=2)),
                   'scope':'Equal nominal R, ideal amplifier and electrical center; no parasitic/loop/remote-delay qualification.'})
    spare=prior['networks']['RN7102']
    need(spare['unused_elements']==['R3','R4'] and prior['matching']['nominal_each_ohm']==100000,'spare-network evidence')
    return {'status':'NO_NONNEGATIVE_COMPLETE_REFERENCE_ALLOCATION_WITH_RETAINED_LOADING',
            'static_target_V':target,'state_budget':budget,
            'negative_reference_independent_ratio_error_V':v*((1+t)/(1-t)-1),
            'reference_initial_table_sensitivity_V':v*spec['reference_initial_sensitivity_fraction'],
            'matched_ratio_only_contribution_V':[v*d for d in spec['matched_ratio_sensitivities']],
            'matched_spare_option':{'device':prior['device'],'network':'RN7102','elements':spare['unused_elements'],
                                   'pairs':{k:prior['pin_pairs'][k] for k in spare['unused_elements']},
                                   'resistance_change_ohm':[10000,100000],'currently_NC_must_change_explicitly':True,
                                   'inverting_bias_sensitivity_V_at_15nA_nominal':[.00015,.0015],
                                   'inverting_bias_sensitivity_V_at_15nA_Rmax':[.00015*1.001,.0015*(1+prior['matching']['absolute_resistor_tolerance_fraction'])],
                                   'adopted':False,'conclusion':'Ratio improves; higher impedance increases bias contribution tenfold, so this is not a drop-in budget closure.'},
            'control_tradeoffs':control,'ac_tradeoffs':ac,
            'complete_static_error_bound_V':None,'electrical_acceptance':False,'new_acceptance_criteria':False}


def protected():
    changed=subprocess.check_output(['git','diff',BASE,'--name-only','--diff-filter=DMRTUXB'],cwd=ROOT,text=True).splitlines()
    need(set(changed)<={REL+'WORK.md'},'protected historical bytes changed')
    added=subprocess.check_output(['git','diff',BASE,'--name-only','--diff-filter=A'],cwd=ROOT,text=True).splitlines()
    added+=subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines()
    allowed={'scripts/architecture278/implementation/'+p for p in ('stage24_patterns.py','test_stage24_patterns.py')}
    need(all(p.startswith(REL+'stage24/') or p in allowed for p in added),'out-of-scope addition')
    return {'baseline':BASE,'all_preexisting_bytes_preserved_except':[REL+'WORK.md']}


def build(check_cache=False):
    files=[OUT/'definitions.json',OUT/'sources.json',ROOT/REL/'stage21/inventory-input.json',ROOT/REL/'stage21/inventory-report.json',ROOT/REL/'stage22/evidence.json',ROOT/REL/'stage15/electrical-input.json',ROOT/REL/'stage15/electrical-report.json']
    definition,sources,inventory,patterns,evidence,prior,report=map(read,files)
    need(definition['status']=='CANDIDATE_SOURCE_ONLY_NOT_ADOPTED','candidate status')
    rp=definition['smd']['R0603'];rr=evidence['resistor_mounting']['reflow_mm']
    need(all(math.isclose(a,b,abs_tol=1e-12) for a,b in zip([rp['pad_length_mm'],rp['pad_width_mm'],2*rp['center_abs_x_mm']-rp['pad_length_mm']],[rr['pad_length'],rr['pad_width'],rr['gap']])),'resistor manufacturer pattern')
    cp=definition['smd']['C0603'];cr=patterns['footprint_decisions']['capacitor']['density_patterns_mm']['B']
    need([cp['pad_length_mm'],cp['pad_width_mm'],cp['center_abs_x_mm'],cp['courtyard_mm']]==[cr['pad_length_x'],cr['pad_width_y'],cr['pad_center_abs_x'],cr['courtyard']],'capacitor manufacturer pattern')
    need(definition['annotations']['count']==22 and definition['annotations']['physical_land_definition'] is None,'unselected wiring')
    need(definition['din']['jlc_default_hole_plus_mm']==.13 and definition['din']['jlc_default_hole_minus_mm']==.08 and definition['din']['jlc_default_position_axis_mm']==.075,'JLC default tolerances')
    validate_sources(sources)
    for sid,source in sources.items():
        need(source['authority']=='FABRICATOR_PRIMARY' and source['url'].startswith('https://jlcpcb.com/'),'fabricator source identity')
        if check_cache:
            p=ROOT/source['raw_cache'];need(sha(p)==source['sha256'] and p.stat().st_size==source['bytes'],'fabricator receipt mismatch')
    smd={name:smd_pattern(spec,definition['process']) for name,spec in definition['smd'].items()}
    assignment={ref:{'pattern':'R0603' if ref.startswith('R') else 'C0603','pins':row['captured_source']['pins'],'unit_records':row['captured_source']['unit_records']} for ref,row in inventory['selections'].items()}
    need(len(assignment)==19,'complete passive assignment')
    din={sex:din_pattern(evidence['DIN'][sex],inventory['unbound'][ref]['pins'],definition['din']) for sex,ref in [('female','J17909'),('male','J17910')]}
    result={'status':'CANDIDATE_SOURCE_DEFINITIONS_ONLY','smd_patterns':smd,'assignments':assignment,'DIN':din,
            'electrical':electrical(definition['electrical'],prior,report),'annotations':definition['annotations'],
            'production_CAD_changed':False,'native_execution':'NONE','selection_patch_applied':False,'preservation':protected()}
    files += [OUT/'README.md',Path(requirements.__file__),Path(__file__),Path(__file__).with_name('test_stage24_patterns.py')]
    result['source_sha256']={str(p.relative_to(ROOT)):sha(p) for p in files}
    return result


def main():
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');p.add_argument('--check-cache',action='store_true');args=p.parse_args()
    result=build(args.check_cache);body=dump(result);path=OUT/'patterns-budget-report.json'
    if args.check:need(path.read_text()==body,'deterministic pattern/budget drift')
    else:path.write_text(body)
    print('PASS source definitions: 19 passive assignments / 192 DIN contacts; fabrication BLOCKED, budget infeasible, no adoption/native')


if __name__=='__main__':main()
