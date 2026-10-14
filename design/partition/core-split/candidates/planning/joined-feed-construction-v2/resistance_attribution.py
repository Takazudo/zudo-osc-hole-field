#!/usr/bin/env python3
"""Bounded E16 solution accounting, not a solver or a production artifact loader.

The CLI consumes JSON only. Extracting real solution detail, even from retained
pickles, needs separate diagnostic admission. Union sheet tiles own overlapping
copper once; their member identities are provenance, not additive object shares.
"""
import argparse
import hashlib
import json
import math
from pathlib import Path

import numpy as np
import scipy.sparse as sp

import finite_adapter as adapter
from finite_solve import _extended_residual

HERE = Path(__file__).resolve().parent
CONFIG = HERE / 'evidence/e16/continuation-20261013b/coupled-network-config.json'
MAX_JSON_BYTES = 16 * 1024**2


def need(ok, message):
    if not ok:
        raise ValueError(message)


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, separators=(',', ':'),
                                     allow_nan=False).encode()).hexdigest()


def matrix_record(matrix):
    matrix = matrix.tocsr(copy=True)
    matrix.sum_duplicates()
    matrix.eliminate_zeros()
    matrix.sort_indices()
    return {'n': matrix.shape[0], 'row': matrix.tocoo().row.tolist(),
            'col': matrix.tocoo().col.tolist(), 'siemens': matrix.data.tolist()}


def matrix_read(record):
    n = record['n']
    need(type(n) is int and 0 < n < 2**31, 'invalid matrix order')
    row, col, val = record['row'], record['col'], record['siemens']
    need(len(row) == len(col) == len(val), 'matrix triplet lengths differ')
    need(all(type(i) is int and 0 <= i < n for i in row + col), 'invalid matrix index')
    need(all(type(v) in (int, float) and math.isfinite(v) for v in val), 'nonfinite matrix')
    return sp.csr_matrix((val, (row, col)), shape=(n, n))


def rank_one(n, nodes, weights, resistance_ohm):
    """Same distributed w w'/R stamp used by finite_solve. No solve."""
    need(math.isfinite(resistance_ohm) and resistance_ohm > 0, 'invalid resistance')
    need(len(nodes) == len(weights) and 0 < len(nodes) <= 256, 'unbounded or invalid interface support')
    need(all(type(i) is int and 0 <= i < n for i in nodes), 'invalid interface nodes')
    need(all(math.isfinite(w) for w in weights) and abs(sum(weights)) <= 1e-9, 'invalid interface weights')
    v = np.zeros(n)
    np.add.at(v, nodes, weights)
    nz = np.flatnonzero(v)
    return sp.csr_matrix((np.outer(v[nz], v[nz]).ravel() / resistance_ohm,
                          (np.repeat(nz, len(nz)), np.tile(nz, len(nz)))), shape=(n, n))


def copper_components(assembly, items, case, depth, board, net):
    """In-memory adapter for existing Assembly and its ORIGINAL mesh items.

    Does not mesh, factor, solve or open artifacts. Running on real retained
    meshes is part of a separately bounded diagnostic, never test discovery.
    Sheet/member overlap is owned by each union tile exactly once. Individual
    pad/track/spreading shares inside a union are intentionally unsupported.
    """
    lookup = {(int(g), *np.rint(xy * adapter.SCALE).astype(np.int64)):
              int(node) for g, xy, node in zip(assembly.group, assembly.xy, assembly.vertex_node)}
    groups = {g['group']: g for g in assembly.desc['groups']}
    components = []
    for index, item in enumerate(items):
        group = groups[item['group']]
        nodes = np.array([lookup[(item['group'], *xy)]
                          for xy in np.rint(item['xy'] * adapter.SCALE).astype(np.int64)])
        thickness = case['outer_copper_mm'] if group['layer'] in adapter.FACES else case['inner_copper_mm']
        matrix = sp.csr_matrix((item['val'] * thickness / case['rho_ohm_mm'],
                               (nodes[item['row']], nodes[item['col']])),
                              shape=(assembly.N, assembly.N))
        components.append({'id': f'{board}:sheet:{index}', 'kind': 'sheet_union',
                           'board': board, 'net': net, 'object_ids': sorted(group['fragments']),
                           'layer_interval': [group['layer']],
                           'region': {'group': item['group'], 'tile_mm': item['tile']},
                           'matrix': matrix_record(matrix)})
    _, _, records = assembly.matrix(case, depth)
    for identity, lower, upper, length, resistance in records:
        nodes = [int(assembly.rings[identity, lower]), int(assembly.rings[identity, upper])]
        components.append({'id': f'{board}:barrel:{identity}:{lower}:{upper}',
                           'kind': 'barrel', 'board': board, 'net': net,
                           'object_ids': [identity], 'layer_interval': [lower, upper],
                           'region': {'length_mm': length}, 'branch': {'nodes': nodes, 'weights': [1., -1.],
                                                                    'resistance_ohm': resistance},
                           'matrix': matrix_record(rank_one(assembly.N, nodes, [1., -1.], resistance))})
    return components


def interface_components(operators, config, net, removed_wires=()):
    """Existing terminal_stamps convention on [KA mesh/terms | KB mesh/terms].

    Return interface components and board offsets; copper matrices must be
    embedded at these offsets by the admitted extractor. No reconstruction.
    """
    from finite_solve import terminal_stamps, wire_of
    need(set(operators) == {'KA', 'KB'}, 'both board operators required')
    descriptions = {b: terminal_stamps(operators[b], config) for b in ('KA','KB')}
    offsets = {'KA': 0, 'KB': operators['KA']['N'] + len(descriptions['KA'][0])}
    n = offsets['KB'] + operators['KB']['N'] + len(descriptions['KB'][0])
    components, terminals = [], {}
    for board in ('KA','KB'):
        terms, resistance, supports = descriptions[board]
        terminals[board] = {}
        for k, (identity, (nodes, weights)) in enumerate(zip(terms, supports)):
            terminal = offsets[board] + operators[board]['N'] + k
            terminals[board][wire_of(identity)] = terminal
            ns = [offsets[board] + int(i) for i in nodes] + [terminal]
            ws = list(map(float, weights)) + [-1.]
            need(abs(sum(ws)) <= 1e-9, 'termination support is not normalized')
            components.append({'id': identity + ':termination', 'kind': 'termination',
                'board': board, 'net': net, 'object_ids': [identity],
                'layer_interval': ['pad-support', 'terminal'], 'region': {'support': identity},
                'branch': {'nodes': ns, 'weights': ws, 'resistance_ohm': resistance},
                'matrix': matrix_record(rank_one(n, ns, ws, resistance))})
    need(set(terminals['KA']) == set(terminals['KB']), 'terminal identity sets differ')
    need(set(removed_wires) <= set(terminals['KA']), 'unknown removed wire')
    for wire, a in terminals['KA'].items():
        need(config['wires']['pairs']['W'+str(wire)] == net, 'wire net differs')
        if wire in removed_wires:
            continue
        ns, ws = [a, terminals['KB'][wire]], [1., -1.]
        resistance = config['wires']['bulk_ohm']
        components.append({'id': f'W{wire}:bulk', 'kind': 'wire_bulk', 'board': 'KA-KB',
            'net': net, 'object_ids': [f'W{wire}'], 'layer_interval': ['KA-terminal', 'KB-terminal'],
            'region': {'wire': wire}, 'branch': {'nodes': ns, 'weights': ws, 'resistance_ohm': resistance},
            'matrix': matrix_record(rank_one(n, ns, ws, resistance))})
    return components, offsets


def bindings(packet):
    """Expected values must be pinned independently; this is NOT an attestation."""
    return {key: digest(packet[key]) for key in
            ('identity', 'network', 'components', 'solution', 'scope', 'provenance')}


def _vector(values, n, name):
    # Decimal strings preserve retained long-double potentials through JSON.
    need(isinstance(values, list) and len(values) == n, 'missing solution detail: ' + name)
    need(all(type(v) in (str, int, float) for v in values), 'invalid vector: ' + name)
    x = np.array(values, dtype=np.longdouble)
    need(np.isfinite(x).all(), 'nonfinite ' + name)
    return x


def _nonempty(value, name):
    need(isinstance(value, str) and bool(value.strip()), 'missing identity: ' + name)


def _max(x):
    return float(np.max(np.abs(x))) if len(x) else 0.


def attribute(packet, expected):
    """Validate and attribute an already computed solution; always non-accepting."""
    out = {'schema': 'e16-resistance-attribution-v1', 'status': 'BLOCKED',
           'whole_board_acceptance': False, 'electrical_acceptance': False,
           'adopted': False, 'failures': [], 'components': []}
    try:
        return _attribute(packet, expected, out)
    except (ValueError, KeyError, TypeError, IndexError, OverflowError) as exc:
        out['failures'].append(str(exc))
        return out


def _attribute(packet, expected, out):
    need(packet['schema'] == 'e16-attribution-detail-v1', 'unsupported detail schema')
    need(bindings(packet) == expected, 'stale/mismatched content hashes')
    ident = packet['identity']
    for key in ('board', 'net', 'ref', 'pin', 'pad_uuid', 'process_case', 'depth_case', 'return_state'):
        _nonempty(ident[key], key)
    need(ident['net'] in ('+12V', '-12V', '+5V', 'AGND'), 'unsupported net')
    out['identity'] = ident
    out['input_bindings'] = expected
    out['provenance'] = packet['provenance']
    for key in ('source_sha256', 'operator_sha256', 'extractor_sha256', 'config_sha256'):
        h = packet['provenance'][key]
        need(isinstance(h, str) and len(h) == 64 and set(h) <= set('0123456789abcdef')
             and h != '0' * 64, 'missing/invalid provenance: ' + key)
    need(packet['provenance']['quantity_origin'] in ('synthetic', 'retained_solution'), 'unknown quantity origin')
    cfg = json.loads(CONFIG.read_text())
    need(packet['provenance']['config_sha256'] == hashlib.sha256(CONFIG.read_bytes()).hexdigest(),
         'stale configuration hash')
    tol = cfg['numerical_tolerances']
    out['tolerances'] = tol
    out['tool_sha256'] = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                          for p in (Path(__file__), HERE/'finite_adapter.py', HERE/'finite_solve.py')}
    need(not (ident['net'] == 'AGND' and ident['return_state'] == 'all-three-open'),
         'STRUCTURALLY_FLOATING_AGND_ALL_THREE_OPEN')
    scope = packet['scope']
    need(scope['complete_modeled_network'] is True and scope['omitted_components'] == [],
         'incomplete modeled scope')
    need(isinstance(scope['physical_omissions'], list), 'physical omissions must be explicit')
    out['scope'] = scope
    K = matrix_read(packet['network']['matrix'])
    n = K.shape[0]
    v = _vector(packet['solution']['potential_V'], n, 'potential_V')
    f = _vector(packet['solution']['injection_A'], n, 'injection_A')
    source = ident['source_support']
    need(source['mode'] == 'equipotential_patches' and source['potential_V'] == 0,
         'only original zero-referenced equipotential supports supported')
    need(source['pads'], 'missing source supports')
    source_ids = [p['pad_uuid'] for p in source['pads']]
    need(len(source_ids) == len(set(source_ids)), 'duplicate source pad identity')
    fixed = set()
    for p in source['pads']:
        for key in ('ref', 'pin', 'pad_uuid', 'board'):
            _nonempty(p[key], key)
        need(p['nodes'] and len(p['nodes']) == len(set(p['nodes'])) and all(type(i) is int and 0 <= i < n for i in p['nodes']), 'invalid/duplicate held nodes')
        need(not fixed.intersection(p['nodes']), 'ambiguous shared source support nodes')
        fixed.update(p['nodes'])
    fixed = sorted(fixed)
    free = np.array([i for i in range(n) if i not in set(fixed)], dtype=int)
    need(len(free) > 0 and np.all(v[fixed] == 0) and np.all(f[fixed] == 0),
         'source reference differs or load injected on held support')
    # Every modeled component must reach a fixed source; no silent island dropping.
    _, labels = sp.csgraph.connected_components(K, directed=False)
    need(set(labels) <= set(labels[fixed]), 'singular/floating modeled component')
    if len(free) <= 256:
        dense = K[free][:,free].toarray()
        need(np.allclose(dense, dense.T, rtol=0, atol=0), 'nonreciprocal free operator')
        eigenvalues = np.linalg.eigvalsh(dense)
        floor = np.finfo(float).eps * len(free) * max(_max(eigenvalues), 1e-300)
        need(eigenvalues[0] > floor, 'singular/nonpassive or unresolved tiny free operator')
        out['uniqueness'] = 'CHECKED_TINY_POSITIVE_DEFINITE_FREE_OPERATOR'
    else:
        proof = packet['solution'].get('uniqueness_evidence', {})
        need(proof.get('network_sha256') == digest(packet['network']) and
             proof.get('held_nodes_sha256') == digest(fixed) and
             proof.get('return_state') == ident['return_state'] and
             proof.get('status') == 'POSITIVE_DEFINITE_FREE_OPERATOR' and
             proof.get('receipt_sha256') == packet['provenance'].get('uniqueness_receipt_sha256') and
             isinstance(proof.get('receipt_sha256'),str) and len(proof['receipt_sha256']) == 64 and
             set(proof['receipt_sha256']) <= set('0123456789abcdef') and proof['receipt_sha256'] != '0'*64 and
             bool(proof.get('method')), 'UNIQUENESS_NOT_VERIFIED: bound external positive-definiteness receipt required')
        out['uniqueness'] = 'EXTERNAL_RECEIPT_BOUND_NOT_RECOMPUTED'
    normalization = packet['solution']['normalization']
    mode = normalization['mode']
    need(mode in ('unit_current', 'simultaneous_load'), 'unknown normalization')
    current = normalization.get('current_A')
    if mode == 'unit_current':
        need(type(current) in (float, int) and math.isfinite(current) and current != 0, 'invalid current normalization')
        need(ident['pad_uuid'] not in source_ids, 'observation identity is a held source pad')
        need(math.isfinite(current*current) and current*current > 0, 'unsupported current normalization scale')
        support = ident['observation_support']
        nodes, weights = support['nodes'], support['weights']
        need(len(nodes) == len(weights) > 0 and len(nodes) == len(set(nodes)), 'missing/duplicate observation support')
        need(all(type(i) is int and 0 <= i < n and i not in fixed for i in nodes), 'observation touches held source or invalid node')
        need(all(type(w) in (float, int) and math.isfinite(w) and w >= 0 for w in weights)
             and abs(sum(weights) - 1) <= tol['support_weight_sum'], 'invalid support normalization')
        rhs = np.zeros(n, dtype=np.longdouble)
        rhs[nodes] = np.array(weights, dtype=np.longdouble) * current
        need(_max(f-rhs) / abs(current) <= tol['kcl_relative'], 'unit-current RHS differs from selected pad')
    else:
        need(current is None, 'simultaneous-load energy cannot be normalized as driving-point R')
    if packet['provenance']['quantity_origin'] == 'retained_solution':
        configured = cfg['source_support']
        need(source['board'] == configured['board'], 'source board differs from retained configuration')
        need({(p['ref'],p['pad_uuid'],p['board']) for p in source['pads']} ==
             {(p['ref'],p['pad_id'],configured['board']) for p in configured['pads'][ident['net']]},
             'source identities differ from retained configuration')
        need(ident['depth_case'] in cfg['depth_cases'], 'unknown depth case')
        cases = json.loads((HERE/'evidence/e16/process-cases.json').read_text())['cases']
        need(ident['process_case'] in cases, 'unknown process case')
        allowed = {'all-present'}
        if ident['net'] == 'AGND':
            allowed.update('remove-'+'-'.join('W'+str(w) for w in removed)
                           for group in ('single','double') for removed in cfg['return_states'][group])
        need(ident['return_state'] in allowed, 'unknown return state')
        removed = set() if ident['return_state'] == 'all-present' else {int(w[1:]) for w in ident['return_state'][7:].split('-')}
        wires = {int(w[1:]) for w,net in cfg['wires']['pairs'].items() if net == ident['net']}
        bulk = [c for c in packet['components'] if c['kind'] == 'wire_bulk']
        terms = [c for c in packet['components'] if c['kind'] == 'termination']
        need(sorted(c['object_ids'] for c in bulk) == sorted([[f'W{w}'] for w in wires-removed]),
             'live wire scope differs from configured return state')
        need(sorted((c['board'],c['object_ids']) for c in terms) ==
             sorted((b,[f'CS247-{b}-W{w}']) for b in ('KA','KB') for w in wires),
             'termination scope differs from configured interfaces')
    need(_max(f) > 0, 'zero excitation has no resistance attribution')
    ids = [c['id'] for c in packet['components']]
    need(ids and len(ids) == len(set(ids)) and sorted(ids) == sorted(scope['expected_component_ids']),
         'missing or duplicate component ownership')
    assembled = sp.csr_matrix(K.shape)
    energy = np.longdouble(0)
    contributions = []
    ownership = set()
    class_energy = {}
    for c in packet['components']:
        need(c['kind'] in ('sheet_union', 'barrel', 'termination', 'wire_bulk'), 'unsupported mapping kind')
        for key in ('id', 'board', 'net'):
            _nonempty(c[key], key)
        need(c['net'] == ident['net'], 'component net mismatch')
        need(c['object_ids'] and all(isinstance(i, str) and i for i in c['object_ids']), 'missing physical identities')
        need(c['layer_interval'] and c['region'] is not None, 'missing layer/interval/region')
        physical_key = (c['board'], c['kind'], tuple(sorted(c['object_ids'])),
                        tuple(c['layer_interval']), digest(c['region']) if c['kind'] == 'sheet_union' else None)
        need(physical_key not in ownership, 'duplicate physical interval/interface/union tile')
        ownership.add(physical_key)
        M = matrix_read(c['matrix'])
        need(M.shape == K.shape, 'component matrix order mismatch')
        scale = max(_max(M.data), 1e-30)
        need(_max((M-M.T).data) / scale <= tol['reciprocity_relative'], 'nonreciprocal component')
        need(_max(np.asarray(M.sum(axis=1)).ravel()) / scale <= tol['kcl_relative'], 'component does not conserve current')
        assembled += M
        inj = -_extended_residual(M, v, np.zeros(n))
        e = np.dot(v, inj.astype(np.longdouble))
        need(np.isfinite(e) and e >= 0, 'nonfinite/negative component energy')
        need(math.isfinite(float(e)) and (e == 0 or float(e) > 0), 'energy not representable in JSON watts')
        if mode == 'unit_current':
            need(math.isfinite(float(e/current**2*1000)), 'resistance not representable in JSON milliohms')
        energy += e
        class_energy[c['kind']] = class_energy.get(c['kind'], np.longdouble(0)) + e
        row = {k: val for k, val in c.items() if k not in ('matrix', 'branch')}
        row['joule_energy_W'] = float(e)
        row['effective_resistance_ohm'] = float(e/current**2) if mode == 'unit_current' else None
        row['effective_resistance_mohm'] = float(e/current**2*1000) if mode == 'unit_current' else None
        if 'branch' in c:
            b = c['branch']
            stamp = rank_one(n, b['nodes'], b['weights'], b['resistance_ohm'])
            need(_max((M-stamp).data)/scale <= tol['kcl_relative'], 'branch stamp mismatch')
            row['oriented_current_A'] = float(np.dot(v[b['nodes']], b['weights'])/b['resistance_ohm'])
        contributions.append(row)
    actual = -_extended_residual(K, v, np.zeros(n))
    reference = _vector(packet['solution']['original_node_current_A'], n, 'original_node_current_A')
    work = np.dot(v, f)
    original_energy = np.longdouble(packet['solution']['original_energy_W'])
    need(np.isfinite(original_energy), 'nonfinite original energy')
    escale = max(abs(float(work)), 1e-30)
    iscale = max(_max(f), 1e-30)
    original_classes = packet['solution']['original_class_energy_W']
    need(set(original_classes) == set(class_energy), 'missing original class energy scope')
    for key, value in original_classes.items():
        need(type(value) in (float, int) and math.isfinite(value), 'nonfinite original class energy')
    checks = {
        'energy_classes_relative': max(abs(float(class_energy[k])-original_classes[k]) for k in class_energy)/escale,
        'operator_partition_relative': _max((assembled-K).data)/max(_max(K.data), 1e-30),
        'free_node_kcl_relative': _max((actual-f)[free])/iscale,
        'original_currents_relative': _max(actual-reference)/iscale,
        'global_kcl_relative': abs(float(sum(actual[fixed])+sum(f)))/max(float(sum(abs(f))), 1e-30),
        'energy_work_relative': abs(float(energy-work))/escale,
        'energy_original_relative': abs(float(energy-original_energy))/escale,
        'energy_operator_relative': abs(float(energy-np.dot(v, actual)))/escale,
    }
    out['checks'] = checks
    for key, value in checks.items():
        limit = tol['energy_relative' if key.startswith('energy_') else 'kcl_relative']
        need(math.isfinite(value) and value <= limit, 'reconciliation failed: ' + key)
    need(math.isfinite(float(energy)), 'total energy not representable in JSON watts')
    out.update(status='PASS_MODELED_SOLUTION_ACCOUNTING_ONLY', components=contributions,
               normalization=normalization, total_energy_W=float(energy),
               effective_resistance_ohm=float(energy/current**2) if mode == 'unit_current' else None,
               copper_resistance_ohm=float(sum(e for k,e in class_energy.items() if k in ('barrel','sheet_union'))/current**2) if mode == 'unit_current' else None,
               class_energy_W={k: float(e) for k,e in class_energy.items()},
               source_currents_A=[{**p, 'current_A': float(sum(actual[p['nodes']]))} for p in source['pads']],
               interpretation='Energy partition of a fixed network; no additive physical series path or geometry sensitivity claim.')
    # Aggregation preserves shared union membership as a SET, never one copy per member.
    aggregates = {}
    for c in contributions:
        key = (c['board'], c['kind'], tuple(c['object_ids']), tuple(c['layer_interval']))
        g = aggregates.setdefault(key, {k: c[k] for k in ('board', 'net', 'kind', 'object_ids', 'layer_interval')}
                                  | {'joule_energy_W': 0.})
        g['joule_energy_W'] += c['joule_energy_W']
        g['effective_resistance_ohm'] = g['joule_energy_W']/current**2 if mode == 'unit_current' else None
    out['physical_aggregates'] = list(aggregates.values())
    return out


def summary(result):
    lines = [result['status'], 'Unvalidated hardware; electrical acceptance/adoption: false.']
    if 'identity' in result:
        i = result['identity']
        lines.append(f"{i['board']} {i['net']} {i['ref']}.{i['pin']} UUID={i['pad_uuid']} "
                     f"{i['process_case']} / {i['depth_case']} / {i['return_state']}")
    for row in sorted(result['components'], key=lambda x: -x['joule_energy_W'])[:10]:
        lines.append(f"{row['board']} {row['kind']} {','.join(row['object_ids'])} "
                     f"{'→'.join(row['layer_interval'])}: {row['joule_energy_W']:.9g} W; "
                     f"R contribution={row['effective_resistance_mohm']} mΩ")
    lines.extend(result['failures'])
    return '\n'.join(lines) + '\n'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--detail', type=Path, required=True)
    parser.add_argument('--expected', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    for p in (args.detail, args.expected):
        need(p.stat().st_size <= MAX_JSON_BYTES, 'bounded JSON input exceeds 16 MiB')
    packet = json.loads(args.detail.read_text())
    need(packet['network']['matrix']['n'] <= 100000 and
         all(c['matrix']['n'] <= 100000 for c in packet['components']),
         'CLI limited to 100000 nodes; real extraction/accounting requires admitted in-memory diagnostic')
    result = attribute(packet, json.loads(args.expected.read_text()))
    with args.output.open('x') as stream:
        json.dump(result, stream, sort_keys=True, indent=2, allow_nan=False)
        stream.write('\n')
    print(summary(result), end='')
    return 0 if not result['failures'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
