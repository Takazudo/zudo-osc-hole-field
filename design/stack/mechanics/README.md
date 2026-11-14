# ST-03 stack mechanics (paper study)

Status: **PROPOSAL, unvalidated draft.** Campaign `osc-stack-20261114`, task ST-03, attempt a1 (parametric start), base `91246e9`. This study proposes; the design authority decides. Fit, force, alignment, strain and seating of the stack are **NOT RUN**: no exact connector is selected and no specimen exists (#65).

Every number below is recomputed from [`stackups.json`](stackups.json) by `python3 scripts/stack/mechanics/stack_mechanics.py`. The tables sit between `calc:` markers; `--write-readme` refreshes them and the unit tests fail if they differ. Each term carries a status: SOURCED (file or retrieved page with SHA256), DERIVED (formula) or ASSUMED (reason and what would source it). Connector figures are parameters: allowed misalignment `a` in {0.1, 0.2, 0.3, 0.5} mm, mating force per position `f` in {0.3, 0.5, 1.0} N and mated-height tolerance `t` in {0.1, 0.2, 0.3} mm.

Z is measured from the panel front face, negative toward the rear. "WC" is the arithmetic worst case of the term limits; "RSS" is their root sum of squares, which treats the terms as independent limits of similar confidence. RSS is not a yield figure.

## Neither order closes on worst case; on RSS the pairs close only for a ≥ 0.5 mm and stack-first fails every panel aperture

- **XY at the pairs.** With the best locating scheme per board, the worst pair misses by 0.89 to 1.03 mm on worst case, which fails at every `a`. On RSS, JL, JR, the P unit and EL close for `a` ≥ 0.5 mm and the adapters for `a` ≥ 0.3 mm with two corner locating pins. Using two end power posts as pilots fails at every `a`, because all six posts of a board sit in one row.
- **Panel apertures, stack first.** With K as the XY master and the panel fitted last, every hardware class fails on RSS against its current aperture: jacks by 0.295 mm, pots 0.243, toggles 0.206, buttons 0.185 and selectors 0.128. Closing on RSS needs holes of about 6.8 (jack, pot), 5.6 (toggle), 5.4 (button) and 7.3 mm (selector). Those diameters are owner artwork matters and are not proposed here. **NEEDS_DESIGN.**
- **Panel first, K floating.** The apertures then hold only hardware float, by construction. The pairs see the front-board-to-panel chain and close on RSS for `a` ≥ 0.5 mm at J and P. The adapters fail at every `a` in this order unless they are pinned to K (see the datum section).
- **Z.** The gap budget closes only if a tie post or fastener lies within 15.5 to 23 mm of every pair, and if ST-01's usable wipe is at least 0.43 to 0.83 mm on RSS (0.78 to 1.18 mm WC) for `t` = 0.1 to 0.3 mm. With the six power posts alone the bow term reaches 2.6 to 3.2 mm and nothing closes. JR has only 3 interior fastener candidates. **NEEDS_DESIGN** (part moves on K or JR).
- **K strain.** Over the 15 to 19 mm between the J and P post rows, K tolerates only 0.028 to 0.045 mm of plane mismatch at the design limit of 593 microstrain. If P is also fixed to the panel, the mismatch is 0.90 mm WC and the strain exceeds the ceramic test level many times over. P must be free in Z on its panel side. A rigid rear jam nut on P's toggles interferes by 0.03 mm nominally. **NEEDS_DESIGN.**
- **EL.** At every `f`, the 0.4 mm EL without backing exceeds the strain design limit. It needs a full-face backing platen for seating and removal.

## Recommended datum scheme: the panel sets the front boards, K floats onto them, P and EL follow in Z

| Board | Z plane is set by | XY position is set by | Follows | Datum status |
| --- | --- | --- | --- | --- |
| Panel | Front face is the Z origin; rear face at −2.0 ± 0.2 mm | Fixture or enclosure clips during closing; afterwards the jacks hold it | n/a | Thickness SOURCED (partition; ±10% from the fabricator page) |
| JL, JR | Jack shoulders on the panel rear, clamped by jack nuts: F.Cu = −2.0 − 8.0 mm | Their 100 and 80 jacks in the 6.2 mm apertures | Panel | Shoulder height ASSUMED 8.0 ± 0.2 (required value; seating datum UNSOURCED in `facts/jack.json`) |
| K | J tie posts: J rear face less the 12.9 mm posts, at the J power row (y = 160) and J tie posts | Floats onto the 197 pairs without locating pins; the post screws in oversize K holes fix it after mating | JL and JR | Post length ASSUMED ±0.05 (ST-04) |
| P (with its body carrier) | K, through its 11.1 mm posts and P tie posts. Its panel-side fixings (toggle nuts, carrier feet) must be compliant in Z | Its 101 pots, 32 toggles and 8 buttons in their apertures | K in Z, panel in XY | Toggle seat ASSUMED (2MS3 suffix gate OPEN) |
| EL | P, through the 35 collar posts (7.2 mm gap) | Two collar posts with precision collars on P; must also clear 18 pot shafts in 6.3 mm passages | P | Collar tolerance ASSUMED |
| O1, O3, O5 | K, through new O-to-K standoffs (not in the plan) | Two locating pins in K; the selector shaft floats in its 7.0 mm aperture and the carrier bore | K | Selector seat UNSOURCED (#55) |

The adapters are the exception to "panel sets XY". The selector's 0.4 mm radial aperture clearance, less its 0.2 mm wobble allocation, leaves too little float to locate a board. They therefore take XY and Z from K. Even so, K's float relative to the panel (about 0.33 mm RSS at J) exceeds the selector's 0.2 mm, so the selector row is **NEEDS_DESIGN** in either order.

| Scheme | What it is | Measured trade-off | Proposal |
| --- | --- | --- | --- |
| A. Panel sets front-board XY, J sets Z, K floats, P free in Z | As above | Apertures close by construction; J and P pairs close on RSS at a ≥ 0.5; K strain from P only through the take-up residual; the factory close equals every service refit | **Recommended** |
| B. K is the XY and Z master; front boards pinned to K; panel last (the plan's order) | Plan page "Assembly order" | Pairs close on RSS at a ≥ 0.5 (0.348 to 0.355 mm); every panel aperture class fails on RSS by 0.128 to 0.295 mm | Alternative; needs enlarged apertures |
| C. P sets K's plane; J follows K | P located by its carrier and toggles | J is clamped to the panel by 180 jack shoulders and cannot follow; any mismatch bends K across the 68 mm seam span or the 15 to 19 mm row span | Rejected on the strain tables |

## Panel first, K last closes the apertures and matches every service refit; its cost is one blind 777-position mate

| Criterion | Stack first, panel last | Panel first, K last (recommended) |
| --- | --- | --- |
| Pairs mating at once | One board at a time: 36 (EL), 10 per adapter, 423 (P unit), 162 (JL), 162 (JR) | 36 when the P unit is built, then 777 at once |
| Mating force (f = 0.3 / 0.5 / 1.0 N) | Largest step, the P unit: 127 / 212 / 423 N | 233 / 388 / 777 N |
| Reaction path | Post screws draw each front board onto K; the loop closes through the posts | Post screws draw K onto the front boards; the same internal loop; the panel and hardware solder joints carry nothing |
| What locates the 438 hardware centres in their apertures | K and the pins, through the board chain: 0.33 to 0.37 mm RSS against 0.06 to 0.2 mm of clearance. **Fails** | The apertures themselves; the hardware is fitted and its nuts tightened before K arrives |
| What locates the pairs | Two pins per board in K | The front boards' aperture float; K best-fits on the pairs' lead-in |
| Inspection and rework | Each pair seen before the next board; a bad board is removed alone | The front faces of the pairs are hidden once K is down; inspection must be by continuity |
| Service | Rear service is panel-first anyway: K comes off the panel-held front boards and goes back on the same way | Identical to service, so the factory close proves the service refit |

The strongest counter-argument against the recommendation: every K closure mates 777 positions blind. One bent contact cannot be seen, and the force is 233 to 777 N. The order also asks more of the connector. It closes only if ST-01 shows `a` ≥ 0.5 mm, and the pairs then become the XY guide for K. Guiding is not a structural load path, but lateral force from a guide lands on the pads. Stack first avoids this, but only by moving the error into the panel apertures, where it fails.

## The XY budget closes on RSS for a ≥ 0.5 mm with corner pins and fails on worst case at every a

Misalignment at the worst pair, radial, stack-first (front board pinned to K; EL pinned to P). "Ratio r/L" is the distance from the primary feature to the farthest pair over the distance between the two features. Corner pins sit at 0.9 of the board diagonal (ASSUMED placement). The end posts are the outermost power posts of the board's single post row.

<!-- calc:xy_summary -->
| Pair group | Locating scheme | H, mm | Ratio r/L | Worst case, mm | Worst case against a | RSS, mm | RSS against a |
| --- | --- | --- | --- | --- | --- | --- | --- |
| JL to K | two corner pins, press-fit hole class | 12.900 | 1.07 | 1.031 | fails at every a | 0.355 | closes for a >= 0.5 |
| JL to K | two corner pins, ordinary hole class | 12.900 | 1.07 | 1.091 | fails at every a | 0.370 | closes for a >= 0.5 |
| JL to K | two end posts as pilots, ordinary hole class | 12.900 | 2.20 | 1.563 | fails at every a | 0.596 | fails at every a |
| JR to K | two corner pins, press-fit hole class | 12.900 | 1.07 | 1.028 | fails at every a | 0.354 | closes for a >= 0.5 |
| JR to K | two corner pins, ordinary hole class | 12.900 | 1.07 | 1.088 | fails at every a | 0.369 | closes for a >= 0.5 |
| JR to K | two end posts as pilots, ordinary hole class | 12.900 | 2.06 | 1.505 | fails at every a | 0.566 | fails at every a |
| P unit to K | two corner pins, press-fit hole class | 11.100 | 1.06 | 1.010 | fails at every a | 0.348 | closes for a >= 0.5 |
| P unit to K | two corner pins, ordinary hole class | 11.100 | 1.06 | 1.070 | fails at every a | 0.363 | closes for a >= 0.5 |
| P unit to K | two end posts as pilots, ordinary hole class | 11.100 | 2.28 | 1.581 | fails at every a | 0.611 | fails at every a |
| O1/O3/O5 to K | two corner pins, ordinary hole class | 6.900 | 0.71 | 0.887 | fails at every a | 0.299 | closes for a >= 0.3 |
| EL to P | two corner pins, ordinary hole class | 7.200 | 0.96 | 0.995 | fails at every a | 0.339 | closes for a >= 0.5 |
<!-- /calc:xy_summary -->

Term breakdown at the farthest P-unit pair (the 135-pair board) with corner pins in the press-fit class. The same budget applies to P's pairs in the panel-first order when K is pinned to P:

<!-- calc:xy_terms -->
| Term at the farthest P-unit pair (recommended scheme) | mm, radial | Status |
| --- | --- | --- |
| SMT float, front half | 0.100 | ASSUMED |
| SMT float, carrier half | 0.100 | ASSUMED |
| stacker lean at the tip | 0.097 | ASSUMED |
| primary hole position, front board | 0.106 | DERIVED from SOURCED |
| primary hole position, carrier board | 0.106 | DERIVED from SOURCED |
| primary pin-in-hole float | 0.058 | DERIVED from SOURCED + ASSUMED |
| rotation: secondary slot float x ratio | 0.125 | DERIVED |
| rotation: front hole pair spacing error x ratio | 0.159 | DERIVED |
| rotation: carrier hole pair spacing error x ratio | 0.159 | DERIVED |
| Sum (worst case) | 1.010 | DERIVED |
| Root sum of squares | 0.348 | DERIVED |
<!-- /calc:xy_terms -->

The three rotation terms dominate. The fabricator states ±0.075 mm hole position per hole, and nothing tighter for the spacing between two holes. Corner pins keep the lever ratio near 1. Pins at the six-post row put it at 2.1 to 2.3, which is why posts as locators fail. The press-fit hole class (±0.05 mm) helps by only 0.015 mm on RSS. It also requires multilayer ENIG boards: JL, JR (6 layers) and P (4 layers) qualify by layer count, while EL and the adapters (2 layers) do not.

Panel first (the recommended order) compared with stack first. "K pinned to P" uses locating pins between K and P with all hardware nuts tight. "K floating" has no K pins, and K best-fits on the pairs:

<!-- calc:panel_first -->
| Pair group | K pinned to P: WC, mm | WC against a | RSS, mm | RSS against a | K floating: WC, mm | RSS, mm | RSS against a | Stack first RSS, mm |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| JL to K | 2.130 | fails at every a | 0.553 | fails at every a | 0.840 | 0.334 | closes for a >= 0.5 | 0.355 |
| JR to K | 2.130 | fails at every a | 0.553 | fails at every a | 0.840 | 0.334 | closes for a >= 0.5 | 0.354 |
| P unit to K | 1.010 | fails at every a | 0.348 | closes for a >= 0.5 | 0.874 | 0.363 | closes for a >= 0.5 | 0.348 |
| O1/O3/O5 to K | 2.462 | fails at every a | 0.782 | fails at every a | 1.172 | 0.645 | fails at every a | 0.299 |
<!-- /calc:panel_first -->

## Stack-first panel apertures fail at every hardware class; holes about 0.4 to 0.6 mm larger would close on RSS

Error of each hardware axis against its aperture when the panel is fitted last over a stack located on K. The panel is assumed to best-fit near K's nominal position, because six board groups err independently. Minimum radial clearance = (minimum hole − maximum part) / 2 − wobble allocation. The indicator windows have no mechanical clearance and no acceptance limit (#64), so only their error is reported. The EL passage rows are EL against hardware on P and apply in both orders.

<!-- calc:apertures -->
| Class | Worst board | Hole / min radial clearance, mm | Stack-first error WC, mm | RSS, mm | Verdict | Hole for WC, mm | Hole for RSS, mm |
| --- | --- | --- | --- | --- | --- | --- | --- |
| jack | JL | 6.2 / 0.060 | 1.030 | 0.355 | WC fails by 0.970; RSS fails by 0.295 | 8.14 | 6.79 |
| pot | P | 6.3 / 0.110 | 1.025 | 0.353 | WC fails by 0.915; RSS fails by 0.243 | 8.13 | 6.79 |
| toggle | P | 5.2 / 0.147 | 1.025 | 0.353 | WC fails by 0.878; RSS fails by 0.206 | 6.96 | 5.61 |
| sub_toggle | P | 5.2 / 0.147 | 1.025 | 0.353 | WC fails by 0.878; RSS fails by 0.206 | 6.96 | 5.61 |
| button | P | 5.0 / 0.185 | 1.075 | 0.370 | WC fails by 0.890; RSS fails by 0.185 | 6.78 | 5.37 |
| selector | O1 | 7.0 / 0.200 | 0.974 | 0.328 | WC fails by 0.774; RSS fails by 0.128 | 8.55 | 7.26 |
| el_passage_pot | EL | 6.3 / 0.110 | 1.044 | 0.351 | WC fails by 0.934; RSS fails by 0.241 | 8.17 | 6.78 |
| el_passage_switch | EL | 11.0 / 0.666 | 1.044 | 0.351 | WC fails by 0.378; RSS closes | 11.76 | 10.37 |
| el_passage_button | EL | 9.5 / 0.326 | 1.044 | 0.351 | WC fails by 0.719; RSS fails by 0.025 | 10.94 | 9.55 |
| indicator | EL | window, no limit | 1.757 | 0.464 | no acceptance limit exists (#64) | n/a | n/a |
<!-- /calc:apertures -->

In the recommended order the panel rows do not apply: each front board settles in its apertures before K mates. The EL passage for the 18 pots remains: 6.3 mm passages against Ø6 shafts fail on RSS by 0.241 mm because EL is located on P through pins. **NEEDS_DESIGN:** enlarge the EL pot passages to about 6.8 mm, or locate EL on the pot shafts themselves.

## The Z gap closes only with tie posts within 15.5 to 23 mm of every pair and a usable wipe of at least 0.43 to 0.83 mm on RSS

The posts set each gap. A pair must neither bottom nor lose engagement across the gap error plus its own ±`t`. The usable engagement (wipe) it needs is therefore 2 × (`t` + gap error). ST-01 must show a wipe at least that large. Residual bow uses a 0.05 mm allocation per board (ASSUMED). That allocation holds only if every pair lies within `d_req` of a post or tie post.

<!-- calc:z_gap -->
| Pair | Bow basis | Gap error WC, mm | RSS, mm | Required usable wipe at t = 0.1, WC / RSS, mm | Required usable wipe at t = 0.2, WC / RSS, mm | Required usable wipe at t = 0.3, WC / RSS, mm |
| --- | --- | --- | --- | --- | --- | --- |
| JL to K, 12.9 mm | fasteners at d_req | 0.290 | 0.115 | 0.78 / 0.43 | 0.98 / 0.63 | 1.18 / 0.83 |
| JL to K, 12.9 mm | posts only | 4.532 | 3.194 | 9.26 / 6.59 | 9.46 / 6.79 | 9.66 / 6.99 |
| JR to K, 12.9 mm | fasteners at d_req | 0.290 | 0.115 | 0.78 / 0.43 | 0.98 / 0.63 | 1.18 / 0.83 |
| JR to K, 12.9 mm | posts only | 4.819 | 3.487 | 9.84 / 7.17 | 10.04 / 7.37 | 10.24 / 7.57 |
| P to K, 11.1 mm | fasteners at d_req | 0.290 | 0.115 | 0.78 / 0.43 | 0.98 / 0.63 | 1.18 / 0.83 |
| P to K, 11.1 mm | posts only | 4.368 | 3.060 | 8.94 / 6.32 | 9.14 / 6.52 | 9.34 / 6.72 |
| EL to P, 7.2 mm | allocation | 0.290 | 0.115 | 0.78 / 0.43 | 0.98 / 0.63 | 1.18 / 0.83 |
| O to K, 6.9 mm, adapters on K standoffs | allocation | 0.290 | 0.115 | 0.78 / 0.43 | 0.98 / 0.63 | 1.18 / 0.83 |
| O to K, 6.9 mm, adapters held by the selector carrier | allocation | 0.960 | 0.384 | 2.12 / 0.97 | 2.32 / 1.17 | 2.52 / 1.37 |
<!-- /calc:z_gap -->

Bow at the farthest pair with the six power posts alone, and the fixing distance `d_req` that keeps bow within the allocation (0.75% bow ratio, SOURCED as an attributed IPC figure; uniform-curvature model ASSUMED):

<!-- calc:bow -->
| Board | Longest side L, mm | Farthest pair from a post d, mm | Bow at d, mm | d_req for the bow allocation, mm |
| --- | --- | --- | --- | --- |
| JL | 172.500 | 126.649 | 2.790 | 16.956 |
| JR | 144.000 | 123.179 | 3.161 | 15.492 |
| P | 316.000 | 167.094 | 2.651 | 22.949 |
| EL | 113.000 | 8.500 | 0.019 | 13.723 |
| K | 310.000 | 126.649 | 1.552 | 22.730 |
<!-- /calc:bow -->

Holding the adapters by the selector carrier instead of K puts the panel-to-K chain into a 6.9 mm gap: 0.960 mm WC. They therefore need O-to-K standoffs. JL's 37 and P's 26 interior candidates can meet `d_req` if ST-02 confirms their positions. JR's 3 cannot. **NEEDS_DESIGN** for JR tie-post sites, by part moves on K or JR.

## K tolerates only 0.028 to 0.045 mm of plane mismatch across the J and P post rows, so P must be free in Z

Strain limit for ceramic parts: the inventory MLCC's manufacturer specification (Murata GRM1885C1H103JA01, SOURCED) passes a substrate bending test at 1 mm flexure on a 90 mm three-point span of 1.6 mm FR4. That is 6tδ/L² = 1185 microstrain at the surface. It is a pass condition, not a damage threshold, so half of it, 593 microstrain, is used as the design limit (factor ASSUMED). The X5R/X7R families fitted on K have their own bending figures, which were not retrieved. K is modelled as a fixed-guided strip between the two post rows: ε = 3tΔ/s² (ASSUMED model).

<!-- calc:strain_allow -->
| Span s, mm | Allowed Delta at design limit 593 microstrain, mm | Allowed Delta at test level 1185 microstrain, mm |
| --- | --- | --- |
| 15.000 | 0.028 | 0.056 |
| 19.000 | 0.045 | 0.089 |
| 68.000 | 0.571 | 1.142 |
<!-- /calc:strain_allow -->

<!-- calc:strain -->
| Case | Span s, mm | Delta WC, mm | Delta RSS, mm | Strain WC, microstrain | Strain RSS, microstrain | Verdict (WC) |
| --- | --- | --- | --- | --- | --- | --- |
| P pulled by toggle front nuts only (nominal gap closed) | 15.000 | 2.060 | 1.160 | 43947 | 24747 | exceeds test level |
| P clamped to panel at a fixed stop and bolted to K | 15.000 | 0.900 | 0.373 | 19200 | 7965 | exceeds test level |
| P free in Z, measured take-up at its panel fixings | 15.000 | 0.050 | 0.050 | 1067 | 1067 | within test level only |
| P pulled by toggle front nuts only (nominal gap closed) | 19.000 | 2.060 | 1.160 | 27391 | 15424 | exceeds test level |
| P clamped to panel at a fixed stop and bolted to K | 19.000 | 0.900 | 0.373 | 11967 | 4964 | exceeds test level |
| P free in Z, measured take-up at its panel fixings | 19.000 | 0.050 | 0.050 | 665 | 665 | within test level only |
| JL and JR planes both from jack shoulders, K bolted to both | 68.000 | 1.009 | 0.399 | 1047 | 415 | within test level only |
| K pulled flat from 0.75% bow at fixings | n/a | n/a | n/a | 155 | 155 | within design limit |
<!-- /calc:strain -->

A measured shim at 0.05 mm resolution still exceeds the design limit at s = 15 mm. P's panel-side fixings must therefore be compliant, with no rigid Z stop that also clamps the panel. That means a spring element on the toggle bushings and carrier feet that touch the panel only under operating load. The seam case (JL and JR planes both from jack shoulders) stays within the test level on worst case and within the design limit on RSS.

The toggle rear stop that a clamped bushing would need does not fit:

<!-- calc:toggle -->
| Quantity | mm | Status |
| --- | --- | --- |
| Toggle body front z (P front face + body height) | -3.160 | DERIVED from SOURCED + ASSUMED |
| Panel rear face z | -2.000 | SOURCED |
| Nominal gap body front to panel rear | 1.160 | DERIVED |
| Rear jam nut thickness | 1.190 | SOURCED |
| Rear nut plus washer | 1.650 | SOURCED |
| Nominal interference of a rear jam nut | 0.030 | DERIVED |
| Gap variation from body seat and J-chain, WC | 0.400 | ASSUMED |
<!-- /calc:toggle -->

**NEEDS_DESIGN:** the take-up between P's 32 toggles and the panel. A compliant rear stop, or no rear stop with the nut tightened against a front-side spacer, keeps P free in Z. Toggle operating loads must still have a path. The design authority chooses.

## Screw-driven closing keeps the mating force inside each board pair; separating K needs 233 to 777 N through 18 jacking points

<!-- calc:forces -->
| Step | Positions | Force at f = 0.3 N, N | Force at f = 0.5 N, N | Force at f = 1.0 N, N | Per post or jacking point at each f, N | Within planning screw capacity |
| --- | --- | --- | --- | --- | --- | --- |
| Stack first, step 1: EL onto P (P unit) | 36 | 11 | 18 | 36 | 0 / 1 / 1 | yes |
| Stack first, step 2: each adapter onto K | 10 | 3 | 5 | 10 | n/a / n/a / n/a | n/a |
| Stack first, step 2: P unit onto K | 423 | 127 | 212 | 423 | 21 / 35 / 70 | yes |
| Stack first, step 2: JL onto K | 162 | 49 | 81 | 162 | 8 / 14 / 27 | yes |
| Stack first, step 2: JR onto K | 162 | 49 | 81 | 162 | 8 / 14 / 27 | yes |
| Panel first: K onto all front boards at once | 777 | 233 | 388 | 777 | 13 / 22 / 43 | yes |
| Rear service: K jacked off all front boards | 777 | 233 | 388 | 777 | 13 / 22 / 43 | yes |
<!-- /calc:forces -->

**Closing (recommended order).**

1. Build the P unit: seat EL on P against a full-face backing platen (next section) and fit the collar posts.
2. Lay the panel face down on a fixture with pockets for the nuts and the artwork. Fit JL and JR and tighten the jack nuts; their shoulders set the J plane.
3. Fit the P unit, with its toggle nuts on the compliant take-up, and the adapters.
4. Lower K, rear face up. Its post holes are oversize so that it can float. Start all 18 post screws and every tie-post screw by hand before any contact touches. The screws must engage at least the connector stroke plus lead-in, about 3 mm (ASSUMED).
5. Draw K down evenly in quarter turns. One quarter turn of M2.5 is 0.11 mm, so neighbouring screws never differ by more than 0.11 mm.

**Reaction path when closing.** Mating force at the pairs → the front board in local bending → the nearest post or tie post → screw tension → K → the pairs. The loop is internal, so the panel, the jack and toggle solder joints and the enclosure carry none of the mating force. This needs the tie-post spacing of the Z section. Per post the load is at most 70 N at f = 1.0 N (P unit), within the ASSUMED 1 kN screw capacity.

**Separation (rear service).**

1. Take the rear cover off and remove the 18 post screws and the tie-post screws.
2. Insert jack screws into threaded elements on K's rear face, coaxial with each post. Each screw pushes on the post end (the post stays fixed to its front board).
3. Advance all jack screws in quarter turns.

The jacking force (233 to 777 N in total, up to 70 N per P post at f = 1.0 N) again closes inside K, post and front board. The front boards stay on the panel and their solder joints are not loaded in tension. K's rear lands each have B.Cu parts within 2.6 mm (plan page), so the threaded elements need the same part moves ST-04 lists for the screw heads. Pad retention under unmating load is an ST-01 figure.

## EL cannot be seated or removed without a full-face backing platen

EL is 0.4 ± 0.1 mm thick (SOURCED). Each site takes 6 positions. The outer sites at x = 218.5 and 303.5 lie 8.5 mm outboard of the first and last tab posts. A 17 mm strip is used as the effective width, with FR4 modulus ASSUMED at 20 GPa:

<!-- calc:el_plate -->
| EL thickness, mm | f, N | Force per site, N | Mid-span deflection, mm | Mid-span strain, microstrain | Outer-site deflection, mm | Outer-site strain, microstrain | Unbacked EL |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.400 | 0.3 | 1.8 | 0.102 | 844 | 0.203 | 1687 | exceeds design limit |
| 0.400 | 0.5 | 3.0 | 0.169 | 1406 | 0.339 | 2812 | exceeds design limit |
| 0.400 | 1.0 | 6.0 | 0.339 | 2812 | 0.677 | 5625 | exceeds design limit |
| 0.300 | 0.3 | 1.8 | 0.241 | 1500 | 0.482 | 3000 | exceeds design limit |
| 0.300 | 0.5 | 3.0 | 0.401 | 2500 | 0.803 | 5000 | exceeds design limit |
| 0.300 | 1.0 | 6.0 | 0.803 | 5000 | 1.606 | 10000 | exceeds design limit |
<!-- /calc:el_plate -->

**Seating.** Support P on a fixture plate under the six P-tab sites. Press EL with a rigid platen that has pockets for EL's front parts (1.75 mm maximum front height) and bears on the board around each site and on the 35 collar posts. Close by the collar-post screws in quarter turns. Removal reverses this: the platen is screwed to the collar posts, P is held on its fixture, and jack screws in the platen push on P-tab lands beside each site, so EL leaves flat. Prying at an edge is excluded. If the design authority rejects a platen step, fallbacks F1 to F3 of the plan apply (Q5).

## 12 supports become tie posts, 9 go, P-SUP-6 becomes a compliant guide and 65 stay in role; the seam cradle and cross-members go

<!-- calc:supports -->
| Items | Count | Disposition | Reason |
| --- | --- | --- | --- |
| JL-SUP-1..3, JR-SUP-1..3 | 6 | STAY at the same XY, change role: J-to-K tie posts (12.9 mm), no enclosure joint | Removes the second load loop through the side carrier; adds edge support to K's flatness along x = 6.5 and 311.5, where no power post exists |
| JL-SUP-4, JR-SUP-4 | 2 | GO, merged with K-SUP-3/4 | (6.5, 161.5) and (311.5, 161.5) lie 1.5 mm from K-SUP-3/4 at y = 160; one J-to-K tie post at (6.5, 160) and (311.5, 160) serves both, inside JL and JR (outline y <= 164) |
| K-SUP-3, K-SUP-4 | 2 | STAY at the same XY, change role: the merged J-to-K tie posts | As above |
| K-SUP-5..8 | 4 | STAY at the same XY, change role: P-to-K tie posts (11.1 mm), no frame joint | All four lie inside P's outline; fastening K to the frame as well as to the front boards closes a second load loop through the panel and enclosure |
| K-SUP-1, K-SUP-2 | 2 | GO as clamped supports; optional Z-compliant bumper to the rear cover | At y = 10.5 no front board lies in front of them (J starts at y = 20), so a clamp there can only reach the frame |
| P-SUP-1..5 | 5 | GO; replaced by P-to-K tie posts at interior candidates | Their 3.2 mm collars overlap K's outline edge by 1.1 mm at x = 3.5 and 314.5; moving them inward by >= 1.6 mm would clear K but still tie P to the frame |
| P-SUP-6 | 1 | STAY only as a Z-compliant guide (no axial clamp) | (314.5, 289.5) lies in K's notch (x > 258, y > 246) where no K post can reach; a clamp would fix P's plane against K's |
| P-OPT-* (30 clearance holes) | 30 | STAY | Clearance in P for the EL posts |
| EL-OPT-1..35 | 35 | STAY, change role: EL-to-P collar posts that set the 7.2 mm gap and back EL during mating; two become locators with precision collars | EL takes plane and position from P; the five at y = 172 pass through the P tab (plan page) |
| Seam rear cradle [172, 20, 182, 164], z -13.6..-11.6 | 1 | GO | Lies inside the J-to-K gap; K now holds both J boards through tie posts, so the seam needs no separate carrier. J-to-K tie posts within the seam reserves (x 172..182) replace it |
| Seam front lips [175.2, 20, 178.8, 164] | 2 | GO with the cradle | Attached to the cradle |
| Cross-members y 17..19 and y 165..167, x -2..320 | 2 | GO | Same z range as the J-to-K gap and P's plane; they reach the enclosure frame and would close the second load loop; the y 165..167 member sits 1.5 mm from the EL tab |
| Interior fastener candidates (planning screen): JL 37, P 26, JR 3 | 66 | USE as front-board-to-K tie posts at a spacing that puts every pair within d_req of a fixing; JR NEEDS_DESIGN | Posts alone leave pairs about 125 mm from the nearest fixing (bow table). JR's 3 sites cannot reach d_req without part moves on K or JR |
| Total of the 87 partition supports | 87 |  |  |
<!-- /calc:supports -->

The second load loop the plan names (K's edge posts to the frame, while K also hangs from the panel through J) is removed. K-SUP-1/2 go, and K-SUP-3..8 become tie posts to J and P. After closing, the only joints between the enclosure and the stack are the panel clips and P-SUP-6, which is compliant in Z. Supports are not panel hardware, so moving them is within scope. The interior positions remain an ST-02/ST-12 task.

## A two-board coupon of 100 × 60 mm would measure every connector and strain figure this stack-up assumes

Definition only. Building it is a fabrication and assembly order that only the owner can place (plan question Q7). No order file is produced.

<!-- calc:coupon -->
| Board | Role | Outline, mm | Thickness, mm | Contents |
| --- | --- | --- | --- | --- |
| CK | K-side coupon board | 100 x 60 | 1.6 | The tallest stackers (12.9 mm pair) at 8 x 1x6 and 8 x 1x3 sites in two rows; 2 x 1x5 at the 6.9 mm height; two press-fit locating pins; four post lands of the ST-04 pattern with their screw holes; four 0603 MLCC footprints of the K families in line with the post rows, at 15 mm and 19 mm from the posts, each with a strain-gauge pad; daisy-chain copper through every contact; fiducials at each site |
| CF | front-board coupon (J/P class) | 100 x 60 | 1.6 | Matching low sockets; one round precise locating hole and one plated slot; four WQP518MA and four PTV09A footprints soldered by the same through-hole process beside the sockets; daisy-chain return copper; post lands. Variant CF-dX has its locating hole offset by X = 0, 0.1, 0.2, 0.3 or 0.5 mm along the pair rows to impose a known misalignment |
| CE (optional) | 0.4 mm EL-class coupon | 60 x 30 | 0.4 | Two 1x6 sockets at 17 mm pitch with collar-post holes at the EL tab spacing, to test seating with and without a backing platen |

| Measurement | What it measures | Term it replaces |
| --- | --- | --- |
| C-1 | Mating and unmating force per position: force-displacement on a guided press, per pair width, at least 10 cycles | f and unmate_to_mate_ratio; screw and jacking loads |
| C-2 | SMT float: optical coordinate measurement of each socket and stacker body against its fiducials after reflow | smt_float_front, smt_float_k |
| C-3 | Reflow lean and standoff: tip true position of each stacker pin and housing height above board | pin_lean_deg, connector_standoff_tol |
| C-4 | Alignment yield: mate CF-dX variants and record first-pass mates, continuity of every daisy chain, and damaged contacts | a (the usable misalignment of the real pair, not only the catalogue figure) |
| C-5 | Usable wipe: continuity of every chain while the post gap is raised in 0.05 mm shim steps from bottomed to open | w, the usable mated-height range used in the Z table |
| C-6 | K strain: strain gauges at the MLCC sites while shims of 0.025 to 0.2 mm under one post row impose Delta; MLCC capacitance and cracking after | k_strain_model and the strain limit |
| C-7 | Through-hole process compatibility: inspect open sockets for flux and solder after the jack and pot soldering | plan requirement 6 (process), with ST-01 |
| C-8 | EL seating (optional CE): deflection and strain at f with and without the backing platen | fr4_modulus for 0.4 mm and the EL seating method |
<!-- /calc:coupon -->

## Eight connector figures from ST-01 finish the task

<!-- calc:st01 -->
| Figure | Exact need from ST-01 |
| --- | --- |
| a | Allowed mating misalignment, radial or per axis, for the 1x3, 1x5 and 1x6 pairs at each mated height (6.9, 7.2, 11.1, 12.9 mm), with the drawing locator |
| f | Mating force per position (maximum) and unmating force per position (minimum and maximum), with cycle condition |
| t | Mated-height tolerance of each pair (stacker post height tolerance plus socket seating) |
| w | Usable contact engagement (wipe) range: the gap interval over which every contact is made without bottoming |
| lean | Pin true position or tip coplanarity of the tallest stacker after reflow (or the manufacturer's statement that none is given) |
| standoff | Housing coplanarity and seated height tolerance of each half |
| pegs | Whether a peg or hold-down option exists in the courtyard; this replaces the SMT float assumption |
| retention | Pad or housing retention force under unmating load (for the 777-position jacking) |
<!-- /calc:st01 -->

With these figures each "against a" column becomes a single verdict. The Z table compares the required wipe with `w`. The force table selects one column. C-2 and C-3, or ST-01 equivalents, replace the SMT-float, lean and standoff assumptions, which are about half of every XY and Z budget.

## Six items need the design authority

1. Closing order and datum scheme: panel first with K floating (recommended), or stack first with the panel apertures enlarged by about 0.4 to 0.6 mm (owner artwork).
2. Toggle take-up on P: compliant rear stop or other means. A rigid jam nut interferes by 0.03 mm, and any rigid stop over-constrains K.
3. Selector row: K's float (about 0.33 mm RSS) exceeds the 0.2 mm left after the selector's wobble allocation, in either order.
4. EL pot passages: 6.3 mm fails on RSS by 0.241 mm. Enlarge them to about 6.8 mm or locate EL on the shafts.
5. JR tie posts: 3 candidates cannot meet `d_req` (about 15.5 mm). Part moves on K or JR are needed.
6. Strain safety factor and the bending figures of the X5R/X7R families near the post rows.

## Every term with its status

<!-- calc:terms -->
| Term | Value | Tolerance | Unit | Status | Source, formula or what would source it |
| --- | --- | --- | --- | --- | --- |
| `panel_thickness` | 2 | +/-0.2 | mm | SOURCED | S-PART: panel.thickness_mm; tolerance from S-JLC-PCB 'Thickness Tolerance (Thickness>=1.0mm) +/-10%' (the panel is a fabricated PCB) |
| `board_thickness_1p6` | 1.6 | +/-0.16 | mm | SOURCED | S-PART: boards[].thickness_mm for JL, JR, P, K, O*; tolerance S-JLC-PCB +/-10% |
| `el_thickness` | 0.4 | +/-0.1 | mm | SOURCED | S-PART: osc-stage-optical thickness_mm; tolerance S-JLC-PCB 'Thickness < 1.0 mm +/-0.1mm' |
| `jack_shoulder_to_board` | 8 | +/-0.2 | mm | ASSUMED | to source: Manufacturer drawing with a PCB seating-plane datum, or coupon measurement of seated shoulder height (#65) |
| `toggle_body_height` | 8.64 | +/-0.2 | mm | ASSUMED | to source: Exact 2MS3 drawing with seating plane, or coupon measurement |
| `toggle_nut_thickness` | 1.19 |  | mm | SOURCED | S-TOG: facts.nut_thickness_mm (MNU-2M01) |
| `toggle_washer_thickness` | 0.46 |  | mm | SOURCED | S-TOG: facts.washer_thickness_mm (MNU-2M03) |
| `p_front_face_z` | -11.8 |  | mm | SOURCED | S-PART: boards osc-control face_z_mm |
| `post_length_tol` | 0.05 |  | mm | ASSUMED | to source: ST-04 post drawing length tolerance |
| `post_seat_tol` | 0.02 |  | mm | ASSUMED | to source: ST-04 land design plus coupon C-6 gap measurement |
| `connector_standoff_tol` | 0.05 |  | mm | ASSUMED | to source: ST-01 coplanarity specification; coupon C-3 height measurement |
| `selector_seat_tol` | 0.2 |  | mm | ASSUMED | to source: #55 selector coupon |
| `bow_twist_ratio` | 0.0075 |  | 1 | SOURCED | S-JLC-WARP: FAQ Q1: 'IPC standard is 0.75%' |
| `bow_model` | kappa = 8 b / L; out-of-plane at distance d from the nearest fixing = kappa d^2 / 2 = 4 b d^2 / L |  | 1 | ASSUMED | to source: Measured flatness of the received boards (first article) |
| `bow_allocation` | 0.05 |  | mm | ASSUMED | to source: Design authority choice |
| `murata_flexure` | 1 |  | mm | SOURCED | S-MURATA-GRM18: item 11 Substrate Bending test, Flexure 1mm |
| `murata_span` | 90 |  | mm | SOURCED | S-MURATA-GRM18: Fig.2, supports 45 mm + 45 mm |
| `murata_board` | 1.6 |  | mm | SOURCED | S-MURATA-GRM18: Substrate Bending test substrate thickness 1.6mm |
| `strain_test_level` | 0.0011852 |  | 1 | DERIVED | 6 t delta / L^2 (three-point bend surface strain at mid-span) = 6 x 1.6 x 1.0 / 90^2 |
| `strain_safety_factor` | 2 |  | 1 | ASSUMED | to source: Design authority choice; bending specification of every ceramic part family fitted near the post rows |
| `strain_design_limit` | 0.0005926 |  | 1 | DERIVED | strain_test_level / strain_safety_factor |
| `k_strain_model` | fixed-guided beam: eps = 3 t Delta / s^2 |  | 1 | ASSUMED | to source: Plate FE model in ST-12 or strain-gauge coupon C-6 |
| `shim_resolution` | 0.05 |  | mm | ASSUMED | to source: Take-up hardware design (ST-12) and first-article measurement |
| `smt_float_front` | 0.1 |  | mm | ASSUMED | to source: ST-01 footprint guidance; coupon C-2 measurement |
| `smt_float_k` | 0.1 |  | mm | ASSUMED | to source: ST-01; coupon C-2 |
| `pin_lean_deg` | 0.5 |  | deg | ASSUMED | to source: ST-01 true-position or tip-coplanarity specification; coupon C-3 lean measurement |
| `hole_position_tol_axis` | 0.075 |  | mm | SOURCED | S-JLC-PCB: 'Hole Position Tolerance +/-0.075 mm' |
| `hole_position_radial` | 0.1061 |  | mm | DERIVED | sqrt(2) x hole_position_tol_axis |
| `pth_hole_tol_plus` | 0.13 |  | mm | SOURCED | S-JLC-PCB: 'Through-holes: +0.13 / -0.08 mm'; also 'Slot Hole size Tolerance Plated: +0.13 / -0.08 mm' |
| `pth_hole_tol_minus` | 0.08 |  | mm | SOURCED | S-JLC-PCB: as pth_hole_tol_plus |
| `press_fit_hole_tol` | 0.05 |  | mm | SOURCED | S-JLC-PCB: 'Press-fit holes: +/-0.05 mm (Finished hole size 0.55-2.0mm. Multilayer ENIG boards and circular holes only.)' |
| `routed_hole_position_tol_axis` | 0.1 |  | mm | SOURCED | S-JLC-PCB: '+/-0.1mm(Precision) and +/-0.2mm(Regular) for CNC routing' |
| `routed_hole_position_radial` | 0.1414 |  | mm | DERIVED | sqrt(2) x routed_hole_position_tol_axis |
| `loc_pin_diameter` | 2 | +0.0/-0.006 | mm | ASSUMED | to source: Purchased pin drawing (ST-12) |
| `loc_hole_clearance_precise` | 0.06 |  | mm | ASSUMED | to source: Design authority |
| `loc_slot_clearance` | 0.1 |  | mm | ASSUMED | to source: Design authority |
| `r_loc_precise` | 0.058 |  | mm | DERIVED | (loc_hole_clearance_precise + press_fit_hole_tol + loc_pin_diameter.minus) / 2 |
| `r_loc_standard` | 0.118 |  | mm | DERIVED | (0.10 + pth_hole_tol_plus + loc_pin_diameter.minus) / 2, a round hole of pin + 0.10 in the ordinary through-hole class |
| `r_slot` | 0.118 |  | mm | DERIVED | (loc_slot_clearance + pth_hole_tol_plus + loc_pin_diameter.minus) / 2 |
| `diag_pin_span_factor` | 0.9 |  | 1 | ASSUMED | to source: ST-02 placement of the locating holes |
| `th_lead_float` | 0.1 |  | mm | ASSUMED | to source: Lead dimensions from the drawings versus finished drill sizes; first-article axis measurement |
| `smd_led_float` | 0.1 |  | mm | ASSUMED | to source: Assembly provider placement data; #64 optical coupon |
| `button_guide_float` | 0.15 |  | mm | ASSUMED | to source: Carrier and plunger drawing (ST-12) |
| `selector_leg_float` | 0.1 |  | mm | ASSUMED | to source: #55 coupon |
| `fr4_modulus` | 20000 |  | N/mm^2 | ASSUMED | to source: Laminate datasheet of the fabricator's FR4 for the 0.4 mm EL |
| `unmate_to_mate_ratio` | 1 |  | 1 | ASSUMED | to source: ST-01 unmating force per contact |
| `screw_axial_capacity` | 1000 |  | N | ASSUMED | to source: ST-04 post and screw drawings with thread engagement |
| `m25_pitch` | 0.45 |  | mm | DERIVED | ISO metric coarse pitch implied by the M2.5 designation |
| `el_site_pitch` | 17 |  | mm | SOURCED | S-PART: connectors EL-E1..E6 centres x = 218.5 + 17k, y = 172 |
| `el_post_pitch` | 17 |  | mm | SOURCED | S-PART: supports EL-OPT-1/8/15/22/29 at x = 227 + 17j, y = 172 |
| `el_cantilever` | 8.5 |  | mm | DERIVED | 227 - 218.5: the outer EL sites (218.5 and 303.5) lie 8.5 mm outboard of the first and last tab posts |
| `el_positions_per_site` | 6 |  | count | SOURCED | S-PLAN: EL plugs into a P tab: six 1x6 pairs |
| `posts_per_board` | 6 |  | count | SOURCED | S-PLAN: Power joints: each branch keeps its six joints |
<!-- /calc:terms -->

Geometry inputs (pair counts and positions, posts, board extents, distances) are DERIVED by `scripts/stack/mechanics/stack_mechanics_geometry.py` from `partition.json`, `mechanical-candidate.json`, `placements.lock.json` and `stage-optical-candidate.json`. Their SHA256 values are stored in `stackups.json` under `geometry.sources`. The derivation reproduces the plan's 197 pairs and 777 positions on K, and 135 pairs and 423 positions on P.

## Checks: unit tests run; every physical check NOT RUN

- Run: `python3 scripts/checks/frozen_studies.py discover scripts/stack/mechanics`. The tests check that the README tables equal the calculator output, that the DERIVED terms recompute, that the geometry matches the hashed sources, that the 87 supports are accounted for, and that every term has a status with its basis.
- **NOT RUN**: installed fit, mating and unmating force, alignment yield, reflow lean, wipe, K and EL strain, take-up stiffness, thermal effects on alignment, and the coupon. No exact connector is selected and no specimen exists (#65, Q7).
- **NOT RUN**: KiCad, DRC and the regeneration gate. They are excluded by the task brief, and no board file changed.
- Not retained: the three fabricator pages and the Murata PDF were retrieved and hashed, but not stored in `circuit-dev-resources`, because this task may not write to GitHub. The Murata PDF is byte-identical to the source already recorded in the `component-murata-grm1885c1h103ja01d` bundle.
