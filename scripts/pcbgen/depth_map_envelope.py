"""Exact-rational metric bounds for a conditional piecewise depth map.

No manufacturing class is selected here. All x/y domains, holes, source
supports and material identities must be unchanged, and EVERY conducting
volume must be mapped by the same continuous, strictly increasing z map.
This includes foil/barrel/collar interfaces. Independent solder/contact/wire
terms, etch, registration, radial plating and drill changes are not covered.
"""
from fractions import Fraction
import math


def positive(value):
    value=float(value)
    if not math.isfinite(value) or value<=0:
        raise ValueError('positive finite represented input required')
    return Fraction(value)


def text(value):
    return str(value.numerator)+'/'+str(value.denominator)


def bounds(nominal_heights,actual_height_intervals,rho_reference,rho_min,rho_max):
    """Return exact factors as rational strings, without floating certification.

    D F = diag(1,1,lambda). The Piola current field is
    J_new(F(x)) = D F J_old(x)/det(D F). Its resistive metric is
    diag(1/lambda,1/lambda,lambda). The pulled-back potential metric
    is diag(lambda,lambda,1/lambda). Full interface normal flux and
    pointwise potential traces remain compatible under the SAME map.
    Volumetric sources map as q/lambda; boundary sources map as flux
    measures. The band sequence must be contiguous and cover every mapped
    conductor, including barrel segments across dielectric bands.
    """
    if not nominal_heights or len(nominal_heights)!=len(actual_height_intervals):
        raise ValueError('matching nonempty ordered band intervals required')
    reference,minimum,maximum=map(positive,(rho_reference,rho_min,rho_max))
    if not minimum<=reference<=maximum:
        raise ValueError('material interval must contain nominal resistivity')
    rows=[];global_metric=Fraction(1);low_total=Fraction(0);high_total=Fraction(0)
    for height,interval in zip(nominal_heights,actual_height_intervals):
        if len(interval)!=2:raise ValueError('two interval endpoints required')
        nominal=positive(height);low,high=map(positive,interval)
        if not low<=nominal<=high:
            raise ValueError('positive thickness interval must contain its nominal band')
        a,b=low/nominal,high/nominal
        metric=max(b,1/a)
        global_metric=max(global_metric,metric)
        low_total+=low;high_total+=high
        rows.append({'stretch_lower_exact':text(a),'stretch_upper_exact':text(b),
            'metric_eigenvalue_lower_exact':text(1/metric),
            'metric_eigenvalue_upper_exact':text(metric)})
    return {'status':'UNSELECTED conditional map theorem; actual class and matrix application NOT RUN',
        'bands':rows,'global_metric_upper_exact':text(global_metric),
        'resistance_operator_lower_factor_exact':text(minimum/reference/global_metric),
        'resistance_operator_upper_factor_exact':text(maximum/reference*global_metric),
        'sum_actual_height_interval_mm_exact':[text(low_total),text(high_total)],
        'ordering':'For every compatible source combination, lower_factor * R_nominal <= R_mapped <= upper_factor * R_nominal in Loewner order. This is not entrywise mutual-transfer monotonicity.',
        'premises':'All conductor volumes and source/observation functionals mapped together; positive isotropic resistivity bounds on every mapped conductor. Constant physical outer-face x/y supports have unchanged normal flux under this depth-only map. The actual total thickness must separately meet the selected mechanical contract.'}
