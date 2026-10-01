# Electrical-standard summary consistency

Issue #89 corrects summaries that were not updated after #49 and the later
external-source revisions. It changes the `Precision output` disposition text
in `electrical-standard.json` and the authored electrical-standard page.
All cell values, source requirements and hardware positions remain unchanged.

The initial 10 kΩ / 100 pF precision-feedback choice is identified as historical;
the current source uses 100 Ω jack feedback and 1 nF local feedback. Required
continuous delivery is 1700/1600/300 mA and transient delivery is 2000/1900/400 mA.
These are minimum required deliveries, not measured or available source capacity.
Maximum delivered-current limits remain 2100/2000/500 mA. Original pinned-source
ceilings and their preliminary deficit remain explicitly historical.

The fresh entry aggregate check passed at main410dfa9 through the pinned oracle
(guard exit0,197 seconds). Component evidence validation passed before and after
the correction. Four calculation/model reports bind the complete standard JSON;
they must be regenerated, preserving all numerical results and acceptance flags.
The powered-on precision-output diagnostic must run fresh rather than rebinding
its input hash. It still does not model physical relay switching or qualification.

Issue #10's original decision/handoff criteria were individually audited; its
closure waits for this consistency fix and checks. Later #49/#48/#52/#58/#59/#61/#62
supersessions do not establish hardware acceptance. Physical source capacity,
protection, procurement, assembly and bench qualification remain open.

Post-change verification passed: 24/24 fresh native model cases, 62 focused tests,
and exact equality of all four regenerated reports after excluding their input
hash maps. Full aggregate regeneration, component generation, documentation checks,
build and strict site checks passed under the guard (exit0,421 seconds). The one
existing workbench template-link exception remains allowlisted. Independent
read-only review found no blockers. CI remains the final exact-commit check.
