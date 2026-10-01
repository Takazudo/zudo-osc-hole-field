"""Conditional PTH wall-mean current to an internal B.Cu annular cut.

The complete finished shell, annular B.Cu sleeve, material bound, and their
dimensions are PROJECT conditions. No native or manufactured geometry is
admitted here. Exterior F/B face fluxes and zero-mean wall flux are separate.
"""
from dataclasses import dataclass
from fractions import Fraction
import math


def _positive(value, name):
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f'{name} must be finite and positive')
    return value


def _up(value):
    result = float(value)
    if not math.isfinite(result):
        raise ValueError('energy coefficient overflow')
    if Fraction.from_float(result) < value:
        result = math.nextafter(result, math.inf)
    return result


@dataclass(frozen=True)
class Geometry:
    inner_radius_mm: float
    shell_outer_radius_mm: float
    land_radius_mm: float
    board_depth_mm: float
    b_foil_thickness_mm: float
    transfer_depth_mm: float

    def checked(self):
        ri = _positive(self.inner_radius_mm, 'inner radius')
        ro = _positive(self.shell_outer_radius_mm, 'shell outer radius')
        radius = _positive(self.land_radius_mm, 'complete B annulus radius')
        length = _positive(self.board_depth_mm, 'board depth')
        band = _positive(self.b_foil_thickness_mm, 'B foil thickness')
        depth = _positive(self.transfer_depth_mm, 'transfer depth')
        if not ri < ro < radius or not 0 < depth < band < length:
            raise ValueError('positive shell, complete annulus, and internal B cut required')
        return ri, ro, radius, length, band, depth


def shell_field(geometry, r_mm, z_mm, current_a):
    """Return (Jr,Jtheta,Jz) in A/mm² on ri<=r<=ro, 0<=z<=L.

    Psi=I/(2*pi*L)*[(1-s)z+s*L*G(z)], s=(r²-ri²)/(ro²-ri²),
    G=max(0,(z-(L-d))/d) in the board interval. Jr=Psi_z/r,
    Jz=-Psi_r/r. Values at z=L-d use the lower one-sided Jr trace;
    Jz is continuous there. The seam has zero measure.
    """
    ri, ro, _, length, _, depth = geometry.checked()
    r = float(r_mm); z = float(z_mm); current = float(current_a)
    if not math.isfinite(current) or not ri <= r <= ro or not 0 <= z <= length:
        raise ValueError('shell sample/current outside conditional domain')
    delta = ro*ro-ri*ri
    s = (r*r-ri*ri)/delta
    active = z > length-depth
    g = 1/depth if active else 0.0
    G = (z-(length-depth))/depth if active else 0.0
    factor = current/(2*math.pi*length)
    return (factor*((1-s)+s*length*g)/r,
            0.0,
            -2*factor*(length*G-z)/delta)


def sleeve_field(geometry, r_mm, z_mm, current_a):
    """Return (Jr,Jtheta,Jz) on ro<=r<=R, L-d<=z<=L.

    Jr=I*(R²-r²)/(2*pi*d*(R²-ro²)*r),
    Jz=I*(z-L)/(pi*d*(R²-ro²)). The cut at z=L-d exports the
    uniform outward profile I/[pi*(R²-ro²)] into remaining B foil.
    """
    _, ro, radius, length, _, depth = geometry.checked()
    r = float(r_mm); z = float(z_mm); current = float(current_a)
    if not math.isfinite(current) or not ro <= r <= radius or not length-depth <= z <= length:
        raise ValueError('sleeve sample/current outside conditional domain')
    delta = radius*radius-ro*ro
    factor = current/(2*math.pi*depth)
    return (factor*(radius*radius-r*r)/(delta*r),
            0.0,
            2*factor*(z-length)/delta)


def resistance_upper(geometry, rho_max_ohm_mm):
    """Outward bound on E/I² in ohms for the disjoint shell+sleeve fields.

    Shell: rho*D/(4*pi*ri²*L)*[max(1,L/d)²+(2*ri*L/D)²].
    Sleeve: rho*D2/(4*pi*d)*[1/ro²+(2*d/D2)²].
    pi>3, so rational denominators use 12. The shell and sleeve are
    disjoint except their shared zero-volume interface; other source/model
    fields that overlap them require cross-energy accounting.
    """
    ri, ro, radius, length, _, depth = geometry.checked()
    rho = _positive(rho_max_ohm_mm, 'maximum resistivity')
    ri, ro, radius, length, depth, rho = (
        Fraction.from_float(x) for x in (ri, ro, radius, length, depth, rho)
    )
    delta = ro*ro-ri*ri
    delta2 = radius*radius-ro*ro
    shell = rho*delta/(12*ri*ri*length) * (
        max(Fraction(1), length/depth)**2 + (2*ri*length/delta)**2
    )
    sleeve = rho*delta2/(12*depth) * (
        1/(ro*ro) + (2*depth/delta2)**2
    )
    return {'shell_ohm_upper': _up(shell),
            'sleeve_ohm_upper': _up(sleeve),
            'total_ohm_upper': _up(shell+sleeve),
            'scope': 'Conditional full wall plus complete B annular sleeve only; no exterior face, zero-mean wall, physical or joined-model acceptance.'}
