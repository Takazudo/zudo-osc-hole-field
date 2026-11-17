# MC02 WSL candidate reconciliation, 2026-11-17

**PRELIMINARY SOURCE RECONCILIATION — NOT AN INTEGRATED GATE PACKET.**

This supplement brings the existing MC02 packet forward with the source-only
reconciliation and later WSL verification receipts. The [historical packet](mc02-packet-preflight-20261116.md)
remains unchanged. Neither source-test success nor a body-height candidate
establishes assembled access, functional layout, Gate A approval or hardware
adoption. Coordinator: Codex on x0x WSL under the user's continuous-work instruction.

## Revision and ownership ledger

| Role | Exact revision |
| --- | --- |
| Historical extraction | `690366aa69450b642f7daee2cb809eb5ded38d63` |
| Reviewed MC01 c6 + MC03 engineering input | `2c53715d49a4a7639723595590d1fd4eeb3a3c1f` |
| Historical preliminary MC02 packet | `af027d73c90de3ad9510d952534fea026cd0f752` |
| MC03 access-note sibling | `3c12df936de9754265f555d48325d313717cedf4` |
| Offline latch-height audit | `f1521630e169822c7b7929e047649027d7633ed2` |

The MC02 packet and MC03 access note originated as sibling documentation lines
from the engineering input. They were composed locally at
`d0d94ce5a606892a648c9bb9f2776251bb1374d9` for review, together with the
supplemental audit. This is not main integration or hardware adoption. The
audit descends from the MC02 packet and adds supplemental code/evidence only.
The access note is available on review branch `wsl/osc-mc03-c6-access-20261117`;
this is candidate publication, not integration. The packet's earlier
“unpublished”, “aggregate NOT RUN” and “Moya sole integrator” statements describe
its authoring context. They remain preserved as history; subsequent user
instructions and the receipts below establish the current WSL coordinator and
work performed.

## Historical Git blob matrix

All eleven historical IDs match the packet. Candidate columns are equal at both the engineering source and access-note head.

| Source path | Historical blob | Candidate blob | Byte relation |
| --- | --- | --- | --- |
| `design/stack/geometry/links/link-gate.json` | `4e2b76400de0a84a45b94d5ebc807be408d254b9` | `fa1116ab377aad9bfffd04cc7d8252ae6f252495` | CHANGED |
| `design/stack/fixings/threading-procedure.json` | `bda863cdc0210b1ecd4b3d50e66fe363a94b4100` | `bda863cdc0210b1ecd4b3d50e66fe363a94b4100` | UNCHANGED |
| `design/stack/link-electrical/link-ratios.json` | `d83ff5e59e79f4f9267a311102bbc22953ab7974` | `ac132d7e68fa5a4224e4219e0e17fec9b8ad881a` | CHANGED |
| `design/stack/link-electrical/inputs.json` | `e348e079042a57d5af741861eabcce8211787123` | `a4fd638f23d31590209e90c012f69188bbf7c4f0` | CHANGED |
| `design/stack/connectors/flex-links.json` | `1e85f9fa937675f3a826008c055e9431424436a5` | `1e85f9fa937675f3a826008c055e9431424436a5` | UNCHANGED |
| `circuit/orchestration/campaigns/osc-stack-20261114/st-01.md` | `cdddc2e3f6e0d5b199b93bdd251218a4ecdbea06` | `cdddc2e3f6e0d5b199b93bdd251218a4ecdbea06` | UNCHANGED |
| `design/stack/connectors/flex-land-patterns.json` | `d55790531315f6cbacc323d6936bd2d9da597574` | `d55790531315f6cbacc323d6936bd2d9da597574` | UNCHANGED |
| `design/stack/geometry/links/link-gate.md` | `e90d43b6f23301b5a530c1ea4ebb2e6c4c574390` | `39397f4a7e48941b2309a513114ed818b2ed878b` | CHANGED |
| `design/stack/fixings/threading-procedure.md` | `115f380fa5cafaa670774fbc6e0c8a8d2631921c` | `115f380fa5cafaa670774fbc6e0c8a8d2631921c` | UNCHANGED |
| `design/stack/link-electrical/README.md` | `c84160df19da4ceabb2bc9c442615007a934507b` | `77a5294e45bca71318683f01a36e9b475a395a5b` | CHANGED |
| `design/stack/thermal/README.md` | `6c780be111573f22c0de42dd43a492328ddfece6` | `6c780be111573f22c0de42dd43a492328ddfece6` | UNCHANGED |

## Candidate digest and numerical checks

| Source | SHA-256 |
| --- | --- |
| `scripts/stack/link_electrical/link_ratios.py` | `5902c93d2ffd5aa4ba4635840f5daca63d89427eb99800f580fd6434a1c0e111` |
| `design/stack/geometry/links/link-gate.json` | `1c091c1d6d4b9c000f770a0e604cb986d5c55e44cb77ea22083249afbf5cdb0d` |
| `design/stack/link-electrical/inputs.json` | `aeb837844dd0359fa7a08348431f633f1ce5c03e9042f143d0822f2e13b25ea1` |
| `design/stack/link-electrical/link-ratios.json` | `9c35ee28dce48376836577ec46748c7420dc596ced6f6803f7aace1686d4f3c3` |
| `design/stack/link-electrical/c6-pass.json` | `2e22fd43b78c7c55386587a2e31492bcf1acbd2d062a1aedf7d4536644dd8f55` |

Consumed electrical record projection: `54d9fc4e26453d951cf0dfc7a5b092789f63250e99a743b9f67fa6d7962b85f6`.
Source values: 61 links; 511 signals; 340 grounds; 321 unused positions; 56 numeric coupling ratios and five intentional STATIC/WIPER-only nulls. Numeric maximum 0.978101; zero ratios above 1.0. P all-posts-open modeled contact current 0.0997772 A. These numbers reproduce stored candidate results; no model regeneration or physical measurement was performed by this addendum.

## Exact unresolved sets

The following sets are identical in the packet, historical extraction source, engineering candidate and access-note head.

| Board | Unplaced ICs |
| --- | --- |
| JL | `U1216` `U1416` `U1417` `U1518` `U2119` `U2218` |
| JR | `U4346` `U4347` `U4348` `U8314` `U8318` `U8417` |
| K | `U1415` `U4324` `U4341` `U4417` `U4433` `U4524` `U4526` `U4527` `U4623` `U4635` `U5110` `U5209` `U5210` `U8409` |

The 31 `NOT SHOWN` latch link IDs:

- `JL-K-JL-L02`
- `JL-K-JL-L03`
- `JL-K-JL-L08`
- `JL-P-K-JL-L01`
- `JL-P-K-P-L01.01.01.01`
- `JR-K-JR-L01`
- `JR-K-JR-L05`
- `JR-K-JR-L06`
- `JR-K-JR-L07`
- `O-K-O3`
- `O-K-O5`
- `P-K-P-L01.01.01`
- `P-K-P-L01.01.02`
- `P-K-P-L02.01.01`
- `P-K-P-L03.01`
- `P-K-P-L06.02`
- `P-K-P-L07`
- `P-K-P-L08`
- `P-K-P-L10.01.02`
- `P-K-P-L10.02`
- `P-K-P-L11.01.01.01`
- `P-K-P-L11.01.01.02`
- `P-K-P-L12.01.01.02`
- `P-K-P-L12.01.02.02`
- `P-K-P-L12.02.01.01`
- `P-K-P-L12.02.01.02`
- `P-K-P-L13.01.02.01`
- `P-K-P-L14.01.01.02`
- `P-K-P-L14.01.02.02`
- `P-K-P-L15.01.02.02`
- `P-K-P-L15.02.01.01`

## Verification receipts and their limits

- [Focused checks at engineering input `2c53715`](https://github.com/Takazudo/zudo-osc-hole-field/issues/362#issuecomment-6940464164): geometry regeneration without tracked drift, electrical/c6 checks and trimmer checker; guarded PASS in 190 seconds after numerical dependencies were provisioned.
- [Aggregate at that same input](https://github.com/Takazudo/zudo-osc-hole-field/issues/362#issuecomment-6940929889): pinned KiCad 10.0.6 aggregate-only regeneration PASS in 567 seconds, without tracked drift.
- [Independent aggregate scope/cleanup audit](https://github.com/Takazudo/zudo-osc-hole-field/issues/362#issuecomment-6940945710): no remaining container, scope or scratch worktree observed for that completed run.
- The supplemental [offline height audit](../../../../scripts/checks/mc02_height/README.md), commit `f1521630e169822c7b7929e047649027d7633ed2`, passed nine offline tests and independent review without a blocking finding. Negative cases cover changed source bytes, identity/ref drift, missing coverage and silent adoption of Murata's inconsistent raw maximum. The real retained-source audit produced 88 references and 31 links.
- `pnpm circuit:check` before/after the audit passed: manual inventory, 84 lines and 445 declared placements unverified; pin-asset checking performed. This is evidence-contract validation, not schematic/placement proof.

These are distinct receipts: prior engineering source validation and subsequent
supplemental-code checks. No unchanged native aggregate was rerun for this
supplement. These results do not qualify a future merged integration head.

## Body-height candidate coverage

| Dimension-evidence category | Distinct references |
| --- | ---: |
| Exact named identity with a body-height candidate | 59 |
| Family dimension only; complete orderable suffix unresolved | 2 |
| Empty retained MPN | 27 |
| Total | 88 |

| Link coverage bucket | Links | Access verdict |
| --- | ---: | --- |
| Every listed neighbour has exact named body-height evidence candidates | 16 | NOT SHOWN |
| No empty MPNs, but at least one unresolved orderable suffix | 2 | NOT SHOWN |
| At least one empty-MPN neighbour, regardless of other evidence | 13 | NOT SHOWN |
| Total | 31 | NOT SHOWN |

The buckets are disjoint. `exact` is a study-identity classification, not a new
owner-fact verdict. The two suffix cases are `BAT54S,215` and `MMBT3906,215`.
An exact package drawing or body-height bound excludes solder/standoff, latch
sweep, approach axis, adjacent board/component tolerance and human handling.
All mounted heights remain unknown and all 31 access outcomes remain `NOT SHOWN`.

For the 29 `GRM188R71H104KA93D` neighbours, the retained official API response
has displayed thickness `0.8 mm ±0.1 mm`, yielding a candidate body range
`0.7–0.9 mm`. Its `thicknessMax.value` is `0.8` while `displayName` is `0.9mm`.
The audit preserves that conflict and refuses silent use of the raw value as a
maximum. The inspected response digest and acquisition receipt are pinned in
[audit evidence](../../../../scripts/checks/mc02_height/evidence.json). The 27
empty-MPN references follow explicit builder/sourcing policy; they must not be
filled from a symbol label, package family or representative nominal value.

## Five-check disposition and next source decisions

| Check | Candidate preparation now available | Remaining decision/evidence |
| --- | --- | --- |
| 1. Connector/cable identity | Exact selected identities and unchanged source blobs can be traced; current primary-source searches distinguish exact Hirose variants from similarly named variants. | Obtain exact selected same-side cable tolerance drawings and FH12 opening/contact-1 evidence. Opposite-side A771 is not a substitute. A manufacturer category such as Front does not identify the project's placed latch side. |
| 2. Opening/locking/access | All 31 NOT SHOWN IDs and neighbour sets rebound; body-height candidate coverage above is executable offline. | Resolve 27 empty identities and two orderable suffixes; establish mounted/latch swept geometry and assembly handling. Documented source download denials stay unavailable rather than being bypassed. |
| 3. Allocation/current | 511 signals, 340 grounds, 321 unused positions; candidate P all-posts-open contact current 0.0997772 A. | Rebind the eventual integrated source. Historical 322-ground/one-post-open 0.047 A and candidate 340-ground/all-posts-open cases are different revisions and operating cases, not competing measurements. |
| 4. Coupling | One bound kernel/projection; 56 numeric ratios, five intentional nulls, maximum 0.978101 and zero above 1.0. | Integrated-source rebind and independent ruling; measured harness behavior remains unknown. |
| 5. Cumulative rework | Exact 26 unplaced packages, functional map below and unchanged historical workload/operation evidence. | DS-88/DS-97 disposition of the nonempty unplaced set and bounded remedies. Do not repeat or widen the placement search; courtyard room is not functional layout. |

MC03/ST-07 tool access is useful context but **is not a formal Gate A-paper
prerequisite** under [MC04 issue #367](https://github.com/Takazudo/zudo-osc-hole-field/issues/367).
It must not prevent unrelated MC02 preparation. Conversely, the nonempty 26-IC
list is an explicit input to the paper gate, not permission for an expanded
search. MC04 still requires the actual integrated-source rebind and an
independent confirmed Astra ruling; this document is neither that ruling nor a
release of DS-06 K interface-routing holds. Keep accepted DS-108 thermal option A
and first-article obligations; numerical height or coupling results do not
establish thermal compliance.

The available source work can be extended by exact-identity/evidence binding,
conditional circuit/assembly requirements and bounded review preparation.
A source unavailable on one path does not establish that all development work
is blocked. No hardware selection, route/position change, native rerun, DRC,
fill, manufacturing or canonical adoption is performed by this supplement.

## Functional review map for the 26 unplaced packages


| Board | Ref | Instance / source family | Project MPN | Source unit roles (supply omitted) | Inferred review category |
| --- | --- | --- | --- | --- | --- |
| JL | U1216 | O2 / oscillator | OPA4196IDR | 1: high_impedance_input:A; 2: high_impedance_input:A; 3: high_impedance_input:A; 4: general_output:A | Oscillator FM/PWM/SYNC input and sine-output interfaces |
| JL | U1416 | O4 / oscillator_tssop | OPA4196IDR | 1: high_impedance_input:A; 2: high_impedance_input:A; 3: high_impedance_input:A; 4: general_output:A | Oscillator FM/PWM/SYNC input and sine-output interfaces |
| JL | U1417 | O4 / oscillator_tssop | OPA4196IDR | 1: general_output:A; 2: general_output:A; 3: general_output:A; 4: oscillator:unused grounded follower | Oscillator waveform output interfaces |
| JL | U1518 | O5 / oscillator | OPA4197IDR | 1: high_impedance_input:A; 2: oscillator:unused grounded follower; 3: oscillator:unused grounded follower; 4: oscillator:unused grounded follower | Precision pitch input (1V_BUFFER) |
| JL | U2119 | F1 / filter | OPA4196IDR | 1: magnitude_indicator:A; 2: magnitude_indicator:A; 3: magnitude_indicator:A; 4: magnitude_indicator:A | Filter magnitude-indicator paths |
| JL | U2218 | F2 / filter | OPA4196IDR | 1: general_output:A; 2: general_output:A; 3: general_output:A; 4: general_output:A | Filter LP/BP/HP/dry output interfaces |
| JR | U4346 | E3 / envelope_tssop_e3 | OPA4196IDR | 1: high_impedance_input:A; 2: high_impedance_input:A; 3: high_impedance_input:A; 4: general_output:A | Envelope input and output interfaces |
| JR | U4347 | E3 / envelope_tssop_e3 | OPA4196IDR | 1: general_output:A; 2: general_output:A; 3: general_output:A; 4: magnitude_indicator:A | Envelope bipolar/EOC/stage outputs and indication |
| JR | U4348 | E3 / envelope_tssop_e3 | OPA4196IDR | 1: magnitude_indicator:A; 2: magnitude_indicator:A; 3: envelope:unused grounded follower; 4: envelope:unused grounded follower | Envelope rise/fall magnitude indicators |
| JR | U8314 | M4A / mix4_vca | OPA4196IDR | 1: high_impedance_input:A; 2: high_impedance_input:A; 3: high_impedance_input:A; 4: high_impedance_input:A | Four mixer input buffers |
| JR | U8318 | M4A / mix4_vca | OPA4196IDR | 1: magnitude_indicator:A; 2: magnitude_indicator:A; 3: magnitude_indicator:A; 4: magnitude_indicator:A | Mixer magnitude indicators including post-VCA sum |
| JR | U8417 | M4B / mix4_vca | OPA4196IDR | 1: high_impedance_input:A; 2: general_output:A; 3: magnitude_indicator:A; 4: magnitude_indicator:A | Mixer attenuation input, post-VCA output and indicators |
| K | U1415 | O4 / oscillator_tssop | OPA4196IDR | 1: oscillator:SINE_DIFF; 2: oscillator:SINE_GAIN; 3: oscillator:unused grounded follower; 4: oscillator:unused grounded follower | Analog differential sine / summing feedback |
| K | U4324 | E3 / envelope_tssop_e3 | SN74HC00DR | 1: envelope:NAND55; 2: envelope:NAND57; 3: envelope:NAND58; 4: envelope:NAND60 | Envelope combinational state/timing logic |
| K | U4341 | E3 / envelope_tssop_e3 | OPA4197IPWR | 1: envelope:FALL_EXPO_SCALE; 2: envelope:FALL_EXPO_SERVO; 3: envelope:ENV_BUFFER; 4: envelope:unused grounded follower | Envelope exponential fall servo and storage-buffer path |
| K | U4417 | E4 / envelope_tssop_e4_e5 | SN74HC00DR | 1: envelope:NAND19; 2: envelope:NAND21; 3: envelope:NAND22; 4: envelope:NAND23 | Envelope combinational state/timing logic |
| K | U4433 | E4 / envelope_tssop_e4_e5 | SN74HC74DR | 1: envelope:LOOP_SYNC1; 2: envelope:LOOP_SYNC2 | Envelope clocked synchronizer / timing logic |
| K | U4524 | E5 / envelope_tssop_e4_e5 | SN74HC00DR | 1: envelope:NAND55; 2: envelope:NAND57; 3: envelope:NAND58; 4: envelope:NAND60 | Envelope combinational state/timing logic |
| K | U4526 | E5 / envelope_tssop_e4_e5 | SN74HC00DR | 1: envelope:NAND66; 2: envelope:NAND68; 3: envelope:NAND69; 4: envelope:NAND70 | Envelope combinational state/timing logic |
| K | U4527 | E5 / envelope_tssop_e4_e5 | SN74HC00DR | 1: envelope:NAND71; 2: envelope:NAND72; 3: envelope:NAND73; 4: envelope:NAND74 | Envelope combinational state/timing logic |
| K | U4623 | E6 / envelope | SN74HC00DR | 1: envelope:NAND51; 2: envelope:NAND52; 3: envelope:NAND53; 4: envelope:NAND54 | Envelope combinational state/timing logic |
| K | U4635 | E6 / envelope | SN74HC74DR | 1: envelope:TOP_SYNC2; 2: envelope:BOTTOM_SYNC1 | Envelope clocked synchronizer / timing logic |
| K | U5110 | W2 / wavefolder | OPA4196IDR | 1: wavefolder:F1; 2: wavefolder:F2; 3: wavefolder:F3; 4: wavefolder:F4 | Wavefolder four analog summing/feedback stages |
| K | U5209 | W1 / wavefolder_tssop | OPA4196IDR | 1: wavefolder:CURRENT_SERVO; 2: wavefolder:PRE_GAIN; 3: wavefolder:DRIVE_SUM; 4: wavefolder:DRIVE_INVERT | Wavefolder current servo and gain/summing feedback |
| K | U5210 | W1 / wavefolder_tssop | OPA4196IDR | 1: wavefolder:F1; 2: wavefolder:F2; 3: wavefolder:F3; 4: wavefolder:F4 | Wavefolder four analog summing/feedback stages |
| K | U8409 | M4B / mix4_vca | OPA4196IDR | 1: remote_buffer:A; 2: bipolar_attenuverter:A; 3: remote_buffer:A; 4: bipolar_attenuverter:A | Mixer remote-buffer / attenuverter feedback and summing |

## Count and DS-97 boundaries

Board totals: {'JL': 6, 'K': 14, 'JR': 6}. MPN totals: {'OPA4196IDR': 16, 'OPA4197IDR': 1, 'SN74HC00DR': 6, 'SN74HC74DR': 2, 'OPA4197IPWR': 1}. The retained list has 25 SOIC-14 packages and one TSSOP-14 (U4341).

None of these 26 belongs to the explicitly first-priority DS-97 classes (AS3340D, LF398M_NOPB, REF5050AIDR on K, or F1/F2/F3 Q-prefix transistors). This does not make the list electrically insensitive: DS-97 explicitly distinguishes courtyard room from functional layout and requires later moves as function groups. The OPA4197 entries are U1518 (IDR) and U4341 (IPWR); these are among DS-97 named report classes.

The DS-97 gate decides whether the unresolved list and displacement work are acceptable. This inventory does not repeat or widen DS-88 search radii, introduce thermal preferences, move links, or release routing holds.

## Concrete gate review questions

1. Can the gate accept a nonempty list with 6 JL, 6 JR and 14 K packages still unplaced? If not, which bounded remedy is authorized before another attempt? No numerical search expansion is proposed here.
2. For U1518 (/O5/1V_BUFFER) and U4341 (FALL_EXPO_SCALE/FALL_EXPO_SERVO/ENV_BUFFER), which existing circuit error, leakage, storage-node and feedback constraints must accompany any eventual function-group move? No added trace/via allowance is retained by this map.
3. For U4324/U4417/U4524/U4526/U4527/U4623 and U4433/U4635, what must the later layout review preserve about combinational state paths, CLOCK, READY and synchronizer relationships? This is a request for a bounded layout verification contract, not a timing proof.
4. For U1415, U5110/U5210, U5209 and U8409, which feedback/summing paths and associated passive groups must remain together in an eventual layout proposal? Source nets identify review scope; they do not establish parasitic or stability margins.
5. For the input/output/indicator packages, what load, protection, decoupling and interaction checks apply when moving their complete functions? Indicator roles alone do not demonstrate absence of analog coupling impact.

## Precision-function evidence follow-up

The independently reviewed [U1518/U4341 constraint map](mc02-precision-constraints-20261117.md) answers the source-backed portions of review question 2. It retains exact topology, existing calibration/ideal-fixture scopes and source hashes. It does not allocate new routing, leakage, via or stability budgets.

## Retained catalog follow-up — 2026-11-17

The [retained FH12 review](mc02-retained-fh12-review-20261117.md) confirms the
packet-matching catalog bytes and exact standard-variant/closed-height locators.
Contact-1 mapping, numeric open envelope, placed access and selected same-side
LX cable tolerances remain unresolved. This narrows source provenance; it does
not promote the packet or any hardware gate.

## Exact cable drawings obtained — 2026-11-17

The [selected cable source update](mc02-selected-cable-source-update-20261117.md)
now supplies exact manufacturer drawings for C81339,C68390,C29534. These expose
interval and contact-finish mismatches; they do not establish compatibility.
C26618 and C32128 link the same generic drawing without exact applicability. Earlier
blanket missing-drawing statements are historical, not the current disposition.
