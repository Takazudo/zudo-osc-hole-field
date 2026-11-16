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
| Existing MC-02 extraction | Task `6afac5fc-b834-8191-b0a2-d6f9c613d03a`, completed read-only on `690366aa69450b642f7daee2cb809eb5ded38d63` per Moya. **Its exact findings/receipt are not present in this worktree; import them from that owner, not a second extraction.** |
| Final packet source | **PENDING** reviewed *integrated* MC-01 revision and exact rebind from both the MC-01 candidate and the existing MC-02 extraction. The local composition above is not that revision. |

The bounded MC-01 source review found no blocking code defect in the paper
model. Its retained c6 report preserves 61 placed links and 511 signal
identities, with 340 ground and 321 unused positions. The model reports zero
link ratios above 1.0; its maximum is **0.978101** on `P-K-P-L03.01`. These are
calculated cable/ground-coupling bounds, not measured harness performance. The
P all-posts-open current bound is `0.0997772 A` in `link-ratios.json`, subject
to the retained model assumptions. Neither figure decides the other four
Gate A-paper checks.

## Five-check handoff slots

| Check | Candidate facts now bound | Existing extraction / final rebind needed | Status |
| --- | --- | --- | --- |
| 1. Connector and cable identity | MC-01 link count and source identities above | Import the owned extraction's exact complete MPN, supplier/order code, counts, thickness, land-pattern and provenance findings. Keep FH12 opening height, side and contact-1 assumptions labelled by their retained source. | PENDING extraction receipt and integrated revision |
| 2. Opening, locking and access | No new physical access conclusion from MC-01 | Import owned extraction's 31 `NOT SHOWN` latch reaches, 12 supporting-hand operations, maximum 17-end threading stage, neighbour heights, fold, nut/washer and insertion/service-count qualifications with exact evidence. | PENDING extraction receipt and physical assumptions |
| 3. Allocation and current | 511 signals, 340 grounds, 321 unused; modelled P all-posts-open bound `0.0997772 A` | Rebind every final allocation and current result to integrated MC-01 source. Verify the 26 unplaced IC references and retained search limits from the existing extraction; do not silently rerun or widen the 25 mm search. | CANDIDATE model only; final rebind pending |
| 4. Coupling | All 61 link records, maximum model ratio `0.978101`, none above 1.0, sourced by the hashes above | Rebind full class-pair table and the independent c6 review to integrated MC-01; retain source/native verification and unknown measured harness behaviour. | CANDIDATE paper result only |
| 5. Cumulative rework | MC-03 has a separate 104-adjustment *candidate*, not a Gate A-paper input | Import owned extraction's cumulative displaced-function counts and the 26 unplaced ICs; distinguish courtyard room from real timing, precision, summing, route and service effects (DS-97). | PENDING extraction receipt and actual layout |

The accepted FFC workload and thermal choice are to be carried from the
existing decision record without weakening these five checks. Thermal is
outside the five gate criteria; first-article obligation #64 remains. The
withdrawn connector coupon and Gate A-physical do not revive. MC-03 / #366
informs later layout/service work but is not itself a formal Gate A-paper
prerequisite.

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

Before a final MC-02 packet: (1) obtain the completed extraction owner's exact
receipt; (2) integrate and independently review MC-01 through Moya's serialized
path; (3) rebind each five-check row and all 26 ICs to that exact revision; (4)
complete applicable focused and aggregate/native checks at the integration
head; and (5) send the compact packet to independent confirmed Astra review
under #367. An offline paper ratio, an exit-zero source test, or this draft is
not Gate A approval or canonical-board adoption.
