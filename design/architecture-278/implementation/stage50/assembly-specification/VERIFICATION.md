# Stage50 verification

Source-only; pinned numerical Python /workspace/shared/osc-ci-python/bin/python.
The two unittest commands pass seven tests each, no skips; the two evaluator
commands reproduce result.json and verify bindings:

```
/workspace/shared/osc-ci-python/bin/python -m unittest scripts.checks.test_assembly_specification -v
/workspace/shared/osc-ci-python/bin/python -O -m unittest scripts.checks.test_assembly_specification -v
python3 design/architecture-278/implementation/stage50/assembly-specification/evaluate.py
python3 -O design/architecture-278/implementation/stage50/assembly-specification/evaluate.py
```

Controls cover independently known distances, overlap/touch, rejection of invalid
geometry, arbitrary-angle conservative bound, identity/acceptance nonpromotion,
recorded-result replay and byte bindings. No tests assert factory acceptance.
Primary source receipt hashes were independently checked against all eight cached
files; the exact Yageo PDF drawing was visually inspected. Local raw cache is not
required by CI; retained normalized facts and file hashes are the portable evidence.

`pnpm circuit:check` before/after and `pnpm check` pass: manual inventory 68 lines,
0 declared placements, no schematic/placement binding; pin-asset check performed.
Generated pages/preflight/models/31 previews unchanged; tsc passes. This does not
prove a populated resistor identity. Bounded seven historical checkpoint binding
verification and Stage41–49 review manifests are checked in normal/optimized Python;
full historical replay/aggregate regeneration is left to exact-head CI.

Review manifest binds Stage50 substantive files, exact identity sources, and all
Stage49 files. REVIEW.md and the manifest itself are outside its self-reference.
History command: `python3 design/architecture-278/implementation/stage50/assembly-specification/check_bindings.py` and the same command with `-O`.
The first generic manifest driver failed on baseline_head metadata; the retained
driver handles the nested sha256 maps without weakening any hash check.
Whitespace and scope are checked before commit. CI terminal result and exact final
SHA are reported externally on Issue278/PR287 after normal commit/non-force push.
Native local DRC, assembly, physical, manufacturing and electrical verification:
NOT RUN in Stage50. Stage49 native evidence is preserved, not represented as a new
Stage50 native run. No thresholds relaxed or new PCB geometries generated.
