# Conditional collet headroom and qualification ledger

The proposed collet has **0.197966 mm of conditional local headroom** above the
0.25 mm board-clearance criterion. This is one shared allowance in a geometric
calculation. It is not demonstrated manufacturing capability or permission to
relax a requirement. All eleven qualification-ledger entries remain unqualified;
no supplier, measured assembly, material or load-test evidence has been supplied.

`collet_headroom.py` replays `collet_clearance.calculate()`, requires equality
with its saved JSON after JSON type normalization, and records exact SHA-256
bindings to the collet, curve, process, reconciliation and source-lock inputs.
The existing collet calculation also validates its producer source chain. The
generated `collet-headroom.json` records this script's hash. None of the frozen
process or producer inputs are amended.

## Local arithmetic and its limits

For a flat-ended cylinder with outer radius `r`, first grip station `s`, anchor
height `H`, and axis outward-normal component `v`, the exact closest-plane gap
is `H + s*v - r*sqrt(1-v*v)`. The current worst case uses `H=1.95 mm`,
`s=1 mm`, `r=2 mm`, and `v=0.536177083`, after the proposed 0.572967-degree axis
cone. This outer-cylinder model contains no flange, screw head, lug, arm or end
cap outside the specified cylinder.

| Quantity | Conditional value |
| --- | ---: |
| Cylinder gap before independent closures | 0.797966035 mm |
| Allocated independent closure sum | 0.350000000 mm |
| Remaining gap | 0.447966035 mm |
| Required residual gap | 0.250000000 mm |
| Maximum total closure at the fixed geometry | 0.547966035 mm |
| Single shared headroom | 0.197966035 mm |

The closure sum includes 0.05 mm outer profile, 0.10 mm board warp, 0.05 mm
thermal displacement, 0.05 mm retention displacement and 0.10 mm registration.
It conservatively retains the full registration allowance even when its effect
might partly overlap measured anchor height. No common-datum cancellation is
assumed. These are proposed bounds, not measured capabilities.

Holding every other local input fixed gives the following diagnostic boundaries:
anchor height 1.752034 mm minimum, outer radius 2.234528 mm maximum, grip start
0.630782 mm minimum, or axis half-cone approximately 6.699901 degrees maximum.
These are separate one-variable sensitivities. They cannot be combined and do
not replace the accepted-for-proposal dimensions or the current C1 requirement.
Changing dimensions would require renewed wire, source-obstacle, bore, carrier,
length and bending checks. Boundaries are double-precision calculations rather
than directed-rounding interval certificates; they are not production targets.

The counterexample in the JSON spends the full headroom on each of two closure
terms. Each isolated change reaches its one-variable boundary, but their
combination leaves only 0.052034 mm, failing the 0.25 mm criterion. A hypothetical
unmodeled 0.25 mm feature toward the board similarly leaves only 0.197966 mm.
This is an illustrative feature, not an assertion that the design has one.

## Angular clearance cannot relax the wire-shape requirement

The proposed C1 deviation remains `|e'| <= 0.01`. Where the bore axis follows the
straight gripped wire, this bounds angular deviation by `asin(0.01)`, provided
that alignment itself is qualified. A positional inspection alone establishes
neither this direction bound nor C2 curvature control.

The local clearance calculation tolerates a much larger angular cone, but the
existing curve and cut certificates impose tighter coupled limits. Holding the
reference radius, C2 bound, reference path, cut and preparation inputs fixed:

| Diagnostic C1 limit | Value |
| --- | ---: |
| Current proposed requirement | 0.010000000 |
| Cut plus minimum preparation certificate boundary | 0.017441735 |
| Bend-radius certificate boundary | 0.023598183 |
| Collet/board angular clearance alone | 0.116669028 |

These limits follow from `R_actual >= (1-eta1)^2/(1/R_ref+eta2)` and
`preparation >= cut_min-(1+eta1)*reference_path_max`. The angular sensitivity
table uses the minimum C1 bound needed to permit each whole angular cone;
angular alignment alone never establishes C1 control over the entire wire.
At a 2-degree cone the local board gap still passes (0.400596 mm), while these
conditional bending and preparation certificates no longer establish their
requirements. Failure of a conservative certificate is not proof of actual
physical failure. None of these calculations authorizes changing C1, C2, cuts,
preparation or electrical limits.

## What must be qualified

The JSON explicitly separates proposed dimensional acceptance, geometric model
assumptions, load/displacement assumptions, continuous-shape requirements and
the residual design criterion. Every entry has `qualified: false`, no evidence
receipt, and a concrete required verification. Qualification must include
assembled datum inspection with measurement uncertainty, complete exterior
containment, bore/wire alignment, board warp, service retention, thermal/load
response, and continuous C0/C1/C2 behavior including collet exits and strain
transitions. Factory cut and stripping/solder preparation also remain unproven.

This work closes a bounded arithmetic/assumption ledger only. Complete revised
carrier solids, wire-to-carrier and wire-to-wire sweeps, grip/insulation behavior,
realized copper, all trimmer access and physical qualification remain open. The
previous collet/source XY screen is neither rerouted nor generalized into a full
feed collision result. No native execution, hardware change or architecture
adoption is performed.

From this directory, with the source Python environment:

```sh
PYTHONDONTWRITEBYTECODE=1 /tmp/osc-arch-source-venv/bin/python collet_headroom.py --check
PYTHONDONTWRITEBYTECODE=1 /tmp/osc-arch-source-venv/bin/python -m unittest test_collet_headroom -v
```

Omit `--check` to regenerate the JSON. The tests cover both sides of the angular
and radius boundaries, shared-budget double spending, the coupled angular
counterexample, omitted exterior geometry, source-evidence drift rejection and
the absence of qualification or authorization flags.
