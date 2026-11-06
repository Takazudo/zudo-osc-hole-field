# Stage50 — specification-based R8270 / off-pad via screen

Stage49 remains the accepted **disposable** routing study, not canonical CAD.
This stage changes no board, net, hardware, stackup, footprint, manufacturing output
or component assignment. It resolves the courtyard concern as a conditional source
calculation and records the remaining identity/process decisions. No additional
routing candidate is proposed: changing copper cannot resolve a missing BOM binding,
and courtyard overlap alone supplies no supported reason to disturb the passing route.

## Exact identity boundary

There is **no populated R8270 manufacturer/part assignment in the existing records**.
The JL netlist entry R8270 (M5B, 5600 ohm, R0603) has empty MPN, Manufacturer and LCSC
fields. `design/architecture-278/source-ledger.json` /packages entry R8270 likewise
has empty mpn, dnp=false, instance=M5B, current_board=JL. Inventory /lines/33 is a
representative 100 kohm Yageo RC0603FR-07100KL with no declared placements.
`scripts/schgen/README.md` explicitly keeps differing-value passive instance MPNs
blank. The inherited library symbol is not a 5.6 kohm population assignment.
The existing BOM-named files found in the project concern Stage36 connector coupons.

**Conditional standard candidate:** Yageo RC0603FR-075K6L, 5.6 kohm, 1%, 0603/1608,
tin terminations. No LCSC code is inferred; electrical suitability and adoption are
not decided here. [Exact manufacturer spec](https://yageogroup.com/component-documentation/download/specsheet/RC0603FR-075K6L),
physical PDF page 0, unnumbered, Dimensions/drawing, generated 2026-10-19:
L=1.6±0.1, W=0.8±0.1, T=0.45±0.1, B1/B2=0.25±0.15 mm.
The dimension drawing was visually inspected; terminal metal lies within the stated
external length/width. This bounds the component, not solder fillets. The
[RC-series datasheet](https://yageogroup.com/content/datasheet/asset/file/PYU-RC_GROUP_51_ROHS_L)
is retained locally for corroboration, not used to assign a populated part.
`sources.json` binds inspected downloaded bytes; raw PDFs/HTML stay ignored.

## Geometry and finite error budget

The inherited Stage49 source receipt binds native-derived pads and board settings.
At the fixed R8270 centre (270.31,133.94), rotation 90°, the maximum candidate body
rectangle is x=[269.86,270.76], y=[133.09,134.79] mm. The LED_K via centre is
(271.32,132.8), copper diameter 0.60, hole 0.30 mm.

| Source comparison | Result | Meaning |
|---|---:|---|
| Maximum body/termination envelope to annulus | 0.330635 mm | No nominal-position intersection |
| Maximum body/termination envelope to hole | 0.480635 mm | Nominal hole only; no diameter tolerance assumed |
| Nearest R8270:2 copper / nominal mask opening to annulus | 0.280 mm | Off-pad, no nominal aperture intersection |
| Same pad/opening to hole | 0.430 mm | Source geometry only |
| Courtyard intrusion, annulus / hole | 0.20 / 0.05 mm | Preserved Stage49 fact, not body collision |

The closest maximum-body corner is separated from the via centre by (0.56,0.29) mm;
Euclidean distance minus 0.30 gives the first result. Even arbitrary rotation about
the fixed centre is conservatively bounded by the component circumcircle:
`hypot(1.01,1.14) - hypot(0.85,0.45) - 0.30 = 0.261286935 mm`.
Thus combined relative radial translation, positive copper-radius growth, solder
extension and any required clearance must sum to **less than 0.261286935 mm** for
that conservative nonintersection proof. Equality allows touching. This is an
available geometric budget, **not an asserted assembler placement tolerance**.
For a fixed 90° part, the corresponding budget is 0.330634601 mm.
There is no source basis here for allocating those budgets among process errors.
Height is at most 0.55 mm before solder seating; no out-of-plane fit is inferred.

## Published JLCPCB criteria and applicability

The current [PCB capability table](https://jlcpcb.com/capabilities/pcb-capabilities)
permits 1:1 mask openings and specifies 0.09 mm opening-to-neighboring-trace spacing.
Applying that distance conservatively to this via annulus gives 0.190 mm nominal
margin. This is a source screen, not approval of a finished mask. Its ink-plugging
row requires 0.35 mm to other mask openings: the annulus-based screen is **0.070 mm
short**. Do not select ink plugging on this evidence. Published via-in-pad epoxy/
copper filling defaults for six-layer boards do not prove the eventual order's
chosen process. The 0.15–0.55 mm diameter wording must not be used to infer that a
0.60 mm copper annulus is rejected; hole versus pad interpretation/order is unresolved.

The [via-covering guide](https://jlcpcb.com/help/article/pcb-via-covering) distinguishes
tenting from ink plugging. A 0.30 mm nominal hole is below its 0.40 mm ideal tenting
limit and 0.50 mm maximum; limited opening separation can compromise coverage.
The inherited board requests both-side tenting, but CAD settings are not factory
process acceptance. Tenting can leave tin beads; a requirement forbidding those
needs a different process decision. No numerical via-hole diameter tolerance is
promised; do not borrow the component-PTH +0.13/−0.08 mm allowance. See also the
[via/pad-hole distinction](https://jlcpcb.com/help/article/difference-and-tolerance-explanation-between-via-and-pad-holes).

The [assembly capabilities](https://jlcpcb.com/capabilities/pcb-assembly-capabilities)
include 0603 within supported package sizes; Standard supports both faces. Package
size support is not this layout's acceptance, and no quantitative placement-tolerance
bound was located there. The [0.18 mm 0603 spacing recommendation](https://jlcpcb.com/help/article/minimum-spacing-for-smd-components)
is component-to-component; it is not a via-to-body limit. No courtyard-to-via rule
was found in these sources. Nominal mask apertures, not generated Gerbers, were
compared. Mask colour, copper weight, finish, selected service and actual process
remain eventual order inputs; nothing was ordered or sent.

## Decision and continuation

Keep Stage49 as a conditional routing candidate. Do not reroute solely to clear the
courtyard, and do not claim assembly qualification. The minimal remaining source
work is an explicit value-specific passive identity decision, including electrical
rating suitability, followed by a scoped component evidence/placement binding.
Use that result and a selected published assembly process to allocate the error
budget above. If a supported requirement consumes it, propose the smallest local
routing alternative and repeat full retained-partition/DRC/two-build acceptance.
No such requirement or alternative is silently adopted here.

Unrelated source progress can continue immediately: select the next isolated JL
open from Stage45's 90-net inventory, retain fixed hardware/netlist/stackup and
require exactly its intended partition merge with no new rule/parity errors or
uncapped warnings. Parent chooses that scope; this stage does not start it.
No standard connector test order is required by this result. Earlier wire, service,
mechanical, capped-silk and physical gates remain unresolved.

Before eventual assembly acceptance, record the actual resistor MPN and part drawing,
selected via-covering process and mask apertures. In an ordinary unpowered integrated
prototype inspection, verify correct population, no exposed-via/solder bridge near
R8270, unobstructed resistor seating and no conductive debris; compare measured
clearance plus measurement uncertainty with the explicitly chosen process criteria.
If any necessary tolerance or criterion is missing, record UNRESOLVED; do not invent
a pass threshold. No separate coupon purchase or energized test is requested.
