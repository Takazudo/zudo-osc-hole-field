"""Conditional same-foil drilled-face lift for arbitrary signed L2 traces.

This is a symbolic field contract, not a native-board or material certificate.
An admitted cut needs actual foil, cover, patch, and local Poincare witnesses.
"""

from fractions import Fraction as F
from math import isqrt

from scripts.pcbgen.finite_cover_flux import cover_poincare_upper, exact_tree_source_balance


def _nonnegative(value, name):
    result = F(value)
    if result < 0:
        raise ValueError(f'{name} must be nonnegative')
    return result


def _positive(value, name):
    result = _nonnegative(value, name)
    if not result:
        raise ValueError(f'{name} must be positive')
    return result


def sqrt_upper(value):
    """Rational square-root upper bound on a 10^-12 grid."""
    value = _nonnegative(value, 'radicand')
    scale = 10**12
    floor = isqrt(value.numerator * scale**2 // value.denominator)
    return F(floor if F(floor * floor, scale**2) == value else floor + 1, scale)


def face_field_coefficients(*, current, source_value, return_value, depth, height,
                            face, global_outward_sign):
    """Pointwise formal Jz coefficient at one point; q=source_value on S.

    The in-plane component is grad(psi)/h, where the Neumann solution obeys
    Delta(psi)=q-I*b on D and has zero outward lateral/drill-wall flux.
    """
    i = F(current)
    q = F(source_value)
    b = F(return_value)
    z = _nonnegative(depth, 'depth')
    h = _positive(height, 'height')
    if z > h or b < 0:
        raise ValueError('depth outside slab or negative return density')
    if face not in ('F.Cu', 'B.Cu') or global_outward_sign != (1 if face == 'F.Cu' else -1):
        raise ValueError('face orientation mismatch')
    f = q - i*b
    jz = -i*b - z*f/h
    return {'divergence_jxy': f/h, 'divergence_jz': -f/h,
            'jz_local': jz, 'jz_global': global_outward_sign*jz,
            'exterior_outward': -q if z == h else None,
            'cut_outward': i*b if z == 0 else None,
            'drill_wall_outward': F(0), 'lateral_outward': F(0)}


def conditional_energy_upper(*, current_a, source_l2_a_per_mm,
                             return_patch_area_mm2, source_slab_mm,
                             rho_max_ohm_mm, cover_poincare_mm2):
    """Outward rational bound on rho integral |J|², including cross terms.

    The caller must separately prove the patch is contained in D, the slab
    exists within the actual face foil, and C applies to the entire support
    of f=q-I*b. No board/model admission follows from this number.
    """
    i = F(current_a)
    qnorm = _nonnegative(source_l2_a_per_mm, 'source L2 norm')
    area = _positive(return_patch_area_mm2, 'return patch area')
    h = _positive(source_slab_mm, 'source slab')
    rho = _positive(rho_max_ohm_mm, 'resistivity')
    c = _positive(cover_poincare_mm2, 'cover Poincare bound')
    # Minkowski includes nonzero redistribution when I=0. Both square roots
    # and the final square are computed with exact rationals and outward grids.
    bnorm = sqrt_upper(1/area)
    fnorm_upper = qnorm + abs(i)*bnorm
    amplitude = abs(i)*sqrt_upper(h/area) + fnorm_upper*sqrt_upper(c/h+h/3)
    return {'f_l2_upper_a_per_mm': fnorm_upper,
            'energy_w_upper': rho*amplitude**2,
            'status': 'CONDITIONAL SYMBOLIC ONLY; no actual cut, source, material, or model admission'}


def finite_cover_coefficient(*, local_poincare_mm2, full_f_support_area_upper_mm2,
                             parents, overlap_area_lower_mm2, exact_partition_masses):
    """Demand every cover-tree input and exact total balance before C exists."""
    exact_tree_source_balance(exact_partition_masses, parents)
    return cover_poincare_upper(
        local_poincare_mm2=local_poincare_mm2,
        source_area_upper_mm2=full_f_support_area_upper_mm2,
        parents=parents,
        overlap_area_lower_mm2=overlap_area_lower_mm2,
    )
