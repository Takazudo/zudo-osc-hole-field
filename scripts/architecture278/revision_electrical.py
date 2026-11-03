"""Design-only connection conservation and scalar circuit bounds; no CAD/solver execution."""
import argparse, hashlib, json, math
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
PACK=ROOT/'design/architecture-278'

def require(ok):
    if not ok:raise ValueError('connection invariant failed')

def validate_geometry(mechanical):
    # This bounded candidate supports this populated tile/bank only. A revised
    # fixture design must update the geometry contract rather than silently
    # reusing hard-coded manufacturer contact datums and orientation formulas.
    expected={'tile_mm':[103,115],'connector_box_mm':[1.5,11,101.5,26],
              'middle_depth_mm':50,'core_depth_mm':69.2}
    cfg=mechanical['config']
    for key,value in expected.items():
        if cfg.get(key)!=value:raise ValueError('unsupported route geometry: '+key)
    stack=cfg['core_depth_mm']-cfg['middle_depth_mm']
    tolerance=cfg.get('stack_tolerance_mm')
    if isinstance(tolerance,bool) or not isinstance(tolerance,(int,float)) or not math.isfinite(tolerance) or tolerance<0:
        raise ValueError('invalid connector stack tolerance')
    if stack-tolerance<18.3 or stack+tolerance>20 or stack+tolerance>25:
        raise ValueError('connector stack exceeds selected pair or developed-path allocation')

def compare_front_banks(contract, mechanical, pinout, functional_links=None, angles=None):
    """Move proposed headers to actual function midpoints without changing panel hardware."""
    validate_geometry(mechanical)
    rows=[]
    for instance in ('O1','O2'):
        ox,oy=mechanical['config']['origins_mm'][instance]
        angle=(angles or {}).get(instance,0)
        def rotate(x,y):
            return {0:(x,y),90:(115-y,x),180:(103-x,115-y),270:(y,103-x)}[angle]
        harnesses=contract['harnesses'] if functional_links is None else contract['harnesses'][:4]+[{'id':l['id'],'function_uid':l['uid'],'faces':[{'pin_map':l['pins']}]} for l in functional_links]
        for h in harnesses:
            members=[]
            for pin,netname in h['faces'][0]['pin_map'].items():
                if netname=='AGND':continue
                n=next(n for n in contract['nets'] if n['net']==netname)
                uids=[v['uid'].replace('O1',instance) for v in n['source_crossing'].get('members',[]) if v.get('uid')]
                if h.get('function_uid'):uids=[h['function_uid'].replace('O1',instance)]
                if not uids:
                    key=netname.split('/')[-1].split('_')[0]
                    uids=[f'J:{instance}.{key}']
                front=[p for p in mechanical['front_locked_O1_O2'] if p['uid'] in uids]
                members.append((pin,n,front))
            points=[p for _,_,pp in members for p in pp]
            if not points:
                rows.append({'instance':instance,'harness':h['id'],'status':'front association unavailable; no passing length inferred'})
                continue
            fx=(min(p['x_mm'] for p in points)+max(p['x_mm'] for p in points))/2
            fy=(min(p['y_mm'] for p in points)+max(p['y_mm'] for p in points))/2
            for pin,n,front in members:
                dp=next((p for p in pinout if p.get('source_conductor')==h['id']+':'+pin),None)
                if dp is None and h.get('function_uid'):dp=next((p for p in pinout if p.get('net')==n['net']),None)
                if not dp or not front:
                    rows.append({'instance':instance,'harness':h['id'],'pin':pin,'net':n['net'],'status':'shared-middle-only or front association unavailable; retained in original conductor ledger'})
                    continue
                p=dp['pin'];lx,ly=rotate(12.13+(int(p[1:])-1)*2.54,18.5+('abc'.index(p[0])-1)*2.54);px=ox+lx;py=oy+ly
                direction=n['source_crossing'].get('direction',{})
                drivers=direction.get('source_nodes',[]) if isinstance(direction,dict) else []
                endpoints=[e for e in n['endpoints'] if e['owner']=='rear-core']
                sources=[e for e in endpoints if any(v['ref']==e['ref'] and v['pin']==e['pin'] for v in drivers)]
                remote_endpoints=sources or endpoints
                rear=max([abs(ox+rotate(*q['origin_mm'])[0]-px)+abs(oy+rotate(*q['origin_mm'])[1]-py)+5 for e in remote_endpoints for q in mechanical['O1_placements'] if q['ref']==e['ref']],default=0)
                front_trace=max(math.hypot(p['x_mm']-fx,p['y_mm']-fy) for p in front)+10
                middle=math.hypot(px-fx,py-fy)+5
                total=front_trace+60+middle+25+rear
                geometric=max([math.sqrt((ox+rotate(*q['origin_mm'])[0]-f['x_mm'])**2+(oy+rotate(*q['origin_mm'])[1]-f['y_mm'])**2+(69.2-11.8)**2) for e in remote_endpoints for q in mechanical['O1_placements'] if q['ref']==e['ref'] for f in front],default=0)
                rows.append({'instance':instance,'harness':h['id'],'pin':pin,'net':n['net'],'new_front_bank_mm':[fx,fy],'front_panel_uids':[p['uid'] for p in front],'front_trace_mm':front_trace,'front_flex_mm':60,'middle_mm':middle,'connector_mm':25,'rear_to_source_or_receivers_mm':rear,'geometric_straight_line_lower_bound_mm':geometric,'lower_bound_scope':'optimistic endpoint geometry only; omits connector detour, bend radii, return topology and circuit-aware routing','total_mm':total,'within_300mm':total<=300,'remote_endpoint_refs_pins':[e['ref']+':'+e['pin'] for e in remote_endpoints],'status':'evaluated header relocation comparison, not chosen implementation; raw-wiper dedicated refinement is separate'})
            rows.append({'instance':instance,'harness':h['id'],'net':'AGND','status':'adjacent return follows each signal corridor; whole-card AGND endpoint spread is not a single remote signal length; strict complete power return budget remains separate'})
    return rows

def build(contract):
    slots=[f'{r}{i}' for i in range(1,33) for r in 'abc']
    reference=json.loads((PACK/'interface-contract.json').read_text())
    if contract != reference:raise ValueError('input differs from source-bound interface contract')
    routes=[]; din=[]
    for h in contract['harnesses']:
        require(len(h['faces'])==2)
        a,b=h['faces']; require(a['pin_map']==b['pin_map'])
        for pin,net in a['pin_map'].items():
            mid_only=net.startswith('OSC_OCT')
            row={'harness':h['id'],'original_pin':pin,'net':net,'original_faces':[a['id'],b['id']],
                 'front_link':h['id'],'middle_destination':'shared octave source' if mid_only else 'rear connector',
                 'rear_pin':None if mid_only else slots[len(din)]}
            routes.append(row)
            if not mid_only: din.append({'pin':row['rear_pin'],'net':net,'source_conductor':h['id']+':'+pin})
    for net in ('OSC_REF5','OSC_REFN5','OSC_GATE_REF'):
        for n in (net,'AGND'):din.append({'pin':slots[len(din)],'net':n,'source_conductor':'new shared reference interface'})
    require(len(routes)==51 and len({(r['harness'],r['original_pin']) for r in routes})==51)
    require(len(din)<=len(slots) and len({r['pin'] for r in din})==len(din))
    require(set(contract['shared_services'])=={'+12V','-12V','+5V','AGND','OSC_REF5','OSC_REFN5','OSC_GATE_REF',*[f'OSC_OCT{i}' for i in range(6)]})
    # Place five raw wiper inputs next to their explicit relocated receiver resistors.
    raw=[c for c in contract['controls'] if c['type']=='unbuffered wiper']
    for c,target in zip(raw,('a17','a5','a9','a13','a1')):
        row=next(d for d in din if d['net']==c['pins']['2'])
        old=row['pin'];other=next(d for d in din if d['pin']==target)
        other['pin']=old;row['pin']=target
    for row in routes:
        if row['rear_pin'] is not None:
            row['rear_pin']=next(d['pin'] for d in din if d['source_conductor']==row['harness']+':'+row['original_pin'])
    # All declared rear pins receive physical ends; unused fitted contacts remain NC.
    pinout=[{'pin':p,**next(({'net':r['net'],'source_conductor':r['source_conductor']} for r in din if r['pin']==p),{'net':None,'source_conductor':'NC spare'})} for p in slots]
    controls=[]
    for c in contract['controls']:
        if c['type']!='unbuffered wiper':continue
        r=c['source_resistance_upper_ohm']*1.2
        controls.append({'uid':c['uid'],'ref':c['ref'],'wiper_net':c['pins']['2'],'Rth_upper_design_ohm':r,
            'pot_tolerance_assumed_percent':20,'remote_only_tau_at_1nF_us':r*.001,'local_series_ohm':1000,'local_pulldown_ohm':10000000,'local_filter_nF':10 if c['uid'].split('.')[-1] in ('TUNE','FINE','PW') else 0,'local_tau_us':(r+1000)*10000000/(r+1000+10000000)*.01 if c['uid'].split('.')[-1] in ('TUNE','FINE','PW') else 0,'DC_loading_fraction':(r+1000)/(10000000+r+1000),
            'error_at_1nA_uV':(r+1000)*.001,'error_at_10nA_uV':(r+1000)*.01,
            'remote_only_settle_to_0_1percent_us':math.log(1000)*r*.001,
            'maximum_bias_plus_leakage_for_100uV_nA':100000/(r+1000),
            'status':'conditional sensitivity; actual bias/leakage/temp/probe load not certified'})
    require(len(controls)==5)
    # Explicit complete current paths: shared prefix once; three separately powered owners.
    paths=[]
    for owner in ('front-jack','rear-core'):
        for rail in ('+12V','-12V','+5V'):
            paths.append({'owner':owner,'rail':rail,'edges':['source regulation/protection','source feed '+rail,'middle '+rail+' distribution',owner+' bolted rail joint 1',owner+' copper rail strap',owner+' bolted rail joint 2',owner+' local trace/decoupling/load',owner+' local AGND trace',owner+' AGND joint 2',owner+' AGND strap',owner+' AGND joint 1','middle AGND distribution','source AGND feed'], 'state_maxima_mA':dict.fromkeys(('normal','startup','ramp','missing_rail','off_state_injection','output_short','recovery'))})
    for rail in ('+12V','-12V'):
        paths.append({'owner':'shared-middle-reference','rail':rail,'planning_allowance_mA':26,'charge_scope':'once per shared source, never per oscillator','edges':['source regulation/protection','source feed '+rail,'middle '+rail+' distribution','shared reference local trace/decoupling/load','middle local AGND','source AGND feed'],'state_maxima_mA':dict.fromkeys(('normal','startup','ramp','missing_rail','off_state_injection','output_short','recovery'))})
    mechanical=json.loads((PACK/'revision-mechanical-report.json').read_text())
    validate_geometry(mechanical)
    remote_paths=[]
    for instance in ('O1','O2'):
        ox,oy=mechanical['config']['origins_mm'][instance]
        for c in raw:
            front=next(p for p in mechanical['front_locked_O1_O2'] if p['uid']==c['uid'].replace('O1',instance))
            pin=next(d['pin'] for d in din if d['net']==c['pins']['2'])
            px=ox+51.5-39.37+(int(pin[1:])-1)*2.54
            py=oy+18.5+('abc'.index(pin[0])-1)*2.54
            net=next(n for n in contract['nets'] if n['net']==c['pins']['2'])
            endpoint=next(n for n in net['endpoints'] if n['owner']=='rear-core')
            placement=next(p for p in mechanical['O1_placements'] if p['ref']==endpoint['ref'])
            rx,ry=placement['origin_mm']
            rear=abs(ox+rx-px)+abs(oy+ry-py)+5
            middle=math.hypot(px-front['x_mm'],py-front['y_mm'])+5
            length=10+60+middle+25+rear
            remote_paths.append({'uid':front['uid'],'front_ref_pin':front['ref']+':2','receiver_O1_reference_pin':endpoint['ref']+':'+endpoint['pin'],'DIN_pin':pin,'front_trace_allocation_mm':10,'front_flex_cut_length_mm':60,'middle_diagonal_with_detour_mm':middle,'connector_path_allocation_mm':25,'rear_Manhattan_with_fanout_mm':rear,'total_mm':length,'limit_mm':300,'within_length_allocation':length<=300,'status':'dimensioned route allocation, no routed PCB proof; return follows same corridor; capacitance remains separate'})
    require(all(p['within_length_allocation'] for p in remote_paths))
    front_function_links=[]
    for control in contract['controls']:
        if control['uid'].endswith('.OCT'):continue
        nets=[control['pins'][str(i)] for i in (1,2,3)]
        if 'AGND' not in nets:nets.append('AGND')
        position=next(p for p in mechanical['front_locked_O1_O2'] if p['uid']==control['uid'])
        front_function_links.append({'id':'FRONT-'+control['uid'],'uid':control['uid'],'panel_ref':control['ref'],'bank_mm':[position['x_mm'],position['y_mm']],'pins':{str(i+1):n for i,n in enumerate(nets)},'conductors':len(nets),'header_mpn':f'BM0{len(nets)}B-GHS-TBT(LF)(SN)','housing_mpn':f'GHR-0{len(nets)}V-S','contact_mpn':'SSHL-002T-P0.2','identity_status':'GH family-derived candidate; exact 4-way manufacturer evidence required before production','cut_length_mm':60,'both_faces':['front-control','middle']})
    require(sum(p['conductors'] for p in front_function_links)==24)
    old_control=[n for h in contract['harnesses'] if h['id'].startswith('K-P-') for n in h['faces'][0]['pin_map'].values()]
    new_control=[n for p in front_function_links for n in p['pins'].values()]
    from collections import Counter
    require(Counter(new_control)-Counter(old_control)==Counter({'/O1/LOCAL_REF5':2,'/O1/LOCAL_REFN5':1}))
    require(not(Counter(old_control)-Counter(new_control)))
    transport_lengths=[]
    for route in routes:
        harness=next(h for h in contract['harnesses'] if h['id']==route['harness'])
        front_face=next(f for f in harness['faces'] if f['board']!='K')
        # Retained front connector location is a proposal, not a locked panel centre.
        fx,fy=front_face['center_mm']
        ox,oy=mechanical['config']['origins_mm']['O1']
        net=next(n for n in contract['nets'] if n['net']==route['net'])
        rear_endpoints=[e for e in net['endpoints'] if e['owner']=='rear-core']
        if route['rear_pin'] is not None:
            pin=route['rear_pin'];px=ox+51.5-39.37+(int(pin[1:])-1)*2.54;py=oy+18.5+('abc'.index(pin[0])-1)*2.54
            lengths=[]
            for e in rear_endpoints:
                q=next((p for p in mechanical['O1_placements'] if p['ref']==e['ref']),None)
                if q:lengths.append(abs(ox+q['origin_mm'][0]-px)+abs(oy+q['origin_mm'][1]-py)+5)
            rear=max(lengths,default=0);middle=math.hypot(px-fx,py-fy)+5;connector=25
        else:
            # Shared source zone reservation next to the O1 bank; final source placement is not generated.
            middle=math.hypot((ox+51.5)-fx,(oy+18.5)-fy)+25;rear=0;connector=0
        transport_lengths.append({'harness':route['harness'],'pin':route['original_pin'],'net':route['net'],'front_bank_mm':[fx,fy],'front_bank_basis':'retained proposed front header centre; not locked panel hardware','front_trace_allocation_mm':30,'cut_wire_length_mm':60,'middle_trace_allocation_mm':middle,'rear_connector_path_allocation_mm':connector,'rear_trace_max_to_mapped_packages_mm':rear,'total_allocation_mm':30+60+middle+connector+rear,'rear_endpoint_refs_pins':[e['ref']+':'+e['pin'] for e in rear_endpoints],'status':'complete conductor planning bill; unplaced source endpoints/local-copper paths require implementation extraction; raw wipers superseded by refined remote_paths'})
    pin_search=[]
    import copy
    for reference_net in ('/O1/LOCAL_REF5','/O1/LOCAL_REFN5'):
        candidates=[]
        for candidate in pinout:
            if candidate['net'] is not None:continue
            trial=copy.deepcopy(pinout)
            next(p for p in trial if p['net']==reference_net)['pin']=candidate['pin']
            # This is a rejected one-contact geometric experiment, not a publishable pinout.
            paths_trial=compare_front_banks(contract,mechanical,trial,front_function_links)
            candidates.append((max(p['total_mm'] for p in paths_trial if p.get('net')==reference_net and 'total_mm' in p),candidate['pin']))
        best,pin=min(candidates)
        pin_search.append({'net':reference_net,'best_free_pin':pin,'best_worst_receiver_path_mm':best,'candidates_examined':len(candidates),'adopted':False,'reason':'single-pin geometric relocation still exceeds300mm; cannot waive return pairing or claim a passing pinout'})
    return {'status':'bounded design revision; no physical acceptance','source_sha256':{'interface-contract.json':hashlib.sha256((PACK/'interface-contract.json').read_bytes()).hexdigest(),'revision_electrical.py':hashlib.sha256(Path(__file__).read_bytes()).hexdigest()},
      'reference_pin_relocation_experiment':pin_search,'functional_grouped_route_comparison':compare_front_banks(contract,mechanical,pinout,front_function_links),'functional_front_links':front_function_links,'functional_front_regrouping':{'harnesses':11,'conductors':54,'crimps':108,'GH_mating_locations':22,'GH_signal_solder_joints':108,'GH_mechanical_solder_joints':44,'DIN_pairs':1,'DIN_solder_joints':192,'total_proposed_wire_mm':3240,'extra_reference_branches':['LOCAL_REF5 to two additional control links','LOCAL_REFN5 to one additional control link'],'status':'recommended functional grouping supersedes historical mixed K-P pairings; original conductor ledger retained'},'front_bank_relocation_comparison':compare_front_banks(contract,mechanical,pinout),'all_51_transport_lengths':transport_lengths,'O1_front_wire_total_proposed_mm':sum(p['cut_wire_length_mm'] for p in transport_lengths),'remote_paths':remote_paths,'mechanical_report_sha256':hashlib.sha256((PACK/'revision-mechanical-report.json').read_bytes()).hexdigest(),'original_conductors':routes,'rear_connector_pinout':pinout,'active_rear_contacts':len(din),'removed_key_positions':[],
      'service_allocation':{s:('dedicated supported copper feed; not DIN' if s in ('+12V','-12V','+5V','AGND') else 'middle to selector existing GH; no rear stub' if s.startswith('OSC_OCT') else 'DIN with adjacent AGND') for s in contract['shared_services']},
      'comparison':[
       {'name':'original one-cable source baseline','harnesses':11,'wire_conductors':51,'crimps':102,'GH_mating_pairs':22,'GH_header_signal_solder_joints':102,'DIN_pairs':0,'DIN_solder_joints':0},
       {'name':'prior literal two-cable candidate','harnesses':22,'wire_conductors':102,'crimps':204,'GH_mating_pairs':44,'GH_header_signal_solder_joints':204,'DIN_pairs':0,'DIN_solder_joints':0},
       {'name':'direct rear with original front flexible links (mixed recommended)','harnesses':11,'wire_conductors':51,'crimps':102,'GH_mating_pairs':22,'GH_header_signal_solder_joints':102,'DIN_pairs':1,'DIN_solder_joints':192,'DIN_active_mating_contacts':len(din),'DIN_fitted_mating_contacts':96},
       {'name':'all-direct front and rear conditional comparison','harnesses':0,'wire_conductors':0,'crimps':0,'GH_mating_pairs':0,'GH_header_signal_solder_joints':0,'DIN_pairs':4,'DIN_solder_joints':768,'status':'three front regions require connector adapters; rejected because independently fixed front planes need different seating adapters and transmit insertion load'}],
      'additive_power_all_candidates':{'powered_owners':['front-jack','rear-core'],'conductors_per_owner':4,'straps':8,'bolted_contact_interfaces':16,'bolts':16,'washers':32,'locking_elements':16,'independent_strain_relief_points':16,'source_feeders':'retained external shared source wiring; 36 original terminal records preserved below; not extra O1-specific wires'},
      'existing_factory_terminals':contract['rear_terminals'],'paths':paths,
      'power_bound':{'DIN_contact_max_mOhm':20,'rail_total_limit_mOhm':1,'return_total_limit_mOhm':.5,'DIN_single_contact_disposition':'REJECT for rail and ground qualification; signal AGND contacts are supplemental parallel returns, no strict-budget credit','copper_example_length_mm':50,'copper_width_mm':10,'copper_thickness_mm':1,'temperature_C':60,'rho20_ohm_mm2_per_m':.01724,'alpha_per_C':.00393,'bulk_mOhm':.01724*(1+.00393*40)*.05/10*1000,'two_joint_allocation_mOhm':.10,'remaining_return_budget_mOhm':.5-(.01724*(1+.00393*40)*.05/10*1000)-.10,'status':'joint allocation is not supplier guarantee; complete common feed and local trace must fit remainder; four-wire acceptance before energization'},
      'raw_wipers':controls,
      'octave_dynamics':{'branches':5,'series_R_ohm':1000,'filter_C_nF':100,'pull_down_Mohm':10,'max_step_V':5,'nominal_tau_us':100,'initial_all5_current_mA':25,'charge_all5_uC':2.5,'historical_driver_planning_limit_mA':2,'minimum_charge_time_at_2mA_ms':1.25,'linear_settle_to_2mV_ms':math.log(2500)*.1,'direct_parasitic_budget_pF':900,'aggregate_limit_pF':1000,'decision':'25mA step exceeds 2mA planning condition; 0.782ms ideal exponential conditional on nonlimiting source; actual dynamic drive capability unknown, 2mA is a planning condition; retain source circuit, qualify five-receiver switching before acceptance; no buffer substitution'},
      'switched_reference_alternative':{'status':'design option only; not applied','R_series_ohm':15000,'R_series_tolerance':.01,'R_pulldown_ohm':220000000,'R_pulldown_tolerance':.01,'C_F':1e-7,'C_tolerance_assumed':.1,'step_V':5.025,'worst_initial_all5_mA':5*5.025/(15000*.99)*1000,'divider_error_mV':5.025*(15000*1.01)/(220000000*.99+15000*1.01)*1000,'bias_error_at_15nA_mV':15e-9*15000*1.01*1000,'tau_max_ms':15000*1.01*1e-7*1.1*1000,'settle_2mV_ms':math.log(5.025/.002)*15000*1.01*1e-7*1.1*1000,'open_switch_discharge_tau_seconds':220000000*1e-7,'decision':'retain original receiver for parity prototype; measure actual 25mA transient recovery; alternative trades slower fail-to-zero response for lower transient demand'},
      'test_fixture':{'final_connections':0,'temporary_probe_contacts':4,'purpose':'mechanical four-probe simultaneous reservation; move probes sequentially across existing measurement nodes for six trims, no six dedicated new test terminals' ,'reference_load_fixture':'four extra receiver equivalents R1k C100nF R10M plus fifth DUT; separate non-final fixture; counted in 900pF direct probe allowance'}}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--check',action='store_true');args=ap.parse_args()
    out=json.dumps(build(json.loads((PACK/'interface-contract.json').read_text())),indent=2,sort_keys=True)+'\n'
    path=PACK/'revision-electrical-report.json'
    if args.check:
        if not path.exists() or path.read_text()!=out:raise SystemExit('stale revision electrical report')
    else:path.write_text(out)
    print('PASS revision connection conservation/scalar bounds; physical qualification NOT RUN')
if __name__=='__main__':main()
