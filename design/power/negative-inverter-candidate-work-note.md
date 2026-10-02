# Negative-rail inverter candidate study

Scope: issue #59, unselected OPA388IDBVR plus 150k/1k/4.99k/150 ohm inverter. Preserve current monitor capture, selected parts, current ceilings, panel positions and every red qualification gate. No supplier actions or orders.

The exact source record retains OPA388 SBOS777D and exact Yageo resistor bytes in ignored cache, with committed hashes/locators. Existing TPS37044 source and pin/threshold facts are bridged to the current draft. Candidate identities stay outside selected inventory and CAD.

The calculator derives a strict normal-band total-error allowance, conditional fault-trip/overdrive limits, forced-output backfeed and cold high-Z sensitivity, resistor power enclosures, and a clearly conditioned current comparison. It preserves the RG=1k countermodel and refuses to infer manufacturer leakage, interpolation, maximum settling or ground-loss protection.

Entry and post-edit component validation: PASS, 66 records. Baseline guarded regeneration: PASS (329 seconds), no tracked drift. Thirteen focused arithmetic/source/provenance tests and retained-PDF/report checks pass. Foreground review applied output-contention, opposite load-polarity, strict-boundary rounding and current-report dependency-closure clarifications. Final aggregate/docs checks and exact-head CI remain pending at this first draft commit.

No installed proof is obtained. Source applicability at actual common-mode/supply/load, output and partial-power behavior, current and thermal bounds, maximum timing, compensation, return integrity and full protection remain open. Native/dynamic/bench validation of this new topology is NOT RUN. No native model run can substitute typical-only data for a maximum guarantee.

## Integration evidence

Main PR121 and PR122 were integrated without study-input or numerical changes. The 13 focused tests, retained-PDF/report check and component validation passed again. Initial exact-head CI36975043563 passed (documentation 53 seconds; Python/native/aggregate 11 minutes 8 seconds).

The additional local final waiter was confirmed queued and canceled by coordination before any suite execution: **NOT RUN, exit 143**, not a passed or failed test. Final combined-head CI supplies aggregate regeneration and documentation verification; its exact commit/result are retained on PR123 and the independent review log. This avoids a duplicate local aggregate for unchanged study inputs. No new native or physical qualification is inferred.
