# No-solve P wetting-restriction diagnostic

This is an **unselected nominal diagnostic** of the preserved P source and
operator epoch. It does not admit a physical process/contact/current class,
change any copper or source trace, release a potential restriction, or satisfy
#38's original common/current/rail/drop requirements.

The original paired solve and field archive remain byte-for-byte unchanged.
`wetted-restriction-diagnostic.json` binds those artifacts, the current mesh,
the complete earlier P receipt/profile/native data, and imported arithmetic
helpers. The new script does not assemble or factor any operator and does not
call a linear solver. Imported mesh classes are only deserialized.

## What is measured

The original potential trial is constant on each 4 × 4 mm B-foil maximum-wetting
region at TP990031, TP990033 and TP990035. Each terminal also ties every foil
port of 25 complete barrels to that same value. Those 75 barrel volumes and
their transfer collars therefore have constant potential. This is a trial
restriction, not physical equipotential copper.

Current-sheet membership uses complete triangles whose vertices lie strictly
inside the wetting rectangle with the retained geometric guard. Boundary-crossing
triangles are excluded. Native barrel UUIDs, terminal identities, wetting
rectangles and barrel-index sets are checked for duplicate or overlapping
ownership before union sums. All these regions remain common copper.

On a region where the continuous potential v is constant, its constitutive
mismatch with a compatible conserved trial q is exactly its current energy:

```
integral_W rho |q + sigma grad(v)|² = integral_W rho |q|².
```

The retained raw sheet outward currents yield a lower energy using the physical
triangle metric envelope. Their exact finite-source vertical lift is included;
its energy is additive by directional orthogonality. For each tied barrel,
the diagnostic uses an **exact balanced, internally conserved local trace**,
not the divergence of a raw numerical internal field. In each dielectric gap,
conservation fixes the axial cut current. Cross-section Cauchy gives
`rho * gap_length * cut_current² / annulus_area` as a lower energy. The annulus
area is bounded upward using π ≤ 22/7 and outward radius bounds. Band, flange
and collar energies omitted by this expression are nonnegative.

This mixed reference consists of raw sheet fields and the exact internally
repaired local barrel operator at the retained raw port coefficients. The
barrel's trace is the operator's exact balanced projection. The retained global
correction certificate bounds the change from that local operator reference
to final globally conserved port/foil fields. Retaining the larger combined
global-plus-internal correction allowance remains conservative. No raw barrel
divergence is promoted to exact conservation.

Given raw lower energy A and complete squared correction norm C, the present
conserved-trial energy lower is

```
max(0, sqrt(A) - sqrt(C))².
```

For the disjoint union the correction is charged once. This measures mismatch
of the saved trial; it is not automatically a floor for a different current
trial.

## Independent restriction-forced floor

A second calculation constructs a continuous P1 test potential ψ. It is 1 only
at vertices whose entire triangle star lies inside the selected region, and
0 at all mesh/barrel boundaries and all other vertices. It extends by zero to
the rest of the conductor and is constant through the foil thickness. It is
an explicit function, not a solved or optimized field.

The exact finite boundary source functional uses the same 1-pm coordinate
convention as the retained source projector. Whole source triangles and
rectangular source supports are checked explicitly; partial source triangles
are rejected. Incoming current gives the boundary identity
`integral q·grad(ψ) = -f(ψ)`. The depth-constant ψ has zero gradient paired with
the vertical lift, but the lift's external-face normal trace still contributes
to f(ψ). Matching only terminal totals would not justify this functional.

Green's identity and Cauchy imply, for **any** compatible conserved current,

```
integral_W rho |q|² >= |f(ψ)|² / integral_W sigma |grad(ψ)|².
```

The numerator is exact rational arithmetic and the denominator is bounded
upward; the quotient rounds downward. Binary P1 cells are either constant or
one signed barycentric basis, allowing an explicit finite energy evaluation.
A zero source functional produces zero. This is a true lower bound on the
restriction-forced mismatch floor, not the exact value of that floor.

## Results and interpretation

The first retained-data postprocess completed in 8.656 seconds without any
operator assembly, factorization or solve. Final validation adds explicit
artifact linkage and disjoint-union/helper-hash checks; the preliminary receipt
is preserved, and the final guarded postprocess receipt is recorded below.

Each main-terminal subset contains 1165 current triangles and 255 nonzero
bubble vertices. TP990031 includes all 152 source triangles in the selected
subset and has `f(ψ) = −1` for both columns. The other terminals have zero
source functional. The chosen binary bubble's energy upper is about 24.758 MS,
so its independent floor is weak.

All displayed lower bounds and lower-bound percentages below are rounded
downward; exact outward values are retained in the receipt.

| Quantity | Observation column | Source column |
|---|---:|---:|
| Present-trial mismatch lower | 0.014795862 mΩ | 0.014794844 mΩ |
| Fraction of retained variational gap | 8.02296% | 6.43262% |
| Independent restriction-forced floor lower | 0.0000403906 mΩ | 0.0000403906 mΩ |
| Floor lower / retained gap | 0.0219015% | 0.0175613% |

These are conservative **lower** bounds. They neither establish that the
restriction accounts for most of the gap nor prove it negligible. In
particular, the weak independent floor does not justify releasing ties or
predict that doing so would close the 0.5 mΩ objective. The denominator for
these fractions is the retained variational upper gap, which also includes
numerical allowances; it is not an independently measured physical error.
The primary complete-PCB transfer interval remains 0.439020–0.644971 mΩ,
straddling the target and not finalizing a common/private allocation.

## Next bounded computation, not executed here

Keep the potential restriction unchanged. The smallest useful next solve is
one potential-only reconstruction of the same two functions on the unchanged
operator, recording the initial factor solve plus refinement increments through
a wrapper installed after `restrict_wetted_terminals`. Preserve full finite
traces, all native/model checks, the reduced projection map and gauge. The
current fields already exist, so no new current solve or full basis is needed.

Localize constitutive mismatch by streaming intersections of current RT and
potential P1 sheet cells, accounting separately for geometric-envelope
extensions and all numerical/correction terms. For each complete barrel and
collar, avoid an unnecessary interior Q1 export: a locally conserved balanced
current and matched continuous potential give

```
integral_barrel+collar J·grad(v)
  = sum_sector I_sector * (V_sector_start + V_sector_end)/2.
```

This is the exact Green boundary pairing for uniform arclength/depth current
and linear arclength, depth-constant potential traces. The local current and
potential diagonal energy uppers are already available from the condensed
operators. If the chosen balanced local reference differs from the saved raw
port field, charge that change explicitly in the same correction norm. After
potential restriction, original port indices cannot directly index reduced
coefficients; recover the actual port trace through the updated projections.

This proposed calculation can identify whether fixed-geometry trial refinement
has a useful target. It is not authorized or executed by this diagnostic. A
future restriction change must preserve continuity on the full possible
contact-metal envelope. Keeping the B-face trace constant while freeing deeper
barrel potentials may be admissible for the bare-PCB nominal domain, but physical
credit also requires accounting for possible solder intrusion or a selected
process exclusion. No supplier/process guarantee is inferred here.

Seven focused tests cover analytic finite-face and zero-source cases, exact
signed rectangular source integration, partial-triangle rejection, triangle
energies, correction norms, conservative whole-star membership, trace-only
shell energy, immutable artifact linkage and disjoint regions.

The final guarded no-solve postprocess returned `verdict=PASS`, exit 0,
7 seconds of guarded execution, 6.55 seconds process wall time and 5.841 seconds
recorded diagnostic time. Peak resident memory was 534216 KiB (about 522 MiB);
no swap occurred. Bounds are exactly unchanged from the preliminary receipt.

Final receipt:
`.circuit-cache/issue38-recovery/wetted-restriction-v2/receipt.json`, SHA-256
`ce8cb86dfc0c6f9bb72408d07552efcd0ad8cf2165c763dbd9cf36b8f9046678`.
Reviewed executable SHA-256:
`d912f0d4f2a1b78df0d43e7a36a3ca7436e74256f5f7d111ae402e44bd2cdcf9`.
The receipt binds the full input/helper closure and source manifest. The seven
focused and 22 related tests pass. No second P conductor solve or refinement
was requested or performed, and the original receipt/archive remain unchanged.
