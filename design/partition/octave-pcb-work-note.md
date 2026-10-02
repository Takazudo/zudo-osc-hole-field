# Five passive octave adapter PCB drafts

The five source-defined SRBV160803 adapters now have actual two-layer PCB layouts. Each contains the fixed switch and two JST BM07B-GHS-TBT(LF)(SN) headers. Source outlines, stack proposals, component/pad poses and all panel centres are unchanged. These are unvalidated drafts, not fabrication files.

All five routed on their first bounded attempt. O1/O3/O5 use 33 tracks and 7 vias, with 111.7603 mm total track length; O2/O4 use 22 tracks and 3 vias, with 69.9345 mm. Each has eight connected functional nets, zero actual native open edges, zero all-severity DRC findings, and zero schematic parity findings. The complete current checker also verifies all 30 native pad/net mappings, source poses, fixed outline, zones and full project rule/class settings. It runs fresh DRC after capturing source bytes and rejects stale clean reports, physical changes and weakened rules. CI rechecks disposable copies without heuristic routing.

The placer now accepts boards whose entire inventory is already source-anchored, while rejecting unaccounted/free footprints and incomplete/nonfinite poses. It does not serialize a board when it moves no footprints. Untouched rear-switch reference labels are moved onto the existing top tongue; edited label positions are preserved.

## Validation history

- Initial aggregate baseline: PASS, 364 seconds, no tracked drift.
- First O1 preflight: FAIL, 2 seconds, because the placer unconditionally required a region; no routing occurred. The fixed-only path corrected that contract.
- Five-board native preflight: PASS, 20 seconds; each initially had 14 expected open edges over eight functional nets.
- First O1/O2 routes: PASS, 27 seconds. O3–O5: PASS, 34 seconds. No subsequent heuristic routes were required.
- Early stability harnesses: FAIL at 10 and 16 seconds. Raw native serialization needed deterministic owned-item ordering; complete parsed item comparisons found no geometry changes. A transient intermediate was not retained, so no speculative normalizer defect is claimed or patched.
- Two complete standalone sync/place/check passes finished for all five boards with byte-identical PCBs and clean DRC. That 285-second wrapper subsequently failed in the new terminal checker because KiCad UTF8 wrappers were compared directly to Python strings. The checker now compares full library-qualified string identities.
- Fourteen native fixed-only controls and eight current-board rejection controls exercise the actual KiCad oracle. The latter include a copied clean report plus a new short, altered drill, ignored short rule, extra assignment, moved outline, added cutout and changed zone clearance.

Historical peripheral ground receipts remain byte-identical and stale for physical/current acceptance. A separate routing-only transition proves that the five canonical board definitions change only by the declared routing object; it does not promote those historical model results. Actual current PCB evidence is separate.

## Remaining scope

The SRBV body and stepped carrier/shaft assembly, final solder process, harness handling and installed fit remain NOT RUN under #55/#65. The three front and two rear adapters preserve the selected mechanical proposal; renders are not physical qualification. The control board P is still incomplete under #39. Jack/core ground-current limits, rail/protection implementation and whole-instrument electrical acceptance remain open. No Gerber, drill, BOM or placement order files are generated.

Latest corrected native finish: PASS, 51 seconds; all five unchanged routing gates, 14 fixed-only and eight current-geometry/rule controls, fresh source checks and rear-label renders.

Final aggregate validation passed in 275 seconds. It legitimately changed AGND's exported net class from Default to Ground in the five netlists; the final native source checks are repeated against those actual outputs. No connectivity or component value changed. A high-quality fresh O3 top render replaced a basic render that omitted portions of the visible model/text; its board bytes did not change. All ten native copper SVG views and all front/back body arrangements were inspected.

Post-regeneration native/source checks and documentation build/site checks: PASS, 49 seconds. The existing single allowlisted workbench link exception is unchanged. Twenty-six related portable tests pass; label and native rejection controls pass. Source and DRC hashes were checked again before commit. Final integrated CI is pending.
