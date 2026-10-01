# Unselected K ground conductor prerequisite

This source is a bounded feasibility prerequisite for #38. It is not the #43
PCB implementation, a selected manufacturing class, or electrical acceptance.
Canonical K hardware, origins, outline, layer count and exclusions remain fixed.

The proposed nominal stack has four 70 um foils and 0.06 / 1.20 / 0.06 mm
dielectric gaps. F, In1 and B carry AGND pours. Native geometry retains all
foreign-net pads, drills, fixed keepouts and source footprints. Future rail and
signal routing can change the conductor; #43 must re-extract its final layout.

## Explicit copper ownership

- `main-via-plan.json` retains 188 individually identified legal sites from the
  original eighteen 5 x 5 grids. The nine AGND lands have 15/14/5, 18/17/12 and
  4/8/17 vias. No 25-via assumption, translated array or ideal pad is used.
- `header-stitch-plan.json` names two vias near each of 52 J-facing headers:
  104 vias, 206 exact source ground contacts, and no added tracks. Each proposed
  site lies in the actual connected F sheet and In1/B AGND fills, away from
  foreign copper, holes, every pad and all retained rule areas. Full sheet
  access and barrel energy remain charged. Equal sharing is not assumed.
- Current source therefore proposes 292 vias in total, plus existing physical
  plated contacts. The full native pad geometry/net/face/position must match
  the retained pre-stitch source exactly; metadata child UUID changes are
  separately recorded through source/native identity bindings.

The original stitch plan retained pad UUIDs. Its next version also retained
exact pad coordinates and layers for explicit binding after metadata projection.
The final planner parses immutable input bytes, retains entry digests, and
checks them again before publication. Those refinements change provenance,
not the 104 chosen sites. All runs remain planning evidence only.

## Exact owning-terminal reservation exceptions

Every original POWER polygon and its track/zone prohibition remains. Native
custom rules permit only the owning reference's pad and footprint, and same-net
vias wholly inside its 4 x 4 mm land. Foreign pads and footprints are rejected
even when their net is AGND. The source audit separately requires the exact
owning footprint UUID, F-side origin, one pad numbered 1, owning net and 4 x 4
rectangular SMD geometry. Moved or straddling objects remain prohibited.

Pinned native fixtures exercise legal ownership and wrong-net, foreign same-net,
outside, straddling, unrelated-land, shifted-owner and track cases. The first
extended fixture used a synthetic footprint without a courtyard; its pad was
rejected, but native footprint-area matching had no physical footprint outline.
The corrected fixture uses the actual retained terminal and courtyard with the
same rule predicates. This does not assert stronger native footprint matching
than the oracle provides; source identity and pad geometry checks remain required.

## Metadata authority

The pinned canonical netlist has separate `fields` and `property` blocks. K
native parity uses the complete `fields` block. Source layout/current metadata
and empty DNP/BOM markers retain their original property namespace. Every
original schematic unit remains unchanged and is retained in the projection
receipt; field values can legitimately come from different units of one package.

The complete 3594-package metadata fixture has zero positive parity errors and
rejects an intentionally changed mixed-unit field. Its unrelated geometry and
unconnected-item report is not a full K acceptance result. The earlier partial
v2 field audit is historical evidence, not runtime projection authority.

## Required next gates

The v2/v5 native trials failed. Their populated geometry exports cannot enter an
electrical model. A new successful full native receipt, exact source/companion
hashes, zero rule/parity errors and all 206 selected GH plus nine main contacts
connected are mandatory. The inventory also retains all 1903 fitted K AGND
contacts. Selecting coupling ports does not set the other contacts' currents to
zero; later joined/common/voltage acceptance must include their supported loads
or independently bound their effects. Four JL utility returns additionally need
the P/rest-network operator.

Actual finite contact classes, material/process envelopes, signed current
conditions, common/private allocation and complete voltage budgets remain open.
Common J+K ground stays at most 0.5 mOhm, common rail at most 1 mOhm, each GH
contact at most 0.5 A, hot distribution at most 20 mV, and total drop at most
0.20 V. Physical qualification remains NOT RUN under #65.
