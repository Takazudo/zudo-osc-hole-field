"""Retain exact candidate route specifications after native identity auditing.

This records reproducible source intent; it does not promote the candidate or
claim electrical acceptance. Native geometry remains the resistance authority.
"""
import argparse
import hashlib
import json
import re
from pathlib import Path

from scripts.pcbgen.uuid_tools import stable_uuid
from scripts.pcbgen.verify_local_links import blocks,TRACK_NET_RE


def retain(board_id,checkpoint,candidate,plans,bridges_path,output):
    before,after=blocks(checkpoint),blocks(candidate)
    units_path=Path('.circuit-cache/issue38-recovery/native-coordinate-units.json')
    units=json.loads(units_path.read_text())
    if units['oracle_version']!='10.0.6' or units['integer_units_per_mm']!=1000000 or units['one_integer_unit_mm']!=1e-6:
        raise ValueError('pinned native coordinate-unit evidence is missing or changed')
    retire_path=Path('design/partition/obsolete-plane-vias.json')
    retired=json.loads(retire_path.read_text())['boards'][board_id]
    retired_ids={r['uuid'] for r in retired}
    original_retired={r['uuid'] for r in retired if r['present_in_canonical_prior_copper']}
    expected={'via':{},'segment':{},'arc':{}}
    geometry={}
    maximum_coordinate_or_dimension_difference=0.
    def track(uid,net,start,end,width,layer):
        if uid in expected['segment']:raise ValueError('duplicate retained track intent')
        expected['segment'][uid]=net
        geometry[uid]={'start':start,'end':end,'width':[width],'layer':layer}
    def via(uid,net,at,diameter,drill):
        if uid in expected['via']:raise ValueError('duplicate retained via intent')
        expected['via'][uid]=net
        geometry[uid]={'at':at,'size':[diameter],'drill':[drill]}
    stages=[];transfers=[]
    for path in plans:
        plan=json.loads(path.read_text())
        if plan['board_id']!=board_id:raise ValueError('source plan belongs to a different board')
        stages.append({'name':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                       'historical_input_board_sha256':plan['board_sha256'],
                       'transfer_count':len(plan['added'])})
        for row in plan['added']:
            identity=row['net']+':'+row['cluster']
            if row['via_xy_mm'] is not None:
                uid=stable_uuid(board_id,'rail-transfer-via',identity)
                if uid not in retired_ids:
                    via(uid,row['net'],row['via_xy_mm'],row['via_diameter_mm'],row['via_drill_mm'])
                else:
                    row={**row,'via_xy_mm':None,'retired_candidate_via_uuid':uid}
            for index in range(len(row['points_mm'])-1):
                uid=stable_uuid(board_id,'rail-transfer-track',identity+':'+str(index))
                width=row.get('segment_widths_mm',[row['width_mm']]*(len(row['points_mm'])-1))[index]
                layer=row.get('segment_layers',[row['layer']]*(len(row['points_mm'])-1))[index]
                track(uid,row['net'],row['points_mm'][index],row['points_mm'][index+1],width,layer)
            transfers.append(row)
    bridge_spec=json.loads(bridges_path.read_text())
    if bridge_spec['board_id']!=board_id:raise ValueError('terminal bridges belong to another board')
    for row in bridge_spec['bridges']:
        capture=row['finite_main_capture_points_mm']
        for name,start,end,width in (
            ('capture',*capture,row['finite_main_capture_width_mm']),
            ('bridge',row['start_mm'],row['end_mm'],row['width_mm'])):
            uid=stable_uuid(board_id,'rail-terminal-exit',row['net']+':'+name)
            track(uid,row['net'],start,end,width,'In2.Cu')
        for index,at in enumerate(row['via_positions_mm']):
            uid=stable_uuid(board_id,'rail-terminal-exit',row['net']+':via:'+str(index))
            via(uid,row['net'],at,row['via_diameter_mm'],row['via_drill_mm'])
    if before['footprint']!=after['footprint']:
        raise ValueError('candidate altered a fixed owner footprint')
    for kind in expected:
        removed=original_retired if kind=='via' else set()
        if set(before[kind])-set(after[kind])!=removed:
            raise ValueError('candidate retired unlisted prior '+kind)
        for uid,value in before[kind].items():
            if uid not in removed and after[kind].get(uid)!=value:
                raise ValueError('candidate altered retained prior '+kind)
        if set(after[kind])-set(before[kind])!=set(expected[kind]):
            raise ValueError('retained source does not explain every new native '+kind)
        for uid,net in expected[kind].items():
            match=TRACK_NET_RE.search(after[kind][uid])
            if match is None or match[1]!=net:
                raise ValueError('retained intent and native copper net disagree')
            for field,value in geometry[uid].items():
                match=re.search(r'\('+field+r'\s+([^)]*)\)',after[kind][uid])
                if match is None:raise ValueError('native source geometry field missing')
                if field=='layer':
                    if match[1].strip('"')!=value:raise ValueError('native source layer mismatch')
                else:
                    actual=[float(v) for v in match[1].split()]
                    differences=[abs(a-b) for a,b in zip(actual,value)]
                    maximum_coordinate_or_dimension_difference=max(maximum_coordinate_or_dimension_difference,*differences)
                    if len(actual)!=len(value) or any(d>1e-6+1e-12 for d in differences):
                        raise ValueError('source geometry differs by more than native 1 nm quantization')
    result={'schema_version':1,'status':'UNSELECTED source candidate; electrical and promotion gates remain OPEN',
        'board_id':board_id,'coordinate_frame':'Native KiCad mm; fixed source panel coordinates plus [100, 50] mm',
        'checkpoint_board_sha256':hashlib.sha256(checkpoint.read_bytes()).hexdigest(),
        'audited_candidate_sha256':hashlib.sha256(candidate.read_bytes()).hexdigest(),
        'plane_proposal':'design/partition/rail-plane-proposals.json','plane_profile':'surface-rails-140um-ground',
        'plane_proposal_sha256':hashlib.sha256(Path('design/partition/rail-plane-proposals.json').read_bytes()).hexdigest(),
        'retirement_source':str(retire_path),'retirement_source_sha256':hashlib.sha256(retire_path.read_bytes()).hexdigest(),
        'retired_uuid_receipts':retired,
        'reconciliation_command':['python3','-m','scripts.pcbgen.retain_power_candidate_source',board_id,
                                  str(checkpoint),str(candidate),str(bridges_path),str(output),*[str(p) for p in plans]],
        'reconciliation_script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        'native_coordinate_unit_mm':1e-6,'comparison_floating_guard_mm':1e-12,
        'native_coordinate_oracle_evidence':units,
        'native_coordinate_evidence_sha256':hashlib.sha256(units_path.read_bytes()).hexdigest(),
        'maximum_observed_source_native_difference_mm':maximum_coordinate_or_dimension_difference,
        'historical_planner_stages':stages,
        'terminal_bridge_source_sha256':hashlib.sha256(bridges_path.read_bytes()).hexdigest(),
        'terminal_bridges':bridge_spec['bridges'],'transfers':transfers,
        'native_new_copper_uuid_counts':{k:len(v) for k,v in expected.items()},
        'source_accounting':'Every new native track/via is explained by a retained generator identity, exact net/layer and dimensions/positions within native 1 nm quantization. Retired candidate vias are omitted; listed prior retirements remain explicit. Refill, native rules, full connectivity, owner preservation and resistance must be rechecked after replay.'}
    output.parent.mkdir(parents=True,exist_ok=True)
    output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
    print(board_id,len(transfers),'transfers',result['native_new_copper_uuid_counts'])


if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('board_id');p.add_argument('checkpoint',type=Path)
    p.add_argument('candidate',type=Path);p.add_argument('bridges',type=Path);p.add_argument('output',type=Path)
    p.add_argument('plans',type=Path,nargs='+');a=p.parse_args()
    retain(a.board_id,a.checkpoint,a.candidate,a.plans,a.bridges,a.output)
