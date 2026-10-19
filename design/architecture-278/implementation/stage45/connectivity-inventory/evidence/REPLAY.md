# Routing-attempt provenance

`propose.sh` and `propose-v2.sh` are historical command records, not commands that
should be rerun over existing output. At the first execution `route_ground.py`
contained B.Cu only; those exact source bytes are preserved as
`first-attempt/route_ground.py.txt`. At the second execution the sole routing
parameter change was F.Cu/In2.Cu/B.Cu. Both attempts returned exit1/NOPATH and
produced empty copper arrays. Neither proposal was applied to a board.

The final helper adds an explicit `--rear-only` switch so replay does not depend
on which historical version occupies the live path. To reproduce *only when a
new routing run is authorized*, use a new ignored output directory per attempt,
the hash-bound existing native dump, the numerical Python environment and the
machine-wide heavy guard:

```
/workspace/shared/osc-ci-python/bin/python design/architecture-278/implementation/stage45/connectivity-inventory/route_ground.py .circuit-cache/stage45/dump.json <new-rear-directory>/proposal.json --rear-only
/workspace/shared/osc-ci-python/bin/python design/architecture-278/implementation/stage45/connectivity-inventory/route_ground.py .circuit-cache/stage45/dump.json <new-three-layer-directory>/proposal.json
```

Do not execute the archived `.txt` directly: its root calculation assumes the
original source directory. Do not rerun the historical driver blindly: its
relative live source path now selects the final helper. Native source board hash
remains pinned and source/destination UUIDs, bounds, widths, raster, clearance and
obstacles remain identical. The final CLI-only addition was source-reviewed;
no third native or routing run is claimed.
