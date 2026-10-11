#!/usr/bin/env python3
"""Source-only tolerance study. No CAD, routing, or physical qualification."""
import argparse
from dataclasses import asdict, dataclass
from importlib.metadata import version
import json
import math
from pathlib import Path

import numpy as np
from numpy.polynomial.legendre import leggauss
from scipy.optimize import brentq

import check as base

HERE = Path(__file__).resolve().parent


@dataclass(frozen=True)
class Family:
    offset_mm: float = 58.0
    tail_each_mm: float = 2.5
    anchor_height_nominal_mm: float = 2.0
    anchor_height_range_mm: tuple = (1.95, 2.05)
    face_gap_range_mm: tuple = (24.3, 24.5)
    required_withdrawal_mm: float = 10.0
    stop_travel_range_mm: tuple = (10.0, 10.1)
    free_length_nominal_mm: float = 66.0
    free_length_range_mm: tuple = (65.9, 66.1)
    direction: tuple = (0.5933040689317951, 0.5927989259019525, -0.5445913286478836)
    position_error_max_mm: float = 0.2
    first_derivative_error_max: float = 0.01
    second_derivative_error_max_per_mm: float = 0.002
    minimum_bend_radius_mm: float = 25.908
    gap_cells: int = 200
    length_cells: int = 8
    curve_cells: int = 512

    @property
    def gap_range(self):
        return (self.face_gap_range_mm[0] - 2*self.anchor_height_range_mm[1],
                self.face_gap_range_mm[1] - 2*self.anchor_height_range_mm[0] + self.stop_travel_range_mm[1])


QUADRATURE = {n: ((leggauss(n)[0]+1)/2, leggauss(n)[1]) for n in (96, 192)}


def control(family, gap, handle):
    v0 = np.asarray(family.direction)
    v1 = v0*np.array([1, -1, 1])
    end = np.array([family.offset_mm, 0, -gap])
    tail = family.tail_each_mm
    return np.array([tail*v0, (tail+handle)*v0, end-(tail+handle)*v1, end-tail*v1])


def position(p, t):
    t = np.asarray(t)[:, None]
    return (1-t)**3*p[0] + 3*(1-t)**2*t*p[1] + 3*(1-t)*t*t*p[2] + t**3*p[3]


def first(p, t):
    t = np.asarray(t)[:, None]
    return 3*((1-t)**2*(p[1]-p[0]) + 2*(1-t)*t*(p[2]-p[1]) + t*t*(p[3]-p[2]))


def second(p, t):
    t = np.asarray(t)[:, None]
    return 6*((1-t)*(p[2]-2*p[1]+p[0]) + t*(p[3]-2*p[2]+p[1]))


def arclength(p, order=96):
    t, w = QUADRATURE[order]
    return float(np.sum(w*np.linalg.norm(first(p, t), axis=1))/2)


def handle(family, gap, length):
    return brentq(lambda h: arclength(control(family, gap, h))-length, 0, 80, xtol=1e-12)


def product(a, b, c, d):
    values = np.array([a*c, a*d, b*c, b*d])
    return values.min(axis=0), values.max(axis=0)


def sweep_cell(family, gap0, gap1, handle0, handle1):
    n = family.curve_cells
    t, dt = (np.arange(n)+.5)/n, .5/n
    corners = [control(family, g, h) for g in (gap0, gap1)
               for h in (handle1-1e-7, handle0+1e-7)]
    p = np.array([position(q, t) for q in corners])
    dp = np.array([first(q, t) for q in corners])
    dd = np.array([second(q, t) for q in corners])
    d3 = np.max(np.abs([6*(q[3]-3*q[2]+3*q[1]-q[0]) for q in corners]), axis=0)
    ddlo, ddhi = dd.min(axis=0)-d3*dt-1e-9, dd.max(axis=0)+d3*dt+1e-9
    dmax = np.maximum(abs(ddlo), abs(ddhi))
    lo, hi = dp.min(axis=0)-dmax*dt-1e-9, dp.max(axis=0)+dmax*dt+1e-9
    speed_lower = np.linalg.norm(np.maximum(0, np.maximum(lo, -hi)), axis=1)
    cross = []
    for i, j in ((1, 2), (2, 0), (0, 1)):
        a, b = product(lo[:, i], hi[:, i], ddlo[:, j], ddhi[:, j])
        c, d = product(lo[:, j], hi[:, j], ddlo[:, i], ddhi[:, i])
        cross.append(np.maximum(abs(a-d), abs(b-c)))
    cross_upper = np.linalg.norm(np.asarray(cross).T, axis=1)
    radius = speed_lower**3/np.maximum(cross_upper, 1e-30)
    position_high = p.max(axis=0)+np.maximum(abs(lo), abs(hi))*dt+1e-9
    return float(radius.min()), float(hi[:, 2].max()), float(position_high[:, 1].max())


def calculate(family=Family()):
    for name, expected in [('numpy', '2.2.6'), ('scipy', '1.15.3')]:
        base.need(version(name) == expected, 'numerical environment drift')
    lock = base.read(HERE/'source-lock.json')
    for name, digest in lock['files'].items():
        base.need(base.sha(base.ROOT/name) == digest, 'frozen source drift: '+name)
    base.need(abs(np.linalg.norm(family.direction)-1) < 1e-14, 'direction must be unit length')
    gs = np.linspace(*family.gap_range, family.gap_cells+1)
    lengths = np.linspace(*family.free_length_range_mm, family.length_cells+1)
    hs = np.array([[handle(family, g, length) for length in lengths] for g in gs])
    base.need(np.all(np.diff(hs, axis=0) < 0) and np.all(np.diff(hs, axis=1) > 0), 'root monotonicity failure')
    zero_handle_max = max(arclength(control(family, g, 0)) for g in family.gap_range)
    base.need(zero_handle_max < min(lengths), 'positive rising root not established')
    disagreement = max(abs(arclength(control(family, g, h), 192)-length)
                       for g, row in zip(gs, hs) for length, h in zip(lengths, row))
    base.need(disagreement < 1e-8, 'independent quadrature disagreement')
    radius, max_z, max_y = math.inf, -math.inf, -math.inf
    for j in range(family.gap_cells):
        for k in range(family.length_cells):
            bound, z, y = sweep_cell(family, gs[j], gs[j+1], hs[j, k+1], hs[j+1, k])
            radius, max_z, max_y = min(radius, bound), max(max_z, z), max(max_y, y)
    base.need(max_z < 0, 'nonmonotone Z invalidates gap/root argument')
    eta1, eta2 = family.first_derivative_error_max, family.second_derivative_error_max_per_mm
    base.need(0 <= eta1 < 1 and eta2 >= 0, 'invalid derivative error requirements')
    actual_radius = (1-eta1)**2/(1/radius+eta2)
    vz = -family.direction[2]
    nominal_bridges = 2*family.anchor_height_nominal_mm/vz
    maximum_bridges = 2*max(family.anchor_height_range_mm)/vz
    reference_path_max = float(max(lengths)+2*family.tail_each_mm+maximum_bridges)
    actual_path_max = (1+eta1)*reference_path_max
    cut_range = (84.5, 85.0)
    main_cut_range = (103.5, 104.0)
    preparation_min = 4.5
    remaining = min(cut_range)-actual_path_max
    d = base.read(base.ROOT/'design/partition/partition-input.json')['load_distribution']
    drops = {rail: base.path_drop(amps, d['single_return_max_A'], max(main_cut_range), max(cut_range), d, .0001, .0001)
             for rail, amps in d['rail_max_A'].items()}
    return {
        'status': 'CONDITIONAL SOURCE TOLERANCE STUDY; NOT APPLIED; COLLISIONS AND PHYSICAL QUALIFICATION NOT RUN',
        'source_commit': lock['source_commit'], 'source_lock_sha256': base.sha(HERE/'source-lock.json'),
        'tool_sha256': base.sha(Path(__file__)), 'accepted': False, 'family': asdict(family),
        'datums': {
            'gap_range_mm': list(family.gap_range),
            'derivation': 'Face gap [24.3,24.5] minus independently bounded anchor heights [1.95,2.05], plus continuous withdrawal through an actual stop in [10,10.1].',
            'scope': 'Proposed acceptance requirements, not supplier capabilities. XY offset and fixed tangent are reference values; residual position/tangent/shape errors require the complete C0/C1/C2 bound after datum registration. A common rigid transform does not affect curvature; it DOES affect obstacle clearance.',
        },
        'reference_curve': {
            'radius_lower_bound_mm': radius, 'bend_margin_mm': radius-family.minimum_bend_radius_mm,
            'maximum_Z_derivative_upper_mm': max_z, 'maximum_positive_Y_bow_upper_mm': max_y,
            'handle_range_mm': [float(hs.min()), float(hs.max())],
            'zero_handle_length_max_mm': zero_handle_max, 'quadrature_disagreement_mm': disagreement,
            'method': '200 gap x 8 free-length x 512 curve cells. Cubic derivative/position boxes enclose the gap/handle rectangle; convex length in handle and negative Z derivative establish the positive rising root and its ordering. Handles have 1e-7 mm padding; arithmetic has 1e-9 padding. Floating engineering bounds, not certified directed interval arithmetic.',
        },
        'actual_shape_requirement': {
            'radius_lower_bound_if_requirements_hold_mm': actual_radius,
            'bend_margin_if_requirements_hold_mm': actual_radius-family.minimum_bend_radius_mm,
            'registration': 'q(s)=r(s)+e(s), with s the reference centerline arclength, including both straight tails and bridges. Require global C1 matching and piecewise C2 bounds, including transitions at both collet exits.',
            'derivation': '|q_s|>=1-eta1 and |q_ss|<=1/R_reference+eta2 imply curvature<= (1/R_reference+eta2)/(1-eta1)^2.',
            'qualification': 'C0 position error alone does not bound curvature. Fixture, endpoint-axis, collet-exit strain transition, insulation, formed-wire equilibrium and the complete continuous actual centerline must be qualified against C1/C2 requirements. Actual material length must stay constant through withdrawal; eta1 is a reference-shape comparison, not permission to stretch wire. A point-cloud or position-tube check alone cannot pass this gate.',
        },
        'cut_and_preparation': {
            'nominal_two_bridge_length_mm': nominal_bridges, 'maximum_two_bridge_length_mm': maximum_bridges,
            'reference_complete_path_upper_mm': reference_path_max,
            'actual_complete_path_upper_if_C1_holds_mm': actual_path_max,
            'new_cut_nominal_mm': 84.75, 'new_cut_tolerance_mm': .25, 'new_cut_range_mm': list(cut_range),
            'main_cut_nominal_mm': 103.75, 'main_cut_tolerance_mm': .25, 'main_cut_range_mm': list(main_cut_range),
            'required_other_preparation_min_mm': preparation_min,
            'other_preparation_at_shortest_cut_and_longest_path_mm': remaining,
            'preparation_headroom_mm': remaining-preparation_min,
            '84mm_cut_other_preparation_before_cut_undersize_mm': 84-actual_path_max,
            'scope': 'Lengths pay both bridges once and allow up to 1% C1 arclength growth of the entire new-wire path. Preparation is reserved outside that path, not available service slack. Existing main-cut qualification is an independent prerequisite; this study does not apply the new-wire shape certificate to main wires.',
        },
        'joined_budget': {
            'global_rail_target_ohm': .0001, 'global_return_target_ohm': .0001,
            'drops_mV_if_all_requirements_hold': drops, 'minimum_margin_mV': 20-max(drops.values()),
            'scope': 'Targets are stricter than existing global ceilings, charged once, with original hot-wire/contact/current assumptions. No realized copper extraction or new-main cut qualification is claimed.',
        },
        'gates': {
            'reference_radius_arithmetic': radius > family.minimum_bend_radius_mm,
            'conditional_C1_C2_radius_arithmetic': actual_radius > family.minimum_bend_radius_mm,
            'conditional_preparation_arithmetic': remaining >= preparation_min,
            'conditional_electrical_arithmetic': max(drops.values()) < 20,
            'new_geometry_collision_sweep': False, 'new_carrier_geometry': False,
            'actual_C0_C1_C2_qualification': False, 'actual_cut_and_preparation_qualification': False,
            'existing_main_cut_qualification': False, 'actual_copper': False,
            'face_contract': False, 'physical_fit': False, 'all_100_trim_access': False, 'native': False,
        },
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--check', action='store_true')
    args = parser.parse_args()
    result = calculate()
    text = json.dumps(result, indent=2, sort_keys=True)+'\n'
    target = HERE/'robust-curve.json'
    if args.check:
        base.need(target.read_text() == text, 'robust curve evidence drift')
    else:
        target.write_text(text)
    print(json.dumps({'reference': result['reference_curve']['radius_lower_bound_mm'],
                      'conditional_actual': result['actual_shape_requirement']['radius_lower_bound_if_requirements_hold_mm'],
                      'preparation_headroom': result['cut_and_preparation']['preparation_headroom_mm'],
                      'gates': result['gates']}))


if __name__ == '__main__':
    main()
