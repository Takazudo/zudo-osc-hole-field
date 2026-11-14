# ST-03 stack mechanics (paper study, attempt a2)

Status: unvalidated paper study. Every fit, force, strain and take-up check on real parts is NOT RUN, because no part, coupon or board exists.

Every number below is recomputed from [`stackups.json`](stackups.json) by `python3 scripts/stack/mechanics/stack_mechanics.py`. The tables sit between `calc:` markers. `--write-readme` refreshes them, and the unit tests fail if they differ. `--refresh-geometry` re-derives the XY block from the ST-02 geometry candidate (`design/stack/geometry/stack-candidate.json`, SHA256 recorded as `S-GEOM`).

Attempt a2 works on the decisions D1 to D6 of the design authority (`reviews/da-01.md`, `S-DA01`). It does not re-decide them. Where a number contradicts a decision, it is marked NEEDS_DESIGN.

Each term carries a status:

- SOURCED: a file or a fetched page with its SHA256.
- DERIVED: a formula.
- ASSUMED: with the reason and what would source it.
- UNSOURCED: no document states it.

Vendor figures are cited by DA-01's section and its vendor-document table; nothing was fetched for a2.

## Heights come from DA-01 D3; the candidate's heights differ and are recorded as notes only

The geometry candidate still carries the cable-era heights. This study uses the DA-01 parameter block (K F.Cu at −30.4 mm; gaps 12.8, 17.0, 18.8 and 7.2 mm). The differences are a note, not an error.

<!-- calc:notes -->
| Height (note, not an error) | Geometry candidate, mm | Used here (DA-01), mm |
| --- | --- | --- |
| K F.Cu z | -30.400 | -30.400 |
| JL/K gap | 18.800 | 18.800 |
| JR/K gap | 18.800 | 18.800 |
| P/K gap | 17.000 | 17.000 |
| O1/K gap | 12.800 | 12.800 |
| EL/P gap | 7.200 | 7.200 |
<!-- /calc:notes -->

## Closing order D2: each step's datums and joint chains

<!-- calc:closing -->
| Step | Action (DA-01 D2) | XY set by | Z set by | Chain at this step |
| --- | --- | --- | --- | --- |
| 1 | Build the P unit: seat EL on P against the backing platen | EL: two close-collar posts on P | EL: P, through the collar posts (7.2 mm) | EL to P: collar-post locator chain plus per-pair terms |
| 2 | Mate the three adapters onto K; tighten their standoff screws | O1, O3, O5: their own two pairs on K (no other constraint yet) | O1, O3, O5: K, through two standoffs each (12.8 mm) | Adapter to K: per-pair terms only (N = 2 per adapter) |
| 3 | Panel face down; fit JL, JR and the P unit; every jack and toggle nut finger-loose | JL, JR: jacks in apertures, free within the clearance; P: pots, toggles, buttons in apertures, free within the clearance | JL, JR: resting on jack shoulders; P: resting, not yet set | None mated |
| 4 | Lower K onto the tapered pilot pins; start every post and tie-post jack screw by hand | K: coarse, by pilot pins (not locators) | K: held on the jack screws | Capture: board rest offset in its clearance + hardware-on-board + aperture position + per-pair terms, against the initial limits |
| 5 | Draw K down in quarter turns until the posts seat; tighten post and tie-post screws | JL, JR, P: each board moves within its aperture clearance to the pairs' lead-in; K floats to the common fit | K: J posts and J tie posts (18.8 mm); P: K, through P posts and tie posts (17.0 mm) | Final: residual board offset beyond its minimum clearance + per-pair terms, against the final limits |
| 6 | Tighten the jack nuts, then the toggle nuts on their compliant take-up, then the selector bushing nuts | all: frozen | JL, JR: jack shoulders on the panel rear; P: unchanged: compliant take-up, P free in Z | Selector row: K against panel + two SMT floats + leg float + hole and aperture positions, against 0.2 mm |
<!-- /calc:closing -->

## Every joint fits its sourced insertion window; body clearance governs the closing side

Gap = pin tip + socket − insertion (DA-01 D3). The open margin is insertion − 2.13 mm. The closing margin is the smaller of 4.32 mm − insertion and the body clearance (gap − socket − "A"). The body clearance is DERIVED from the D3 codes. It is tighter than DA-01's ±0.74 mm window figure on the J and P joints (0.82 to 0.84 mm against 1.27 to 1.45 mm). That refines the D3 margin; it does not contradict it.

<!-- calc:heights -->
| Joint | Gap, mm | Pin tip, mm | Stacker A, mm | Socket, mm | Insertion, mm | Gap may open by, mm | Gap may close by (window), mm | Body clearance, mm | Gap may close by (governing), mm | Height in the geometry candidate, mm (note only) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| JL to K | 18.800 | 17.350 | 13.462 | 4.500 | 3.050 | 0.920 | 1.270 | 0.838 | 0.838 | 18.800 |
| JR to K | 18.800 | 17.350 | 13.462 | 4.500 | 3.050 | 0.920 | 1.270 | 0.838 | 0.838 | 18.800 |
| P unit to K | 17.000 | 15.370 | 11.684 | 4.500 | 2.870 | 0.740 | 1.450 | 0.816 | 0.816 | 17.000 |
| O1/O3/O5 to K | 12.800 | 11.860 | 7.493 | 4.500 | 3.560 | 1.430 | 0.760 | 0.807 | 0.760 | 12.800 |
| EL to P | 7.200 | 7.850 | 4.318 | 2.290 | 2.940 | 1.540 | open (pins pass through) | 0.592 | 0.592 | 7.200 |
<!-- /calc:heights -->

## Capture meets 0.39 mm at the median worst pair but misses at the 95th percentile on JL, JR and P (NEEDS_DESIGN against D5)

Allowed misalignment is tested per axis against the four limits DA-01 cites from the MMS product specification (`V-MMS-SPEC`, sections 5.1.1 and 5.1.2):

- initial: 0.39 mm along the row, 0.57 mm across it;
- final: 0.07 mm along the row, 0.16 mm across it.

Applying them to the TW-SM stacker is ASSUMED (D1). The EL pair has no sourced limit: the CLT figure is UNSOURCED. The MMS double-row figures are shown for reference only.

Terms drawn once per board are separated from terms drawn once per pair. Each term is uniform per axis. The worst pair of N is an exact order statistic on a 0.0005 mm grid: H(x) = Σ p(B)·[F(x − B) − F(−x − B)]^N, with B the board offset and F the per-pair distribution. It is deterministic, and its outputs are rounded.

At capture (step 4) each front board rests anywhere in its aperture clearance. The tapered pilot pins are not modelled as locators (D2), so this errs on the safe side.

In the final state (step 5) each board has moved toward the pairs' common fit. Only the part of its offset beyond the minimum aperture clearance remains.

- **Capture.** At the median, the worst pair is 0.344 to 0.401 mm: JL and JR meet 0.39 mm, P misses by 0.011 mm. At the 95th percentile it is 0.52 to 0.59 mm, which misses 0.39 mm on every K board. DA-01 D2 and D5 state "met on root sum of squares (0.33 to 0.36 mm)". A plain root sum of squares reproduces that, but the worst pair of 27 to 135 does not.
- **Final.** The final limit is missed in every case: at least 0.27 mm at the median worst pair against 0.07 mm along and 0.16 mm across. This agrees with DA-01 M2. Only coupon C-4 closes it.

<!-- calc:xy -->
| Phase | Pairs | N | Worst pair, median, mm per axis | Worst pair, 95th percentile, mm | Worst case, mm | p95 against the sourced limits |
| --- | --- | --- | --- | --- | --- | --- |
| capture | JL to K | 29 | 0.347 | 0.527 | 0.816 | along misses 0.39; across meets 0.57 |
| capture | JR to K | 27 | 0.344 | 0.524 | 0.816 | along misses 0.39; across meets 0.57 |
| capture | P unit to K | 135 | 0.401 | 0.591 | 0.849 | along misses 0.39; across misses 0.57 |
| capture | O1/O3/O5 to K | 6 | 0.165 | 0.245 | 0.304 | along meets 0.39; across meets 0.57 |
| capture | EL to P | 6 | 0.274 | 0.519 | 0.955 | UNSOURCED limit (CLT); MMS double-row reference 0.37 |
| capture | all K pairs | 197 | 0.459 | 0.606 | n/a | along misses 0.39; across misses 0.57 |
| final | JL to K | 29 | 0.268 | 0.355 | 0.541 | along misses 0.07; across misses 0.16 |
| final | JR to K | 27 | 0.266 | 0.353 | 0.541 | along misses 0.07; across misses 0.16 |
| final | P unit to K | 135 | 0.283 | 0.327 | 0.474 | along misses 0.07; across misses 0.16 |
| final | O1/O3/O5 to K | 6 | 0.165 | 0.245 | 0.304 | along misses 0.07; across misses 0.16 |
| final | EL to P | 6 | 0.274 | 0.519 | 0.955 | UNSOURCED limit (CLT); MMS double-row reference 0.07 |
| final | all K pairs | 197 | 0.303 | 0.380 | n/a | along misses 0.07; across misses 0.16 |
<!-- /calc:xy -->

<!-- calc:xy_terms -->
| Pairs | Phase | Drawn once per board (uniform per axis, limits in mm) | Drawn once per pair (uniform per axis, mm) |
| --- | --- | --- | --- |
| JL to K | capture | hardware float on board 0.100; hardware hole registration 0.075; aperture position 0.075; rest offset within the aperture clearance 0.215 | SMT float, socket half 0.100; SMT float, stacker half 0.100; stacker lean at the tip 0.151 |
| JL to K | final | hardware float on board 0.100; hardware hole registration 0.075; aperture position 0.075; less the minimum clearance 0.060 | SMT float, socket half 0.100; SMT float, stacker half 0.100; stacker lean at the tip 0.151 |
| JR to K | capture | hardware float on board 0.100; hardware hole registration 0.075; aperture position 0.075; rest offset within the aperture clearance 0.215 | SMT float, socket half 0.100; SMT float, stacker half 0.100; stacker lean at the tip 0.151 |
| JR to K | final | hardware float on board 0.100; hardware hole registration 0.075; aperture position 0.075; less the minimum clearance 0.060 | SMT float, socket half 0.100; SMT float, stacker half 0.100; stacker lean at the tip 0.151 |
| P unit to K | capture | hardware float on board 0.100; hardware hole registration 0.075; aperture position 0.075; rest offset within the aperture clearance 0.265 | SMT float, socket half 0.100; SMT float, stacker half 0.100; stacker lean at the tip 0.134 |
| P unit to K | final | hardware float on board 0.100; hardware hole registration 0.075; aperture position 0.075; less the minimum clearance 0.110 | SMT float, socket half 0.100; SMT float, stacker half 0.100; stacker lean at the tip 0.134 |
| O1/O3/O5 to K | capture | none (the adapter floats onto K) | SMT float, socket half 0.100; SMT float, stacker half 0.100; stacker lean at the tip 0.104 |
| O1/O3/O5 to K | final | none (the adapter floats onto K) | SMT float, socket half 0.100; SMT float, stacker half 0.100; stacker lean at the tip 0.104 |
| EL to P | capture | EL hole registration 0.075; P hole registration 0.075; collar float 0.118; rotation: slot float x ratio 0.118; rotation: hole pair spacing, both boards 0.300 | SMT float, socket half 0.100; SMT float, stacker half 0.100; stacker lean at the tip 0.069 |
| EL to P | final | EL hole registration 0.075; P hole registration 0.075; collar float 0.118; rotation: slot float x ratio 0.118; rotation: hole pair spacing, both boards 0.300 | SMT float, socket half 0.100; SMT float, stacker half 0.100; stacker lean at the tip 0.069 |
<!-- /calc:xy_terms -->

The stacker lean is ASSUMED at 0.5°. At the sourced 2° maximum sway of the stacker print, the P unit's worst pair doubles:

<!-- calc:lean -->
| Lean, degrees | P unit final worst pair, median, mm | 95th percentile, mm |
| --- | --- | --- |
| 0.5 | 0.283 | 0.327 |
| 2 | 0.653 | 0.711 |
<!-- /calc:lean -->

The adopted scheme has no K-to-P pin chain, so no row above carries it (M4). The adapters ride on K (D4), so the 0.6 mm selector aperture clearance is not a term of the adapter pairs; it reappears only in the selector row below. Each board is charged its full offset from nominal, although a floating K removes the part common to all boards. That errs on the safe side.

## The selector row is 0.267 mm on root sum of squares against the 0.2 mm budget (NEEDS_DESIGN, as D4 states)

<!-- calc:selector -->
| Selector-row term (adapters on K, D4) | mm, radial |
| --- | --- |
| K against the panel | 0.100 |
| SMT float, socket half | 0.100 |
| SMT float, stacker half | 0.100 |
| selector leg float | 0.100 |
| selector hole position on the adapter | 0.106 |
| routed aperture position | 0.141 |
| Worst case | 0.647 |
| Root sum of squares | 0.267 |
| Budget (S-SEL, kept by DA-01 D4) | 0.200 |
| Over the budget (RSS) | 0.067 |
<!-- /calc:selector -->

ST-12 must show 0.2 mm with measured terms, or the three selector apertures grow from 7.0 to 7.3 mm (owner item 2).

## Apertures fail on hardware-on-board terms in any order; the remedy is the soldering fixture

The baseline row sets every locating term to zero. It keeps only lead float, hole position and aperture position. It fails every class, which reproduces DA-01 M3: jack by 0.120 mm, pot by 0.070, toggle by 0.033, button by 0.027 and selector by 0.003 mm. The hardware must be soldered with the panel, or a plate drilled like it, as the fixture. That this fixture exists is ASSUMED (owner item 5). The order is decided on other grounds (D2).

<!-- calc:apertures -->
| Class | Hole, mm | Min radial clearance, mm | Max radial clearance, mm | Baseline WC, mm (hardware-on-board only) | Baseline RSS, mm | Baseline RSS verdict |
| --- | --- | --- | --- | --- | --- | --- |
| jack | 6.2 | 0.060 | 0.215 | 0.312 | 0.180 | fails by 0.120 |
| pot | 6.3 | 0.110 | 0.265 | 0.312 | 0.180 | fails by 0.070 |
| toggle | 5.2 | 0.147 | 0.315 | 0.312 | 0.180 | fails by 0.033 |
| sub_toggle | 5.2 | 0.147 | 0.315 | 0.312 | 0.180 | fails by 0.033 |
| button | 5.0 | 0.185 | 0.340 | 0.362 | 0.212 | fails by 0.027 |
| selector | 7.0 | 0.200 | 0.600 | 0.347 | 0.203 | fails by 0.003 |
<!-- /calc:apertures -->

EL passages, for reference. D4 enlarges the pot passages to 6.8 mm, and ST-02 checks them:

<!-- calc:el_passages -->
| EL passage | Hole, mm (a1 values) | Min radial clearance, mm | WC, mm | RSS, mm | RSS verdict |
| --- | --- | --- | --- | --- | --- |
| el_passage_pot | 6.3 | 0.110 | 0.998 | 0.402 | fails by 0.292 |
| el_passage_switch | 11.0 | 0.666 | 0.998 | 0.402 | closes |
| el_passage_button | 9.5 | 0.326 | 0.998 | 0.402 | fails by 0.076 |
<!-- /calc:el_passages -->

## Z closes on JL, JR, the adapters and EL; P still misses with the five provisional sites (NEEDS_DESIGN to ST-08)

Z is tested against the sourced MMS window: the open and closing margins from the heights table, with `t` = 0.2 mm ASSUMED. The bow uses the screen model (0.75 %, deviation 4·b·d²/L from the nearest fixing). JL and JR take the panel's plane through the jack shoulders (M7). Their own term is then panel bow plus an ASSUMED 0.2 mm local shoulder term. The fixings are the 18 posts and the 12 kept supports, then the same with the five D4 sites added. The five sites are PROVISIONAL: ST-08 fixes them.

<!-- calc:z_gap -->
| Joint | Fixings | Worst pair WC: id, mm | Worst pair RSS: id, mm | Need WC (+ t), mm | Need RSS (+ t), mm | Margin open, mm | Margin close, mm | Verdict |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| JL to K | 18 posts + 12 kept supports | JL-K-9 3.455 | JL-K-9 2.179 | 3.655 | 2.379 | 0.920 | 0.838 | RSS: open misses, close misses; WC: misses |
| JL to K | + 5 provisional sites | JL-K-9 1.224 | JL-K-9 0.630 | 1.424 | 0.830 | 0.920 | 0.838 | RSS: open meets, close meets; WC: misses |
| JR to K | 18 posts + 12 kept supports | JR-K-1 3.120 | JR-K-1 1.943 | 3.320 | 2.143 | 0.920 | 0.838 | RSS: open misses, close misses; WC: misses |
| JR to K | + 5 provisional sites | JR-K-15 0.666 | JR-K-15 0.294 | 0.866 | 0.494 | 0.920 | 0.838 | RSS: open meets, close meets; WC: misses |
| P unit to K | 18 posts + 12 kept supports | K-P-120 2.440 | K-P-120 1.594 | 2.640 | 1.794 | 0.740 | 0.816 | RSS: open misses, close misses; WC: misses |
| P unit to K | + 5 provisional sites | K-P-42 1.763 | K-P-42 1.116 | 1.963 | 1.316 | 0.740 | 0.816 | RSS: open misses, close misses; WC: misses |
| O1/O3/O5 to K | adapter standoffs (not placed) | K-O1-1 0.983 | K-O1-1 0.743 | 1.183 | 0.943 | 1.430 | 0.760 | RSS: open meets, close misses; WC: misses |
| EL to P | EL collar posts | EL-P-E1 0.216 | EL-P-E1 0.093 | 0.416 | 0.293 | 1.540 | 0.592 | RSS: open meets, close meets; WC: meets both |
<!-- /calc:z_gap -->

## The 40 mm rule is not met from the retained fixings: 107 pairs miss it, and 67 with the five provisional sites (NEEDS_DESIGN to ST-08)

D4 says 27 pairs miss it (JL 3, JR 7, P 17) and that the five sites cover them. That count used the 66 interior candidate sites, whose coordinates are not retained in this repository. From the retained fixings (18 posts, 12 kept supports, five provisional sites), JL keeps 9 and P keeps 58 pairs beyond 40 mm. The distance is taken to the nearest fixing on the same front board. ST-08 must place the fixings that close the rule. This calculator re-tests any set written into `stackups.json` `fixings`.

<!-- calc:coverage -->
| Fixings | Board | Pairs beyond 40 mm | References |
| --- | --- | --- | --- |
| 18 posts + 12 kept supports | JL | 14 | JL-K-12, JL-K-13, JL-K-14, JL-K-15, JL-K-16, JL-K-17, JL-K-18, JL-K-3, JL-K-4, JL-K-5, JL-K-6, JL-K-7, JL-K-8, JL-K-9 |
| 18 posts + 12 kept supports | JR | 10 | JR-K-1, JR-K-10, JR-K-11, JR-K-12, JR-K-2, JR-K-3, JR-K-4, JR-K-5, JR-K-8, JR-K-9 |
| 18 posts + 12 kept supports | P | 83 | K-P-1, K-P-100, K-P-101, K-P-102, K-P-103, K-P-104, K-P-105, K-P-106, K-P-107, K-P-108, K-P-109, K-P-11, K-P-110, K-P-111, K-P-112, K-P-113, K-P-114, K-P-115, K-P-116, K-P-117, K-P-118, K-P-119, K-P-120, K-P-121, K-P-122, K-P-123, K-P-14, K-P-15, K-P-17, K-P-2, K-P-21, K-P-22, K-P-23, K-P-25, K-P-26, K-P-27, K-P-28, K-P-29, K-P-30, K-P-32, K-P-36, K-P-40, K-P-41, K-P-42, K-P-43, K-P-46, K-P-47, K-P-48, K-P-52, K-P-53, K-P-55, K-P-58, K-P-59, K-P-60, K-P-64, K-P-65, K-P-66, K-P-67, K-P-68, K-P-70, K-P-71, K-P-72, K-P-73, K-P-74, K-P-76, K-P-77, K-P-8, K-P-80, K-P-9, K-P-91, K-P-95, K-P-96, K-P-97, K-P-98, K-P-99, P-K-E4, P-K-E5, P-K-E6, P-K-SUB-O2, P-K-SUB-O4, P-K-X2, P-K-X3, P-K-X4 |
| with the 5 provisional sites | JL | 9 | JL-K-12, JL-K-18, JL-K-3, JL-K-4, JL-K-5, JL-K-6, JL-K-7, JL-K-8, JL-K-9 |
| with the 5 provisional sites | JR | 0 | none |
| with the 5 provisional sites | P | 58 | K-P-1, K-P-100, K-P-101, K-P-102, K-P-103, K-P-104, K-P-105, K-P-106, K-P-107, K-P-108, K-P-109, K-P-11, K-P-110, K-P-111, K-P-112, K-P-113, K-P-114, K-P-115, K-P-116, K-P-120, K-P-121, K-P-122, K-P-123, K-P-26, K-P-28, K-P-32, K-P-36, K-P-40, K-P-41, K-P-42, K-P-43, K-P-46, K-P-47, K-P-48, K-P-52, K-P-53, K-P-67, K-P-68, K-P-70, K-P-71, K-P-72, K-P-73, K-P-74, K-P-76, K-P-91, K-P-95, K-P-96, K-P-97, K-P-98, K-P-99, P-K-E4, P-K-E5, P-K-E6, P-K-SUB-O2, P-K-SUB-O4, P-K-X2, P-K-X3, P-K-X4 |
<!-- /calc:coverage -->

<!-- calc:coverage_worst -->
| Board | Farthest pair, front-board / K fixing, mm (base) | Same with the 5 provisional sites, mm |
| --- | --- | --- |
| JL | 126.649 / 126.649 | 66.068 / 66.068 |
| JR | 119.509 / 119.509 | 38.000 / 38.000 |
| P | 108.334 / 108.334 | 90.588 / 90.588 |
<!-- /calc:coverage_worst -->

## K dishes by about 1.3 to 3.5 mm under the mating load in its largest unfixed bay, so tie posts are needed for the closing force too

Model (ASSUMED): a circular plate of K's thickness, with the bay radius equal to the farthest pair's distance to a fixing, under the bay's positions at f spread uniformly. w = qR⁴/(64D) for a clamped edge, ×(5 + ν)/(1 + ν) for a simply supported edge. E = 20 GPa and ν = 0.15 are ASSUMED. Coupon C-9 measures an 80 × 80 mm bay.

<!-- calc:dish -->
| Fixings | Bay centre (pair) | Bay radius, mm | Positions in the bay | f, N | Force, N | Dish, clamped edge, mm | Dish, simply supported edge, mm |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 18 posts + 12 kept supports | JL-K-9 | 126.649 | 228 | 0.84 | 192 | 2.188 | 9.797 |
| 18 posts + 12 kept supports | JL-K-9 | 126.649 | 228 | 0.97 | 221 | 2.526 | 11.314 |
| 18 posts + 12 kept supports | JL-K-9 | 126.649 | 228 | 1.33 | 303 | 3.464 | 15.512 |
| with the 5 provisional sites | K-P-42 | 90.588 | 263 | 0.84 | 221 | 1.291 | 5.782 |
| with the 5 provisional sites | K-P-42 | 90.588 | 263 | 0.97 | 255 | 1.491 | 6.677 |
| with the 5 provisional sites | K-P-42 | 90.588 | 263 | 1.33 | 350 | 2.044 | 9.155 |
<!-- /calc:dish -->

## K's 0.028 to 0.045 mm plane-mismatch allowance is a lower bound; P stays free in Z (D4)

The fixed-guided beam treats P and J as rigid, so the allowance is a lower bound (M8). The a1 statement about a 0.05 mm shim is withdrawn. In the case where the toggle front nuts pull P, the root-sum-of-squares delta is the toggle gap plus the P mismatch (1.16 + 0.373 = 1.533 mm). This is the code-review fix F1.

<!-- calc:strain_allow -->
| Span s, mm | Lower bound of the allowed Delta at 593 microstrain, mm | Lower bound at the test level 1185 microstrain, mm |
| --- | --- | --- |
| 15.000 | 0.028 | 0.056 |
| 19.000 | 0.045 | 0.089 |
| 68.000 | 0.571 | 1.142 |
<!-- /calc:strain_allow -->

<!-- calc:strain -->
| Case (upper bound: K alone bends) | Span s, mm | Delta WC, mm | Delta RSS, mm | Strain WC, microstrain | Strain RSS, microstrain | Verdict (WC) |
| --- | --- | --- | --- | --- | --- | --- |
| P pulled by toggle front nuts only (nominal gap closed) | 15.000 | 2.060 | 1.533 | 43947 | 32712 | exceeds test level |
| P clamped to the panel at a fixed stop and bolted to K | 15.000 | 0.900 | 0.373 | 19200 | 7965 | exceeds test level |
| P pulled by toggle front nuts only (nominal gap closed) | 19.000 | 2.060 | 1.533 | 27391 | 20388 | exceeds test level |
| P clamped to the panel at a fixed stop and bolted to K | 19.000 | 0.900 | 0.373 | 11967 | 4964 | exceeds test level |
| JL and JR planes both from jack shoulders, K bolted to both | 68.000 | 1.009 | 0.399 | 1047 | 415 | within test level only |
| K pulled flat from 0.75% bow at fixings | n/a | n/a | n/a | 155 | 155 | within design limit |
<!-- /calc:strain -->

## The toggle gap reaches 0.26 mm on worst case, 0.04 mm below the D4 washer window (NEEDS_DESIGN to ST-12)

D4 states the washer stack works over 0.3 to 2.1 mm and also that the gap is 1.16 mm ±0.9 mm worst case. 1.16 − 0.9 = 0.26 mm, so the window must reach 0.26 mm or the worst case must shrink.

<!-- calc:toggle -->
| Quantity | mm | Status |
| --- | --- | --- |
| Nominal gap, toggle body front to panel rear | 1.160 | DERIVED |
| Gap range, worst case (P follows K) | 0.260 to 2.060 | DERIVED |
| D4 washer working range | 0.3 to 2.1 | SOURCED (DA-01 D4) |
| Range inside the D4 window | no | DERIVED |
| Rear jam nut thickness against the nominal gap | 1.190 vs 1.160 | SOURCED / DERIVED |
<!-- /calc:toggle -->

## K needs 653 to 1,033 N to mate its 777 positions and 365 to 761 N to separate

Sourced from the double-row qualification report via DA-01 M9 (`V-QUAL-154341`): 0.84, 0.97 and 1.33 N per position mating, 0.47 to 0.98 N unmating. Applying them to the single-row pair is ASSUMED. Per-board totals count each joint's own positions. "K, all joints" counts K's 777 positions. "All joints per side" counts the 825 of D6, including EL's 48. The draw-down load per fixing divides each board's mating force by its fixings (posts plus kept supports, then with the provisional sites).

<!-- calc:forces -->
| Joint | Positions | Mating at 0.84 N, N | Mating at 0.97 N, N | Mating at 1.33 N, N | Unmating at 0.47 to 0.98 N, N | Draw-down load per fixing at each f, N (posts + kept supports) | At 1.33 N with the 5 provisional sites, N |
| --- | --- | --- | --- | --- | --- | --- | --- |
| JL to K | 162 | 136 | 157 | 215 | 76 to 159 | 14 / 16 / 22 over 10 | 20 over 11 |
| JR to K | 162 | 136 | 157 | 215 | 76 to 159 | 14 / 16 / 22 over 10 | 18 over 12 |
| P unit to K | 423 | 355 | 410 | 563 | 199 to 415 | 36 / 41 / 56 over 10 | 47 over 12 |
| O1/O3/O5 to K | 30 | 25 | 29 | 40 | 14 to 29 | 4 / 5 / 7 over 6 | 7 over 6 |
| EL to P | 48 | 40 | 47 | 64 | 23 to 47 | n/a (platen) | n/a |
| K, all joints (count: K positions) | 777 | 653 | 754 | 1033 | 365 to 761 |  |  |
| All joints per side incl. EL (count: DA-01 D6) | 825 | 693 | 800 | 1097 | 388 to 808 |  |  |
<!-- /calc:forces -->

## EL cannot be seated or removed without a full-face backing platen (accepted in DA-01)

Each of the six sites carries 8 positions (2 × 4 CLT).

<!-- calc:el_plate -->
| EL thickness, mm | f, N | Force per site, N | Mid-span deflection, mm | Mid-span strain, microstrain | Outer-site deflection, mm | Outer-site strain, microstrain | Unbacked EL |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0.400 | 0.84 | 6.7 | 0.379 | 3150 | 0.759 | 6300 | exceeds design limit |
| 0.400 | 0.97 | 7.8 | 0.438 | 3637 | 0.876 | 7275 | exceeds design limit |
| 0.400 | 1.33 | 10.6 | 0.601 | 4987 | 1.201 | 9975 | exceeds design limit |
| 0.300 | 0.84 | 6.7 | 0.899 | 5600 | 1.798 | 11200 | exceeds design limit |
| 0.300 | 0.97 | 7.8 | 1.038 | 6467 | 2.077 | 12933 | exceeds design limit |
| 0.300 | 1.33 | 10.6 | 1.424 | 8867 | 2.847 | 17733 | exceeds design limit |
<!-- /calc:el_plate -->

## Supports: 12 become tie posts, 9 go, P-SUP-6 becomes a compliant guide and 65 stay in role

<!-- calc:supports -->
| Items | Count | Disposition | Reason |
| --- | --- | --- | --- |
| JL-SUP-1..3, JR-SUP-1..3 | 6 | STAY at the same XY, change role: J-to-K tie posts (18.8 mm, DA-01 D3), no enclosure joint | Removes the second load loop through the side carrier; adds edge support to K's flatness along x = 6.5 and 311.5, where no power post exists |
| JL-SUP-4, JR-SUP-4 | 2 | GO, merged with K-SUP-3/4 | (6.5, 161.5) and (311.5, 161.5) lie 1.5 mm from K-SUP-3/4 at y = 160; one J-to-K tie post at (6.5, 160) and (311.5, 160) serves both, inside JL and JR (outline y <= 164) |
| K-SUP-3, K-SUP-4 | 2 | STAY at the same XY, change role: the merged J-to-K tie posts | As above |
| K-SUP-5..8 | 4 | STAY at the same XY, change role: P-to-K tie posts (17.0 mm, DA-01 D3), no frame joint | All four lie inside P's outline; fastening K to the frame as well as to the front boards closes a second load loop through the panel and enclosure |
| K-SUP-1, K-SUP-2 | 2 | GO as clamped supports; optional Z-compliant bumper to the rear cover | At y = 10.5 no front board lies in front of them (J starts at y = 20), so a clamp there can only reach the frame |
| P-SUP-1..5 | 5 | GO; replaced by P-to-K tie posts at interior candidates | Their 3.2 mm collars overlap K's outline edge by 1.1 mm at x = 3.5 and 314.5; moving them inward by >= 1.6 mm would clear K but still tie P to the frame |
| P-SUP-6 | 1 | STAY only as a Z-compliant guide (no axial clamp) | (314.5, 289.5) lies in K's notch (x > 258, y > 246) where no K post can reach; a clamp would fix P's plane against K's |
| P-OPT-* (30 clearance holes) | 30 | STAY | Clearance in P for the EL posts |
| EL-OPT-1..35 | 35 | STAY, change role: EL-to-P collar posts that set the 7.2 mm gap and back EL during mating; two become locators with precision collars | EL takes plane and position from P; the five at y = 172 pass through the P tab (plan page) |
| Seam rear cradle [172, 20, 182, 164], z -13.6..-11.6 | 1 | GO | Lies inside the J-to-K gap; K now holds both J boards through tie posts, so the seam needs no separate carrier. J-to-K tie posts within the seam reserves (x 172..182) replace it |
| Seam front lips [175.2, 20, 178.8, 164] | 2 | GO with the cradle | Attached to the cradle |
| Cross-members y 17..19 and y 165..167, x -2..320 | 2 | GO | Same z range as the J-to-K gap and P's plane; they reach the enclosure frame and would close the second load loop; the y 165..167 member sits 1.5 mm from the EL tab |
| Interior fastener candidates (planning screen): JL 37, P 26, JR 3 | 66 | USE as front-board-to-K tie posts where ST-08 needs them to put every pair within 40 mm of a fixing (DA-01 D4) | Posts and kept supports alone leave pairs up to 127 mm from the nearest fixing (coverage table). The 66 site coordinates are not retained, so this calculator cannot test them; DA-01 D4 adds five PROVISIONAL sites and ST-08 fixes the set |
| Total of the 87 partition supports | 87 |  |  |
<!-- /calc:supports -->

## The coupon is a requirements frame with DA-01's seven changes and the A-physical pass numbers

This is a definition of what a coupon must measure. It is not a specification, an order or a quote request. ST-09 writes the retained specification and outlines.

<!-- calc:coupon -->
| Board | Role | Outline | Thickness, mm | Contents |
| --- | --- | --- | --- | --- |
| CK | K-side board | set by ST-09 | 1.6 | TW-SM single-row stackers for the three gaps 12.8, 17.0 and 18.8 mm (lead styles -03, -06, -07), each gap at two stacker heights: 'A' by the D3 rule and 'A' = 4.32 mm (D5 change 2); at least 20 pairs per board per variant (change 4); posts of the ST-04 class setting each gap (change 1); one tie-post bay of 80 x 80 mm with pairs at its centre, closed by jack screws (change 6); strain-gauge pads at 0603 MLCC sites near the posts; daisy-chain copper through every contact; fiducials |
| CF | front-board board | set by ST-09 | 1.6 | MMS -02 -SV single-row sockets matching CK (change 1), carrying their polyimide pads through the through-hole soldering of jacks and pots on the same face (change 7); variants CF-along-X and CF-across-X impose an offset X = 0, 0.1, 0.2, 0.3 and 0.4 mm along the row and, separately, across it (change 3) |
| CE | 0.4 mm EL-class board with a P-tab partner | set by ST-09 | 0.4 | CLT 2x4 sockets with double-row TW-SM stackers at 7.2 mm, with the eight relief holes per site (change 5); seated and removed with and without the backing platen |

| Measurement | What it measures | Pass number (DA-01 D5) |
| --- | --- | --- |
| C-1 | Mating and unmating force per position, single-row pair, force-displacement over 10 cycles | Mating at most 1.35 N per position; unmating within the jack-screw plan of ST-08 (A-physical condition 2) |
| C-2 | Surface-mount float of each half after reflow | At most 0.1 mm per half (condition 3) |
| C-3 | Pin tip position and lean after reflow, at both stacker heights | Tip within 0.2 mm of nominal (condition 3) |
| C-4 | Alignment tolerance of the real pair under imposed offsets along and across the row | At 0.25 mm along and, separately, across: every pair mates on the first pass, every chain continuous, no contact damaged after 10 cycles, at each of the three gaps (condition 1). If it passes only at 0.1 mm or less, the K joints of JL, JR and P are not adopted |
| C-5 | Usable engagement: continuity while the post gap is shimmed around nominal | Every chain continuous over +/-0.6 mm around the nominal gap (condition 4) |
| C-6 | K strain at MLCC sites under imposed post-row mismatch | Replaces the beam model; the 593 microstrain design limit stands until then (D4) |
| C-7 | Sockets after through-hole soldering with pads on: flux or solder in the contacts | No contamination (no number set by DA-01) |
| C-8 | EL seating on CE with and without the platen: deflection, strain, insertion | No number set by DA-01 |
| C-9 | Dish of the 80 x 80 mm bay under the mating force, closed by jack screws | No number set by DA-01; compared with the plate estimate in this README |
<!-- /calc:coupon -->

## Seven figures stay open

<!-- calc:open -->
| Figure | Exact need |
| --- | --- |
| Final misalignment the real pair tolerates | Coupon C-4 at 0.25 mm imposed offset along and across the row at each gap (A-physical condition 1); the paper budget cannot close it |
| t | Pin-length and tip-height tolerance of the TW-SM stacker per lead style (ASSUMED 0.2 mm); coupon C-5 or a manufacturer statement |
| SMT float and lean | Measured float per half and pin tip position after reflow (coupon C-2, C-3; A-physical condition 3) |
| Single-row force | Mating and unmating force of the single-row MMS with TW-SM (coupon C-1); the sourced figures are for the double-row MMS with TMM |
| CLT misalignment and pass-through | CLT product specification and print: allowed misalignment of the double-row CLT and whether pins may pass through (ST-01b) |
| Socket land pattern | MMS -02 -SV recommended land pattern (ST-01b) |
| Placement | Whether the assembler places pad-less 1x3 stackers and lead style -07 from tubes (owner item 3) |
<!-- /calc:open -->

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
| `murata_flexure` | 1 |  | mm | SOURCED | S-MURATA-GRM18: item 11 Substrate Bending test, Flexure 1mm |
| `murata_span` | 90 |  | mm | SOURCED | S-MURATA-GRM18: Fig.2, supports 45 mm + 45 mm |
| `murata_board` | 1.6 |  | mm | SOURCED | S-MURATA-GRM18: Substrate Bending test substrate thickness 1.6mm |
| `strain_test_level` | 0.0011852 |  | 1 | DERIVED | 6 t delta / L^2 (three-point bend surface strain at mid-span) = 6 x 1.6 x 1.0 / 90^2 |
| `strain_safety_factor` | 2 |  | 1 | ASSUMED | to source: Design authority choice; bending specification of every ceramic part family fitted near the post rows |
| `strain_design_limit` | 0.0005926 |  | 1 | DERIVED | strain_test_level / strain_safety_factor |
| `k_strain_model` | fixed-guided beam: eps = 3 t Delta / s^2 |  | 1 | ASSUMED | to source: Plate FE model in ST-12 or strain-gauge coupon C-6 |
| `smt_float_front` | 0.1 |  | mm | ASSUMED | to source: ST-01 footprint guidance; coupon C-2 measurement |
| `smt_float_k` | 0.1 |  | mm | ASSUMED | to source: ST-01; coupon C-2 |
| `pin_lean_deg` | 0.5 |  | deg | ASSUMED | to source: ST-01 true-position or tip-coplanarity specification; coupon C-3 lean measurement |
| `hole_position_tol_axis` | 0.075 |  | mm | SOURCED | S-JLC-PCB: 'Hole Position Tolerance +/-0.075 mm' |
| `hole_position_radial` | 0.1061 |  | mm | DERIVED | sqrt(2) x hole_position_tol_axis |
| `pth_hole_tol_plus` | 0.13 |  | mm | SOURCED | S-JLC-PCB: 'Through-holes: +0.13 / -0.08 mm'; also 'Slot Hole size Tolerance Plated: +0.13 / -0.08 mm' |
| `pth_hole_tol_minus` | 0.08 |  | mm | SOURCED | S-JLC-PCB: as pth_hole_tol_plus |
| `routed_hole_position_tol_axis` | 0.1 |  | mm | SOURCED | S-JLC-PCB: '+/-0.1mm(Precision) and +/-0.2mm(Regular) for CNC routing' |
| `routed_hole_position_radial` | 0.1414 |  | mm | DERIVED | sqrt(2) x routed_hole_position_tol_axis |
| `loc_pin_diameter` | 2 | +0.0/-0.006 | mm | ASSUMED | to source: Purchased pin drawing (ST-12) |
| `loc_hole_clearance_standard` | 0.1 |  | mm | ASSUMED | to source: ST-12 collar drawing |
| `loc_slot_clearance` | 0.1 |  | mm | ASSUMED | to source: Design authority |
| `r_loc_standard` | 0.118 |  | mm | DERIVED | (loc_hole_clearance_standard + pth_hole_tol_plus + loc_pin_diameter.minus) / 2 |
| `r_slot` | 0.118 |  | mm | DERIVED | (loc_slot_clearance + pth_hole_tol_plus + loc_pin_diameter.minus) / 2 |
| `th_lead_float` | 0.1 |  | mm | ASSUMED | to source: Lead dimensions from the drawings versus finished drill sizes; first-article axis measurement |
| `smd_led_float` | 0.1 |  | mm | ASSUMED | to source: Assembly provider placement data; #64 optical coupon |
| `button_guide_float` | 0.15 |  | mm | ASSUMED | to source: Carrier and plunger drawing (ST-12) |
| `selector_leg_float` | 0.1 |  | mm | ASSUMED | to source: #55 coupon |
| `fr4_modulus` | 20000 |  | N/mm^2 | ASSUMED | to source: Laminate datasheet of the fabricator's FR4 for the 0.4 mm EL |
| `screw_axial_capacity` | 1000 |  | N | ASSUMED | to source: ST-04 post and screw drawings with thread engagement |
| `m25_pitch` | 0.45 |  | mm | DERIVED | ISO metric coarse pitch implied by the M2.5 designation |
| `el_locator_ratio` | 1 |  | 1 | ASSUMED | to source: ST-12 choice of the two collar posts |
| `poisson_fr4` | 0.15 |  | 1 | ASSUMED | to source: Laminate datasheet |
| `jack_shoulder_local` | 0.2 |  | mm | ASSUMED | to source: #65 seated-height measurement |
| `da01.K_face_z_mm` | -30.4 |  |  | SOURCED | S-DA01: D1 item 2; D3 'K F.Cu z = -17.6 - 12.8 = -30.4 mm' |
| `da01.gap_mm` | {"O": 12.8, "P": 17.0, "JL": 18.8, "JR": 18.8, "EL": 7.2} |  |  | SOURCED | S-DA01: D3 joint table; EL 'The gap stays 7.2 mm' |
| `da01.stacker_tip_mm` | {"O": 11.86, "P": 15.37, "JL": 17.35, "JR": 17.35, "EL": 7.85} |  |  | SOURCED | V-TWSM-PRINT: table 1 maximum 'A' per lead style -03, -06, -07; EL -02 (DA-01 D3) |
| `da01.stacker_A_in` | {"O": 0.295, "P": 0.46, "JL": 0.53, "JR": 0.53, "EL": 0.17} |  |  | DERIVED | O, P, JL, JR: the D3 rule 'A <= gap - 4.50 - 0.80 mm, rounded down to 0.005 in', which gives the working codes TW-xx-03-L-S-295-SM, -06-L-S-460-SM and -07-L-S-530-SM. EL: read from the D3 code TW-04-02-L-D-170-SM-P-TR; it is not set by the 0.80 mm rule (body clearance 0.59 mm against the 2.29 mm CLT socket, shown in the heights table) |
| `da01.socket_height_mm` | {"single": 4.5, "EL": 2.29} |  |  | SOURCED | V-MMS-PRINT: MMS seated height 4.496 +0.102/-0.051 (sheet 1); CLT 2.29 mm from V-CLT-PAGE |
| `da01.insertion_window_mm` | {"single": [2.13, 4.32], "EL_min": 1.4} |  |  | SOURCED | S-DA01: D3 evidence table (retained MMS catalogue page); EL: CLT top-entry insertion 1.40 mm minimum, pins pass through EL relief holes |
| `da01.body_clearance_rule_mm` | 0.8 |  |  | SOURCED | S-DA01: D3 rule for the stacker height |
| `da01.t_mm` | 0.2 |  |  | ASSUMED | to source: Coupon C-5; a manufacturer statement if the owner asks (owner item 4) |
| `da01.misalignment_mm` | {"initial": {"along": 0.39, "across_single": 0.57, "across_double_MMS": 0.37}, "final": {"along": 0.07, "across_single": 0.16, "across_double_MMS": 0.07}} |  |  | SOURCED | V-MMS-SPEC: page 4, section 5.1.1 (X-axis figure, table 1) and 5.1.2 (X-axis figure, table 5); applying them to the TW-SM stacker is ASSUMED (DA-01 D1) |
| `da01.el_misalignment` | null |  |  | UNSOURCED | to source: CLT product specification (ST-01b) |
| `da01.mating_force_N` | [0.84, 0.97, 1.33] |  |  | SOURCED | V-QUAL-154341: printed pages 15-16 via DA-01 M9: 0.84 N (largest connector, new), 0.97 N (new, highest sample), 1.33 N (after 100 cycles); applying the double-row report to the single-row pair is ASSUMED |
| `da01.unmating_force_N` | [0.47, 0.98] |  |  | SOURCED | V-QUAL-154341: DA-01 M9 |
| `da01.el_positions_per_pair` | 8 |  |  | SOURCED | S-DA01: D3: six 2x4 pairs, 48 positions |
| `da01.positions_per_side_total` | 825 |  |  | SOURCED | S-DA01: D6 plan-page figures: 825 positions per side in total |
| `da01.fixing_distance_rule_mm` | 40.0 |  |  | SOURCED | S-DA01: D4 'Every pair lies within 40 mm of a post or tie post' |
| `da01.pin_sway_max_deg` | 2.0 |  |  | SOURCED | V-TWSM-PRINT: note 1: 2 degrees maximum either direction |
| `da01.toggle_takeup_window_mm` | [0.3, 2.1] |  |  | SOURCED | S-DA01: D4 Z take-up row: washer stack works over 0.3 to 2.1 mm |
| `da01.k_vs_panel_selector_mm` | 0.1 |  |  | ASSUMED | to source: ST-12 with measured terms |
| `da01.selector_budget_mm` | 0.2 |  |  | SOURCED | S-SEL: shaft_clearance_budget: (6.9 - 6.1)/2 - 0.2 wobble; kept as the budget by DA-01 D4 |
<!-- /calc:terms -->

## Checks: unit tests and the calculator run; every physical check NOT RUN

- Run: `python3 -m unittest scripts/stack/mechanics/test_stack_mechanics.py`, the calculator twice with a clean tree, `pnpm circuit:check`, and `frozen_studies.py discover`.
- NOT RUN: fit, force, strain, dish and take-up on real parts. No coupon or board exists, and building one would be a fabrication action outside this task.
