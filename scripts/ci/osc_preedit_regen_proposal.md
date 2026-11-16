# OSC manual pre-edit regeneration lane: blocked design proposal

Status: **proposal only; no workflow or controller is enabled.** Prepared against
`main` `690366aa69450b642f7daee2cb809eb5ded38d63` for MC-01 / issue #364.
The existing registered workflow is `.github/workflows/osc-candidate-check.yml`.
This note does not admit native execution or change the held board DRC gate.

## Required manual lane

Extend that registered `workflow_dispatch` workflow with a third mode,
`preedit-regen`, and exactly one new job selected only for that mode. Retain the
existing smoke/identity job, its old behavior, and `contents: read`. The new job
must use `ubuntu-24.04`, have `timeout-minutes: 30`, and have no `push`, PR,
schedule, artifact upload, cache, deployment, or secret reference. Source checkout
must use the exact reviewed source commit (initially the main SHA above), with
`persist-credentials: false`. Tooling checkout must use the exact workflow commit
SHA, also without persisted credentials. Pin checkout, Node, Python, and pnpm
setup actions by full SHA; retain the project's `pnpm@11.5.2`, Python dependency
locks, and `scripts/kicad/pin.env` image digest
`sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec`.
Verify the native oracle reports KiCad 10.0.6 before interpreting any output.
Do not use a branch ref as an implicit source pin or fall back to host KiCad.
The action SHAs already used by `check.yml` are checkout
`3d3c42e5aac5ba805825da76410c181273ba90b1`, pnpm setup
`ea17c68df8912ef543352723c149a84f56e3d413`, Node setup
`820762786026740c76f36085b0efc47a31fe5020`, and Python setup
`5fda3b95a4ea91299a34e894583c3862153e4b97`. Review these exact
pins again when the lane is implemented. The existing workflow's registration
on default branch must suffice for branch-ref dispatch; if it does not, stop
instead of registering a new workflow.

After setup, the single job should run, in order, the exact unmodified
`pnpm circuit:check` and `bash scripts/checks/regen-all.sh` against the source
checkout. The latter runs schematic export/ERC, including the two concurrent
board ERC containers. Follow with `pnpm circuit:check` and the applicable
source/project checks only if the bounded attempt still has time. Report exit
status and tracked diff names/status/stat from `git diff` without printing a
binary patch, generated file bodies, private source bytes, or private resource
content. Do not upload logs, receipts, or diffs. A changed tracked diff is a
review item, never an automatic push or an accepted regeneration.

## Aggregate resource gate, before any native command

The required limit is **one job-owned cgroup v2 ancestor** with `cpu.max` equal
to 2 CPU, `memory.max` equal to 4 GiB, and `memory.swap.max` equal to zero. The
regeneration parent and every KiCad container, including the two concurrent ERC
containers, must be descendants of that same ancestor. Per-container Docker
limits or serial Docker calls do not prove the aggregate bound.

A future controller may proceed only when it can read `/proc/self/cgroup`, verify
the `cpu` and `memory` controllers and existing delegation, create only a
job-owned subtree, set and read back all three limits, and move its command
parent into a host leaf. It must verify the parent's actual membership. It must
also verify Docker's cgroup driver and ensure **each** container is placed in a
child of that ancestor, with runtime membership readback before its native
command starts. A probe container is insufficient evidence for later containers.
Use an immutable owner ID tied to the Actions run and attempt; enumerate only
that owner's containers for teardown, confirm their identity, stop/remove them,
move the parent out, and remove only the empty owned cgroup. Any missing
controller, unwritable/delegation failure, driver mismatch, limit mismatch,
unverified membership, orphan, or cleanup uncertainty fails closed. Do not
modify a shared parent, daemon settings, systemd units, security policy, or
network configuration, and do not bypass a denial.

## Blocker at this revision

`scripts/kicad/run.sh` calls `docker run` directly with no cgroup-parent input.
`scripts/schgen/check_board_erc.py` invokes that wrapper from two concurrent
workers. [Docker documents `--cgroup-parent`](https://docs.docker.com/reference/cli/dockerd/#default-cgroup-parent)
as either a per-container option or a daemon default; the systemd driver
requires a slice name. Therefore the
unchanged native path cannot place both ERC containers under a verified job
ancestor through a controller/workflow/test-only edit. A PATH-intercepting Docker
shim or daemon/systemd configuration would become the prohibited control
mechanism or security-sensitive runner change. This runner's cgroup delegation,
Docker driver, and actual membership have not been observed, and CI/native
execution is outside this attempt. Do not add a selectable mode that could
appear safe on that evidence.

Independent review must resolve the narrow implementation boundary first:
either authorize a reviewed, minimal per-container cgroup-parent and membership
gate in the existing KiCad wrapper (while preserving its normal behavior), and
demonstrate pre-native readback on a runner with delegated cgroup v2; or provide
an already registered runner whose existing policy supplies the same aggregate
bound without a new systemd/Docker control mechanism. If neither is available,
retain this stop. No new workflow registration or global runner configuration
change is a fallback.

## Offline negative tests required before dispatch

Pure tests must inject fake cgroup files and Docker observations, with **zero**
native calls, for: absent v2/controllers; no delegation/write permission; CPU,
memory, or swap readback mismatch; host process outside the owned leaf; Docker
driver mismatch; container outside the aggregate ancestor; one of two ERC
containers missing; spoofed owner ID; limit change after startup; timeout;
failed/uncertain owned-container cleanup; and a nonempty cgroup at removal.
Workflow tests must assert dispatch-only mode isolation, one new job, exact
source/tool SHA checkouts, read-only permission, 30-minute ceiling, and no
upload/cache/secret/push/DRC path for the new job. Preserve the existing
smoke/identity tests and artifact behavior for those old modes.

## Verification state

The pre-edit `pnpm circuit:check` passed locally using a temporary PNPM_HOME.
`regen-all.sh`, KiCad, ERC, DRC, CI, and offline controller tests: **NOT RUN**.
No source/kernel/reorder files were changed. No CI, PR, merge, or deployment
is part of this proposal.
