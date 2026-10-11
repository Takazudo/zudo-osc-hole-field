#!/usr/bin/env python3
"""Authenticate and diagnose a saved breakout graph; never execute router A* or native."""
import argparse
import copy
import hashlib
import importlib.util
import json
import math
from pathlib import Path
from unittest.mock import patch

import numpy as np
from scipy import ndimage
import f3_adapter as a
import f3_breakout

HERE = Path(__file__).resolve().parent
COMPONENT_SOURCE = HERE.parent / 'diagnosis-o1/analyze.py'
spec = importlib.util.spec_from_file_location('f3_retained_components', COMPONENT_SOURCE)
component_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(component_module)
components = component_module.components
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()


def authenticate(candidate):
    read = lambda p: json.loads(p.read_text())
    binding = read(candidate/'source-binding.json')
    current = f3_breakout.source_binding(HERE, candidate/'original-dump.json', candidate/'terminal-breakout.json')
    a.require({k:v for k,v in binding.items() if k != 'candidate_file_sha256'} == current, 'candidate method binding drift')
    for name, expected in binding['candidate_file_sha256'].items():
        a.require(sha(candidate/name) == expected, 'candidate file drift: '+name)
    original = read(candidate/'original-dump.json'); card = read(candidate/'terminal-breakout.json')
    packet = read(HERE/'f3-packet/request.json'); domain = packet['demand_and_preservation_contract']
    base_pool = a.saved_pool(read(HERE/'cohort-validation.json'), domain)
    pool, receipt = f3_breakout.prepare(original, domain, base_pool, packet['budget'], packet['route_policy'], 'two-A', card)
    a.require(pool == read(candidate/'adapter-pool.json'), 'candidate pool drift')
    a.require(a.digest(receipt) == a.digest(read(candidate/'breakout-receipt.json')), 'candidate receipt drift')
    a.require(sha(HERE/'route-1641/access-plan.json') == packet['cases']['two-A']['access_plan_sha256'], 'before access plan drift')
    return original, card, packet, pool, receipt, binding


def capture(original, groups, records, packet):
    """Capture the first actual graph input, deriving and checking its exact window."""
    domain = packet['demand_and_preservation_contract']; budget = packet['budget']; policy = packet['route_policy']
    net = domain['targets']['signal']['net_token']
    derived = copy.deepcopy(original)
    derived['pads'].extend(records[u]['pad'] for group in groups for u in group)
    derived['islands'] = {net: groups}; saved = {}; real = a.grid.Raster
    class StopBeforeSearch(Exception): pass
    def raster(*args, **kwargs):
        saved['raster'] = real(*args, **kwargs)
        return saved['raster']
    def stop(free, via, src, goal, *args):
        saved.update(free=free.copy(), via=via.copy(), src=src.copy(), goal=goal.copy())
        raise StopBeforeSearch()
    with patch.object(a.grid, 'Raster', raster), patch.object(a.grid, 'astar', stop), \
         patch.object(a.grid, 'native_astar', side_effect=AssertionError('native forbidden')), \
         patch.object(a.grid, 'astar_py', side_effect=AssertionError('router search forbidden')):
        try:
            a.grid.route(derived, nets=[net], res=budget['raster_mm'], clearance=budget['clearance_mm'],
                rail_nets=policy['rail_nets'], rail_width=budget['rail_width_mm'], signal_width=budget['signal_width_mm'],
                via_diameter=budget['via_diameter_mm'], via_drill=budget['via_drill_mm'],
                max_expansions=budget['max_expansions_per_search'], window_mm=budget['window_margin_mm'],
                bounds_mm=domain['common_bounds_mm'], planes={}, fill_guards=policy['fill_guards'],
                rip=(), full_board=False, rrr_rounds=0, log=lambda _:None)
        except StopBeforeSearch: pass
    a.require('free' in saved, 'no graph input captured')
    r = saved['raster']; fullsrc = a.grid.island_mask(r, derived, groups[1]); fullgoal = a.grid.island_mask(r, derived, groups[0])
    margin = round(budget['window_margin_mm']/budget['raster_mm']); matches = []
    for mask in (fullsrc, fullsrc|fullgoal):
        points = np.argwhere(mask.any(0)); lo = points.min(0); hi = points.max(0)
        y0, y1 = max(0,int(lo[0])-margin), min(r.h,int(hi[0])+margin+1)
        x0, x1 = max(0,int(lo[1])-margin), min(r.w,int(hi[1])+margin+1)
        if np.array_equal(fullsrc[:,y0:y1,x0:x1], saved['src']) and np.array_equal(fullgoal[:,y0:y1,x0:x1], saved['goal']):
            matches.append((y0,y1,x0,x1))
    a.require(len(set(matches)) == 1, 'graph window ambiguous')
    saved['window'] = list(matches[0])
    return saved


def graph_summary(saved, seed_mask):
    passable = saved['free'] | saved['src'] | saved['goal']
    labels = components(passable, saved['via'], saved['src'], saved['goal'])
    roots = set(map(int,np.unique(labels[seed_mask])))-{0}
    reached = np.isin(labels,list(roots)) if roots else np.zeros_like(passable)
    nodes = np.argwhere(reached)
    return {'reachable_nodes': int(reached.sum()),
        'reachable_by_layer': {name:int(reached[i].sum()) for i,name in enumerate(saved['raster'].layers)},
        'goal_nodes_reached': int((reached&saved['goal']).sum()),
        'raster_via_sites': int((reached.any(0)&saved['via']).sum()),
        'through_sites': int((reached.any(0)&(saved['src'].all(0)|saved['goal'].all(0))).sum()),
        'touches_window_edge': bool(reached[:,0,:].any() or reached[:,-1,:].any() or reached[:,:,0].any() or reached[:,:,-1].any()),
        'local_nodes_sha256': a.digest(nodes.tolist())}, reached


def compare(before, after, seed):
    a.require(before['window'] == after['window'], 'different windows cannot establish seed-only causality')
    for key in ('free','via','goal'):
        a.require(np.array_equal(before[key],after[key]), 'non-source graph drift: '+key)
    a.require(not (before['src'] & ~after['src']).any(), 'old source lost')
    added = after['src'] & ~before['src']
    a.require(int(added.sum()) == 1 and added[seed], 'repair must add exactly the named single-layer seed')
    rows = {}; masks = {}
    for name, saved, seeds in [('before',before,before['src']), ('old_sources_on_repaired_graph',after,before['src']),
                               ('new_seed_only',after,added), ('combined_after',after,after['src'])]:
        rows[name], masks[name] = graph_summary(saved,seeds)
    return rows,masks


def exact_region(original, card, packet, saved, reached):
    """Check every internal allowed planar edge, cardinal cut and possible via site."""
    geo = a.Geometry(original); r = saved['raster']; y0,y1,x0,x1 = saved['window']
    net = card['net']; b = packet['budget']; width = b['signal_width_mm']; clearance = b['clearance_mm']
    xy = lambda y,x: [v/1e6 for v in r.point(y+y0,x+x0)]
    guard = round(1.5/b['raster_mm']); margin = b['raster_mm']/math.sqrt(2)+.01
    g0,g1,h0,h1 = max(0,y0-guard),min(r.h,y1+guard),max(0,x0-guard),min(r.w,x1+guard)
    distances = {}
    for li in range(len(r.layers)):
        lab = r.label[li][g0:g1,h0:h1]; fixed = r.fixed_label[li][g0:g1,h0:h1]
        foreign = ((lab!=0)&(lab!=r.net_id[net])) | ((fixed!=0)&(fixed!=r.net_id[net]))
        distances[li] = ndimage.distance_transform_edt(~foreign)*b['raster_mm']
    def endpoint_predicates(li,y,x):
        values = {'foreign_copper':(float(distances[li][y+y0-g0,x+x0-h0]),clearance+width/2+margin),
                  'board_edge':(float(r.d_edge[y+y0,x+x0]),.5+width/2+margin),
                  'keepout':(float(r.d_keep_track[li][y+y0,x+x0]),width/2+margin)}
        return {k:{'distance_mm':d if math.isfinite(d) else None,'threshold_mm':t,'pass':d>=t} for k,(d,t) in values.items()}
    planar = []; boundary = []; vias = []
    for li,y,x in np.argwhere(reached):
        li,y,x = int(li),int(y),int(x); start = xy(y,x); layer = r.layers[li]
        for dy,dx in ((-1,0),(1,0),(0,-1),(0,1),(-1,-1),(-1,1),(1,-1),(1,1)):
            yy,xx = y+dy,x+dx
            if not (0<=yy<reached.shape[1] and 0<=xx<reached.shape[2]):continue
            inside = bool(reached[li,yy,xx])
            if dy and dx and (not inside or not(reached[li,y,xx] and reached[li,yy,x])):continue
            if inside and (yy,xx)<(y,x):continue
            end = xy(yy,xx); validation = geo.segment(start,end,net,layer,width,clearance)
            row = {'layer':layer,'start_mm':start,'end_mm':end,'validation':validation}
            if not inside:
                row['raster_end_predicates'] = endpoint_predicates(li,yy,xx)
                a.require(not all(v['pass'] for v in row['raster_end_predicates'].values()), 'unexplained boundary predicate')
            (planar if inside else boundary).append(row)
        validation = geo.via(start,net,b['via_diameter_mm'],b['via_drill_mm'],clearance)
        # The explicit breakout via is emitted with any full pair. Nearby second vias
        # must also obey validate_rows' new-via spacing; original-only geometry is insufficient.
        distance = math.dist(start,[v/1e6 for v in card['via_nm']])
        spacing = b['via_diameter_mm']/2+b['via_drill_mm']/2+.25+a.EPS
        vias.append({'xy_mm':start,'validation_on_original':validation,'raster_via_ok':bool(saved['via'][y,x]),
            'distance_to_breakout_via_mm':distance,'required_distinct_via_spacing_mm':spacing,
            'distinct_via_allowed_after_breakout':bool(validation['pass'] and distance>=spacing)})
    a.require(all(x['validation']['pass'] for x in planar), 'exact-invalid internal edge; refine claimed region')
    identities = sorted({v['validation']['nearest_foreign'] for v in boundary if v['validation']['nearest_foreign']} |
        {v['validation_on_original']['nearest_foreign'] for v in vias if v['validation_on_original']['nearest_foreign']})
    objects = {o['uuid']:dict(kind=kind,object=o) for kind in ('pads','tracks','vias') for o in original[kind]}
    owners = {}
    for uid in identities:
        a.require(uid in objects, 'unknown obstacle owner '+uid)
        item = objects[uid]; net_members = sorted(p['ref']+'.'+p['pad'] for p in original['pads'] if p['net']==item['object']['net'])
        owners[uid] = dict(item,net_pad_members=net_members)
    nodes = np.argwhere(reached); physical = [xy(int(y),int(x)) for _,y,x in nodes]
    return {'scope':'Complete original obstacle model; exact swept full-width edges and all-layer via/hole/SMD checks. No new graph transitions or physical copper.',
        'reachable_bounds_mm':[min(p[0] for p in physical),min(p[1] for p in physical),max(p[0] for p in physical),max(p[1] for p in physical)],
        'internal_legal_edges':len(planar),'internal_exact_failures':0,'internal_edges_sha256':a.digest(planar),
        'boundary_cardinal_edges':len(boundary),'boundary_exact_pass':sum(v['validation']['pass'] for v in boundary),
        'boundary_exact_fail':sum(not v['validation']['pass'] for v in boundary),'boundary':boundary,
        'original_exact_via_sites':sum(v['validation_on_original']['pass'] for v in vias),
        'distinct_exact_vias_after_breakout':sum(v['distinct_via_allowed_after_breakout'] for v in vias),
        'via_checks':vias,'owners':owners}


def main():
    p = argparse.ArgumentParser(description=__doc__);p.add_argument('--candidate',type=Path,required=True);p.add_argument('--output',type=Path,required=True)
    args = p.parse_args();a.require(not args.output.exists(),'fresh output directory required')
    original,card,packet,pool,receipt,binding = authenticate(args.candidate)
    domain=packet['demand_and_preservation_contract'];target=domain['targets']['signal']
    before_plan=json.loads((HERE/'route-1641/access-plan.json').read_text())['demands']['signal']
    groups,records,_=a.portals(original,target,pool['signal'],packet['budget'],domain['common_bounds_mm'])
    before=capture(original,before_plan['groups'],before_plan['records'],packet);after=capture(original,groups,records,packet)
    y,x=after['raster'].cell(*card['via_nm']);y0,_,x0,_=after['window'];seed=(after['raster'].layers.index('In2.Cu'),y-y0,x-x0)
    summary,masks=compare(before,after,seed);geometry=exact_region(original,card,packet,after,masks['new_seed_only'])
    all_rows={name:records[name] for group in groups for name in group}
    result={'status':'STOP THIS IN2-ONLY REPAIR; NO USEFUL FULL-ROUTE REACHABILITY',
        'diagnostic':'Graph components and exact transitions only; no router A*, native search, copper proposal or PCB apply',
        'candidate_source_binding_sha256':sha(args.candidate/'source-binding.json'),
        'input_dump_sha256':binding['input_dump_sha256'],'method_base_sha':binding['base_method_sha'],
        'source_sha256':{str(path.relative_to(a.ROOT)):sha(path) for path in (Path(__file__),HERE/'test_f3_breakout_region.py',COMPONENT_SOURCE)},
        'same_window_cells':before['window'],'same_free_via_goal_masks':True,'added_source_node':list(seed),
        'mask_sha256':{name:{key:hashlib.sha256(saved[key].tobytes()).hexdigest() for key in ('free','via','src','goal')} for name,saved in [('before',before),('after',after)]},
        'graph':summary,'new_seed_exact_geometry':{k:v for k,v in geometry.items() if k not in ('boundary','via_checks','owners')},
        'original_goal_portals':[all_rows[u] for u in groups[0]],'original_source_portals':[all_rows[u] for u in groups[1]],
        'negative_scope':'Current graph remains disconnected. Exact-clear raster-blocked exits exist; this is not physical impossibility. Reusing the attachment through-via on another layer would be a separately justified transition change, absent here.',
        'blocked_demands':'All four original demands retained. U2309 rails remain blocked by own adjacent pads; AGND unchanged.',
        'native_executed':False,'proposal_created':False,'adopted':False,'next_native_packet':'NOT CREATED; stop ineffective repair',
        'native_reservations':'All slots free; no admission'}
    a.require(not any(row['goal_nodes_reached'] for row in summary.values()),'positive reachability requires a different reviewed conclusion')
    args.output.mkdir(parents=True);(args.output/'region-proof.json').write_text(json.dumps(result,indent=2)+'\n')
    (args.output/'exact-boundary.json').write_text(json.dumps(geometry,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ('status','same_window_cells','graph','new_seed_exact_geometry','native_executed')}))


if __name__=='__main__':main()
