# Selected P common-region probe

This is an **unselected nominal diagnostic**, not an accepted common/private
allocation or a physical conductor/contact/source class. It preserves the
`control-feasibility-v4` P native, finite-profile and solver epoch. All hardware
remains an unvalidated draft and #38's original targets remain required.

`common-region-probe.json` names exactly two balanced functions:

- Observation: `J900134:2 − TP990031:1` (retained column 4).
- Source: `C107:2 − TP990031:1` (retained column 128).

The prior complete nominal matrix gives a transfer interval approximately
0.437138–0.647410 mΩ. This straddles 0.5 mΩ. It neither proves a failure nor
establishes the joined J/P+K common requirement. The selected computation
reconstructs these two fields and spatial accounting without solving the entire
343-column basis. The complete native port inventory is still checked first;
selection of two right-hand sides does not remove physical ports or copper.

## Physical accounting

All PCB copper is common for this stronger diagnostic: every active foil,
main-land spreading, shared neck, barrel, flange and annular transfer collar.
There are no PCB-private regions and no subtraction of private diagonals.
Each barrel's native ownership UUID is a region. Each foil is another region;
barrel ownership was already subtracted by the retained extraction. The
one-face source lift occupies its foil region. Its in-plane/vertical energy
orthogonality is used rather than inventing disjoint volumes for overlapping
fields. Exact shared-main and overlapping source cross terms remain included.
External solder, connectors and wire are outside this board diagnostic and
must still be paid in any joined proof; they are not zero-cost regions.

A nominal all-PCB lower transfer above 0.5 mΩ would reject this stronger
sufficient allocation for the named pair. It would not automatically reject
the original private-aware common requirement or a physical process class.
A source-owned exclusive foil neck may permit a later private region; no such
new geometry is credited by this old epoch.

## Reconstruction and integration

The new standalone `regional_probe.py` calls the existing full P native entry,
`current_matrix` and `potential_matrix` APIs without modifying the 44 model
inputs. It verifies input hashes before and after computation, uses only the
existing hash-bound mesh caches, and refuses an existing output directory.
It records fields through the public `conservation_repair` hook, retaining all
existing refinement, reciprocity, residual and exact-tree correction gates.
The potential lower retains the same finite wetted-terminal restriction.

The exported raw fields are **not declared conserved**. The complete exact-tree
correction has an explicitly retained squared norm bound C_global. Barrel basis
fields have a separate local exact-tree correction; arbitrary linear
combinations are bounded by `sum_j |a_j| sqrt(C_j)`. Their evaluation errors and
positive contraction roundoff are charged, then combined with C_global by the
triangle inequality. The raw barrel port is the original evaluated value,
without another balancing operation: changing that reference can invalidate an
already combined raw-to-corrected error bound.

For each raw regional pair, U and L enclose its physical quadratic metric.
The cross term uses two-sided polarization:

```
center = pᵀ(U+L)q/2
radius <= sqrt((pᵀ(U−L)p)(qᵀ(U−L)q))/2
```

An upper Gram off-diagonal alone is not an upper physical transfer. Foil RT
cells use their two-sided geometric metric envelope. Barrel RT cells use the
componentwise radial/angular metric extrema on the same reference cells.
The annular collar currently uses zero as its metric lower and the retained
analytic metric upper, explicitly allowing an inconclusive interval. The
finite rectilinear source-lift Gram is computed with exact rational areas on
the same 1-pm coordinate grid as the source projector; nonrectilinear source
profiles are rejected by this probe. Field contractions have explicit
operation-count and outward-conversion allowances.

With raw regional energy uppers E_b,E_s and raw-to-conserved squared norm bounds
C_b,C_s, charge the cross error

```
sqrt(E_b C_s) + sqrt(E_s C_b) + sqrt(C_b C_s).
```

The corresponding conserved regional energy upper is `(sqrt(E)+sqrt(C))²`.
For an aggregate union the correction is charged once, after summing raw
regional quantities. Individual regional bounds are independent conservative
bounds and need not sum below a tighter valid global trial-energy upper.

For the exact PDE solution, the regional Cauchy error then uses the existing
whole-domain current/potential gaps δ_b,δ_s:

```
sqrt(U_b,W δ_s) + sqrt(U_s,W δ_b) + sqrt(δ_b δ_s).
```

The complete-domain Loewner interval is also reported separately and is the
primary result for this all-PCB union. The generic regional formula is valid
but unnecessarily loose when W is the entire modeled domain. For conserved
compatible trials `q_s=J_s+e_s`, `q_b=J_b+e_b`, the exact equilibrium fields are
energy-orthogonal to the zero-source current errors. Consequently

```
<q_s,q_b> - <J_s,J_b> = <e_s,e_b>
whole-domain radius <= sqrt(delta_s delta_b).
```

This cancellation requires the complete domain and matched full source traces;
it does not generally apply to a proper common subset. Regional integration
alone does not promise useful convergence or physical admission.

## Verification and output

Focused tests cover both signs of the PSD-upper off-diagonal counterexample,
negative transfer, metric enclosures, exact overlapping source lifts, raw
correction errors, independent regional bounds, changed hashes, and a real
four-foil sheet/barrel/source fixture using the unchanged current API.

The guarded run uses the retained solver environment:

```sh
bash "$HOME/.codex/scripts/heavy-guard.sh" -- \
  .circuit-cache/issue38-recovery/solver-venv/bin/python3 \
  -m scripts.pcbgen.regional_probe \
  --output .circuit-cache/issue38-recovery/common-region-pair-v1
```

Large fields stay in ignored cache. `current-fields.npz` records the two hybrid
fields, all four sheet outward-flux/source arrays and all raw barrel port
coefficients; the hash-bound barrel operators reconstruct internal RT fields.
`receipt.json` records exact input and output hashes, native prerequisite,
source/observation/reference identities, numerical gates, per-region trial
energy and cross intervals, raw-to-conserved corrections, complete U/L matrices
and both transfer enclosures. No cached factorization is required or retained.

The single guarded run completed with `verdict=PASS`, exit 0, 45 seconds of
heavy-slot execution and 5367 MB minimum available memory. Solver receipt time
was 43.294 seconds. Current/potential maximum equation residuals were
3.645e-10 A / 6.985e-10 A. The 9 probe tests and 32 combined focused tests pass;
`pnpm circuit:check` passed before and after the change.

Retained output:

- Receipt: `.circuit-cache/issue38-recovery/common-region-pair-v1/receipt.json`,
  SHA-256 `30306a92098d8f1ecd64a15e4da389a3a2061cc1a75f0c5f2f37aa1a210acd68`.
- Raw fields: `current-fields.npz` in that directory (24,330,251 bytes),
  SHA-256 `c7fb2db490f446aa8ca1c1840538898d67d090bb0772c6f0e08f8bbd156709df`.
- The JSON source manifest records exact native/profile/mesh inputs. The output
  receipt additionally records all 44 unchanged model hashes and the executable
  hash `bfae8dd7a35a339296951f7890a171098a38e9b664e09183e61599e0300d0f79`.

| Result | Interval or value |
|---|---|
| Complete-PCB transfer | **0.439019665–0.644970631 mΩ** |
| Conserved current-trial common cross | 0.587859089–0.594151038 mΩ |
| Generic regional-formula radius on all PCB | 1.138473934 mΩ |
| Generic regional-formula interval on all PCB | −0.550614845–1.732624971 mΩ |
| Observation/source whole energy gaps | 0.184418850 / 0.229997098 mΩ |
| Raw-to-conserved cross correction radius | 0.000158071 mΩ |

The 199 common regions are four foils and 195 complete barrel/collar objects.
The broad generic regional interval is a bound-formula limitation, not an
estimate of 1.138 mΩ of unresolved physical error. Whole-domain orthogonality
reduces that formula's radius to 0.205950966 mΩ and gives a current-trial-based
interval 0.381908123–0.800102004 mΩ. The retained Loewner interval above is tighter
still. For a future proper common subset, the linear regional error terms
remain and its geometry/source accounting must first be selected. Local
metric integration and conservation-correction widths are comparatively small. Maximum residual-work allowance is 0.00887 µΩ; maximum
added current numerical diagonal is 0.24317 µΩ, far below the 184–230 µΩ whole
column gaps. Further residual bookkeeping alone cannot be presumed to close
this nominal convergence gap. Regional trial energies do not localize the
actual PDE error, so no particular copper region is blamed from its energy alone.

The narrower whole-PCB interval still straddles 0.5 mΩ. This is an inconclusive
nominal diagnostic, not a pass or a physical counterexample. No further
refinement was run. Full-basis recomputation, a new native board, hardware
qualification and source/contact/material admission remain NOT RUN by this
probe. The original common/current/rail/drop targets are unchanged.
