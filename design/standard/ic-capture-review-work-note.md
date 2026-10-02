# Current shortlist capture review

Date: 2026-10-02. Scope: original issue 15 capture acceptance and current-source
coverage. All symbols, footprints, schematics and boards remain unvalidated drafts.

The fresh audit failed: the capture ledger still named KT-0603W / KT-0603R,
while the current shortlist selects Kingbright APHHS1005QWF/D and APG1005SEC/E-T.
Only 34 of 36 rows matched. Its static native fixture also omitted the selected
Nexperia BAS16GW-QX diode. The original implementation is already merged; this
pass repairs current coverage rather than replaying that implementation.

The capture ledger now matches all 36 current shortlist identities. The native
fixture resolves each exact MPN to one symbol, rejects missing or ambiguous
matches, obtains reference prefixes from symbol properties, and places every
unit. It includes all three PTV09A pot values and both selected compact LEDs.
Nine columns keep all 69 units within the A3 fixture page. CI now executes both
the capture/pin-evidence check and the all-unit native ERC fixture.

Sixteen retained-source metadata records had truncated revision strings, old
publication dates, or irrelevant embedded PDF metadata. The accompanying
`source-metadata-audit.json` records inspected byte hashes, replacement fields,
and the actual supporting physical/printed page locators. Acquisition hashes
and dates are unchanged. The Vishay TNPW0805 drawing is physical index 14,
printed page 15, not the cover; its symmetric project pad numbers are not
manufacturer terminal numbers. The Fenghua mirror is visibly a high-voltage
MLCC family specification, revision A2 dated 2025-05-30. It still does not
establish exact 1206CG104J500NT identity or performance; its exact-part facts
remain UNSOURCED and its real mirror hash is retained.

Checks performed:

- Before edits: component contract PASS (manual inventory, 65 lines, zero
  declared placements; no schematic/placement binding, pin-asset check run).
- Guarded baseline aggregate regeneration PASS, 187 seconds, no tracked drift.
- Current capture/pin evidence PASS: 36/36 rows, 31 standard pin maps checked.
- Native KiCad 10.0.6 all-unit ERC PASS: 36 symbols, 69 units, 240 pins,
  zero violations. This checks symbol capture, not a functioning circuit.
- Three regression tests PASS: exact replacement inclusion, suffix mismatch
  rejection, and ambiguous-MPN rejection.
- Post-change aggregate regeneration and native checks PASS. The combined
  runner then failed on an unsupported documentation CLI option; no source
  failure was reported. Corrected documentation check/build/publication/link
  suite PASS under the guard in 36 seconds.
- Independent review found no blocking issue. Final-head CI is recorded in
  the PR; parent integration is checked separately before merge.

Sourcing and assembly risks remain open, including exact Fenghua evidence,
factory-only soldering, programmed NOISE2 supply, AS3340D allocation and actual
stock/assembly acceptance. No part selection, pin connection, footprint,
model, fixed hardware position or electrical requirement changed. Physical
qualification is NOT RUN: this pass has no assembled hardware or measurements.
