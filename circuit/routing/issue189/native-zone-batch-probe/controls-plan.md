# Native batching controls — prepared, not run

The134 completed saved zone fixtures have no zone-linked silk findings. Timing
equality on that archive alone therefore cannot demonstrate detection of a
positive finding. No production batching or acceptance change is authorized by
an all-negative sample.

`probe_zone_batch_controls.py` prepares an independent native control: copy the
exact full zone polygon coordinates from SHA95c815b2178511621f97cd7021938023b96d4ee19c9282ae99b35fb387ba10c5,
deliberately map its layer to F.Mask, and insert two synthetic silk lines inside
that exposed mask region plus one outside. This is a deliberately modified test
fixture, never a source/candidate board. It requires pinned10.0.6, original
project/rules, exact native polygon coordinates, exact artwork IDs and below-cap
reports. Single-positive, single-negative and joint reports must detect exactly
the expected IDs, and the batch identity set must equal the single-item union.
A missing positive finding fails the control; it must not be relabeled a pass.

Eleven unit tests pass for serialization, explicit layer mapping, identities,
invalid scope, native version and capped report rejection. **Native NOT RUN.**
First reconcile performance run38002541870 on b19d387. If batching meets the
predeclared2x threshold with identical scope/identities, run these controls once
with a10-minute command bound on the supported pinned runner. Do not retry local
image unpacking. Keep core writer37984573591 untouched.

```sh
timeout --signal=INT --kill-after=2m 10m \
  bash scripts/kicad/run.sh python3 scripts/pcbgen/probe_zone_batch_controls.py \
  PATH_TO_VERIFIED_BEFORE_BOARD .circuit-cache/issue189-zone-batch-controls
```

A successful control still does not certify core1402. Production batching would
need exact before/after coverage, per-batch source/geometry/context/report
binding, both report caps, complete identity unions, coverage rejection tests,
and a fresh full native audit. The existing acceptance path is unchanged.
