"""Admissible foil correction for arbitrary L2 flux on a convex SMD pad.

The pad extrusion must be entirely actual conductor: no intersecting drill,
slot, missing foil or material interface. Native nominal geometry alone does
not certify a manufactured domain. External source boundaries only.
"""
from fractions import Fraction as F
import math
from scripts.pcbgen.contact_flux_lift import _up, _positive


def domain_bounds(primitive):
    kind=primitive['kind']
    hx,hy=(F(x,1000000) for x in primitive['half_size_nm'])
    if min(hx,hy)<=0:raise ValueError('positive convex source domain required')
    r=F(primitive.get('corner_radius_nm',0),1000000)
    if kind=='rectangle':lo=hi=4*hx*hy
    elif kind=='roundrect':
        if not 0<r<=min(hx,hy):raise ValueError('invalid roundrect source domain')
        # 3 < pi < 22/7, hence rigorous area bounds on the exact primitive.
        lo=4*hx*hy-r*r;hi=4*hx*hy-F(6,7)*r*r
    elif kind=='circle':
        if hx!=hy or r:raise ValueError('invalid circular source domain')
        lo=3*hx*hx;hi=F(22,7)*hx*hx
    else:raise ValueError('unsupported non-convex/unknown source domain')
    diameter2=4*hx*hx if kind=='circle' else 4*(hx*hx+hy*hy)
    return lo,hi,diameter2


def coefficient_bounds(primitive,*,minimum_height_mm,maximum_height_mm,
                       rho_max_ohm_mm,profile_area_min_mm2,drill_free):
    """Separate unit net-profile and unit normalized-redistribution energies.

    q=I/A+g, integral(g)=0, r=sqrt(A)*||g||2. A contained reference profile
    is uniform on S. Delta=q-I*1_S/|S| has zero mean. A Neumann solution
    Delta psi=Delta on D yields Jxy=grad(psi)/h, Jz=-z*Delta/h: no bottom
    or side flux, exact -Delta outward top flux. Payne-Weinberger gives
    integral |grad psi|^2 <= diameter(D)^2/pi^2 * ||Delta||2^2.

    Thus the separate squared energy norms have bounds U_net and U_shape.
    A complete current trial must charge at least the Minkowski envelope
    (sqrt(U_base)+|I|sqrt(U_net)+r*sqrt(U_shape))^2, or a tighter proven Gram.
    Merely adding these diagonal energies would omit overlapping cross terms.
    """
    if drill_free is not True:raise ValueError('source foil slab is not certified drill-free')
    lo,hi,d2=domain_bounds(primitive)
    h0=_positive(minimum_height_mm,'minimum height');h1=_positive(maximum_height_mm,'maximum height')
    rho=_positive(rho_max_ohm_mm,'maximum resistivity');area=_positive(profile_area_min_mm2,'contained profile area')
    if h0>h1 or area>lo:raise ValueError('invalid height or contained profile area')
    # Patch containment is a separate geometric gate, not implied by its area.
    C=max(rho*(h/3+d2/(9*h)) for h in (h0,h1))
    return {'net_to_uniform_profile_energy_ohm_upper':_up(C*(1/area-1/hi)),
            'unit_normalized_redistribution_energy_ohm_upper':_up(C/lo),
            'area_mm2_lower':(math.nextafter(float(lo),-math.inf) if F.from_float(float(lo))>lo else float(lo)),'area_mm2_upper':_up(hi),
            'diameter_squared_mm2_upper':_up(d2),
            'scope':'Conditional convex drill-free actual foil slab and contained profile; superposition cross energy and all physical/current admission remain mandatory.'}
