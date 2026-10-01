# Conditional partial-cell potential energy diagnostic

This unselected issue #38 diagnostic tightens the retained nominal B.Cu P1 potential-energy lower bound by integrating certified triangle subsets. It does not change the 44 model sources, native copper, sources, captured field, material/contact class, or acceptance limits. Current-inner containment in physical nominal copper remains an inherited premise. Manufacturing and joined electrical admission remain open.

The prior localization counts 68,987 whole inner B.Cu potential triangles and excludes 71,372. Its excluded-cell potential-energy uppers are 0.323186 and 0.496049 mΩ, larger than the complete variational gaps. These numbers do not establish a dominant physical B.Cu error.

## Exact chart and geometry proof

Ordinary nodes are recovered on the source 1e-9 mm grid. Barrel-interface nodes use exact rational centres on the 1e-6 mm grid, exact binary relative endpoints from the frozen barrel API, and exact retained longdouble affine parameters. Shared endpoint definitions must agree exactly and all sectors must telescope. Every vertex in both indexed meshes is checked before broad-phase exclusions are trusted.

The cached metric coordinates are a nominal rational chart enclosed around the reconstructed chart by the existing per-vertex arithmetic allowance:

`eta = 64 eps(longdouble) max(1,abs(x),abs(y)) + 32 eps(float64)`.

The 2 pm interface projection guard is not substituted for this arithmetic bound. Each triangle uses the maximum vertex eta. For edge halfplanes `a*x+b*y <= c`, the guaranteed interior uses `c-eta*(abs(a)+abs(b))`. Both triangles are eroded before exact rational convex clipping. Matching-vertex L-infinity bounds imply this interior is contained in the corresponding exact canonical triangle.

For potential triangle edge vectors d,e with positive determinant D, its actual area is bounded above by:

`A_plus = (D + 2 eta (norm1(d)+norm1(e)) + 8 eta^2)/2`.

The determinant lower must remain positive. The certified fraction is the sum of exact disjoint intersection areas divided by A_plus. A value above one is rejected, never clamped. Current fragments are checked pairwise for positive-area overlap; exact canonical target potential cells are checked against all nearby potential cells, including the already counted set. Duplicate IDs and adding to an already counted cell are rejected.

The spatial index supplies only outward bounding-box candidates. Adjacent binary64 values enclose longdouble conversion, and outward global-eta expansion encloses every canonical vertex. No floating polygon area or intersection predicate supplies a proof.

## Energy and bounded work

The retained potential is affine on each exact canonical cell. Exact rational gradient-numerator intervals include both endpoint coefficient errors after anchoring. The full-cell energy lower uses the lower squared gradient numerator and divides by the retained metric inflation; the upper uses the upper squared numerator and multiplies by that inflation. Exact arithmetic avoids a new floating contraction error. This preserves coefficient and metric costs before multiplying the LOWER by the certified area fraction. No error upper is scaled by a lower fraction.

Individual results are rounded outward to binary64 before aggregate exact sums; this prevents unbounded rational denominator growth. Geometry fractions remain exact until each final contribution is rounded down.

The source manifest selects at most 4,096 excluded B.Cu cells ranked by the sum of the two newly computed certified full-cell energy uppers, with ascending cell IDs breaking ties. These ranking uppers can be conservative and are not interpreted as mismatch. The ranking cap is 150,000 cells. The census and integration each stop at a 500,000-candidate budget; exact integration also has 500,000 clips and 1,000,000 overlap checks. A final query can reveal that one complete target would exceed a cap; that target is recorded without truncating its candidate list. An incomplete or rejected target contributes zero additional lower energy.

All old current energies, Green/source work, barrel contributions, and potential outer uppers stay unchanged. Every unprocessed target retains its energy allowance. The remaining uncertainty upper is the old excluded full-cell upper minus only the newly certified covered lower. It is not a physical error attribution. New region lowers must remain consistent with the old outer uppers and complete variational gap.

## Execution and evidence

The runner requires an explicit read-only artifact root and a fresh ignored output under its own worktree. It validates old input/native dependency hashes, matches executed model/helper copies to their historical hashes, pins the numeric library versions to capture, and checks reviewed core/runner hashes before and after analysis. It never copies, overwrites, or rebinds old receipts. It reconstructs unchanged geometry and interface endpoints without any current or potential solve.

Portable checks:

```sh
python3 -m unittest scripts.pcbgen.test_partial_cell_energy scripts.pcbgen.test_partial_cell_energy_run
```

A retained run must use the project heavy guard and the capture's Python environment. Supply `--artifact-root`, `--output`, `--frozen-core-sha256`, and `--frozen-runner-sha256` to `python3 -m scripts.pcbgen.partial_cell_energy_run`. `--census-only` performs no subset integration. A reviewed source freeze and manager go-ahead precede either retained mode.

## Reviewed bounded result

Independent review approved the frozen core and runner after 25 portable tests. The guarded census passed in 65 seconds and the guarded integration passed in 142 seconds. All 4,096 targets produced accepted conditional numerical subsets; none were rejected or capped. The run used 131,339 broad-phase candidates, 66,903 exact current clips and 73,917 overlap checks. Peak RSS was about 696 MiB. Complete canonical audits checked all 94,802 potential and 94,643 current vertices before any spatial exclusion.

The small [result receipt](./partial-cell-energy-receipt.json) binds both fresh ignored analysis outputs and the exact code/configuration hashes. The full integration receipt SHA-256 is `142d3675becc8357c1ba835ff1091478e09fff0caf7ef8027c9b81c6a2526523`.

The table is rounded for display; use the receipt's outward bounds for calculations.

| Captured unit source, reference TP990031:1 | Added potential-energy lower | Remaining excluded/unprocessed energy upper | Refined B.Cu mismatch interval |
| --- | ---: | ---: | ---: |
| J900134:2 | 0.312974 mΩ | 0.010213 mΩ | 0.132810–0.144503 mΩ |
| C107:2 | 0.485778 mΩ | 0.010270 mΩ | 0.178372–0.190178 mΩ |

The complete canonical mismatch uppers remain 0.184390 and 0.229967 mΩ. These results localize retained-trial constitutive mismatch under the inherited nominal inner-domain premise. They do not identify a dominant error in manufactured hardware or establish joined electrical acceptance. The independent fixed-depth source-lift lower is separate and must not be added again to these bounds.

No second refinement batch or native revalidation was run. If the ignored retained inputs/outputs are unavailable, retained revalidation is **NOT RUN**; portable analytic tests do not replace it.
