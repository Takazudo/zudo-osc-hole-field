# Next engineering intervention — source-only assessment

Source: execution SHA `9f69cd8a2e7b80cba813a5bd66546c4d5ac705ec`. This review read completed attempt-4 service output, retained t2 residual atlases, long-B construction/evaluation, feed-remedy proposal/rejection witnesses, and source-dependency records. No geometry generation, native call, numerical solve, source edit or adoption was performed. Exact service hash, candidate identities/coordinates and evidence hashes are in adjacent `engineering-candidate-analysis.json`.

The newly completed service unit confirms 151 supported, 59 partial, 21 unserved, and 194 unmapped devices. Included signed current is KA +12V/+5V/-12V/AGND = +94.16/+0.06/-94.16/-0.06 mA; KB = +77.44/+1.18/-77.44/-1.18 mA. These are the declared whole-device quiescent/static subset, not instrument consumption. Each partial device has its complete package current excluded. This is structural/load-accounting evidence, not a coupled numerical PASS. At inspection, only service and first two reduction step receipts existed; no attempt-4 coupled electrical result was used.

## Preferred partial-device target: KA U2314

Exact device: Texas Instruments OPA4196IDR, SOIC-14, LCSC C2057385, F3 audio op-amp package U2314. Its supported ±12 V quiescent rows are already in the normal-typ-v1 ledger, ±0.56 mA total package current (140 uA × four amplifiers; output current omitted). +12 V pin 4 (`8df78f33-5fd1-51c4-9ed7-e810ba473573`) is served; -12 V pin 11 (`b0f9dbc5-d3f3-5380-a8d2-0fe230e28db0`) is not. Completing only this missing supply path would make one whole supported package eligible without inventing loads.

The -12 V orphan component also contains C2342.1 (`2412205a-2a0a-5aa6-b8ef-6c883912d2b4`) and access vias `19a8d3d3-d974-5b5c-9ad6-2feb6a732bf8` / `777f3632-457b-52cb-905e-d88ee0abe7f4`. They land on isolated `KA--12V-SHEET-0068`, area 6.883 mm². Its gap to fed In3 sheet is 0.2772 mm. The named blocker is AGND via `1e1b90ef-f82d-5e94-a82e-416153b33ef3` at (110.245,184.97), 0.6/0.3 mm, facing the two In3 signal segments `127141f3-ffb2-55dd-82f8-f83de6cb72d8` and `d3ddf061-51ab-594f-8345-7661bfd81e93` on X91D7FB7B3C74A3368139.

An additive candidate already exists: `continuation-20261013b/ka-longb/`, exact source digest `666b20da1158b86fae495ce54fb200c060368ce416e4e73d76d4d4d150fc3ccd`. It preserves 73,699 old objects and adds 15 B.Cu segments, width 0.2 mm, length 23.554079825569 mm. It joins the orphan via to C1249.1 (`6804d6f9-488d-54ac-9189-87ecc94e7363`). Retained complete census credits exactly U2314.11 and C2342.1, KA196→194, zero newly disconnected. This source candidate is distinct from baseline and has no corrected finite coverage/numerical/native acceptance.

Do not promote that long-B route as a successful electrical remedy: the independently retained isolated-strip screen is 34.732 mΩ, versus the existing 1 mΩ copper requirement. This is an analytic screening calculation, not a solved full-path result or formal lower bound. Its minimum clearance margin is only 0.000615 mm above the 0.25 mm source rule. Lower injected current cannot turn those concerns into resistance acceptance.

The better geometric mechanism is a short In3 sheet reconnection at the named gap. Retained source re-clipping shows selectively removing the named AGND via's nonfunctional In3 annulus can join the island (0.813 mm available versus 0.75 mm required); the present source/materialization adapter cannot represent/prove it. Moving the via or changing original padstack/copper is outside this campaign. Thus the bounded follow-up is an explicitly separate, source-owned one-via padstack experiment with exact barrel/functional-annulus preservation fixtures, native-adapter round-trip capability evidence, and full graph/census comparison before any adoption. No such change is authorized or executed here. Do not launch the existing high-resistance long route merely to obtain a green connectivity number.

Expected measurable objectives for the one-package intervention: exact closure of the two named pads; zero new disconnections; both actual finite supply paths present; supported devices 151→152 and partial 59→58 if all other groups remain unchanged; inclusion of balanced +0.56/-0.56 mA only after coverage; unchanged numerical tolerances; measured copper/full-path resistance against unchanged targets. Native DRC, process/padstack qualification, physical source/protection and installed fit remain separate required gates.

## Immediately bounded additive alternative: existing KA seven-via feed candidate

If corrected baseline confirms a receiving-land transfer bottleneck, the already source-owned `feed-parallel-vias` candidate is the narrow next additive comparison: source digest `894cc6b211a50d0c3d79bc6300317202a189e42f06140797643901a4212fe16b`. It adds exactly seven 0.6/0.3 mm through vias at fixed receiving lands, preserving all 73,699 old objects and the exact KA196 residual identities. It is also exactly the retained combined candidate; wider-face proposals add nothing, so these are not three independent designs worth rerunning.

| Land | Net | Added via centres (mm) |
| --- | --- | --- |
| TP990026 | +12V | (141,175) |
| TP990028 | -12V | (158,175), (160,175) |
| TP990030 | +5V | (175,175), (177,175) |
| TP990032 | AGND | (192,175), (194,175) |

All UUIDs and pad identities are in the JSON companion. TP990026's other site was rejected for obstruction and cumulative sheet severance; TP990034/TP990036 sites and face routes remain rejected. Do not search substitutes or drop those negative records. The candidate has full source graph/census preservation evidence, but variant finite coverage is NOT RUN and full-path resistance NOT ESTABLISHED. Additional drill antipads can alter other sheet resistances even without disconnection, so electrical improvement is an expectation to measure, not a monotonicity guarantee.

Mechanism: parallel barrels can reduce local pad-to-sheet transfer resistance without moving lands, introducing terminals or changing loads. A future exact candidate comparison should measure affected receiving-land transfer resistance, per-net copper resistance maxima, equal-load voltage drop/return sharing and dissipation, with unchanged acceptance and resource limits; reject any new coverage loss or resistance regression. No percentage improvement is invented here. This is a new geometry variant campaign, outside the current baseline numerical authorization, and must not run now.

## Remaining boundary

Neither local intervention supplies the missing physical source: CN301/XB301 have no footprint, no BOM population and no implemented raw-to-load bridge. The P-side conductor, actual POWER-P-* source wire/end geometry, complete source-to-load return operator and process-qualified caps/plating remain open. All 380 inherited GH conductors retain unevaluated current/compliance. The baseline's corrected electrical results must remain tied to their actual source support assumptions, supported load subset and completed cases/states. Previous failed numerical values and historic partial-model results have not been used as trustworthy current performance figures.

KEEP_K1402_INCUMBENT, canonical boards/copper, locked panel positions, electrical targets, loads, manufacturing rules and decision.json remain unchanged. These are next-step definitions, not adopted or validated boards.
