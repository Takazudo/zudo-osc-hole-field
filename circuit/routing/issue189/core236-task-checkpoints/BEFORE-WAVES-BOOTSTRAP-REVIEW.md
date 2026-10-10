# Review checkpoint: remaining before waves and read-only after geometry

Source only; no new workflow dispatch, native bootstrap, routing, adoption or merge.
Review the pushed source and exact-head CI before admitting this sequence.

Authenticated baseline remains 251/426: both F.Cu stages (220), B.Cu-before
0–30 (31), B.Cu-after (0). The original pilot run38081076014 artifact11681470375
has SHA256448b59dc66125efbb3a3027ccf5fc1752325dc8e46025956a39a53611a3cf7ec.
Its approval remains byte-identical SHA256fe548a14a5e6aa810d0a39178a38ed2defa7b09c7eb6307d15c7e635c74044c1.
Compatibility is limited to that artifact, run, approval and producer
53c3034aea893f4f64848789f3d57302c066919a, with its original six source blobs
independently rehashed from git. Other producers retain strict orchestration
revision equality. Native kernel, source/context and 426-task manifest are unchanged.

## Frozen B.Cu-before plan

Plan file SHA256: afbc6714df3a6e3faeb2131240836ac18c0e86990bad4443b22326e5cbbdb0bb.
The JSON contains all exact task IDs and baseline IDs.

| Wave | Packets (ordinal ranges, inclusive) | Tasks | Reconciled coverage |
|---|---|---:|---:|
| 0 | 31–38, 39–46 | 16 | 267/426 |
| 1 | 47–54, 55–62 | 16 | 283/426 |
| 2 | 63–70, 71–78 | 16 | 299/426 |
| 3 | 79–86, 87–94 | 16 | 315/426 |
| 4 | 95–102 | 8 | 323/426 |

Nine eight-task packets, 72 tasks; max two workers globally under the existing
concurrency group. Each wave shares one 40-minute command /50-minute job budget,
12GiB aggregate RSS ceiling, 2GiB minimum available memory and 6GiB/container caps.
Pinned image and native10.0.6 requirements are unchanged. Cleanup and partial
uploads remain mandatory. Before another admission, download and authenticate
immutable terminal artifact bytes, producer/source/kernel/revision/ledgers and
every native receipt, then require the exact full wave and zero native errors.
Proof mismatch, partial coverage, capped warnings, guard or cleanup failure stops
without automatic retry. Existing exact-source admissions are rejected, including
when invoked with a new output directory. Exclusive admission markers precede
POST; lost responses are ambiguous, never retried automatically. Completed packets
cannot be selected. A stop retains raw outputs and sequence.json; do not launch
another sequence without reviewing that state and constructing an explicit resume.

## Separate geometry bootstrap

The geometry-bootstrap mode runs one pinned native container, no DRC task.
It authenticates exact source/context, manifest and native validator revision;
loads the two boards in independent native processes, reproduces all three existing
signatures as controls, checks the after f27efe521f4ed4f6c0ceb53f45f58a82a824c05475ef012a2034a0d1d2a154d1
B.Cu AGND zone e389d344-872d-538e-9bfc-39577adb1686 UUID/layer/net/source-zone
bytes, rejects arcs and uses the existing native signature function. There is no
refill, save, reroute or DRC call. Two reloads must agree and source/context bytes
must remain unchanged. The authenticated artifact receipt binds producer/image,
validator, source/context, manifest, geometry reference and signature, reports
zero completed DRC tasks, and explicitly requires stage review. It does not rewrite
the 426-task manifest or automatically authorize any of the 103 after tasks.
The bootstrap has not run; fake-native tests are not native10 evidence.

## Exact continuation after source review

Use a clean checkout of the reviewed pushed commit. First require all five CI jobs
successful on that exact head; the sequence checks this rather than accepting a
branch-name result. Prepare fresh ignored source and output directories:

```sh
python3 scripts/pcbgen/core_audit_pilot.py prepare --output /tmp/issue189-reviewed-wave-input
python3 scripts/pcbgen/core_audit_sequence.py \
  --source /tmp/issue189-reviewed-wave-input \
  --config circuit/routing/issue189/core236-task-checkpoints \
  --output /tmp/issue189-reviewed-five-waves \
  --reviewed-commit REVIEWED_FULL_COMMIT \
  --reviewed-plan-sha afbc6714df3a6e3faeb2131240836ac18c0e86990bad4443b22326e5cbbdb0bb \
  --ci-run EXACT_HEAD_GREEN_CI_RUN
```

These commands have not been executed. The sequence stops at323/426. After that,
review the accumulated sequence.json and immutable approvals, then dispatch the
registered routing-benchmark workflow only in geometry-bootstrap mode with those
resume approvals, exact reviewed commit/manifest and all other work flags false.
Authenticate the terminal geometry artifact with core_audit_pilot.authenticate_geometry
before reviewing the after-stage transition. Do not fabricate an after binding or
count bootstrap as a task. Final426 exact union, complete_reports, warning/group,
connectivity, publication and integration gates remain required and unchanged.

Existing successful copper is untouched: no PCB file is edited here. Accepted
JL117/JR129/core1402 remains distinct from the unadopted core1312 candidate.
No new connectivity, speedup, DRC/parity or fabrication qualification is claimed.
