# Foil-collar native reconstruction: rejected local-only admission

This is a reproducible **UNSELECTED native experiment**, not a selected PCB or accepted electrical epoch. The constructor copies exact preserved JL/K inputs into ignored state, applies the bounded foil-collar source proposal, and retains complete native diagnostics. It does not write canonical or recovery boards. The companion JSON records the measured final results and artifact hashes; absent ignored artifacts mean actual native revalidation is **NOT RUN**.

Run preparation on the host with a fresh ignored directory, then run each board through the guarded pinned oracle:

```sh
python3 -m scripts.pcbgen.reconstruct_foil_collar --prepare /path/to/preserved/recovery --cache .circuit-cache/foil-collar-native-fresh
bash "$HOME/.codex/scripts/heavy-guard.sh" -- bash scripts/kicad/run.sh python3 -m scripts.pcbgen.reconstruct_foil_collar --cache .circuit-cache/foil-collar-native-fresh --run-board JL
bash "$HOME/.codex/scripts/heavy-guard.sh" -- bash scripts/kicad/run.sh python3 -m scripts.pcbgen.reconstruct_foil_collar --cache .circuit-cache/foil-collar-native-fresh --run-board K
```

An existing destination is rejected. A failed local-only delta gate returns a nonzero exit **after** writing the full diagnostic receipt; that result must not be called a passing native admission. The recorded native run uses KiCad 10.0.6, preserves all original project/rule/schematic companions, copies hierarchical sheets and relative libraries, and verifies their retained hashes after checking. KiCad's project metadata rewrite during SaveBoard is replaced by the independently retained companion before parity checks, not adopted as new authority.

The source construction preserves every full footprint/pad block and all unretired explicit copper byte for byte. It removes only the named JL stitch via/track, applies exact local zone-outline set differences, and adds the source-shaped connected pad/shoulder/neck/flare zone and JL paid dogleg/via. Existing outer-foil zone minimum thickness remains 0.150 mm. No original rule is relaxed. The candidate board and export receive new hashes; historical electrical receipts are never reused.

The filled-copper audit computes each original zone's symmetric difference before/after, then subtracts a predeclared local region derived from the source clips, source island/access geometry, exact retired copper and maximum retained clearance. That region is fixed before seeing the delta. Full outside-region polygons are retained. Their nonzero area is a failed local-only admission even when native rule, parity or connectivity checks pass.

The audit separately records copper-region component/hole counts and compares the complete physical connectivity partition of all existing named pads/tracks, excluding only the explicit retirement/addition IDs. It also compares the complete named open-edge inventory. Native DRC's reported unconnected list is truncated on large boards; it must not replace that complete native connectivity accounting. Reported warnings and their identities remain unresolved evidence, not waived checks.

A bidirectional native polygon-offset diagnostic measures how much offset is needed to cover the changed material outside the declared region. It reports the largest failed and smallest tested covering offsets, 0.001 mm search resolution and 0.0001 mm offset-polygon approximation. This is a geometric diagnostic, not an exact Hausdorff certificate, manufacturing tolerance, electrical perturbation bound or retrospective permission to pass the failed gate. Connectivity equality does not prove a preserved minimum neck width or resistance.

Diagnostic v1 failed on copied-project context and rewritten metadata, rather than a demonstrated copper conflict. After those defects were corrected, v2 JL had zero native rule errors and parity issues, with its complete 1,063 open edges and 507 reported warnings unchanged. The later v3 audit found 3.007403563 mm² of JL B.Cu filled-copper change outside the declared region. Source zone outlines themselves have zero outside-region area change on every foil. An unchanged-board refill adds 0.216777277 mm² on JL F.Cu; reapplying exact source net classes gives the same control result. Neither the baseline regeneration difference nor the further collar-associated fill changes is admitted. Failed and exploratory artifacts remain separate from the final diagnostic run.

The native collar screen examines the entire nominal 0.200 × 0.760 mm section without endpoint trimming, including the complete same-face copper union and absence of other-foil copper in the side-isolation window. It checks actual connectivity to the retained AGND members and any new paid via, unchanged mask openings, absence of mask graphics across the dry section, and inherited two-face tenting for the new via. Nominal CAD mask coverage is not a measured mask seal. Manufacturing tolerances, actual full-section geometry/material pullback, three-dimensional solder support and complete field extension remain open.

A fully isolated straight prism with net current crossing every section would also yield a conditional series lower reference by Cauchy: `rho_min * L_min / A_max`. The proposed numbers give approximately 0.699 mΩ per neck, versus the straight homogeneous upper reference 1.582 mΩ. These calculations are not admitted for a sheared/nonuniform manufactured class, a bypassed collar, or an unqualified assembled harness. They cannot establish the selected GH current limit by themselves. Both collar costs remain inside the tested assembly once; JL/K board-side flare, via, annular and spreading costs stay separately paid.

The original 0.5 mΩ common, GH 0.5 A/contact, rail 1 mΩ, distribution 20 mV and full-path 0.20 V targets remain intact. Fixture isolation/local power certification and test-to-installed/remated-contact applicability remain open. Other GH grounds, harnesses, boards and main wires prevent whole-board V/I_total from certifying this individual return. All physical and joined electrical gates remain open irrespective of the native local-geometry findings.

Exact local refill invariance is this experiment's boundary, not an original project acceptance target. The smallest next correction is to declare the complete refilled JL/K copper as a new draft geometry epoch, retain every measured difference, and require fresh matched electrical witnesses against those actual full exports. This avoids treating historical fill as an additional hardware constraint. Original electrical and physical requirements still apply without relaxation.

The shoulder excess needs a bounded geometry classification against the prospective source envelope; it does not automatically invalidate the separately checked dry prism when its intersection with that prism's guard is zero. A reviewed shoulder/fill representation can become the nominal geometry for a finite manufacturing class, but neither a small area nor unchanged connectivity bounds its current/energy impact. No tolerance is retroactively applied to this failed local-only experiment. Any later selected candidate requires fresh geometry extraction, complete matched current/potential construction and current-source electrical admission.

## Recorded final diagnostic results

| Check | JL | K |
| --- | --- | --- |
| Preserved full footprint blocks | 1,099 | 3,793 |
| Full nominal dry prism, no trimming | PASS | PASS |
| Existing physical connectivity partition | Unchanged | Unchanged |
| Complete named open edges | 1,063 | 7,354 |
| Native rule errors | 0 | 1: equal-priority AGND zones intersect |
| Schematic parity issues | 0 | 0 |
| Reported warning records | 507, unchanged | 551, unchanged |
| Largest material-set offset established by this diagnostic | NOT ESTABLISHED for B.Cu | NOT ESTABLISHED for F.Cu |
| Local-only admission | FAIL | FAIL |

The limited offset search fails to enclose JL B.Cu and K F.Cu differences within its search range, including after native Unfracture normalization. This is an inconclusive diagnostic, not a certified physical displacement greater than 1 mm and not permission to dismiss fragments as harmless tessellation. JL F.Cu has a tested covering offset of 0.195 mm at 0.001 mm search resolution and 0.0001 mm offset approximation. Both collar-polygon overshoots have a tested covering offset of 0.001 mm with those same numerical limitations, and exactly zero overlap with their complete dry-neck guards. JL excess is 8.8809e-8 mm²; K excess is 1.290325e-7 mm².

JL v5 also failed its final source-hash guard because an extra diagnostic edit landed after queued execution started. Its individual completed check artifacts remain available, but a passing current-constructor execution receipt was not invented. Separately hashed read-only probes bind the supplemental measurements to the actual candidate and frozen proposal. K completed against the frozen constructor and produced an explicitly rejected native receipt. These distinct execution/provenance outcomes remain in the JSON.

K's concrete `zones_intersect` error arises because both the existing F.Cu AGND zone and the new AGND collar have priority 0. The smallest source correction is an explicit distinct priority for that owned collar, followed by a K-only native rerun as a new full-refill epoch. Changing priority is a source correction; suppressing the rule would be a waiver and is not proposed. JL's historical hashes must remain unchanged by that K-only correction.
