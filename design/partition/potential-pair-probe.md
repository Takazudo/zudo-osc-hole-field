# Retained P potential pair and complete-region diagnostic

This diagnostic captures the same two continuous potential trials as the
retained P pair: `J900134:2 − TP990031:1` and `C107:2 − TP990031:1`.
It does not change copper, finite source profiles, material, wetted-terminal
restrictions or any of the 44 historical model inputs. Every hardware design
remains an unvalidated draft. This is not a common-region allocation or a
proof of the 0.5 mΩ target.

## Immutable potential capture

`potential_pair_probe.py` checks the complete retained native prerequisite and
input closure, reconstructs the unchanged restricted potential operator, and
records its one two-column solve. The recording proxy is installed after
restriction. It checks each refinement operand and reproduces the exact
sequential float64 update order, gauge, call count, and equation residual.
Original port identities are mapped through exactly unit reduced projection
rows. Canonical finite interface traces are reconstructed from their endpoint
values, with nodal conversion errors retained. Arbitrary reduced indices are
never substituted for old port indices.

Executable and exact parsed manifest bytes are snapshotted before work and
verified again before publication. Restriction equality uses canonical JSON:
tuple/list serialization differences are normalized, but geometry, tied
indices and every numeric value must agree exactly.

The first guarded attempt (`potential-pair-v1.log`) failed before solving
because it compared in-memory geometry tuples against JSON lists. Its log is
preserved; no v1 result was rebound. After the exact comparison fix and mutation
regressions, the separately named v2 capture passed:

| Artifact or check | Result |
| --- | --- |
| Receipt | `.circuit-cache/issue38-recovery/potential-pair-v2/capture.json` |
| Receipt SHA-256 | `6df84e4db0e09820184597ffbacef668322918ea540ad876ea766054de8d04c6` |
| Field archive SHA-256 | `98c43c3d4a0cca542e37aa31cc3e38e7fb7f9f74abe2d6909954a42ace0e9d0c` |
| Captured shape | 265805 × 2 |
| Solve/refinement calls | 1 / 0 |
| Independent equation residual | 6.984919309616089e−10 A |
| Maximum lower-matrix change | Exactly 0 Ω |
| Maximum canonical versus projected trace difference | 2.717746896944715e−20 |
| Runtime / peak RSS | 30.16 s / 1641880 KiB |
| Heavy guard | PASS, 31 s |

No global current solve was performed. The existing constructor rebuilt local
barrel operators, including their local current bases. These local solves are
part of the reported runtime. The captured fields and receipt are immutable;
the separate localization module consumes them without another global solve.

## Complete-region mixed-work proof

Take current positive outward from each complete barrel into a foil. For a
continuous potential `v`, the complete foil mixed work is

`W_foil = −Σ_ports I_port mean(v)_port − f_foil(v)`.

The complete barrel mixed work is `+Σ_ports I_port mean(v)_port`. Its current
trace is uniform on each sector and potential is linear along it, so the exact
mean is the average of its two endpoint values. The depth-constant foil
potential pairs to zero with the vertical source-lift current, but the finite
source functional `f_foil(v)` remains in Green's identity. All source patches
are integrated once over complete grid-exact potential triangles using the
same reduced field. Partial cuts and non-unit source projections fail closed.

The retained raw barrel coefficients need not sum to zero. The reference
keeps the old internally repaired shell, whose trace is `P α`, and replaces
only the radial collar current `α` by `P α`. The additional squared norm is
bounded by `Σ collar_diagonal (P α − α)²`. This is not a claim that newly
reconstructed and old current bases coincide. The old complete correction
bound and this collar shift combine by the norm triangle inequality.

For each foil, a continuous local barrel test extension equals that foil's
centered trace and zero on every other band. Cauchy bounds the discrepancy
between reference and globally conserved port work using the complete
correction norm and the sum of these extension energies. A single constant
is used per complete foil, including in `f(v−c)=f(v)−c f(1)`; all barrel
contributions are accumulated before charging the source once. A whole-barrel
constant is harmless because its balanced trace has zero total current.

The 199 disjoint regions are the four complete foils and 195 complete
barrel/collar domains. Current and potential energy intervals and signed
mixed-work intervals give `E_q + E_v + 2 W`, an interval for constitutive
mismatch. Negative upper bounds, inverted intervals and incompatible summed
lower bounds fail. Nonnegativity may improve a lower bound only.

Potential energy uppers integrate every outer-envelope cell. Potential energy
lowers include only entire cells covered by the inward-guarded inner copper
envelope. Excluded or crossing-cell energy is reported separately: it is not
identified as physical error or absent copper. Metric integration is streamed
and two-sided; upper-Gram off-diagonals are never treated as exact mixed work.

The canonical physical source functional and outer potential-energy upper
also give an independently evaluated dual lower. Its global mismatch budget
is reported separately from the original API variational gap, including any
additional enclosure looseness. Regional mismatch uppers are not exact
physical error, and trial energy alone does not identify a defective region.

## Scope of follow-up

The separately reviewed localization passed in 29.76 s, peak RSS 844724 KiB,
with heavy-guard PASS (30 s). Its immutable receipt is
`.circuit-cache/issue38-recovery/potential-localization-v1/localization.json`,
SHA-256 `4bab35c0b49a7208da578d41250ff8ea3cee9e5dd6fe01a5af16079263d7544a`.
The table displays approximate values in mΩ; the receipt contains outward
bounds and exact finite-source functional values.

| Quantity | J900134 pair | C107 pair |
| --- | ---: | ---: |
| Original API variational gap upper | 0.1844188495 | 0.2299970975 |
| Independently evaluated canonical mismatch upper | 0.1843899413 | 0.2299670386 |
| F.Cu mismatch upper | 0.0076846356 | 0.0076663388 |
| In1.Cu mismatch upper | 0.0006586366 | 0.0006554219 |
| In2.Cu mismatch upper | 0.0104074456 | 0.0103571962 |
| B.Cu mismatch upper | 0.1445027260 | 0.1901776321 |
| Sum of all barrel mismatch lowers | 0.0098005165 | 0.0097996997 |
| B.Cu excluded/crossing-cell potential-energy upper | 0.3231863769 | 0.4960486842 |

Every foil mismatch lower is zero. B.Cu's large upper does **not** establish
that its actual mismatch dominates. Whole-cell inclusion retains only 68987
of its 140359 potential triangles; the excluded potential-energy upper is
larger than the complete mismatch budget. In1.Cu retains no whole cell under
this strict rule, also explicitly reported. This geometric lower-enclosure
loss, rather than evidence of a defective physical region, limits attribution.
The canonical dual is slightly stronger than the API lower here because its
separate physical energy evaluation avoids some API numerical allowances;
neither receipt is overwritten or relabeled.

The smallest justified next diagnostic is a reviewed, conservative partial-cell
potential-energy lower on B.Cu using the same retained fields and inner copper
envelope. A P1 gradient is constant on each affine cell, so a certified lower
intersection area can recover part of the excluded energy without a new
solve. Floating polygon intersection areas alone are insufficient: the area
and metric containment need explicit outward arithmetic or an inscribed
geometric construction. No such follow-up is implemented or claimed here.
The current evidence does not justify releasing the wetted restrictions or
performing another full solve.

A missing finite trace,
source coverage or geometry obligation must produce an explicit failure,
while leaving the verified potential capture intact. No mesh refinement,
restriction release, new global current solve or whole-basis rerun is part of
this diagnostic. The original current archive and all earlier receipts remain
unchanged.
