# Independent resource review: bounded weighted increment

Reviewer: separate `/root/resource_review` agent, 2026-10-15 JST.
Scope: source inspection and independent execution of bounded synthetic fixtures.
No original numerical archive was decoded; no diagnostic, baseline, grant,
qualification, key operation or production execution occurred.

**Verdict:** ACCEPT the bounded synthetic increment and its negative method
result. REJECT direct original-size deployment of this fixed eight-pass producer.
It is not an eligible reason to spend a diagnostic. No production fit or scalar
counter remapping is approved. The valid weighted verifier remains useful local
infrastructure even though this particular weight-production recipe fails the
rooted grids and has a separate conditional cost obstruction.

## Reviewed identities and independent execution

SHA256 identities at review:

- `fixture/prototype.py`: `78c5e38f29a065010bdb42f7ffd042e666c7465b60166d700e0c0e180944fe33`
- `fixture/test_weighted.py`: `2d778f8722d1984f5174c0bb3150be99a7bd1f251a06bb89316c75f9291f07ac`
- `fixture/test_prototype.py`: `d232775271f3647cbe5a425a8a0d93ed4820f4c37c20d69a07e3c92951bd74e4`

Executed both runners independently using the established numerical venv,
`python -B`, one BLAS thread and outer `timeout 30s`. Each runner enforces
512 MiB address space and 20 CPU seconds before numerical imports. The legacy
18 tests PASS (0.064s unittest time); the weighted eight tests PASS (0.896s).
The final eight-test suite also verifies deterministic producer output with exact-oracle functions patched to fail if called, the retained incomplete-grid factors, and a mixed-sign coupled case.
Order remains at most 128; dense exact reference inversion remains at most 16.
No dense residual, global inverse or auxiliary solve is in the candidate path.

Representative candidate invocation measurements from this independent run:

| Case | Result | Cumulative kernel charges | Peak reserved slots | Traced peak bytes | Wall seconds |
| --- | --- | ---: | ---: | ---: | ---: |
| Rooted grid 4 | REFUSED, q=1.0174973682921387 | 2345 | 323 | 7168 | 0.02059 |
| Rooted grid 8 | REFUSED, q=1.017614535203576 | 10073 | 1283 | 32876 | 0.08934 |
| Held-out rooted grid 9 | REFUSED, q=1.0169453661652166 | 12840 | 1623 | 42198 | 0.11371 |
| Floating KB joined to grounded KA | CERTIFIED | 658 | 130 | 8572 | 0.00697 |
| Weak-ground coupled, screen inconclusive | CERTIFIED | 658 | 130 | 9244 | 0.00695 |
| Boards pass, Schur refuses | REFUSED | 438 | 122 | 9280 | 0.00566 |
| Disconnected wire, Schur refuses | REFUSED | 648 | 130 | 9425 | 0.00677 |
| Retained incomplete grid 4 | CERTIFIED, inverse <=51.55444466703878 | 4757 | 391 | 10494 | 0.03157 |
| Retained incomplete grid 8, weak ground | REFUSED, q=1.0171011427090524 | 22106 | 1607 | 57366 | 0.14696 |
| Producer overflow refusal | REFUSED | 14 | 38 | 3087 | 0.00046 |

Observed process high-water RSS reached 69,548 KiB. That is cumulative process
RSS including imports and independent oracle/fixture work, not an individual
candidate allocation peak. Traced bytes and wall time cover the measured
candidate invocation, excluding prebuilt inputs, subsequent physical evaluation
and reference solves. Tracemalloc is not a complete native-allocation metric.
The independent address-space cap covers the whole worker. None of these tiny
measurements extrapolates to the original operation's memory or deadline.

## Accounting and allocation lifetime

All factor production, eight weight passes, exhaustive outward residual work,
comparison applications, signed solves and small Schur work use one cumulative
Meter per candidate invocation. Both boards share it. Counters are not reset on
refusal. Every attempted factor product, including dropped destinations, stays
charged. The failed 100-update test retains the exceeding charge and the same
sum of phase counts. Completed weight passes and emitted packets are recorded.
There is no auxiliary numerical system in this producer (order/work zero).

The historical finer convention is preserved: a scalar multiply, subtract, add
or divide, or one interval primitive call, is a charge; an interval multiply
internally evaluates several endpoint products. This is neither a FLOP count
nor the production scalar Schur-update convention. Absolute values, comparisons,
index operations, validation scans, hashes, JSON copies and container allocation
are runtime work outside this floating-kernel counter. They remain subject to
the actual worker limits. Three midpoint arithmetic operations per tiny Schur
entry are now explicitly charged as inverse production; the older reports and
counts are retained as historical evidence, not overwritten.

Review found an oracle-control setup factor producer outside the reported
cumulative candidate meter. This was corrected: it now has its own cumulative
oracle preparation meter, phase totals and retained-board allowance, and a
combined kernel count is reported. It is explicitly reference-control preparation,
not candidate output. Exact Fraction reference operations and actual resolution
functional evaluation remain outside the candidate counter and are labeled as
such. Consequently the reported kernel totals are not a complete physical
pipeline operation count.

The former residual loop reduced its live-entry reservation while the final
row dictionary was still alive. `residual_rows` now deletes both `put` and `row`
before decreasing that reservation, on every producer and verifier row. The
independent regression uses weak references to actual dictionary instances and
frame inspection: all 144 dictionaries from eight order-16 producer passes plus
one verifier pass have died at their corresponding reservation decreases. A
remaining scalar interval is covered by the explicit vector/scratch allowance.
This corrects toy accounting lifetime; it establishes no historical production
memory breach.

Weighted storage reserves retained factor entries plus pattern entries plus
16n vector/scratch slots and the live streamed row. This accommodates the weight
packet, old/new iterates, RHS and comparison vectors, residual output and signed
solve overlap in these fixtures. The coupled routine reserves 12m^2 tiny-system
slots and carries earlier board allowances forward, rather than discarding them
from the count when the next board starts. The reserve overcounts released
vectors but does not turn slots into bytes. Original CSR/B inputs, Python object
and list overhead, JSON/hash copies, caller-owned control packets, imported
libraries and exact-oracle matrices are governed by actual bounded process
resources. A production layout would require a fresh byte/lifetime proof for
all inputs and outputs and both boards; a small factor count supplies no such
proof.

For example, the held-out order-81 candidate records production 80; weight
residual 8480; weight RHS 648; weight comparison 1928; outward residual 1060;
residual comparison 241; weight scaling 162; ones comparison 241, totaling
12840 without acceptance. All discarded weight-production effort is included.

## Original-size obstruction and next decision

Let n be a board order, E the strict-L plus strict-U entries, and F=n+E.
For any connected union of factor graphs, E >= n-1. Exhaustive logical LU
multiplication requires

    Wprod = sum_k (1 + nnz(strict-L column k)) nnz(U row k) >= F.

Each implemented producer pass alone charges at least 2 Wprod + 2 E + n:
residual multiply/subtract, comparison multiply/add, and U diagonal division.
This intentionally omits residual weighting/reduction, adding ones and all other
work. Eight passes therefore require at least 56n-32 primitive charges per board.
At retained original free orders 1,513,837 and 1,541,278, that is

    56 (1,513,837 + 1,541,278) - 64 = 171,086,376.

Even an optimistic hypothetical contribution model assigning one charge to each
LU product and one to each strict-factor comparison contribution needs

    8 [(2nKA-1)+(nKA-1)+(2nKB-1)+(nKB-1)] = 73,322,728.

Both exceed 20M before factor production, independent verification, signed
factor solves, Schur, functional work or complete-operation overhead. The second
number is a conservative obstruction under that hypothetical mapping, **not an
approval of it**. Any proposal to use a different mapping for a fit claim still
requires explicit production-loop correspondence and independent resource review.
The connected-factor hypothesis is essential; these bounds do not reject every
possible weighted certificate or disconnected factor pattern.

Independently of scaling, this exact eight-pass recipe emits positive weights
but fails outward contraction on the retained 4/8 grids and held-out 9 grid,
including the specified weak-ground cases. The retained incomplete 4-grid does certify with a better inverse bound than its unit-weight control, while the incomplete weak-ground 8-grid refuses. This positive bounded outcome does not remove the rooted-pattern or original-size obstruction. Oracle weights remain distinct
controls. Increasing the pass count would increase an already rejected cost;
no original-data characterization is needed to decide against this recipe.
The justified next local action is a method change with a predeclared pass/work
budget and an analytic useful-weight rationale, reusing this verifier and these
negative controls. It is not another full qualification, a baseline, a cap
increase, or reuse of a consumed request.

The 180-second guard entry, 1216 MiB worker, 2 GiB aggregate including reserve,
zero-operation-swap, 64 MiB output and existing certificate input/live/update
limits remain unchanged. Complete original-pipeline resource qualification is
NOT RUN and NOT QUALIFIED; production remains NOT ADMITTED.
