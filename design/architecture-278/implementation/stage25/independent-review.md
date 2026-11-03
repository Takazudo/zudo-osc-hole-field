# Stage25 independent review

**PASS — source review only.** No adoption, electrical acceptance, CAD/native execution, purchase or supplier contact. Reviewed hashes and exact commands are in [independent-review.json](independent-review.json).

34 focused tests passed in normal Python and 34 in optimized Python. Deterministic report, cached source bytes, supplier replay and protected-path verification passed.

## Independent findings

- Independently checked stationary loading against a dense grid and nominal impedance, settling, track power/current, unchanged open-wiper return sensitivity; 16 component corners are accurately described.
- Candidate binds exact B104-to-B103 identity, retained pin nets/NCs, placement and unit metadata; no reference swap or production topology change is adopted.
- Read OPA4197 printed page 7: 20 pA is MAX under table conditions, not typical; 15 nA PW full-temperature sensitivity and doubled two-point sensitivity are correctly distinguished from installed drift.
- Read REF50 printed pages 7 and 24: initial grade limits, box-method drift and typical noise/aging/hysteresis support the qualified claims; no local derivative or lifetime guarantee is inferred.
- Bourns ordering and ratings support resistance-code-only candidate; faster filtering and higher reference load remain tradeoffs, not proven precision necessity.
- Dated exact JLC observations replay from cached pages; stock fields are snapshots, not allocation, order acceptance or exact process qualification.
- Independent current JLC capability research supports tighter circular-hole sizing for multilayer ENIG; position, female fixing holes, finished-drilling interpretation and exact assembly remain unresolved. Default guarantee gaps do not prove universal incompatibility.
- Complete remainder ledger keeps unknown terms null and cannot issue a complete mathematical pass while incomplete; hardware acceptance is always false. Initial intercept removal requires real setup, not fitted data subtraction.

## Corrections and resolved findings

- My Stage24 review's fixed-knob 'feasibility failure' is a diagnostic result only, not proof of failure after real baseline adjustment under the retained Stage15 owner decision. Stage25 corrects that interpretation without rewriting historical evidence.
- My earlier advisory that 20 pA might be typical was incorrect for the retained OPA4197 table: it is the table-conditioned maximum; Stage25 correctly scopes it.
- Root corrected prose from 32 to 16 corners, bound central Stage15 and retained DIN dependencies, and added redirect/UTC/available-hash validation with negative tests.

## Remaining boundaries

- Temperature/time-after-setup envelope and factory protocol remain unapproved/null; simultaneous actual-condition error bounds and the separate 1 mV load-change bound remain open.
- Pot candidate is not adopted; reference buffer current, filtering response, contact behavior, stability and installed assembly need qualification.
- DIN position/fixing/process agreement remains unresolved; fabrication specification is unsent. No exact replacement route is qualified.

Reviewer authored only these two review receipts; root remains sole implementation/branch writer.
