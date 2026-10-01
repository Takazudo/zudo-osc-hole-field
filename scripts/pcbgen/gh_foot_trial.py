"""Conserved finite rectangular contact redistribution trial.

This is a mathematical template, not a JST geometry or material guarantee.
A physical use must establish a contained conducting slab and matching normal
traces at its real boundaries. Uniform trial currents are not assumed actual
current densities. All dimensions are mm and resistivity is ohm mm.
The formulas are real-arithmetic trials; returned floating values are diagnostic
and need a numerical enclosure before use in an authoritative certificate.
"""
import math
import numpy as np


def validate(width,length,inlet_length,inlet_start,height,rho):
    values=(width,length,inlet_length,inlet_start,height,rho)
    if any(not math.isfinite(v) for v in values) or min(width,length,inlet_length,height,rho)<=0:
        raise ValueError('positive finite contact dimensions and resistivity required')
    if inlet_start<0 or inlet_start+inlet_length>length:
        raise ValueError('inlet must be contained in the contact slab')


def field(x,z,*,width,length,inlet_length,inlet_start,height):
    """Unit current enters a top rectangle and leaves the whole bottom.

    The slab has width in y, length in x and thickness in z. CDF differences
    give continuous Jx across inlet edges; Jy is zero. Divergence vanishes
    pointwise away from the two harmless tangential discontinuities.
    """
    validate(width,length,inlet_length,inlet_start,height,1.)
    x=np.asarray(x);z=np.asarray(z)
    f=np.where((x>inlet_start)&(x<inlet_start+inlet_length),1/(width*inlet_length),0.)
    g=1/(width*length)
    j=(np.clip(x-inlet_start,0,inlet_length)/inlet_length-x/length)/width
    return j/height,-g-(f-g)*z/height


def energy(*,width,length,inlet_length,inlet_start,height,rho):
    validate(width,length,inlet_length,inlet_start,height,rho)
    displacement=inlet_start-(length-inlet_length)/2
    lateral=rho*((length-inlet_length)**2/12+displacement**2)/(width*height*length)
    normal=rho*height/(3*width)*(1/inlet_length+2/length)
    return {'lateral_ohm':lateral,'normal_ohm':normal,'total_ohm':lateral+normal,
        'scope':'Admissible current trial only for the stated contained slab and matching inlet/outlet traces; no physical contact qualification.'}


def height_interval_upper(*,minimum_height,maximum_height,**kwargs):
    if not 0<minimum_height<=maximum_height:raise ValueError('positive bounded contact height required')
    # a/h+b*h is convex; its maximum on a closed interval is at an endpoint.
    endpoints=[energy(height=h,**kwargs) for h in (minimum_height,maximum_height)]
    return max(r['total_ohm'] for r in endpoints)
