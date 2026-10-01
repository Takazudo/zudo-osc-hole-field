# P ground prerequisite for issue 38

This is an **unselected disposable source variant**, not implementation or
acceptance of issue 39. All 418 source footprint origins, faces, rotations,
pin nets and library geometry are retained, including all 139 panel controls.
The coupling inventory is 127 GH ground contacts plus three main ground lands.
All 214 own-load AGND contacts remain explicit; they are not assumed to carry
zero current.

## Bare native result and source revision

The first bare planning export completed in 11 seconds. Its actual native
result is **31 rule errors and zero parity errors**. It has no ground planes or
arrays and is prohibited from entering a conductor model. The complete native
UUID/item inventory is retained by `audit_control_bare_conflicts.py`.

Thirty errors come from the original `load-power` rectangle, source
`[139,176.5]..[196,184]`, on both F and B. It intersects fixed pots, three GH
headers and four intended load terminals. The rectangle was a proposed load
reservation; the retained source specifies six separate wires and terminals,
not a physical transverse bus or solid component occupying the whole strip.

The other error is RV601 mounting pad 4 at source `(94.2,185)`. Its retained
copper radius is 1.2 mm and its plated drill radius is 0.9 mm. The original
notch at x94 cuts 1.0 mm into that copper and 0.7 mm into the drill. The proposed
local tab extends only to x92.35 over y182.8–187.2. It gives 0.65 mm nominal
copper clearance and 0.95 mm drill clearance while keeping the global 0.5 mm
copper-edge rule, pad, drill and fixed control unchanged.

The O5 conservative body/support projection ends at x91.6. The proposed tab
leaves 0.75 mm nominal XY clearance, or 0.55 mm after both existing 0.1 mm axis
allocations; the existing minimum is 0.5 mm. The O5 adapter reaches x92.4, so
there is 0.05 mm projected overlap with the tab. That overlap is represented
honestly: its front face is z−16, behind P's rear at z−13.4. The 2.6 mm nominal
z gap leaves 1.85 mm after the existing 0.5 mm body/tail growth and 0.25 mm
relative-z allocation. The full body/support, board/copper/solder, both rear
headers, carrier and both complete O5 loom channels are separately checked.
These are conditional source envelopes; installed qualification remains open
under issues 55 and 65.

## Individual terminal reservations

The variant replaces only the broad strip with four 6 × 6 mm B-side
reservations at TP990025, TP990027, TP990029 and TP990031. They match the two
existing individual reservations at TP990033 and TP990035. Every unrelated
reservation is retained. Exact owner reference, UUID, net, face, position and
finite land checks permit only the owning pad/footprint and contained own-net
vias. Foreign tracks, pads, vias, footprints and zones remain prohibited.

The complete source screen checks all 146 rear package courtyards, all 127
rear header courtyards and every native B-side copper projection, including
all through-hole contacts. Package courtyards include the existing 0.05 mm
native-cache inflation. F-side surface bodies are separated by the PCB; no
through-hole feature is removed by that face distinction.

The reservation screen retains the existing 0.25 mm source clearance used by
the load-pad mechanical checks and the floorplan's native free-clearance
bound. Its smallest package gap is 0.45 mm after the 0.05 mm cache inflation,
measured from the larger 6 × 6 mm reservation, not the 4 × 4 mm copper land.
The separate O5 neighbor target remains 0.5 mm in XY and 0.75 mm in z.

The maximum wetted support remains the 4 × 4 mm land. The proposed finite
nineteen-core fan fits inside that projection, but its physical material and
contact class remain unselected. A factory tool must stay within each finite
individual column, with P accessible before K and intervening loom are
installed. This is a process requirement, not an installed service-access
claim. The complete later insulated-wire routes remain their existing 3D
source proposals; the P fan-to-bulk interface and full electrical witness
still require explicit composition.

## Required next gates

- Fresh pinned native source geometry and parity checks, preserving all
  component/pad/hole identities and the explicit source-owned geometry delta.
- Original-grid main-via screening against every foreign conductor, hole,
  reservation and board edge; no assumption that all 150 sites survive.
- Source-defined AGND fills on F/In2/B and actual connectivity of all 344
  source ground contacts. Any further transfer must have a named source path
  and finite electrical cost.
- Mandatory successful native/model-entry receipt, then matched physical
  contact and full-network J/K/P/EL/adapter/current composition. Common
  resistance, GH current, manufacturing/material and voltage budgets remain
  open. Native or numerical completion alone cannot select this source.
