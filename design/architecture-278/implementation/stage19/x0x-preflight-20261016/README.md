# X0X Stage19 exact-run preparation — NOT APPROVED / NOT ADMITTED / NOT RUN

The owner requested X0X continuation with one OSC execution session. No parallel OSC agent/session was started. Cloud remains idle and its separate environment was not accessed or modified. Historical RUN002 remains FAIL.

## Binding

- Publication inspected: b9b3d0f4d7c1a7d4e8b0eb39cd4ac342ffeff09c, PR286 draft/unmerged.
- Source implementation: 91403f4d78b72757187d8cfdbb4d2dc436a3cf72.
- Exact verifier checkout: /mnt/c/Users/takaz/Documents/Codex/2026-10-16/task-3/osc-stage19-verifier at a57e02f6bfd770e55ebf448bc067e79fc6b08eb5.
- Published request copied without modification: native-request.json, SHA256 a5ea1b6814adabd66b326773f92089ac2bdd35a054d3b0e9d1edde61d20e25d1.
- Exact new output path: /home/takazudo/osc-stage18-native-001 (absent at preflight).
- No old approval, admission, nonce, capability receipt or RUN002 result is reused.

## Exact proposed host invocation (DO NOT execute before fresh approval)

Run inside X0X Ubuntu WSL, as takazudo:

```sh
bash /home/takazudo/.codex/scripts/heavy-guard.sh -- python3 /mnt/c/Users/takaz/Documents/Codex/2026-10-16/task-3/osc-stage19-verifier/scripts/architecture278/implementation/stage19_host.py --repo /mnt/c/Users/takaz/Documents/Codex/2026-10-16/task-3/osc-stage19-verifier --run /home/takazudo/osc-stage18-native-001 --request /mnt/c/Users/takaz/Documents/Codex/2026-10-16/task-3/osc-stage19-preflight/native-request.json --owner-approval /mnt/c/Users/takaz/Documents/Codex/2026-10-16/task-3/osc-stage19-preflight/owner-approval.json
```

The owner-approval.json above intentionally does not exist. owner-approval.template.json is invalid/unapproved scaffolding, never a receipt. All paths must be rechecked immediately before launch, as must request hash, pristine checkout and absent container/run name. No shell script automatically launches anything.

Only native argv, after new live admission:

```text
kicad-cli version
kicad-cli sch export netlist --format kicadxml -o /output/netlist.xml /inputs/stage18/generated/a01.kicad_sch
```

The version must be exactly10.0.6. The first version process consumes the single opportunity; failed/missing results never retry. Post-retention logical comparison uses the immutable request's Stage18 comparator argv.

## Host feasibility and enforcement boundary

X0X existing Ubuntu24.04.4 WSL2 Docker29.3.0 uses overlayfs, cgroupv2/systemd. Exact linux/amd64 pinned image is already present; no download or installation required. Disk and memory byte observations are in linux-host.json/windows-host.json. At initial inspection Windows C had about449GiB free and WSL about338GiB; no running Docker containers or KiCad/OSC native processes observed. Windows KiCad was not located in standard Program Files, local Programs, PATH or HKLM/HKCU uninstall records; portable/nonstandard paths were not exhaustively searched and no Windows binary was invoked. Windows native execution cannot satisfy this unchanged Linux/container request; a separate reviewed adaptation would be required to choose it. It is unnecessary for the present proposal.

The existing shared guard's SHA256 is074a463dd6b3a65b7e2168df95b200c0192c414862375bcfb95f979c34c67ee7. Default one slot must remain shared; no environment override or bypass. The host rechecks a held slot and more than4GiB available memory. The proposed output parent /home/takazudo already has mode0750 and trusted owner; no permission change made. The Windows workspace has broader sandbox ACL access, so it is not proposed as live private metadata storage.

The exact docker-argv-proposal.json resolves input paths; only the fresh nonce remains intentionally unresolved. It requests read-only Stage17/18 input mounts and root/control, networknone, nonroot image identity,2CPU,4GiB/no swap,128PIDs,no privileges,250MiB tmpfs for all writable output/config/cache/tmp,600s independent timeout. Total output budget:250MiB live+250MiB retained+12MiB trusted metadata=512MiB. Docker daemon capability flags support these mechanisms. **Actual new-container enforcement is NOT YET PROVEN.** No container was launched; historical RUN002 cgroup receipts cannot admit this run.

## Fresh authorization and genuine independent admission required

Before launch, the owner must approve this exact request/source/verifier/run path for one opportunity, with approved_by, authentic approval_reference and issued/expires times at most24hours apart. The latest instruction authorizes preparation, not native execution. After authorized launch, the inert supervisor generates a fresh nonce and actual Docker/cgroup/mount/network proofs. A genuinely independent reviewer must inspect those exact bytes and publish live-review.json then admit.json atomically within300seconds, binding all13 reviewed files (exact inventory in native-request.json), request digest, commits, run ID/nonce, capability and Docker-inspection hashes. Each reviewer JSON must remain below1MiB within12MiB metadata budget.

No live independent review exists yet; the preparer must not claim independence or sign someone else's review. The retained Cloud source review covers implementation only. Under the one-session/no-parallel-agent constraint, arrange an independent human review or an explicitly authorized handoff before starting the waiting supervisor; do not silently spawn a second OSC agent. No launch until that admission process is viable. Any failed capability or expired review stops before native work; there is no automatic retry.

All CAD remains an unvalidated draft. No ERC/DRC/PCB/routing/simulation/hardware action.19passiveMPNs and DIN/land footprints remain unresolved. Canonical boards,locked placements,decision.json andKEEP_K1402_INCUMBENT remain unchanged. PR286 draft/unmerged; parkedPRs unchanged. Repository aggregate regeneration is NOT RUN because it invokes native operations outside this preparation scope. Required pnpm checks are NOT RUN if the existing shell/package dependencies are unavailable; no installation is authorized.

## Reconciliation and check evidence

The current PR head exactly matched the supplied b9b3d0f checkpoint, so the clean existing source branch was fast-forwarded; no newer matching work was overwritten. The separate verifier checkout remains detached at a57e02f. Published request reproduction and every bound byte passed:72generated inputs,155verification files,5runtime files. The owner's explicit X0X direction supersedes the older document's Cloud-first preference; Linux/container controls and all hashes are unchanged, so no Windows-native adaptation is proposed. This package records preflight evidence and resolved paths, not a changed immutable request.

See checks.json and check-*.stdout/stderr for actual source test outcomes. The pnpm circuit:check attempt reported `pnpm: command not found`; package installation was not attempted. No aggregate/native regeneration, container launch or KiCad version probe occurred. Existing daemon/image discovery is read-only. Actual enforcement and independent live admission remain pending even when all source checks pass.

Exact post-retention source-only comparator command, from the immutable verifier checkout (only after durable XML retention):

```sh
cd /mnt/c/Users/takaz/Documents/Codex/2026-10-16/task-3/osc-stage19-verifier
python3 scripts/architecture278/implementation/stage18_observation.py --netlist /home/takazudo/osc-stage18-native-001/retained/netlist.xml --output /home/takazudo/osc-stage18-native-001/xml-parity.json
```

This comparator was not invoked against a new native output because none exists. Full118references/561pins/154unitUUIDs remain required; no omission waiver or electrical acceptance.

Checks completed: Stage19 synthetic34/34 normal and34/34 optimized; Stage18 source/parser55/55; Stage18 exact compatibility regeneration --check PASS. Request reconstruction and source/runtime/input hashes PASS. These are preparer-run source tests, not independent review or native evidence. No source implementation changed, so broader historical suites were not repeated. pnpm checks remain NOT RUN (unavailable existing command).
