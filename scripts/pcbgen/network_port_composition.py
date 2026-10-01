"""Explicit many-board finite-port composition, with no ideal rest node.

This is an exact-arithmetic identity evaluated as a FLOATING DIAGNOSTIC.
It is not an outward resistance certificate. Every supplied board operator
must use matching physical normal-current and continuous potential traces;
bare patch averages alone do not establish those premises. All source and
measurement columns are explicit balanced integer contact functionals.
"""
from collections import deque
import numpy as np


def cycle_coordinates(board_ids, endpoint_boards):
    """Integer tree right inverse and full cycle basis of the physical wires."""
    board_ids = tuple(board_ids)
    if not board_ids or len(set(board_ids)) != len(board_ids):
        raise ValueError('Unique explicit board identities required')
    lookup = {name: index for index, name in enumerate(board_ids)}
    incidence = np.zeros((len(board_ids), len(endpoint_boards)), dtype=np.int64)
    neighbors = [[] for _ in board_ids]
    for edge, (first, second) in enumerate(endpoint_boards):
        if first not in lookup or second not in lookup or first == second:
            raise ValueError('Each physical wire must join two declared boards')
        a, b = lookup[first], lookup[second]
        incidence[a, edge], incidence[b, edge] = -1, 1
        neighbors[a].append((b, edge, 1))
        neighbors[b].append((a, edge, -1))
    parent = {0: None}
    queue = deque([0])
    while queue:
        node = queue.popleft()
        for child, edge, sign in neighbors[node]:
            if child not in parent:
                parent[child] = (node, edge, sign)
                queue.append(child)
    if len(parent) != len(board_ids):
        raise ValueError('Physical board network disconnected; no implicit rest connection supplied')
    right = np.zeros((len(endpoint_boards), len(board_ids)-1), dtype=np.int64)
    tree_edges = set()
    for child in range(1, len(board_ids)):
        node = child
        while node:
            previous, edge, sign = parent[node]
            right[edge, child-1] = sign
            tree_edges.add(edge)
            node = previous
    expected = np.vstack((-np.ones((1, len(board_ids)-1), dtype=np.int64),
                          np.eye(len(board_ids)-1, dtype=np.int64)))
    if not np.array_equal(incidence @ right, expected):
        raise ValueError('Integer tree source identity failed')
    chords = [edge for edge in range(len(endpoint_boards)) if edge not in tree_edges]
    cycles = np.zeros((len(endpoint_boards), len(chords)), dtype=np.int64)
    for column, edge in enumerate(chords):
        cycles[edge, column] = 1
        cycles[:, column] -= right @ incidence[1:, edge]
    if np.any(incidence @ cycles):
        raise ValueError('Integer physical-wire cycle identity failed')
    return incidence, right, cycles


def compose(operators, contact_boards, wires, sources):
    """Minimize all explicit board and whole-wire energies over wire cycles.

    operators[board] contains a reference contact, ordered non-reference ports,
    and their energy matrix. contact_boards is the complete declared contact
    inventory. Each wire has id, from_contact, to_contact and paid resistance.
    sources is a contact -> integer row map, with one column per named external
    source or actual endpoint-to-endpoint observation. The caller must retain
    those column identities and physical support provenance separately.
    """
    board_ids = tuple(sorted(set(contact_boards.values())))
    if set(operators) != set(board_ids):
        raise ValueError('Every declared board needs an explicit operator; no ideal omitted board')
    contacts = tuple(contact_boards)
    index = {name: i for i, name in enumerate(contacts)}
    n = len(contacts)
    if set(sources) != set(contacts):
        raise ValueError('Explicit source rows required for the complete contact inventory')
    raw = np.asarray([sources[name] for name in contacts])
    if raw.ndim != 2 or not raw.shape[1] or not np.isfinite(raw).all() or np.any(raw != np.rint(raw)) or np.max(np.abs(raw)) > 10**6:
        raise ValueError('Finite bounded integer source/measurement functionals required')
    source = raw.astype(np.int64)
    if np.any(source.sum(axis=0)):
        raise ValueError('Every global source/measurement column must balance explicitly')
    if not wires or len({row['id'] for row in wires}) != len(wires):
        raise ValueError('Unique paid physical wire identities required')
    edge_map = np.zeros((n, len(wires)), dtype=np.int64)
    endpoints = []
    resistances = []
    for edge, wire in enumerate(wires):
        a, b = wire['from_contact'], wire['to_contact']
        if a not in index or b not in index:
            raise ValueError('Wire endpoint missing from declared physical contacts')
        edge_map[index[a], edge], edge_map[index[b], edge] = -1, 1
        endpoints.append((contact_boards[a], contact_boards[b]))
        resistances.append(wire['resistance'])
    resistance = np.asarray(resistances, dtype=float)
    if not np.isfinite(resistance).all() or np.any(resistance <= 0):
        raise ValueError('Every included whole wire needs finite positive paid energy')
    incidence, right, cycles = cycle_coordinates(board_ids, endpoints)
    board_source = np.array([source[[index[c] for c in contacts if contact_boards[c] == board]].sum(axis=0) for board in board_ids])
    particular = -right @ board_source[1:]
    if np.any(incidence @ particular + board_source):
        raise ValueError('Integer board source balance failed')
    contact_source = source + edge_map @ particular
    contact_cycles = edge_map @ cycles
    weighted_source = resistance[:, None] * particular
    weighted_cycles = resistance[:, None] * cycles
    energy = particular.T @ weighted_source
    cross = particular.T @ weighted_cycles
    internal = cycles.T @ weighted_cycles
    for board in board_ids:
        operator = operators[board]
        ports = list(operator['ports'])
        reference = operator['reference']
        declared = {contact for contact in contacts if contact_boards[contact] == board}
        if reference in ports or len(set(ports)) != len(ports) or set(ports) | {reference} != declared:
            raise ValueError('Board operator must cover every declared contact exactly once, including its reference')
        matrix = np.asarray(operator['energy'], dtype=float)
        if matrix.shape != (len(ports), len(ports)) or not np.isfinite(matrix).all() or not np.allclose(matrix, matrix.T, rtol=1e-12, atol=1e-15):
            raise ValueError('Finite symmetric board energy operator required')
        rows = [index[contact] for contact in ports]
        cs, cc = contact_source[rows], contact_cycles[rows]
        energy = energy + cs.T @ matrix @ cs
        cross = cross + cs.T @ matrix @ cc
        internal = internal + cc.T @ matrix @ cc
    if len(cycles.T):
        try:
            factor = np.linalg.cholesky((internal + internal.T)/2)
        except np.linalg.LinAlgError as error:
            raise ValueError('Internal cycle energy is not positive definite; no finite minimum certified') from error
        amplitudes = -np.linalg.solve(factor.T, np.linalg.solve(factor, cross.T))
    else:
        amplitudes = np.zeros((0, source.shape[1]))
    wire_currents = particular + cycles @ amplitudes
    result = energy + cross @ amplitudes
    return {'energy': (result + result.T)/2, 'wire_current_map': wire_currents,
        'wire_ids': [wire['id'] for wire in wires], 'board_ids': board_ids,
        'integer_balance_verified': True,
        'cycle_count': cycles.shape[1],
        'floating_board_KCL_residual': float(np.max(np.abs(incidence @ wire_currents + board_source))),
        'scope': 'NOT ACCEPTED: exact-arithmetic composition identity evaluated as a floating diagnostic. Complete physical traces, material/contact/current classes, outward numerical bounds and the separate common/voltage targets remain required.'}
