# Selective-annulus source implementation and engineering handoff

Implemented source capability, fail-closed native reporting and a quantified resistance intervention on `topic/e16-selective-annulus`, based on integration `5af0e7b675123b40367078ee605a1355bae49a62`. [Draft topic PR274](https://github.com/Takazudo/zudo-osc-hole-field/pull/274) targets `integration/epic-242-core-routing`. The integration owner must incorporate reviewed commits with provenance; this session did not write the integration branch or merge any PR. All hardware remains an unvalidated draft. KEEP_K1402_INCUMBENT.

## Delivered and proven scope

- Source commit `f30c0bf0`: strict policy for AGND via `1e1b90ef-f82d-5e94-a82e-416153b33ef3`, In3.Cu only. Its center (110.245,184.97) mm, 0.3 mm drill, six-layer physical barrel, 0.6 mm other lands, original identity/net and U2314.10 obligation remain fixed. Full original-object and computed contact bindings refuse changed inputs, unknown identities/layers, functional/tangent contacts and supplemental unreviewed copper. JSON reload and repeated application preserve the policy. Clipping, graph and finite fragments understand the foil projection; dependency seals include the new helper.
- Source commit `2f42f386`: existing native reporting separates command execution, connectivity reconciliation, findings completeness, native acceptance and adoption. Saturated 199/499 categories, truncation, omitted scope/categories, ignored rules and disagreement with the same-board native open-edge census block acceptance. Pad counts are never compared to open-edge counts. Retained reports remain INCOMPLETE; the unchanged capped command cannot establish exhaustive findings.
- Source commit `b27391dea630ef60a5613608bcbb6b25458a0d8d`: tiny native negative-control fixture and narrow existing-admission-lane support. One fixed `annulus-fixture`/`annulus` operation, 60 seconds, unchanged native guard/limits and separate operator approval. No arbitrary command or production board target was added.

The exact component is Texas Instruments OPA4196IDR, SOIC-14, LCSC C2057385: missing U2314.11 and co-target C2342.1 are -12V. C2342's retained Murata GRM188R71H104KA93D source remains unavailable; no component qualification is inferred.

[Original AGND inspection](original-agnd-contact-review.json) verifies the exact retained source/caps/planes/graph: 798 other AGND In3 objects, zero annulus contacts, nearest gap 5.5306174122 mm. Via and U2314.10 retain their original fed AGND component in that evidence. This is a read-only original-source result, not a changed-board graph or native proof.

The model retains the 0.025 mm radial barrel wall on In3, giving a 0.35 mm outer envelope. The historical 0.813 mm local screen cannot transfer: the corresponding simple barrel-preserving estimate is 0.788 mm, only 0.038 mm above the unchanged 0.750 mm corridor requirement. No fresh production clipping was performed.

## Native representation blocker and disposable candidate disposition

Pinned KiCad 10.0.6 primary source has no established durable exact per-layer no-flash setting. Global unused-annulus removal would broaden the change; zone-layer overrides are recomputed during refill. A custom 0.35 mm In3 diameter remains a flashed residual land and is **not accepted as the requested removal**. The production serializer explicitly raises `UNSUPPORTED_NATIVE_SELECTIVE_ANNULUS`. See [representation research and concrete alternative](representation-research.md).

The prepared tiny fixture compares a default via with that custom-diameter **negative control**, preserving UUIDs, drill/span, other lands, three functional tracks and owner artwork through load/save/reload. Even a future successful characterization would not prove true selective removal, settled refill, DRC acceptance, process qualification or the KA repair. A 0.025 mm residual land must be assessed against unchanged annular-width rules; no exclusion or relaxed limit is proposed.

**Production geometry changes: zero.** No disposable KA repair was generated, no finite coverage rebuilt, and no changed-geometry solver run occurred. The exact representation/native gate and separate geometry/numerical authority remain missing. Later candidate requests cannot be honestly sealed until a permitted representation and actual candidate inputs exist. The conditional 196→194 and 151→152 improvements are not measured results.

Recorded baseline remains KA196 / KB486, separate KB-P1 480 and distinct prior KA long-B194. Service remains 151 supported / 59 partial / 21 unserved / 194 unmapped, 302 eligible supply pads. U2314's existing ±0.56 mA pair was not injected. The eventual variant must demonstrate full-package coverage before including either supply and reevaluate ±12V/AGND, plus +5V unless exact unchanged-operator/current evidence is independently accepted.

## Resistance decision

[Ranked engineering report](resistance-analysis.md), [per-pad CSV](resistance-loaded-ranking.csv), and [quantitative evidence](resistance-analysis.json) cover 1,536 loaded observations, 302 unique pads and 28 verified input indices. Every retained loaded observation exceeds its applicable fixed allowance. Worst loaded example: KB U4330.14, +5V, sensitivity-thin, **28.872 mΩ / 1 mΩ**. Driving-point resistance, simultaneous-load voltage, local-ground error and complete-path acceptance remain distinct.

Prioritize a separately scoped TP990026 +12V transfer experiment. Its F.Cu group has one functional F-to-In4 barrel: existing via `87d2de81-b7e7-5e5c-9063-52b28f51939e` at (142,175) mm. The exact proposed extra 0.6/0.3 mm via at (141,175) mm could ideally halve its local barrel term from **1.405→0.703 mΩ nominal**, but **2.891→1.445 mΩ thin** still exceeds the global rail allowance. Whole-network improvement, current division and new antipad effects remain unmeasured; a bounded object-energy diagnostic and fresh geometry/finite/native comparison require separate admission. Neither the seven-via hypothesis nor KA long-B's 34.732 mΩ strip screen is an established resistance remedy.

No allowance is restarted per board, no load is reduced and no omitted conductor is assigned zero cost. Physical source/protection, all 380 GH conductors, unsupported/dynamic/output loads, full source/load/return paths, complete DRC enumeration and physical/bench qualification remain open. The report ranks these gaps without inventing package mappings.

## Tests, review and preservation

- Existing source-only suite: **1,798 PASS**, with the two exact oracle discovery exclusions unchanged. Seven new fixture tests added after its E16 discovery were then covered by the final **239-test E16 rerun, PASS**.
- Independent main-source/DRC review: **47 tests PASS**. An oblique-tangent audit defect was reproduced, corrected and regression-tested.
- Independent fixture/admission review: **27 + 7 tests PASS**; unavailable native APIs fail explicitly and non-via geometry is included in round-trip assertions. These are synthetic tests, not native acceptance.
- `pnpm circuit:check`, `pnpm check`, guarded 301-page documentation build and strict site checks: **PASS**. Existing one-entry link allowlist unchanged. Manual inventory scope: 68 lines, no schematic/placement binding; pin-asset check performed.
- Full regeneration: **NOT RUN**, because it invokes native operations outside this exact fixture request. Retained-artifact integration and seven optional local source-byte cache checks are **NOT RUN** as detailed in the logs. No source-only substitute is claimed equivalent to full regeneration.
- CI: **SKIPPED/NOT RUN**, intentionally using `[skip ci]` to avoid unadmitted PR native scheduling. Mac browser: **NOT RUN**, all 19 tested input bindings unchanged; no WSL replacement claim.

See [check summary](checks/summary.json), [source review](review-source.md), [resistance review](review-resistance.md), [fixture review](review-native-fixture.md), and [exact request review](review-native-request.md). [Preservation audit](preservation.json) matches 539 protected topic files and all 550 original execution files; the 11 topic-absent files are untracked KiCad UI state retained in the original checkout. Canonical boards, accepted copper, 438 panel centers, 33 modules, harness/circuit intent, factory-complete soldering obligations and decision.json are unchanged.

All 135 original attempt-5 pickles match their exact indexed sizes/SHA-256: **844,803,369 bytes** at `/home/takazudo/.cache/zudo-e16-runs/coupled-approved-852ffac-8262c033`. [Recovery verification](recovery.json) binds the original campaign index; preserve its relative directory structure and reverify every indexed hash when transferring. No Git LFS or large PCB/pickle commit was introduced. Attempt 5's 147 numerical checks and 148 serialized units remain historical exact-input results, with only **0.28005%** minimum energy headroom. Do not transfer PASS to this changed source, geometry or platform.

## Consolidated next admission request

The only next request prepared here is the tiny native characterization, **not** the production repair or another numerical campaign:

- Exact request SHA-256: `f8da55c709fa59ba3221806f1c10cc4d25462fe8bf9d8c50acf313b0d3fdf4e3`.
- [Retained request bytes](native-request.json); [independent binding review](review-native-request.md).
- Frozen clean execution checkout: `/home/takazudo/repos/circuits/zudo-osc-hole-field/worktrees/e16-annulus-fixture-ad8f3b1a`, source `b27391dea630ef60a5613608bcbb6b25458a0d8d`.
- Request path within that checkout: `.circuit-cache/annulus-fixture-ad8f3b1a/request.json`.
- Run `ad8f3b1a33ef4b5eaf638b183708ef64`, attempt 1; eight input bindings plus the installed shared-heavy-guard hash.
- Output: `.circuit-cache/annulus-fixture-ad8f3b1a/guard.json.annulus`; guard receipt `.circuit-cache/annulus-fixture-ad8f3b1a/guard.json`.
- Exact operation: one load/save/reload negative control, at most 60 seconds after guard entry. Native 6 GiB worker / 12 GiB aggregate, zero swap, 8 GiB launch floor, one separately reserved global slot; startup handshake and producer-first cleanup remain mandatory.

**Missing:** genuine separate operator approval of this digest, actual exclusive native reservation and applicable qualification attestation. The user's implementation instruction and baseline-only numerical authority are not such approval. No personal digest review is claimed. `scripts/kicad/README.md` and `local_native_admission.py approve` require those attestations; no approval file was manufactured.

After that separate approval creates `.circuit-cache/annulus-fixture-ad8f3b1a/approval.json`, the exact next execution command, from the frozen checkout, is:

```sh
python3 scripts/kicad/local_native_admission.py execute \
  --request .circuit-cache/annulus-fixture-ad8f3b1a/request.json \
  --approval .circuit-cache/annulus-fixture-ad8f3b1a/approval.json
```

Do not invoke it before admission, change the frozen checkout, reuse consumed identities or hold an outer heavy slot. Failure is terminal for this identity. The prepared request uses the existing preconfigured noninteractive authentication path; if that context is unsuitable, prepare and review a new request rather than changing its bound mode.

No native/production numerical scope, lock or claim was created by this task. Campaign consumption remains **2/3 full baselines and 8/24 diagnostics**. The original terminal campaign and all negative evidence are preserved. PR260 remains draft/unmerged, issue253 open; neither architecture adoption nor physical qualification is claimed.
