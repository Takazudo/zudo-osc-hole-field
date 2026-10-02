# Exact precision-feedback passive identities

The 16 captured precision-output feedback networks now select Yageo
RC0603FR-07100RL (100 ohm, 1%, 0.1 W at 70 C, 0603) and KEMET
C0603C102J5GACTU (1 nF, 5%, 50 V, C0G, 0603). Their retained manufacturer
product sheets were generated and inspected on 2026-10-02. Supplier order
codes, stock and factory allocation remain unverified.

Dedicated `r_feedback` and `c_feedback` roles preserve the previous generic
100 kohm and 100 pF representative identities. Circuit values, connectivity,
footprint geometry and all fixed panel positions are unchanged. Derived
symbols use the existing R0603 and C0603 family assets. The existing models
are nominal body illustrations, not maximum tolerance or installed-fit
proof. In particular, the capacitor's existing land geometry and model offset
remain unqualified; neither is promoted to exact vendor fidelity.

The resistor's 0.1 W rating applies at 70 C. The family voltage ceiling is
not permission to apply 75 V across 100 ohm; power, derating and fault duty
must all be satisfied. Physical output stability, tolerance, temperature,
protection, thermal behavior and assembly qualification remain open.
No fabrication or order files are created.

Validation completed before the first commit:

- Clean baseline regeneration: PASS, 268 seconds. Final full regeneration:
  PASS, 303 seconds, including native board ERC (zero errors, 673 retained
  warnings). The first runs exposed missing receipt hashes and stale master
  statistics; both were corrected from actual source/native outputs.
- Component contract: PASS, 68 manual inventory lines, no declared placement
  binding. Exact shortlist capture: 38/38. Fresh isolated native ERC: all 38
  symbols, 71 units and 244 pins, zero violations.
- Fresh simulations: 12/12 precision cases, 24/24 protection-candidate
  diagnostic cases and 13 mixer cases, PASS in 39 seconds. None is physical
  stability or protection qualification.
- Publication, regenerated footprint-selection manifest, documentation build
  and strict site checks: PASS, 39 seconds, retaining the existing single
  workbench-link allowlist exception.
- All 1,122 discovered unit cases are covered by passing group runs and
  targeted reruns. The legacy blank-MPN assertion was replaced with the two
  exact identities. Python 3.12 was used for report comparisons, matching
  regeneration; the retained numerical environment is Python 3.10. Its two
  floating-result report differences were not adopted. Three genuinely stale
  dependent candidate reports were regenerated and their tests rerun.
- The complete IO comparison changes only 32 symbol/MPN pairs and the bound
  native-netlist hash. A separate source-only epoch proves that the peripheral
  definitions remain unchanged. Historical native/model receipts are retained
  unchanged and are not made current by this proof. Historical local-artifact
  integration was NOT RUN in this clone.

The first CI run caught a stale generated standard-cell precision-output
sheet. The harness was regenerated from the exact roles, and its generator
was added to the aggregate regeneration command so future identity changes
cannot omit this output. A fresh native cell-harness check and CI rerun are
pending. Supplier allocation, factory solderability, installed
clearance, fault/thermal duty and physical output stability remain open.
