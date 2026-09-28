# Conditional protection draft amendments after issue 58

Manager applies these acceptance revisions to #52 and #54. No source uncertainty alone blocks a NON-ORDERABLE / NOT-ENERGIZABLE draft. Exact circuit realization is persistently open in [#59](https://github.com/Takazudo/zudo-osc-hole-field/issues/59); physical source/installed qualification stays in #57.

## Issue 52 revised acceptance

1. Consume #48 unchanged one-domain delivery/loss/geometry contracts and `design/power/protection58-draft-contract.json`. Keep physical source, protection MPNs and exact inlet/mate NOT SELECTED. Preserve 33 modules, 438 centres and no parallel regulated outputs.
2. Replace the misleading historical inlet/PTC presentation with an explicit **REQUIREMENT ONLY / NON-ORDERABLE / NOT-ENERGIZABLE** EXT source/interface boundary. Its circuit obligations are external-source/inlet current limiting, low-drop switching/reverse blocking, autonomous load-rail sensing, coordinated shutdown/discharge and observable return integrity. This is a contract, not an implemented circuit.
3. Verify actual source-domain and connector/net semantics. Distinguish raw inlet rails from conditional load rails at the unimplemented boundary; do not use a wire, ideal source or power flag to claim protected connectivity. Any abstract source used to keep a schematic draft inspectable must carry the unimplemented status in specification, generated schematic, netlist/BOM reporting and verification output. Do not emit an orderable footprint/BOM entry for the abstract boundary.
4. Preserve the existing failed single/two-source and PTC comparisons. Show all 82 output,16 precision feedback and30 octave receiver paths as unresolved protection obligations. Do not insert the #58 lumped-model candidate or claim output/sense isolation is implemented. Synth-side work may implement only source-domain/connector separation that the actual netlist can verify; state exactly which separation exists.
5. Reconcile the existing actual rail ledger and capacitor inventory, reserving the source/interface obligation without adding fictitious zero-current parts or booking unused-channel savings. Any unproven new isolation/control package demand remains a quantified open allowance in #59.
6. Passing acceptance is **conditional draft contract + verified domain/connectivity facts**, with the circuit implementation gate still red. `python3 scripts/checks/protection58.py --check --require-draft` checks only the contract; `--require-closed` must fail until #59 provides circuits and evidence. #57 remains open and no energization is authorized.

## Issue 54 revised acceptance

1. Accept #52's requirement-only boundary for **conditional board partition**, provided generated artifacts and reports retain the non-orderable/non-energizable status and cite #59/#57. Do not demand purchased/qualified physical source hardware before a draft partition.
2. Audit one EXT domain, all module/hardware counts, reference distribution within EXT and common patch-sleeve AGND without assuming equal return sharing. No parallel regulated outputs or hidden signal normals.
3. Preserve the #48 source/inlet mechanical reservation as requirement-only geometry. An exact connector body/pilot sequence cannot be inferred. Retain #47/#55 selector reservations and sensitive local islands.
4. Keep precision amplifier, jack feedback and compensation local. Record all 82 output/16 sense/30 receiver boundaries and candidate channel/package/current/capacitance demands. An unresolved protection footprint or package allocation is an **OPEN partition reservation**, not a fitted zero-area device or proved clearance. Draft partition may proceed, but packing/routing closure for affected boards awaits #59's resolved geometry and thermal/current budget.
5. The partition report must separately state: contract arithmetic and topology checks; actual captured implementation checks; open circuit evidence (#59); physical tests NOT RUN (#57). Never roll these into one overall protection PASS. Carry that boundary into #35–#43 board work and interface manifests.

## Why this continuation is safe as a draft

An unimplemented contract can safely carry engineering requirements because it conveys no authority to build/order/energize the interface and makes unknowns visible. The electrical observability counterexample only refutes rail-only return detection; it does not prohibit a separately instrumented return path or a requirement-only source/interface draft. Neither the paired ADG5412F diagnostic nor a mechanical pilot closes that electrical proof. Ordinary external power-off patching stays required. Scope completion of #52/#54 under these amended draft criteria does not close #59 or #57.
