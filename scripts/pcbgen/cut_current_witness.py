"""Exact resistor-graph fixture for a closed-network cut-current certificate.

This module certifies only the explicitly supplied finite resistor graph. It
does not admit physical contacts, continuum traces, material/process classes,
or any issue-38 hardware. No candidate edge is removed or shorted.

Incidence B is +1 at an edge's ``from`` node and -1 at its ``to`` node.
Positive current flows from ``from`` to ``to`` and B*j=f. For resistance R
in ohms and C=R^-1, a signed cut selector c defines c.T*j. A normalized
unit-EMF potential v is dimensionless; the circulation trial k has units S.

For z=c-B.T*v and B*k=0, the exact gap is

    Delta = z.T*C*z - (2*c.T*k - k.T*R*k)
          = (C*z-k).T*R*(C*z-k)                     [S].

If j0 carries the external source f, U_f=j0.T*R*j0 is an upper bound on
physical source energy. The passive graph's actual current obeys

    |c.T*j_actual - f.T*v|^2 <= Delta * U_f         [A^2].

The continuum analogue uses an auxiliary potential with a unit jump across
every strand of a full wire cut and continuous elsewhere. It does not make
the physical cut or either face equipotential. Complete physical trace and
geometry admission is a separate obligation. In particular, this S-valued
gap must not be mistaken for a unit-current voltage-observation gap in ohms.
"""
from fractions import Fraction


SCOPE = (
    "Exact supplied resistor-graph fixture only; physical conductor/contact "
    "admission and issue-38 current/common/voltage acceptance NOT ESTABLISHED"
)


def _rational(value):
    # Reject binary floats rather than silently interpreting a decimal claim
    # as a different rational or hiding a NaN/infinity conversion.
    if isinstance(value, bool) or not isinstance(value, (int, str, Fraction)):
        raise ValueError("Use finite exact int, Fraction or rational-string inputs")
    try:
        return Fraction(value)
    except (ValueError, ZeroDivisionError) as error:
        raise ValueError("Finite exact rational input required") from error


def _graph(edges):
    if not edges:
        raise ValueError("A nonempty explicit graph is required")
    parsed = []
    edge_ids = set()
    nodes = set()
    neighbors = {}
    for edge in edges:
        identity, first, second = edge["id"], edge["from"], edge["to"]
        if not all(isinstance(x, str) and x for x in (identity, first, second)):
            raise ValueError("Nonempty string graph identities required")
        if identity in edge_ids or first == second:
            raise ValueError("Unique non-self edge identities required")
        resistance = _rational(edge["resistance_ohm"])
        if resistance <= 0:
            raise ValueError("Each conductor needs finite positive resistance")
        parsed.append((identity, first, second, resistance))
        edge_ids.add(identity)
        nodes.update((first, second))
        neighbors.setdefault(first, set()).add(second)
        neighbors.setdefault(second, set()).add(first)
    reached = set()
    pending = [next(iter(nodes))]
    while pending:
        node = pending.pop()
        if node not in reached:
            reached.add(node)
            pending.extend(neighbors[node] - reached)
    if reached != nodes:
        raise ValueError("Explicit graph must be connected; no ideal rest node")
    return parsed, nodes, edge_ids


def _values(values, identities, name):
    if set(values) != identities:
        raise ValueError(name + " must name every graph identity exactly")
    return {identity: _rational(value) for identity, value in values.items()}


def _divergence(edges, nodes, currents):
    result = dict.fromkeys(nodes, Fraction(0))
    for identity, first, second, _ in edges:
        result[first] += currents[identity]
        result[second] -= currents[identity]
    return result


def cut_current_witness(edges, cut, potential, circulation):
    """Evaluate an exact unit-EMF upper/lower pair and mismatch-square gap.

    ``cut`` maps selected edge IDs to +1 or -1; multiple entries can represent
    the strands of a complete wire cross-section. Actual cut coverage is not
    inferred from a graph label. ``potential`` explicitly names every node;
    ``circulation`` names every edge and must have exactly zero divergence.
    The variational lower may be negative and the gap may be exactly zero.
    """
    parsed, nodes, edge_ids = _graph(edges)
    if not cut or not set(cut) <= edge_ids:
        raise ValueError("A named nonempty cut inside the graph is required")
    selector = {identity: _rational(value) for identity, value in cut.items()}
    if any(value not in (-1, 1) for value in selector.values()):
        raise ValueError("Cut orientations must be exactly +1 or -1")
    values = _values(potential, nodes, "Potential trial")
    currents = _values(circulation, edge_ids, "Circulation trial")
    if any(_divergence(parsed, nodes, currents).values()):
        raise ValueError("Circulation trial has nonzero external divergence")
    upper = lower = gap = Fraction(0)
    for identity, first, second, resistance in parsed:
        c = selector.get(identity, Fraction(0))
        z = c - values[first] + values[second]
        k = currents[identity]
        upper += z * z / resistance
        lower += 2 * c * k - resistance * k * k
        gap += resistance * (z / resistance - k) ** 2
    if upper - lower != gap or gap < 0:
        raise ArithmeticError("Exact constitutive mismatch identity failed")
    return {
        "scope": SCOPE,
        "auxiliary_energy_upper_S": upper,
        "auxiliary_energy_lower_S": lower,
        "gap_S": gap,
        "gap_units": "S",
        "potential_units": "dimensionless (normalized unit test EMF)",
        "circulation_units": "S (test current per volt)",
    }


def source_current_bound(edges, cut, potential, circulation, source, source_trial):
    """Return center in A and exact squared error radius in A^2.

    No approximate square root is needed: a proposed interval can enclose the
    nonnegative returned squared radius with separate outward arithmetic.
    Source columns, balances and current/redistribution budgets are external
    to this fixture. An exactly balanced source is never silently inferred.
    """
    witness = cut_current_witness(edges, cut, potential, circulation)
    parsed, nodes, edge_ids = _graph(edges)
    values = _values(potential, nodes, "Potential trial")
    supplied = _values(source, nodes, "External source")
    trial = _values(source_trial, edge_ids, "Source current trial")
    if sum(supplied.values(), Fraction(0)):
        raise ValueError("External source must balance globally")
    if _divergence(parsed, nodes, trial) != supplied:
        raise ValueError("Source current trial does not carry the exact source")
    energy = sum((resistance * trial[identity] ** 2
                  for identity, _, _, resistance in parsed), Fraction(0))
    center = sum((supplied[node] * values[node] for node in nodes), Fraction(0))
    return {
        **witness,
        "center_A": center,
        "source_energy_upper_W": energy,
        "error_radius_squared_A2": witness["gap_S"] * energy,
    }
