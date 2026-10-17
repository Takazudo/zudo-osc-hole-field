## Current A01 whole-arch retention and wire/current evidence — Stage34

[Stage34](stage34/README.md) adds RG34 to the owner's provisional R33 study baseline. RG34 is one slot
channel per arch on the rear carrier, with walls, a cap, a former whose height is set at assembly, and
removable leg sleeves. Stage34 also builds the A01 conductor current budget from recorded terms and the
wire ledger.
- **R33 + RG34 (CONDITIONAL_PENDING_COVER_REGISTRATION_AND_MEASUREMENT):**
  - RG34 bounds the whole arch geometrically at every tolerance corner (cut, bow, registration), without
    using cable stiffness. It keeps every single-end 15 mm withdrawal at constant length.
  - The J-PWR channel wall faces the core (0.29 mm robust spare, registration out of the chain).
  - **The J-SIG cap does not fit under the rear cover** (needs z 106.21; the cover is at 105). A deeper
    cover or a 2.4 mm shorter J-SIG is an owner decision.
  - Inter-carrier registration (≤ 1.0 mm required) is UNKNOWN.
  - Front jack board removal must remove RG34 first, and RG34 sits outside the reserved volumes (both
    proposals).
- **Negative controls:** a local-leg guide alone, RG34 without its former, a fixed (not set) former, and
  a both-ends withdrawal with the lid closed all fail as expected.
- **Currents:** the Stage33 J-PWR inputs were Stage8 X1 values and are superseded; the Stage33 bytes
  are unchanged. The A01 budget gives conditional maxima only, and no conductor has an established
  maximum.
- **Wire:** the selection stays null.
  - Thermax M22759/18-26 fails nothing: its current checks are CONDITIONAL and there is no maker bend
    radius.
  - Alpha 6710 / 1851 (AWG28/30) lack a JST contact rating; that is UNKNOWN, not a failure.
- **NOT RUN:** M34-01…08, M-01, M-09, M-12, KiCad, ERC/DRC, simulation, fabrication output and
  energisation.

## Current A01 large-radius routing study — Stage33

[Stage33](stage33/README.md) replaces the Stage32 5 mm bends with routes that meet the wire
makers' 10× OD bend rule, and checks the installed state, latch access, the 15 mm withdrawal and
the core 40 mm motion in one model at constant cable length.
- **R33 (CONDITIONAL, pending retention):**
  - J-SIG:middle and J-PWR:middle move to the A01-middle rear face, a broader change that is
    proposed only.
  - Each cable forms one vertical arch at R 12, with a fan-in straight at every exit.
  - Design lengths are 133 / 149 mm. K4 holds for every bow case in the arch's ideal plane.
  - No state enters the undesigned front volume.
  - No part retains the arches laterally (S3 fails); the J-PWR allowance is 1.89 mm.
- **F33 (UNKNOWN):** with front-face headers, the slot path fails K4. The other path runs below the
  code-default foreign plane, inside the undesigned front volume.
- **B32 (INFEASIBLE for every identified wire):** the Stage32 bend-rule and uniform-bow failures
  are carried unchanged.
- **Wire:** no identified wire qualifies for either cable, so the selection is null. AWG28 has no
  JST current rating, and the J-SIG current is not budgeted.
- **NOT RUN:** M-01, M-09, M-12, the M33 measurements, native and physical checks.

## Current A01 service-envelope and retention study — Stage32

[Stage32](stage32/README.md) takes Stage31 B as the working option. It checks the installed state
(at design length, slack in the local loop), latch access, 2.45–15 mm constant-length withdrawal
and the core 40 mm motion in one 3D envelope model. The undesigned neighbouring volume is kept as
UNKNOWN.
- **Recommended:** **B32**, status CONDITIONAL_PENDING_WIRE_SELECTION.
  - Captive notch guides R1/R2 (N1 4.5 mm, N2 4.1 mm deep).
  - Runs lowered for an explicit tolerance stack.
  - J-PWR:middle moved 0.7 mm toward −y.
- **B31 (B as committed)** fails K4 once A01-middle bow and part tolerances are counted.
- **Open:** every identified wire states a 10× OD bend radius, which the r 5 route does not meet.
  K4 fails if a uniform 1.282 mm bow is assumed.
- **Owner decisions:** the 15 mm release needs the RV-DIP / RV-ACCESS reservations.
- **Rail strength:** calculated conditionally (allowable tip load ≥ 11.4 N); not a physical result.
- **NOT RUN:** M-01, M-09, M-12, the M32 measurements, native and physical checks.

## Current A01 cable-entry redesign study — Stage31

[Stage31](stage31/README.md) compares three common entries for J-SIG and J-PWR into the A01
middle carrier ring. The comparison uses filleted 3D routes with r 5 bends, bundle
envelopes, and foreign-depth bounds instead of a cap. **B** is recommended for the next
prototype study: move J-SIG:middle and J-PWR:middle into the clear strip, turn them 90°, and
cut two notches (2.3 / 1.8 mm) in the left rail. It is a proposal only. Rail strength is NOT_CALCULATED,
lengths are design lengths, and M-01, M-09, M-12, native and physical checks are NOT RUN.

## Current provisional DIN design integration — Stage30

[Stage30](stage30/README.md) uses the Stage29 contact positions as **DESIGN_ONLY_PROVISIONAL**
A01 design data, as the owner approved on 2026-10-17 before M-01. It recomputes the 34
DIN-incident Stage15 allocations and 11 signal paths, and traces the 16 assigned contacts.
The Stage28 harness is unchanged.

A separate J-PWR route study finds no route under the existing conditions; a middle-rail
relief is a proposal only. Stage30 also prepares 1:1 M-01 prints and an empty record sheet.
D02 stays CONFLICT_REQUIRES_DECISION, and M-01, native and physical checks are NOT RUN.

## Current DIN source correction candidate — Stage29

[Stage29](stage29/README.md) re-reads both HARTING drawings, including their vector
geometry. Both views look from the body toward the board, and the female fixing holes sit
0.3 mm toward row a. It proposes the column-reversal relabeling
`candidate_position(row, n) = Stage10_position(row, 33 − n)` for J17909/J17910. Nets stay with
the physical contact IDs, and the hole grid and fixing holes are unchanged. NOT adopted:
D02 stays CONFLICT_REQUIRES_DECISION, physical M-01 is NOT RUN, and no copper is bound.

## Current DIN manufacturing and harness continuation — Stage28

[Stage28](stage28/README.md) turns the retained HARTING 96-contact DIN pair and the
A01 transport ledger into a decision table, a vendor-completed harness ledger, an
assembly drawing candidate, an unsent questionnaire and a minimum measurement list.
It finds that the Stage10 DIN labels are mirrored against the HARTING views; a
proper-handed relabeling candidate is recorded but not adopted. Manufacturing,
harness lengths and anchors remain UNCONFIRMED; physical and native NOT RUN.

## Current HF-trim continuation — Stage27

[Stage27](stage27/README.md) selects TC33X-2-203E / C720648 for the existing
20 kΩ HF trim in a separate complete source candidate inventory. It closes that
candidate identity gap while leaving measured adjustment coverage, installed rear
access and assembly qualification open. Stage26 remains the A01–A06 acceptance
authority; historical missing-identity statements below describe their checkpoints.

# Current acceptance and source candidate — Stage26

[Owner-approved A01–A06 musical utility scope](stage26/README.md) is the current
acceptance authority for ATTEN/OFFSET. The inherited 2 mV calibrated static and
associated 1 mV precision-load criteria are NOT APPLICABLE to these six utility
modules; historical reports below retain their original results. Safety, stability,
range, noise, clipping, sensible loading and practical settling remain required.
VCO 1 V/oct tracking and all unrelated precision paths are unchanged.

[Machine-readable scope](stage26/acceptance.json), [functional checks](stage26/functional-checks.json),
[source candidate inventory](stage26/candidate-inventory.json), and
[oscillator calibration clarification](stage26/oscillator-calibration.json).
Keep RV1308 at 100 kΩ; no precision-only reference/pot redesign. Nineteen JLC passive
identities are selected in the source inventory only; production/native CAD remains
unchanged. Existing oscillator rear trims cover base/scale/HF/waveform functions;
final playing pitch uses the front TUNE/FINE controls. Exact HF-trimmer identity and
actual calibration range remain open, with no redundant control added.

Run `python3 scripts/architecture278/implementation/check_source.py` for immutable
historical reproduction plus current scoped checks. No native execution. Next work:
DIN process/position/fixing and externally assembled wiring/strain relief; no further
precision-budget audit for A01–A06. PR286 stays draft; KEEP_K1402_INCUMBENT.

## Historical implementation narrative (superseded acceptance applicability)

The material below records earlier engineering stages. Its old “current” labels and
2 mV/1 mV obligations do not override the dated Stage26 owner scope above.

[Stage17 isolated A01 schematic/library source](STAGE17.md) — source parity only; native acceptance NOT RUN.

Historical preparation: [Stage16 executable A01 native-verification handoff](STAGE16.md). Source packet only; prototype unconfirmed and native materialization/admission pending.

Manual OFFSET requirement: [no centre detent; exact selected part retained](STAGE15-DETENT.md). This addendum applies to the proposed procedure below.

Historical proposal: [Stage15 intended use and factory procedure](STAGE15-PROCEDURE.md). Owner approved continuous manual control; proposed factory procedure remains unadopted, with unchanged2mV/1mVcriteria.

Historical interpretation: [Stage15 acceptance correction](STAGE15-INTERPRETATION.md) supersedes the blanket redesign conclusion in the preserved [allocation analysis](STAGE15-ALLOCATION.md). 2mV is after factory calibration;1mV is separate load change. No component/geometry/calibration change; acceptance remains open.

# O1 candidate source checkpoint — Stage 1 remains OPEN

**Historical Stage15 source result:** [STAGE15.md](STAGE15.md) implements two local LT5400AIMS8E-2#PBF matched-network candidates. All six resistor functions and fixed controls remain;86packages/291pads and108power/return paths include all106 previous targets plus two shield returns. Ratio-onlyCV error improves, but complete2mV static and1mV load-change acceptance remain unresolved. All predecessor evidence and Stage13 calibration remain frozen. Allocated lengths are not actual copper. Native/CAD/ERC/DRC/simulation/physical NOT RUN. Earlier sections below are historical evidence, not current acceptance claims.

This isolated implementation branch starts at PR285 `d218fc537818dcbbd470eb15d192cfc8d0be5f0a`. The owner authorized the one-zone candidate source stage; that approval is not native exact-run admission, architecture adoption or hardware authority. KEEP_K1402_INCUMBENT. PR285 evidence and canonical sources remain byte-identical.

## Implemented source result

`candidate.json` replaces the capacity-only rear packing with eight explicit whole-package functional clusters: FM/PWM, local reference, tune/octave/VEE, PW/LFO, timing/summing/compensation, sync, waveform scaling and sine shaping. The compiler preserves all 154 physical rear packages, their units, local feedback and source `Decouples` associations. Six trim footprints and 6 mm rear tool reservations stay within their circuit clusters. The retained reference/supply/spare units are not removed. Inter-cluster sensitive net distances still require actual layout review; a cluster box alone does not qualify loop inductance or timing performance.

`candidate-netlist.json` is a source interchange manifest, **not a native KiCad netlist or schematic**. Its 250 package/declaration entries, 329 source units, 806 Ref/unit/pin/net/owner tuples and 38 NC tuples exactly preserve the live-extracted O1 plus shared OCTAVE_REF contract. Front jack/control/selector and shared-reference owners are distinct. All 36 legacy factory terminals are retained. No new performance I/O, hidden normal, multiplexing or shared audio/CV bus is introduced. Native schematic and board generation has not run.

Eight dedicated jack signal/AGND links replace the two mixed eight-position jack links. Together with seven function-specific control links and two selector links, the candidate has **17 harnesses / 54 conductors / 108 crimps**, 34 GH header/housing mating locations, 108 signal solder joints and 68 mechanical hold-down joints. Three additional control reference conductors remain explicit. This trades six extra harnesses and 24 extra hold-down solder joints against the prior11/54/108 candidate; no cost or assembly-time saving is claimed. The historical11/51/102 and literal22/102/204 remain comparison baselines.

A deterministic bottleneck matching assigns each rear signal to a unique c-row DIN contact with its adjacent b-row AGND. It minimizes the worst modeled O1/O2 path jointly, rather than independently selecting conflicting pins. All96 positions remain fitted:26 signals,26 AGND and44 NC. This adds **one** AGND assignment relative to the old25, preserving every old signal/return conductor identity. The192 DIN solder joints are unchanged. Electrical pin labels apply to both mates; exact mating-face orientation, physical library and keying remain OPEN. The three shared middle reference nets have no cost in this front-to-rear optimization; their actual middle source paths still require placement and are explicitly listed as unmodeled, together with six octave tap paths.

## Modeled length closure is not routed closure

All52 evaluated O1/O2 front-to-rear rows, including successors to the14 original non-wiper failures and ten raw-wiper paths, now allocate at most **299.760 mm**. Rear distances use the actual retained footprint pad offsets. The sum retains10 mm front trace,60 mm front flex,5 mm middle detour,25 mm connector developed path and5 mm rear fanout allowances. No300 mm ceiling was increased. **Only0.240 mm remains at the worst path.**

The front10 mm term and link centres are assumptions tied to locked panel positions, not a populated front layout. Shared whole front IC packages serve several jacks; final pad/header placements may invalidate those assumptions. Middle diagonals have no routed obstacle/return extraction. Therefore this closes the bounded allocation worksheet only. It does not establish a complete pad-to-pad electrical path, all shared-source paths, capacitance, leakage, return continuity or tolerance margin. Routing and Stage1 acceptance remain OPEN. No onward five-card replication is authorized by this result.

## Candidate mechanical inputs and retained limits

O1/O2 grow from103×115 to **103×150 mm**, at the unchanged proposed rear origins(2,122)/(107,122). All438 panel centres and all33 functions/fiveOSC scope remain unchanged. A vertical100×15 mm DIN reservation at x2.5..17.5/y25..125 provides access along the card. New source-owned supports, asymmetric guides, power strap landing reservations, four existing rail/buffered probe nodes, rear handles and six tool axes are drawn and checked for nominal XY interference and panel bounds. The2 mm inter-card gap leaves1 mm after combined0.5 mm positional tolerances. Middle/core/cover depths remain50/69.2/105 mm; support stack19.2±0.3 mm. Extraction is40 mm with100 mm external workspace after cover removal, with front/middle/neighbor independently retained.

The old support/service receipt does not transfer: old power3 and probe2–4 positions collide with this new population. The new fixture allocations avoid those nominal conflicts. Actual connector tails, guide first-engagement, fastener/support solids and stiffness, formed strap bends, insulation, exact component heights and front seated datums are unqualified.5 mm remains a procurement height bound. O3–O5 retain their prior103×115 **reservations only**; five150 mm cards do not fit the old two-row arrangement. Remaining28-function rear space and all-five population remain OPEN.

Power still uses separately supported low-resistance rail/return joints, not DIN contacts as a qualified main feed. Original source→distribution→branch→load→return paths and all seven unknown load-state maxima are retained. Limits remain branch+K return≤0.5 mΩ, rail≤1 mΩ, hot≤20 mV, full source/rail/return≤0.20 V and GH≤0.5 A/contact. The0.10 mΩ joint allocation is unachieved. Geometry changes invalidate old developed-strap lengths until re-extracted. Unknown contact tolerances, source regulation, dynamic/fault currents and parallel signal-ground behavior remain unknown.

Raw-wiper loading and local1 kΩ/10 MΩ networks, applicable10 nF filters and the complete≤1 nF remote envelope remain. Shared octave1 nF is aggregate over five branches; it does not include five100 nF receivers behind1 kΩ. The retained simultaneous5 V step demands25 mA ideally and transfers2.5 µC; the2 mA planning condition is not a proven physical clamp. No reference-buffer substitution or ground-error cancellation is assumed. #57/#59/#65/#247 stay open.

## Reproduce without native execution

```sh
python3 scripts/architecture278/implementation/candidate.py
python3 scripts/architecture278/implementation/check_source.py
python3 -m unittest discover -s scripts/architecture278/implementation -p 'test_*.py'
```

The second command checks the unchanged seven-generator PR285 packet, candidate output hashes and a stricter checkpoint guard allowing **only** the two implementation subtrees. Generated JSON/SVG is edited only through source/compiler changes. There is no subprocess native runner in the compiler, no fabrication output, no admission receipt synthesis and no change to the native wrapper or CI.

## Remaining bounded work

This task remains bounded to A01. See [STAGE11.md](STAGE11.md) for the next engineering work: resistance-domain reconciliation, a reviewed candidate reference-capacitor correction, loaded-control accuracy and exact joint/service qualification. No A02–A06 replication, POWER hosting, X1 reopening or native/hardware authority follows from this source checkpoint.

A future native run still requires genuine exact-run admission and the required KiCad10.0.6 capabilities. Native/ERC/DRC/routing and physical tests are **NOT RUN**. No source worksheet, deterministic test or review closes full Stage1 acceptance. No manufacture, purchase, energization, merge, adoption or deployment occurred.

## Stage15 — local matched-network candidate, acceptance open

[STAGE15.md](STAGE15.md) implements two local LT5400AIMS8E-2#PBF source candidates from cc005dc4:86packages/291pads, all106 previous power-return targets plus2shield returns. Ratios improve; whole-cell2mV static and1mV load-change targets remain unestablished. Canonical/predecessor bytes and fixed controls are preserved. No native/CAD/simulation/hardware/adoption. Final checks and reviews are in [stage15](stage15/) and [WORK](WORK.md).
