"""Conditional finite-port composition of two boards and complete wires.

This is a small algebraic diagnostic, not a certified floating-point bound or
an actual K/contact model. Both board operators and compatible physical source
functionals must be supplied explicitly. There is no default ideal K plane.

Applying the identity to current-trial upper matrices requires pointwise matched
normal traces at every joint. Applying it to potential-trial lower matrices
requires continuous matching traces over the entire possible contact support;
matching only a patch average is insufficient. The current bare-PCB GH probes
do not establish those physical lower-trace premises.
"""
import numpy as np


def joined_energy(j, k, j_sources, k_sources, wire_j, wire_k, wire_resistance):
    """Minimize all three constituent energies over internal wire currents.

    Each board matrix uses its own reference terminal. -1 denotes that reference
    in the wire endpoint lists. The first wire must connect the J reference;
    all other J wire endpoints are non-reference terminals. K's reference is
    the balancing external source. Columns of j_sources/k_sources are exact
    external source/measurement functionals, not assumed physical pad shorts.
    """
    j, k, sj, sk = [np.asarray(v, dtype=float) for v in (j, k, j_sources, k_sources)]
    resistances = np.asarray(wire_resistance, dtype=float)
    if j.ndim != 2 or j.shape[0] != j.shape[1] or k.ndim != 2 or k.shape[0] != k.shape[1]:
        raise ValueError('two explicit square board energy operators required')
    if sj.ndim != 2 or sk.ndim != 2 or sj.shape[0] != len(j) or sk.shape != (len(k), sj.shape[1]):
        raise ValueError('incompatible external source functionals')
    if not wire_j or wire_j[0] != -1 or any(i < 0 or i >= len(j) for i in wire_j[1:]):
        raise ValueError('first wire must be the sole J reference wire')
    if len(set(wire_j)) != len(wire_j) or len(wire_k) != len(wire_j) or resistances.shape != (len(wire_j),):
        raise ValueError('wire endpoint identities or energies are inconsistent')
    if any(i < -1 or i >= len(k) for i in wire_k):
        raise ValueError('wire endpoint is outside the explicit K operator')
    if any(not np.isfinite(v).all() for v in (j, k, sj, sk, resistances)) or min(resistances) <= 0:
        raise ValueError('finite constituents and positive paid wire energies required')
    if not np.allclose(j, j.T, rtol=1e-12, atol=1e-15) or not np.allclose(k, k.T, rtol=1e-12, atol=1e-15):
        raise ValueError('symmetric constituent operators required')

    count = len(wire_j) - 1
    pj = np.zeros((len(j), count))
    pk = np.zeros((len(k), count + 1))
    for column, endpoint in enumerate(wire_j[1:]): pj[endpoint, column] = 1.
    for column, endpoint in enumerate(wire_k):
        if endpoint >= 0: pk[endpoint, column] = 1.
    # J reference-wire current is sum(external J injection) - sum(other wires).
    a = np.zeros((count + 1, sj.shape[1])); a[0] = sj.sum(axis=0)
    b = np.vstack((-np.ones((1, count)), np.eye(count)))
    ck = sk + pk @ a
    dk = pk @ b
    d = np.diag(resistances)
    h = sj.T @ j @ sj + ck.T @ k @ ck + a.T @ d @ a
    cross = -sj.T @ j @ pj + ck.T @ k @ dk + a.T @ d @ b
    internal = pj.T @ j @ pj + dk.T @ k @ dk + b.T @ d @ b
    if count:
        # A valid Loewner lower matrix may be indefinite. Stationary elimination
        # is a minimum only when this INTERNAL block is positive definite. Do
        # not silently project a lower matrix to PSD or invert a maximum.
        try:
            factor = np.linalg.cholesky((internal + internal.T) / 2)
        except np.linalg.LinAlgError as error:
            raise ValueError('internal wire-current energy is not positive definite; no finite minimum certified') from error
        currents = -np.linalg.solve(factor.T, np.linalg.solve(factor, cross.T))
    else:
        currents = np.zeros((0, sj.shape[1]))
    energy = h + cross @ currents
    return {'energy': (energy + energy.T) / 2,
            'wire_current_map': a + b @ currents,
            'scope': 'Conditional exact-arithmetic Schur identity only; compatible physical interfaces, actual K bounds and outward numerical allowance are not established by this helper.'}


def open_candidate_current(upper, lower, observation, load_columns, total_absolute_current, candidate_wire_minimum):
    """Thevenin numerator bound; no candidate PCB/contact denominator credit."""
    u, l = np.asarray(upper, dtype=float), np.asarray(lower, dtype=float)
    if not np.isfinite(candidate_wire_minimum) or not np.isfinite(total_absolute_current) or candidate_wire_minimum <= 0 or total_absolute_current < 0:
        raise ValueError('positive candidate wire minimum and nonnegative current norm required')
    if u.ndim != 2 or u.shape[0] != u.shape[1] or l.shape != u.shape or not np.isfinite(u).all() or not np.isfinite(l).all():
        raise ValueError('finite matching paired energy matrices required')
    if not load_columns or observation < 0 or observation >= len(u) or any(i < 0 or i >= len(u) for i in load_columns):
        raise ValueError('explicit observation and nonempty load profile identities required')
    gap = np.diag(u - l)
    if min(gap) < -1e-12:
        raise ValueError('inconsistent compatible energy bounds')
    gap = np.maximum(gap, 0.)
    centres = ((u + l) / 2)[observation, load_columns]
    widths = .5 * np.sqrt(gap[observation] * gap[load_columns])
    voltage = float(max(np.abs(centres) + widths) * total_absolute_current)
    return {'open_voltage_upper_V': voltage,
            'candidate_current_upper_A': voltage / candidate_wire_minimum,
            'candidate_added_PCB_contact_ohm': 0.,
            'alternative_Thevenin_denominator_credit_ohm': 0.,
            'status': 'NOT ACCEPTED: supplied compatible port/operator/current assumptions only'}
