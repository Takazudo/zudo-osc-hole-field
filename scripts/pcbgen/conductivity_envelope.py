"""Loewner scaling for a fixed geometry with bounded scalar resistivity.

Unlike entrywise transfer monotonicity, the quadratic-form ordering is valid
for spatially varying conductivity. Geometry, contact functionals and owned
volumes must be the same; foil/drill/registration changes need separate maps.
"""
import numpy as np


def fixed_geometry_bracket(lower,upper,rho_reference,rho_min,rho_max):
    # Scalar NumPy dtypes also control division precision independently of the
    # matrices. Widen represented input values before validating or dividing.
    rho_reference,rho_min,rho_max=map(float,(rho_reference,rho_min,rho_max))
    if not 0<rho_min<=rho_reference<=rho_max:
        raise ValueError('positive material interval must contain the reference resistivity')
    # The outward allowance below encloses float64 operations. In particular,
    # preserve the exact value of an incoming float32 coefficient by widening
    # it before scaling, rather than performing a float32 multiplication.
    L=np.asarray(lower,dtype=np.float64);U=np.asarray(upper,dtype=np.float64)
    if L.shape!=U.shape or L.ndim!=2 or L.shape[0]!=L.shape[1]:
        raise ValueError('matching resistance operators required')
    # Rayleigh quadratic ordering for ALL source combinations supplies
    # (rho_min/rho_ref) R_ref <= R_actual <= (rho_max/rho_ref) R_ref.
    # It does not assert monotonicity of an individual mutual transfer.
    lo=L*(rho_min/rho_reference);hi=U*(rho_max/rho_reference)
    eps=np.finfo(float).eps
    lo-=np.diag(16*eps*np.sum(abs(lo),axis=1))
    hi+=np.diag(16*eps*np.sum(abs(hi),axis=1))
    return lo,hi
