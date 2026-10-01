"""Conditional full-harness energy bounds from finite physical lead collars.

This arithmetic helper does not admit an actual JST assembly or a measurement.
Its domain is a complete passive conductor between two connected lead ends,
including both contacts/crimps and the complete intervening wire exactly once.
The collars must be FULL physical sections with insulated lateral boundaries,
not contained prisms into which unknown side metal can inject current.

On a reference convex prism D x [0,L], set chi=z/L and mu=(I/|D|)*e_z.
For conserved finite-energy J let g=J_z-I/|D| and solve Delta_xy psi=chi'*g
with Neumann sides and zero mean. Then

  K=(1-chi)*J + chi*mu + (grad_xy psi, 0)

preserves the inner trace, has uniform outer trace and zero divergence.
Orthogonal projection onto mu and the convex Neumann inequality give
||K|| <= (1+d/(pi*L))*||J||. A full-domain coefficient/geometry metric ratio
beta multiplies the squared bound. pi>3 is used below with exact rationals.

For an axially invariant positive reference conductivity sigma_0(x,y), the
target profile is sigma_0/integral(sigma_0), not uniform. Weighted projection
and the weighted Neumann bound replace d by sqrt(kappa)*d, where kappa is the
reference cross-section conductivity contrast. Additional axial/material/map
variation belongs in beta, not in an undocumented perfect-prism assumption.
"""
from fractions import Fraction as F

from scripts.pcbgen.observation_support_bound import rational, sqrt_upper, upward


def _identity(value, name):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(name + ": nonempty explicit reference required")
    return value


def collar_certificate(*, collar_id, reference_length_lower_mm,
                       reference_diameter_upper_mm, metric_ratio_upper,
                       trace_kind, full_physical_section,
                       insulated_lateral_boundary, source_free_collar,
                       no_unmodeled_internal_interface_energy,
                       premise_reference, reference_sigma_ratio_upper=1,
                       conductivity_profile_reference=None):
    """Return an exact rational energy multiplier for declared collar premises.

    The booleans declare mathematical premises; this function cannot inspect
    physical sections, material, side metal or the geometric map. Their source
    and actual compliance remain an independent admission responsibility.
    beta=metric_ratio_upper bounds upper/lower pullback resistivity metrics
    relative to the chosen reference conductivity on the COMPLETE collar.
    """
    identity = _identity(collar_id, "collar identity")
    reference = _identity(premise_reference, "collar premise")
    if (full_physical_section is not True or insulated_lateral_boundary is not True
            or source_free_collar is not True):
        raise ValueError("Full physical, laterally insulated, source-free collar required")
    if no_unmodeled_internal_interface_energy is not True:
        raise ValueError("Complete volumetric collar energy required; no omitted internal interface charge")
    length = rational(reference_length_lower_mm, "collar length", True)
    diameter = rational(reference_diameter_upper_mm, "collar diameter", True)
    beta = rational(metric_ratio_upper, "complete collar metric ratio", True)
    contrast = rational(reference_sigma_ratio_upper, "reference conductivity contrast", True)
    if min(length, diameter) <= 0 or min(beta, contrast) < 1:
        raise ValueError("Positive finite collar dimensions and ratios >=1 required")
    if trace_kind == "uniform_reference_section":
        if contrast != 1 or conductivity_profile_reference is not None:
            raise ValueError("Uniform reference profile requires homogeneous reference conductivity")
        target = "Uniform normal flux on the full reference section, Piola mapped to the actual end"
    elif trace_kind == "conductivity_weighted_reference_section":
        _identity(conductivity_profile_reference, "complete transverse conductivity profile")
        target = "sigma_0/integral(sigma_0) on the full reference section, Piola mapped to the actual end"
    else:
        raise ValueError("Unknown full-section output trace family")
    gamma = beta*(1+sqrt_upper(contrast)*diameter/(3*length))**2
    return {"collar_id": identity,
            "multiplier_exact": gamma,
            "multiplier_upper": upward(gamma),
            "target_trace": target,
            "trace_kind": trace_kind,
            "premise_reference": reference,
            "conductivity_profile_reference": conductivity_profile_reference,
            "status": "CONDITIONAL COLLAR CONSTRUCTION; physical premises not verified"}


def assembled_harness_bound(*, test_domain_id, test_boundary_reference,
                           test_resistance_upper_ohm, test_bound_kind,
                           linear_passive_dc, other_power_sources_absent,
                           all_excitation_current_crosses_both_collars,
                           other_electrical_ports_absent,
                           fixture_energy_subtracted, collars_disjoint,
                           collars, adapters, allowance_ohm=None):
    """Convert one whole-domain scalar energy upper to two fixed end traces.

    R_test bounds TOTAL dissipated power/I^2 between actual excitation
    terminals. Passive fixtures may be included conservatively, never naively
    subtracted. A point Kelvin voltage, catalogue per-contact maximum or a
    sum of unidentified per-end resistances is not that premise.

    For disjoint collars, E_new <= max(gamma_left,gamma_right)*E_test.
    The multipliers are neither added nor multiplied. Separately supplied
    adapter regions are outside the tested harness/collars and must match
    their complete output traces. Region names do not prove physical disjointness.
    """
    domain = _identity(test_domain_id, "complete assembled domain")
    boundary = _identity(test_boundary_reference, "actual excitation boundary")
    if test_bound_kind != "total_passive_input_power_over_current_squared":
        raise ValueError("Whole-domain total passive input-power bound required")
    if linear_passive_dc is not True or other_power_sources_absent is not True:
        raise ValueError("Linear passive DC domain without other power sources required")
    if (all_excitation_current_crosses_both_collars is not True
            or other_electrical_ports_absent is not True):
        raise ValueError("Entire excitation current must cross both collars; no bypass or other port")
    if fixture_energy_subtracted is not False:
        raise ValueError("Unproved subtraction of fixture or spreading energy is forbidden")
    if collars_disjoint is not True or len(collars) != 2:
        raise ValueError("Exactly two physically disjoint full-section collars required")
    resistance = rational(test_resistance_upper_ohm, "whole-domain resistance bound", True)
    if resistance <= 0:
        raise ValueError("Finite positive complete-domain energy bound required")
    certificates = [collar_certificate(**row) for row in collars]
    ids = [row["collar_id"] for row in certificates]
    if len(set(ids)) != 2:
        raise ValueError("Two distinct collar identities required")
    multiplier = max(row["multiplier_exact"] for row in certificates)
    seen = set(ids) | {domain}
    paid = F(0)
    for adapter in adapters:
        identity = _identity(adapter.get("region_id"), "adapter region")
        if identity in seen:
            raise ValueError("Duplicate/overlapping named region in once-only ledger")
        seen.add(identity)
        if adapter.get("outside_tested_domain_and_collars") is not True:
            raise ValueError("Adapter must be outside the tested harness and collar volumes")
        if adapter.get("matching_collar_id") not in ids:
            raise ValueError("Adapter must bind a complete named collar output trace")
        _identity(adapter.get("matching_trace_reference"), "adapter full-trace matching proof")
        paid += rational(adapter["energy_upper_ohm"], "adapter current energy", True)
    transformed = multiplier*resistance
    total = transformed+paid
    result = {
        "status": "CONDITIONAL FULL-HARNESS ENERGY ONLY; actual hardware and test applicability NOT ADMITTED",
        "test_domain_id": domain, "test_boundary_reference": boundary,
        "test_bound_kind": test_bound_kind,
        "collars": [{**row, "multiplier_exact": str(row["multiplier_exact"])} for row in certificates],
        "maximum_collar_multiplier_exact": str(multiplier),
        "maximum_collar_multiplier_upper": upward(multiplier),
        "whole_harness_fixed_trace_upper_ohm": upward(transformed),
        "disjoint_adapter_energy_upper_ohm": upward(paid),
        "total_upper_ohm": upward(total), "total_upper_exact_ohm": str(total),
        "limitations": [
            "The test bound includes both assembled contacts/crimps and all wire once; no strand sharing is inferred.",
            "The entire measured excitation current crosses both collars in series; fixtures and other wires may not bypass the tested conductor.",
            "Every collar is the full physical cross-section; a contained core with unmodeled lateral metal is insufficient.",
            "The complete collar energy is represented by the volumetric metric; an omitted internal Robin-interface charge is not covered by a bulk resistivity ratio.",
            "Full profile matching, metric/material/geometry bounds, isolation and actual power terminals require evidence.",
            "Additional passive metal may not bypass the declared full-section cuts or create an unmodeled external port.",
            "A compatible whole-wire potential witness is still required for lower bounds and the cut-current objective.",
            "No common-ground, GH-current, rail, voltage or manufactured-hardware acceptance follows from this helper.",
        ],
    }
    if allowance_ohm is not None:
        allowance = rational(allowance_ohm, "existing local allowance", True)
        result["conditional_local_allowance_screen"] = "PASS" if total <= allowance else "FAIL"
        result["allowance_ohm"] = upward(allowance)
    return result
