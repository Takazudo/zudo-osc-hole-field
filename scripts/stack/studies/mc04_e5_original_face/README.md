# One E5 original-face annulus pilot

This is a separately admitted room-only hypothesis after the completed current-B
exchange attempt (`d96ceb71`, receipt e99dd9467b294f47a2ba53d057ffad29,
SHA-256 afaa58e04a0919c3c83c84f54a2dabd304d88415c81f17fd7604f1de53ec0542).
That attempt found zero U4517 individual rooms and45 R4577 room offsets; it remains
unchanged evidence. The earlier C4534 representation-failure receipt also remains.

U4517's original F-face/angle0 step1 search stopped at12mm; a B-face step2 position
was then accepted at6.5mm before step3. The untested original-F annulus12.25–25mm
is therefore a new finite domain, not an increase of the25mm displacement cap.
The new model uses the **complete original F footprint extracted from the pinned
board before reconstruction**, including its original pads and courtyard. It does
not relabel an accepted B-face model. Strict original geometry is stored in the
spec and a source-only extraction regression checks its complete representation.

The domain contains exactly1,248 retained0.25mm/24-direction offsets, original
ring indices1153–2400, based at original origin(185.95,140.7). Each candidate must
also stay within25mm of accepted origin(191.5792,143.95); rounded coordinate
vectors are checked with exact Decimal squared distances, without epsilon growth.
Original F face and angle0 remain fixed. U4527 stays at the one admitted
point214, shift(1.591,-1.591), B/angle180. R4577 stays B/angle90 and uses only the
exact45 eligible offsets from the hashed previous result: each is revalidated
against the same scene and probe without another2,401-point resistor enumeration.

All412 accepted transforms and26 unresolved originals are reconstructed under
reviewed R1 predicates. Only U4527/U4517/R4577 originals are excluded while testing
these potential models. All seven companion/analog anchors are checked exactly,
including C4534 F/-90 and accepted C4544 B/90 at(189.2026,136.8974).
The original45-contact ledger (one movable U4517 contact,44 frozen) and expanded
function/analog identities remain intact; R4577's exact MPN stays blank.

Candidate pairs are ordered by original U4517 ring index then retained R4577
ring index, at most1,248×45=56,160 checks. Every witness is revalidated as all three
models against the complete frozen scene and pairwise complete courtyard/pad
geometry. Moving models must retain their exact faces/angles and SMD identity;
the frozen scene retains opposite-face through-hole constraints. No extra body,
rotation, link movement or larger domain is admitted.

Terminal statuses distinguish no original-face individual room, no pair fit,
cap reached, a room-only witness and admission/source failure. No-room and cap
results authorize no further retry/domain. Every result leaves canonical26,
canonical changes[] and adopted placements[]. A witness is not functional-layout,
timing/analog/decoupling, routing, access or hardware acceptance.

## Checks and execution boundary

```sh
python3 -B scripts/checks/frozen_studies.py discover scripts/stack/studies/mc04_e5_original_face
```

Small synthetic tests and the one source-only board extraction test are allowed.
Actual original-face search is **NOT RUN during implementation**. Execution needs
independent review and coordinator admission:1CPU,1GiB memory, zero swap,128PIDs,
total600seconds including setup/analysis/cleanup, existing machine-wide shared
heavy lock through termination/cleanup, one attempt and zero automatic retries.
The script is not a resource launcher.

```sh
python3 -B scripts/stack/studies/mc04_e5_original_face/study.py \
  --output "$PWD/.circuit-cache/mc04-e5-original-face/result.json"
```

Output is reserved exclusively before analysis in the ignored cache. All50 input
pins, including reviewed predicates and authorized prior receipts, must match.
Failure preserves a receipt and raises; unknown statuses return nonzero. No
native KiCad, DRC, fill, CAD/canonical geometry edits, adoption or manufacturing.
