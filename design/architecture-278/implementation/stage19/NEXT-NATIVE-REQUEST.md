# Immutable next native request — not admitted or executed

- Source implementation: `91403f4d78b72757187d8cfdbb4d2dc436a3cf72`.
- Supervisor verification commit: `a57e02f6bfd770e55ebf448bc067e79fc6b08eb5`.
- Request: [native-request.json](native-request.json), SHA256
  `a5ea1b6814adabd66b326773f92089ac2bdd35a054d3b0e9d1edde61d20e25d1`.
- Exact bindings:72input files,155verification files,5runtime files.
- Review: [independent review](review-independent.md), with exact hashes in
  [review-independent.json](review-independent.json).
- Image: `kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec`.

Use a separate exact checkout at the supervisor verification commit. The later
publication commit adds only this request/document and WORK notes. Copy the
published request outside that checkout and verify its digest. Do not execute an
old Stage17 wrapper or reuse RUN001/RUN002 admission.

Future owner-authorized invocation, after resolving absolute host paths:

```bash
bash "$HOME/.codex/scripts/heavy-guard.sh" -- \
  python3 <exact-checkout>/scripts/architecture278/implementation/stage19_host.py \
  --repo <exact-checkout> \
  --run <fresh-parent>/osc-stage18-native-001 \
  --request <published-stage19-native-request.json> \
  --owner-approval <fresh-owner-approval.json>
```

This command has **not** been executed. The JSON request defines exact native argv,
Docker argv template, resource limits, input/runtime/source hashes, approval and
admission fields, and post-retention comparator argv. Fresh owner approval is
required before container launch. A fresh live independent reviewer must bind the
new nonce and actual Docker/cgroup/mount/network proofs before native work. The
single opportunity is consumed before the version probe; failures never retry.

Remaining host preflight: prefer Cloud; prove its existing Linux Docker runtime,
already-present pinned image, shared heavy guard, available memory and required
isolation. If Cloud cannot prove these, assess existing X0X Linux/WSL afresh. No
installation, image pull or version probe belongs to preflight. Neither host's
current capabilities were inspected or assumed in this source-only task. A fresh
absent output directory/container name and private metadata budget are mandatory.

The reviewer and source tests establish supervisor implementation behavior only.
After one future admitted run, first retain and verify exact raw receipts, then run
the Stage18 comparator on `retained/netlist.xml`. Native export success and logical
parity are separate outcomes. RUN002 full parity remains FAIL;118references,
561pins and154unitUUIDs must all be present. No electrical acceptance is claimed.
19unresolved passiveMPNs and unbound DIN/land footprints remain procurement/PCB
blockers. Canonical boards, locked placements and architecture decisions remain
unchanged; PR286 is draft/unmerged.
