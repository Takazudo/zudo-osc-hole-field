"""Variational metric bounds for a finite positive copper/stack class.

Reference depth intervals map affinely to actual foil/dielectric intervals.
The optional radial map is monotone and shares its endpoint traces with the
foil collar. Registration/XY ownership are separate geometry obligations.
"""
import numpy as np


def cylindrical_bounds(radius,theta_derivative,radial_scale,depth_scale,rho):
    """Return energy suprema for mapped RT currents and Q1 potentials.

    Coordinates are polygon arclength u, reference radius r and reference z.
    Physical cylindrical radius R(r), depth Z(z) give Jacobian R theta' R' Z'.
    All intervals must bound the same positive actual map. Independent extrema
    are conservative, even when geometry constraints correlate their values.
    """
    intervals=(radius,theta_derivative,radial_scale,depth_scale,rho)
    if any(not (0<float(lo)<=float(hi)<np.inf) for lo,hi in intervals):
        raise ValueError('material map requires finite positive intervals')
    r0,r1=radius;t0,t1=theta_derivative;q0,q1=radial_scale;s0,s1=depth_scale;p0,p1=rho
    current=p1*np.array([r1*t1/(q0*s0),q1/(r0*t0*s0),s1/(r0*t0*q0)])
    potential=np.array([q1*s1/(r0*t0),r1*t1*s1/q0,r1*t1*q1/s0])/p0
    return np.nextafter(current,np.inf),np.nextafter(potential,np.inf)


def depth_scales(reference_boundaries,actual_interval_lengths):
    """One positive affine scale interval for every foil and dielectric band."""
    reference=np.asarray(reference_boundaries,dtype=float)
    if len(actual_interval_lengths)!=len(reference)-1 or np.any(np.diff(reference)<=0):
        raise ValueError('stack intervals do not match increasing reference boundaries')
    scales=[]
    for length,(lo,hi) in zip(np.diff(reference),actual_interval_lengths):
        if not 0<lo<=hi:raise ValueError('actual stack interval has nonpositive thickness')
        scales.append((float(lo/length),float(hi/length)))
    return scales
