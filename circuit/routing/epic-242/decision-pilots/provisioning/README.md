# Trusted CI preparation correction

Admission1347's unused reservation is released by parent instruction; see
`reservation-release.json`. Its capability refusal and complete logs remain
unchanged atc4a4e824. No routing outcome was measured.

The refusal exposed two orchestration mistakes: the preflight required the
developer HOME heavy-guard on an isolated GitHub-hosted runner despite the
repository's existing hosted-runner dispatch policy, and it inspected the
KiCad image before the existing preparation step had pulled it. These are
recoverable provisioning omissions, not native routing failures.

## Recovered trusted sources

`trusted-source-recovery.json` independently authenticates complete ZIPs from
successful two-A run38133584276/artifact11699982799 and two-B
run38135093123/artifact11700304065, including CRCs, exact source commits, image
receipts, actual guard argv and final workload absence. Their sources are
59d032e3 and65d44bc5 respectively. Both used native guard SHA256
`ee755233af405e60cf592956dcf42ca1069f5face6c20c1cdfcdf6f8479ef8ca`, identical
to frozen method29140d4e. Both pulled the official image
`kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec`
and authenticated local image ID
`sha256:1398ad98bb7f066ff8b445e2be96131f0f461a7765ff0078a0b207461b705f51`.

No historical HOME guard installation was found or inferred. The existing
`scripts/pcbgen/with_route_guard.sh`, introduced inda0d51cb and present unchanged
in accepted main and method29140d4e, has SHA256
`29afbe134f0a3c196ab01482382f3042ac32ce5c825ea0728eb416c536ff383e`.
Only `GITHUB_ACTIONS=true` AND `RUNNER_ENVIRONMENT=github-hosted` selects direct
dispatch; local/shared/self-hosted paths retain the HOME machine-wide queue.
Direct dispatch still calls the mandatory native guard. It is not an alternative
to the6GiB/no-swap worker,12GiB aggregate,2GiB free floor, deadline/watchdog,
container handshake or cleanup controls. No new guard is installed or invented.

The unchanged `settle_only_pilot.prepare_image` helper in method29140d4e is
SHA256 `8bf1e311e08554501e33e099cff164b69704f81df0aabe91cd980fd5fd98b531`.
It uses the pinned `pin.env`, pulls by digest, checks exact RepoDigest, observes
disjoint Docker/containerd service memory and aborts at the existing thresholds
and300s preparation deadline. Those daemon observations are sampled abort
thresholds, **not kernel hard caps on the existing Docker daemon**. The helper
does not reconfigure services. On failure it retains image/log/client evidence
and refuses native start; stopping a pull client does not prove the daemon has
ceased all backend work. This limitation remains explicit.

## Smallest source change

`../provision_host.py` validates14 exact method/input hashes (the original12 plus
the existing dispatch/image-preparation helpers), binds real `sys.executable`
and numpy2.2.6/scipy1.15.3/shapely2.1.2, verifies hosted/systemd/local-Docker
capabilities and invokes only the unchanged image preparer. It emits future
O1/K1402 argv but has **no route execution branch**. It leaves the29140d4e
checkout clean and does not edit any frozen method or hardware bytes.

`../provision-host.workflow.yml` is an isolated development workflow template:
two checkouts, pinned existing checkout/setup/upload actions, Python3.11 as in
the successful runs, existing numerical-requirements install bounded180s,
provisioning helper, and always-retained positive/negative evidence. Existing
43min enclosing job cap includes setup. Image preparation's300s cap is separate
from the future route's unchanged300s including both Docker probes. No KiCad
version probe/container, fixture, routing, apply, settle, fresh copy or audit runs
in this provisioning job. No automatic retry is present.

The request packet replaces nonportable `/tmp` Python arguments with an actual
execution-host binding, uses the existing dispatch wrapper, and requires a new
native-evidence **JSON file**. The prior request/refusal remains in Git history.

## Evidence needed for renewed admission

1. Inspect provisioning receipt, exact image digest/ID, numerical versions,
  14 matched source hashes, source cleanliness, actual host capabilities,
  image-preparation accounting and successful pull-client exit. A successful
  ephemeral provisioning job is evidence for the recipe; its image does not
  persist onto a future fresh runner. Repeat provisioning on the execution host.
2. Parent supplies a new admission ID and worker reservation under unchanged
  global limits. Released1347 cannot be reused. Recheck actual free capacity.
3. Authenticate all six complete ZIPs, prepare a new exact O1/K1402 private
  fixture, verify lock/before hashes, and replace plan placeholders. These steps
  are not claimed by the provisioning-only job.
4. Execute only the unchanged guarded300s route if newly admitted. Retain both
  gated Docker memberships and successful exits, immutable before hashes,
  proposal/diagnostics/logs, and resource/cleanup receipt even on failure.
  Zero additions means NO IMPROVEMENT. No retry/cuts/wider bounds/fallback.
5. Two-A/apply/settle/fresh/audit remain separately unadmitted. No canonical
  adoption, merge, closure, fabrication or energization follows.

Source checks include exact guard `--plan` parsing (no worker starts), payload
and cap preservation, new-file/fixture refusal cases, the repository's existing
hosted/local dispatch tests and independent review. Actual runtime hard-limit
enforcement is inherited historical evidence until a newly admitted execution
records it again; provisioning alone does not prove new native membership.

## Provisioning-only measured result

[Run38146298766](https://github.com/Takazudo/zudo-osc-hole-field/actions/runs/38146298766)
passed on orchestration84339974f72e77f6bcf4e0edb72eb5b6b7356005, source driver
59b0c2c21ccf2ded58cd2031e4a4289d546feca3, immutable method29140d4e.
Actual Python was `/opt/hostedtoolcache/Python/3.11.17/x64/bin/python`, with
numpy2.2.6/scipy1.15.3/shapely2.1.2. All14 method hashes matched before and after;
the checkout remained tracked-clean. Hosted dispatch, systemd PID1, cgroupv2
memory, sudo and local Docker memory/swap capability checks passed. The official
image digest/ID above were authenticated after successful pull-client exit0.

The101 preparation samples recorded minimum available memory15,282,429,952bytes
and maximum combined backend use3,128,696,832bytes. Those are sampled observations,
not a new native hard-limit qualification. **No native worker, KiCad probe or
container was started. No fixture/route/apply/settle/fresh/audit ran.**

[Artifact11705061761](https://github.com/Takazudo/zudo-osc-hole-field/actions/runs/38146298766/artifacts/11705061761)
is10,371bytes, SHA256
`d9e24a42e4d173cf56f7fc7f5e2eaead8a8677c7d0636ab3774718185e109fea`.
The downloaded full ZIP passed local SHA/size/CRC and all7 member hashes.
`host.json`, `image-preparation.json`, bootstrap/job outcome are exact artifact
members. Complete artifact logs are losslessly stored as strings in
`provision-logs.json`; complete decoded Actions log is `actions-log.json`.
`verification.json` records checks and provenance. This proves the preparation
recipe works, not persistent host readiness or renewed native admission.
