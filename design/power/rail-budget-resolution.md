# Issue #34 — rail budget resolution decision

**Authority:** PROPOSAL (planning, owner-delegated). **Status:** Unvalidated draft; the design ceiling is an 80% project margin against unmeasured zudo-pd supply targets, not demonstrated source capacity. **Decision:** Issue #34 follows its fourth case. No source-backed option 1–3 establishes that this instrument can remain below all ceilings at guaranteed maximum load. Do not change the circuit, electrical standard, shortlist, supply ceiling or board partition to force an apparent pass. Propose a second supply feed for later engineering review; this document does not design one.

## Captured starting point

`bash scripts/schgen/build_master_budget.py --check` reproduces `design/power/rail-budget.json` from all eleven current worksheets plus the issue #24 inlet bleeders. The 34 non-power rows are 33 modules and the shared octave reference. Netlist counts come from `design/reports/netlist-stats.json` after the issue #33 master audit: 77 OPA4197IPWR quads, 170 OPA4196IDR quads, 48 fitted B104 100 kΩ DC pots, 92 magnitude LEDs, 10 clip LEDs and 12 stage LEDs. All 438 panel UIDs are bound once. Nothing below changes those counts.

| Rail | Reported/assumed typical subtotal | Planning upper subtotal | 80% design ceiling | Planning excess | Guaranteed maximum |
| --- | ---: | ---: | ---: | ---: | --- |
| +12 V | 781.958 mA | 1,404.819 mA | 960 mA | **444.819 mA** | **NOT ESTABLISHED** |
| −12 V | 715.458 mA | 1,313.569 mA | 640 mA | **673.569 mA** | **NOT ESTABLISHED** |
| +5 V | 80.273 mA | 177.286 mA | 400 mA | none in the known subtotal | **NOT ESTABLISHED** |

These are summed report allowances, **not** manufacturer-guaranteed instrument currents. The sample-and-hold worksheet omits +5 V logic/reference demand, NOISE2 current is assumed, output/fault/temperature/startup currents are incomplete, and the supply targets are unmeasured. The upper subtotal includes worst-voltage/resistance inlet bleeders; typical uses nominal bleeders. The preliminary OSC-ES-1 deficit of 72.655 mA is superseded by this captured master subtotal.

## Option comparison and source limits

`python3 scripts/schgen/analyze_rail_options.py --check` reproduces the deliberately generous sensitivity cases in `design/power/rail-options.json`. It books **zero** savings into the master budget. The op-amp IQ comparison uses retained Texas Instruments `circuit/sources/ic-library/OPA4197.pdf` and `OPA4196.pdf`, physical PDF page index 7 / printed page 8, *Electrical Characteristics — Power Supply* row: full-temperature maximum quiescent current is 1.5 mA versus 0.25 mA per amplifier at zero output current. Four channels give the already-budgeted 6 versus 1 mA per whole quad. These rows do not bound output load or startup current. LED and pot currents below are **project planning allowances** from `design/standard/rail-budget-preliminary.json`, not manufacturer maximum currents or visibility evidence.

| Conditional case | Maximal arithmetic saving on each analog rail | Remaining +12 / −12 planning subtotal | −12 excess |
| --- | ---: | ---: | ---: |
| 1. Replace **all 77** OPA4197 quads with OPA4196 | 77 × (6 − 1) = 385 mA | 1,019.819 / 928.569 mA | 288.569 mA |
| 1 + 2. Also turn **all** 92 magnitude and 10 clip LEDs off | + 92 × 1.25 + 10 × 1.1 = 126 mA | 893.819 / 802.569 mA | 162.569 mA |
| 1 + 2 + 3. Also remove **all** 48 B104 pot current | + 48 × 0.125 = 6 mA | 887.819 / 796.569 mA | **156.569 mA** |

Case 1 is a theoretical upper bound, not a viable blanket role substitution. Audio/CV/indicator roles already use OPA4196. The 77 precision quads include stages whose offset, noise, input bias, slew and stability constraints must be reviewed before any exact substitution. OPA4196 pin/package differences also need exact library and layout review. None of those analyses is completed here.

Case 2 sets LEDs to **zero**, so it destroys the intended indicator function and is only a mathematical ceiling on savings. A 0.6 mA/LED diagnostic target would save 64.8 mA per analog rail in the planning model, and visibility behind the fixed window is NOT RUN. The 12 envelope stage LEDs load +5 V, so subtracting them from an analog rail would be double counting. Exact brightness current appears in module worksheets; no driver resistor or LED identity changed.

Case 3 removes the entire planning current allowance of all 48 fixed B104 DC-source pots, which would also remove their function. Increasing a 100 kΩ pot network's impedance needs an exact orderable part or a new buffer/transfer design and a noise/offset/taper review. Only six manual offset pot loads are separately itemized in their module worksheet; other pot loads are embedded in broader reserves. Thus **6 mA is an overgenerous cap, not a bookable subtraction**. No pot value or topology changed.

The exploratory package-packing sensitivity retained in `design/power/rail-options.json` lists 43.4 mA −12 V from a hypothetical 62 fewer ADG packages at the 0.7 mA planning unit allowance, 38 mA from a hypothetical six fewer OPA4197 plus two fewer OPA4196 sample-and-hold quads at their 6/1 mA source-backed IQ maxima, and 10 mA from ten fewer comparator packages at the 1 mA planning allowance: 91.4 mA total. The package counts are hypotheses against `design/reports/netlist-stats.json`, not a generated packing plan; unit allowances come from `design/standard/rail-budget-preliminary.json` and the retained OPA PDFs. Those are mixed planning allowances, not manufacturer maxima or a validated package reallocation. The sample-and-hold op-amp term **overlaps** case 1 and cannot be independently added. Even granting the full 91.4 mA *as an intentionally double-counted extra* after the impossible cases above leaves 705.169 mA on −12 V, **65.169 mA above** the 640 mA ceiling. This sensitivity check is not booked or an approved optimization. It closes the apparent package-packing shortcut without inventing a substitution.

## Fourth case and next evidence

The existing single-feed design does not have a demonstrated ceiling-compliant maximum. **A second supply feed is a proposal only.** Its quantity, rail allocation, connector, pin map, return current, isolation, sequenced startup, protection, mechanical route and interaction with the design-locked zudo-pd assembly are intentionally undecided. Tracked follow-up [#48](https://github.com/Takazudo/zudo-osc-hole-field/issues/48) must first establish source-side continuous and startup capacity at the pinned revision; complete instrument typical/maximum current by rail and temperature; cable/connector/return-path current and fault behavior; and a proposed split that keeps Sensitive nets off connectors. Then it can compare a revised single source, a second feed, or a reduced instrument scope against mechanical and owner constraints. The board partition remains gated by that decision and by physical bench evidence. The [epic status comment](https://github.com/Takazudo/zudo-osc-hole-field/issues/1#issuecomment-5862767776) records this escalation; neither link is a supply design approval.

The master hard gates remain unchanged and pass: exact 35-instance hierarchy, 438 locked panel bindings, zero ERC errors with 240 documented electrical-type warnings, exported netlist parity, unique designators, all Sensitive members assigned to islands with no panel crossing, and complete deliberately terminated package units. No fabrication order file or release claim is made.
