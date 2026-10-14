# Technical acceptance remains unresolved after the construction study

Independent source/mathematics reviewer: `/root/certificate_feasibility`.
Reviewed executable checkout:5aec693549a9e380d7e7832a430f5294dacbaf05.
No original artifacts were opened; no implementation or campaign state changed.
This is a negative feasibility finding, not an approval of another checker/run.

## Conditional theorem

Let x contain every original free KA/KB node and terminal variable, with held KA
nodes fixed to zero. An exact construction reference Q can sum original P1 element
energies after the original coordinate/ring mapping, every consecutive barrel
interval, complete distributed terminations and all live wires. Positive physical
conductances and exact PSD element terms make Q positive semidefinite. Grounding
must eliminate every zero-energy mode of the COMPLETE joined construction; a
floating KB must be constrained through its actual terminations/wires to KA.

If a rigorous witness proves x^T Q x >= alpha ||x||2^2 with alpha>0, and an exhaustive
comparison proves H=(M+M^T)/2=Q+E with ||E||inf <= epsilon < alpha, symmetry gives
lambda_min(H)>=alpha-epsilon and ||M^-1||inf<=sqrt(N)/(alpha-epsilon).
That theorem preserves the original solver/RHS/tolerances and residual enclosure.
The inverse bound must also be useful for the unchanged resolution gates; a huge
bound and bare positivity do not establish a resolved TP990026 reaction or Stage C.

## Source evidence and missing witnesses

The source supports the form of this argument:

- scripts/pcbgen/sheet_mesh.py:203–215 forms Gram-like element stiffness, applies
  metric factors, casts to binary64 and accumulates COO entries.
- finite_adapter.py:173–179 merges tile stiffness through the original node map;
  :203–214 applies process scaling and consecutive barrel stamps.
- finite_solve.py:206–230 restricts held nodes and constructs distributed
  terminations; :296–303 supplies live-wire coupling.

It does not supply a quantitative certificate. The missing technical evidence is:

1. **Bound element-level witnesses.** finite_adapter.py:138–139 exports tile
   coordinates and assembled COO entries but only a triangle count. It does not
   export triangle connectivity, original gradients, areas, metric factors or
   accumulation-error enclosures. The Gram form inside Sheet cannot simply be
   asserted for the exact stored aggregate. Any recovery route needs a demonstrated
   binding back to that original matrix; unbound reconstruction is insufficient.
2. **A quantitative grounding margin alpha.** Connectivity alone is insufficient.
   Verify local coercivity constants and a complete grounded path/frame bound,
   including ring collapse, all copper, actual support weights, floating KB and
   every required wire. No such usable margin is in the retained aggregate metadata.
3. **An exhaustive error bound epsilon.** Cover element evaluation/casts, tile and
   class accumulation, process scaling, barrels, termination products/divisions
   and final free-operator assembly. Four mismatch samples, coefficient maxima,
   partition tolerances and topology checks cannot provide this bound.
4. **Correct termination energy.** It is (w^T v-t)^2/Rt, not the sum of independent
   positive edges w_i(v_i-t)^2/Rt. The latter can overstate coercivity. Approximate
   unity/nonnegativity checks at finite_adapter.py:189 do not prove exact unit-sum
   or nonnegative weights; use exact stored weights or rigorous error enclosures.
5. **Unchanged-budget verification.** Include all original mesh/mapping passes,
   interval operations and live evidence, preserving the existing nine-pass
   accounting obligations. Even a nominally linear algorithm has no demonstrated
   fit under4M live entries,20M arithmetic updates,1216MiBworker and180seconds.

## Actual decision and next local action

No minimal construction-based replacement is ready for implementation or a new
campaign claim. The precise prerequisite is a retained witness proving a useful
positive alpha-epsilon AND a verification procedure within the unchanged complete
operation budget. No source assertion, alternative ordering name, faster code or
signature can replace those quantities. Natural and RCM failure do not prove every
possible certificate impossible, but they provide no approval of a third attempt.

Stop numerical attempts at **technical acceptance unresolved**. The WSL coordinator
retains responsibility for a future proof-and-witness design addressing the five
specific gaps above. Keep it source-only until an actual eligible guarded diagnostic
or corrected full qualification can be concretely reviewed. Do not introduce another
generic checker, unbound mesh reconstruction, new geometry experiment, hidden RHS,
cap increase or unchanged retry. No new owner-policy decision is required or implied
by this report; the signing owner/delegation remains resolved.
