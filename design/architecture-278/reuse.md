# Source, reuse and unresolved-requirement ledger (#279)

Use source-ledger.json for exact 33 function contracts, all 438 UID coordinates, 5,904 packages and 8,226 units (including explicitly unused/grounded and supply units), 10 current boards and shared services. Existing reports are retained source evidence, not fresh native verification. O1/O2/O5 live-source parity is separately checked by extract.py. No physical package may be split across cards. Changes to a function's shared packages invalidate its siblings' affected evidence as well.

## Reuse classification

| Exact input at revision | Disposition | Reason and invalidation |
|---|---|---|
| main 65cefd41fc39e064d38319115ad96016a1c6b71c: project/osc-hole-field/block-contracts.json; design/grid/placements.lock.json | reuse unchanged | Fixed function and panel contract. Any UID, XY or endpoint change violates this task. |
| same main: design/spec/**, design/standard/**, scripts/schgen/**; design/reports/io-partition.json | adapt and reverify | Circuit intent and whole-package regions reusable. New board boundaries require complete Ref-pin parity, local feedback/bypass/island closure and fresh ERC/DRC; source success is not hardware suitability. |
| same main: .claude/skills/component-*/ and circuit-spec-integration/references/rules.json | reuse unchanged for exact-part claims only | Pin, identity and retained manufacturer evidence survive unchanged conditions. Different suffix, footprint, ambient, supply or assembly process invalidates applicability; no promotion of typical to guaranteed behavior. |
| same main: design/partition/**, design/connectors/**, design/reports/connectors.json | adapt and reverify | Exact old header/pin/wire inventory and 195/911/1822+18 baseline retained. New middle faces, lengths, contacts, supports and loading require new whole-path checks. |
| same main: boards/** and design/boards/** | evidence only for new architecture | Canonical copper remains untouched incumbent. Old connectivity/DRC receipts belong to exact boards; do not transfer to rerouted functional cards. Core-only alternative may preserve front copper but changed endpoints still invalidate joined evidence. |
| same main: design/mechanical/**; design/partition/partition.json | evidence only | Retain exact nominal component envelopes and conditional planes; seated datums, loads, tolerances and enclosure remain open. Connector height is not board spacing. |
| same main: design/power/** and design/reports/current/** | adapt and reverify | Retain load identities, assumptions, gaps and limits. Reassign source-to-load paths without resetting budgets; unknown dynamic/fault maxima remain unknown. |
| same main: scripts/checks/**, scripts/pcbgen/**, scripts/kicad/** | adapt and reverify | Pure read-only checks reusable within scope. Native wrapper is the sole 10.0.6 oracle only after separate admission; exact hashes/receipts and resource limits must be rebound. No invocation now. |
| PR261 7aba720c1246d6ec3f02909af6fb08dc774b3d31: design/service/trimmer-functions.json; trimmer-inventory.json; component-review/**; scripts/service/** | adapt and reverify | Reuse semantic labels, 100 trims/28 roles, six OSC trims and shared octave span. 23 blank MPNs remain unresolved; same-value candidate evidence is not selection. Join Ref+Block+Role; current board/face/tool access must be rebuilt. |
| PR267 62281e832f65e36757a98f8b21fce6cbe336ea64: scripts/pcbgen/trimmer_labels* | adapt and reverify | Source-owned label generation and rejection tests useful later. Native annotation/clearance not performed; do not copy old geometry or apply labels here. |
| PR260 5af0e7b675123b40367078ee605a1355bae49a62: design/partition/core-split/** | evidence only | Preserve failed copper resistance, load/GH incompleteness, historical split/service/burden studies. No wholesale stack adoption. |
| PR277 fdac23b2611dcb26f840c520348771821ea9c35d: design/partition/core-split/candidates/planning/joined-feed-construction-v2/WORK.md and evidence/e16/** | evidence only | Full resource qualification NOT_QUALIFIED, production NOT_ADMITTED/NOT_RUN, Stage C NOT RUN. 16/24 diagnostic and 2/3 baseline consumption retained; no restart. |
| Old dispatch prompts, native receipts as new-board acceptance, reduced-load passes as full acceptance, discarded alternatives as adopted designs | do not reuse | Authorization and input scope do not transfer. No reopening finite-path coverage or classified 552 omissions. |

The linked architecture epoch 011e8be351e81d51a13d2d56cb246fd36d623843 supplies block-contracts, connectors and osc-board-stack/io-partition/block-osc/electrical-standard/reference-fanout/octave-reference documents. Compare exact blobs with main before reuse; linked text is historical when inputs differ. No parked file is copied into production.

## Requirement owners and prior lineage

| Owner | Retained obligation / applicability |
|---|---|
| #278/#279/#280 | All 33 functions, five OSC, 438 centres; complete package/endpoint/rear-terminal inventory; preserved shared services. Other families remain boundary-only. |
| #281/#283, #55/#65 | Seated hardware, 3+2 selectors, support stiffness, enclosure, insertion/extraction, six-trimmer/probe access and physical assembly. Drawings do not close these. |
| #282/#247 | Complete fitted current, dynamic/short/startup/return/contact and whole-path budgets; partial/unmapped/unserved loads do not disappear. |
| #57 | Selected source/inlet, realization and safe physical source/rail testing. Requirement-only CN301/XB301 is not a conductive realized inlet. |
| #59 | Raw input/output/feedback and off-state/rail-loss/return-integrity protection; 82 outputs, 16 precision sense paths, 30 octave receivers plus local fanout inputs retain scope. |
| #21/#29/#30/#31/#248 | Exact component identities, missing passive/trim MPNs, oscillator and other family circuit/calibration suitability. Six OSC trims plus shared span; no new trims selected. |
| #249 / PR261/#267 | Semantic annotation and future exact-board label/native access verification; historical readiness is source contract only. |
| #189/#38/#39/#43 | Unfinished canonical electrical/CAD delivery and copper requirements; design packet does not complete them. |
| #64 | Optical/thermal LED behavior, unaffected but still required instrument-wide. |
| #214/#44/#45/#1 | Toolchain/full assembly/manufacturing/instrument qualification remains independently owned. |
| #242/#243–246/#250–259 (including #253) | Old execution parked; acceptance defects and original-group obligations preserved. #253 remains open. No dispatch implied by old prompts. |
| PR262/#264/#265/#270/#271 | Historical split/power/mechanical constraints, no new-board acceptance. |
| PR266/#268/#269 | JR/JL/K endpoints and rejected pilots retained; no routing restart. |
| PR274–277; PR221/#225/#226/#229/#233/#236–241 | Retained native/rejection/audit/admission lineage, open drafts not blanket-adopted or closed. |

Changed connector type, length, pinout, mating orientation, rail source, receiver count, load state, return topology, reference buffering, component/MPN, board placement or copper invalidates corresponding electrical/mechanical/native evidence. Even unchanged net names do not preserve a physical return path. Shared octave capacitance remains aggregate over five branches, not five independent 1 nF allowances. Source/reference changes affect all five and potentially every common-rail function.
