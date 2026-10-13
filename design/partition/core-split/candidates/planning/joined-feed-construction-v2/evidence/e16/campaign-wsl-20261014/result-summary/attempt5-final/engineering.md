# E16 baseline engineering assessment

Snapshot observed 2026-10-13T22:21:10.658977+00:00; summary SHA-256 `8df092b5f3e6a9a1e28f3f09ebfc17e965b7379ec4861796221eb5c7849a03cd`.
Execution source `852ffac7f85aff4bb436eb25f7ce993cee48146b`; request `ef0213b3b38f4de23804ad192043b082d8e1b2be3086c5e20e4343afea4052d6`.

Numerical full baseline complete: **True**. TERMINAL; 148/148 serialized units, 12/12 net/case combinations and 30/30 finite states. A partial snapshot cannot establish the remaining combinations or terminal cleanup.

**Electrical acceptance is not established.** Numerical residual tests assess solution accuracy; copper limits independently assess this conditional electrical model.

## Execution and numerical accuracy

Integrity errors: 0; numerical failures: 0. Guard-pass receipts: 148; max reported RSS 2061976 KiB; max solver elapsed 93.14 s. Each production unit remains bounded at 180 seconds, 2 GiB memory and zero swap. Independent owned-process cleanup must be reported separately.

| Numerical check | Maximum observed | Fixed limit | Step |
| --- | ---: | ---: | --- |
| couple.all-present.driving_point_solve_residual | 1.84702721635e-12 | 1e-09 | couple-AGND-sensitivity-thin-uniform-dielectric |
| couple.all-present.energy_minus_load_work_relative | 9.97199476829e-10 | 1e-09 | couple-+5V-legacy-conditional-requirement-uniform-dielectric |
| couple.all-present.global_kcl_relative | 3.7566066409e-10 | 1e-09 | couple-+5V-legacy-conditional-requirement-uniform-dielectric |
| couple.all-present.max_free_node_kcl_relative | 4.19360064155e-11 | 1e-09 | couple-AGND-legacy-conditional-requirement-uniform-dielectric |
| couple.remove-W4-W5.driving_point_solve_residual | 1.84702721635e-12 | 1e-09 | couple-AGND-sensitivity-thin-uniform-dielectric |
| couple.remove-W4-W5.energy_minus_load_work_relative | 3.12515877693e-10 | 1e-09 | couple-AGND-legacy-conditional-requirement-uniform-dielectric |
| couple.remove-W4-W5.global_kcl_relative | 5.58994529932e-10 | 1e-09 | couple-AGND-sensitivity-thin-uniform-dielectric |
| couple.remove-W4-W5.max_free_node_kcl_relative | 3.25331384602e-11 | 1e-09 | couple-AGND-legacy-conditional-requirement-uniform-dielectric |
| couple.remove-W4-W6.driving_point_solve_residual | 1.84702721635e-12 | 1e-09 | couple-AGND-sensitivity-thin-uniform-dielectric |
| couple.remove-W4-W6.energy_minus_load_work_relative | 3.17838824494e-10 | 1e-09 | couple-AGND-legacy-conditional-requirement-uniform-dielectric |
| couple.remove-W4-W6.global_kcl_relative | 5.67885862103e-10 | 1e-09 | couple-AGND-sensitivity-thin-uniform-dielectric |
| couple.remove-W4-W6.max_free_node_kcl_relative | 4.44586374624e-11 | 1e-09 | couple-AGND-nominal-average-uniform-dielectric |
| couple.remove-W4.driving_point_solve_residual | 1.84702721635e-12 | 1e-09 | couple-AGND-sensitivity-thin-uniform-dielectric |
| couple.remove-W4.energy_minus_load_work_relative | 2.12489228052e-10 | 1e-09 | couple-AGND-legacy-conditional-requirement-uniform-dielectric |
| couple.remove-W4.global_kcl_relative | 3.44939270919e-10 | 1e-09 | couple-AGND-sensitivity-thin-uniform-dielectric |
| couple.remove-W4.max_free_node_kcl_relative | 4.44586374624e-11 | 1e-09 | couple-AGND-nominal-average-uniform-dielectric |
| couple.remove-W5-W6.driving_point_solve_residual | 1.84702721635e-12 | 1e-09 | couple-AGND-sensitivity-thin-uniform-dielectric |
| couple.remove-W5-W6.energy_minus_load_work_relative | 3.36677073979e-10 | 1e-09 | couple-AGND-legacy-conditional-requirement-uniform-dielectric |
| couple.remove-W5-W6.global_kcl_relative | 6.06366470532e-10 | 1e-09 | couple-AGND-sensitivity-thin-uniform-dielectric |
| couple.remove-W5-W6.max_free_node_kcl_relative | 4.44586374624e-11 | 1e-09 | couple-AGND-nominal-average-uniform-dielectric |
| couple.remove-W5.driving_point_solve_residual | 1.84702721635e-12 | 1e-09 | couple-AGND-sensitivity-thin-uniform-dielectric |
| couple.remove-W5.energy_minus_load_work_relative | 2.13295568005e-10 | 1e-09 | couple-AGND-legacy-conditional-requirement-uniform-dielectric |
| couple.remove-W5.global_kcl_relative | 3.44745338627e-10 | 1e-09 | couple-AGND-sensitivity-thin-uniform-dielectric |
| couple.remove-W5.max_free_node_kcl_relative | 3.02145316933e-11 | 1e-09 | couple-AGND-legacy-conditional-requirement-uniform-dielectric |
| couple.remove-W6.driving_point_solve_residual | 1.84702721635e-12 | 1e-09 | couple-AGND-sensitivity-thin-uniform-dielectric |
| couple.remove-W6.energy_minus_load_work_relative | 2.240488197e-10 | 1e-09 | couple-AGND-legacy-conditional-requirement-uniform-dielectric |
| couple.remove-W6.global_kcl_relative | 3.67615009614e-10 | 1e-09 | couple-AGND-sensitivity-thin-uniform-dielectric |
| couple.remove-W6.max_free_node_kcl_relative | 3.25839608009e-11 | 1e-09 | couple-AGND-legacy-conditional-requirement-uniform-dielectric |
| dpoint.solve_residual_relative | 1.84702721635e-12 | 1e-09 | KA-dpoint-AGND-sensitivity-thin-uniform-dielectric-003 |
| reduce.interface_solve_residual_relative | 1.24097184795e-13 | 1e-09 | KA-reduce-+12V-legacy-conditional-requirement-uniform-dielectric |
| reduce.load_solve_residual_relative | 1.10491812262e-11 | 1e-09 | KB-reduce-+5V-nominal-average-uniform-dielectric |
| reduce.reciprocity_relative | 1.02386777058e-13 | 1e-09 | KB-reduce-+5V-nominal-average-uniform-dielectric |

## Electrical scope and exact budgets

One whole-path allowance is shared across both boards; it does not restart per board. Rail copper limit is 1 mΩ; common AGND copper limit is 0.5 mΩ. The 20 mV path allowance and 0.5 A GH-conductor requirement are not demonstrated by a source-relative rail potential.

Exact bound configuration budgets: `{"agnd_copper_ohm": 0.0005, "application": "Charged once over the modelled KA+wire+KB path; the unmodelled inlet/star, branch and protection copper must fit in the same allowance, so a modelled value within budget is necessary, not sufficient.", "gh_conductor_A": 0.5, "path_error_V": 0.02, "rail_copper_ohm": 0.001, "source": "design/partition/core-split/power/contract.json conductor_screen.global_budget and power/joined/handoff.md: one global 20 mV path allowance, 1 mOhm rail and 0.5 mOhm common AGND copper, never restarted per board; 0.5 A per GH conductor."}`.

Device groups: `{"partial": 59, "supported": 151, "unmapped": 194, "unserved": 21}`; eligible supply pads: 302. Whole-device gating excludes partial/unserved groups. Unmapped groups have unsupported load mappings; counts do not represent an all-device current total.

Included signed board/net currents (A): `{"KA": {"+12V": 0.09416, "+5V": 6e-05, "-12V": -0.09416, "AGND": -6e-05}, "KB": {"+12V": 0.07744, "+5V": 0.00118, "-12V": -0.07744, "AGND": -0.00118}}`.

Counts below are observations for one net/case/state, not distinct physical identities accumulated across cases. “Loaded” means included in the declared load subset; all-pad maxima can identify unenergized pads.

| Net | Case | State | Board | Budget mΩ | All pads over / evaluated | Loaded over / evaluated | Max all mΩ | Max loaded mΩ |
| --- | --- | --- | --- | ---: | ---: | ---: | ---: | ---: |
| +12V | legacy-conditional-requirement | all-present | KA | 1 | 274/275 | 76/76 | 5.302948473130239 | 5.302948473130239 |
| +12V | legacy-conditional-requirement | all-present | KB | 1 | 250/250 | 40/40 | 6.769985682480797 | 6.03536482317546 |
| +12V | nominal-average | all-present | KA | 1 | 275/275 | 76/76 | 5.174020386507961 | 5.003293921822727 |
| +12V | nominal-average | all-present | KB | 1 | 250/250 | 40/40 | 6.48095296289586 | 5.9921452927738486 |
| +12V | sensitivity-thin | all-present | KA | 1 | 275/275 | 76/76 | 8.145953652090807 | 7.380137074493637 |
| +12V | sensitivity-thin | all-present | KB | 1 | 250/250 | 40/40 | 9.89708281222026 | 9.261725770223796 |
| +5V | legacy-conditional-requirement | all-present | KA | 1 | 24/24 | 3/3 | 23.05397731413559 | 23.05397731413559 |
| +5V | legacy-conditional-requirement | all-present | KB | 1 | 398/398 | 32/32 | 23.12979004915616 | 21.920533758999603 |
| +5V | nominal-average | all-present | KA | 1 | 24/24 | 3/3 | 21.105600306546222 | 21.105600306546222 |
| +5V | nominal-average | all-present | KB | 1 | 398/398 | 32/32 | 21.204675563292895 | 20.534034276571568 |
| +5V | sensitivity-thin | all-present | KA | 1 | 24/24 | 3/3 | 28.485241696866964 | 28.485241696866964 |
| +5V | sensitivity-thin | all-present | KB | 1 | 398/398 | 32/32 | 29.539192505917548 | 28.872050771399127 |
| -12V | legacy-conditional-requirement | all-present | KA | 1 | 201/201 | 76/76 | 18.150621710368036 | 18.150621710368036 |
| -12V | legacy-conditional-requirement | all-present | KB | 1 | 146/146 | 40/40 | 19.19272960431854 | 19.19272960431854 |
| -12V | nominal-average | all-present | KA | 1 | 201/201 | 76/76 | 16.60692318739169 | 16.60692318739169 |
| -12V | nominal-average | all-present | KB | 1 | 146/146 | 40/40 | 17.67366643151428 | 17.67366643151428 |
| -12V | sensitivity-thin | all-present | KA | 1 | 201/201 | 76/76 | 22.39109621092611 | 22.39109621092611 |
| -12V | sensitivity-thin | all-present | KB | 1 | 146/146 | 40/40 | 24.110590211550196 | 24.110590211550196 |
| AGND | legacy-conditional-requirement | all-present | KA | 0.5 | 849/849 | 3/3 | 13.371337529647336 | 5.582133840838536 |
| AGND | legacy-conditional-requirement | all-present | KB | 0.5 | 995/995 | 32/32 | 17.18682173600259 | 8.431117714981827 |
| AGND | legacy-conditional-requirement | remove-W4 | KA | 0.5 | 849/849 | 3/3 | 13.371366251575374 | 5.58214100217328 |
| AGND | legacy-conditional-requirement | remove-W4 | KB | 0.5 | 995/995 | 32/32 | 17.221357245444075 | 8.461993012903356 |
| AGND | legacy-conditional-requirement | remove-W4-W5 | KA | 0.5 | 849/849 | 3/3 | 13.37139973857765 | 5.582147759568734 |
| AGND | legacy-conditional-requirement | remove-W4-W5 | KB | 0.5 | 995/995 | 32/32 | 17.36107906838843 | 8.596787558819491 |
| AGND | legacy-conditional-requirement | remove-W4-W6 | KA | 0.5 | 849/849 | 3/3 | 13.371399738577054 | 5.582147759568602 |
| AGND | legacy-conditional-requirement | remove-W4-W6 | KB | 0.5 | 995/995 | 32/32 | 17.403425296848418 | 8.649274192478947 |
| AGND | legacy-conditional-requirement | remove-W5 | KA | 0.5 | 849/849 | 3/3 | 13.37134192095785 | 5.582134480707017 |
| AGND | legacy-conditional-requirement | remove-W5 | KB | 0.5 | 995/995 | 32/32 | 17.22247979556277 | 8.466446425401276 |
| AGND | legacy-conditional-requirement | remove-W5-W6 | KA | 0.5 | 849/849 | 3/3 | 13.371399738576816 | 5.582147759568537 |
| AGND | legacy-conditional-requirement | remove-W5-W6 | KB | 0.5 | 995/995 | 32/32 | 17.534129460956105 | 8.788127407123604 |
| AGND | legacy-conditional-requirement | remove-W6 | KA | 0.5 | 849/849 | 3/3 | 13.371394693464813 | 5.582146197435719 |
| AGND | legacy-conditional-requirement | remove-W6 | KB | 0.5 | 995/995 | 32/32 | 17.30366928731564 | 8.553267446711972 |
| AGND | nominal-average | all-present | KA | 0.5 | 849/849 | 3/3 | 12.431765681562034 | 5.441039073514381 |
| AGND | nominal-average | all-present | KB | 0.5 | 995/995 | 32/32 | 15.658680566026518 | 8.004346615204074 |
| AGND | nominal-average | remove-W4 | KA | 0.5 | 849/849 | 3/3 | 12.431790096797114 | 5.441045331706076 |
| AGND | nominal-average | remove-W4 | KB | 0.5 | 995/995 | 32/32 | 15.692890090762646 | 8.03521514242354 |
| AGND | nominal-average | remove-W4-W5 | KA | 0.5 | 849/849 | 3/3 | 12.431817990951764 | 5.441051147510942 |
| AGND | nominal-average | remove-W4-W5 | KB | 0.5 | 995/995 | 32/32 | 15.828809611121812 | 8.166698350798903 |
| AGND | nominal-average | remove-W4-W6 | KA | 0.5 | 849/849 | 3/3 | 12.431817990951046 | 5.441051147510769 |
| AGND | nominal-average | remove-W4-W6 | KB | 0.5 | 995/995 | 32/32 | 15.866965560442974 | 8.21396076485898 |
| AGND | nominal-average | remove-W5 | KA | 0.5 | 849/849 | 3/3 | 12.431769316793627 | 5.441039624026166 |
| AGND | nominal-average | remove-W5 | KB | 0.5 | 995/995 | 32/32 | 15.694182823500377 | 8.039552695633086 |
| AGND | nominal-average | remove-W5-W6 | KA | 0.5 | 849/849 | 3/3 | 12.43181799095076 | 5.4410511475106835 |
| AGND | nominal-average | remove-W5-W6 | KB | 0.5 | 995/995 | 32/32 | 15.984386381278235 | 8.33869958655018 |
| AGND | nominal-average | remove-W6 | KA | 0.5 | 849/849 | 3/3 | 12.43181377736456 | 5.441049809529364 |
| AGND | nominal-average | remove-W6 | KB | 0.5 | 995/995 | 32/32 | 15.767079445904404 | 8.117468182392278 |
| AGND | sensitivity-thin | all-present | KA | 0.5 | 849/849 | 3/3 | 17.26005362587183 | 8.174545759613846 |
| AGND | sensitivity-thin | all-present | KB | 0.5 | 995/995 | 32/32 | 20.94312140837007 | 11.521232688806766 |
| AGND | sensitivity-thin | remove-W4 | KA | 0.5 | 849/849 | 3/3 | 17.260089780420074 | 8.174555425368233 |
| AGND | sensitivity-thin | remove-W4 | KB | 0.5 | 995/995 | 32/32 | 20.996999211015964 | 11.570858878488393 |
| AGND | sensitivity-thin | remove-W4-W5 | KA | 0.5 | 849/849 | 3/3 | 17.260132305736906 | 8.174564702887798 |
| AGND | sensitivity-thin | remove-W4-W5 | KB | 0.5 | 995/995 | 32/32 | 21.200512291806266 | 11.768622747836826 |
| AGND | sensitivity-thin | remove-W4-W6 | KA | 0.5 | 849/849 | 3/3 | 17.260132305735258 | 8.17456470288735 |
| AGND | sensitivity-thin | remove-W4-W6 | KB | 0.5 | 995/995 | 32/32 | 21.25038045890259 | 11.830336765624207 |
| AGND | sensitivity-thin | remove-W5 | KA | 0.5 | 849/849 | 3/3 | 17.260059199009465 | 8.17454665078336 |
| AGND | sensitivity-thin | remove-W5 | KB | 0.5 | 995/995 | 32/32 | 20.998227515369916 | 11.575954289857108 |
| AGND | sensitivity-thin | remove-W5-W6 | KA | 0.5 | 849/849 | 3/3 | 17.2601323057346 | 8.174564702887132 |
| AGND | sensitivity-thin | remove-W5-W6 | KB | 0.5 | 995/995 | 32/32 | 21.403187331857215 | 11.992662747599626 |
| AGND | sensitivity-thin | remove-W6 | KA | 0.5 | 849/849 | 3/3 | 17.26012586466531 | 8.174562584888442 |
| AGND | sensitivity-thin | remove-W6 | KB | 0.5 | 995/995 | 32/32 | 21.093326069182748 | 11.677649241104643 |

Source-pad identities, worst-pad identities, signed injections, source-relative potential extrema, wire-current vectors, removed wires, energy by board/class and 110 mm wire sensitivity are retained in summary.json. Zero unserved entries in a coupled output only means the already-filtered injected subset was served; it does not erase the service ledger’s partial/unserved/unmapped groups.

## Limits and engineering consequences

The source model fixes whole KA land patches equipotential. The inlet, load-side star, raw-to-load bridge, protection and branch loads are not implemented by this model. TP990036 is excluded as structurally unresolved. Return all-three-open is structurally singular/open and deliberately not a finite solution; the seven finite AGND states are required separately for each of the three cases. Actual completed states are recorded in the snapshot matrix coverage; missing states are not inferred.

Do not infer rail-to-local-ground device error from these rail-source potentials. No nearest-ground return assignment or GH conductor compliance is established. The nominal depth is a conditional uniformly divided dielectric, not a qualified six-layer stackup. DRC enumeration, exact native reconciliation, manufacturing/process qualification and installed mechanical fit remain separate.

Board-class energy can support an aggregate barrel/access contribution but cannot identify a specific land as the dominant resistance. The existing seven-via feed idea is therefore not proven by aggregate energy alone.

## Prepared bounded follow-up

Select the U2314.11/C2342.1 short In3 supply reconnection. The cache manifest `../../next-intervention-u2314-in3/manifest.json` binds the exact source identities. The single candidate via `1e1b90ef-f82d-5e94-a82e-416153b33ef3` serves U2314.10 AGND; only its nonfunctional In3 annulus is proposed for a future capability experiment, preserving the barrel and required AGND supports. The present materializer rejects selective unused-annulus policy. Adapter/schema fixtures and native roundtrip support must precede any disposable geometry candidate.

Conditional goals are U2314 changing partial→supported, both exact -12V pads becoming fed, supported groups 151→152, partial groups 59→58, eligible supply pads 302→304 and KA disconnections 196→194 with zero newly disconnected identities. The fixed ledger contributes ±0.56 mA for this package only once both supply pins are served. Existing targets and all other load amounts stay fixed. Restored coverage is not a promise to meet the copper resistance requirement.

Native/variant numerical execution is outside the present baseline campaign. Future validation must reconcile geometry→caps→clip→graph→census, protect AGND access and rerun the affected rail/return operators under separately admitted requests. Preserve KEEP_K1402_INCUMBENT, canonical boards/copper, locked panel positions, circuit intent and decision.json. The retained long-B alternative remains negative (34.732173 mΩ analytic strip estimate, not an accepted full-path remedy).
