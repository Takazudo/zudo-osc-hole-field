"""One explicit unchanged-copper corridor screen; not a routing proposal."""
import argparse
import collections
import json
import math
import subprocess
from pathlib import Path

from shapely.geometry import LineString, Point, Polygon

from attribution import seal
from prepare_diagnostic import HERE, ROOT, authenticate, encoded, read, sha, target_members

OLD = 'c0665fffed85e4790aaa2ffb921cf8334ee6c0f0'
OLD_LANE = 'circuit/routing/issue189/jl117-u8202-via-branch/'
SOURCE_UUID = '6975e90e-b67f-50cd-863b-4b65183570b6'
ANCHOR_UUID = '39a29ec9-950c-594e-8404-a79c5e4be303'
VICTIM = 'X9231A7A2CB5A5CD78220'
NEXT_CASE = 'XA31851703CA7C8D2D0C4'


def source_rows(dump):
    return [(kind[:-1], i, obj) for kind in ('pads', 'tracks', 'vias') for i, obj in enumerate(dump[kind])]


def identity(kind, index, obj):
    return {'object_type': kind, 'source_row_index': index, 'uuid': obj['uuid'],
            'source_row_sha256': seal(obj), 'source_geometry': obj}


def collision(kind, obj, line, width=.3, clearance=.25, res=.025):
    """Continuous distance to the exact recorded polygon/segment/disc.

    Conservative envelope uses rail growth and both source-router half-cell
    diagonals plus .01 mm. It can reject extra geometry; it is not the EDT mask,
    a KiCad shape oracle or evidence of physical impossibility.
    """
    scale = 1e6
    growth = .05 if obj['net'] in ('+12V', '-12V', '+5V', 'AGND') else 0
    if kind == 'pad':
        if 'F.Cu' not in obj['layers'] or not obj['poly']: return None
        shape = Polygon([(x/scale,y/scale) for x,y in obj['poly']]); radius=0
    elif kind == 'track':
        if obj['layer'] != 'F.Cu': return None
        shape=LineString([(x/scale,y/scale) for x,y in (obj['a'],obj['b'])]); radius=obj['width']/2/scale
    else:
        shape=Point([v/scale for v in obj['xy']]); radius=obj['diameter']/2/scale
    distance=max(0, line.distance(shape)-radius)
    physical=clearance+width/2
    conservative=physical+growth+2*res/math.sqrt(2)+.01
    if distance >= conservative: return None
    return {'minimum_centreline_to_recorded_copper_mm': distance,
            'required_width_half_plus_clearance_mm': physical,
            'rail_growth_mm': growth, 'two_half_diagonals_plus_epsilon_mm': 2*res/math.sqrt(2)+.01,
            'conservative_required_mm': conservative,
            'unexpanded_envelope_collision': distance < physical,
            'rule': 'F.Cu foreign copper unchanged; conservative continuous-distance screen'}


def net_obligation(dump, net):
    rows=[identity(k,i,o) for k,i,o in source_rows(dump) if o['net']==net]
    groups=dump['islands'].get(net)
    return {'net': net, 'all_source_rows_count': len(rows), 'all_source_rows_sha256': seal(rows),
            'all_source_row_identities': [[row['object_type'], row['source_row_index'], row['uuid'], row['source_row_sha256']] for row in rows],
            'all_original_pad_identities': [{**{k: row[k] for k in ('source_row_index', 'source_row_sha256')}, **{k: row['source_geometry'][k] for k in ('uuid', 'ref', 'pad', 'net', 'xy', 'layers')}} for row in rows if row['object_type']=='pad'],
            'original_disconnected_groups': groups,
            'connectivity_scope': 'Full original group membership available in accepted dump' if groups is not None else 'Net omitted from disconnected-islands map; preserve all source rows and original connected topology. Exact connected-group membership is not supplied by this dump.',
            'restoration': 'Any later transaction must reconnect every displaced pad and retained outside boundary to its original group; unchanged objects remain byte-identical. No cuts or restoration geometry selected here.'}


def boundary_candidates(blocker, dump):
    """Source copper touching exact potential endpoints; not native topology."""
    obj=blocker['source_geometry']; kind=blocker['object_type']
    endpoints=[obj['a'],obj['b']] if kind=='track' else [obj['xy']]
    layers=[obj['layer']] if kind=='track' else obj['layers'] if kind=='pad' else dump['layers']
    output=[]
    for endpoint in endpoints:
        point=Point([v/1e6 for v in endpoint]); touching=[]
        for other_kind,index,other in source_rows(dump):
            if other['net']!=obj['net'] or (other_kind==kind and index==blocker['source_row_index']):continue
            other_layers=[other['layer']] if other_kind=='track' else other['layers'] if other_kind=='pad' else dump['layers']
            common=sorted(set(layers)&set(other_layers))
            if not common:continue
            if other_kind=='pad':
                if not other['poly']:continue
                distance=point.distance(Polygon([(x/1e6,y/1e6) for x,y in other['poly']]))
                radius=0
            elif other_kind=='track':
                distance=point.distance(LineString([(x/1e6,y/1e6) for x,y in (other['a'],other['b'])]));radius=other['width']/2e6
            else:
                distance=point.distance(Point([v/1e6 for v in other['xy']]));radius=other['diameter']/2e6
            if distance<=radius+1e-9:
                touching.append({'object_type':other_kind,'source_row_index':index,'uuid':other['uuid'],
                                 'source_row_sha256':seal(other),'layers':common})
        output.append({'xy_nm':endpoint,'layers':layers,'retained_same_net_touching_row_candidates':touching})
    return {'object_type':kind,'uuid':obj['uuid'],'source_row_index':blocker['source_row_index'],
            'source_row_sha256':blocker['source_row_sha256'],'endpoints':output,
            'scope':'Exact recorded copper overlap at potential removal endpoint, without growth/margins. These are source boundary candidates; poured zones ignored, no cut topology calculated or native outside component identity established.',
            'restoration_status':'NOT PROVED; no removal selected and no complete coupled restoration geometry. Preserve all original pads/source rows/native groups and outside boundaries.'}


def refuse_duplicate_cut_ids(dump, selected):
    counts=collections.Counter(o['uuid'] for kind,index,o in source_rows(dump))
    if any(counts[u]!=1 for u in selected):
        raise ValueError('selected cut identity missing or repeated UUID; cuts refused')


def generate(archive):
    dump,endpoints,artifact=authenticate(archive)
    rows=source_rows(dump); pads={p['uuid']:p for p in dump['pads']}
    source=pads[SOURCE_UUID]; anchor=pads[ANCHOR_UUID]
    target=set(target_members(dump))
    group=next(g for g in dump['islands']['AGND'] if ANCHOR_UUID in g)
    if target & set(group) or len(anchor['layers']) != len(dump['layers']):
        raise ValueError('anchor must be through copper in a distinct original AGND component')
    path=[[v/1e6 for v in source['xy']], [source['xy'][0]/1e6,anchor['xy'][1]/1e6], [v/1e6 for v in anchor['xy']]]
    line=LineString(path); blockers=[]
    for kind,index,obj in rows:
        if obj['net']=='AGND': continue
        result=collision(kind,obj,line)
        if result is not None: blockers.append({**identity(kind,index,obj),**result})
    foreign_nets=sorted({b['source_geometry']['net'] for b in blockers})
    receipts={}
    for name in ('plan.json','boundary-endpoints.json','native-cut-membership.json'):
        raw=subprocess.run(['git','show',OLD+':'+OLD_LANE+name],cwd=ROOT,check=True,capture_output=True).stdout
        receipts[name]={'commit':OLD,'path':OLD_LANE+name,'sha256':sha(raw),'content':json.loads(raw),
                        'scope':'immutable committed historical receipt only; original full native artifact not reauthenticated or rerun'}
    previous=read(HERE/'diagnostic-plan.json')
    six=previous['six_pad_minus12_preservation_obligation']
    for obj in six:
        if pads[obj['uuid']] != obj or obj['net'] != '-12V': raise ValueError('six-pad obligation drift')
    duplicate_ids={u for u,n in collections.Counter(o['uuid'] for k,i,o in rows if k=='track').items() if n>1}
    next_case=next(c for c in read(HERE/'cases.json')['cases'] if c['net']==NEXT_CASE)
    return {'status':'BOUNDED NEGATIVE SOURCE CORRIDOR SCREEN; NO COMPLETE COUPLED PLAN; NO COPPER PROPOSAL',
            'board_sha256':endpoints['settled_board_sha256'],'dump_sha256':endpoints['dump_sha256'],
            'archive_digest':artifact['digest'],'script_sha256':sha(Path(__file__).read_bytes()),
            'corridor':{'source':source,'existing_anchor':anchor,'layer':'F.Cu','centreline_mm':path,
                        'width_mm':.3,'clearance_mm':.25,'via_diameter_mm':.6,'via_drill_mm':.3,
                        'allocation_mm':previous['diagnostic']['bounds_mm'],
                        'new_via_required':False,'length_mm':line.length,
                        'goal_component':{'all_member_count':len(group),'sorted_members':sorted(group),'sorted_members_sha256':seal(sorted(group))}},
            'screen':{'blocker_rows':blockers,'blocker_endpoint_preservation_obligations':[boundary_candidates(b,dump) for b in blockers], 'blocker_rows_count':len(blockers),'foreign_nets':foreign_nets,
                      'zone_pours':'IGNORED; no poured-zone clearance or connectivity claim',
                      'scope':'One explicit centreline against recorded continuous shapes with conservative margins; not route search/native oracle/exhaustive escape review. Blockers overlap and are not a minimum cut set.',
                      'disposition':'Reject this unchanged-copper corridor; no blocker removed, no mask cleared, no rule relaxation',
                      'duplicate_uuid_rows_encountered':sorted({b['uuid'] for b in blockers}&duplicate_ids),
                      'cut_identity_policy':'No cuts selected. A duplicate-UUID cut is rejected; exact row geometry does not grant permission to cut a UUID shared by multiple accepted rows.'},
            'full_coupled_restoration_obligations':[net_obligation(dump,n) for n in sorted(set(foreign_nets)|{'AGND','-12V',VICTIM})],
            'historical_pr233':{'receipts':receipts,'victim_net':VICTIM,
                                'six_pad_minus12_original_group_obligation':six,
                                'boundary_and_victim_restoration':'Historical two cut components and both retained outside anchors must reconnect with all victim pads in any later coupled transaction; not proven feasible here'},
            'next_diagnosed_case':{'selection_scope':'Different diagnosed case for source-only escape review; no feasibility or routing acceptance claimed',
                                   'reason':'Separate source-diagnosed D8228.2/D8227.2 B.Cu pair 15.299 mm apart, outside the rejected U8202 geometry; D1004.1 F.Cu remains the third mandatory component. This endpoint choice is for review only, with both native open edges retained.',
                                   'case':next_case},
            'search_executed':False,'native_executed':False,'removed_uuids':[],'added_copper':[],
            'next_native_action':'NONE: retained baseline reproduction is not the next action; parent forbids native baseline work and no routing transaction is admissible',
            'remaining':'No complete plausible coupled restoration geometry found by this single bounded screen; stronger method review/native qualification and exact parent slot remain required.'}


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('archive',type=Path)
    parser.add_argument('--check',action='store_true')
    args=parser.parse_args();result=generate(args.archive)
    output=HERE/'coupled-escape-spec.json'
    if args.check:
        if output.read_bytes()!=encoded(result):raise ValueError('coupled source specification drift')
    else:output.write_bytes(encoded(result))
    print(result['status'])
    print('blocker rows:',result['screen']['blocker_rows_count'],'foreign nets:',len(result['screen']['foreign_nets']))
