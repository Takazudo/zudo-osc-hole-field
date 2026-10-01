"""Finite prospective GH reference-cell current construction, not hardware admission.

All arithmetic is exact rational until outward display conversion. Components
occupy disjoint volume interiors; normal traces match, so their energies add
without omitted cross terms. The crimp/strand slabs include their mean and
zero-mean fields and exploit their proved orthogonality, not a diagonal guess.

The reference cell requires a continuous crimp hub whose existence in the
exact JST contact is NOT KNOWN. Passing its energy and external-envelope
screens does not establish internal geometry compatibility or select a source.
"""
from fractions import Fraction as F
import hashlib
import json
from pathlib import Path

from scripts.pcbgen.observation_support_bound import upward


ROOT = Path(__file__).resolve().parents[2]
PROPOSAL = ROOT / "design/partition/gh-contact-cell-proposal.json"


def interval(value):
    if not isinstance(value, list) or len(value) != 2:
        raise ValueError("Explicit two-endpoint interval required")
    lo, hi = (F(x) for x in value)
    if not 0 < lo < hi:
        raise ValueError("Finite positive nonzero-width interval required")
    return lo, hi


def rectangle_integral_upper(a0, b0, a1, b1, subdivisions=128):
    """Upper integral of 1/(a(t)b(t)) for linearly varying positive sides.

    On each subinterval bound each affine side by its smaller endpoint.
    This is valid for expansion, contraction and opposite-slope sides.
    """
    if subdivisions < 1 or min(a0, b0, a1, b1) <= 0:
        raise ValueError("Positive rectangle and subdivision count required")
    total = F(0)
    for i in range(subdivisions):
        left, right = F(i, subdivisions), F(i + 1, subdivisions)
        amin = min(a0 + (a1 - a0) * left, a0 + (a1 - a0) * right)
        bmin = min(b0 + (b1 - b0) * left, b0 + (b1 - b0) * right)
        total += 1 / (subdivisions * amin * bmin)
    return total


def taper_upper(a0, b0, a1, b1, length, rho, offset=(F(0), F(0))):
    """Piola current in an affine rectangular taper, including centre shift.

    For x=cx(z)+a(z)*xi, y=cy(z)+b(z)*eta, xi,eta in [-1/2,1/2],
    J=I/(a*b)*(cx'+a'*xi, cy'+b'*eta, 1). Its divergence vanishes,
    side normal flux is zero and end normal profiles are uniform I/(a*b).
    The cross-section average squared slope is cx'^2+cy'^2+(a'^2+b'^2)/12.
    Interval minima bound the inverse area and interval extrema bound slopes.
    """
    if min(a0[0], b0[0], a1[0], b1[0], length[0], rho) <= 0:
        raise ValueError("Positive finite taper dimensions/material required")
    da = max(abs(a1[1] - a0[0]), abs(a1[0] - a0[1]))
    db = max(abs(b1[1] - b0[0]), abs(b1[0] - b0[1]))
    shape = 1 + (offset[0] ** 2 + offset[1] ** 2 + (da ** 2 + db ** 2) / 12) / length[0] ** 2
    inverse_area = rectangle_integral_upper(a0[0], b0[0], a1[0], b1[0])
    return rho * length[1] * inverse_area * shape


def corner_upper(width, incoming_length, height, rho):
    """Exact RT0 90-degree turn bounded across its positive box intervals.

    In [0,a]x[0,b]x[0,h], J=(0,I*y/(a*b*h),I*(1-z/h)/(a*b)).
    The bottom receives uniform I/(a*b); y=b emits uniform I/(a*h).
    Other faces are insulated and divergence is zero. Reversal and rigid
    rotation supply the second toe corner without changing energy.
    """
    a, b, h = width, incoming_length, height
    return rho * (h[1] / (3 * a[0] * b[0]) + b[1] / (3 * a[0] * h[0]))


def slab_upper(area_lo, area_hi, diameter2_hi, height, patch_total_area_lo, rho,
               normalized_profile_l2_squared_upper=None):
    """Uniform whole-section mean to uniform finite patch union on one face.

    J_mean and zero-mean Neumann correction are energy-orthogonal: the
    correction's vertical cross-section integral is zero at each depth.
    E/I^2 <= rho*h/A + rho*(h/3+d^2/(9h))*(1/S-1/A).
    pi^2>9 is used. The section is a real convex solid slab; patch locations
    are contained and nonoverlapping by a separate exact geometry check.
    """
    if not 0 < patch_total_area_lo <= area_lo <= area_hi:
        raise ValueError("Positive contained finite patch area required")
    coefficient = rho * max(h / 3 + diameter2_hi / (9 * h) for h in height)
    profile_norm = (1/patch_total_area_lo if normalized_profile_l2_squared_upper is None
                    else normalized_profile_l2_squared_upper)
    if profile_norm < 1/area_hi:
        raise ValueError("Source profile norm contradicts its unit integral")
    return rho * height[1] / area_lo + coefficient * (profile_norm - 1 / area_hi)


def maximum_weight_square_sum(ratio, count=7):
    """Bound optimized weights for strand unit-energy ratios <= ratio.

    Each weight lies in [1/(1+(n-1)ratio), ratio/(ratio+n-1)]. Maximizing the
    convex sum of squares over that box and sum=1 fills its largest entries
    to the upper endpoint, with at most one fractional remainder.
    """
    if ratio < 1 or count < 2:
        raise ValueError("Positive strand count and ratio >=1 required")
    low, high = 1/(1+(count-1)*ratio), ratio/(ratio+count-1)
    weights = [low]*count
    remaining = 1-count*low
    for i in range(count):
        extra = min(high-low, remaining)
        weights[i] += extra
        remaining -= extra
    if remaining:
        raise ArithmeticError("Strand weight envelope is infeasible")
    return sum(x*x for x in weights)


def bulk_class_admission(spec, strands):
    """Construct upper/lower bulk witnesses and the actual trial weights.

    Each actual metal section contains its core circle and is contained by a
    1.01-times-radius circle, allowing finite noncircular shape tolerances.
    Independent radius and axial resistivity bounds apply per strand. Complete
    normal-frame path and maximum-metal hypotheses are prospective premises.
    Cold/hot conditions are direct material bounds, not invented temperatures.
    """
    p = {key: interval(value) for key, value in spec["intervals"].items()}
    contract = spec["bulk_correlated_class"]
    length = F(contract["current_strand_arclength_over_axis_upper"])
    bend = F(contract["current_core_radius_times_curvature_upper"])
    spin = F(contract["current_frame_spin_upper_rad_per_mm"])
    potential_bend = F(contract["potential_bundle_curvature_times_metal_radius_upper"])
    if not 0 <= bend < 1 or not 0 <= potential_bend < 1 or length < 1 or spin <= 0:
        raise ValueError("Finite nondegenerate current/potential curve class required")
    metric = length*(1+spin**2*p["contained_strand_radius"][1]**2/(1-bend))
    axis_area = F(contract["potential_axis_section_area_over_normal_section_upper"])
    if axis_area < 1:
        raise ValueError("Actual-axis metal area factor must be at least one")
    potential_metric = axis_area/(1-potential_bend)
    outer_ratio = F(contract["actual_radius_over_contained_radius_upper"])
    if outer_ratio <= 1:
        raise ValueError("Finite positive actual-metal shape tolerance required")
    area0 = polygon_area(polygon(spec))
    r0 = p["contained_strand_radius"][0]
    if len(strands) != 7:
        raise ValueError("Every one of seven actual strand parameter sets is required")
    resistances, conductance_terms = [], []
    for row in strands:
        radius, lo, hi = (F(row[key]) for key in ("radius_mm", "rho_lower_ohm_mm", "rho_upper_ohm_mm"))
        if not r0 <= radius <= p["contained_strand_radius"][1] or not p["rho_wire"][0] <= lo <= hi <= p["rho_wire"][1]:
            raise ValueError("Strand parameter escapes declared physical intervals")
        area = area0*(radius/r0)**2
        resistances.append(hi*metric/area)
        conductance_terms.append(F(22,7)*(outer_ratio*radius)**2/lo)
    inverse = sum(1/r for r in resistances)
    weights = [(1/r)/inverse for r in resistances]
    upper = 1000/inverse
    lower = 1000/(potential_metric*sum(conductance_terms))
    ratio = max(resistances)/min(resistances)
    ratio_limit = F(contract["strand_unit_energy_ratio_upper"])
    accepted = (upper <= F(contract["wire_resistance_upper_ohm_per_m"])
                and lower >= F(contract["wire_resistance_lower_ohm_per_m"])
                and ratio <= ratio_limit)
    if accepted and sum(a*a for a in weights) > maximum_weight_square_sum(ratio_limit):
        raise ArithmeticError("Computed strand weights violate their proved envelope")
    return {"admissible_correlated_parameters": accepted,
            "current_metric_upper": metric, "potential_metric_upper": potential_metric,
            "bulk_upper_ohm_per_m": upper, "bulk_lower_ohm_per_m": lower,
            "strand_weights": weights, "strand_unit_energy_ratio": ratio,
            "weight_square_sum_upper": maximum_weight_square_sum(ratio_limit)}


def polygon(spec):
    quadrant = [(F(x), F(y)) for x, y in spec["geometry"]["strand_polygon_first_quadrant"]]
    points = []
    for turn in range(4):
        for x, y in quadrant[:-1]:
            for _ in range(turn):
                x, y = -y, x
            points.append((x, y))
    return points


def polygon_area(points):
    return sum((x * v - y * u for (x, y), (u, v)
                in zip(points, points[1:] + points[:1])), F(0)) / 2


def toe_body_centres(p, geometry):
    """The taper starts on the second corner and ends on the body spine."""
    toe, body = (F(geometry[key]) for key in ("toe_projection", "body_front_y"))
    return (tuple(toe + h/2 for h in p["toe_height"]),
            tuple(body + b/2 for b in p["body_depth"]))


def displacement_upper(start, end):
    return max(abs(end[1]-start[0]), abs(end[0]-start[1]))


def required_envelopes(spec, p, centres):
    """Enclose every reference solid and all permitted outgoing strand metal.

    Each taper is affine, so endpoint extrema enclose its complete sides.
    The sequential z interfaces already share the same cumulative parameters.
    Full possible pad wetting is a separate constant-potential support at z=0;
    its rectangle is centred on the native pad. Required minimum wetting shares
    the current patch's x centre and starts at y=0.
    """
    g=spec["geometry"]
    minimum=[F(x) for x in g["minimum_allowed_solder_support"]]
    maximum=[F(x) for x in g["maximum_wetting_native_pad"]]
    if len(minimum)!=2 or len(maximum)!=2 or min(minimum+maximum)<=0:
        raise ValueError("Positive two-dimensional solder/wetting supports required")
    if minimum[0]>maximum[0] or minimum[1]>maximum[1]/2:
        raise ValueError("Required solder support escapes full possible pad wetting")
    toe, body, axis = (F(g[key]) for key in ("toe_projection","body_front_y","wire_axis_y"))
    outer=F(spec["bulk_correlated_class"]["actual_radius_over_contained_radius_upper"])
    if outer<=1:
        raise ValueError("Finite positive actual-metal shape tolerance required")
    radius=outer*p["contained_strand_radius"][1]
    half_x=max(p[key][1] for key in ("toe_width","body_width","mating_patch_width","hub_width"))/2
    half_y=max(p[key][1] for key in ("body_depth","mating_patch_depth","hub_width"))/2
    required={
        "x":(min(-half_x,-minimum[0]/2,*(x-radius for x,y in centres)),
             max(half_x,minimum[0]/2,*(x+radius for x,y in centres))),
        "y":(min(F(0),toe,body,axis-half_y,*(axis+y-radius for x,y in centres)),
             max(minimum[1],p["solder_patch_length"][1],toe+p["toe_height"][1],
                 body+p["body_depth"][1],axis+half_y,*(axis+y+radius for x,y in centres))),
        "z":(F(0),F(g["wire_cut_z"])),
    }
    box=g["maximum_possible_metal_box"]
    if not isinstance(box,dict) or set(box)!={"x","y","z"}:
        raise ValueError("Complete three-dimensional maximum metal envelope required")
    for key,(lo,hi) in required.items():
        bounds=box[key]
        if not isinstance(bounds,list) or len(bounds)!=2:
            raise ValueError("Two ordered maximum metal coordinates required")
        a,b=map(F,bounds)
        if not a<b or a>lo or b<hi:
            raise ValueError("Required reference/strand metal escapes maximum envelope: "+key)
    return {"required_metal_envelope_mm":{key:list(map(str,value)) for key,value in required.items()},
            "full_possible_wetting_xy_mm":[str(-maximum[0]/2),str(-maximum[1]/2),
                                            str(maximum[0]/2),str(maximum[1]/2)]}


def geometry_checks(spec):
    if spec.get("physical_model") != {"continuous_solid_crimp_hub_required": True,
                                       "interface_law": "finite_patch_local_robin", "strand_count": 7}:
        raise ValueError("Explicit full solid hub, finite-patch local law and seven strands required")
    p = {key: interval(value) for key, value in spec["intervals"].items()}
    g = spec["geometry"]
    points = polygon(spec)
    radius = p["contained_strand_radius"][0]
    if any(x*x + y*y > radius*radius for x, y in points):
        raise ValueError("Strand polygon escapes its required contained copper core")
    # Convexity and patch containment are exact half-plane tests.
    corners = [(sx * p["crimp_patch_width"][1] / 2, sy * p["crimp_patch_width"][1] / 2)
               for sx in (-1, 1) for sy in (-1, 1)]
    for i, (x, y) in enumerate(points):
        u, v = points[(i + 1) % len(points)]
        if any((u-x)*(b-y)-(v-y)*(a-x) < 0 for a, b in points + corners):
            raise ValueError("Convex strand section or contained crimp patch failed")
    centres = [(F(x), F(y)) for x, y in g["strand_centres"]]
    if len(centres) != 7 or len(set(centres)) != 7:
        raise ValueError("Seven distinct explicit strand roots required")
    for i, (x, y) in enumerate(centres):
        for u, v in centres[i+1:]:
            # All possible complete strand cores, not only current polygons.
            outer = F(spec["bulk_correlated_class"]["actual_radius_over_contained_radius_upper"])
            if (x-u)**2 + (y-v)**2 <= (2*outer*p["contained_strand_radius"][1])**2:
                raise ValueError("Finite strand core envelopes touch or overlap")
        if max(abs(x), abs(y)) + p["crimp_patch_width"][1]/2 > p["hub_width"][0]/2:
            raise ValueError("Crimp patches escape the minimum continuous hub")
    # The shared interface patch is finite and smaller than both adjoining
    # conductor end faces. Its two neighbours use precisely that same patch.
    if p["mating_patch_width"][1] > p["body_width"][0] or p["mating_patch_depth"][1] > p["body_depth"][0]:
        raise ValueError("Mating patch escapes its metal spine")
    minimum_support = [F(x) for x in g["minimum_allowed_solder_support"]]
    if p["toe_width"][1] > minimum_support[0] or p["solder_patch_length"][1] > minimum_support[1]:
        raise ValueError("Foil/solder current patch escapes minimum solder support")
    toe_projection = F(g["toe_projection"])
    if p["solder_patch_length"][1] >= toe_projection:
        raise ValueError("No positive horizontal toe remains")
    # Two corner boxes share the same vertical interval: they do not add two
    # toe heights. The mating interface is a finite-area zero-thickness law.
    vertical_terms = ["solder_height", "toe_height", "body_taper_length",
                      "header_spine_length", "receiver_spine_length",
                      "hub_taper_length", "hub_height", "strand_tip_length"]
    zlo = sum(p[key][0] for key in vertical_terms) + 2*p["mating_taper_length"][0]
    zhi = sum(p[key][1] for key in vertical_terms) + 2*p["mating_taper_length"][1]
    if zhi >= F(g["maximum_mated_metal_z"]) or F(g["maximum_mated_metal_z"]) >= F(g["wire_cut_z"]):
        raise ValueError("Positive outgoing wire collar does not fit its envelope")
    # Primary external screen only: pitch=1.25 mm, body front at y=.7,
    # depth=4.25 mm, body nominal height=7.3 mm. The actual internal cavity is
    # not known, so these checks deliberately cannot set physical admission.
    if p["hub_width"][1] >= F("1.25") or zhi >= F("7.3"):
        raise ValueError("Reference solids exceed primary gross pitch/height")
    if p["hub_width"][1] >= F("0.55"):
        raise ValueError("Reference hub exceeds the drawing's smaller contact cross-envelope")
    if F(g["wire_axis_y"]) - p["hub_width"][1]/2 < F(g["body_front_y"]) or F(g["wire_axis_y"]) + p["hub_width"][1]/2 > F(g["body_front_y"])+F("4.25"):
        raise ValueError("Reference hub escapes gross header depth")
    if p["toe_height"][1] + p["solder_height"][1] > F("0.15"):
        raise ValueError("Toe and solder exceed nominal drawing toe height")
    envelopes=required_envelopes(spec,p,centres)
    return p, points, {**envelopes,"strand_polygon_area_mm2": polygon_area(points),
                       "metal_before_outgoing_collar_z_mm": [zlo, zhi],
                       "wire_tail_length_mm": [F(g["wire_cut_z"])-zhi, F(g["wire_cut_z"])-zlo],
                       "gross_external_envelope_screen": "PASS for constructed reference only",
                       "actual_internal_metal_containment": "NOT RUN; continuous crimp hub is unverified"}


def evaluate(spec=None, verify_sources=True):
    spec = json.loads(PROPOSAL.read_text()) if spec is None else spec
    if verify_sources:
        for source in spec["sources"]:
            if hashlib.sha256((ROOT/source["path"]).read_bytes()).hexdigest() != source["sha256"]:
                raise ValueError("Retained primary source changed: "+source["path"])
    p, points, geometry = geometry_checks(spec)
    ra, rs, rw = (p[key][1] for key in ("rho_alloy", "rho_solder", "rho_wire"))
    a, b, h = p["toe_width"], p["solder_patch_length"], p["toe_height"]
    ba, bb = p["body_width"], p["body_depth"]
    ma, mb = p["mating_patch_width"], p["mating_patch_depth"]
    hub = p["hub_width"]
    area = geometry["strand_polygon_area_mm2"]
    patch = p["crimp_patch_width"]
    weight_square = maximum_weight_square_sum(F(spec["bulk_correlated_class"]["strand_unit_energy_ratio_upper"]))
    q = {}
    q["solder_volume"] = rs*p["solder_height"][1]/(a[0]*b[0])
    q["two_solder_interfaces"] = 2*p["solder_interface_areal_resistance"][1]/(a[0]*b[0])
    q["foil_to_horizontal_toe_corner"] = corner_upper(a, b, h, ra)
    q["horizontal_toe"] = ra*(F(spec["geometry"]["toe_projection"])-b[0])/(a[0]*h[0])
    q["horizontal_to_vertical_corner"] = corner_upper(a, h, h, ra)
    toe_centre,body_centre=toe_body_centres(p,spec["geometry"])
    q["toe_to_body_taper"] = taper_upper(a, h, ba, bb, p["body_taper_length"], ra,
                                            offset=(F(0),displacement_upper(toe_centre,body_centre)))
    axis=F(spec["geometry"]["wire_axis_y"])
    shift=displacement_upper(body_centre,(axis,axis))
    # Constant-section sheared prism; dimensions are the same at both ends,
    # so no fictitious taper derivative is charged.
    length = p["header_spine_length"]
    q["header_spine"] = ra*length[1]/(ba[0]*bb[0])*(1+(shift/length[0])**2)
    q["two_mating_tapers"] = 2*taper_upper(ba, bb, ma, mb, p["mating_taper_length"], ra)
    q["finite_mating_interface"] = p["mating_interface_areal_resistance"][1]/(ma[0]*mb[0])
    q["receiver_spine"] = ra*p["receiver_spine_length"][1]/(ba[0]*bb[0])
    q["receiver_to_hub_taper"] = taper_upper(ba, bb, hub, hub, p["hub_taper_length"], ra)
    q["continuous_crimp_hub"] = slab_upper(hub[0]**2, hub[1]**2, 2*hub[1]**2,
                                              p["hub_height"], 7*patch[0]**2, ra,
                                              normalized_profile_l2_squared_upper=weight_square/patch[0]**2)
    q["seven_finite_crimp_interfaces"] = p["crimp_interface_areal_resistance"][1]*weight_square/patch[0]**2
    area_hi = area*(p["contained_strand_radius"][1]/p["contained_strand_radius"][0])**2
    q["seven_strand_tips"] = slab_upper(area, area_hi, 4*p["contained_strand_radius"][1]**2,
                                          p["strand_tip_length"], patch[0]**2, rw)*weight_square
    q["seven_wire_tails_to_cut"] = rw*geometry["wire_tail_length_mm"][1]*weight_square/area
    total = sum(q.values(), F(0))
    target = F(spec["end_energy_ceiling_ohm"])
    # This is a counterexample to the unselected parameter BOX, not to the
    # actual Alpha product. Its allowed homogeneous straight circular member
    # has r=r_min and rho=rho_max. pi<22/7 bounds its conductance from above.
    circular_member_lower = 1000*rw/(22*p["contained_strand_radius"][0]**2)
    reference = spec["bulk_correlated_class"]["reference_case"]
    rho70 = F("0.000017241")*(1+F("0.003947")*50)
    reference_strands = [{"radius_mm": reference["radius_mm"],
                          "rho_lower_ohm_mm": reference["rho_lower_ohm_mm"],
                          "rho_upper_ohm_mm": rho70} for _ in range(7)]
    bulk_reference = bulk_class_admission(spec, reference_strands)
    return {"status": "CONDITIONAL ANALYTIC REFERENCE CELL ONLY; NOT AN ADMITTED GH ASSEMBLY",
            "unit_current_end_energy_upper_ohm": upward(total),
            "exact_upper_ohm": str(total), "end_energy_ceiling_ohm": upward(target),
            "conditional_energy_screen": "PASS" if total <= target else "FAIL",
            "headroom_ohm_lower": -upward(total-target),
            "costs_ohm_upper": {key: upward(value) for key, value in q.items()},
            "exact_costs_ohm": {key: str(value) for key, value in q.items()},
            "geometry": {**geometry, "strand_polygon_area_mm2": str(area),
                         "metal_before_outgoing_collar_z_mm": [str(x) for x in geometry["metal_before_outgoing_collar_z_mm"]],
                         "wire_tail_length_mm": [str(x) for x in geometry["wire_tail_length_mm"]]},
            "uniform_bulk_wire_trial_ohm_per_m_upper": upward(1000*rw/(7*area)),
            "allowed_straight_circular_bulk_member_ohm_per_m_lower": -upward(-circular_member_lower),
            "exact_circular_member_lower_ohm_per_m": str(circular_member_lower),
            "bulk_parameter_box_screen": "FAIL: allowed homogeneous member exceeds 0.17 ohm/m"
                if circular_member_lower > F("0.17") else "NO LOWER VIOLATION ESTABLISHED",
            "correlated_bulk_reference": {key: ([str(x) for x in value] if isinstance(value,list)
                                                else str(value) if isinstance(value,F) else value)
                                          for key,value in bulk_reference.items()},
            "strand_weight_square_sum_upper": str(weight_square),
            "potential_trial": "Constant over all possible connector metal, full possible PCB wetting and the outgoing collar; zero volume gradient and zero interface jump. This is a trial restriction, not a physical ideal terminal.",
            "physical_class_selected": False,
            "remaining": ["Exact-MPN continuous crimp hub and contained lead geometry unverified",
                          "Finite microscopic contact patches and areal laws unverified",
                          "Correlated bulk class is constructive; actual Alpha material, strand and curve compliance NOT RUN",
                          "Native face/origin/rotation and full PCB/wire trace composition not admitted",
                          "Instrument common/current/rail/drop objectives remain open"]}


if __name__ == "__main__":
    print(json.dumps(evaluate(), indent=2))
