# Stage30 independent source review

Reviewer: independent Claude Code subagent (local), 2026-10-17, baseline `00266037a7e2134c9c6c70d1ae95695932e7f1f6`. Status `PASS_SOURCE_REVIEW_ONLY`: source review only. M-01, native KiCad, ERC/DRC, simulation and physical checks are NOT RUN; D02 stays CONFLICT_REQUIRES_DECISION; no route is adopted.

## Design map and allocations reproduce exactly

192/192 contact rows, determinants (design +1, Stage10 mirrored) consistent with HARTING views A/B, 34 recomputed allocations and 11 signal paths agree within 5e-7 mm; power and local paths contain no DIN edge.

## J-PWR screen reproduces; W4 clear only under the recorded z 34 cap

Independent screen gives the same W1-W4 statuses, clearances, cuts and bend limits. W4 meets foreign hardware of unknown depth if that depth reaches z 34.293; the cap is now an explicit ASSUMPTION.

## M-01 PDF geometry and labels are correct

PyMuPDF read-back: 96 holes at 2.54 mm pitch, 78.74 mm span, 90 mm fixing holes offset 0.3 mm toward row a, two 100 mm bars, corner labels at the right physical holes on all four sheets.

## All 12 findings resolved or accepted; none MEDIUM/HIGH open

| Severity | Finding | Resolution |
|---|---|---|
| MEDIUM | M1: W4 clear status relied on an unrecorded cap of foreign unknown depth at z 34 (0.29 mm margin) | route-input.json records foreign_unknown_depth_top_z_mm = 34 as ASSUMPTION, obstacles() reads and checks it, each candidate reports the flip cap (W1/W2/W4 34.293, W3 30.293), README states the margin, test covers cap 36 -> J1710; re-verified |
| LOW | L1: README claimed screening against every Stage10 keep-out; spacers, heads, bosses, other cables not modelled | README now says modelled keep-out classes and lists the unmodelled ones; re-verified that adding them changes nothing |
| LOW | L2: local-end lead ceiling wording ignored loop routes | wording narrowed to routes turning directly toward the ring; loop routes noted as not considered |
| LOW | L3: sampled rail-relief window was 0.016 mm short | analytic x-clipping; window [163.391, 169.943], top 43.898; re-verified |
| LOW | L4: J-SIG proxy distance dominated by the shared start segment | reported per segment; re-verified |
| LOW | L5: PDF read-back used a dict for labels, unsigned offset, generator layout as expectation | one label per corner required, expectation from Stage10 pads plus rev(), hole set compared, offset sign toward row a checked; re-verified |
| LOW | L6: A02-A05 label covered E2/E3 switches | labels corrected and per-candidate unknown-depth blocks listed (W3: A04, A05, E2, E3) |
| LOW | L7: historical consumer count from text match read as exact | field renamed matching_allocation_values; markdown says found by text match |
| LOW | L8: corridor list omitted top crossmember and right rail | other_ring_members added (same 2.4 mm slot) |
| LOW | L9: W3 clearance shown without saying unknown-depth boxes are excluded | field and column renamed to known keep-outs only |
| LOW | L10: power path unchanged statement hid the 16 parallel AGND DIN branches | sentence added in connection-impact.md |
| LOW | L11: hard-coded SVG coordinates; PDF axis glyph without arrowheads | accepted as cosmetic, unchanged; no effect on results |

## Scope held: only README and check_source.py changed

No canonical, locked or decision file changed; command paths use only git and Python. File hashes are in [independent-review.json](independent-review.json).
