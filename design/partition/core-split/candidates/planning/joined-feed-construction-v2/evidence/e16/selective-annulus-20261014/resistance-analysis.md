# Retained attempt-5 resistance diagnosis and next intervention

This is read-only engineering analysis of execution `852ffac7f85aff4bb436eb25f7ce993cee48146b`, request `ef0213b3b38f4de23804ad192043b082d8e1b2be3086c5e20e4343afea4052d6`. No new geometry, native work, finite coverage or numerical solve was executed. Numerical accuracy passed for the retained inputs; copper compliance failed throughout the evaluated loaded population. The narrowest energy check has only 0.28005% headroom below its unchanged limit. That PASS does not transfer to changed inputs or platforms.

`resistance-loaded-ranking.csv` ranks every retained loaded observation by copper-budget exceedance, with board, net, exact Ref/pin/UUID, package, service/mapping class, signed current, case, return state, allowance, copper resistance, driving-point resistance and source-relative potential. `resistance-analysis.json` retains the 302 distinct loaded pads at their worst state, all 60 board/net/case/state summaries, aggregate energy, same-pad return-removal differences, excluded device identities, local transfer evidence and verified input sizes/hashes. The helper checks exact retained bindings and performs arithmetic only; it is outside test discovery and never unpickles solver outputs.

## Ranking and meaning

The 1 mΩ rail and 0.5 mΩ common-AGND allowances are charged once over the defined path, including both boards; they are not refreshed at the second board. Driving-point copper resistance describes the bound network's unit-current response with non-copper contributions separated by the existing method. Simultaneous-load source-relative voltage includes all included currents; it is not resistance multiplied by one package current, rail-to-local-ground error, or full source/load/return acceptance.

| Rank | Board / net | Ref.pin (package; mapping) | Case / return | Allowance mΩ | Copper mΩ | Ratio |
| ---: | --- | --- | --- | ---: | ---: | ---: |
| 1 | KB / +5V | U4330.14 (SN74HC74DR; conditional) | sensitivity-thin / all-present | 1.0 | 28.872051 | 28.872× |
| 2 | KA / +5V | U1107.14 (SN74HC14DR; conditional) | sensitivity-thin / all-present | 1.0 | 28.485242 | 28.485× |
| 3 | KB / -12V | U4541.11 (OPA4197IPWR; supported) | sensitivity-thin / all-present | 1.0 | 24.110590 | 24.111× |
| 4 | KB / AGND | U4138.7 (SN74HC74DR; conditional) | sensitivity-thin / remove-W5-W6 | 0.5 | 11.992663 | 23.985× |
| 5 | KA / -12V | U1415.11 (OPA4196IDR; supported) | sensitivity-thin / all-present | 1.0 | 22.391096 | 22.391× |
| 6 | KA / AGND | U1407.7 (SN74HC14DR; conditional) | sensitivity-thin / remove-W4-W5 | 0.5 | 8.174565 | 16.349× |
| 7 | KB / +12V | U7105.4 (OPA4197IPWR; supported) | sensitivity-thin / all-present | 1.0 | 9.261726 | 9.262× |
| 8 | KA / +12V | U1510.4 (OPA4197IPWR; supported) | sensitivity-thin / all-present | 1.0 | 7.380137 | 7.380× |

These are the worst loaded observations for each board/net, ranked across all three cases and applicable finite return states. All have whole-device service status supported; conditional logic mapping is kept distinct from primary-supported op-amp quiescent mapping. Full UUIDs and each individual state are in the companion files.

Every loaded observation exceeds its applicable allowance. The highest loaded ratios occur in +5V, then thin-case -12V and return-degraded AGND. Low logic currents explain the small source-relative voltages; those voltages do not waive the resistance criterion. Unloaded maxima identify possible next problems but do not imply those pads were energized. All-pad and loaded maxima remain separate in the JSON.

## Shared and local contributions

For nominal all-present loading, KA +12V barrel dissipation is 14.068585 µW, versus 21.149607 µW total KA copper dissipation: 66.519%. This establishes a *class-level* concentration under that simultaneous-load vector. It does not establish which via dominates a particular driving-point resistance. +5V instead concentrates in inner copper: KA 77.56% and KB 97.23% of their copper dissipation. A +12V land repair should therefore not be presented as the general remedy for the worst +5V pads.

The finite AGND removal comparisons are a valid controlled network perturbation: same geometry/process and loads, but named W4/W5/W6 conductors removed. Compare each exact pad with itself, not maxima from different pads. The JSON records those deltas. The largest loaded same-pad copper increase is 0.471430 mΩ for KB pad `448df9e2-d06c-5225-b7b4-624a2e687b34` in sensitivity-thin, remove-W5-W6 versus all-present (0.943× the common-AGND allowance). These demonstrate shared-return sensitivity while preserving the substantial all-present copper failure. Removing all three returns is structurally open and has no finite result.

The retained 85 mm interboard wire model has 1.105 mΩ bulk plus 0.075953 mΩ for both terminations. Its 110 mm sensitivity adds 0.325 mΩ bulk. Those modeled non-copper sections are not part of a fresh per-board copper allowance. The absent inlet, star, raw/load bridge, actual source conductors, output loading and returns are unquantified, not zero-cost.

An additive series-path decomposition of the parallel copper network would be invalid. Retained JSON provides board/class Joule energy, not object-level unit-current energy. To causally rank individual necks and vias for a chosen driving-point target, admit a bounded diagnostic that uses its exact unit-current solution to report E_e = I_e² R_e by physical object/interval, with interface current balance and total energy reconciliation. Such a diagnostic must preserve the same operator, source support, process, loads where applicable and normalization; it is not authorized by this report. For a fixed linear network, the local derivative dR_eff/dr_e = (i_e/I)² supports sensitivity attribution. Large changes or new drill antipads require a fresh operator; they cannot be predicted by blindly adding isolated strip resistances.

## Prioritized dimensioned intervention: TP990026 transfer branch

The next *resistance* intervention is a tightly bounded TP990026 +12V transfer comparison, separate from the U2314 selective-annulus connectivity candidate. It targets an actual demonstrated local access resistance. It is not asserted to be the dominant whole-network bottleneck or a compliance fix.

The retained KA +12V descriptor has SHA-256 `68fb68123c03d6820cef569f913296801ef95d4c37ada410b6de2d7dbb03dba7`, matching the attempt-5 coverage binding. TP990026 pad `4837930f-294a-5712-878f-44a71b63bce6`, centered at (142,175) mm, occupies only F.Cu group 41. That group contains only the land and centered via `87d2de81-b7e7-5e5c-9063-52b28f51939e`; this via is its sole barrel connection. Its In1/In2/In3 annuli and B.Cu end are leaf groups containing only that via. Its functional sheet exit is In4.Cu. This is a real single-barrel F-to-In4 transfer branch in the retained topology. It is not a claim that this branch lies in series with every load: the model also holds TP990002 and TP990014 equipotential as separate +12V sources.

Propose exactly the already retained additional through via `4cf6b906-bc79-5bcb-b06f-fe661ad1242f` at (141,175) mm, outer diameter 0.6 mm, finished drill 0.3 mm, net +12V. Keep the existing (142,175) via, fixed 4×4 mm land, all original geometry and contacts. The two centers are 1 mm apart; the new via's outer edge lies 0.7 mm inside the left edge of the land. The opposite (143,175) proposal was rejected for obstruction/cumulative sheet severance and must not be substituted or retried by search.

Under the exact retained uniform-dielectric assumption, F-to-In4 foil-center distance is 4×(0.236+0.070)=1.224 mm. For finished drill d=0.3 mm, plating p and resistivity ρ, axial barrel R = ρL/[π((d/2+p)²−(d/2)²)]. Two identical barrels with equal end potentials halve this *barrel term*. The numerical table in the JSON evaluates all three retained process cases. Face/cap/contact and plane spreading are not set to zero in the physical proposal; they are outside this barrel-only calculation and need explicit extraction or supported bounds.

| Process case | Plating µm | One barrel mΩ | Two equal barrels mΩ |
| --- | ---: | ---: | ---: |
| nominal-average | 18 | 1.405160 | 0.702580 |
| sensitivity-thin | 10 | 2.890664 | 1.445332 |
| legacy-conditional-requirement | 25 | 1.102900 | 0.551450 |

Nominal barrel-only resistance is about 1.405 mΩ for one and 0.703 mΩ for two. Thin sensitivity is about 2.891 mΩ for one and 1.445 mΩ for two; even the ideal doubled barrel term alone exceeds the entire 1 mΩ rail allowance in that case. Thus the exact one-via addition is a mechanism test, not a credible standalone path-compliance promise. No additional via site, enlarged drill, changed plating guarantee or new equipotential extension is silently assumed. A favorable nominal local result cannot select the architecture.

Admission and validation must first compare this exact retained local topology with object-level currents/energy, then independently review the one-addition source proposal. A separately admitted candidate must preserve original UUIDs, exact census groups and every source boundary; regenerate affected sheets/finite coverage; measure the land's local transfer and target-pad driving-point resistance with the same source supports; reevaluate all nets affected by drill antipads and every applicable process/return state; reconcile native geometry/DRC completely. Extra drill antipads may worsen other nets even with zero new disconnected pads. Filled/capped process and plating assumptions remain physically unqualified. No source or candidate is modified by this proposal.

## Seven-via hypothesis and retained negative alternatives

The retained seven-via source candidate adds the one TP990026 via above, two at TP990028 (-12V, (158,175)/(160,175)), two at TP990030 (+5V, (175,175)/(177,175)), and two at TP990032 (AGND, (192,175)/(194,175)); all are 0.6/0.3 mm. Exact UUIDs remain in `campaign-wsl-20261014/engineering-candidate-analysis.json`. Its retained source census preserves KA196 and all original 73,699 objects. Wider-face and combined proposals did not provide independent successful alternatives. Their rejected TP990034/TP990036 sites and face paths remain negative.

The seven-via bundle has neither fresh finite coverage nor a solved resistance comparison. The demonstrated TP990026 local branch and class energy justify a narrow diagnostic, not global seven-via acceptance. Each extra barrel can only be credited against its actual parallel transfer path, with all antipad changes re-extracted. No percentage reduction in worst-pad resistance is claimed.

KA long-B remains a distinct negative control: 15 B.Cu segments, 0.2 mm wide, 23.554079825569 mm long, connecting via `19a8d3d3-d974-5b5c-9ad6-2feb6a732bf8` to C1249.1 `6804d6f9-488d-54ac-9189-87ecc94e7363`. It closed U2314.11/C2342.1 structurally (KA196→194; zero newly disconnected), but the retained isolated-strip nominal screen is 34.732173 mΩ versus 1 mΩ. That is a screening estimate, not an additive full-path resistance or formal lower bound. The minimum clearance margin above the 0.25 mm rule is only 0.000615 mm. Small voltage drop at ±0.56 mA cannot make this a resistance success. Prior KA long-B194 and KB-P1 480 remain separate from the new selective-annulus proposal.

## Ranked unresolved load and interface work

1. **Physical source/protection and return realization:** CN301/XB301 lack implemented footprint/BOM/raw-to-load bridge; actual P-side and POWER-P source conductor/end geometry remain absent. Their realization changes boundary conditions, so even a locally successful via cannot settle the architecture. Keep protection/return-integrity obligations and factory-complete assembly requirements open.
2. **Unmapped device classes (194):** 102 SN74HC00DR, 24 REF5050AIDR, 24 LM393BIDR, 16 LM13700M_NOPB, 12 ADG5412FBRUZ, 8 CD74HC221M96, 5 AS3340D, 2 LF398M_NOPB, 1 NOISE2. KB holds 160 and KA 34. Reference/current-sensitive and derived-rail devices are high priority for valid source/return modeling; the large logic population is high priority for omitted +5V demand. Counts do not rank amperes: no supported magnitude order is available. Exact pin/current/source and operating-state evidence is required before mapping; no new mapping is asserted here.
3. **Partial and unserved supported packages:** 59 partial (28 OPA4197IPWR, 19 SN74HC74DR, 8 OPA4196IDR, 4 SN74HC14DR) and 21 unserved (9 OPA4197IPWR, 8 SN74HC74DR, 3 OPA4196IDR, 1 SN74HC14DR). KA has 14 partial/4 unserved; KB 45/17. The JSON lists every excluded device and missing pins. U2314 is prioritized by exact supported repair evidence, not presumed largest current: its existing ±0.56 mA pair enters only after both supply paths are proven. Larger-current op-amp packages merit subsequent topology-guided prioritization; no package is split or counted twice.
4. **GH and dynamic/passive loads:** all 380 inherited GH conductors remain unevaluated in this E16 model, including the 333 powered core/front and 47 peripheral conductors. The joined handoff's separate conditional return calculations do not transfer to unimplemented access geometry. EL module ceilings are not per-pad injections. Output loads, passive rail paths, transistor/diode/LED currents and dynamic logic are not covered by this quiescent/static subset. Uniform module-total spreading would manufacture evidence and is prohibited.
5. **Local-ground and complete paths:** rail-source potentials do not assign package return locations. Complete source/load/return pairing, wire/contact/termination losses, open-return behavior and 20 mV/0.5 A conductor criteria remain separate; all-three-AGND-open stays structurally singular. Native completeness, process/stackup qualification, mechanical fit and bench qualification remain open.

The retained supported subset is KA +94.16/+0.06/−94.16/−0.06 mA and KB +77.44/+1.18/−77.44/−1.18 mA for +12V/+5V/−12V/AGND. It is not instrument consumption. The expected selective-annulus change, if later admitted and proven, adds the same U2314 package once: +0.56 and −0.56 mA; current evidence remains 151 supported, 59 partial, 21 unserved, 194 unmapped, 302 eligible pads, KA196/KB486 unresolved. No changed-geometry results are claimed.

## Reproduction, storage and boundary

Run the adjacent `resistance-report.py.txt` from the repository root to regenerate only this report's JSON/CSV from retained JSON/GZIP evidence. It asserts the original summary, service, load ledger, all 12 coupled outputs, local descriptor/coverage and retained negative-evidence hashes. Its input index records exact byte lengths and SHA-256. Original outputs, requests, negative attempts and pickles remain untouched. Recover any absent originals using `campaign-wsl-20261014/attempt5/index.json` and the campaign README; do not rerun a baseline to regenerate missing files.

No native/numerical unit or heavy slot was requested or consumed by this analysis. Campaign consumption remains 2/3 full baselines and 8/24 diagnostics. The proposed resistance experiment needs a separate exact admission; unused quota supplies no authority. KEEP_K1402_INCUMBENT, canonical boards, accepted copper, all fixed panel centers, 33 modules, circuit/harness identities and `decision.json` remain unchanged. Independent report review is recorded by the task owner separately; the arithmetic helper's assertions are self-checks, not independent engineering approval.
