# O1 matched negative-result diagnosis

Parent accepted both NO IMPROVEMENT results and RELEASED reservations1420/1438.
Both empty proposals stay unapplied; all native slots are free. No trial was
repeated, no native process was run, and no new native admission is requested.
K1402 remains the accepted incumbent. PR260 and the epic remain open.

## What the retained trials actually establish

`mask-diagnosis.json` reconstructs the unchanged29140d4e router masks from the
complete authenticated1420/1438 artifacts, original board dumps, exact recorded
windows, matched pad polygons and pinned numerical versions. No `route`, A*, C
router or KiCad call is made. Those entry points are replaced by explicit refusal
in the diagnostic tool. Four-connected planar components, joined only at frozen
legal-via/through-terminal cells, have the same connectivity as the router's
eight-neighbor graph with corner cutting forbidden. Search costs and paths are
not computed. All proposals were empty, so no intermediate copper changed masks.

The direction is the original second anchor toward the first. `free|source|goal`
preserves endpoint overrides; own-net copper is traversable but does not silently
become an alternate landing. Existing complete native groups remain preservation
obligations. The table uses the last recorded window for each demand.

| Demand / source → goal | K1402 source / goal cells | two-A source / goal cells | Concrete frozen-graph cause |
| --- | --- | --- | --- |
| +12V C1134.1 → U1109.4 |209 /59|31093 /59|Goal is exactly59terminal cells, zero free exits and zero via sites. K source additionally has no via access; two-A source reaches multiple layers but cannot enter the same boxed goal.|
| -12V C1135.1 → U1109.11 |27486 /56|35106 /56|Goal is exactly56terminal cells, zero free exits and zero via sites on both boards.|
| AGND C1111.2 → U1105.12 |68548 /145|82279 /145|Search hit50000expansions, but complete component analysis shows an isolated145-cell F.Cu goal with no via site. The cap masked graph disconnection; it was not the sole obstacle.|
| TRI_SUM U1114.6 → R1177.2 |395 /705|395 /705|Two separate B.Cu regions with no legal via site, with identical extents/counts on both boards. Local pad exits exist but cannot reach the other region.|

All four graphs are disconnected in every recorded window. Raising the search
cap cannot connect these unchanged graphs. No failure reached fill-guard veto;
no endpoint is absent from the window. Extra open region on two-A is observable
but does not repair the identical terminal bottlenecks. This sample therefore
cannot distinguish an architecture advantage under the frozen method. It does
not establish continuous physical impossibility or prove that placement must move.

## Clearance evidence and its boundary

The additional source screen examines blocked four-neighbor centers around small
endpoint components, using the same widths/clearance with actual dump pad polygons,
analytic track/via radii, nonplated drills, physical outline and track keepouts.
It is a **pointwise center-clearance screen**, not an edge sweep, via-landing,
contact-cross-section, native DRC, electrical or physical qualification.

- U1109.4 and U1109.11 have0legal blocked boundary centers on either board.
  The best margins are−0.040008mm and−0.054851mm at the0.5mm rail width and
  0.25mm clearance. Nearest constraints at those points are adjacent U1109.5
  and U1109.10 pads. The0.25mm pad-edge gaps and fine-pitch terminal geometry
  are a concrete local access constraint, even after removing raster inflation
  at these tested centers. This is not a proof that every off-grid, finite-width
  terminal connection is impossible.
- U1105.12 has22blocked boundary centers which satisfy unchanged point-clearance
  requirements; best margin0.087764mm. The raster's conservative inflation
  excludes real point-clearance space near this terminal.
- TRI_SUM source/goal have73/139such centers on both boards, best margins
  0.116241/0.116551mm. These witnesses show raster pessimism, not a continuous
  route or legal via transition. K1402 C1134.1 likewise has50point witnesses.

The conservative raster expands obstacles by a cell half-diagonal, then requires
clearance plus half-width plus another half-diagonal and0.01mm. That policy is a
screen for subsequent native verification, not a proof that all rejected geometry
is physically blocked. Do not remove safety margins globally on this evidence.
Nearby-copper lists in the JSON are context only, not exhaustive causal attribution;
the separately labeled boundary screen includes vias, drills and keepouts.

## Smallest justified next change

Continue with a **source-only exact terminal-access adapter/checker** on these
same four demands and both authenticated original boards before requesting another
route. Retain the common bounds, source identities, complete original groups,
0.5mm rail/0.3mm signal widths,0.25mm clearance, via rules, all successful copper,
fixed panel and electrical obligations. Validate local off-grid terminal-contact
geometry and the full swept copper of each candidate local edge, not only its
end centers. Include rounded pad corners, neighboring pads/tracks/vias, keepouts,
edge clearance, via barrel/drill/SMD restrictions and contact cross-section.

The checker must demonstrate a legal finite-width escape into usable free space
for the blocked terminals without hidden neck-down or reducing required clearance.
Source counterexamples must reject center-only clearance, corner crossing,
invalid via access and a tiny tangential pad overlap presented as adequate contact.
Only after those source gates and independent review should a new matched method
revision and bounded route request be prepared. If the rail contacts require a
narrower section or changed placement, stop and quantify the electrical/design
change; it is outside this diagnosis. Do not select a different pair merely because
it is easier or already connected; the previously defined F3/E1 samples would
need the same source/terminal-access screen before selection.

**No new native request is justified yet.** No repeat, budget increase, wider
window, fallback, copper removal, placement change or subsequent native phase.
The source analysis is useful precisely because it resolves the capped AGND
ambiguity without spending another native slot.

## Reproduction and checks

Use numpy2.2.6/scipy1.15.3/shapely2.1.2 and the complete retained ZIPs:

```sh
python3 circuit/routing/epic-242/decision-pilots/diagnosis-o1/analyze.py \
  --k /path/to/epic242-route-1420-38147266896.zip \
  --two-a /path/to/epic242-route-1438-38148185181.zip \
  --output /tmp/mask-diagnosis.json
python3 -m unittest discover \
  -s circuit/routing/epic-242/decision-pilots/diagnosis-o1 -p 'test*.py'
```

The tool checks complete ZIP hashes/CRCs, original board/dump bindings, frozen
router bytes, manifest/spec hashes and numerical versions. Six tests cover graph
connectivity against an independent eight-neighbor reference and explicit corner,
via, blocked-layer, through-terminal, foreign-via, NPTH and keepout counterexamples.
Independent review reproduced all component counts and disconnections. Source
results do not replace native preservation/full-warning/eligibility gates.


## Parallel tolerance/clearance progress

[Finite-collet clearance](../feed-arrangement/collet-clearance.md) adds a
reproducible conditional bound for the revised58mm feed arrangement. The exact
flat-ended cylinder, including the C1-derived axis cone and all independently
summed profile/warp/thermal/retention/registration allowances, leaves
0.447966035mm to its own board against0.25mm required. All12collets were also
screened against2430source reservations with no broad-phase omission; minimum
remaining XY gap is3.233303944mm. The source requirements are explicit, not
supplier capability or actual assembly evidence. Support arms/joints,
wire-to-new-collet/arm, complete feed collisions, material/retention, actual shape,
physical fit and native gates remain OPEN. No mechanical producer, physical
part, canonical board or copper changed.

Final checks PASS:6diagnostic tests,23feed-arrangement tests, deterministic collet
receipt check, baseline verifier and circuit/docs/TypeScript checks. Independent
baseline review reproduced the complete mask-diagnosis.json byte-for-byte and
reviewed the pointwise screen. The coordinator separately ran all23feed tests and
reviewed the finite-cylinder support bound. Component check scope remains manual
inventory68lines/0declaredplacements, with no schematic/placement binding.
