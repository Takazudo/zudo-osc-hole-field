# MC-02 five-check packet: pre-integration rebind draft

**State:** DRAFT / NOT A GATE PACKET. This note binds the reviewed MC-01 paper
candidate to the existing MC-02 extraction handoff. It does not replace that
extraction, establish an integrated revision, decide Gate A-paper or qualify a
board. Moya remains the sole campaign integrator. Issue: [#365](https://github.com/Takazudo/zudo-osc-hole-field/issues/365).

## Source and ownership boundary

| Item | Identity / status |
| --- | --- |
| Current local review composition | `2c53715d49a4a7639723595590d1fd4eeb3a3c1f` (MC-01 c6 `bf6c67718f2fe157bd58966d0c3555ea8f37b596` plus MC-03 source rebind); clean local candidate, **not integrated or pushed** |
| MC-01 kernel | Reviewed ancestor `e4b300b31fccf53acfeafc8fbba286278c32ecfb`; `scripts/stack/link_electrical/link_ratios.py` SHA-256 `5902c93d2ffd5aa4ba4635840f5daca63d89427eb99800f580fd6434a1c0e111` |
| Conductor/geometry record | `design/stack/geometry/links/link-gate.json` SHA-256 `1c091c1d6d4b9c000f770a0e604cb986d5c55e44cb77ea22083249afbf5cdb0d`; consumed record projection `54d9fc4e26453d951cf0dfc7a5b092789f63250e99a743b9f67fa6d7962b85f6` |
| Electrical source and output | `inputs.json` SHA-256 `aeb837844dd0359fa7a08348431f633f1ce5c03e9042f143d0822f2e13b25ea1`; `link-ratios.json` SHA-256 `9c35ee28dce48376836577ec46748c7420dc596ced6f6803f7aace1686d4f3c3`; `c6-pass.json` SHA-256 `2e22fd43b78c7c55386587a2e31492bcf1acbd2d062a1aedf7d4536644dd8f55` |
| Existing MC-02 extraction | Task `6afac5fc-b834-8191-b0a2-d6f9c613d03a`, turn `01a1e395-6e5f-7017-8843-351f064a2df9`, completed read-only on `690366aa69450b642f7daee2cb809eb5ded38d63`. Moya forwarded its exact preliminary receipt; the historical findings are transcribed below. No second extraction ran. |
| Final packet source | **PENDING** reviewed *integrated* MC-01 revision and exact rebind from both the MC-01 candidate and the existing MC-02 extraction. The local composition above is not that revision. |

The bounded MC-01 source review found no blocking code defect in the paper
model. Its retained c6 report preserves 61 placed links and 511 signal
identities, with 340 ground and 321 unused positions. The model reports zero
link ratios above 1.0; its maximum is **0.978101** on `P-K-P-L03.01`. These are
calculated cable/ground-coupling bounds, not measured harness performance. The
P all-posts-open current bound is `0.0997772 A` in `link-ratios.json`, subject
to the retained model assumptions. Neither figure decides the other four
Gate A-paper checks.

## Owned preliminary extraction at historical main

The following owner receipt is pinned to historical `690366aa69450b642f7daee2cb809eb5ded38d63`.
It is not a claim that the bytes or results survive MC-01 or a future merge.
Its Git blob IDs were checked against that commit:

| Artifact | Historical Git blob ID |
| --- | --- |
| `design/stack/geometry/links/link-gate.json` | `4e2b76400de0a84a45b94d5ebc807be408d254b9` |
| `design/stack/fixings/threading-procedure.json` | `bda863cdc0210b1ecd4b3d50e66fe363a94b4100` |
| `design/stack/link-electrical/link-ratios.json` | `d83ff5e59e79f4f9267a311102bbc22953ab7974` |
| `design/stack/link-electrical/inputs.json` | `e348e079042a57d5af741861eabcce8211787123` |
| `design/stack/connectors/flex-links.json` | `1e85f9fa937675f3a826008c055e9431424436a5` |
| `circuit/orchestration/campaigns/osc-stack-20261114/st-01.md` | `cdddc2e3f6e0d5b199b93bdd251218a4ecdbea06` |
| `design/stack/connectors/flex-land-patterns.json` | `d55790531315f6cbacc323d6936bd2d9da597574` |
| `design/stack/geometry/links/link-gate.md` | `e90d43b6f23301b5a530c1ea4ebb2e6c4c574390` |
| `design/stack/fixings/threading-procedure.md` | `115f380fa5cafaa670774fbc6e0c8a8d2631921c` |
| `design/stack/link-electrical/README.md` | `c84160df19da4ceabb2bc9c442615007a934507b` |
| `design/stack/thermal/README.md` | `6c780be111573f22c0de42dd43a492328ddfece6` |

ST-04's pinned link projection SHA-256 was
`6584f7ddf44ef7143848cf362eada29a6faf6fd91eb6c4f9eccf9cb955bda8ad`;
ST-08's different gate-record projection was
`2139208b7af181992f32e6d63305b450e47a65556806b1d62e0e8958d58cce6b`.
The private resource inventory at `Takazudo/circuit-dev-resources@d7cdf9e4dde7906abeafe82c7aa4f66134eee2f9`
listed FH12 PDF SHA-256 `9f056f58ff000739633cc3cb7697ba185967083dcf1429b7ab10783b3f55bac5`
and Bourns PTV09 PDF SHA-256 `411cdb6a62e61f9c5bc2df76ed64ee21d7bcfbee035c1ba36beff08c43f28558`.
The owner did not independently byte-hash those private PDFs or publish copies.

## Five-check handoff slots

| Check | Candidate facts now bound | Existing extraction / final rebind needed | Status |
| --- | --- | --- | --- |
| 1. Connector and cable identity | Historical ST-01h records 122 Hirose `FH12-{8,14,26,40}S-0.5SH(55)` bottom-contact connectors and LX same-side FFCs on 61 links. Selected cable codes: C26618 40P/50 mm ×18, C29534 8P/50 mm ×28, C32128 26P/60 mm ×3, C68390 14P/50 mm ×9, C81339 8P/40 mm ×3. Land record: 0.5 mm pitch, 0.3 × 1.3 mm pads, 2.2 mm tab length, derived 1.8 mm tab width. | The retained LX A771 drawing gives 0.30 ± 0.03 mm tail and 0.12 ± 0.03 mm body thickness for an *opposite-side* 40P cable, not these selected same-side codes. Selected-code drawings, FH12 open height/side and contact-1 end remain UNSOURCED; 5.0 mm open height is ASSUMED. Rebind exact identities. | PRELIMINARY; source/physical gaps open |
| 2. Opening, locking and access | Historical threading record: 13 steps, K lowered in nine stages, at most 17 ends at once; 27 open, three open after displacement, 31 `NOT SHOWN` latch reaches. Twelve K locks need the other hand supporting K's edge. | Neighbour package heights absent; exempt packages being below the 2.0 mm connector is assumed. Human 17-end threading and cable folds staying put NOT RUN. M3 × 25 mm screw/tape retention assumed; nut height and washer thickness unsourced. Confirm actual assembled access. | PRELIMINARY; 31 access gaps |
| 3. Allocation and current | Historical: 511/511 signals, 61 placed links, 322 grounds/339 unused; worst one-post-open ground contact `0.047 A` against `0.35 A` working bound. Local c6: 511 signals, 340 grounds/321 unused and modelled P all-posts-open `0.0997772 A`. These are **different revisions and operating cases**. | Recompute allocation, current and record projection together at reviewed integrated MC-01. The 26 unplaced ICs below remain gate inputs. Current is modeled, not measured. | CANDIDATE model; final rebind pending |
| 4. Coupling | Historical `NEEDS_DESIGN`: five above 1.0, max 1.42134. Local reviewed c6 candidate: all 61 modeled links at or below 1.0, max `0.978101`. | Rebind complete class-pair table, projection, kernel and independent review to integrated MC-01; retain source/native checks and unknown measured harness behaviour. | CANDIDATE paper result only |
| 5. Cumulative rework | Historical: 438 displaced footprints, 412 courtyard positions, 26 unplaced ICs. K service opening takes 288 operations; after ten openings K ends reach 11 of the sourced 20 insertions. Accepted workload: 122 latches, lead trimming on 83 parts (92 per-tail entries), 22 fixings and 30 lengthened tails. MC-03's 104-adjustment plan is a separate candidate. | Courtyard room does not prove timing, precision, summing routes, service or assembled clearance (DS-97). Rebind counts and 26 refs to integrated record. | PRELIMINARY; actual layout unresolved |

The five historical over-limit links were `P-K-P-L01.01.01` 1.42134,
`P-K-P-L07` 1.13579, `P-K-P-L08` 1.134, `P-K-P-L03.01` 1.1325 and
`P-K-P-L13.01.01.01` 1.04125. Three had unused-position remedies in the
historical report; two had none at their then-current size. The old 0.978
prediction was not a historical pass. The newer 0.978101 is a separately
reviewed **local c6 model** result.

**All 26 historically unplaced ICs**, from `replacement.footprints` with
`step="no position"`:

| Board | References |
| --- | --- |
| JL (6) | `U1216 U1416 U1417 U1518 U2119 U2218` |
| JR (6) | `U4346 U4347 U4348 U8314 U8318 U8417` |
| K (14) | `U1415 U4324 U4417 U4433 U4524 U4526 U4527 U4623 U4635 U5110 U5209 U5210 U8409 U4341` |

These are 25 SOIC-14 and one TSSOP-14 (`K U4341`). The retained search tried
own-face within 12 mm, K opposite-face within 12 mm, then either face within
25 mm, using 0.25 mm rings in 24 directions and cumulative obstacles. Do not
repeat or silently widen that search. DS-88 sends the nonempty list to the
paper gate; verify exact refs against the future integrated record.

**All 31 historically `NOT SHOWN` latch links** from
`threading-procedure.json`:

| Group | Full link IDs |
| --- | --- |
| O-K | `O-K-O3`, `O-K-O5` |
| JL-K | `JL-K-JL-L02`, `JL-K-JL-L03`, `JL-K-JL-L08` |
| JR-K | `JR-K-JR-L01`, `JR-K-JR-L05`, `JR-K-JR-L06`, `JR-K-JR-L07` |
| P-K | `P-K-P-L01.01.01`, `P-K-P-L01.01.02`, `P-K-P-L02.01.01`, `P-K-P-L03.01`, `P-K-P-L06.02`, `P-K-P-L07`, `P-K-P-L08`, `P-K-P-L10.01.02`, `P-K-P-L10.02`, `P-K-P-L11.01.01.01`, `P-K-P-L11.01.01.02`, `P-K-P-L12.01.01.02`, `P-K-P-L12.01.02.02`, `P-K-P-L12.02.01.01`, `P-K-P-L12.02.01.02`, `P-K-P-L13.01.02.01`, `P-K-P-L14.01.01.02`, `P-K-P-L14.01.02.02`, `P-K-P-L15.01.02.02`, `P-K-P-L15.02.01.01` |
| JL-P-K | `JL-P-K-JL-L01`, `JL-P-K-P-L01.01.01.01` |

The full historical JSON also records neighbouring references. `NOT SHOWN`
means access was not established; it is not a physical pass or a demonstrated
failure.

Thermal remains outside the five checks, but the historical ST-05 screen
placed P/pots at 58.5–75.1 °C in a 40 mm closed case at 40 °C ambient, above
the Bourns 50 °C operating maximum. K's 85 °C-rated classes were `NOT SHOWN`
met, and all 101 pot dissipation calculations were `NOT COMPUTED`. DS-108
option A provisionally retains the pots with about 10 mm feet or equivalent
rear clearance, opposite-edge vents and first-article measurement under #64;
thermal compliance is not established. The accepted FFC workload remains as
stated above. The withdrawn connector coupon and Gate A-physical do not
revive. MC-03 / #366 informs later layout/service work but is not itself a
formal Gate A-paper prerequisite.

## Checks and release condition

On the exact local composition `2c53715`, the bounded focused suites passed:
geometry **101/101**, electrical **57/57**, trimmers **13/13**; `pnpm
circuit:check` passed with its stated manual-inventory scope. A regenerated
link-gate JSON compared byte-for-byte with the retained record; electrical and
c6 report `--check` returned `current`, and the trimmer checker passed. The
worktree remained clean. These checks do **not** bind a future integration
head. Aggregate `bash scripts/checks/regen-all.sh --check` is **NOT RUN** here;
that wrapper does not invoke the changed MC-01 link-gate/electrical or MC-03
trimmer generators, so their focused checks remain a separate integration-head
gate. Native KiCad, CI, DRC/fill, physical fit/service and hardware checks are
also **NOT RUN** here.

This expanded packet itself has **not** received independent exact-head
review. The source-only identity checks above verify transcription against
historical artifacts; they do not supply that review or current-head gates.

Before a final MC-02 packet: (1) integrate and independently review MC-01
through Moya's serialized path; (2) rebind each five-check row, all 26 ICs and
31 latch links to that exact revision; (3) complete applicable focused and
aggregate/native checks at the integration
head; (4) independently review this packet at its final exact head; and (5)
send the compact packet to independent confirmed Astra review
under #367. An offline paper ratio, an exit-zero source test, or this draft is
not Gate A approval or canonical-board adoption.
