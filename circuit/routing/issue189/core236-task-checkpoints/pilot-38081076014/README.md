# One bounded pilot — verified partial audit progress, no eligibility

Parent independently approved exact source53c3034aea893f4f64848789f3d57302c066919a.
All five exact-head CI38080201692 jobs succeeded before one registered-workflow
pilot38081076014 was dispatched. All six unrelated workflow jobs skipped. No
source changed during the run; no PCB, routing, adoption, publication or merge.

The two disjoint B.Cu-before packets15–22 and23–30 completed all16tasks. The
controller step ran1065seconds (19:46:33–20:04:18UTC), within the shared2400second
command; whole job1128seconds (19:45:41–20:04:29UTC), within50minutes. No retry,
full audit, after bootstrap or after tasks were dispatched.

Artifact11681470375,73861869bytes, SHA256
448b59dc66125efbb3a3027ccf5fc1752325dc8e46025956a39a53611a3cf7ec was fully downloaded
and byte-verified against authenticated GitHub metadata. Producer/run/source,
registered workflow path, native kernel and separate orchestration revision,
exact manifest, inspected pinned-image ID, shard ledgers and every leaf receipt
were verified. Every new fixture was reconstructed from immutable source/context
bytes; native geometry receipt, report version10.0.6, all-severity scope, raw report
hashes and target warning identities matched. The native verifier itself was not
rerun during local reconciliation. Heavy guard PASS86s, minimum memory9856MiB.

Coverage is251/426: F.Cu before110/110 and after110/110; B.Cu before31/103 and
after0/103. Missing175 comprises72B.Cu-before batches31–102 and103B.Cu-after
batches0–102. Exact task IDs are in missing-task-ids.json. The three historical
native geometry bindings remain unchanged; B.Cu-after remains unbound.

All16new raw native reports have zero errors. Other raw fixture warnings are
3184isolated_copper,241lib_footprint_issues and9silk_overlap; these are NOT a claim
of complete warning equivalence. Peak aggregate owned RSS5296624KiB (5.05GiB),
minimum available10457952KiB (9.97GiB). No cleanup errors, owned containers or
owned process descendants remained. Both actual inspected images matched pinned
kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec.

The exact251-ID partial union was rejected by final_union's incomplete-coverage
check. Original zone_batch_evidence verification remains unchanged and has NOT
passed for426tasks. complete_reports, full warning/group/connectivity/eligibility
and publication gates remain required and unrun. Accepted main is unchanged at
65cefd41fc39e064d38319115ad96016a1c6b71c: JL117/JR129/core1402, native DRC/parity0/0.
Core1312 remains unadopted. Source b9f5.../f27e... remains immutable; retained
candidate copper evidence133551old+115additions/0cuts is unchanged. Issue189 OPEN.

## Exact continuation — stop for parent review

Review verified-partial-union.json and source53c3034 before any further work.
Do NOT replay the now-complete16-task packets or dispatch the original pilot
again. Frozen baseline manifest/plan files remain unchanged; this checkpoint
records the additive16new leaves and the precise175missing IDs separately.

For future reuse, download immutable artifact11681470375 through authenticated
GitHub, verify its exact digest, and use production verify-checkpoints with the
pinned authenticated-artifact-approval.json file hash
fe548a14a5e6aa810d0a39178a38ed2defa7b09c7eb6307d15c7e635c74044c1.
The approval was generated from authenticated artifact metadata and the explicitly
reviewed producer source, not a producer self-declared pass flag. New source or
manifest/kernel/orchestration changes require fresh review; never rewrite a prior
approval to manufacture equivalence.

Saved local ZIP: /tmp/issue189-core-task-pilot-38081076014.zip. Verified raw files:
/tmp/issue189-core-task-pilot-38081076014-verified. Original saved source/context
files: /tmp/issue189-task-source/{before,after}/osc-core.kicad_pcb. Source archive
/tmp/issue189-core236-reconciliation-inputs.zip digest4211d6ae2ebe9861e17ae45f133c8e6318fcbaa74998740aa10ba879d70bd9ef;
its immutable parent inspection artifact11671779973 digestc5971fa98d5235861294e015150242572cb71dd5fc94a862c0587f8f979d881e.
Oversized raw ZIP/PCB data remains local, outside Git; no LFS.

Reconciliation after those immutable inputs are present (use a new/disjoint
extraction output directory):

```bash
bash /home/agent/.codex/scripts/heavy-guard.sh -- \
  /workspace/zudo-osc-hole-field/.circuit-cache/route-venv/bin/python \
  circuit/routing/issue189/core236-task-checkpoints/pilot-38081076014/reconcile.py \
  /tmp/issue189-core-task-pilot-38081076014.zip \
  /tmp/issue189-core-task-pilot-38081076014-metadata.json \
  /tmp/issue189-core-task-pilot-recheck
```

The73.9MB pilot ZIP was fully locally verified. Historical235-leaf full1.05GB
ZIP was NOT locally byte-verified; the separately approved narrow immutable
producer/compact-receipt equivalence remains its proof basis. No new controlled
same-input routing speedup comparison is claimed; historical H1/H2 regressions
and paired JL/JR/core benchmarks remain unchanged.
