# P complete-contact nominal diagnostic scope

Status: **current-source native prerequisite and nominal complete-contact
diagnostic PASS; physical/electrical acceptance OPEN**. This does not select
a physical contact, material, current or manufacturing class.

The pinned P bare-v4 and full-v4 candidates use the current IO/exporter/stack
source. The full native gate reports zero rule/parity errors, all 344 source
ground contacts and all 75 AGND array vias connected. A fresh guarded
343-function current/potential run completed in 563 seconds. Its result
retains all current model/native source hashes and reports maximum numerical
residuals 5.907e-10 A (current) and 2.221e-9 A (potential), both below the
unchanged 1e-8 A gate. The 343×343 upper/lower gap is positive semidefinite;
the largest self upper is 1.2574 mΩ. These are fixed numerical contact
profiles in a nominal conductor; no hot joined limit follows. The older P v3
native receipt and numerical matrix remain historical source epochs.
The current checkpoint-source result is
`.circuit-cache/issue38-recovery/control-feasibility-v4/ground-full-nineteen-checkpoint-v2.json`
(SHA-256 `00890dac518ca52ecefbdc2a54471cf752a8e92c0f68056bcada6dbe1a9b05f8`).
Its 343×343 current and potential matrices are bitwise equal to the prior
v4 nominal solve; all 43 current and 43 potential batches were recomputed in
this guarded run. Both receipts remain `NOT ACCEPTED` for physical and joined
electrical use. The prior solver-source receipt is historical.

The earlier source proposal described 129 independent coupling functions:
127 GH grounds and three mains, less one named main reference. Preserve that
historical description and its native source receipts. The first planned P
diagnostic now includes the 214 own-load contact functions as well, for
**343 independent functions over all 344 declared ground contacts**. This
avoids treating own loads as absent and avoids a second whole-board run just
to add them. It changes the diagnostic basis, not the source hardware,
stack, conductor geometry or native acceptance requirements.

## Exact invocation and prerequisites

The planned driver must explicitly use `--port-limit 0 --include-loads
--main-strands --adaptive`, coarse 2 mm, local fine 0.25 mm and refinement 1.
The initial guard limit is 3600 seconds with a 6000 MB available-memory start
gate. Output stems are fresh. All source, native, prerequisite, profile, mesh,
contact/helper and phase hashes must remain bound and checked before and
after the computation. The 1e-8 residual and all conservation/energy gates
remain unchanged.

A passing bare planning export is insufficient. Entry requires a successful
filled native P candidate with zero actual rule/parity errors, all 344 source
ground contacts and all 75 declared AGND array vias connected, exact source
pad/hole/footprint preservation and original companion authority. The generic
P command path must reject a missing, failed, stale or mismatched receipt.
Actual positive entry and negative bypass tests are mandatory before dispatch.

## Geometry and functionals

The actual P terminals and GH pads are on B.Cu. The nominal source uses four
70 µm foils in the fixed 1.6 mm construction, with dielectric gaps
0.06/1.20/0.06 mm. AGND pours are on F/In2/B; all actual AGND annuli on the
other foil remain in the complete conductor. The retained v2 diagnostic
export has 195 circular plated AGND bridges (97 × 1.0 mm, 23 × 1.09 mm and
75 × 0.3 mm drills). The passing final export must independently confirm its
exact bridge inventory rather than inherit this failed-run observation.

TP990031 is the first named AGND main and the mathematical reference. It is
not a newly selected source inlet or physical ideal ground. Every probe is a
balanced pair. GH and own-load functions remain fixed finite numerical foil
profiles. A through-hole load's chosen B-foil profile is not a claim that its
actual package injects a uniform current on B.Cu. Each main uses the nineteen
finite supports and full-wetting restricted potential trial already declared
by the unselected contact proposal. They do not imply equal physical strand
sharing or an ideal PCB pad.

## Remaining acceptance

The computation is nominal/profile diagnostic only. Actual lead/solder/wire
trace composition, every permitted physical terminal distribution, a finite
material/geometry envelope, the global signed source-current class and
complete J/K/P/EL/adapter composition remain required. Refinement and numerical
margin must be demonstrated for any eventual acceptance. The combined common
ground ceiling, GH current limits, rail ceiling and complete voltage budgets
are unchanged. Physical qualification stays open; a deterministic failure
cannot be relabeled as qualification work.
