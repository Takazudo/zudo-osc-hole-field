# Issue 58 work note

Requested: exact conditional protection architecture for #52. Outcome: unsupported-evidence gate remains OPEN; no safe complete circuit selected. The authored decision and executable audit preserve the concrete counterexamples and a bounded replan rather than asserting hardware impossibility.

Baseline: `pnpm circuit:check` PASS (42 manual lines, no schematic/placement binding); `bash scripts/checks/regen-all.sh` PASS, no tracked drift. KiCad oracle reports 10.0.6. Read #48 source contract and manager-provided #52 partial commit fb3302ea7356aa16a89b1080b15be546f08eca69 without editing sibling files.

Actions: retained actual TI LM74502 and Nexperia PSMN1R0-40YLD PDFs; inspected exact conditions; retained failed ADG5401F acquisition honestly. Extended the existing ADG5412FBRUZ owner with power-off, missing-rail, current and leakage limits and explicit OPEN project-output domain. No candidate added to inventory. Publication selection unchanged because existing ADG owner was already selected; generated component page changes are regenerated evidence only.

Derived all 82 output UIDs, 16 sense paths, and 30 octave receiver connections from actual source specifications. Built source-hash/domain/count checks, series-loss arithmetic, proposed enable state table, and return-observability counterexample. State tables are requirements, not hardware sequencing simulation. The optional `--require-closed` gate intentionally returns 1.

Diagnostic paired-switch proposal: 998 ohm main resistance and 2.74 kohm sense resistance on the protected-source side; 10 Mohm local feedback plus 10 nF compensation. Pinned TI amplifier model with lumped switch R/C passes all 12 cases; actual switch vendor/fault/partial-power behavior NOT RUN and not claimed. New package current violates the reserved 20 mA auxiliary budget unless actual reuse/allocation and the complete ledger prove otherwise. No package savings assumed.

No schematic, PCB, inlet pin map, module source or hardware centres edited. No physical experiments, supplier contact, orders, fabrication files or deployment. Exact rail/control topology, guaranteed thresholds/timing, fault energy, floating-rail injection, return-integrity mechanism and package/current/capacitance allocation remain open.

Manager clarified that a conditional external source/interface contract is an allowed CAD fallback. Added a separate draft-contract gate, exact #52/#54 acceptance amendments, and persistent circuit-evidence follow-up #59. Draft continuation is permitted; implemented protection and orderability remain explicitly false. Foreground review corrected an initially overbroad pause on all #52 work and the TI revision date (actual bytes say May 2022).

Final focused verification: six regression tests PASS; `pnpm circuit:check` and `pnpm check` PASS; generated pages/preflight/previews current; contract-only draft gate PASS and exact-circuit gate intentionally rejects closure. Visual primary-source review: ADG5412F printed pp11/26 (TSSOP current and grounded-reference conditions) and PSMN1R0-40YLD printed p6 (hot max versus typical columns). No layout/UI visual check: no schematic/layout/UI implementation changed. Full build/site/browser suites NOT RUN by this worker; manager owns combined verification.

Foreground self-review applied: corrected source revision metadata; separated draft permission from circuit closure; bound reference records to actual receiver pins; added guards against original-cell drift and false hardware promotion. No remaining implementation defect found in the bounded audit. Electrical gates remain deliberately open in #59.
