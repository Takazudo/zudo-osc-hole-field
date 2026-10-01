"""Finite-energy redistribution for every L2 trace on a rectangular contact.

Geometry/material bounds are project inputs, not manufacturer guarantees.
The returned scalar upper is rounded outward from exact represented inputs.
This helper does not supply a physical lead, a current budget, or model entry.
"""
from fractions import Fraction
import math


def _positive(value, name, allow_zero=False):
    value = float(value)
    if not math.isfinite(value) or value < 0 or (not allow_zero and value == 0):
        raise ValueError(f'{name} must be finite and positive')
    return Fraction.from_float(value)


def _up(value):
    result = float(value)
    if not math.isfinite(result):
        raise ValueError('contact energy overflow')
    if Fraction.from_float(result) < value:
        result = math.nextafter(result, math.inf)
    return result


def energy_upper(*, width_mm, length_mm, height_mm, rho_ohm_mm,
                 net_current_a, redistribution_l2_a_per_mm):
    """Bound rho integral |J|^2 in ohm A^2 (watts).

    A = width * length. Top outward trace is -q, bottom outward trace is
    I/A, q=I/A+g, integral(g)=0, ||g||_L2 <= redistribution_l2_a_per_mm.
    Solve Delta psi=g with insulated sides and zero mean. Then
    Jxy=grad(psi)/h and Jz=-I/A-z*g/h are a conserved admissible field.
    The first nonzero Neumann eigenvalue is pi^2/max(width,length)^2.
    Using pi^2 > 9 gives a rational conservative bound without libm rounding.
    A zero net current does NOT discard nonzero redistribution energy.
    """
    w = _positive(width_mm, 'width')
    l = _positive(length_mm, 'length')
    h = _positive(height_mm, 'height')
    rho = _positive(rho_ohm_mm, 'resistivity')
    current = float(net_current_a)
    if not math.isfinite(current):
        raise ValueError('net current must be finite')
    current = Fraction.from_float(current)
    g = _positive(redistribution_l2_a_per_mm, 'redistribution norm', True)
    uniform = rho * h * current**2 / (w*l)
    redistribution = rho * (h/3 + max(w,l)**2/(9*h)) * g**2
    return {'uniform_energy_w_upper': _up(uniform),
            'redistribution_energy_w_upper': _up(redistribution),
            'total_energy_w_upper': _up(uniform + redistribution),
            'scope': 'Every zero-mean L2 trace within the supplied norm bound on the exact homogeneous contained slab; no physical class or budget inferred.'}


def height_range_upper(*, minimum_height_mm, maximum_height_mm, **kwargs):
    lo = _positive(minimum_height_mm, 'minimum height')
    hi = _positive(maximum_height_mm, 'maximum height')
    if lo > hi:
        raise ValueError('inverted height interval')
    # The complete upper is a*h+b/h with nonnegative a,b, hence convex.
    return max(energy_upper(height_mm=h, **kwargs)['total_energy_w_upper']
               for h in (minimum_height_mm, maximum_height_mm))


def cosine_mode_field(x, z, *, width_mm, length_mm, height_mm,
                      net_current_a, amplitude_a_per_mm2, mode=1):
    """Exact single-mode fixture field; g=amplitude*cos(mode*pi*x/length)."""
    if not isinstance(mode, int) or mode <= 0:
        raise ValueError('positive integer mode required')
    for value in (width_mm, length_mm, height_mm):
        _positive(value, 'dimension')
    k = mode*math.pi/length_mm
    g = amplitude_a_per_mm2*math.cos(k*x)
    return (amplitude_a_per_mm2*math.sin(k*x)/(k*height_mm),
            -net_current_a/(width_mm*length_mm)-g*z/height_mm)
