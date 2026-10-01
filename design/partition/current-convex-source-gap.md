# Current convex own-source flux gap inventory

Status: **nominal geometry inventoried; coefficients BLOCKED; physical and
electrical qualification NOT RUN**. This source proposal records the current
v6 own-contact aggregate, SHA-256
`a5bbda74de40c39dc21427aece3dc0a12857eb8c4f8257280dd8c9ab525b5d81`.
`scripts/pcbgen/current_convex_source_gap.py` rejects any change to that
aggregate or its 327 recorded source dependencies before producing a new
inventory. A new board/source epoch requires an explicit reviewed re-pin.

The exact current population is 3,620 nominal drill-free convex SMD AGND own
contacts: JL 886, JR 691, K 1,889, P 94 and EL 60. It spans 3,365 B.Cu and
255 F.Cu external faces. The output binds each ref, pad, native UUID, face,
convex primitive, and rational area/diameter bounds. Every row has null
coefficient fields and a `BLOCKED_PHYSICAL_SOURCE_INPUTS` status. The other
218 drilled SMD and 305 PTH contacts have different source classes and are
outside this inventory.

The analytic coefficient in `convex_source_flux.py` applies only after each
contact has a continuous **actual** drill-free foil slab under the complete
possible support, a geometrically contained positive reference-profile patch,
a positive minimum and maximum slab height, and a maximum resistivity for the
declared hot material/process envelope. Native copper geometry alone supplies
none of those physical admissions. The current source specification also
requires a face-correct normal trace, external current and redistribution
class qualification, and a joined continuous primal/dual construction. The
global 4.6 A net and separate 4.6 A redistribution budgets in
`contact-flux-class.md` are project requirements, not measured or source
qualified contact behavior. They do not choose a local support or rho maximum.

No coefficient may be inferred from the pad area or a hypothetical full-pad
wetting region. No zero-current contact may be dropped because the selected
class permits nonzero redistribution at zero net current. Any future
coefficient pass must record the support geometry, physical source, process
envelope, material bound and exact current epoch before calling the convex
coefficient function; the energy must then be combined with existing foil
energy using a proved cross-term bound. This inventory does not accept #38,
the common return, or a manufactured board.

## Work note

Requested result: classify all current convex own AGND sources and compute
coefficients only where selected physical inputs allow them. Affected source:
the reviewed v6 aggregate and its source closure; affected files are this
proposal, the standalone helper and its tests. Existing uncertainty: actual
slab, contained profile, process and material bounds are absent for all 3,620
contacts. Action: retain the exact current nominal geometry and block every
coefficient. Evidence: the source aggregate hash and dependency closure above;
the helper's machine-readable local output under `.circuit-cache` is disposable
and must be regenerated from the source. Verification: four focused tests and
`pnpm circuit:check` passed on 2026-09-30. Remaining work: select and qualify
the missing per-contact physical inputs, then construct and compose the full
flux/primal witnesses at the final board epoch.
