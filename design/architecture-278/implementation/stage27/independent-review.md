# Stage27 independent review

**PASS — source review only.** Exact SHA-256 bindings are in [independent-review.json](independent-review.json). No hardware acceptance, production CAD/native execution, purchase or external contact.

12 focused tests passed in normal Python and 12 in optimized Python. Deterministic inventory/report generation, cached supplier replay and protected-path checks passed. Full historical execution remains root integration verification, not an independently executed check here.

## Findings

- Independently retrieved primary Bourns and exact JLC pages, read retained TC33 PDF and visually inspected page 1. Code 203 is 20 kohm and -2 is rotational-stop top adjustment; pin 2 is wiper, pin 1 CCW and pin 3 CW. Existing HF/LINEAR_REF/AGND assignment is consistent; clockwise direction is not a frequency monotonicity guarantee.
- Nominal drawing-to-pad arithmetic verified: end centers 0.6+0.8+0.6=2.0 mm; longitudinal centers 0.75+0.7+1.2+0.6=3.25 mm match 1.45-(-1.8). Rotated wiper size 1.5 by 1.6 mm and end pads 1.2 by 1.2 mm match the retained footprint. This does not establish solder-process, DRC or installed fit qualification.
- Primary 0.15 W at 70 C and distributor 0.1 W are preserved separately. Tolerance, minimum resistance, contact variation, temperature and rotation limits are scoped correctly; no delivered-lot or ambient/segment-power qualification is inferred. Open-frame reflow/cleaning/force limitations remain process obligations.
- Loaded HF DC KCL includes 1.2 Mohm supply injection and core13 current; HF voltage remains operating-point dependent. Segment-power expression includes wiper loading. Hypothetical examples explicitly do not establish actual volts, frequency/cents range or tracking acceptance. Filter branch is omitted only under the stated DC idealization.
- Read retained AS3340 primary pages 1-2 and oscillator source: base current equivalence, scale/RZ nominal resistance intervals and distinct calibration roles are correctly qualified; no new control or numerical precision burden is imposed.
- Full candidate comparison permits only the three HF identity attributes to change. All 250 packages, 806 pins and 329 units plus all other metadata remain intact; explicit every-NC short cases reject. Stage26 A01 inventory remains separate and byte-bound, and its scoped acceptance is unchanged.
- Exact JLC cached observation replay passes; inventory/assembly declarations are dated catalog evidence, not allocation/order acceptance. Historical worktree integration is structurally appropriate under live immutable-path verification. Full historical execution is root integration verification and was not independently run in this review.

## Resolved guard findings

- Receipt date/hash validation now rejects malformed values, and the exact AS3340 primary record is pinned with negative substitution tests.

## Remaining boundaries

- Physical rear tool access, footprint/process compatibility, segment dissipation and real oscillator base/scale/HF adjustment reach remain unqualified.
- Existing DIN position/fixing/finished-hole/process and assembler-completed wiring definition remain open; no supplier contact occurred.
- No production CAD/native packet, architecture adoption, hardware acceptance or oscillator tracking pass is authorized by this source inventory.

Reviewer changed only these two receipts. WORK and the review files themselves are excluded from substantive bindings.
