# Independent decision checkpoint — #284

**Recommendation: REVISE. Neither architecture is adopted; production implementation is not ready for authorization.** The preferred functional architecture preserves source intent but currently adds connection burden in the literal two-link topology. It has no demonstrated package-capacity, connector/service, whole-path electrical or structural closure. The core-only alternative is the control for the next comparison, not an automatically selected fallback. KEEP_K1402_INCUMBENT, production CAD and decision.json remain unchanged.

This is a completed independently reviewed **negative design checkpoint**, not completed acceptance of every #279–284 requirement. Keep the epic and children open. The packet is reproducible; further progress on the indispensable geometry/connector/effort choices requires an owner decision and a bounded revision, not resumption of the old routing stack.

## Evidence and acceptance disposition

| Issue | Delivered evidence | Acceptance still blocked |
|---|---|---|
| #279 | 33 function contracts, 438 locked UIDs, all 5,904 packages/8,226 units, 10 existing boards, shared services; unchanged main and parked heads; explicit reuse/invalidation and requirement owners; 100 trim semantic joins to immutable PR261 | No new-board validity inferred from retained inventory; broader component and old electrical obligations remain open |
| #280 | Live O1/shared-reference source extraction: 329 units/declarations, 806 pins including 38 NC, 171 nets; complete package/source parity; O2/O5 Ref-pin mapping; 8 controls including 5 raw wipers, 6 trims and shared octave span; 11/51 harnesses and both faces; 36 shared supply terminals | Exact new connector MPN/pinout/contact multiplicity, worst-case loading/direction contracts, supported detachable terminal conversion and full electrical suitability |
| #281 | Dimensioned fixed-geometry parametric drawing, 3+2 selector planes, separate support/force paths, six trim axes, probes, tool/extraction/cover reservations and conditional service sequence | Actual seated datums, all package solids/capacity, connector latch/mating force, support stiffness/tolerances, cover and supported solder-free replacement |
| #282 | All source packages/347 worksheet rows retained; unchanged whole-path resistance/loss/current limits; common-prefix/branch-tail model; five-receiver reference allocation and fault verification owners | Actual per-device/state maxima and physical path terms, reference frequency-dependent load/noise/drift, exact protection and source realization. 587 partial, 5,309 unmapped, 8 DNP; zero complete supported entries, not zero current |
| #283 | O1/O2 at actual 17 mm pitch, individual old cut lengths, both-face same-path connection arithmetic, hardware/assembly/service/fixture distinctions and non-OSC boundaries | Feasible package/support/connector fit and demonstrable total assembly improvement; exact services/fixture bill and all neighbors' occupied volumes |
| #284 | Separate independent circuit/source, electrical, and mechanical/service reviews; resolved checker defects; retained blockers; staged verification and self-contained future prompt | Owner selection of next bounded study; no go/adoption or Stage 1 readiness |

Counts are scoped: 250 extracted O1 plus shared package/declarations comprise 220 O1 and 30 shared. This does not make 250 packages fit a proposed O1 card. The old source list includes nonphysical declarations explicitly; no source flag is turned into a real part.

## Comparison and engineering findings

1. **Electrical topology is preservable at source level.** Raw-input protection/buffers and output drivers/local feedback remain front-jack; wipers remain explicitly unbuffered where source says so. Core timing, summing, compensation, HF, VEE5 feedback and internal waveforms remain local. Source region packing already prevents physical package splitting. Separate front boards still require new layout and joined verification.
2. **Literal modular interconnect costs more terminations.** Replacing 11 existing spans with front-middle and middle-rear links gives 22 harnesses, 102 conductor segments and 204 crimps versus 11/51/102. Both middle faces are counted. These are subtotals before extra rail/reference/return/service/test connections, not final quantities or projected cost/time savings. The original 55/255 five-OSC and 195/911/1,822 whole-instrument plus 18 power-wire baselines remain intact.
3. **Narrow repeated cards are not yet a fit solution.** Fixed adjacent pitch is 17 mm, while the proposed finger envelope is 20 mm. The 15 mm-wide card reservation has no demonstrated populated/routed capacity. Tool release, wider/offset/staggered core locations or a different supported connector/removal scheme must be evaluated without moving panel hardware. A logical middle zone is neither a separate PCB requirement nor permission to split ground.
4. **Tiny inherited impedance limits remain binding.** 0.5 mΩ combined return and 1 mΩ rail transfer have not been met by selected complete connectors/cables/copper. The five-OSC planning return envelope is 704.5 mA, exceeding one 0.5 A GH contact without proving a safe parallel allocation. No cancellation or equal sharing credit is assumed. Full 0.20 V and hot 20 mV limits remain separate whole-path obligations.
5. **Reference arithmetic reveals missing margin, not qualification.** Proposed direct capacitance allocation is 900 pF over five branches, leaving 100 pF. Existing 100 nF receivers behind 1 kΩ require separate switched-load/stability analysis. The proposed 1 mV absolute receiver error consumes the full 2 mV adjacent differential target in the worst case. Temperature/noise bandwidth/ageing and actual terms remain unknown; buffers do not remove remote AGND error.
6. **Mechanical access depends on exact evidence.** Jack/control planes -10/-11.8 mm retain missing seated datums. Octave -16/-29 mm and its source tolerances remain conditional. Connector mating height is not PCB spacing. Existing soldered main terminals cannot become a solder-free removable card by drawing an extraction arrow.

## Review findings and disposition

`review-circuit.md`, `review-electrical.md` and `review-mechanical.md` bind their conclusions to exact file SHA256s. Reviewers are separate from the corresponding original authors. Findings fixed in this packet include newly introduced shared-reference crossing classification; exact endpoint/net/owner validation; finite numeric/group/limit validation in the electrical allocator; and mechanical parameter/drawing consistency, retained cable bend allowance and package-count scope. Final review receipts record rechecks. Unknown hardware evidence remains a blocker rather than a fabricated passing result.

Reuse source and exact-part evidence within their conditions; rebind all affected geometry, parasitic, load, fault, return, native and physical evidence when inputs change. Parked #260/#277 and #242/E16 negative results remain preserved. Historical finite-path coverage, 552 omission classification and remaining native budgets are not reopened. No old issue is closed by this gate.

## Precise owner decision

Choose whether to fund **one bounded design revision** of the functional candidate, allowing wider/offset/staggered rear-card placement and a tool-operated keyed removal scheme while retaining all panel centres, or prioritize **core-only cards retaining front copper** as the next comparison. For that study, specify enclosure inner depth/support/cover-opening constraints, permitted front-board redesign, connector/removal preference, prototype effort/budget ceiling, and priority between completion and old-copper reuse. The existing 120 mm enclosure is only a proposal. No price or schedule is invented.

Even approval of the study is not approval to fabricate, energize, deploy, merge or run native campaigns. Exact connector and enclosure decisions may require another design review before the one-zone implementation stage.

## Separately authorized stages

1. One zone source/schematic/PCB candidate: exact net/Ref-pin/package parity; complete ERC/DRC/warning disposition; source-linked power/return, protection, mechanical and reproducibility verification. Pinned KiCad 10.0.6 wrapper only with genuine exact-run admission. No whole-instrument motherboard routing.
2. One physical unit with final interfaces and five-receiver-equivalent reference loading: reviewed safe fault/current/energy limits, rails/VEE5 and every order/loss/brownout/off-state state; output load/short recovery; 20-minute warmup, six trims, five-octave tracking, octave steps, waveforms/DC/distortion, FM/PWM/hard/soft sync, drift and service. No fabrication or testing under this packet.
3. Independently assembled second unit: repeat calibration/performance, interchangeability and simultaneous adjacent operation. One-unit success is insufficient.
4. All five oscillators and whole-instrument qualification: complete common services, interference, thermal/assembly/service tests and existing acceptance owners.

5 cents at 25 °C and 2 mV adjacent octave steps remain targets. 0.015–20,000 Hz remains characterization. Define distortion, temperature, settling, drift and other missing thresholds before replication. No missing, capped, reduced-load or unavailable check is PASS.
