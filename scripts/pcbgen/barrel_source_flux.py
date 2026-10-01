"""Existing plated-shell lift for every mean-zero inner-wall L2 flux.

No solder fill/cap or physical uniform wall injection is assumed. This is one
piece of the external PTH contact construction; annular foil faces and the
net-current reference transfer require their own compatible fields.
"""
import math
from scripts.pcbgen.contact_flux_lift import _positive,_up


def energy_coefficient_upper(*,inner_radius_mm,outer_radius_mm,length_mm,rho_max_ohm_mm):
    """Return C with energy <= C * ||delta||_L2(inner wall)^2.

    Surface coordinates u=ri*theta, z∈[0,L]. Delta psi=delta has periodic u
    and insulated z ends. D=ro²-ri², w=(ro²-r²)/D:
      Jr=ri*delta*w/r, Jtheta=2*r*psi_u/D, Jz=2*ri*psi_z/D.
    Inner outward trace=-delta; outer/end traces=0. Exact cylindrical
    divergence vanishes. Poincare constant <=max(ri²,L²/9), since pi²>9.
    Radial energy coefficient <=ro-ri; the larger tangential coefficient
    is (ro²+ri²)/(ri*D). Exact rational evaluation rounds C outward.
    """
    ri=_positive(inner_radius_mm,'inner radius');ro=_positive(outer_radius_mm,'outer radius')
    length=_positive(length_mm,'length');rho=_positive(rho_max_ohm_mm,'resistivity')
    if ro<=ri:raise ValueError('positive actual plating thickness required')
    delta=ro*ro-ri*ri
    C=rho*((ro-ri)+(ro*ro+ri*ri)/(ri*delta)*max(ri*ri,length*length/9))
    return _up(C)


def net_wall_to_annulus_resistance_upper(*,inner_radius_mm,outer_radius_mm,length_mm,rho_max_ohm_mm):
    """Unit-current trial from the full inner wall to one full exterior annulus.

    With z=0 insulated and z=L the receiving annulus, inner-wall incoming
    density q=I/(2*pi*ri*L), let w=(ro²-r²)/(ro²-ri²). The field
    Jr=q*ri*w/r, Jtheta=0, Jz=2*q*ri*z/(ro²-ri²) is divergence-free. Its
    outward flux is -q at the inner wall, zero at the outer wall and z=0,
    and +I/[pi*(ro²-ri²)] at z=L. Bounding |Jr| by |q| and |Jz| by
    2*|q|*ri*L/D gives the stated energy bound using pi>3. This supplies
    no transfer from the annulus into the rest of the foil.
    """
    ri=_positive(inner_radius_mm,'inner radius');ro=_positive(outer_radius_mm,'outer radius')
    length=_positive(length_mm,'length');rho=_positive(rho_max_ohm_mm,'resistivity')
    if ro<=ri:raise ValueError('positive actual plating thickness required')
    D=ro*ro-ri*ri
    return _up(rho*D/(12*ri*ri*length)*(1+(2*ri*length/D)**2))


def net_wall_to_annulus_mode(r,z,*,inner_radius_mm,outer_radius_mm,length_mm,current):
    """Return (Jr,Jtheta,Jz) for a local unit-test field in cylindrical axes."""
    ri=float(inner_radius_mm);ro=float(outer_radius_mm);length=float(length_mm)
    net_wall_to_annulus_resistance_upper(inner_radius_mm=ri,outer_radius_mm=ro,
                                         length_mm=length,rho_max_ohm_mm=1)
    if not ri<=r<=ro or not 0<=z<=length:raise ValueError('sample outside plated shell')
    D=ro*ro-ri*ri;q=float(current)/(2*math.pi*ri*length)
    w=(ro*ro-r*r)/D
    return q*ri*w/r,0.,2*q*ri*z/D


def mode_field(r,u,z,*,inner_radius_mm,outer_radius_mm,length_mm,amplitude,
               angular_mode=1,axial_mode=1):
    """Explicit Neumann/periodic mode for a meaningful local field fixture."""
    if any(not isinstance(x,int) or x<0 for x in (angular_mode,axial_mode)) or not (angular_mode or axial_mode):
        raise ValueError('nonconstant nonnegative integer mode required')
    ri=float(inner_radius_mm);ro=float(outer_radius_mm);length=float(length_mm)
    energy_coefficient_upper(inner_radius_mm=ri,outer_radius_mm=ro,length_mm=length,rho_max_ohm_mm=1.)
    ku=angular_mode/ri;kz=axial_mode*math.pi/length;k2=ku*ku+kz*kz
    delta=amplitude*math.cos(ku*u)*math.cos(kz*z)
    pu=amplitude*ku*math.sin(ku*u)*math.cos(kz*z)/k2
    pz=amplitude*kz*math.cos(ku*u)*math.sin(kz*z)/k2
    D=ro*ro-ri*ri;w=(ro*ro-r*r)/D
    return ri*delta*w/r,2*r*pu/D,2*ri*pz/D
