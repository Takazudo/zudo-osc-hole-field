# Independent electrical/interface review — revision 2

Reviewer: revision_review, independent of revision_electrical and revision_mechanics authors. Review lane: local WSL/Linux, Python 3; read-only source inspection and scalar/checker tests. No circuit, connector, model or test implementation authored by this reviewer. Production baseline is 65cefd41fc39e064d38319115ad96016a1c6b71c; preceding design checkpoint is 4fbbe9c28c10b2648bd1edd8e45e9ff8c5651212. Final reviewed bytes are recorded below.

## Decision

The mixed topology is a specific, useful candidate for separately authorized one-zone implementation: retain independently supported front flexible links, direct rear signal mating, and supported low-resistance power/return joints. Recommend that next engineering stage, conditional on its acceptance tests; **no architecture adoption, electrical acceptance or physical qualification** follows. Remaining exact footprint/seating, structural, low-resistance joint and load-state work is required implementation/qualification work, not a request that the owner choose every connector parameter again.

The revision removes the incorrect inference that a three-layer architecture inherently doubles crimps. The original 11 harnesses/51 conductors/102 crimps remains the mixed transport count; the literal two-cable topology has 22/102/204. Mixed adds one 96-contact DIN pair (51 assigned, 45 fitted NC; 192 connector solder joints). GH contributes 102 signal and 44 hold-down solder joints. Eight proposed power/return straps add 16 contact interfaces and their listed fasteners; shared source feeders and 36 historical factory terminals remain separate. Core-only retained-board adapters still need a complete implementation bill, so neither cost/time savings nor complete equality with core-only is established. All-direct counts are a deliberately populated comparison, not a globally optimized solution.

## Independent source and arithmetic checks

Read the actual oscillator builder and electrical-standard control/reference cells. The five raw wipers retain 1 kΩ series and 10 MΩ pull-down; only TUNE/FINE/PW have local 10 nF filters. The revised model distinguishes local filtering from the 1 nF remote envelope and existing control-law attenuation from added connector/leakage error. Conditional 4/31 kΩ source-plus-series sensitivity gives 4/31 µV per nA; the three 10 nF local filters yield approximately 309 µs at the stated source-resistance assumption. These remain conditional values, not complete temperature/component-tolerance guarantees.

Five nominal 100 nF octave receivers behind 1 kΩ demand 25 mA initially for simultaneous 5 V transitions and 2.5 µC total recharge. At a hypothetical 2 mA available current the charge lower bound is 1.25 ms; the retained 2 mA value is a planning condition, **not a proven amplifier current clamp**. The aggregate 900 pF direct parasitic allocation cannot absorb the 500 nF behind resistors. The proposed 15 kΩ/220 MΩ alternative has a consequential 22 s nominal open-switch discharge and is correctly not silently adopted. Its resistor, capacitor, bias and leakage assumptions remain explicit.

For the core strap example, 50 mm × 10 mm × 1 mm copper at the assumed 60 °C gives 0.09975064 mΩ. Adding the proposed 0.10 mΩ two-joint allocation leaves 0.30024936 mΩ of the unchanged 0.5 mΩ return limit for common feed, spreading and local return. This is a design allocation pending measured joint evidence, not an achieved resistance. DIN's 20 mΩ specified maximum does not guarantee the inherited rail/return limits; excluding it as the guaranteed main power path is appropriate. No equal parallel-contact sharing or positive/negative rail cancellation earns acceptance credit. Whole-device state maxima remain unknown, not zero.

Independently read exact selected-male manufacturer-authored data mirrored by RS (physical page 1 / printed 2 of 5), and retained exact female PDF using pypdf (physical pages 0, 1 and 3 / printed 1, 2 and 4 of 4). Both identify the selected MPNs and specify 2 A at 20 °C with derating, maximum 20 mΩ, maximum 90 N insertion/60 N withdrawal, at least 400 cycles, and no hot plugging. Mirror provenance is disclosed. Official selected-pair seating/drawing bytes are not retained; manufacturer table search extraction is candidate evidence only, not approved footprint or mating-tolerance verification. The dimensional/guide implementation must close that before component acceptance.

## Findings and dispositions

1. Initial missing-pin coding did not prevent reversed mating: a missing male pin alone fits an empty socket. Author removed that claim and retained all 96 contacts; separately polarized guides must stop wrong orientation before contact engagement. Exact manufacturer coding instructions additionally confirm that actual contact-loss coding needs a female coding pin and opposite male removal. RESOLVED design claim; guide geometry remains mechanical implementation acceptance.
2. Initial force/resistance values came from other variants and were described too strongly. Exact selected male and female documents now corroborate the values, with mirrored retrieval provenance and remaining seating uncertainty explicit. RESOLVED rating applicability; exact mounting/mating tolerance remains required.
3. Initial raw-wiper model omitted local 1 kΩ/10 MΩ/10 nF paths. Author added them and distinguished remote-only settling. RESOLVED within a conditional scalar model; full two-node response, actual bias/leakage/temperature and protection remain later verification.
4. Count-only checks initially accepted simultaneous net mutation on both faces and used assertions disabled by Python optimization. Author changed to explicit ValueError rejection against the source-bound interface contract. Independently exercised both-face mutation under Python -O successfully. RESOLVED. This depends on extract.py --check in the complete packet pipeline: equality to an on-disk contract alone is not independent live-source parity.
5. Initial revised path list omitted the shared middle-reference load despite calling itself complete. Requested an explicit shared source/rail/local-load/return path, charged once. Author added +12 V and -12 V shared-middle-reference paths, each retaining 26 mA planning allowance charged once per shared source and unknown state maxima. RESOLVED; reran all 10 tests and deterministic report check PASS.

## Verification and limitations

Initial independent run: test_revision_electrical.py, 10 tests PASS; revision_electrical.py --check PASS; additional optimized-Python both-face mutation rejection PASS. Recomputed copper remainder and all five raw-wiper filter assignments independently. pdftotext was unavailable in this WSL lane; pypdf successfully read the retained female evidence instead. Parent owns final complete packet, circuit:check and documentation checks.

Read the revised NEXT-PROMPT: it requests a distinct, isolated one-zone source/schematic/PCB implementation with exact parity, full electrical/mechanical acceptance and genuine separate native admission. It does not ask the owner again to specify every engineering dimension, and does not authorize fabrication, energization, adoption or merge. Publication must pin the actual reviewed source commit; placeholder replacement is metadata, not permission to change reviewed engineering.

**NOT RUN:** candidate CAD/route/ERC/DRC, native campaigns, contact/strap resistance under torque/temperature/ageing, load/fault/rail sequencing and injection tests, five-receiver stability/switching, warmup/calibration/tracking, adjacent operation or physical service qualification. No drawing or model pass substitutes for these. Keep #57/#59/#65/#247 and unmet #278–284 acceptance open.

## Initial revision review receipt (superseded by final closure receipt when present)

The following bytes were reviewed after the shared-reference path fix. Any subsequent route/fixture/model change needs a fresh closure review; this initial receipt is not final-state acceptance.

- `scripts/architecture278/revision_electrical.py`: `558086417329a802001802705bd6754380e741f120f4081fade4fcbd7cfa5d53`
- `scripts/architecture278/test_revision_electrical.py`: `93f16cf7dcf70d4b13e61b21f6f1ced7e12c6e224285dfb1b7d0134825e7b422`
- `design/architecture-278/revision-electrical-report.json`: `602e8d05272925e0f1c35a2b8e73dc5ad915c4ecc025daf0104466f015032e27`
- `design/architecture-278/revision-connectors.md`: `414bac63144d01033d0b9eb1b1c58dcf0e591bc92f73b6acea36d30255443495`
- `design/architecture-278/connector-source-receipt.json`: `f8cbcf4568b3075b2137896b55195da5b69c46b66783392966014f0493020870`
- `design/architecture-278/evidence/harting-09032966824-mirrored.pdf`: `978b11ceab4ffa9b0bf7661240a6b32eb54bec8197e8bf1f726761b88db0eed6`
- `design/architecture-278/interface-contract.json`: `1a96d576f5b33536014da093b6d0bf1e34b7ef5816dd1a35fb6d26465d4e656b`
- `design/architecture-278/NEXT-PROMPT.md`: `8cf19dba8c90d5bb4f79ca7e1ded2a375eaaf646c077c5a025f44515277511e6`

## Final route and checker review

The revised mapping conserves 51 original conductors through the reassigned DIN pins: independently checked all 96 pin labels unique, exactly 51 active, and every original rear-bound conductor's assigned net equal to the final pinout. Five intact receiver R_W packages move within the rear tile, rather than moving timing/summing/feedback circuits or adding front buffers. Ten O1/O2 coordinate-based raw-wiper allocations now include front trace, flex, middle distance/detour, connector developed length, rear Manhattan distance and fanout. The maximum is 295.96708681047653 mm for O2 PWM, leaving only 4.03291318952347 mm. This is an implementation allocation, not a measured or routed upper bound: panel centres are not pad coordinates, front-header placements and actual trace detours/tolerances must fit the declared allowances. Returns need the corresponding actual corridor and contact allocation. Capacitance is a separate requirement.

All 51 coarse transport length rows are now inventoried; 23 exceed 300 mm. These rows use retained proposed header banks and are not demonstrated compliant remote-control paths. Refined raw-wiper rows supersede their coarse estimates; the other applicable remote paths still require implementation routing/allocation closure. The 3060 mm proposed front wire total is 51 × 60 mm, not measured cutting length or a savings claim. The GATE and next implementation acceptance must preserve this limitation.

Independent final focused tests: 14 PASS. Read-only mutation of the mechanical O2 origin by +500 mm makes the electrical generator reject route overflow; it did not modify a file. Shared middle-reference +12/-12 V load paths each retain a 26 mA planning allowance exactly once, with actual state maxima null. The complete packet guard now runs six generators, including populated mechanics followed by revised electrical, so its source hash dependency is checked. A first full check during concurrent mechanical edits correctly failed on stale electrical output; final regeneration/recheck is recorded below rather than calling that failure a PASS.

The female PDF was moved to the ignored working cache under the project's publication policy. Independently verified its SHA256 remains 978b11ceab4ffa9b0bf7661240a6b32eb54bec8197e8bf1f726761b88db0eed6. The committed receipt retains URL/hash/physical and printed locators; the PDF is not committed or published. Offline model reproduction does not require that PDF. Exact official mating/drawing evidence remains a candidate-component implementation acceptance item.

## Final reviewed bytes and closure

After regeneration, `python3 scripts/architecture278/check_packet.py` PASS across all six generators and protected paths. GATE now explicitly rejects the 23 coarse overlength allocations and identifies the narrow refined-route margin. NEXT-PROMPT keeps full remote-path and physical acceptance open and separates stage authorization. Conditional recommendation stands; no remaining review finding requires pretending current electrical acceptance.

- `scripts/architecture278/revision_electrical.py`: `b933f5b5c511d1121513b755213ffa8fdcc46db01997f1d1d44b6a4be4dedf66`
- `scripts/architecture278/test_revision_electrical.py`: `c878ff8a7ad695a850637e7ef26f3e256784a1b934931e0fe6c34334b1228f85`
- `scripts/architecture278/check_packet.py`: `cca145e3cd2eb8594878206f04f4f2a814e0066273928090c02cf91c14ad3a69`
- `design/architecture-278/revision-electrical-report.json`: `b2b59b92d9088190a98045bf0054344f0681223a897a8233f95af69410139422`
- `design/architecture-278/revision-mechanical-report.json`: `a1b1c90589ec7005ff4d9a9d1dc41a8fb2fcd020daf0ca0d1687f9792a4b272a`
- `design/architecture-278/revision-connectors.md`: `3e3ef0235eca353379e553eea4a5536accb68bf98f00a7cd6da63c3cf7712cb7`
- `design/architecture-278/connector-source-receipt.json`: `910a26c3f670f02c2f3eb4a5c7126be9bd90b28ffe252fe4179e16730cc5537c`
- `design/architecture-278/interface-contract.json`: `1a96d576f5b33536014da093b6d0bf1e34b7ef5816dd1a35fb6d26465d4e656b`
- `design/architecture-278/GATE.md`: `50120bf2dae8a70db4c6e5873b14417f8ad1e9cfed3d8c0e2b6844292c018770`
- `design/architecture-278/NEXT-PROMPT.md`: `8937f7dd607f917bc05379f279207ac1320a7e5b6b5f6d1e11579449e263c2d0`

The NEXT-PROMPT source-checkpoint placeholder may be replaced with the actual immutable source commit after review; this narrow publication metadata replacement is permitted without representing different engineering as reviewed.

## Final functional regrouping, partial loads and orientation review

This closure supersedes the earlier 11/51/102 mixed-candidate recommendation and earlier source hashes where changed; the previous counts and failed allocations remain historical evidence. The recommended functional control regrouping now uses **11 harnesses / 54 conductors / 108 crimps**, including seven control links with all seven original AGND conductors and three additional reference branches (LOCAL_REF5 twice, LOCAL_REFN5 once). The checker uses multiset differences, not unique-net counts, so duplicated returns cannot disappear. Original 51-conductor transport accounting remains a separate preserved ledger. DIN still has 96 fitted positions, 51 assigned, and 192 solder joints; functional GH signal solder joints are now 108 plus 44 mechanical hold-down joints. Four-way GH identities are explicitly family-derived candidates requiring exact component evidence before production. No unchosen jack regrouping is included in those totals.

Independently joined the exact OPA packages from interface-contract parts and owner facts: front jack has two OPA4196IDR and one OPA4197IPWR; rear has four and three respectively; shared source has three OPA4197IPWR. At retained full-temperature no-output-load maxima, these contribute 8/22/18 mA per analog rail. These are useful supported partial components of demand, not full load-state maxima or AGND current. The revision-loads.md reconciliation correctly preserves 62.7/61.8/6 mA O1 planning allowance and shared 26/26 mA once; REF5050 and VEE5 are not counted again as fictional independent supplies. Quiescent data do not bound faults, startup or output load. Read the actual owner IQ facts and independently checked package counts rather than accepting the prose totals alone.

The source-derived U1110 whole-package/feedback/bypass cluster relocation and functional front grouping still leave **14 non-wiper allocations above 300 mm**, two on O1 and twelve on O2, with maximum 374.93113563741736 mm. Independently enumerated those rows. The old retained-bank comparison's 23 excessive rows remains historical; neither result is a passing interface. Ten raw-wiper coordinate allocations remain within 295.967 mm, subject to actual pads, header seating, trace detours and tolerances as previously noted.

Read orientation_sweep.py and the report. All eight O1/O2 cases transform connector and package coordinates together; the new test verifies unchanged rear-local Manhattan distances for quarter turns. All cases retain failures. O2 at 270 degrees reduces its count from 12 to 9 but worsens maximum allocation to 406.511 mm, so choosing it merely to reduce failure count would be misleading. Nineteen signal-by-signal 96-position searches are explicitly optimistic: they ignore mutually exclusive contact assignment and return pairing and are not an adopted pinout. They do not establish physical fit or justify relocating one component out of its circuit cluster. These bounded negative results identify a circuit-aware layout problem, not architectural impossibility; optimistic geometric lower bounds are not realizable routes.

Read final GATE and NEXT-PROMPT after these changes. Both retain the fourteen named failures and require whole-cluster placement/explicitly recounted jack-link regrouping before Stage 1 interface acceptance or onward routing/replication. The recommendation is permission to investigate a candidate in the separately authorized one-zone stage, **not a GO for an already workable electrical interface**. No owner choice is required merely to select every engineering parameter, and no physical qualification is claimed. The unresolved layout work is concrete and recoverable.

An additional checker finding was raised: fixed connector coordinates, board width/height and depth could silently diverge from changed mechanical inputs. The author must derive those coordinates or explicitly reject an unsupported configuration; final disposition and exact bytes follow.

## Latest closure receipt — supersedes earlier changed-file receipts

Geometry mismatch finding RESOLVED: the electrical comparison now explicitly rejects unsupported tile dimensions, connector box, middle/core depth and invalid/out-of-range stack tolerance before any route/orientation calculation. This is a deliberately bounded geometry contract, not a claim of general parametric support. Author added connector-bank, tile and stack mutations. Independently reran **19 electrical tests PASS**, the **seven-generator packet/protected-path check PASS**, nonfinite/boolean/negative tolerance rejection under optimized Python PASS, and the functional-net multiset conservation check with assertions enabled PASS. No production, native or physical work ran.

Exact final engineering files reviewed:

- `scripts/architecture278/revision_electrical.py`: `6cd007221b0b1be182ecbe9e46b371de14ccd9bd53c8e2fcb3e670ea8a63a321`
- `scripts/architecture278/test_revision_electrical.py`: `b77680005b307cc678ed85bac6b93f091b4377c1e5eb100e097548ffcc6c77a3`
- `scripts/architecture278/orientation_sweep.py`: `8e269c7870b0bdd773c7404c1e6deca530487329c91f363c3e2bbaba0ec32497`
- `scripts/architecture278/check_packet.py`: `206f683fb279215c996494a25fa3983351f53ec98329b390e8d7f36ac1a7450b`
- `design/architecture-278/revision-electrical-report.json`: `003eb7234951a1cc4fb5386c994614c71408248f64d716e09db9c3aec70fca26`
- `design/architecture-278/revision-orientation-report.json`: `aa251d4deaa5d64496fcb48cd761a7332191ba527e0b708e4b91d2aeea63a278`
- `design/architecture-278/revision-mechanical-report.json`: `43e0023e80951181d0006ef82e9c1f1523e5975a70e8357fe373b2e25aa79c6d`
- `design/architecture-278/revision-connectors.md`: `f48c9417f172557652f8e10659f686449236a0497c110ffcc8fa016b3b67b752`
- `design/architecture-278/revision-loads.md`: `92c5656a43ad49c72fe614eecac368b49f8e8d8772c025f3895e0302b7980546`
- `design/architecture-278/connector-source-receipt.json`: `910a26c3f670f02c2f3eb4a5c7126be9bd90b28ffe252fe4179e16730cc5537c`
- `design/architecture-278/interface-contract.json`: `1a96d576f5b33536014da093b6d0bf1e34b7ef5816dd1a35fb6d26465d4e656b`
- `design/architecture-278/GATE.md`: `64fdf33171834c60153a8368b41e2cb216cc081cf84bab09c35292f0bf44f36f`
- `design/architecture-278/NEXT-PROMPT.md`: `635c46c136e9becc3f16b3eb6902d1a71e5791cfcec83c05ee6c3047657ffe12`

Scope remains conditional authorization recommendation for further one-zone engineering, with fourteen named route violations requiring closure before implementation acceptance. The final publication may substitute the real immutable source SHA for NEXT-PROMPT's source-checkpoint placeholder only; it may not silently change these engineering inputs.
