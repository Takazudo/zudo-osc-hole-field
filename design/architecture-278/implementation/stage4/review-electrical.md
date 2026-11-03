# Independent electrical review: Stage 4 candidate and power inventory

Reviewed root-authored `stage4_candidate.py` and separately authored `stage4_power_inventory.py`, their final reports and focused tests. No electrical source-accounting defect found in these final bytes. This receipt is independent of those implementations. It does not claim independent review of my own Stage 4 requirements audit or region generator; another reviewer covers them.

An independent calculation reconstructed all 5904 physical packages and 8226 units from the live `design.spec.instrument.specification()` using canonical designators, rather than trusting the power generator's package counts. All retained package pins and units agree: 20419 pins including 939 NC. For every power variant, the four rail/AGND endpoint multisets agree with the reconstructed source; 1125 placed packages and 4779 unplaced packages form an exact disjoint partition. All 13 POWER package geometries remain null. No missing other-function package is treated as free space.

Independently recalculated all 225 candidate crossing rows from the previous baseline and unchanged octile/interface allowances. Exactly 65 shared rows change: 30 octave endpoint rows translate their source pads and 35 reference endpoint rows translate their source pads. The 160 nonshared rows remain byte-for-byte equivalent. Source driver/ref/pin/net/panel identities remain unchanged, all 225 front/other XY pairs agree with the normalized power package pad table, and all totals/direct pad separations agree. All 30 shared packages retain their complete pad sets and units under +6 mm X translation. The two grip positions are a source geometry proposal only; mechanical qualification is outside this review.

All 240 inherited front/GH/DIN/rear return branch records remain exactly unchanged because their endpoint geometry does not move. The newly moved shared AGND and rail pads resolve separately through the normalized package table. This is correct inventory and coordinate accounting, not a complete routed source/common/branch return graph. The return resistance, rail distribution resistance, routed edges, current-sharing solution and external-source regulation remain unknown. Bypass associations retain their original targets; geometric binding does not qualify bypass loops or stability.

The normalized power report intentionally keeps inherited Stage 3 path totals with an explicit requirement that a translated shared source be recalculated by the candidate generator. The candidate does perform that recalculation. Its retained compact power graph is labeled historical inventory; the normalized table is the new endpoint coordinate authority. Consumers must use this distinction instead of treating old graph coordinates or totals as the new layout.

All nine shared aggregate capacitance obligations and the common injective 26-signal DIN map remain unchanged. Direct capacitance is still unextracted; the selected 1 kohm/100 nF receiver dynamics remain separate. The candidate maximum remains 334.018298 mm with 38 rows above the historical complete-path 300 mm allocation. The shared-only maximum after translation is 253.875510 mm. These are planning/sensitivity results, not measured unsafe/safe boundaries. The original harness-only envelope versus later complete-path interpretation remains a requirements-review issue; no topology addition, canonical limit change or adoption follows from this receipt.

Validation: candidate tests 7/7 PASS; power inventory tests 13/13 PASS, including missing/duplicate endpoints, missing units, stale coordinates, wrong actual aliases and invented POWER placement mutations. Independent source reconstruction, path arithmetic, source hash maps and rail endpoint conservation checks PASS. No native KiCad, ERC/DRC, extracted routing/parasitics, physical electrical or mechanical test was run. Full occupied-space, return/power, capacitance, error/drift, modulation and gate-transient qualification remain open.

## SHA-256 bindings

- `scripts/architecture278/implementation/stage4_candidate.py`: `6bb1fc9c053aa48c615dccf8627041942adb4ec1909722c4ed0d996ded82161b`
- `scripts/architecture278/implementation/test_stage4_candidate.py`: `44637c14ef5cf5f422e49a1b0fb37322a16d040f5cfbc131d966ffc84b2d9fcf`
- `scripts/architecture278/implementation/stage4_power_inventory.py`: `985f9ce633c1c77069108051534cf0bae8876f08218294bb38ada789861408b6`
- `scripts/architecture278/implementation/test_stage4_power_inventory.py`: `5286aade8477e02916da237d54048b0c7a8ae5ed0f8ffd703e91a20e3001797d`
- `design/architecture-278/implementation/stage4/candidate-report.json`: `fde4939aeb285c9081cdbcc7ad9d4b0b95cfdaf713de829fcf89d5f4b7b32bcd`
- `design/architecture-278/implementation/stage4/power-inventory-report.json`: `e49574f6be6567d8df68d0cd4cb1d68cae068b5a2438c21757bfd835285e9a2d`
- `design/architecture-278/implementation/direct-study-report.json`: `d2d8fe01d15bafdb555c09eb5d354bb3d1e178e533134849f143a2d3722ef15f`
- `design/architecture-278/implementation/assembly-report.json`: `2d8f9cbb7316011c8885fe46c1e2a785a7afb07f8ec4efdb5630bde124c498b0`
- `design/architecture-278/source-ledger.json`: `708826e21e701dd04cea00e283360d4b7d6d48f78ef235a709b694927a538ce1`
