# Stage19 — reviewed supervisor proposal for Stage18 XML

This source-only checkpoint supersedes Stage18's supervisor-preparation gap. It
preserves Stage17 RUN002 raw receipts and full-parity FAIL. No container, KiCad
command, version probe, simulation, or hardware operation was run to prepare it.
The Stage18 source implementation remains `91403f4d78b72757187d8cfdbb4d2dc436a3cf72`.
The published `native-request.json` identifies the exact supervisor verification
commit and every input/runtime/source hash. A later documentation commit publishes
that request without changing its bound implementation. Use a separate checkout
at the verification commit for a future run; do not substitute the branch tip.

## Future launch contract

Prefer Codex Cloud. Use X0X Linux/WSL only if Cloud cannot prove the required
existing runtime. Neither host is admitted by historical receipts. No install or
image pull is authorized. The digest-pinned image must already exist. The retained
RUN002 controls are Linux/WSL portable, but actual uid, mounts, cgroup and Docker
inspection must pass again. Unsupported controls fail closed before native work.

The host entry point is `stage19_host.py`. Invoke it through the existing shared
heavy guard with `--repo`, `--run`, `--request`, and `--owner-approval`; the immutable
request supplies the exact argument template. Resolve host paths in fresh owner
approval. The run basename is `osc-stage18-native-001`; its directory and container
name must be absent. Owner approval binds the request SHA256, source and verifier
commits, absolute run path, one export, identity, evidence reference and a lifetime
of at most 24 hours. The host generates a fresh 256-bit nonce. It never authors
approval or live admission on anyone's behalf.

The container is an inert capability supervisor until admission. An independent
reviewer must inspect `proposal.json`, `docker-argv.json`, `docker-inspect.json`,
`capability.json`, `input-binding.json`, approved request and runtime bytes. Publish
`live-review.json` then `admit.json` atomically into the host run directory. Both
bind the nonce, run ID, commits, request digest and a lifetime of at most 300s;
admission hashes exactly the files named by `admission_reviewed_files` in the
request. Review declares independence and binds both actual capability proof
hashes. Consumed/old admissions cannot be reused. The container exclusively writes
`consumed.json` before the first native process. A lost response, timeout, bad
version or failed export consumes the opportunity; there is no retry.

Only these native argv are permitted, in order:

```
kicad-cli version
kicad-cli sch export netlist --format kicadxml -o /output/netlist.xml /inputs/stage18/generated/a01.kicad_sch
```

Cleanup targets only a full inspected container ID with this run’s random nonce
label. An existing name is rejected before launch; a lost response never authorizes
stopping a foreign container.

Version stdout must equal `10.0.6` after whitespace stripping. The inputs are
exactly 61 Stage17 generated assets and 11 Stage18 generated files in separate
read-only mounts. No whole-repository mount is used. Annotation exclusion flags
remain unchanged; generic XML export uses no extra options. There is no ERC, DRC,
PCB export, simulation or hardware command.

## Limits and evidence

Two CPUs, 4GiB memory, zero swap, 128 PIDs, no network, read-only root/control/input
mounts, non-root identity and no other writable paths must be proved. The writable
budget is 250MiB live tmpfs + 250MiB retained bytes + 12MiB host metadata = 512MiB.
The metadata directory is private trusted control state; independent reviewers
must keep their JSON files below 1MiB and within its 12MiB budget. Logs stream into
the bounded tmpfs; host subprocess stdout and retention streams are byte bounded.

The independent container timeout is 600s. Admission ends at 300s; native processes
have a shared 500s deadline; completion polling stops at 520s; retention must end
by 580s. Timers start at container/launch respectively; host preparation precedes
launch and executes no native code. Resource shutdown remains mandatory if evidence
is incomplete. A failed copy leaves partial host evidence and the stopped container
record; the host never removes an unverified container. Stopping a container can
lose tmpfs contents, so such failures remain UNKNOWN unless durable receipts prove
more. Do not retry or claim successful retention from a container record alone.

Retention reuses the tested RUN002 byte transport with isolated Python scanners,
exact pre/post inventories, byte quotas, per-file hashes, fsync and atomic directory
publication. A separate disk/hash/receipt pass validates command order/count,
version gate, exits, resource logs, quiescent completion, consumed run/proof bindings, and successful XML root
and exporter version. XML declarations are rejected; depth64/100,000-element limits
and removal of completed elements bound the receipt parser. Only verified receipts
permit removal. Complete failed-run
receipts may be retained and cleaned up but remain failures, never parity PASS.
Run `stage18_observation.py` on the retained XML afterward to assess logical parity.
The runner does not claim the XML's logical content passed that comparator.

## Source validation

Run `python3 -m unittest discover -s scripts/architecture278/implementation -p
 'test_stage19*.py'`, existing Stage15–18 and schgen tests, the integrated source
guard, `stage18_compat.py --check`, `stage19_request.py --check`, `pnpm circuit:check`
and `pnpm check`. All new tests use synthetic files, injected subprocess responses
or local Python byte streams; they never invoke Docker or KiCad. Existing historical
files and `check_source.py` remain unchanged; the Stage19 request check is additional.

118 references, 561 pins and 154 unit UUIDs remain the logical parity contract.
The 19 unresolved passive MPNs and unbound DIN/land footprints remain procurement
and PCB blockers. KEEP_K1402_INCUMBENT, decision.json, boards, locked placements,
and parked PRs260/277/285 stay untouched. PR286 stays draft/unmerged. This checkpoint
makes no electrical acceptance claim.
