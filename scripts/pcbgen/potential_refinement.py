"""Improve a continuous potential witness without changing its energy proof.

Extended-precision residuals choose a better coefficient vector using the same
LU factors. The final stored vector is still an arbitrary admissible H1 trial:
its residual work, source evaluation and matrix-formation allowances must be
recomputed by the caller. No correction is assumed exact or conservative by
itself. The original float64 equation-residual gate remains unchanged.
"""
import numpy as np


def refine(matrix,rhs,factor,extended_matrix=None,initial=None,maximum_corrections=2):
    rhs=np.asarray(rhs,dtype=np.float64)
    field=np.zeros_like(rhs) if initial is None else np.asarray(initial,dtype=np.float64).copy()
    if field.shape!=rhs.shape or matrix.shape!=(len(rhs),len(rhs)) or np.any(field[0]!=0):
        raise ValueError('matching gauge-fixed potential coefficients required')
    if initial is None:field[1:]=factor.solve(rhs[1:])
    before=float(np.max(abs(matrix@field-rhs)))
    residual=before;count=0;accurate_max=None
    # A stricter internal target supplies headroom under the unchanged 1e-8 A
    # acceptance gate. Two corrections bound work even at a gauge/rounding floor.
    while residual>2.5e-9 and count<maximum_corrections:
        if extended_matrix is None:extended_matrix=matrix.astype(np.longdouble)
        accurate=extended_matrix@field.astype(np.longdouble)-rhs.astype(np.longdouble)
        accurate_max=float(np.max(abs(accurate)))
        field[1:]+=factor.solve(np.asarray(-accurate[1:],dtype=np.float64))
        count+=1;residual=float(np.max(abs(matrix@field-rhs)))
    if not np.isfinite(field).all():raise ValueError('potential refinement produced nonfinite coefficients')
    return field,{'corrections':count,'initial_float64_residual_A':before,
                  'final_float64_residual_A':residual,
                  'last_pre_correction_extended_residual_A':accurate_max}
