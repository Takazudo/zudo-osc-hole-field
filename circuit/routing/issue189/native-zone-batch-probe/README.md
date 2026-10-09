# Inactive, read-only zone batching comparison

No native probe has run. No acceptance code, workflow, source placement, or
canonical copper is changed by this preparation. The existing sole core worker
37984573591 remains authoritative for its own terminal result; do not duplicate it.

The follow-on branch also exposes already-captured stderr when the precision
vendor sweep stdout assertion fails. Expected exit status and stdout are
unchanged. This improves the next failure's diagnosis; it does not establish the
cause of the earlier empty-stdout failures. That native sweep remains unrun here,
and PR213 stays at803bba6 for its unchanged-head retry.

Run37983410773 stopped at its 80-minute bound with exit124. Its first zone completed
only stage0 items0..133 of144. Upload succeeded: artifact11644814747, archive SHA256
925d83879571b2127af73526ead4cef86472138f3093fc909dfcf19a22f54c1b. The downloaded ZIP
matches; all134 reports say native10.0.6 and all135 fixture project/rule pairs match
the original context. Its result explicitly denies complete zone evidence.
`terminal-receipt.json` retains report hashes and context verification.

The proposed changed method batches artwork while retaining the entire unchanged
native zone. `scripts/pcbgen/probe_zone_batches.py` compares batch sizes1,4,16 on
the same16 evenly spaced saved before-board fixtures. It recreates single-item
bytes exactly before testing any batch; rechecks native geometry, artwork scope,
rendered text and project/rules; and rejects either silk warning category reaching
its199-report cap. Batch identities must equal the saved single-item union.

Predeclared budget:40minutes, one native probe, no repeat with unchanged inputs.
Useful performance threshold: at least2x lower total measured fixture time for
one batched variant than the freshly rerun size1 variant, with exact identities.
The sample is before-only and may contain no zone warnings. Even a successful
comparison is **not** complete warning evidence or permission to adopt core1402.
Any production batching change still needs paired full-scope coverage, positive
native warning controls, cap/coverage regression tests and ordinary/fresh gates.

Preparation checks: eight focused unit tests pass. All16 selected saved fixtures
reconstruct byte-for-byte from the SHA-bound source (heavy-guard PASS24seconds;
offline serialization only). `offline-serialization.json` preserves each fixture
hash. To reproduce that check without invoking native tools:

```sh
python3 -m unittest scripts.pcbgen.test_probe_zone_batches scripts.pcbgen.test_audit_zone_silk_scope
bash "$HOME/.codex/scripts/heavy-guard.sh" -- \
  python3 circuit/routing/issue189/native-zone-batch-probe/check_serialization.py \
  PATH_TO_SAVED_BEFORE_BOARD PATH_TO_VERIFIED_ZIP /tmp/zone-serialization.json
```

## Reproducible execution after native access is restored

Use a supported runner with the repository's exact pinned KiCad10.0.6 image
already available. Current cloud storage and CI pull-quota blockers are recorded
in issue214. Do not retry local image unpacking, alter Docker configuration,
substitute an oracle, or dispatch another core writer to run this probe.

The current session's immutable inputs are:

- `/tmp/issue189-zone-fast.zip` (SHA above).
- `/workspace/zudo-osc-hole-field/.circuit-cache/issue189-downloaded/core-finer-ground-batch/.circuit-cache/osc-core-grid-shards-start/osc-core.kicad_pcb`
  with SHA95c815b2178511621f97cd7021938023b96d4ee19c9282ae99b35fb387ba10c5,
  and its original `.kicad_pro`/`.kicad_dru` siblings.

Copy those inputs into `.circuit-cache/issue189-zone-batch-input/` in the probe
checkout so the existing pinned container can read them. Name the ZIP `golden.zip`.
Then, only after the native-access prerequisite is satisfied:

```sh
bash "$HOME/.codex/scripts/heavy-guard.sh" -- \
  timeout --signal=INT --kill-after=2m 40m \
  bash scripts/kicad/run.sh python3 scripts/pcbgen/probe_zone_batches.py \
  .circuit-cache/issue189-zone-batch-input/osc-core.kicad_pcb \
  .circuit-cache/issue189-zone-batch-input/golden.zip \
  .circuit-cache/issue189-zone-batch-result
```

The output directory must not already exist. Retain all raw reports/fixtures,
`result.json`, console log, input hashes and output archive digest. Compare the
three trial timings from that one run. Never use this output as a substitute for
`complete_native_warnings` evidence. Keep issue189 open.
