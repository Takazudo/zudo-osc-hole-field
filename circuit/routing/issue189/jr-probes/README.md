# Bounded JR negative probes

These are raster-only diagnostics after the identical-input benchmark, not native
acceptance. All three produced zero copper additions and zero removals. Canonical
JR remains 162 native open edges. Stop these configurations; another global retry
with the same method is not justified.

| Probe | Change | Seconds | Result |
| --- | --- | ---: | --- |
| fine-grid.py | 0.05 mm grid at RB4611.1 | 14.77 | Fill-guard rejection, rollback |
| protected-victim.py | Exclude prior failed victim from removal | 8.90 | Another victim could not reconnect, rollback |
| surface-only.py | 0.05 mm B.Cu only, surface-accessible victims | 9.24 | No legal probe path |

Widths, clearances, neck-down rules, via dimensions and the -12V fill guard remain
unchanged. No placement or source requirement changed.

## Reproduce

Download artifact 11572210336 from run 37824203279. Verify ZIP SHA256
`4216483ee7e284de2b0160344034f839bc71ab0233fb2ba01bdb527502958244`.
Extract its `issue189-osc-jack-right/input/dump.json` to
`.circuit-cache/issue189-downloaded/jr-dump.json`; the dump SHA256 must be
`b53fc851992843175db2669ec12540e1e6e27b4eda4c28a5834ce349c11f377b`.
Use the pinned `scripts/pcbgen/numerical-requirements.txt` environment, from the
repository root:

```sh
bash "$HOME/.codex/scripts/heavy-guard.sh" -- .circuit-cache/route-venv/bin/python circuit/routing/issue189/jr-probes/fine-grid.py
bash "$HOME/.codex/scripts/heavy-guard.sh" -- .circuit-cache/route-venv/bin/python circuit/routing/issue189/jr-probes/protected-victim.py
bash "$HOME/.codex/scripts/heavy-guard.sh" -- .circuit-cache/route-venv/bin/python circuit/routing/issue189/jr-probes/surface-only.py
```

The scripts write separate cached proposal/diagnostic JSONs; the checked-in JSONs
are the original negative receipts. Native checks were NOT RUN because there was
no proposed copper to check. A next method should address the source-defined
circuit locality or return-path geometry, not simply raise search limits.
