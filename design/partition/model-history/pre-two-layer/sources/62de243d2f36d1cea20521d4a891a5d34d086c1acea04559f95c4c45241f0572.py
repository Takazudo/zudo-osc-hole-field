"""Positive diagonal envelope for many small correction-energy quadratics.

For any real M and |x_i|<=b_i, x.T M x <= sum_i d_i b_i², where
 d_i = .5 sum_j (|M_ij|+|M_ji|). This uses 2|x_i x_j|<=x_i²+x_j²;
no numerical symmetry assumption or cancellation is needed.
"""
import numpy as np


def row_envelope(matrix):
    M=np.asarray(matrix,dtype=np.longdouble)
    if M.shape[-1]!=M.shape[-2] or not np.isfinite(M).all():
        raise ValueError('finite square energy matrices required')
    a=abs(M);rows=(a.sum(axis=-1,dtype=np.longdouble)+a.sum(axis=-2,dtype=np.longdouble))/2
    eps=np.finfo(np.longdouble).eps;n=4*M.shape[-1]+8
    gamma=n*eps/(1-n*eps)
    return np.nextafter(rows*(1+gamma),np.longdouble(np.inf))


def diagonal_energy(weights,absolute_bounds):
    """Sum over all field axes, retaining the final independent-profile axis."""
    d=np.asarray(weights,dtype=np.longdouble);b=np.asarray(absolute_bounds,dtype=np.longdouble)
    if b.shape[:-1]!=d.shape or np.any(d<0) or np.any(b<0):
        raise ValueError('positive energy weights and matching absolute bounds required')
    values=d[...,None]*b*b
    axes=tuple(range(d.ndim));result=np.sum(values,axis=axes,dtype=np.longdouble)
    eps=np.finfo(np.longdouble).eps;n=2*d.size+8
    gamma=n*eps/(1-n*eps)
    return np.nextafter(np.asarray(result*(1+gamma),dtype=float),np.inf)


def positive_quadratic_energy(matrix,absolute_bounds):
    """Outward float64 evaluation of the existing absolute quadratic bound.

    All operations after widening are positive, so a standard operation-count
    gamma bound applies without a cancellation premise. This preserves the
    full quadratic enclosure instead of replacing it by a looser diagonal.
    """
    M=np.asarray(matrix,dtype=np.longdouble);b=np.asarray(absolute_bounds,dtype=np.longdouble)
    if M.shape[-1]!=M.shape[-2] or b.shape[:-1]!=M.shape[:-1] or np.any(b<0):
        raise ValueError('matching square matrices and nonnegative bounds required')
    if not np.isfinite(M).all() or not np.isfinite(b).all():raise ValueError('finite energy inputs required')
    # Widen every represented input toward +infinity before the double kernel,
    # including a possible long-double to double conversion rounding downward.
    coefficients=np.nextafter(np.asarray(abs(M),dtype=np.float64),np.inf)
    bounds=np.nextafter(np.asarray(b,dtype=np.float64),np.inf)
    n=M.shape[-1];blocks=int(np.prod(M.shape[:-2]))
    # Keep the two contractions separate: an optimizer must not form b*b
    # first, underflow there, and then amplify that loss by a large M.
    product=np.einsum('...ij,...jb->...ib',coefficients,bounds,optimize=True)
    values=np.einsum('...ib,...ib->b',bounds,product,optimize=True)
    operations=4*blocks*n*n+16
    eps=np.finfo(np.float64).eps
    gamma=operations*eps
    if gamma>=.01 or not np.isfinite(values).all():raise ValueError('positive energy evaluation exceeds arithmetic envelope')
    # Any underflow in the first contraction can be amplified by the second
    # bound. Charge that actual later multiplier, as well as final-stage
    # underflow, before the relative-error denominator. Extended precision
    # prevents the allowance itself from losing tiny*large products.
    tiny=np.nextafter(np.float64(0),np.float64(1))
    underflow=np.longdouble(operations)*np.longdouble(tiny)*(1+np.longdouble(bounds.max()))
    result=(values.astype(np.longdouble)+underflow)/(1-np.longdouble(gamma))
    rounded=np.nextafter(np.asarray(result,dtype=np.float64),np.inf)
    if not np.isfinite(rounded).all():raise ValueError('energy upper cannot be represented in float64')
    return rounded
