# Issue 246: source-owned mechanical comparison

Status: MECHANICAL_COMPARISON_READY for architecture review; no topology, physical fit, component substitution or production geometry accepted.

Open `generated/inspection.html` locally (no server/dependencies), select alternative/board/face, and select a trimmer Ref. Ten dimensioned assembled/exploded SVGs and `comparison.json` are generated from `candidates.json`, frozen repository sources and the pinned #248 inputs. The full interface inventory retains 195 harness IDs, 390 endpoint Refs, complete pin order and source non-core poses. No canonical board/circuit/generator is written.

Pins:
- Original/current-main source epoch: `65cefd41fc39e064d38319115ad96016a1c6b71c`.
- Reconciled integration parent: `1da1909846dc3255888ecd36c88cee9737c85834` (baseline ledger + status documents only versus epoch).
- #248 labels/component review: `7aba720c1246d6ec3f02909af6fb08dc774b3d31`; `inputs/` contains byte-for-byte copies of `design/service/trimmer-functions.json` and `design/service/component-review/review.json`. Ref/Block/Role joins fail on mismatch. Candidate MPNs are not adopted.

Run from repository root:

```sh
PYTHONPYCACHEPREFIX=/tmp/osc246-pycache python3 design/partition/core-split/mechanical/build.py
PYTHONPYCACHEPREFIX=/tmp/osc246-pycache python3 design/partition/core-split/mechanical/build.py --check
PYTHONPYCACHEPREFIX=/tmp/osc246-pycache python3 -m unittest discover -s design/partition/core-split/mechanical -p 'test_*.py'
python3 circuit/routing/epic-242/baseline/verify_inputs.py
```

`build.py` checks recorded source hashes before writing only its own generated directory. Source changes require explicit reviewed rebinding, not silent regeneration. Source-lock records source bytes and generator/input hashes. Unit tests exercise preservation mutations, continuous curve bounds, rejected spans, passage/support collisions, label disjointness and unqualified acceptance states. Temporary browser profiles/instrumented copies stay outside production assets. Reviewed browser receipts and screenshots are retained under `evidence/issue263-mac/`.

## Model and limitations

Panel front Z=0, rearward negative; all dimensions mm. Source XY, rotations and F/B poses stay fixed in assigned families. Two-core is a comparison preference only. All boards retain the 310×284 outline and 56×46 notch. Independently enclosure-supported trays reuse eight M2 seats: 2.2 holes, 3.2 collar envelopes; 26 plane pitch gives 24.4 PCB-face gap and 12.1 allowance-to-allowance gap with 7.3 front/5 rear allowances. These are not confirmed component solids or latch clearances. Proposed rear work depth 60, cradle inner 322×302 and 10 unmating travel are project reservations, not manufacturer-qualified travel. Supports cannot load solder joints/connectors; stiffness, threads, carrier extraction and hands remain unverified.

Retained bow law is y=y0+4 sin²(πt). Route length uses a conservative continuous upper bound span+4π²/span, then 10 cut allowance and integer ceiling; sampled chord is lower only. Continuous minimum-radius bound is span²/(8π²), compared with 9.398 for max-OD AWG26. Through-board ribbon reservations include 0.05 sampling allowance and 0.5 edge margin. Passage collisions enumerate actual parts, supports, GH headers, protection and tool reserves. Full continuous pairwise cable/support/hand sweep is NOT checked. Straight-line power bounds plus 10 are necessary lower bounds only, not realizable wires or voltage-drop evidence. The reconciled original 18 main wires terminate on KA only; no original wire is hypothetically reassigned to KB/KC. New CS247 branches are separate, unplaced contracts with a retained 110 mm cut ceiling.

No alternative is interference-free: compact options hit the four retained JL–P loops; deep options require more case depth and new power budgets; all retain through-board/material, component and tool-access blockers. The rejected 48/74/100 option exposes 58 bend-radius failures. Zero label overlap is only reservation geometry: maximum relocation is 111.832 mm (two) / 82.354 mm (three), so leaders/local Ref silk and readability need #249 review.

All 100 trims remain inventoried (44 F, 56 B). Preserve the accepted owner adjustment intent, without owner soldering. Reversible supported trays and a factory-connected service-loop loom are proposals, not permission to desolder for calibration. #248 confirms TC33X-2 top adjustment, nominal 1.2 height, conservative 3.9×4.1×1.5 candidate bound and 1.7 cross-slot tool; 3 mm shaft/60 free-length reserves here are larger project assumptions. Axis alignment, seating, mirrored installation, hand sweep and calibrated rotation remain unverified; 23 source MPNs remain unresolved.

## Sources and next coordination

Primary retained PDFs: `design/connectors/sources/jst-gh.pdf` (mated GH/connector drawings), `design/partition/sources/alpha-6821.pdf` (AWG26 OD/bend), `design/partition/sources/alpha-5859.pdf` (power wire OD/bend), `circuit/sources/ic-library/TC33X.pdf` (Bourns drawing). Hashes and CAD receipts are in source-lock; #248 review records exact source locators and qualification gaps. Courtyards and family 3D references are not measured solids.

#245/#249: resolve family placement, passages, support collisions and local label access before native placement. #247: actual feed ownership, slack/loops, cuts and electrical budgets. #253/#55/#64/#65: supported access and measured mechanical evidence. Do not select topology from this report alone.

Native routing/DRC/ERC, complete initial/final canonical regeneration, physical fit and full CI are NOT RUN. No global native slot was assigned; canonical regeneration also writes unowned production paths. Commit skips automatic CI deliberately because existing workflows can exceed global native concurrency. A coordinator must assign a bounded pinned KiCad 10.0.6 command through `scripts/kicad/run.sh` before native acceptance. No substitutes or mock acceptance.

The historical Cloud browser deferral in [#263](https://github.com/Takazudo/zudo-osc-hole-field/issues/263) now has successful Mac Chrome interaction and visual evidence in [the browser review](evidence/issue263-mac/README.md). All five alternatives / 500 alternative-specific rows, all boards, face/reset behavior and assets passed. Issue #263 remains open pending review/integration of the portability fix; physical/native acceptance is unchanged. Run `check_browser.py --output-dir <new-evidence-directory> --visuals` through the available shared browser guard; executable discovery can be overridden with `--browser` or `CHROME_BIN`.

## Power contract reconciliation and deterministic correction

The source correction consumes [power PR #262](https://github.com/Takazudo/zudo-osc-hole-field/pull/262) at exact `6494b3b40b50b999e52fb064c1384aec7381ea8d`. Byte-identical `input.json` and `contract.json` snapshots are kept as `inputs/power-input.json` and `inputs/power-contract.json`, with generator hashes in `generated/source-lock.json`. Every assigned core package is checked against the power module ownership. Neither comparison topology is selected.

All 13 POWER parts, original 18 K main lands and the 76×70 protection reserve stay on KA. The old replicated protection masks on KB/KC have been removed from label/passage checks and views; that removal does **not** free space for adoption, because satellite feed, bulk and monitor envelopes are still unplaced. Each added core receives a separate KA load-side star branch: six factory-soldered Alpha Wire 5859 BK005 wires, in order +12 V, −12 V, +5 V, AGND, AGND, AGND. Existing GH identities/pins are untouched and are not repurposed as full-core power feeds.

Each CS247 branch needs **both** endpoint rows of 91×6 and separate F-side service corridors of 91×28×28. Three 5×3×5 B-side bulk reservations per core and one 20×20×5 B-side monitor per satellite are carried verbatim, with null global origins. At 26 plane pitch, the nearest forward core leaves 24.4 bare face gap: a 28 high normal corridor has a **conditional 3.6 deficit** wherever its XY projection crosses that board (8.6 versus a 5 rear-body allowance). It exceeds the ordinary 7.3 front-body allowance by 20.7. This screen does not invent coordinates or assert a collision at an unknown location. Edge escape, aperture or changed geometry requires explicit placement and collision review; KA's front-assembly clearance is also unknown. These unplaced envelopes are visible in the inspector's power-reconciliation data, not drawn as fabricated global solids.

The 110 cut ceiling does not provide extra slack for tray withdrawal. Soldered branches do not establish removable/reversible service. Factory-connected loops, independent strain relief, hand/tool access and supported adjustment without owner soldering remain requirements needing a realizable route; no desoldering or live internal service is assumed. Global 1 mΩ rail / 0.5 mΩ common-AGND / 20 mV budgets cannot restart at each core. Existing #57/#59/#65 gates remain open.

The coordinator's generation drift was reproduced by reversing filesystem enumeration: four footprint receipt lists changed order while source bytes were identical. CAD receipt paths are now sorted before serialization. The regression reverses every `Path.glob` enumeration and compares all generated outputs byte-for-byte, covering JSON, HTML, source lock and ten SVGs. This proves order independence for that mutation, not native or physical acceptance.

The integrated 9e0aceda two-core follow-up is in [feasibility-handoff.md](feasibility-handoff.md): continuous cardinal placement blocker, exact 40 strict-gap proposals, and new JSON/SVG artifacts. It supersedes no production geometry.
