# Exact request for a new owner-approved run002

**PROPOSAL ONLY. No fresh owner approval or live admission has been granted.**
The parent chat will request approval. Do not launch the following commands
under the old run001 authorization.

- Design source: `5469def6cdf2a5f0f9d4a61cec88efbc7ac2130b`.
- Verification implementation: `23bc06ac84147c3ba1e8079e6be5b4eeaf986eb4`.
- Root: `design/architecture-278/implementation/stage17/generated/a01.kicad_sch`.
- Root SHA256: `2d7530895ab55e5b7dd1e41d416f1cb9b295fd716b3b07aa83c83e6dbf195538`.
- Complete61generated/66source bindings: original `stage17/schematic-report.json`.
- Exact scripts and independent review: `review-retention-repair.json` in this
  directory at the verification commit. No design-source changes are proposed.
- Host: existing X0X Ubuntu24.04.4 WSL2, Docker29.3.0, same existing digest
  `kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec`.

## Fresh isolated paths and host argv

After approval, re-read PR286's current head and reconcile it with these exact
design and verification commits. A later documentation-only request commit
does not silently replace either binding. Stop on unexplained drift. Create
this isolated worktree using the existing task checkout, without modifying
other projects:

```sh
git -C /mnt/c/Users/takaz/Documents/Codex/2026-10-16/task-3/osc-validation -c core.autocrlf=false worktree add --detach /mnt/c/Users/takaz/Documents/Codex/2026-10-16/task-3/osc-validation-run002 23bc06ac84147c3ba1e8079e6be5b4eeaf986eb4
```

Exact proposed launcher, within the existing shared heavy guard:

```sh
bash /home/takazudo/.codex/scripts/heavy-guard.sh --max-run 600 --label osc-stage17-x0x-002 -- python3 /mnt/c/Users/takaz/Documents/Codex/2026-10-16/task-3/osc-validation-run002/scripts/architecture278/implementation/stage17_native_host.py --repo /mnt/c/Users/takaz/Documents/Codex/2026-10-16/task-3/osc-validation-run002 --run /mnt/c/Users/takaz/Documents/Codex/2026-10-16/task-3/osc-stage17-x0x-002 --verification-commit 23bc06ac84147c3ba1e8079e6be5b4eeaf986eb4
```

The fresh run directory must not exist beforehand. The launcher binds executing
script bytes to the verification commit, all inputs to the original source,
and writes exact Docker argv. It initially runs Python capability checks only.
Independently review actual cgroups/mounts/network and source/code/argv hashes,
then create a new `admit.json` using the seven exact hashes required by the
container supervisor. Record the owner's new approval and independent review
receipt. No old admission file or old success assertion may be reused.

## Exactly one native opportunity

```sh
kicad-cli version
# Only if stdout is exactly 10.0.6:
kicad-cli sch export netlist --format kicadsexpr -o /output/netlist.net /inputs/a01.kicad_sch
```

One concurrent run,2CPU,4GiB RAM,zero swap,600second whole-container hard
timeout,network disabled,readonly generated inputs and root. Configuration,
cache,tmp and logs share the250MiB tmpfs. One retained stream copy is at most
250MiB; host metadata is at most12MiB. Total remains at most512MiB. No runtime
installation, download, service/permission/credential changes, ERC,DRC,PCB,
simulation,hardware action or automatic retry. Unexpected resource enforcement
or version means stop. Source repair requires another separately bound admission.

The changed conditions are: unique run002 and worktree paths; repaired live
stream retention; exact script-commit binding; explicit command-attempt/status
records; full required-file/size/hash/inventory and native success-semantic
verification before normal cleanup. On retention failure preserve partial
evidence and hold source until hard timeout; do not label success or retry.
Synthetic proof is4files/4194471bytes plus26retention tests, not native proof.

After verified retention, run the source-only comparator from that checkout:

```sh
python3 /mnt/c/Users/takaz/Documents/Codex/2026-10-16/task-3/osc-validation-run002/scripts/architecture278/implementation/stage17_native_parity.py --repo /mnt/c/Users/takaz/Documents/Codex/2026-10-16/task-3/osc-validation-run002 --netlist /mnt/c/Users/takaz/Documents/Codex/2026-10-16/task-3/osc-stage17-x0x-002/retained/netlist.net --output /mnt/c/Users/takaz/Documents/Codex/2026-10-16/task-3/osc-stage17-x0x-002/native-parity.json
```

Compare all118references/561pins/154unit UUIDs, including transport/lands,
unusedLT5400ends,EPgrounds,identity/value/footprints and explicit native NC
omissions. An unsupported native representation fails closed; source-only
parser corrections may be reviewed without repeating native export. Retain
exact limitations and independent result review.19null passive MPNs and
unboundDIN/landfootprints remain unresolved. Logical parity is not electrical
acceptance. PR286 stays draft;285/260/277 parked; canonical geometry,
placements,decision.json andKEEP_K1402_INCUMBENT unchanged.
