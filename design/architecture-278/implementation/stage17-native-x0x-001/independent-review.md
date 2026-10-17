# Independent review: bounded Stage17 native validation

Reviewer: delegated independent reviewer, separate from host-runner author.
Source commit: `5469def6cdf2a5f0f9d4a61cec88efbc7ac2130b`.

Read root AGENTS.md, circuit/WORKFLOW.md, project brief/next actions,
STAGE17.md, schematic-report.json and Stage17 source parity implementation.
The owner's exact bounded authorization supersedes the historical Stage17
prohibition on native operations. Historical source artifacts must stay frozen.

The reviewer authored `native_parity.py` and `test_native_parity.py` outside
the repository. These parse native observations against frozen Stage16 inputs
and Stage17's independent transport reconstruction, without importing the
schematic emitter. Source hierarchy parity is checked first. The comparator
requires all 118 references, 561 physical pins and 154 unit UUIDs; exact value,
MPN, manufacturer, footprint and symbol identities; native library pin coverage;
and exact named net assignments. Source NC pins may be absent from native nets
only while retained in the native library pin roster, or appear on singleton
`unconnected-*` nets. Source-land omission produces explicit failure rather
than a silent waiver. Source-land population flags are required when exported.

Twelve synthetic mutation tests passed using existing WSL Python. The fixtures
are comparator tests, not native evidence. They cover source-land omission,
wrong net, duplicate/missing endpoints, missing NC library pin, missing unit,
wrong MPN/footprint, NC short, singleton NC and missing population flags.

Admission script review requested fixes for stale admission reuse, full input
rehashing, binding reviewed scripts/proof/argv/manifest, retained supervisor
errors, total retained output accounting, and other writable container mounts.
The revised design was approved for capability-only container startup, with no
KiCad invocation until actual runtime proof and exact admission are reviewed.
Actual runtime/admission and native observations remain pending at this record.

No native commands, software installations, canonical source edits or changes
to other host projects were performed by this reviewer. Logical parity cannot
establish electrical, mechanical, procurement or PCB acceptance. Nineteen null
passive MPNs and unbound DIN/source-land footprints remain unresolved.

## Final observation: evidence retention failure

The independent review approved actual capability/admission in
`native-run-001/review-admission.json`. Subsequent host retention failed:
`retained/` contains zero files and `result.json` reports zero retained bytes.
The host accepted `docker cp` exit success without verifying required files or
hashes, then killed and removed the container. The exact cause of Docker's
empty copy is not established. The review missed the missing durable-copy
verification before destruction, and was insufficient on that point.

Native outcome is **UNKNOWN**, not PASS and not NOT RUN. The supervisor writes
its done marker after both normal completion and exceptions; the surviving
`native_done=true` therefore proves no native success. The final container exit
137 is the cleanup kill, not the version or export exit. Version/export may
have occurred, but logs, native result and netlist were lost. Native parity was
NOT RUN because no netlist survives. No repeat is authorized by the single-run
scope. A future attempt needs separate exact admission and pretested bounded
stream retention with inventory/hash verification before container destruction.
See `native-run-001/review-result.json` for the bound final review receipt.
