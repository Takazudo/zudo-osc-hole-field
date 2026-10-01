"""Constructive divergence lift from a finite connected cover of real copper.

Cover geometry, exact source partition and positive overlap supports are
mandatory external inputs. No convex hull across a drill is permitted.
The scalar bound includes all overlapping-field cross terms by Young's
inequality; it is intentionally conservative and does not claim acceptance.
"""
from fractions import Fraction as F
from scripts.pcbgen.contact_flux_lift import _positive,_up


def annulus_poincare_upper(inner_radius_mm,outer_radius_mm):
    """L2 zero-mean Poincare constant on a complete annulus (mm²).

    Compare r-weighted variance with the unweighted periodic rectangle in
    (r,theta). The measure ratio is ro/ri, radial constant (ro-ri)²/pi²,
    angular constant ro². pi²>9 gives the stated rational upper.
    """
    ri=_positive(inner_radius_mm,'inner radius');ro=_positive(outer_radius_mm,'outer radius')
    if ro<=ri:raise ValueError('positive annulus width required')
    return _up(ro/ri*max((ro-ri)**2/9,ro**2))


def tangent_cover_radius_squared(inner_radius_mm):
    """Eight exact halfplanes x/y>=a or +/-x+/-y>=1.5a.

    Every halfplane avoids the open radius-a disk (diagonal distance is
    1.5a/sqrt(2)>a). Their complement is the octagon with vertices
    (+/-a,+/-.5a) and (+/-.5a,+/-a), radius²=1.25a². Therefore an actual
    annulus with outer radius²>1.25a² covers every remaining exterior point.
    """
    a=_positive(inner_radius_mm,'inner radius')
    return _up(F(5,4)*a*a)


def cover_poincare_upper(*,local_poincare_mm2,source_area_upper_mm2,
                         parents,overlap_area_lower_mm2):
    """Uniform energy coefficient of a conserved planar mean-zero lift.

    Disjoint source partition S_i subset D_i covers all source support.
    f_i=f*1_S_i and subtree integrals m_i route along the parent tree with
    identical uniform profiles on each actual overlap O_i. Local g_i equals
    f_i plus child profiles minus its outgoing profile, hence integral g_i=0.
    Root is mean-zero by the global source identity, not a numeric tolerance.
    Neumann fields on D_i extended with zero normal flow sum to div J=f;
    overlap source/sink terms cancel exactly. The following rational bound
    applies ||sum J_i||² <= n sum ||J_i||² and
    ||g_i||² <= (1+degree_i)*(||f_i||²+sum_edges |m_e|²/|O_e|),
    with |m_e|²<=A_source*||f||² and ||f_i||²<=||f||².
    """
    n=len(parents)
    if n==0 or len(local_poincare_mm2)!=n or len(overlap_area_lower_mm2)!=n:
        raise ValueError('complete nonempty cover tree required')
    if parents[0]!=-1 or any(not isinstance(p,int) or not 0<=p<i for i,p in enumerate(parents[1:],1)):
        raise ValueError('ordered rooted cover tree required')
    area=_positive(source_area_upper_mm2,'source area')
    local=[_positive(c,'local Poincare constant') for c in local_poincare_mm2]
    overlaps=[None]+[_positive(a,'positive overlap area') for a in overlap_area_lower_mm2[1:]]
    if overlap_area_lower_mm2[0] is not None:raise ValueError('root has no outgoing overlap')
    edges=[[] for _ in parents]
    for i in range(1,n):edges[i].append(overlaps[i]);edges[parents[i]].append(overlaps[i])
    bound=n*sum(c*(1+len(e))*(1+sum(area/a for a in e)) for c,e in zip(local,edges))
    return _up(bound)


def exact_tree_source_balance(source_integrals,parents):
    """Exact rational fixture/constructor of the local overlap source totals."""
    q=[F(x) for x in source_integrals]
    if len(q)!=len(parents) or not q or sum(q)!=0:raise ValueError('exact balanced source required')
    if parents[0]!=-1 or any(not 0<=p<i for i,p in enumerate(parents[1:],1)):raise ValueError('ordered tree required')
    subtree=q.copy()
    for i in range(len(q)-1,0,-1):subtree[parents[i]]+=subtree[i]
    local=q.copy()
    for i in range(1,len(q)):
        local[i]-=subtree[i];local[parents[i]]+=subtree[i]
    if any(local):raise ValueError('local source construction failed')
    return subtree
