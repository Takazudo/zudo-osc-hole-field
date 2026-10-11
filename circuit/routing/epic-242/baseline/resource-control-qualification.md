# Resource controls: source wired, operational qualification held

The owner authorized Sol Medium source implementation and inexpensive harmless tests, with no native KiCad jobs or changes to OS security settings/access controls. The implementation agent supplied the worker guard, Docker hook, CI admission gate and extracted unchanged check scripts. The coordinator and separate baseline reviewer reviewed them. No workflow was dispatched, repository admission variables set, native routing started or board output adopted.

## Evidence

- `resource-control-kernel-proof.json` retains the actual local Docker proof: two children requesting 40 MiB each beneath one 64 MiB/no-extra-swap cap caused OOM/exit70; the sleeping parent/child tree was killed after one second, exit137, Running=false/Pid=0. Owned containers/image were removed. The helper builds/imports a tiny static C fixture locally; no network image pull, KiCad or systemd resource changes occurred.
- Fourteen harmless boundary tests cover timeout/OOM/free floor, worker and shared-parent caps, actual hook arguments against fake Docker, local pinned-image authentication, remote/fallback refusal, stale populated workers/headroom, cleanup order, and exact CI admission binding.
- Actual harmless preflight invocations failed closed: worker launcher refused PID1=`tail` before Docker/systemd/slot operations; CI entry refused absent exact run admission before invoking the launcher.
- `pnpm circuit:check`, `pnpm check`, shell syntax, Python tests and diff checks pass. Full native checks/regen/build/CI remain NOT RUN.

Independent review fixed systemd hierarchy encoding (hex single-child slice names), reserved unconsumed worker headroom, and image-pull escape (local exact RepoDigest required and bounded Docker uses `--pull=never`). Each worker has a shared host-command/container 6 GiB slice; an aggregate parent enforces 12 GiB/no swap. Admission serializes startup and counts stale populated slices even after frontend lock release. Containers receive individual 6 GiB caps plus the same parent; independent watchdog, inner absolute timeouts, RuntimeMaxSec and targeted bounded cleanup are source implemented. Parent admission still controls the global two-worker limit across hosts and unrelated lanes.

## Remaining qualification and source epochs

This host uses PID1 tail and Docker cgroupfs. It cannot qualify the required systemd worker/watchdog path. The scaled Docker proof is **not** evidence for whole-worker membership, exact6/12 GiB setup, watchdog death/parent crash or systemd cleanup. CI is deliberately fail closed until the parent chooses a capable runner, reserves global capacity, and qualifies a bounded harmless control pilot there. Do not change this host's security/access settings or silently substitute a weaker control.

`resource-control-epoch.json` explicitly declares tooling epoch `epic242-tools-e1-resourceguard`. The historical1883-file input manifest is retained;1881 original files still match and only README/run.sh receive exact declared tooling replacements. Newly installed tooling is sealed separately. Hardware epoch `epic242-e0`, accepted JL117/JR129/K1402, copper, circuit/harness/pose contracts and original artifact hashes remain unchanged. Historical candidate receipts bound to the old wrapper remain historical; owners must reconcile tool bindings to the pushed integration SHA before any new native execution. Do not rewrite their receipts to imply a fresh run.

#250 resumed repository-only source preparation under the owner's explicit personal-startup waiver for #250 alone. Denied runtime/config paths remain prohibited and no personal-profile discovery is claimed. #252 source-only assignment is session01a129a1-9e0d-71d6-8be9-ed999b474088 at immutable40aa1cec58190487dc70aa5048a366e29a6b32a1. Both lanes may continue source work independently and reconcile before integration/execution.

## Smallest next runnable work

1. Source-only lanes #250/#252 continue now. #244 remains KEEP_K1402 blocked disposition; no wave2 or artifact transport authorization.
2. Parent-selected capable runner: separately admitted bounded harmless whole-worker control pilot, testing two slices/shared parent, membership, deadline, guard death and cleanup/floor receipts. No routing or full suite is needed to qualify controls.
3. After qualification: retain #249's two-face render/reload proof and semantic comparison, then admit one300second/6GiB label fixture. Next is #245's one300second/6GiB complete three-A settle. #251's retained two-cut negative remains preferred unless new topology observation is specifically needed.
