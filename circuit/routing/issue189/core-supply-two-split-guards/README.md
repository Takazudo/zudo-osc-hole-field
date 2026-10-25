# Core supply trial after two native AGND splits

This distinct90whole-case/115segment proposal omits exactly three whole cases from source47bb19a42f6612a114e4aff51c4b120301fe5e71: U4106.13 (+12V), U4206.4 (−12V), U4206.13 (+12V). All133551accepted copper objects remain; no vias, cuts, moves or requirement changes. Every new segment remains0.25mm wide.

The predecessor1402→1311 was rejected for AGND1988→1985+3 (C4170.2/U4145.12/C4171.2) and9→7+2 (C4270.2/J900155.2), independently verified from artifact11666004488. The omitted cases are the nearest same-layer whole supply cases to these detached pads (5.22mm and6.86/9.98mm). This geometric ranking is **not causal attribution or native acceptance**; it only defines a bounded hypothesis. Native settled/fresh original-group checks must establish whether it helps. Do not adopt a lower count with any split.

The native serializer checks exact input/proposal hashes; route_shards requires complete native warning audits,batch16,and all existing settled/fresh/group/DRC/parity/publication gates. Structural native failure now rejects before expensive supplemental audits. Canonical core remains1402 until the complete proof and exact-head CI are accepted.

```sh
gh workflow run routing-benchmark.yml --ref agent-fix/189-core-supply-two-split-guards -f board=osc-core -f recover_core=true -f core_replay=supply-two-split-guards
```

Dispatch once, own its run to terminal reconciliation, preserve exactsource/output/artifact hashes, and do not overlap another core worker. Issue189 remainsOPEN; this is not fabrication or hardware qualification.
