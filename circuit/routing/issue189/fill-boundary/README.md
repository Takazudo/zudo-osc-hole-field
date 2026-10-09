# Fill boundary regression

The old fill guard could use empty raster padding outside the physical outline as a connection path. `bypass-before.json` demonstrates a synthetic plane cut accepted by the old screen even though the two inside-domain pads are disconnected. The two new tests initially errored because the old constructor had no domain argument (`before.txt`); these are not assertion failures or native-board evidence.

The guard now intersects its region with a copied physical/search domain, including after reset. Route construction supplies `raster.d_edge > 0`. The screen remains approximate: exact native zone shapes, refill and whole-board connectivity are mandatory. All 99 affected tests passed.

## Same-input comparison

Run from repository root:

```sh
bash "$HOME/.codex/scripts/heavy-guard.sh" -- .circuit-cache/route-venv/bin/python circuit/routing/issue189/fill-boundary/benchmark.py
```

The script saves the old Python and C A* sources from immutable commit `3f7fb6895f4a7d2d7590ef40d3d66486025480a8`, requires native A* in both cases and asserts that the control exactly reproduces the saved 115 copper objects. The first harness attempt omitted the adjacent C source, fell back to Python and failed that assertion; it is excluded from this comparison. The corrected guarded run passed.

Input board SHA256: `3d9940791131e31d22ea65e4457ccb77d5250d629eaa2b5d3c6b03024ac3405c`. Dump SHA256: `135e1c2495204972ad3f410d90b649c67f3ce9fa87eab724f19cb7196c87c53b`. Identical net, frame and numerical parameters are recorded in `benchmark.py` / `benchmark.json`.

Before: 4.836299s, 115 objects. After: 4.924470s, the identical 115 objects. Single-run timings do not establish a speedup. This boundary correction does **not** prevent the known native -12V split from run37925027262. No new native run or accepted copper is claimed. Exact zone-domain fidelity remains further work.
