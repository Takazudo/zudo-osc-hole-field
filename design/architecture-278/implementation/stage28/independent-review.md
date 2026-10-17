# Stage28 independent review

**PASS — source review only.** Exact SHA-256 bindings are in [independent-review.json](independent-review.json). No hardware acceptance, production CAD/native execution, purchase or external contact.

18 focused tests passed in normal Python and 18 in optimized Python. Deterministic generation, cached receipt replay and protected-path checks passed (`--check --check-cache`). Full historical replay (`--check-history`) is root integration verification and was not run in this review.

## Findings

- Mirror finding independently derived: locked frame x right/y down/z rear is right-handed; both HARTING view arrows look from body toward board (female A above body, tails down; male B below body, tails up). Female viewed along -z gives drawing-to-global det +1, male along +z det -1; the drawings are mutually consistent (Xm = diag(1,-1) Xf, so det Mf = -det Mm). Fitted Stage10 labels give Mf=[[0,1],[1,0]] (det -1) and Mm=[[0,-1],[1,0]] (det +1) with Mm diag(1,-1)=Mf: mated-consistent but both mirrored.
- Root cause traced to stage6/mechanical-input.json matrices asserted at stage6_mechanical.py:12-14, which act on a paper frame (u right, v down, v=-Y); Stage10 signed_transform copies them. Their dets are not drawing-to-global dets.
- Proper-handed relabelings are hole-grid symmetries with det -1 (column or row reversal). With the female 0.3 offset toward row a, only column reversal keeps the Stage10 fixing holes; row reversal shifts them 0.6 mm. This is conditional on the offset side, which remains open (Q-M04, M-01).
- Mated net continuity is preserved because both boards carry net(label P) at the same position P and the physical contact k at P on the female mates with male contact k at P. The 09031966922 loading is all standard pin type A, so mating sequence is unaffected; the consequence is contact numbering, inspection and orientation, not a short.
- D03/D04/D05/D07/D14 values read against the rendered HARTING drawings (96x Ø1±0.1, position Ø0.05 without datum letters, 2x Ø2.8 +0.1 at 90±0.1, symmetry 0.1 to A, offset 0.3±0.1, female tail 2.9 +0.15/-0.05, male tail 3 +0.4); 0.075*sqrt(2)=0.106 mm > 0.025 mm arithmetic correct. JST GH policy (AWG30-26, insulation OD 0.76-1.0, 50 V, 105 C, SSHL-002T-P0.2) matches design/connectors/sources/jst-gh.pdf page 1.
- Harness ledger reproduces 20 GH conductors in 4 links (7/4/6/3), 14 permanent tails, 96 DIN contacts (16 assigned on b1-b8/c1-c8, 80 NC), 22 non-BOM land annotations with exclusion flags, and 20 source NC endpoints. Measured path, cut, bend radius, anchor and clearance stay null; all results NOT_RUN.
- Mutation tests reject missing contact, one-side mirror, both-side relabel (via D02 binding), contact swap, one-connector net swap, NC contact made live, unsupported pass in status or free text, zeroed unknown/nominal/tolerance, empty post-answer decision, moved header/flange/grid/land, frame flip and trimmer loss.
- Full historical replay (--check-history) is root integration verification and was not independently run in this review.

## Resolved findings

- D-1 (HIGH): report.json was stale (source hashes of stage28/README.md and check_source.py) and the generated-files test skipped report.json. Regenerated; the test now compares report.json with preservation_baseline taken from disk.
- D-2 (MEDIUM): 'only column reversal' was unconditional while D05 leaves the offset side open. Now stated as conditional in README, report.din.hole_preserving_condition, D02, Q-M01 and M-01 records the offset side.
- D-3 (MEDIUM): Stage6 paper-frame (v=-Y) root cause and Stage10 signed_transform note added (report.din.stage6_frame_note, README); pin-type-A mating note added (report.din.mated_contact_types).
- D-4 (MEDIUM): tail OD up to 1.0 mm through a 1.0 mm guide allowed zero clearance. Policy now requires OD strictly below the guide minimum open diameter bound per row from Stage10 carrier_wire_guides; clearance_mm null UNDETERMINED (Q-H03).
- D-5 (LOW-MEDIUM): D06 changed to UNCONFIRMED with retention left open consistent with D09; D11 softened to what the drawings state.
- D-6 (LOW): nominal/tolerance <= 0 rejected; case-insensitive free-text claim guard over all source strings; non-empty decision if/then enforced; missing-contact tests assert messages.

## Remaining boundaries

- D02 remains CONFLICT_REQUIRES_DECISION; the column-reversal candidate is not adopted and no board copper may bind DIN labels to XY until Q-M01, M-01 and owner decision Q-O01.
- Fixing-hole offset side, finished-versus-tool hole diameter, Ø0.05 position capability, board thickness, mating forces, process limits, cleaning and inspection class remain UNCONFIRMED or UNDECIDED; the questionnaire is unsent and no supplier contact occurred.
- Harness wire MPNs, lengths, bend radii, anchors and clearances remain undetermined pending fit-up measurement; every physical and inspection check is NOT_RUN.
- No production CAD, native KiCad execution, fabrication output, architecture adoption or hardware acceptance is authorized by this source review.

Reviewer changed only these two receipts. The review files themselves are excluded from the bindings.
