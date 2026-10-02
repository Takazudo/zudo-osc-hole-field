# Toggle/button evidence correction

Acceptance review of issue 13 found that its existing native footprint fixture
passes while several source criteria remain open. Keep the issue open; do not
substitute a different toggle identity or infer physical qualification.

Correct Omron B3F-1020's terminal/PCB figure locator to physical PDF index 3,
printed page 4. Correct the Dailywell catalogue mirror's first relevant page to
physical index 1, printed page 25. Retained PDF bytes and their hashes are
unchanged. The official Dailywell GET was retried on 2026-10-02 and still returned
HTML with contact/CAPTCHA fields, not a PDF. Keep both official source records
SOURCE UNAVAILABLE with zero hashes. The separate receipt hashes the inspected
HTML response only; no form was submitted or supplier contacted.

The retained switch tables establish drawing POS.1 -> 2-3, POS.2 open for 2MS3,
and POS.3 -> 2-1. They do not by themselves establish panel-left/right under the
current pad3-left convention. Remove that unsupported equivalence from both the
mechanical facts and pin-map truth table. Preserve terminal pairs, symbols, pads,
nets, selected MPNs and panel centres. Drawing projection, installed face/rotation
and physical continuity still need reconciliation before wiring acceptance.

The 9.4 mm actuator datum is not a pivot-to-tip maximum and cannot justify the
claimed conservative swept radius. Remove that claim from the facts and fixture
output. The native fixture contains footprints only; actual swept-envelope
clearance remains NOT RUN. Derive its nominal courtyard-gap printout from the
actual footprint instead of fixed summary literals.

Fresh pre-edit fixtures at main8337991 passed native DRC with zero violations and
rendered SVG; that result establishes local footprint clearance only. The source
and post-edit checks are recorded with the PR. Exact unsuffixed/-5 equivalence,
lever mapping, swept clearance and installed fit remain open in issue 13 and
physical qualification tasks. No fabricated source, measurement or positive fit
claim is introduced by these corrections.

Post-edit guarded aggregate regeneration, fresh pinned toggle/button fixture,
component validation, generated output, documentation build and strict links
passed (297 seconds). Independent source review found no remaining scoped issue.
All tracked CAD, symbols, schematics, boards, panel lock and electrical-standard
bytes remain unchanged. Exact final CI and any parent integration are recorded
in the PR; this evidence correction does not satisfy the open issue-13 gates.
