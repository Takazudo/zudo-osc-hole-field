"""Bind a reversible two-deep feed overlay to exact published lane sources."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import check

HERE = Path(__file__).resolve().parent


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':')).encode()).hexdigest()


def build():
    historical = check.build()  # Validates all15 frozen source inputs.
    power = check.read(check.ROOT/'design/partition/core-split/power/contract.json')
    comparison = check.read(check.ROOT/'design/partition/core-split/mechanical/generated/comparison.json')
    mech = next(x for x in comparison['alternatives'] if x['id'] == 'two-deep')
    original = power['options']['two']['new_feeds'][0]
    revised = copy.deepcopy(original)
    # Preserve complete ordered wire records, including all IDs and current limits.
    revised['endpoint_envelopes'] = [
        {'id':original['endpoint_envelopes'][i]['id'], 'board':board, 'side':side,
         'anchor_xy_mm':[[23+17*(j%3)+shift,15.5+9*(j//3)] for j in range(6)],
         'anchor_height_mm':[1.95,2.05], 'land_position':'Tangent continuation to measured board plane; see robust-curve.json',
         'installed_fit':'NOT QUALIFIED; complete revised collision sweep pending'}
        for i,(board,side,shift) in enumerate([('KA','B.Cu',0),('KB','F.Cu',58)])]
    revised['strain_relief_gap'] = 'Proposed machined split dielectric collet/carrier process; complete arm/joint geometry and retention qualification OPEN'
    check.need(revised['wires'] == original['wires'], 'feed identity/full pin order changed')
    candidates = check.read(check.ROOT/'design/partition/core-split/candidates/two.json')['boards']
    partition = check.read(check.ROOT/'design/partition/partition.json')
    rows = check.obstacles(candidates['two-B'], 'B.Cu', mech, partition)
    monitor_box = [120,12,140,32]
    monitor_gap = min(check.rectgap(monitor_box,o['box']) for o in rows)
    check.need(monitor_gap >= .70, 'moved monitor reserve lacks proposed source clearance')
    return {'schema':1, 'status':'RECONCILED SOURCE OVERLAY; incomplete geometry/physical qualification; NOT APPLIED',
            'producer_epoch':historical['source_commit'],
            'source_lock_sha256':check.sha(HERE/'source-lock.json'),
            'tool_sha256':check.sha(Path(__file__)),
            'process_budget_sha256':check.sha(HERE/'process-budget.md'),
            'scope':'Only CS247 KA-to-KB feed in two-deep; unchanged canonical hardware and lane producers',
            'full_preserved_sections_sha256':{
                'existing_main_lands':digest(power['existing_main_lands']),
                'existing_main_wires':digest(power['existing_main_wires']),
                'ordered_new_feed_wires':digest(original['wires']),
                'return_and_fault_contract':digest(power['return_and_fault_contract']),
                'layer_contract':digest(power['layer_contract']),
                'mechanical_harness_records':digest(mech['harnesses']),
                'frozen_interfaces':digest(comparison['frozen_interfaces']),
                'three_core_option':digest(power['options']['three'])},
            'producer_replacements':{
                'feed':revised,
                'local_corridor':'Historical local 91x34x28 boxes superseded for this overlay only by revised complete swept geometry, currently OPEN',
                'wire_cut_class_mm':[84.5,85.0],
                'existing_main_cut_class_mm':[103.5,104.0],
                'monitor':{'id':'CS247-MON-KB','board':'KB','side':'B.Cu','box_xy_mm':monitor_box,
                           'height_mm':5, 'source_gap_mm':monitor_gap, 'mpn':None,
                           'status':'SOURCE RESERVE ONLY; complete wire/clamp collision pending'}},
            'curve_evidence':{'file':'robust-curve.json','sha256':check.sha(HERE/'robust-curve.json')},
            'require_all_before_physical_acceptance':['full revised obstacle/arm/collet/tube sweep',
                'actual continuous C0/C1/C2 wire and collet-exit qualification',
                'carrier load path and retention/thermal/insulation qualification',
                'qualified main/new cuts and preparation', 'actual hot copper resistance extraction',
                'all100 trimmer access and assembly service', 'all native gates'],
            'gates':{'source_face_identity_reconciliation':True,'complete_new_geometry':False,
                     'supplier_process_capability':False,'physical_fit':False,'native':False,'architecture_adopted':False}}


if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('--check', action='store_true'); args=parser.parse_args()
    result=build(); text=json.dumps(result,indent=2,sort_keys=True)+'\n'; path=HERE/'reconciled-contract.json'
    if args.check: check.need(path.read_text()==text, 'reconciled overlay drift')
    else: path.write_text(text)
    print(json.dumps({'status':result['status'],'gates':result['gates']}))
