"""Outward support bound for an admitted observation witness and two budgets.

This helper checks arithmetic and identity coverage, not physical admission.
For a voltage observation, witness energies/gap have units ohm and the result
is volts. For a unit-jump wire-current observation, they have units siemens
and the result is amperes. Source and redistribution energies always have
units ohm. The two independent GLOBAL amplitude budgets have units ampere.
"""
from fractions import Fraction
import math


def rational(value, name, nonnegative=False):
    if isinstance(value, bool) or not isinstance(value, (int, float, str, Fraction)):
        raise ValueError(f'{name}: finite real scalar required')
    try:
        result = Fraction(value)
    except (ValueError, OverflowError, ZeroDivisionError) as exc:
        raise ValueError(f'{name}: finite real scalar required') from exc
    if nonnegative and result < 0:
        raise ValueError(f'{name}: nonnegative value required')
    return result


def sqrt_upper(value):
    """Exact rational upper square root; absolute resolution 2**-80."""
    value = rational(value, 'square root', True)
    scale = 1 << 80
    scaled = value * scale * scale
    ceiling = -(-scaled.numerator // scaled.denominator)
    root = math.isqrt(ceiling)
    if root * root < ceiling:
        root += 1
    return Fraction(root, scale)


def upward(value):
    try:
        result = float(value)
    except OverflowError as exc:
        raise ValueError('observation bound is not representable') from exc
    if not math.isfinite(result):
        raise ValueError('observation bound is not representable')
    if Fraction.from_float(result) < value:
        result = math.nextafter(result, math.inf)
    if not math.isfinite(result):
        raise ValueError('observation bound is not representable')
    return result


def covered_rows(expected_ids, rows, label):
    expected = list(expected_ids)
    rows = list(rows)
    if any(not isinstance(key, str) or not key for key in expected) or len(set(expected)) != len(expected):
        raise ValueError(f'{label}: unique nonempty expected identities required')
    actual = [row.get('id') for row in rows]
    if any(not isinstance(key, str) or not key for key in actual) or len(set(actual)) != len(actual):
        raise ValueError(f'{label}: unique nonempty witness identities required')
    if set(actual) != set(expected):
        raise ValueError(f'{label}: missing or foreign witness identities')
    return {row['id']: row for row in rows}


def support_bound(*, observation_kind, energy_upper, energy_lower,
                  source_ids, sources, redistribution_ids, redistribution,
                  source_budget_A='4.6', redistribution_budget_A='4.6'):
    """Bound an observation using the complete supplied witness identities.

    For each net source i, |T_i - t_i| <= sqrt(gap * U_i).
    For each normalized zero-net shape j, |T_j| <= s_j + sqrt(gap * C_j),
    where s_j bounds ||v - mean(v)||_L2(D_j) / sqrt(area(D_j)).
    One global L1 net-source budget and a separate global shape budget give
    B*max_i(|t_i|+sqrt(gap*U_i)) + G*max_j(s_j+sqrt(gap*C_j)).

    Optional per-source absolute-current caps optimize the first term by a
    fractional-knapsack support calculation. Every cap needs a named evidence
    reference, whose physical validity remains the caller's admission duty.
    Source energies must include the complete balanced current witness, not
    isolated private lift energies. Shape energies cover every allowed shape.
    """
    if observation_kind not in ('voltage', 'wire_current'):
        raise ValueError('unknown observation kind')
    upper = rational(energy_upper, 'witness energy upper', True)
    lower = rational(energy_lower, 'witness energy lower')
    gap = upper - lower
    if gap < 0:
        raise ValueError('inconsistent negative witness gap')
    budget = rational(source_budget_A, 'global source budget', True)
    shape_budget = rational(redistribution_budget_A, 'global redistribution budget', True)
    net = covered_rows(source_ids, sources, 'source')
    shape = covered_rows(redistribution_ids, redistribution, 'redistribution')
    if (budget and not net) or (shape_budget and not shape):
        raise ValueError('nonzero global budget requires complete witnesses')
    ranked = []
    for key, row in net.items():
        try:
            transfer = rational(row['trial_value'], key+' trial value')
            energy = rational(row['source_energy_upper_ohm'], key+' source energy', True)
        except KeyError as exc:
            raise ValueError(key+': missing source witness coefficient') from exc
        cost = abs(transfer) + sqrt_upper(gap * energy)
        cap = budget
        if 'absolute_current_cap_A' in row:
            if not isinstance(row.get('cap_evidence'), str) or not row['cap_evidence'].strip():
                raise ValueError(key+': current cap requires an evidence reference')
            cap = min(budget, rational(row['absolute_current_cap_A'], key+' current cap', True))
        ranked.append((cost, key, cap))
    remaining = budget
    net_bound = Fraction(0)
    allocation = {}
    for cost, key, cap in sorted(ranked, reverse=True):
        used = min(remaining, cap)
        net_bound += used * cost
        remaining -= used
        allocation[key] = upward(used)
    shape_costs = []
    for key, row in shape.items():
        try:
            oscillation = rational(row['trace_oscillation_upper'], key+' trace oscillation', True)
            energy = rational(row['shape_energy_upper_ohm'], key+' shape energy', True)
        except KeyError as exc:
            raise ValueError(key+': missing redistribution witness coefficient') from exc
        shape_costs.append((oscillation + sqrt_upper(gap * energy), key))
    shape_cost, shape_id = max(shape_costs, default=(Fraction(0), None))
    shape_bound = shape_budget * shape_cost
    return {
        'status': 'CONDITIONAL WITNESS SUPPORT ONLY; physical admission not established here',
        'observation_kind': observation_kind,
        'observation_unit': 'V' if observation_kind == 'voltage' else 'A',
        'witness_gap_unit': 'ohm' if observation_kind == 'voltage' else 'siemens',
        'witness_gap_upper': upward(gap),
        'net_source_contribution_upper': upward(net_bound),
        'redistribution_contribution_upper': upward(shape_bound),
        'observation_abs_upper': upward(net_bound + shape_bound),
        'source_ids': sorted(net), 'redistribution_ids': sorted(shape),
        'maximizing_net_amplitudes_A_upper': allocation,
        'maximizing_redistribution_id': shape_id,
        'unspent_source_budget_A_upper': upward(remaining),
        'limitations': [
            'Caller must admit every actual source, support, material and physical interface.',
            'Complete source/shape energies and trace oscillation must be valid outward bounds.',
            'The two budgets are independent global requirements, not per-board allowances.',
            'Additional source correlations are conservatively omitted; cap evidence is not verified here.',
            'No current/voltage limit, canonical board or physical qualification is accepted by this result.',
        ],
    }
