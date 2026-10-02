# Mixer and schematic-status reporting correction

## Scope

Read-only reconciliation of issues #27 and #50 found that the MIX4 page still announced the original failed waveform target after the fixed in-range model calibration was merged. Its report described the summer/TIA as ±12 V amplifiers even though they are unbounded dependent E sources. Mixer instance indices in the generator README and several worksheet subtotals in the schematic-status page were also stale.

No circuit, component, panel coordinate, numerical model criterion, calibration or simulation deck changes. The retained TI/National LM13700/NS single-OTA model remains the same SNOM267 source, SHA-256 `666df501773da5e65f7fd3b3c806b2c1ae7770784685dd8191a9df33b382f390`. The physical exact device remains LM13700M/NOPB. The fixture's summer/TIA have no supply pins or saturation model; ±12 V supplies feed the OTA model, with bias imposed separately. A bounded waveform result does not establish real headroom or the full current servo.

## Current publication

Canonical regeneration refreshes the mixer package worksheets, the master rail budget, then the marked current sections of the schematic-status page. The renderer obtains family membership and per-instance planning figures from `design/power/rail-budget.json`, covering all 33 modules and the shared octave reference. POWER bleeders remain a separate incomplete contribution. Authored model/connectivity notes remain outside the generated sections.

Current MIX5 family planning subtotals are +79.2/−73.2/+5 1 mA; MIX4 is +93.2/−87.2/+5 1 mA. The same source mapping corrects oscillator, A/B and whole-instrument prose drift. Displays round to 0.001 mA and link to full report precision. Every missing complete maximum remains NOT ESTABLISHED; H1/H2 retains its partial-known-subtotal warning. The historical 80% source-ceiling comparison is not the selected EXT source requirement or measured capacity.

The old connectivity counts and native results are explicitly labeled as the f663143 integration checkpoint. Current retained audit and ERC identity files are named separately; no fresh whole-master native result is claimed by this documentation edit. The A/B status retains the bounded selected-buffer-to-jack model and its excluded input/contact behavior.

## Verification

- Entry component contract PASS for 65 manual inventory lines. Guarded baseline regeneration PASS in 283 seconds, no tracked drift.
- Ten focused mixer/current-publication/master-budget tests PASS. Publication regressions cover changed source values, incomplete/unknown maxima, complete instance coverage, duplicate/missing rows, missing rails and nonfinite values, and marked-section ownership.
- Fresh pinned native mixer rerun PASS in 12 seconds. All 13 deck hashes and every numerical/report value exactly match the prior report after replacing only the twelve corrected condition strings. No new calibration or model criterion was introduced.
- Final guarded aggregate regeneration (`--check`), documentation validation/build and strict site checks PASS in 226 seconds. No tracked regeneration drift; the existing workbench template-link allowlist exception is unchanged. Component contract PASS for 65 manual records.

## Remaining

Physical gain/feedthrough, real amplifier headroom, complete servo and clamp, package coupling, temperature, stability, fault behavior and current maxima remain unqualified. No issue closure, procurement, fabrication or upstream release action is part of this correction.
