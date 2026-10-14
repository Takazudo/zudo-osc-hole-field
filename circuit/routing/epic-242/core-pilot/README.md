# #252 retained one-core source pilot

**Disposition:** `KEEP_K1402`, source preparation complete; bounded raster and
native comparison **NOT RUN**. This is an input to the two/three/one-core
architecture review, not an architecture decision or copper adoption.

## Exact input and scope

- Integration parent: `40aa1cec58190487dc70aa5048a366e29a6b32a1`, epoch `epic242-e0`.
- Published K PCB: `fa60b4e1587a67501782fb55374f0e5d5133f65cd0bbe62624aef502441fda10`.
- Accepted settled native board: `b9f5ca13f83c7ffdbe5836fd271e7c1099e04b901ca1798a7be06f025bd02d66`.
- Accepted dump: `5218becd38f6bb612f9a169230bd8e6657776a09fc12af5baa6113825e671ffb`.
- Accepted evidence: run `38011194282`, artifact `11658776367`, ZIP SHA256
  `1ed58a9cd4c5796654a9e3e5c9b6e1c1129c353f3451e04c990b95032012479f`.
- Complete retained endpoint projection: `../baseline/k-endpoints.json`.
  `cases.json` pins its hash, source group hashes, complete unresolved pad
  identities, accepted context manifest, native source SHA and router/tool hashes.
- Nine representative obligations include OPA4197IPWR V+/V− near U1602–U1604,
  ADG5412FBRUZ VDD/VSS, U4206 signal/AGND interaction and U4231 reference
  return. The historic 160 rail targets are 68 OPA V+, 68 OPA V−, 12 ADG VDD
  and 12 ADG VSS. AS3340 pin 16 is not in this rail set. `cases.json` records
  complete exact UUID/Ref/pad/net/layer/XY and group identities, rather than
  only these abbreviated names.

`prepare.py` reads the unchanged published board and accepted endpoint
projection. Its closest pads are **proximity observations**, not legal starts,
via landings, valid bypass connections or reachable copper targets. The full
saved dump is required to inspect pad polygons, existing tracks/vias, fills,
keepouts and DRC rules. No source PCB, schematic, panel centre, circuit,
harness, footprint or copper was changed by this lane.

## Diagnosis before another search

| Case | Retained K1402 state | Closest pad in largest other group (centre distance only) |
| --- | --- | --- |
| U1602.4 / +12V | isolated B.Cu pad | C1603.1, 3.105 mm |
| U1602.11 / −12V | isolated B.Cu pad | C1609.1, 9.093 mm |
| U1603.4 / +12V | isolated B.Cu pad | C1603.1, 8.133 mm |
| U1604.11 / −12V | isolated B.Cu pad | C1609.1, 8.041 mm |
| U4206.13 / +12V | isolated F.Cu pad | C4222.1, 2.277 mm |
| U4206.4 / −12V | isolated F.Cu pad | C4223.1, 2.868 mm |
| U4206.5 / AGND | 9-member local group | C4267.2, 17.436 mm |
| U4206.3 / signal | isolated F.Cu pad | nearest other signal pad U4206.10, 6.288 mm |
| U4231.7 / AGND | 3-member group with J900249.2/C4248.2 | R5265.2, 6.142 mm |

The old `core1441-rail-screen` is **not** a current K1402 comparison. It
reported U1602.4 and U1604.4 failing after only 1,406 and 11,913 expansions
against a 300,000 limit; U1603.4 had no recorded A* attempt. Its U1602/3/4
negative rail cases had no recorded attempts. The old U4206 rail screen found
raster paths, but never established native acceptance at this baseline. Thus
raising the search cap is not a diagnosed remedy. First inspect terminal
geometry, legal escape pixels, via landing, connected bypass copper, target
availability and the coupled signal/return groups on the exact saved dump.

## Replay boundary and next commands

The accepted artifact download is currently blocked: `gh api
repos/Takazudo/zudo-osc-hole-field/actions/artifacts/11658776367/zip`
returned `403 Forbidden` on 2026-10-11 UTC. No alternate access route was
attempted. The unavailable 713 MB original archive for the unadopted 1312
candidate was not requested. The native dump cannot be reconstructed from
`k-endpoints.json`; this lane does not fabricate one. Obtain the accepted full
archive through a coordinator-approved readable source, verify the complete ZIP
hash above, and extract its `fresh/dump.json` plus full native project context
into a private retained directory. A local `/tmp` copy alone is not a handoff.

Source-only commands, run now:

```sh
python3 circuit/routing/epic-242/baseline/verify_inputs.py
python3 circuit/routing/epic-242/core-pilot/prepare.py
python3 circuit/routing/epic-242/core-pilot/test_source.py
pnpm circuit:check
```

After an authenticated full archive, exact input hash check, reviewed
executable guard and explicit parent native slot, first compare one case on
the identical dump with two bounded raster resolutions. Use a unique private
output/cache directory, never a shared `workspace()` name:

```sh
sha256sum .circuit-cache/epic242-252-unique/accepted/fresh/dump.json
timeout 300 bash scripts/kicad/run.sh python3 circuit/routing/epic-242/core-pilot/replay.py --dump .circuit-cache/epic242-252-unique/accepted/fresh/dump.json --case opa-osc-plus --resolution 0.025 --output .circuit-cache/epic242-252-unique/opa-coarse.json
timeout 300 bash scripts/kicad/run.sh python3 circuit/routing/epic-242/core-pilot/replay.py --dump .circuit-cache/epic242-252-unique/accepted/fresh/dump.json --case opa-osc-plus --resolution 0.0125 --output .circuit-cache/epic242-252-unique/opa-fine.json
```

`replay.py` refuses a wrong dump, board, native group or pad and emits the
existing grid proposal shape with diagnostics, elapsed seconds and peak RSS.
The 300-second timeout is per case, 300,000 A* expansions per attempt, 6 mm
window, 12×12 mm source bounds. The parent guard must enforce at most two
global workers, 6 GiB per worker/12 GiB aggregate and at least 2 GiB free;
the current baseline guard is a proposal and remains unqualified. Do **not**
run these commands before admission. If both settings are non-improving,
record the cause and change method; do not repeat unchanged searches.

For any useful proposal, the coordinator must apply it to a private complete
project copy using `scripts/pcbgen/grid_apply.py`, then run pinned KiCad 10.0.6
full-severity schematic-parity DRC with refill/save-board until three stable
connectivity signatures, and repeat from an independent fresh copy. Preserve
`.kicad_pro`, `.kicad_dru`, all sheets and both library tables. Review all
original connected pad groups, cuts/restorations, warning identities,
non-routing geometry, published/candidate/context/code hashes and the actual
checked blob. The supply and AGND repairs form **one whole transaction**;
per-net route-shard deltas are not automatically composable. Only the sole
coordinator may merge/promote canonical K, and only an `adopted:true` receipt
with its published blob can establish adoption. Current native status is
`NOT RUN`, not a pass or a negative native result.
