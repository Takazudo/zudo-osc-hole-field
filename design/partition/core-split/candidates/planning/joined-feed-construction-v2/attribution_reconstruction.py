#!/usr/bin/env python3
"""Source-fixture reconstruction and local copper accounting for E16.

No artifact loader, production executor, authority or scheduler lives here.
The end-to-end entry point is deliberately bounded to tiny in-memory fixtures.
The local accounting primitive uses one board's sparse pattern and one tile at
a time; it does not construct a joined matrix or a board vector per component.
Production map recovery, independent uniqueness evidence and resource admission
remain explicit gates, not switches that this module can turn on.
"""
import copy
import argparse
import ast
import hashlib
import json
from pathlib import Path

import numpy as np
import scipy.sparse as sp
import scipy.sparse.linalg as spla

import finite_adapter as A
import finite_solve as S
import resistance_attribution as R

FIXTURE_NODES = 256
FIXTURE_ENTRIES = 65536
FIXTURE_VERTICES = 4096
FIXTURE_ITEMS = 128
TOLERANCE = 1e-9
KEY_DTYPE = np.dtype([('group', '<i8'), ('x', '<i8'), ('y', '<i8')])


def coordinate_keys(group, xy):
    xy = np.asarray(xy)
    R.need(xy.ndim == 2 and xy.shape[1] == 2 and np.isfinite(xy).all(), 'invalid mesh coordinates')
    R.need(np.max(np.abs(xy), initial=0) < 2**62 / A.SCALE, 'mesh coordinate overflow')
    result = np.empty(len(xy), dtype=KEY_DTYPE)
    result['group'] = group
    result['x'], result['y'] = np.rint(xy * A.SCALE).astype(np.int64).T
    return result


class AssemblyMap:
    """Reuse original Assembly numbering including collapsed bore rings.

    Structured 24-byte keys replace the reporter's Python dict/tuple per vertex.
    This does NOT recover an Assembly from an operator-only pickle.
    """
    def __init__(self, assembly):
        self.keys = coordinate_keys(assembly.group, assembly.xy)
        R.need(np.array_equal(np.argsort(self.keys), np.arange(len(self.keys))),
               'Assembly keys are not in original lexicographic order')
        R.need(len(np.unique(self.keys)) == len(self.keys), 'duplicate Assembly vertex key')
        self.nodes = assembly.vertex_node
        self.n = assembly.N

    def map(self, item):
        keys = coordinate_keys(item['group'], item['xy'])
        positions = np.searchsorted(self.keys, keys)
        R.need((positions < len(self.keys)).all(), 'mesh vertex absent from original Assembly')
        R.need(np.array_equal(self.keys[positions], keys), 'mesh vertex absent from original Assembly')
        return self.nodes[positions]


def copper_stream(assembly, items, expected_items, case, depth, board, net):
    """Yield (metadata, board nodes, LOCAL matrix), retaining every tile/interval.

    expected_items is the separately bound original mesh plan, in original order.
    Members of a union are provenance, never separate energy owners. No mesh or
    full-matrix construction is performed here. The caller must exhaust the
    iterator before publishing results so missing final items fail closed.
    """
    mapping = AssemblyMap(assembly)
    groups = {g['group']: g for g in assembly.desc['groups']}
    seen = set()
    count = 0
    for index, item in enumerate(items):
        identity = (item['group'], None if item['tile'] is None else tuple(item['tile']))
        R.need(index < len(expected_items) and identity == expected_items[index], 'missing/reordered mesh item')
        R.need(identity not in seen, 'duplicate union tile')
        seen.add(identity)
        count += 1
        group = groups[item['group']]
        mapped = mapping.map(item)
        nodes, inverse = np.unique(mapped, return_inverse=True)
        thickness = case['outer_copper_mm'] if group['layer'] in A.FACES else case['inner_copper_mm']
        # Match Assembly geometric accumulation before process scaling.
        local = sp.csr_matrix((item['val'], (inverse[item['row']], inverse[item['col']])),
                              shape=(len(nodes), len(nodes)))
        local *= thickness / case['rho_ohm_mm']
        yield ({'id': f'{board}:sheet:{index}', 'kind': 'sheet_union', 'board': board, 'net': net,
                'object_ids': sorted(group['fragments']), 'layer_interval': [group['layer']],
                'region': {'group': item['group'], 'tile_mm': item['tile']}}, nodes, local)
    R.need(count == len(expected_items), 'missing final mesh item')
    z = A.layer_z(depth)
    for bid, barrel in assembly.desc['barrels'].items():
        taps = sorted((z[t['layer']], t['layer']) for t in barrel['taps'])
        for (za, la), (zb, lb) in zip(taps, taps[1:]):
            length = depth.get('legacy_leg_mm') or zb - za
            resistance = A.barrel_interval_ohm(case['rho_ohm_mm'], length, barrel['drill_mm'], case['barrel_plating_mm'])
            nodes = np.array([assembly.rings[bid, la], assembly.rings[bid, lb]], dtype=np.int64)
            yield ({'id': f'{board}:barrel:{bid}:{la}:{lb}', 'kind': 'barrel', 'board': board, 'net': net,
                    'object_ids': [bid], 'layer_interval': [la, lb], 'region': {'length_mm': length},
                    'branch': {'nodes': [0, 1], 'weights': [1., -1.], 'resistance_ohm': resistance}},
                   nodes, sp.csr_matrix(np.array([[1., -1.], [-1., 1.]]) / resistance))


class PatternSum:
    """Accumulate a partition into an existing board CSR pattern, never M += tile.

    Absent reference entries are rejected unless exactly zero. One long-double
    value per reference nnz is retained; local matrices and searches are bounded
    by tile size. This is an equivalence primitive, not a throughput claim.
    """
    def __init__(self, reference):
        self.reference = reference.tocsr(copy=True)
        self.reference.sum_duplicates()
        self.reference.sort_indices()
        self.values = np.zeros(self.reference.nnz, dtype=np.longdouble)

    def add(self, nodes, matrix):
        R.need(len(nodes) == len(set(map(int, nodes))) and (nodes >= 0).all()
               and (nodes < self.reference.shape[0]).all(), 'invalid local node mapping')
        local = matrix.tocsr()
        R.need(local.shape == (len(nodes), len(nodes)), 'local matrix shape differs')
        for i in range(len(nodes)):
            start, stop = local.indptr[i:i+2]
            values = local.data[start:stop]
            nonzero = values != 0
            columns = nodes[local.indices[start:stop][nonzero]]
            lo, hi = self.reference.indptr[nodes[i]:nodes[i]+2]
            pattern = self.reference.indices[lo:hi]
            positions = np.searchsorted(pattern, columns)
            R.need((positions < len(pattern)).all() and np.array_equal(pattern[positions], columns),
                   'component entry absent from original operator')
            np.add.at(self.values, lo + positions, values[nonzero].astype(np.longdouble))

    def relative_error(self):
        return R._max(self.values - self.reference.data) / max(R._max(self.reference.data), 1e-30)


def account_copper(reference, components, potential, injection_scale_A=1., output_limit=64*1024**2):
    """Complete local streamed partition audit; no successful partial result.

    One board current accumulator is shared by all components. The independent
    original-operator application is evaluated once after all components. Output
    is bounded as canonical JSON rows before retention; failure returns no rows.
    """
    potential = np.asarray(potential, dtype=np.longdouble)
    R.need(np.isfinite(injection_scale_A) and injection_scale_A > 0, 'invalid current normalization')
    R.need(reference.shape == (len(potential), len(potential)) and np.isfinite(potential).all(), 'invalid board field')
    partition = PatternSum(reference)
    current = np.zeros(len(potential), dtype=np.longdouble)
    rows, ids, physical = [], set(), set()
    energy = np.longdouble(0)
    output_bytes = 2
    for metadata, nodes, matrix in components:
        R.need(metadata['id'] not in ids, 'duplicate component identity')
        ids.add(metadata['id'])
        key = (metadata['board'], metadata['kind'], tuple(metadata['object_ids']),
               tuple(metadata['layer_interval']), R.digest(metadata['region']))
        R.need(key not in physical, 'duplicate physical component')
        physical.add(key)
        R.need(np.isfinite(matrix.data).all(), 'nonfinite local matrix')
        scale = max(R._max(matrix.data), 1e-30)
        R.need(R._max((matrix-matrix.T).data)/scale <= TOLERANCE, 'nonreciprocal local matrix')
        R.need(R._max(np.asarray(matrix.sum(axis=1)).ravel())/scale <= TOLERANCE, 'nonconservative local matrix')
        partition.add(nodes, matrix)
        local_v = potential[nodes]
        local_i = -S._extended_residual(matrix, local_v, np.zeros(len(nodes)))
        np.add.at(current, nodes, local_i.astype(np.longdouble))
        e = np.dot(local_v, local_i.astype(np.longdouble))
        R.need(np.isfinite(e) and e >= 0, 'negative/nonfinite local energy')
        energy += e
        row = {k: v for k, v in metadata.items() if k != 'branch'} | {'joule_energy_W': float(e)}
        if 'branch' in metadata:
            b = metadata['branch']
            row['oriented_current_A'] = float(local_v @ b['weights'] / b['resistance_ohm'])
        output_bytes += len(json.dumps(row, sort_keys=True, separators=(',', ':'), allow_nan=False).encode()) + 1
        R.need(output_bytes <= output_limit, 'accounting output resource bound exceeded')
        rows.append(row)
    R.need(ids, 'empty copper inventory')
    original = -S._extended_residual(reference, potential, np.zeros(len(potential)))
    checks = {'operator_partition_relative': partition.relative_error(),
              'node_current_absolute_A': R._max(current-original),
              'energy_operator_relative': abs(float(energy-potential @ original))/max(abs(float(potential @ original)), 1e-30)}
    R.need(checks['operator_partition_relative'] <= TOLERANCE, 'operator partition reconciliation failed')
    checks['node_current_relative'] = checks['node_current_absolute_A']/injection_scale_A
    R.need(checks['node_current_relative'] <= TOLERANCE, 'partition current reconciliation failed')
    R.need(checks['energy_operator_relative'] <= TOLERANCE, 'local energy reconciliation failed')
    return {'components': rows, 'current_A': current, 'energy_W': energy, 'checks': checks}


def check_fixture_size(operators):
    R.need(set(operators) == {'KA', 'KB'}, 'complete KA/KB operators required')
    R.need(all(type(o['N']) is int and o['N'] > 0 for o in operators.values()), 'invalid fixture node count')
    n = sum(o['N'] + len(o['terminals']) for o in operators.values())
    R.need(n <= FIXTURE_NODES, 'PRODUCTION_BLOCKED: original Assembly recovery and exact uniqueness/resource admission required; fixture ceiling is 256 nodes')
    for op in operators.values():
        check_fixture_payload(op)
        for cls in ('face', 'inner'):
            matrix = op['Kg_'+cls]
            R.need(sp.issparse(matrix) and matrix.shape == (op['N'], op['N'])
                   and matrix.nnz <= FIXTURE_ENTRIES, 'fixture matrix storage resource bound exceeded')
        R.need(len(op['supports']) <= FIXTURE_NODES and len(op['barrels']) <= FIXTURE_ITEMS,
               'fixture support/barrel resource bound exceeded')
        for pid, (ns, weights) in op['supports'].items():
            R.need(len(ns) == len(weights) == len(op['support_inside'][pid]) <= FIXTURE_NODES,
                   'fixture support storage resource bound exceeded')
    return n


def check_fixture_payload(value):
    """Bound all consumed fixture payloads before numpy/Shapely allocations.

    Preconstructed inputs are caller-owned; these limits prevent tiny declared
    N from triggering large subsequent copies, geometry parsing or sparse work.
    They are source-test controls, never production-size admission controls.
    """
    entries, size = 0, 0
    def visit(obj):
        nonlocal entries, size
        entries += 1
        R.need(entries <= 262144 and size <= 4*1024**2, 'fixture payload resource bound exceeded')
        if sp.issparse(obj):
            R.need(obj.shape[0] <= FIXTURE_NODES and obj.shape[1] <= FIXTURE_NODES
                   and obj.nnz <= FIXTURE_ENTRIES, 'fixture sparse payload resource bound exceeded')
            entries += obj.nnz
            size += obj.nnz*24
        elif isinstance(obj, np.ndarray):
            R.need(obj.size <= FIXTURE_ENTRIES and obj.dtype.kind in 'biuf', 'fixture array payload resource bound exceeded')
            entries += obj.size
            size += obj.nbytes
        elif isinstance(obj, (str, bytes)):
            size += len(obj)*4  # Conservative UTF-8 upper bound; no encoding copy.
        elif isinstance(obj, dict):
            R.need(len(obj) <= FIXTURE_ENTRIES, 'fixture mapping payload resource bound exceeded')
            for key, item in obj.items():
                visit(key); visit(item)
        elif isinstance(obj, (tuple, list)):
            R.need(len(obj) <= FIXTURE_ENTRIES, 'fixture sequence payload resource bound exceeded')
            for item in obj:
                visit(item)
        else:
            R.need(obj is None or isinstance(obj, (bool, int, float, np.number)), 'unsupported fixture payload')
            size += 32
        R.need(entries <= 262144 and size <= 4*1024**2, 'fixture payload resource bound exceeded')
    visit(value)


def check_fixture_mesh(items):
    R.need(isinstance(items, (list, tuple)) and len(items) <= FIXTURE_ITEMS, 'fixture item resource bound exceeded')
    R.need(sum(len(it['xy']) for it in items) <= FIXTURE_VERTICES, 'fixture mesh vertex resource bound exceeded')
    R.need(sum(len(it['val']) for it in items) <= FIXTURE_ENTRIES, 'fixture mesh entry resource bound exceeded')
    check_fixture_payload(items)


def recover_fixture_assembly(desc, items, operator):
    """Recover discarded original numbering from original tiny mesh bytes.

    Bounds apply before Assembly's sorting/concatenation. This uses the original
    Assembly implementation, then verifies *all* persisted mappings/stiffness;
    an operator hash alone is not a substitute for this reconstruction check.
    Production-sized recovery must be independently admitted and costed.
    """
    R.need(0 < operator['N'] <= FIXTURE_NODES, 'PRODUCTION_BLOCKED: Assembly recovery exceeds fixture ceiling')
    check_fixture_mesh(items)
    check_fixture_payload(desc)
    check_fixture_payload(operator)
    asm = A.Assembly(desc, items)
    check_assembly(asm, operator)
    return asm


def check_assembly(asm, op):
    R.need(asm.N == op['N'] and asm.rings == op['rings'] and asm.desc['barrels'] == op['barrels'], 'Assembly/ring mapping drift')
    R.need(set(asm.supports) == set(op['supports']), 'Assembly support UUID drift')
    for pid in op['supports']:
        R.need(all(np.array_equal(a, b) for a, b in zip(asm.supports[pid], op['supports'][pid]))
               and np.array_equal(asm.support_inside[pid], op['support_inside'][pid]), 'Assembly support mapping drift')
    for cls in ('face', 'inner'):
        R.need(R._max((asm.Kg[cls]-op['Kg_'+cls]).data) == 0, 'Assembly operator drift')


def reconstruct_fixture(operators, reductions, config, case, depth, observation, current=1., removed=()):
    """One selected RHS + existing reduced coupling, for bounded source fixtures.

    The retained simultaneous-load u0/g are intentionally NOT used. The
    observation-board u is new; every other board has zero selected excitation.
    Full matrices below are tiny independent reporter/uniqueness references.
    No public CLI or flag can increase the fixture ceiling.
    """
    check_fixture_size(operators)  # Before matrix/factorization or reduction reads.
    check_fixture_payload(reductions)
    check_fixture_payload(config)
    check_fixture_payload(observation)
    R.need(np.isfinite(current) and current != 0 and np.isfinite(current*current)
           and current*current > 0, 'invalid current normalization')
    board, pad, net = observation['board'], observation['pad_uuid'], observation['net']
    R.need(board in operators, 'unknown observation board')
    R.need(not (net == 'AGND' and set(removed) == {4, 5, 6}), 'STRUCTURALLY_FLOATING_AGND_ALL_THREE_OPEN')
    configured_sources = config['source_support']['pads'][net]
    R.need(pad not in {p['pad_id'] for p in configured_sources}, 'observation identity is a held source pad')
    terms = {}
    source_pads = []
    small_red = {}
    offsets = {}
    matrices, masks = [], []
    total = 0
    fields = {}
    for tag in ('KA', 'KB'):
        op, red = operators[tag], reductions[tag]
        fixed, src = S.held_nodes(op, config, tag, net)
        free = np.flatnonzero(~fixed)
        ts, _, _ = S.terminal_stamps(op, config)
        R.need(red['N'] == op['N'] and red['terms'] == ts and np.array_equal(red['free'], free), 'reduction held/terminal mapping drift')
        R.need(red['source_pads'] == src, 'reduction source UUID drift')
        R.need(red['board'] == tag and red['net'] == net and red['case'] == observation['process_case']
               and red['depth'] == observation['depth_case'], 'reduction identity drift')
        R.need(red['Y'].shape == (len(free), len(ts)) and np.isfinite(red['Y']).all(), 'invalid retained basis')
        M, _, _ = S.full_matrix(op, case, depth, config, tag, net)
        matrices.append(M)
        masks.append(np.r_[fixed, np.zeros(len(ts), dtype=bool)])
        offsets[tag] = total
        total += M.shape[0]
        terms[tag] = ts
        if src:
            for p in configured_sources:
                ns = op['supports'][p['pad_id']][0][op['support_inside'][p['pad_id']]]
                source_pads.append({'ref': p['ref'], 'pin': '1', 'pad_uuid': p['pad_id'], 'board': tag,
                                    'nodes': (ns + offsets[tag]).tolist()})
        Af, B, D, free, pos, _, _, _, _, _ = S.board_parts(op, case, depth, config, tag, net)
        R.need(R._max(S._extended_residual(Af, red['Y'], B))/max(R._max(B), 1e-30) <= 1e-9,
               'retained basis residual failed')
        R.need(R._max(red['S']-np.asarray(D-B.T @ red['Y'], dtype=float))/max(R._max(red['S']), 1e-30) <= 1e-9,
               'retained Schur matrix differs')
        u = np.zeros(len(free), dtype=np.longdouble)
        q = np.zeros(len(ts))
        if tag == board:
            ns, weights = op['supports'][pad]
            R.need(len(ns) == len(set(map(int, ns))) and (pos[ns] >= 0).all(), 'invalid/held observation support')
            R.need(np.isfinite(weights).all() and (weights >= 0).all() and abs(weights.sum()-1) <= 1e-9, 'invalid observation normalization')
            f = np.zeros(len(free))
            f[pos[ns]] = weights * current
            lu = spla.splu(Af, permc_spec='MMD_AT_PLUS_A', diag_pivot_thresh=0., options={'SymmetricMode': True})
            u, residual = S.refined_solve(lu, Af, f, extended_solution=True)
            del lu
            R.need(np.isfinite(residual) and residual <= 1e-9, 'selected RHS residual failed')
            q = np.asarray(B.T @ u, dtype=float)
        fields[tag] = {'N': op['N'], 'free': free, 'Y': red['Y'], 'u0': u}
        small_red[tag] = {'terms': ts, 'S': red['S'], 'g': q}
        del Af, B, D
    G, wires = S.small_system(small_red['KA'], small_red['KB'], config, set(removed))
    R.need(set(removed) <= set(wires), 'unknown removed wire')
    # Tiny independent positive definiteness will also be checked on the full
    # held operator by the reporter. A successful LU alone is not attestation.
    eig = np.linalg.eigvalsh((G+G.T)/2)
    R.need(len(eig) and eig[0] > np.finfo(float).eps*len(eig)*max(R._max(eig), 1e-300), 'singular/unresolved reduced interface')
    vt = np.linalg.solve(G, -np.r_[small_red['KA']['g'], small_red['KB']['g']])
    k = len(wires)
    v = np.concatenate([np.r_[S.reconstruct_potential(fields[b], t), t]
                        for b, t in (('KA', vt[:k]), ('KB', vt[k:]))]).astype(np.longdouble)
    M = sp.block_diag(matrices, format='csr')
    for j, w in enumerate(wires):
        if w not in removed:
            ns = [operators['KA']['N']+j, offsets['KB']+operators['KB']['N']+j]
            M += R.rank_one(total, ns, [1., -1.], config['wires']['bulk_ohm'])
    f = np.zeros(total, dtype=np.longdouble)
    ns, weights = operators[board]['supports'][pad]
    f[ns+offsets[board]] = weights.astype(np.longdouble)*current
    identity = copy.deepcopy(observation)
    identity.update(return_state='all-present' if not removed else 'remove-'+'-'.join(f'W{w}' for w in removed),
                    observation_support={'nodes': (ns+offsets[board]).tolist(), 'weights': weights.tolist()},
                    source_support={'mode': 'equipotential_patches', 'potential_V': 0,
                                    'board': config['source_support']['board'], 'pads': source_pads})
    return {'matrix': M, 'potential': v, 'injection': f, 'identity': identity,
            'offsets': offsets, 'fields': fields, 'terminal_potential': vt,
            'solve_residual_relative': residual}


def fixture_report(operators, reductions, assemblies, items, plans, config, case, depth,
                   observation, current=1., removed=(), output_limit=64*1024**2):
    """Tiny end-to-end bridge into the unchanged PR275 report semantics.

    Reconstructs a new selected field; original class energies come from the
    independent board operators, not the proposed physical partition. A tiny
    full packet exists only for reporter parity, never for production transport.
    """
    check_fixture_size(operators)
    check_fixture_payload(reductions)
    check_fixture_payload(config)
    for board in ('KA', 'KB'):
        check_fixture_mesh(items[board])
        R.need(len(assemblies[board].xy) <= FIXTURE_VERTICES and len(plans[board]) <= FIXTURE_ITEMS,
               'fixture Assembly/plan resource bound exceeded')
        check_fixture_payload(vars(assemblies[board]))
        check_fixture_payload(plans[board])
    rebuilt = reconstruct_fixture(operators, reductions, config, case, depth, observation, current, removed)
    M, v, f = (rebuilt[k] for k in ('matrix', 'potential', 'injection'))
    n = len(v)
    components, _ = R.interface_components(operators, config, observation['net'], removed)
    originals = {'sheet_union': 0., 'barrel': 0., 'termination': 0.}
    local_checks = {}
    for board in ('KA', 'KB'):
        asm, op = assemblies[board], operators[board]
        check_assembly(asm, op)
        K, Kb, _ = A.laplacian(op['Kg_face'], op['Kg_inner'], op['barrels'], op['rings'], case, depth)
        offset = rebuilt['offsets'][board]
        vm = v[offset:offset+op['N']]
        local = list(copper_stream(asm, items[board], plans[board], case, depth, board, observation['net']))
        # Match the reporter's maximum nodal injection scale, including unequal
        # distributed observations; total excitation magnitude is less strict.
        audit = account_copper(K, iter(local), vm, injection_scale_A=R._max(f), output_limit=output_limit)
        R.need(audit['checks']['node_current_absolute_A']/abs(current) <= 1e-9, 'partition current reconciliation failed')
        local_checks[board] = audit['checks']
        for meta, nodes, matrix in local:
            coo = matrix.tocoo()
            embedded = sp.csr_matrix((coo.data, (nodes[coo.row]+offset, nodes[coo.col]+offset)), shape=(n, n))
            component = copy.deepcopy(meta)
            if 'branch' in component:
                component['branch']['nodes'] = (nodes+offset).tolist()
            components.append(component | {'matrix': R.matrix_record(embedded)})
        for cls, thickness in (('face', 'outer_copper_mm'), ('inner', 'inner_copper_mm')):
            originals['sheet_union'] += float(vm @ (op['Kg_'+cls] @ vm))*case[thickness]/case['rho_ohm_mm']
        originals['barrel'] += float(vm @ (Kb @ vm))
        ts, rt, supports = S.terminal_stamps(op, config)
        originals['termination'] += float(sum((w @ vm[ns]-v[offset+op['N']+j])**2/rt for j, (ns, w) in enumerate(supports)))
    if any(c['kind'] == 'wire_bulk' for c in components):
        k = len(rebuilt['terminal_potential'])//2
        vt = rebuilt['terminal_potential']
        wires = [S.wire_of(t) for t in reductions['KA']['terms']]
        originals['wire_bulk'] = float(sum((vt[j]-vt[k+j])**2/config['wires']['bulk_ohm'] for j, w in enumerate(wires) if w not in removed))
    if not any(c['kind'] == 'barrel' for c in components):
        originals.pop('barrel')
    packet = {'schema': 'e16-attribution-detail-v1', 'identity': rebuilt['identity'],
              'network': {'matrix': R.matrix_record(M)}, 'components': components,
              'solution': {'potential_V': list(map(str, v)), 'injection_A': list(map(str, f)),
                           'original_node_current_A': list(map(str, -S._extended_residual(M, v, np.zeros(n)))),
                           'original_energy_W': sum(originals.values()), 'original_class_energy_W': originals,
                           'normalization': {'mode': 'unit_current', 'current_A': current}},
              'scope': {'complete_modeled_network': True, 'omitted_components': [],
                        'physical_omissions': ['Synthetic fixture only; source/protection, GH paths, unsupported loads and physical returns unqualified.'],
                        'expected_component_ids': [c['id'] for c in components]},
              'provenance': {'source_sha256': R.digest(observation), 'operator_sha256': R.digest(R.matrix_record(M)),
                             'extractor_sha256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                             'config_sha256': hashlib.sha256(R.CONFIG.read_bytes()).hexdigest(), 'quantity_origin': 'synthetic'}}
    result = R.attribute(packet, R.bindings(packet))
    result['reconstruction'] = {'scope': 'TINY_SOURCE_FIXTURE_ONLY', 'selected_rhs_count': 1,
                                'solve_residual_relative': rebuilt['solve_residual_relative'], 'local_checks': local_checks,
                                'fixture_config_sha256': R.digest(config)}
    R.need(len(json.dumps(result, allow_nan=False).encode()) <= output_limit, 'report output resource bound exceeded')
    return result, packet


def readiness():
    """Read source contracts only; never inspect or deserialize a real operator.

    This is a reproducible technical blocker, not a request/approval generator.
    Its digest identifies a readiness report, never a numerical execution request.
    """
    here = Path(__file__).resolve().parent
    tree = ast.parse((here/'finite_units.py').read_text())
    function = next(n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'assemble')
    assignments = [n.value for n in ast.walk(function) if isinstance(n, ast.Assign)
                   and any(isinstance(t, ast.Name) and t.id == 'ops' for t in n.targets)]
    R.need(len(assignments) == 1 and isinstance(assignments[0], ast.Dict), 'operator save contract changed: review required')
    saved = sorted(ast.literal_eval(k) for k in assignments[0].keys)
    required = ['group', 'xy', 'vertex_node']
    missing = sorted(set(required)-set(saved))
    experiment = json.loads((here/'evidence/e16/resistance-attribution-wsl-20261014/transfer-experiment.json').read_text())
    return {'schema': 'e16-reconstruction-readiness-v1',
            'B0': 'TINY_BRIDGE_IMPLEMENTED; test/review verdicts are separate evidence',
            'B1': 'NOT_EXECUTABLE_NOT_ADMITTED', 'C': 'NOT_RUN',
            'production_request_sha256': None, 'real_diagnostic_ran': False,
            'electrical_acceptance': False, 'whole_board_acceptance': False, 'adopted': False,
            'selected_experiment': experiment['diagnostic_B'],
            'operator_contract': {'persisted_fields': saved, 'missing_original_mapping_fields': missing,
                                  'original_mesh_required': True, 'scalar_dpoint_is_full_field': False},
            'blocking_operations': [
                {'id': 'serialized-production-driver', 'status': 'NOT_IMPLEMENTED',
                 'requirement': 'Production loading/decompression, original Assembly map recovery, one selected KB RHS and serialized KA/KB local accounting must share one 180s/2GiB/no-swap guard interval. Fixture entry point refuses production before matrix construction.'},
                {'id': 'exact-free-operator-uniqueness', 'status': 'NO_APPLICABLE_INDEPENDENT_EVIDENCE',
                 'requirement': 'Independently reviewed positive-definiteness checking method and receipt bound to actual board free matrices, held mapping and coupled return state. Neither successful SuperLU, tiny G positivity nor graph connectivity certifies the real free operator.'},
                {'id': 'combined-resource-proof', 'status': 'NOT_ESTABLISHED',
                 'requirement': 'Account all map sorting, matrix/LU/basis lifetimes, local-pattern accumulation, uniqueness checks, in-guard hashing and output within one attempt. Historical separate receipts and tiny-fixture timings are not a combined bound.'},
                {'id': 'one-unit-admission', 'status': 'NO_APPLICABLE_EXECUTABLE_REQUEST',
                 'requirement': 'Existing full-baseline hook requires maximum_units=148. Review a narrowly bound one-unit operation using existing admission controls; obtain applicable numerical authorization and exclusive reservation. Never reuse native negative-control approval.'}],
            'source_sha256': {name: hashlib.sha256((here/name).read_bytes()).hexdigest() for name in
                              ('attribution_reconstruction.py', 'test_attribution_reconstruction.py',
                               'finite_units.py', 'finite_adapter.py', 'finite_solve.py',
                               'resistance_attribution.py', 'numerical_unit_guard.py')},
            'next_source_command': '/home/takazudo/.cache/zudo-e16-numerical-venv/bin/python -m unittest test_attribution_reconstruction test_resistance_attribution -v',
            'production_execute_command': None}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--readiness', action='store_true', required=True)
    parser.add_argument('--output', type=Path)
    args = parser.parse_args(argv)
    report = readiness()
    encoded = json.dumps(report, sort_keys=True, indent=2, allow_nan=False)+'\n'
    if args.output:
        with args.output.open('x') as stream:
            stream.write(encoded)
    else:
        print(encoded, end='')
    return 2  # Explicit NOT EXECUTABLE, not successful diagnostic admission.


if __name__ == '__main__':
    raise SystemExit(main())
