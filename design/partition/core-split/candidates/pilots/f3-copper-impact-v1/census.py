#!/usr/bin/env python3
"""Census one frozen retained-record pose; no pose enumeration or route search."""
import argparse
from collections import Counter, defaultdict
import gzip
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import resource
import sys
import time

from shapely.geometry import Point
from shapely.strtree import STRtree

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[5]
sys.path.insert(0, str(ROOT))
from scripts.pcbgen.netlist import read_netlist

spec = importlib.util.spec_from_file_location('repair', HERE.parent/'f3-integrator-cluster-v2/repair.py')
r = importlib.util.module_from_spec(spec)
spec.loader.exec_module(r)
v = r.v1


def key(row):
    # UUID alone is not unique in the inherited source.
    return str(row['source_span'][0])+':'+str(row['source_span'][1])+':'+row['sha256']


def write(out, name, obj):
    (out/name).write_text(json.dumps(obj, indent=2, sort_keys=True)+'\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--input-dump', type=Path, required=True)
    ap.add_argument('--output', type=Path, required=True)
    args = ap.parse_args()
    assert not args.output.exists(), 'one fresh evidence output; never overwrite'
    started = time.monotonic()
    contract = v.read(HERE.parent/'f3-integrator-cluster-v2/repair-contract.json')
    selected = v.read(HERE/'selected-pose.json')
    seals = v.read(HERE/'input-seals.json')
    for path, digest in seals.items():
        assert v.digest((ROOT/path).read_bytes()) == digest, path
    assert v.digest(args.input_dump.read_bytes()) == contract['original_dump_sha256']
    assert r.shapely.__version__ == '2.1.2' and r.shapely.geos_version_string == '3.13.1'
    args.output.mkdir(parents=True)
    write(args.output, 'execution-start.json', {'operation':'ONE_FIXED_POSE_IMPACT_CENSUS',
          'pose_sha256':v.digest((HERE/'selected-pose.json').read_bytes()),
          'source_sha256':v.digest(Path(__file__).read_bytes()),'pose_search':False})
    b = v.read(ROOT/'design/partition/core-split/candidates/two.json')['boards']['two-A']
    original = v.read(args.input_dump)
    text = (ROOT/'boards/osc-core/osc-core.kicad_pcb').read_text()
    index = [json.loads(x) for x in gzip.open(ROOT/'design/partition/core-split/candidates/copper-index.jsonl.gz','rt')]
    screen = r.Screen(contract, b, original, r.load_copper(index,text,original['layers']),started)
    chosen = {x['ref']:x['pose'] for x in selected['selected_records']}
    assert set(chosen) == set(contract['movable_refs'])
    poses = {ref:{'ref':ref,'old_physical_pose':screen.old[ref],
                  'candidate_physical_pose':chosen.get(ref,screen.old[ref]),
                  'moved':ref in chosen} for ref in contract['closure_refs']}
    packs = {ref:screen.pack(ref,pose) for ref,pose in chosen.items()}
    # One combined check only. No screen(), pose_domain(), choose(), or retries.
    placement = v.placement_checks(b,poses,v.read(ROOT/'design/partition/partition.json'))
    placement['bypass_distances'] = [{'ref':c,'ic':u,'old_mm':d,
        'selected_mm':math.dist([chosen[c][k] for k in ('x_mm','y_mm')],
                              [chosen.get(u,screen.old[u])[k] for k in ('x_mm','y_mm')])}
        for c,u in screen.bypass.items() for d in [screen.bypass_max[c]]]
    selected_pads = [pad for pack in packs.values() for pad in pack['pads']]
    old_pads = {p['uuid']:p for p in original['pads']}
    pairs = []
    reasons = defaultdict(list)
    contacts_at_destination = []
    fixed_pad_conflicts = []
    drill_conflicts = []
    for p in selected_pads:
        for phase,pad in [('old',old_pads[p['uuid']]),('selected',p)]:
            poly = r.polygon(pad)
            for j in sorted(map(int,screen.ct.query(r.expanded_bounds(poly,screen.max_radius+.25)))):
                row = screen.rows[j]
                if not set(pad['layers']).intersection(screen.cl[j]): continue
                gap = poly.distance(screen.cg[j])-screen.cr[j]
                tags = []
                if phase == 'old' and row['net_token'] == pad['net'] and gap <= 1e-7:
                    tags.append('ORIGINAL_MOVED_PAD_CONTACT')
                if phase == 'selected':
                    if row['net_token'] != pad['net'] and gap < .25-1e-7:
                        tags.append('FOREIGN_COPPER_CLEARANCE')
                    if row['kind'] == 'via' and gap < 1e-6:
                        tags.append('VIA_SMD_ANNULUS_EXCLUSION')
                    if row['net_token'] == pad['net'] and gap <= 1e-7:
                        contacts_at_destination.append({'object_key':key(row),'pad_uuid':pad['uuid'],
                            'ref':pad['ref'],'pad':pad['pad'],'gap_mm':gap})
                if tags:
                    pair = {'object_key':key(row),'uuid':row['uuid'],'ref':pad['ref'],
                            'pad':pad['pad'],'pad_uuid':pad['uuid'],'pad_net':pad['net'],
                            'object_net':row['net_token'],'phase':phase,'gap_mm':gap,'reasons':tags}
                    pairs.append(pair)
                    reasons[j].append(pair)
            if phase == 'selected':
                for j in sorted(map(int,screen.pt.query(r.expanded_bounds(poly,.25)))):
                    q = screen.fixed_pads[j]
                    gap = poly.distance(screen.pg[j])
                    if q['net'] != pad['net'] and set(q['layers']).intersection(pad['layers']) and gap < .25-1e-7:
                        fixed_pad_conflicts.append({'ref':pad['ref'],'pad':pad['pad'],'other_ref':q['ref'],
                            'other_pad':q['pad'],'other_uuid':q['uuid'],'gap_mm':gap})
                for q,point,radius in screen.drills:
                    gap = poly.distance(point)-radius
                    if gap < .25-1e-7:
                        drill_conflicts.append({'ref':pad['ref'],'pad':pad['pad'],'drill_ref':q['ref'],
                            'drill_uuid':q['uuid'],'gap_mm':gap})
    moved_pad_conflicts = []
    for i,p in enumerate(selected_pads):
        for q in selected_pads[i+1:]:
            if p['ref'] == q['ref'] or p['net'] == q['net'] or not set(p['layers']).intersection(q['layers']): continue
            gap = r.polygon(p).distance(r.polygon(q))
            if gap < .25-1e-7:
                moved_pad_conflicts.append({'a':p['ref']+'.'+p['pad'],'b':q['ref']+'.'+q['pad'],'gap_mm':gap})
    placement.update(fixed_foreign_pad_conflicts=fixed_pad_conflicts,
                     fixed_drill_conflicts=drill_conflicts,moved_foreign_pad_conflicts=moved_pad_conflicts)
    placement['courtyard_reservation_screen_pass'] = placement.pop('pass')
    placement['all_non_copper_placement_checks_pass'] = bool(
        placement['courtyard_reservation_screen_pass'] and not fixed_pad_conflicts
        and not drill_conflicts and not moved_pad_conflicts
        and all(x['selected_mm'] <= x['old_mm']+1e-7 for x in placement['bypass_distances']))
    lookup = {(p['ref'],p['pad']):p for p in original['pads']}
    lookup.update({(p['ref'],p['pad']):p for p in selected_pads})
    placement['bp_int_distance_to_U2306_5_mm'] = {ref+'.'+pin:
        math.dist(lookup[ref,pin]['xy'],lookup['U2306','5']['xy'])/1e6
        for ref,pin in [('C2312','1'),('U2312','12')]}
    names = v.read(ROOT/'design/reports/board-net-tokens.json')
    components,pins = read_netlist(ROOT/'schematic/boards/osc-core.net')
    full_owners = defaultdict(list)
    for (ref,pin),net in sorted(pins.items()): full_owners[net].append({'ref':ref,'pad':pin})
    parts = {p['ref']:p for p in v.read(ROOT/'design/reports/io-partition.json')['physical_packages']}
    all_pad_shapes = [r.polygon(p) for p in original['pads']]
    pad_tree = STRtree(all_pad_shapes)
    prior29 = {x['uuid'] for x in contract['copper_classification']
               if x['classification']=='EXPLICIT_CANDIDATE_RECONSTRUCTION_OBLIGATION'}
    affected = []
    frontier = {}
    for i in sorted(reasons):
        row = screen.rows[i]
        contact_rows = []
        for j in sorted(map(int,screen.ct.query(r.expanded_bounds(screen.cg[i],screen.max_radius+screen.cr[i])))):
            if i == j or row['net_token'] != screen.rows[j]['net_token'] or not set(screen.cl[i]).intersection(screen.cl[j]): continue
            gap = screen.cg[i].distance(screen.cg[j])-screen.cr[i]-screen.cr[j]
            if gap > 1e-7: continue
            neighbor = screen.rows[j]
            endpoints = [n for n,xy in enumerate(screen.ends[i])
                         if Point(xy).distance(screen.cg[j]) <= screen.cr[i]+screen.cr[j]+1e-7]
            contact_rows.append({'object_key':key(neighbor),'uuid':neighbor['uuid'],'source_span':neighbor['source_span'],
                'sha256':neighbor['sha256'],'layers':screen.cl[j],'kind':neighbor['kind'],
                'gap_mm':gap,'touches_endpoint_indices':endpoints,
                'disposition':'ALSO_DIRECTLY_AFFECTED' if j in reasons else 'PRESERVED_FRONTIER'})
            if j not in reasons: frontier[key(neighbor)] = neighbor
        pad_contacts = []
        for j in sorted(map(int,pad_tree.query(r.expanded_bounds(screen.cg[i],screen.cr[i])))):
            pad = original['pads'][j]
            if pad['net'] == row['net_token'] and set(pad['layers']).intersection(screen.cl[i]) and all_pad_shapes[j].distance(screen.cg[i]) <= screen.cr[i]+1e-7:
                pad_contacts.append({'uuid':pad['uuid'],'ref':pad['ref'],'pad':pad['pad'],
                    'original_xy_nm':pad['xy'],'destination_xy_nm':lookup[pad['ref'],pad['pad']]['xy'],
                    'moved':pad['ref'] in chosen})
        affected.append(row|{'object_key':key(row),'source_net':names.get(row['net_token'],row['net_token']),
            'geometry':{'endpoints_or_center_mm':screen.ends[i],'layers':screen.cl[i],
                        'width_or_diameter_mm':2*screen.cr[i],'drill_mm':row.get('drill_mm')},
            'previous_29_obligation':row['uuid'] in prior29,
            'impact_pairs':reasons[i],'complete_same_net_copper_contacts':contact_rows,
            'original_fixture_pad_contacts':pad_contacts,
            'proposed_disposition':'OWNER_DECISION_REQUIRED_EXACT_OBJECT_RECONSTRUCTION',
            'actual_disposition':'PRESERVED_UNCHANGED',
            'obligation':'Preserve all listed source contacts (including midsegment branches), original net/layers/width and via interlayer connectivity; reconnect moved pad UUIDs at proposed destinations. Connect every preserved frontier port before cutting anything. Wider changes require a new exact-object list. Full accepted native groups and zone contacts remain unverified.'})
    nets = []
    affected_nets = {row['net_token'] for row in affected}
    for net in sorted(affected_nets):
        rows = [x for x in affected if x['net_token']==net]
        owners = full_owners[net]
        nets.append({'net_token':net,'source_net':names.get(net,net),'affected_objects':len(rows),
                     'kinds':dict(Counter(x['kind'] for x in rows)),
                     'prior29_objects':sum(x['previous_29_obligation'] for x in rows),
                     'full_source_net_pad_ownership':owners,
                     'outside_24_refs':sorted({x['ref'] for x in owners}-set(contract['closure_refs'])),
                     'shared_rail_or_return':net in ('AGND','+12V','-12V','+5V'),
                     'scope_note':'Net ownership is a continuity recheck obligation, not permission to move owners or reroute/delete the whole net.'})
    ownership_refs = sorted({p['ref'] for net in nets for p in net['full_source_net_pad_ownership']})
    ownership = {ref:parts.get(ref,{'ref':ref,'source':'netlist endpoint absent io physical_packages'}) for ref in ownership_refs}
    summary = {'status':'ONE_RETAINED_POSE_COPPER_IMPACT_PROPOSAL_ONLY','new_pose_searches':0,
        'selected_groups_censused':1,'selected_pad_count':len(selected_pads),
        'accepted_copper_rows':len(screen.rows),'authenticated_index_rows':len(index),
        'direct_affected_objects':len(affected),'direct_kinds':dict(Counter(x['kind'] for x in affected)),
        'previous29_in_direct_set':sum(x['previous_29_obligation'] for x in affected),
        'additional_objects_beyond_previous29':sum(not x['previous_29_obligation'] for x in affected),
        'selected_conflict_pairs':sum(x['phase']=='selected' for x in pairs),
        'old_contact_pairs':sum(x['phase']=='old' for x in pairs),
        'affected_nets':len(nets),'preserved_same_net_frontier_objects':len(frontier),
        'same_net_copper_contact_records':sum(len(x['complete_same_net_copper_contacts']) for x in affected),
        'fixture_pad_contact_records':sum(len(x['original_fixture_pad_contacts']) for x in affected),
        'joint_courtyard_violations':len(placement['same_face_gap_violations']),
        'reservation_conflicts':len(placement['reservation_conflicts']),
        'bypass_policy_violations':sum(x['selected_mm']>x['old_mm']+1e-7 for x in placement['bypass_distances']),
        'fixed_foreign_pad_conflicts':len(fixed_pad_conflicts),'drill_conflicts':len(drill_conflicts),
        'moved_foreign_pad_conflicts':len(moved_pad_conflicts),
        'copper_changed':False,'native_executed':False,'routing_admitted':False,
        'geometry_scope':'Complete pad versus retained straight-segment/circular-via conflict census for this frozen pose only. Fixture-pad contacts are not complete accepted-board pad/group/zone connectivity. No minimum-cut, route feasibility or global minimal-scope claim.',
        'elapsed_seconds':time.monotonic()-started,'peak_memory_kib_linux':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss}
    for path,digest in seals.items(): assert v.digest((ROOT/path).read_bytes()) == digest,path
    assert v.digest(args.input_dump.read_bytes()) == contract['original_dump_sha256']
    write(args.output,'placement-checks.json',placement)
    write(args.output,'affected-objects.json',affected)
    write(args.output,'net-ownership.json',nets)
    write(args.output,'owner-source-records.json',ownership)
    write(args.output,'preserved-frontier.json',list(frontier.values()))
    write(args.output,'selected-pads.json',selected_pads)
    write(args.output,'destination-same-net-contacts.json',contacts_at_destination)
    write(args.output,'zone-recheck-obligations.json',[x for x in index if x['kind']=='zone'])
    write(args.output,'summary.json',summary)
    print(json.dumps(summary,indent=2))


if __name__ == '__main__': main()
