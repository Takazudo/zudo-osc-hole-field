# Epic 242 baseline handoff — epoch e0

Owner: Moya, issue #243, sole integration/canonical-output coordinator. Parent
assigns sessions and native slots. Prior Cloud session is stopped, not waiting
to resume. The new owner request applies only to this epic. No old watch, wave,
merge authorization or unexplained approval card is inherited.

## Immutable inputs and readiness

Refreshed main is `65cefd41fc39e064d38319115ad96016a1c6b71c` (2026-10-11 UTC).
`baseline.json`, `input-files.json` and `harness-contract.json` freeze exact bytes.
Use the integration commit containing this ledger as the worker parent once
published; the source epoch remains e0 because this commit changes no board or
generator. W0 sessions already using the same immutable main need no hardware
rebase; reconcile their touched inputs with this manifest before integration.
Never substitute the moving branch name for an input SHA.

- #245–248: source-ready, assigned sessions/write-sets in `ownership.json`.
- #244, #250, #251: ready for parent assignment from the reviewed source baseline;
  execution still requires their scoped evidence recovery and native admission.
- #249 waits for #248 `LABEL_CONTRACT_READY`; #253 separately needs
  `COMPONENT_REVIEW_READY`, including all 23 identity/envelope gaps.
- #252 waits for reviewed #244 disposition. A blocked audit disposition must be
  formally accepted before the unchanged K can be its comparison baseline.
- #254 shared production-generator work follows the architecture decision and
  remains serialized. No production partition change has been selected here.

Accepted retained exact-board receipts establish JL117/JR129/K1402, 0 DRC/parity,
with fresh-copy agreement in the original runs. This session recomputed published
hashes and receipt bindings, not native connectivity. Older jack `routing.json`
reports are stale and are not current evidence. K published `fa60…` differs from
settled `b9f5…` because of publication cache removal; do not compare interchangeably.
Full per-net obligations are retained in `baseline.json`; full endpoint memberships
and native workspace context digests must be recovered from artifact snapshots
or reconstructed before routing proposals. Null is unknown, not an empty context.

P's zero-edge routed candidate (`7488a643…`) is not its canonical layout
(`a34e150f…`); canonical geometry/adoption remains open. EL and all five octaves
have exact-board-matching retained zero-edge reports. Historical single `osc-jack`
is excluded from the ten active boards. None is a fabrication-ready instrument.

## Recovery and audit transfer

All eleven PRs are still OPEN/DRAFT with refreshed heads/bases and dispositions
in `pr-inventory.json`. Reused PR237's two status corrections, reconciling historical
active-run wording. PR236/238/239/240/241 all carry inherited JR130 bytes: never
bulk merge/cherry-pick their trees over accepted JR129. #244 may submit only reviewed
source patches and exact candidate/evidence deltas. JL rejected PR221/225/226/229/233
remain negative evidence; no unchanged long rerun is admitted.

One Actions inventory of the latest 50 runs found every entry terminal; no
survivor was observed. After wave0 run38101593158/artifact11688551991 and wave1
run38103580685/artifact11689476370 succeeded at execution SHA
`b350905989de9b441aa4ff709a8491d3c753332b`. Both full ZIPs were downloaded through
the GitHub connector and matched fresh GitHub size/digest metadata. Producer
ledger hashes and all 32 new receipt byte seals match. These byte checks are not
the original semantic authentication of all 355 reports: #244 owns that replay.
Owner-reported authenticated coverage is 355/426; after wave2 was never dispatched.
Next potential packets are batches32–39 and40–47, only after #244 reauthenticates
preceding waves and parent admits the native slot. Do not rerun wave0/1.

The original run38044514132 artifact11671963117 is available in GitHub metadata:
713393322 bytes, SHA256
`d02155c0775df089f8ba84310014671436f427dc11b00e94cd551f30e1d6ede5`.
Fresh gh identity/metadata work. Direct ZIP transport returns403, including the
scoped escalation; the connector refuses files over536870912 bytes. Full original
bytes remain a final-gate blocker. No credentials were changed. A subset cannot
replace it. Artifact metadata includes expiry dates; retain full ZIPs before expiry.

Core1312 remains unadopted: 133551 original copper/3807 nonrouting objects retained,
115 additions, zero cuts; complete original warnings/eligibility/publication and
integration gates remain NOT RUN. Capped499 CI items are not full native edges.
The old optional 966643-byte stopped-handoff ZIP and detached 11-blob bundle were
not transferred. `owner-sequence.json` blob3dda9748a834beaca1de834ce5ba9c5d93aaa39f
has no published tree/ref. No final runner was dispatched. Durable PR241 source,
artifacts and this ledger replace any reliance on session-local paths.

Next read-only recovery command for #244:

```sh
git show b350905989de9b441aa4ff709a8491d3c753332b:circuit/routing/issue189/core236-task-checkpoints/AFTER-CONTROLLER-SOURCE-REVIEW.md
```

That document's first-wave command is historical: do not execute it. Recover both
after approvals with original `authenticate_checkpoints`/`reconcile_wave`; reconstruct
five-before and two-after approvals separately. Recheck exact execution head,
manifest, orchestration and terminal metadata. Only then prepare wave2. No new
audit implementation or native execution belongs to #243.

## Exchange and ownership

Existing 195 harnesses/390 endpoint connectors are frozen with both Refs and all
numbered signal/AGND/rail/NC pins, side and pose. All438 panel centers,33 modules,
sensitive node locality, non-core poses and accepted copper stay fixed. New feeds
receive explicit new IDs. Core relocation needs the selected architecture contract.

Every lane result supplies issue/session, parent SHA, epoch, branch/head, owned
paths, source/tool/context hashes, commands/results, artifact IDs/digests/expiry,
negative evidence, unresolved Ref/pad/UUID/group identities and next action. State
which checks are source-only, retained-native or fresh-native. No inferred PASS.

Architecture candidate: option ID; module-to-core mapping; dimensioned outline,
actual courtyards/overlaps/congestion/reservations; harness-contract diff; added
feeds/parts/supports; power/return and service constraints; test evidence and gaps.
Part counts alone do not prove capacity. Disposable native pilots are separate
from canonical adoption and require parent admission.

Label contract: existing Ref, module/function, proposed functional silk, calibration
role, source identity, target board/pose constraints, access and readability limits.
Report LABEL_CONTRACT_READY separately from COMPONENT_REVIEW_READY; no unsupported
circuit/trim addition and no label may conceal an unresolved component identity.

Copper uses existing grid proposal (`board_sha256`, `removed_uuids`, `copper`) or
route-shard (`base_sha256`, `removed`, `added`, `nets`) formats plus exact receipts.
Never rewrite hashes to force a stale proposal. Shared AGND/rail windows are one
coupled ownership domain, not disjoint merely by net/window. One adoption transaction
per board/epoch. Coordinator replays approved copper and regenerates aggregate
conflicts; never hand-merges PCB text. Keep worker PRs open.

Global limit: two native workers,6GiB each,12GiB aggregate,2GiB free, existing
40-minute controller/50-minute job timeguards; parent admission before heavy work.
No native routing/adoption slots were consumed here. Stop after two comparable
negligible runs, at most three unchanged strategy attempts. A changed baseline
requires impact-scoped replay; full joint native gates remain for final integration.

## Verification boundary

Pre-edit `pnpm circuit:check` PASS: manual provider,68 lines,0 declared placements;
no schematic/placement binding; pin-asset check performed. Initial sandbox pnpm
store failure was resolved by scoped escalation. Regeneration was attempted after
hash-preserving all committed boards. Its initial image bootstrap was interrupted
while downloading the pinned oracle; no native result is claimed. Follow-up results
and independent review are recorded in `verification.json` and `review.md`.

Startup instructions arrived through the supplied workspace AGENTS message, not
a demonstrated saved environment startup field. Runtime restoration and personal
loader were each rejected by automatic approval review for prohibited `/root/.codex`
access. No workaround or profile rebuild was used. Repository AGENTS/WORKFLOW and
relevant .claude skills were read; repository .agents/skills is absent. This is an
explicit context-loading limitation, not proof of successful native discovery.

No merge, closure, deployment, fabrication/order, supplier communication or
energization is authorized. #243 is baseline coordination, not completion of #242.
