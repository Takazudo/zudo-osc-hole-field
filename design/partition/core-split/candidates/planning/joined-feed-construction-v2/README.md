# Constructed CS247 feed candidate

This packet constructs disposable KA/KB board contexts and one complete six-wire feed with three separate AGND returns. It keeps the fixed 58 mm lateral offset, 66 mm nominal free-wire length, existing endpoint identities and existing top support holes. The candidate is source geometry for engineering review, not an adopted board, qualified assembly or native clearance result.

The constructor preserves owned local signal copper and original rule areas, emits twelve uniquely identified 4 × 4 mm capped solder lands and 300 plated transfers, and records every original copper-object disposition. Rail distribution is reconstructed separately with explicit ownership. No generated candidate may replace a canonical board.

## Physical construction

Each endpoint has nineteen inclined copper cores, actual board-parallel trimmed tips, finite solder prisms and affine foil contact patches. The contact current fields have matching normal traces; each endpoint integrates to 1 A. The three AGND wires retain separate finite terminal ports. Neither a zero-impedance board node nor equal return-current sharing is assumed.

The mechanical model contains 204 solids with explicit subtractive bores, slots and cavities. Each board has a sleeved metal top beam using its two existing 2.2 mm support holes. Six 2 mm square carrier fingers join split collets through dimensioned lugs. M1 clamp screws, nuts and dielectric caps are explicit solids. Capped M2 support hardware, insulating washers and termination shrouds are included. The beam is displaced outside the board's top edge, and the fingers turn away from their own and neighboring wires before descending to the beam.

The installed insulation begins 3.75 ± 0.05 mm along the inclined axis from each land. The full metal envelope, insulation and both straight wire-end regions are separate from the free cubic curve. Existing 110 mm metadata is explicitly superseded by effective feed cuts of 84.5–85 mm and main cuts of 103.5–104 mm. These are proposed manufacturing limits, not achieved measurements.

## Assembly and service sequence

1. Fabricate the proposed capped-via lands and verify continuous copper over the nineteen finite injection patches. Ordinary open via holes do not meet this geometry.
2. Insert-mold the beam's dielectric sleeve around its metal core; the final closed cavity is not a proposed insertion opening. Assemble each split carrier around the existing top support interfaces with the insulating washers and encapsulated fasteners. Retain the independent board carrier and service guide.
3. Prepare each wire to its effective cut and strip dimensions. Place the termination shroud on the wire before soldering, fixture the inclined cores, solder within the owned land and bounded exposed-metal envelope, and bond the shroud's dielectric base to the finished board surface outside the copper and mask opening. The drawing defines positive-area base patches; the adhesive, surface preparation and suitable bond lands must be specified and qualified without cutting retained copper.
4. Close the split collet around the insulated straight segment. Install its M1 hardware, then bond or otherwise retain the dielectric caps at their dimensioned lug interfaces; cap clearance alone is not retention. Check the actual exit center and tangent before relying on the own-collet exit proof.
5. Inspect land registration, solder spread, insulation cut, material continuity and the full installed wire shape. Check the entire 0–10.1 mm service travel against the conditional C0/C1/C2 limits before physical acceptance.

This sequence specifies construction intent. Retention, fastener torque, split-carrier assembly practicality, creep, thermal behavior, materials, strain relief and measured service repeatability still require qualification. Source solid union and clearance do not establish mechanical strength.

## Source evidence and limits

The continuous free-curve check encloses every cell of the full gap and free-length parameter domains. A separate checker covers straight insulated and bare ends, and another encloses every translating carrier solid throughout service. The source obstacle inventory includes retained component reservations, supports, loom/protection reservations and all 100 proposed trimmer tool columns. Passing these incremental columns does not qualify the baseline's already blocked front approach.

Earlier constructions and their failed checks are retained as diagnostic evidence. Candidate 01 failed against the beam and fingers; 02 failed against a neighboring wire; 03 passed the free-curve and rigid-solid screens but left its own bare-end/finger clearance unresolved. Candidate 04 displaces that finger by a further 1 mm and passes the three continuous source screens. Independent joint review then identified a 0.30 mm clamp-head bearing gap and missing shaft clearances in the support-cap floors. Candidate 05 corrects those actual interfaces, following review, and repeats the affected geometry checks.

No native process, F3 placement trial, canonical board change, adoption, merge or fabrication action is performed by these scripts. Generated boards, full source-disposition tables and full contact/solid meshes remain disposable local artifacts with deterministic producers and SHA-256 receipts; Git LFS is not used.

## Reproduction

Use the pinned Python, NumPy, SciPy, Shapely and GEOS versions in the final evidence ledger. Run each source operation with its 180-second and 2 GiB bounds. Choose a fresh output directory outside the tracked repository, then run `construct.py --output DIR`, `wire_contract.py --candidate DIR --output DIR/wire-family.json`, `check_geometry.py --candidate DIR --output sweep.json`, and `check_solids.py --candidate DIR --output solids.json`. The end, joint and board-access helpers provide separate evidence; no single passing screen is whole-candidate acceptance.

The E16 access epoch replays with `bash replay_e16.sh PYTHON ABS_OUTDIR [--board KA|KB] [--through ROUND] [--resume]`. Each step is hash-ledgered. `compare_replay.py` checks a replay against the retained receipts by content, and `run_finite_network.sh` plus `summarize_network.py` rebuild the conditional finite network. `WORK.md` records the current rounds, results and limits.
