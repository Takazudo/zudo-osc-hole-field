#!/usr/bin/env python3
"""Source-only joined-interface and conditional resistance checks. Never runs KiCad."""
import argparse
from collections import Counter, defaultdict
import hashlib
import json
import math
from itertools import combinations
from pathlib import Path
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[4]
BASE = '9e0aceda2f1d55052a8c9c03f958e8d93271a81c'
MECHANICAL_SHA = 'b3d72e107c166e472ba6fe6476d34304e807b4ad'
POWER = 'design/partition/core-split/power/'
PREFIX = 'design/partition/core-split/'
INPUTS = [PREFIX + p for p in ('decision.json', 'contract.json', 'candidates/two.json',
    'candidates/three.json', 'candidates/interface-contract.json', 'mechanical/candidates.json',
    'mechanical/generated/comparison.json', 'mechanical/inputs/power-contract.json',
    'mechanical/inputs/power-input.json', 'power/input.json', 'power/contract.json',
    'power/harness-contract.json')] + ['design/partition/partition.json',
    'design/partition/partition-input.json', 'design/partition/harness-wire-evidence.json',
    'design/partition/sources/alpha-5859.pdf', 'design/partition/sources/alpha-6821.pdf',
    'scripts/checks/partition35.py', 'design/connectors/jst-gh.json', 'design/connectors/sources/jst-gh.pdf',
    'design/power/supply-architecture.json']
RAILS = ['+12V', '-12V', '+5V']


def require(ok, message):
    if not ok:
        raise ValueError(message)


def read(path):
    return json.loads((ROOT / path).read_text())


def sha(data):
    return hashlib.sha256(data).hexdigest()


def finite(x, positive=False):
    require(isinstance(x, (int, float)) and math.isfinite(x) and
            (x > 0 if positive else x >= 0), 'invalid resistance/current/length')
    return x


def effective_resistance(edges, a, b):
    """One ampere a->b, positive finite resistors; disconnected is infinity."""
    ids = [e['id'] for e in edges]
    require(len(ids) == len(set(ids)), 'duplicate conductor ID')
    adj = defaultdict(set)
    for e in edges:
        finite(e['r'], True)
        require(e['a'] != e['b'], 'self-loop or collapsed endpoints')
        adj[e['a']].add(e['b']); adj[e['b']].add(e['a'])
    seen, todo = {a}, [a]
    while todo:
        for n in adj[todo.pop()] - seen:
            seen.add(n); todo.append(n)
    if b not in seen:
        return math.inf
    if a == b:
        return 0.0
    nodes = sorted(seen - {b}); ix = {n:i for i,n in enumerate(nodes)}
    mat = [[0.0] * (len(nodes)+1) for _ in nodes]
    mat[ix[a]][-1] = 1.0
    for e in edges:
        if e['a'] not in seen:
            continue
        g = 1 / e['r']
        for u,v in [(e['a'],e['b']), (e['b'],e['a'])]:
            if u != b:
                mat[ix[u]][ix[u]] += g
                if v != b:
                    mat[ix[u]][ix[v]] -= g
    original = [row[:] for row in mat]
    for col in range(len(nodes)):
        pivot = max(range(col,len(nodes)), key=lambda k: abs(mat[k][col]))
        require(abs(mat[pivot][col]) > 1e-12, 'singular grounded conductance matrix')
        mat[col], mat[pivot] = mat[pivot], mat[col]
        divisor = mat[col][col]
        mat[col] = [v/divisor for v in mat[col]]
        for row in range(len(nodes)):
            if row != col:
                factor = mat[row][col]
                mat[row] = [v-factor*w for v,w in zip(mat[row],mat[col])]
    voltages = [row[-1] for row in mat]
    residual = max(abs(sum(row[i]*voltages[i] for i in range(len(nodes)))-row[-1]) for row in original)
    require(residual <= 1e-8, 'conductance solve KCL residual')
    result = mat[ix[a]][-1]
    require(math.isfinite(result) and result >= 0, 'invalid effective resistance solution')
    return result


def bound(current, minimum, alternative):
    finite(current); finite(minimum, True)
    require(alternative >= 0 and not math.isnan(alternative), 'invalid alternative resistance')
    return current if math.isinf(alternative) else current * alternative / (minimum + alternative)


def path_drop(rail_a, return_a, rail_lengths, return_lengths, d,
              rail_copper=None, return_copper=None):
    """Every serial wire section pays its ends; copper budget is charged once."""
    rail_copper = d['rail_plane_resistance_ceiling_ohm'] if rail_copper is None else finite(rail_copper)
    return_copper = d['return_plane_resistance_ceiling_ohm'] if return_copper is None else finite(return_copper)
    require(rail_copper <= d['rail_plane_resistance_ceiling_ohm'], 'rail copper budget duplicated')
    require(return_copper <= d['return_plane_resistance_ceiling_ohm'], 'AGND copper budget duplicated')
    for length in rail_lengths + return_lengths:
        finite(length, True)
        require(length <= d['max_wire_length_mm'], 'main cut exceeds unchanged ceiling')
    resistance = lambda lengths: sum(d['hot_resistance_requirement_ohm_per_m']*n/1000 +
                                     d['combined_termination_resistance_ohm'] for n in lengths)
    return 1000*(finite(rail_a)* (resistance(rail_lengths)+rail_copper) +
                 finite(return_a)*(resistance(return_lengths)+return_copper))


def matched_feed(feed):
    fid, boards = feed['id'], feed['boards']
    require(fid == 'CS247-'+'-'.join(boards), 'feed ID/board pair mismatch')
    require(boards[0] == 'KA' and len(set(boards)) == 2, 'feed must join KA to one satellite')
    ends = feed['endpoint_envelopes']
    require([e['board'] for e in ends] == boards, 'endpoint board mismatch')
    require([e['id'] for e in ends] == [fid+'-SRC',fid+'-DST'], 'endpoint ID mismatch')
    require([w['net'] for w in feed['wires']] == RAILS+['AGND']*3, 'feed pin order changed')
    result = []
    for pin,w in enumerate(feed['wires'],1):
        require(w['id'] == f'{fid}-W{pin}', 'missing/duplicate conductor identity')
        require(w['terminal_ids'] == [f'{fid}-SRC-{pin}',f'{fid}-DST-{pin}'], 'unmatched feed terminals')
        require(w['net'] != 'NC' and not w['net'].endswith('_IN'), 'NC/raw boundary wired')
        result.append({'id':w['id'], 'net':w['net'], 'wire_mpn':w['wire_mpn'],
            'ends':[{'id':t,'board':board,'pin':'1','native_ref':None}
                    for t,board in zip(w['terminal_ids'],boards)],
            'logical_pairing':'PASS', 'terminal_realization':'BLOCKED: no CS247 placement or native Ref',
            'local_copper_continuity':'NOT RUN', 'wire_realization':'NOT RUN',
            'end_to_end_continuity':'BLOCKED', 'electrical_qualification':'NOT RUN'})
    return result


def join_sources():
    power = read(POWER+'contract.json'); saved = read(POWER+'harness-contract.json')
    interface = read(PREFIX+'candidates/interface-contract.json')
    partition = read('design/partition/partition.json')
    require(interface['harnesses'] == partition['harnesses'] and
            interface['endpoints'] == partition['connectors'], 'legacy registry changed')
    require(len(interface['harnesses']) == 195 and len(interface['endpoints']) == 390,
            'legacy interface count changed')
    require(interface['source_load_lands'] == partition['load_side_terminals'], 'old main land registry mismatch')
    require(power['existing_main_wires']==partition['load_side_wires'], 'power/main wire registry mismatch')
    endpoints = {e['id']:e for e in interface['endpoints']}
    require(len(endpoints) == 390, 'duplicate legacy endpoint')
    owner = {h['id']:h['core_owner'] for h in saved['harnesses']}
    for h in saved['harnesses']:
        for end in h['endpoints']:
            require(all(end[k] == endpoints[end['id']][k] for k in end if k != 'pose_policy'),
                    'power/candidate endpoint mismatch '+end['id'])
    for name in ['input','contract']:
        require((ROOT/(POWER+name+'.json')).read_bytes() ==
                (ROOT/(PREFIX+'mechanical/inputs/power-'+name+'.json')).read_bytes(),
                'stale mechanical power copy '+name)
    out = {}
    for option in ['two','three']:
        candidate = read(PREFIX+'candidates/'+option+'.json')
        aliases = {b:'K'+b.rsplit('-',1)[1] for b in candidate['boards']}
        placed = {aliases[b]:{p['ref'] for p in v['placements']} for b,v in candidate['boards'].items()}
        core_ids = [e['id'] for v in candidate['boards'].values() for e in v['core_endpoints']]
        require(Counter(core_ids) == Counter(e['id'] for e in interface['endpoints'] if e['board']=='K'), 'missing/duplicate core endpoints')
        for b,v in candidate['boards'].items():
            for end in v['core_endpoints']:
                require(end == endpoints[end['id']], 'candidate endpoint identity/pin/pose drift')
                hid = next(h['id'] for h in interface['harnesses'] if end['id'] in h['header_ids'])
                require(owner[hid][option] == aliases[b], 'candidate/power owner mismatch')
        conductors = []
        for h in interface['harnesses']:
            ends = [endpoints[e] for e in h['header_ids']]
            require(len(ends) == 2 and ends[0]['pin_map'] == ends[1]['pin_map'], 'unmatched GH pin map')
            for pin,net in ends[0]['pin_map'].items():
                conductors.append({'id':h['id']+':'+pin, 'net':net,
                    'wired':net != 'NC',
                    'ends':[{'id':e['id'], 'ref':e['pcb_reference'], 'pin':pin,
                             'board':owner[h['id']][option] if e['board']=='K' else e['board']}
                            for e in ends]})
        expected_feeds = {f'CS247-KA-{b}' for b in placed if b!='KA'}
        feed_defs = power['options'][option]['new_feeds']
        require(Counter(f['id'] for f in feed_defs) == Counter(expected_feeds), 'missing/duplicate feed')
        feeds = [wire for feed in feed_defs for wire in matched_feed(feed)]
        require(len({w['id'] for w in feeds}) == 6*len(expected_feeds), 'new wire identity count')
        require(len({e['id'] for w in feeds for e in w['ends']}) == 12*len(expected_feeds), 'new terminal identity count')
        require(not any(ref.startswith('CS247') for refs in placed.values() for ref in refs),
                'new terminal implementation appeared: reconcile native identities before admitting it')
        old_lands = {b:sorted(ref for ref in refs if ref.startswith('TP990')) for b,refs in placed.items()}
        expected_lands = sorted(t['reference'] for t in interface['source_load_lands'] if t['board']=='K')
        require(old_lands['KA'] == expected_lands and all(not refs for b,refs in old_lands.items() if b!='KA'),
                'existing main-land ownership changed')
        lands = {t['reference']:t for t in interface['source_load_lands']}
        main_conductors = []
        for wire in partition['load_side_wires']:
            ts = [lands[r] for r in wire['terminal_refs']]
            require(len(ts)==2 and all(t['net']==wire['net'] for t in ts), 'main wire net/endpoint mismatch')
            require(len({t['board'] for t in ts})==2, 'main wire does not cross boards')
            main_conductors.append({'id':wire['id'],'net':wire['net'],'wire_mpn':wire['wire_mpn'],
                'ends':[{'ref':t['reference'],'pin':t['manufacturer_pin'],
                         'board':'KA' if t['board']=='K' else t['board']} for t in ts],
                'logical_pairing':'PASS','physical_continuity':'NOT RUN; source mapping only'})
        out[option] = {'existing_main_conductors':main_conductors, 'aliases':aliases, 'legacy_conductors':conductors, 'new_conductors':feeds,
            'old_main_lands':old_lands, 'new_native_terminal_count':0,
            'copied_net_owners':{n:candidate['net_owners'][n] for n in RAILS+['AGND']},
            'feed_realization':'BLOCKED: same rail names do not join boards; no CS247 pads exist',
            'reservation_disposition':'BLOCKED: #245 retains per-board protection holdout; #247/#246 specify KA-only protection plus satellite monitor'}
    return out, owner


def network(alternative, joined, owner, d, gh):
    option = alternative['partition']
    routes = {r['id']:r for r in alternative['harnesses']}
    require(len(routes)==len(alternative['harnesses'])==195, 'missing/duplicate mechanical GH route')
    require(all(not r.get('core_board') or r['core_board']==owner[r['id']][option]
                for r in routes.values()), 'mechanical/power core owner mismatch')
    edges = []
    for c in joined[option]['legacy_conductors']:
        if c['net'] != 'AGND':
            continue
        hid = c['id'].rsplit(':',1)[0]; route = routes[hid]
        lo,hi = route['centreline_length_mm'],route['cut_length_mm']
        require(finite(lo,True) <= finite(hi,True), 'invalid cable length interval')
        edges.append({'id':c['id'], 'kind':'GH', 'a':c['ends'][0]['board'], 'b':c['ends'][1]['board'],
            'r':hi/1000*gh['wire_hot_resistance_ceiling_ohm_per_m']+.1,
            'minimum_r':lo/1000*gh['wire_minimum_resistance_for_parallel_path_bounds_ohm_per_m'],
            'length_lower_mm':lo,'cut_requirement_mm':hi})
    p = read('design/partition/partition.json')
    lands = {t['reference']:t for t in p['load_side_terminals']}
    rmax = d['hot_resistance_requirement_ohm_per_m']*d['max_wire_length_mm']/1000+d['combined_termination_resistance_ohm']
    for w in p['load_side_wires']:
        if w['net']=='AGND':
            nodes = ['KA' if lands[r]['board']=='K' else lands[r]['board'] for r in w['terminal_refs']]
            edges.append({'id':w['id'], 'kind':'main', 'a':nodes[0], 'b':nodes[1], 'r':rmax})
    for w in joined[option]['new_conductors']:
        if w['net']=='AGND':
            edges.append({'id':w['id'], 'kind':'main', 'a':w['ends'][0]['board'], 'b':w['ends'][1]['board'], 'r':rmax})
    require(sum(e['kind']=='GH' for e in edges)==380, 'return conductor inventory changed')
    return edges


def return_scenarios(edges, d, gh):
    main = [e for e in edges if e['kind']=='main']
    scenarios = [('all-present',[])] + [('remove:'+e['id'],[e['id']]) for e in main]
    branches = defaultdict(list)
    for e in main:
        other = e['b'] if e['a']=='KA' else e['a']; branches[other].append(e['id'])
    scenarios += [('remove-two:'+b+':'+str(i),list(pair)) for b,ids in sorted(branches.items()) for i,pair in enumerate(combinations(ids,2),1)]
    scenarios += [('remove-all:'+b,ids) for b,ids in sorted(branches.items())]
    results = []
    for sid,removed in scenarios:
        remaining = [e for e in edges if e['id'] not in removed]
        checks,cache = [],{}
        for e in remaining:
            if e['kind']!='GH':
                continue
            key = (tuple(sorted([e['a'],e['b']])), e['r'])
            if key not in cache:
                cache[key] = effective_resistance([x for x in remaining if x['id']!=e['id']], e['a'], e['b'])
            altwire = cache[key]
            alt = altwire + d['return_plane_resistance_ceiling_ohm']
            amps = bound(d['single_return_max_A'], e['minimum_r'], alt)
            allowed = gh['branch_current_derating_A'] * e['minimum_r'] / (d['single_return_max_A']-gh['branch_current_derating_A'])
            role = 'EL' if 'EL' in [e['a'],e['b']] else 'passive-octave' if any(n.startswith('O') for n in [e['a'],e['b']]) else 'powered-core/front'
            checks.append({'id':e['id'], 'role':role, 'upper_current_A':amps,
                'wire_only_alternative_ohm':None if math.isinf(altwire) else altwire,
                'remaining_total_access_budget_ohm':None if math.isinf(altwire) else allowed-altwire,
                'bound_pass':amps <= gh['branch_current_derating_A']})
        worst = max(checks,key=lambda c:c['upper_current_A'])
        # Full 4.6 A arbitrary-injection class deliberately overbounds EL/passive boards.
        # No invented port-current distribution rescues a failed class bound.
        groups = {role:{'count':sum(c['role']==role for c in checks),
            'exceedance_count':sum(c['role']==role and not c['bound_pass'] for c in checks),
            'worst':max((c for c in checks if c['role']==role),key=lambda c:c['upper_current_A'])}
            for role in sorted({c['role'] for c in checks})}
        results.append({'role_groups':groups, 'id':sid, 'removed':removed,'worst':worst,
            'bound_exceedance_count':sum(not c['bound_pass'] for c in checks),
            'minimum_access_reserve_ohm':min((c['remaining_total_access_budget_ohm'] for c in checks if c['remaining_total_access_budget_ohm'] is not None),default=None),
            'conditional_bound':'PASS' if all(c['bound_pass'] for c in checks) else 'BLOCKED: insufficient bound, not measured overload',
            'fault_eligibility':'NORMAL CONDITIONAL ONLY' if not removed else 'BLOCKED: no admitted return-fault protection',
            'per_conductor':checks if not removed else None})
    return results


def budgets(d):
    results = {}
    for rail,amps in d['rail_max_A'].items():
        one = path_drop(amps,d['single_return_max_A'],[110],[110],d)
        two = path_drop(amps,d['single_return_max_A'],[110,110],[110,110],d)
        total_two_cut = 1000*(.020-amps*d['rail_plane_resistance_ceiling_ohm']-
            d['single_return_max_A']*d['return_plane_resistance_ceiling_ohm']-
            (amps+d['single_return_max_A'])*2*d['combined_termination_resistance_ohm']) / (
            (amps+d['single_return_max_A'])*d['hot_resistance_requirement_ohm_per_m'])
        results[rail] = {'direct_star_drop_mV':one,'direct_margin_mV':20-one,
            'two_serial_sections_with_global_copper_once_mV':two,
            'two_serial_budget_pass':two<=20,
            'two_section_total_cut_limit_for_both_rail_and_return_mm':total_two_cut}
    return results



def mechanical_followup():
    """Consume the coordinator-pinned independent lane without applying its files."""
    path = PREFIX+'mechanical/generated/two-core-feasibility.json'
    blob = subprocess.check_output(['git','show',MECHANICAL_SHA+':'+path],cwd=ROOT)
    data = json.loads(blob)
    require(data['input_sha']==BASE, 'mechanical follow-up has a different baseline')
    for source,expected in data['source_sha256'].items():
        require(sha((ROOT/source).read_bytes())==expected, 'mechanical follow-up source changed: '+source)
    tool = PREFIX+'mechanical/feasibility.py'
    require(sha(subprocess.check_output(['git','show',MECHANICAL_SHA+':'+tool],cwd=ROOT))==data['tool_sha256'], 'mechanical tool hash mismatch')
    counts = {b:{str(r['rotation_deg']):len(r['continuous_translation_screen']['feasible_event_origins_mm'])
                 for r in rows} for b,rows in data['endpoint_placement_search'].items()}
    require(counts['two-A']=={'0':0,'90':0}, 'new KA feasibility needs review')
    return {'commit':MECHANICAL_SHA,'path':path,'sha256':sha(blob),
        'tool_sha256':data['tool_sha256'],'source_reconciliation':'PASS exact current input bytes',
        'cardinal_origin_counts':counts,'cardinal_edge_escape':data['cardinal_edge_escape'],
        'stack_options':data['stack_options'],
        'service_wire_boundary':data['service_wire_boundary'],
        'strict_gap_proposals':{'count':data['strict_gap_summary']['count'],'applied':False},
        'power_disposition':'BLOCK unchanged indivisible91x34 row/corridor: zero KA cardinal origins under retained masks. 34.6mm pitch solves Z only at zero margin. No paired feed geometry or service path admitted.',
        'next_contract':'An evidenced segmented/reshaped swept envelope or service lifecycle may be proposed by its owner, retaining six exact W1..W6 identities/nets, 4x4 lands/5x5 courtyards/6x6 reserves, >=25.908mm wire bend, <=110mm full cut, strain relief and all tool/support/copper obligations. Neither unused row space nor soldering/service clearance may be discarded without evidence. No such change is adopted here.'}


def build():
    locked = {}
    for p in INPUTS:
        current = (ROOT/p).read_bytes()
        pinned = subprocess.check_output(['git','show',BASE+':'+p],cwd=ROOT)
        require(current==pinned,'input differs from reviewed integration: '+p)
        locked[p]=sha(current)
    followup = mechanical_followup()
    joined,owner = join_sources()
    d=read('design/partition/partition-input.json')['load_distribution']
    gh=read('design/partition/harness-wire-evidence.json')['proposal']
    mechanics=read(PREFIX+'mechanical/generated/comparison.json')
    alternatives=[]
    for a in mechanics['alternatives']:
        edges=network(a,joined,owner,d,gh)
        scenarios=return_scenarios(edges,d,gh)
        alternatives.append({'id':a['id'],'partition':a['partition'],
            'edges':edges,'scenarios':scenarios,
            'endpoint_clearance_screens':a['power_reconciliation']['endpoint_clearance_screens'],
            'existing_main_cut_necessary_bounds':a['power_bounds'],
            'geometry_admission':'BLOCKED: unplaced CS247 origins/rotations; branch/service cuts and obstacles unproved',
            'realized_end_to_end_connectivity':'BLOCKED: no new terminal/copper/wire implementation'})
    report={'schema':'cs247-joined-budget-1','base_sha':BASE,'source_sha256':locked,
        'status':'REPRODUCIBLE SOURCE SCREEN; ARCHITECTURE BLOCKED; KEEP_K1402',
        'method':{
            'nodes':'Board return names are CONDITIONAL lumped comparators, never native connected components. All source networks remain unimplemented/unqualified.',
            'injection_class':'Balanced signed injections, sum positive = sum negative magnitudes <=4.6 A; no equal sharing or rail cancellation. Whole-domain class deliberately conservative for EL/O boards.',
            'current_formula':'I_bound = 4.6 * R_alt / (R_min + R_alt); remove candidate, all other wire/contact paths at maxima; candidate cold cable resistance minimum, candidate contact/access minimum zero.',
            'proof':'Reciprocity plus passive maximum principle bounds transfer voltage by effective resistance times total injection. Rayleigh monotonicity bounds alternative resistance. Open alternate path gives 4.6 A, never zero.',
            'access_model':'Add ONE 0.5 mOhm total omitted copper/access inventory bound to wire-only R_alt. Sufficient but stronger than original path requirement: sum of every distinct unmodeled neck/access resistor upper bound in expanded graph <=0.5mOhm. This additionally requires complete connected access subgraphs joining ALL collapsed terminals so every ideal unit flow can be lifted. Disconnected copper cannot qualify at any resistance. Unit-flow energy gives R_alt <= R_wire + sum(R_access). No per-board allowance, zero-access claim, shared-neck omission or parallel-layer credit. Extraction/equivalence NOT RUN; actual feasible allocation unknown.',
            'uncertainty':'Wire hot/cold and contact limits are assembled acceptance requirements, not measurements or manufacturer guarantees. .1 ohm GH alternative allowance is retained two-end contact/crimp requirement. Continuous/cut lengths from mechanical proposals only.',
            'excluded':'Stored capacitor energy, arbitrary external patch injection, missing/late rails, unbounded fault currents and protection dynamics. No patch-sleeve edge is credited.',
            'bound_failure':'A bound above0.5 A blocks this conservative certificate, not proof of actual overload; refined source-supported injections/access graph may tighten it without relaxing limits.'},
        'limits':{'distribution_mV':20,'rail_copper_ohm':.001,'return_copper_ohm':.0005,
            'GH_A':.5,'whole_return_A':4.6,'main_cut_mm':110,
            'EL_rail_mA':read('design/partition/partition.json')['power']['EL_rail_current_contract_mA'],
            'EL_return_mA':170},
        'mechanical_followup':followup,
        'voltage_budget':budgets(d),'alternatives':alternatives,
        'pass_block_criteria':{
            'logical_interface':'Exact matching owner/net/pin at both distinct ends; no NC/raw bridge; all195 harnesses/390 endpoints frozen.',
            'realized_continuity':'BLOCK until each proposed terminal has exact Ref/pad/UUID, all source/load pads join the intended native local components, every cross-board wire has matched ends and complete end-to-end rail/AGND graph connects to load-side star. Copied net names or zone islands do not count.',
            'normal_electrical':'Every admitted GH bound <=0.5A; all source-to-load loops <=20mV; all actual rail/access budgets <=1mOhm/0.5mOhm globally; caps/startup/protection allocations unchanged. Conditional arithmetic alone cannot PASS installed network.',
            'service':'Both end transforms, obstacle-cleared 28mm corridors or reviewed edge/aperture disposition, every bent cut+slack/preparation <=110mm, supported factory-connected service travel, bend radius>=25.908mm. Unplaced/unknown blocks; deeper translation alone cannot erase3.6mm deficit.',
            'faults':'Missing-return numerical re-solves do not admit service; missing/late rails, power-off injection, all-rail shutdown/reverse blocking/return-integrity remain BLOCKED#59; source/hot/fit tests#57/#65 NOT RUN.',
            'native':'NOT RUN / NOT ADMITTED; no architecture selection or canonical adoption'}}
    return {'interfaces.json':joined,'budget.json':report}


def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--check',action='store_true')
    args=parser.parse_args();outputs=build()
    manifest={'base_sha':BASE,'tool_sha256':sha(Path(__file__).read_bytes()),'test_sha256':sha((HERE/'test_joined.py').read_bytes()),'outputs':{}}
    for name,data in outputs.items():
        text=json.dumps(data,indent=2,allow_nan=False)+'\n';manifest['outputs'][name]=sha(text.encode())
        if args.check:require((HERE/name).read_text()==text,'generated drift: '+name)
        else:(HERE/name).write_text(text)
    text=json.dumps(manifest,indent=2)+'\n'
    if args.check:require((HERE/'manifest.json').read_text()==text,'manifest drift')
    else:(HERE/'manifest.json').write_text(text)
    print('PASS source consistency: joined interfaces and budget reproduced. Architecture/continuity/physical gates BLOCKED; native NOT RUN.')


if __name__=='__main__':
    main()
