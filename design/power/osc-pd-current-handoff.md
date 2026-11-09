# Current OSC supply dependency handoff — 9 November 2026

**Implementation dependency, not a selected supply or manufacturing release.**
This records the accepted OSC interface at source commit
`433c88b27b2e49284fe1a717b47ba4226c829dd3` for issues #319, #59 and #57 under
#315. The companion `osc-pd-current-handoff.json` binds exact source bytes and
copies the relevant requirement fields. It is a dated snapshot: recheck its
bindings and applicability after any source change. No sibling file, circuit,
PCB or protected architecture study is changed by this handoff.

The order scope remains ten functional OSC boards plus the separate panel.
The external power assembly is a separate dependency. Current `INLET` and
`BOUNDARY` symbols in `design/spec/modules/power.py` have no orderable identity,
footprint or protection implementation. Their ERC pin types do not implement
power switching. They cannot enter a manufacturing BOM as completed hardware.

## Accepted decisions and the retained current margin

E11 selects the **revised 20 V / 5 A USB-PD direction**, with a 5 A e-marked
cable and changes on the PD side. E12 requires **accept or refuse**: insufficient
contract means all OSC rails stay disabled. Neither decision adopts an entire
architecture study, selects a completed source, or proves startup and protection.

The owner additionally chose to keep the external OSC/PD current contract on
2026-11-04 at 03:07 UTC (option 1). The retained decision is in
`design/architecture-278/integration/power-contract/README.md` and the
`CONTRACT_DECISION`, `CONTRACT_CONTINUOUS_mA` and `CONTRACT_TRANSIENT_mA`
constants in `ledger.py`. The lower post-S2b canonical rule result is **not**
permission to reduce the external contract.

| Quantity | +12 V | −12 V magnitude | +5 V | Meaning |
| --- | ---: | ---: | ---: | --- |
| Canonical calculated continuous minimum | 1,600 mA | 1,600 mA | 300 mA | Current `supply-architecture.json` result, not measured demand |
| Retained external continuous contract | **1,700 mA** | **1,600 mA** | **300 mA** | Required delivery; +12 V retains 100 mA margin |
| Canonical calculated transient minimum | 1,900 mA | 1,900 mA | 400 mA | Current rule result |
| Retained external transient contract, at least 20 ms | **2,000 mA** | **1,900 mA** | **400 mA** | Required delivery, not a 20 ms average |
| Maximum delivered current, including tolerance and fault let-through | 2,100 mA | 2,000 mA | 500 mA | Interface ceilings, not device ratings |
| Source voltage band, ripple included | 12.00–12.30 V | 12.00–12.20 V | 5.05–5.10 V | Required source bands |
| Permitted load voltage magnitude | 11.53–12.48 V | 11.74–12.37 V | 4.81–5.20 V | Include both rail and common-return shifts |
| Nominal load-capacitance ceiling | 150 µF | 150 µF | 100 µF | Add 20% tolerance: 180/180/120 µF |

The resulting limiter window above the retained transient contract is only
100 mA per rail. Its realizability remains unproved. A delayed trip or fuse
rating alone does not bound peak let-through to these maxima. The supply must
also satisfy the 10 ms minimum soft-start requirement, strictly below 1 mVpp
load ripple, and at most 0.20 V total rail-plus-return loss. The inlet allocation
allows at most 40 mV protection loss and 20 mV distribution loss. These remain
requirements, not established capacity or performance.

The retained ramp condition constrains the steepest portion, not only total
duration: a common linear/monotonic 10 ms ramp at the source-band maxima gives
1.23 / 1.22 / 0.51 V/ms. An RC or stepped waveform must bound its maximum
dV/dt; averaging over 10 ms does not bound capacitive inrush. Interrupted
ramps are separate fault/startup cases. The dated study's proposed no-load
slope exceptions are not adopted by this handoff.

The companion snapshot preserves `null` for guaranteed whole-instrument
maximum current and measured source capacity. Planning currents, table maxima
at another supply, or an ideal capacitance-ramp calculation cannot fill them.

## Logical connection and assembly boundary

| Logical pin | Signal |
| --- | --- |
| 1 | +12V_IN |
| 2 | −12V_IN |
| 3 | +5V_IN |
| 4 | NC; unpopulated |
| 5–8 | AGND |

These are logical contract numbers, **not** a manufacturer's mating-face view
or PCB pad assignment. There is no power-good/control pin. Do not turn pin 4
into a control signal without a reviewed interface change.

The exact header, housing, contacts, orientation and footprint are unselected.
Molex 43045-0800 / 43025-0800 / 43030-0007 are retained candidates only. The
contract requires simultaneous contact capability of at least 5 A and 30 V,
a factory-crimped polarized/latching harness, minimum 20 AWG conductors and a
maximum 300 mm length. Verify the selected contact's wire compatibility,
derating and drawing before adoption. An enclosure bracket and strain relief
must carry insertion/cable loads. Do not rely on PCB solder joints alone.

All 180 patch sleeves remain AGND. Any single inlet return must be assessed
for the full 4.6 A sum of interface current maxima; four return contacts do not
prove equal sharing. Inlet hot-plugging remains prohibited. This does not
waive the separate protection requirement for ordinary powered-off patching.

## Exact external work required

The separate PD implementation must deliver the following, bound to an exact
reviewed source/board/programmed revision. This is a dependency handoff, not
permission for this session to edit or order that repository.

1. **Contract acceptance before enable.** Recognize the accepted 20 V / 5 A
   contract and suitable e-marked cable. Refuse default attach, insufficient
   current, other PDOs, failed negotiation and unsupported cables with every
   OSC rail disabled. Produce programmed-state/readback and state-machine
   evidence; a firmware setting or successful negotiation alone is insufficient.
2. **Actual capacity and voltage bands.** Implement converter/regulator/current
   paths for the retained continuous and 20 ms transient contract at source
   bands. Account for cable, connector, switching, quiescent and thermal losses
   with source-backed component conditions. Establish ripple and startup
   behavior at the specified capacitance and load envelopes.
3. **Input protection at 20 V.** Resolve the recorded TVS/controller clamp-margin
   incompatibility with exact parts and tolerances, including transient and
   controller absolute limits. The old 15 V path cannot become a 20 V path by
   changing only a PD request.
4. **Three-rail current limiting and reverse blocking.** Select and capture real
   switching/driver paths, body-diode behavior, hot resistance, dissipation and
   startup SOA. Bound maximum delivered current including dynamic let-through;
   do not substitute a PTC hold/trip number for that proof.
5. **Coordinated removal of power.** On contract loss, insufficient renegotiated
   contract, brownout, source removal or rail fault, disable all rails and
   discharge stored energy under a bounded sequence. Provide detection,
   disable, discharge and injection timing over every arrival/failure order.
   Keep AGND connected. The final restart/latch policy must have explicit
   accepted provenance and a source-backed implementation.
6. **Return integrity and physical interface.** Establish a method independently
   observable from replacement patch-sleeve return, and agree which circuitry
   owns it. Complete exact inlet/mate/pin orientation, harness and assembly
   responsibilities jointly with OSC; no existing control pin may be assumed.

For each item return schematics/netlists, exact BOM/pin/footprint evidence,
worst-case calculations and applicable models, native check receipts, unresolved
conditions, and the physical qualification procedure/results required by #57.
No measured result is available in this handoff.

## OSC work that remains local

External reverse blocking and rail shutdown do not protect every OSC pin.
Issue #59 must still capture actual load-side monitoring, permit/latch and
signal-isolation circuitry; account for all current/precision-sense/octave
paths under powered-off and partial-power states; and prove local feedback,
contention, leakage, stability, package thermal limits and disable timing.
Local-ground loss and return observability remain explicit faults. All added
sections, decoupling and auxiliary current must enter the source/netlist/BOM,
partition reservations and electrical ledger before layout acceptance.

`python3 scripts/checks/protection58.py --check --require-closed` is still
expected to fail because no complete topology is selected. The draft contract
check and zero ERC errors cannot close it. The related source/physical gate
#57 and assembly/fit gates remain open.

## Historical evidence and limitations

The older `design/architecture-278/integration/power-contract/pd-interface-20v.md`
is retained. Its ADG5412F input population, OPA4197IPWR-wide assumptions and
unadopted P59 proposals cannot be transferred wholesale onto S2b. E13–E15
adopted TMUX7412FRRPR input switches, TMUX6112PWR envelope switches and the
specified precision changes. Remaining supply-condition, cold SEL, leakage,
capacitance and timing gaps are not resolved by the identity substitution.

The older interface's proposed 1 ms shutdown, 100 ms discharge, numerical
skew limits and slope exceptions are not silently elevated to accepted
requirements here. Where a value relied on an obsolete device or an unadopted
candidate, rederive it for the actual circuit. Preserve the accepted behavior
and existing targets; unresolved bounds remain blockers. Do not use absolute
maximum ratings as recommended operating limits.

The retained PD quotation inputs name commit
`65031f98f02677998efada217f64e731d39437f7` and capability-screen commit
`6071e1757c7678a4b5ed0af069a9eae202c6ee2d`. They describe historical 15 V
hardware/screens, not a qualified revised supply. The existing read-only
`verify_pd_pin.py` checks those exact bytes without changing the sibling
checkout. Later dated PD references in the study are separate evidence;
none is a claim about today's uninspected sibling head.

Before integration or order review, recheck every snapshot source hash,
recompute canonical requirements, retain the owner contract margin, and bind
new PD evidence to exact revisions. Until the external implementation and
local protection gates pass, the full instrument remains **blocked for
manufacturing review**, while independent engineering may continue.

## Verification of this handoff

- Current snapshot arithmetic: canonical continuous/transient minima are at or
  below the retained owner contract; each retained transient requirement is
  strictly below its interface maximum. The JSON values were read from the
  named sources, not copied from the older prose.
- Historical PD quotation validation: PASS using the existing
  `verify_pd_pin.py` checks. Baseline source bytes came from read-only
  `git show` at `65031f98…`; the local checkout lacked `6071e175…`, so the
  capability file was read from GitHub at that exact commit and verified as
  `e5864272b5e1e4a1876a69c95dc9a2fcd5683fea61a3d783016a52f7b18e2b8d`.
  The validator's reader used those retained bytes only for that exact
  commit/path; all numerical/quotation assertions remained unchanged.
- `pnpm circuit:check`: PASS, 72 manual inventory lines, zero declared
  placements; no schematic/placement binding, pin-asset check performed.
- No native source/copper change, new electrical model, physical measurement,
  revised-PD implementation verification or manufacturing export is claimed.
