# Independent adaptive row arithmetic review

Reviewer `/root/math_review`, separate from implementation,2026-10-15 JST.
Synthetic continuation afteraf9a635a. No original data, authority or campaign work.

**PASS for the row-only compact dyadic kernel and unchanged mathematical proof.**
This review covers the row-only intermediate version identified below; a later
complete compact-scalar path requires its own review and retained results.

A compact pair(m,e) denotes the exact rational m*2^e. Its canonical nonzero
significand is odd; zero is exactly(0,0). Normalization removes only factors of2
from m and increases e equally. It therefore changes representation, never a
stored coefficient. Binary64 decoding is exact, including sign, subnormal and
normal exponents. Addition aligns both integers at the smaller exponent, checks
the shifted widths BEFORE allocation, adds exactly and normalizes. Absolute value
is applied after the exact symmetric half-sum, preserving cancellation. The final
row margin converts to the preceding denominator2^1075 with an exact left shift.
No tolerance, floating sum, symmetry assumption or original metadata enters it.

The row accumulator computes exactly
A_ii-sum_(j!=i)| (A_ij+A_ji)/2 |. Structural reverse lookup is unchanged and
one-sided support refuses. The producer/verifier select this row kernel explicitly;
root/deficit comparisons and tree-edge checks remain the old fixed kernel in this
intermediate version. Final margins, produced witness hashes and certified bounds
are identical to the fixed implementation. Exact row arithmetic does not alter
the stored operator, shifted-tree coercivity or interval perturbation proofs.

Review found two malformed-helper gaps before acceptance: zero shortcuts bypassed
tuple validation, and normalization could emit an exponent above the declared
range. The coordinator added canonical tuple/type/range checks before shortcuts,
raw integer checks before normalization, and a bound on its resulting exponent.
Nonzero even significands, noncanonical zero, booleans, float components and
malformed tuples now refuse. Alignment and final conversion width exhaustion
refuse; cancellation is not used as an excuse to allocate an over-cap temporary.
The2176-bit ceiling and exponent range remain explicit. A resource note about
checking width before allocating abs(oversized negative input) was separately sent
to the coordinator; internally produced row operands are already bounded.

[independent-compact-oracle.py](independent-compact-oracle.py) independently uses
Fractions rather than the fixed kernel as its primary arithmetic reference:

-1000 seeded IEEE pairs:2000 exact decode checks and6000 add/half/negation/absolute/
conversion/cancellation checks pass, including full exponent spans and signed zero.
-100 arbitrary nonsymmetric signed3×3 matrices spanning exponents−1000 through900:
300 exact row margins match both Fraction references and the fixed kernel.
-100 mildly nonsymmetric mixed-sign matrices with exact small diagonal deficits:
200 fixed/compact certified inverse bounds contain their exact inverse norms;
witness hashes and final bounds agree exactly.
-54 malformed tuple/type/exponent/normalization/alignment cases refuse.

The four main compact tests were independently rerun:PASS, observed0.277s.
They also compare grid4/8/held-out9 and complete virtual coupled results and call
the existing physical resolution functions. Results are retained in
[independent-compact-results.json](independent-compact-results.json), under the
established512MiB,20CPU-second,30wall-second and one-thread bounds. Summed independent
case kernel counts in the oracle are labeled as test work, not one candidate run.

| Reviewed row-only file | SHA256 |
| --- | --- |
| fixture/prototype.py | 5a5b41cb4027aaf9de8e7ad30a37450ccb1f14276644dfb6b2530c5919df8133 |
| fixture/test_compact.py | 351a0740a5a7adf3ac0630389a20e732fd8a3bf7c4dbe6887c24a9cd6f8ff6ba |
| independent-compact-oracle.py | a2e84dee7074564fa2071ddc89e9f18facd6d2505b0936235fc71a87b57954db |
| independent-compact-results.json | 94cc0551c27dd6e043115792dd65985bb54f5e31dd8a56995c8bf3174d25a58f |

This establishes exactness and bounded synthetic behavior, not a production bit-
work mapping or aggregate fit. The large fixed final conversion and remaining
fixed tree scalar operations are still charged. Original structural applicability,
useful physical attribution and admission remain unresolved.

The row-only source hash5a5b41cb... identifies a transient uncommitted intermediate;
no standalone source snapshot was retained. Its oracle and results remain intact.
The later compact_symmetric_margins(...,as_fixed=True) interface preserves the
row-to-fixed arithmetic control, but a rerun on later source will have different
source hashes and possibly different accounting. This is not claimed as bitwise
reproduction of the transient complete prototype.
