# Preserved core work — not adopted

Run [37775496177](https://github.com/Takazudo/zudo-osc-hole-field/actions/runs/37775496177)
finished with a failed push: the filled board was 100.11 MB, beyond GitHub's limit.
The source branch remains `8315af554132b283e4e6e9b62d76bbfdcea560c0`. It was not modified.

All eight artifact ZIP SHA-256 values were verified against GitHub's artifact
digests before extracting these exact deltas. Failed shards had retained earlier
partial stage deltas; the aggregate therefore contains more than shard 0 alone.
`aggregate-copper.json` applies the original merger's eight reverted nets to those
deltas. It reproduces 1,413 additions and 29 removals against the unchanged core
SHA in `preservation.json`, retaining 132,924 original copper objects (132,916 unique UUIDs).

`original-native-receipt.json` is historical evidence, including its original
`adopted: true`; **that is not this branch's acceptance decision**. The original
run reported 1,509→1,400 total edges with zero DRC/parity errors, but AGND worsened
252→272. The earlier 1,390-edge candidate had failing copper; reverting eight nets produced
the final 1,400-edge result. This was not evidence of fresh-copy drift. Current pad-membership, warning
identity and independent-copy gates have NOT RUN on this recovered replay.

Reconstruct a disposable candidate without touching canonical copper:

```sh
.circuit-cache/route-venv/bin/python - <<'PY'
import hashlib,json
from pathlib import Path
from scripts.pcbgen.route_jack_grid import workspace
from scripts.pcbgen.route_shards import merge_text
base=Path('boards/osc-core/osc-core.kicad_pcb').read_text()
d=json.loads(Path('circuit/routing/issue189/concurrent-core/aggregate-copper.json').read_text())
assert hashlib.sha256(base.encode()).hexdigest()==d['base_sha256']
out=workspace('osc-core','189-recovered')/'osc-core.kicad_pcb'
out.write_text(merge_text(base,[d]))
print(out,hashlib.sha256(out.read_bytes()).hexdigest())
PY
```

Next intervention: after reviewing the corrected core benchmark, check this
replay in pinned KiCad, identify its split AGND pad groups and repair/stitch the
affected returns. Compare all pad memberships and warnings against the unchanged
base, with settled refill plus independent reload. Do not adopt merely because
the total is lower. Resolve the filled-board storage limit using replayable source
and native-verified handling of derived fill caches; never use Git LFS, discard
successful copper, or commit a board over GitHub's limit.
