# Conditional edge-bubble current probe

This issue #38 diagnostic enriches the retained P current trial on at most 128 ordinary B.Cu interior edges. It does not change geometry, material, full finite source/port normal flux a.e., the vertical source lift, potential restrictions, electrical targets, or hardware status. Tangential current jumps are allowed. No current/potential solve, local operator construction or matrix factorization is used. Current-inner containment in nominal copper remains an inherited conditional premise; actual manufacturing/contact and joined electrical admission remain open.

The source pair is J900134:2 and C107:2, each returning to TP990031:1. Both U/L and raw-to-conserved correction energies come from the SAME paired regional receipt that hashes current-fields.npz. The separate 343-column receipt supplies only geometry/ownership and model provenance; its matrix is never substituted for the paired result. Historical receipts stay unchanged in an explicit read-only artifact root.

## Conserved enrichment

For two nonoverlapping triangles sharing AB, ψ=λ_Aλ_B is continuous on the pair and zero on its outer boundary. Its clockwise curl c=(∂yψ,−∂xψ) has zero divergence, matching shared normal traces, and zero outer normal trace. Extend the sheet perturbation as Jxy=c/t,Jz=0. This preserves every prescribed finite source density and normal flux, including nonzero source triangles. It leaves the fixed linear-depth source lift unchanged.

Ordinary vertices are reconstructed on the exact source grid. The existing canonical chart verifies all vertices before spatial exclusions; interface endpoints come from the unchanged barrel geometry method on a descriptor reproducing its constructor's exact scalar operation order. No constructor is called. Selected cells cannot contain interface vertices, cross any complete barrel polygon, or overlap another current cell in positive area. A barrel cut through a patch is rejected even when none of its interface vertices belongs to that patch. Exact convex clipping supplies these checks; floating indexes provide outward candidates only. Whole physical inner-domain containment is still inherited, not newly proven by these local tests.

Raw currents use the saved local outward face fluxes and the canonical RT0 formula q(x)=Σf_i(x−v_i)/(2A). Opposite-vertex fluxes are permuted together with clockwise triangle vertices. Both q and c are affine, so their work uses exact polynomial integration:

`∫u·v = A/12 [Σu_i·v_i + (Σu_i)·(Σv_i)]`.

The nominal represented sheet-resistance scalar follows the historical constructor's arithmetic. An upper-only metric off-diagonal is never treated as exact physical work.

## Selection and complete matrix bound

The fixed manifest ranks ordinary interior edges by a floating proxy: squared midpoint tangential flux jump, summed over both columns, divided by edge-length squared times the sum of reciprocal adjacent areas. This is selection only. Ties use ascending endpoint IDs. Greedily choose at most 128 patches sharing no triangle, before exact proof checks. No replacement follows rejection. The topology cap is 500000 edges and exact overlap-check cap 100000. Every unprocessed/rejected patch contributes zero perturbation. A finite binary64 rounding of each -g/h chooses an explicit coefficient; optimality is not assumed.

For conserved trial Q_i and saved raw field q_i, C_i bounds `||Q_i−q_i||²`. C has units Ω, its square root sqrt(Ω), and the work uncertainty against W_j is `sqrt(C_i H_jj)` Ω. Form the complete perturbation Gram H and raw work G exactly over all accepted disjoint patches, then charge C once per combined column. Enclose

`A_ij=<Q_i,W_j>+<W_i,Q_j>+<W_i,W_j>`.

If M and r are symmetric midpoint/radius matrices for A, then `U_new=U_old+M+diag(row_sum(r))` is a valid upper Gram by the absolute row-sum PSD bound. Final float serialization receives its own matrix rounding allowance. Keeping only diagonal improvements would be invalid. Exact symmetry/PSD and old/new transfer-interval consistency are mandatory; contradictions fail rather than being clipped.

The unchanged L and both valid U bounds give whole-domain polarization intervals; the result reports their intersection. A worse or unchanged new bound is retained honestly. Even an improved single-pair result cannot establish the original common≤0.5mΩ requirement for the full instrument. No private-access diagonal is removed.

## Verification and lifecycle

Focused fixtures cover exact energy reduction 1→2/3 with preserved full traces, two-column Gram composition, nonzero source divergence, nonzero raw-to-conserved correction, zero improvement, malformed shared/outer traces, invalid overlap, an interface cut without selected interface vertices, descriptor operation identity without construction, paired-epoch/artifact mutations, matrix-rounding enclosure and contradiction rejection.

The runner snapshots manifest bytes and reviewed source/helper hashes before substantial work, verifies all historical native/model dependencies and the imported project-module closure, and verifies again before publishing. It requires the retained numerical library versions and a fresh own-worktree ignored output. Failures produce a separate failure record, not an energy bound. The reviewed guarded retained experiment is recorded below; hardware/common admission remains open.

Portable tests:

```sh
python3 -m unittest scripts.pcbgen.test_foil_edge_bubble_probe scripts.pcbgen.test_foil_edge_bubble_run
```

Retained runs use the existing solver venv through heavy-guard and require `--artifact-root`, `--output`, `--frozen-core-sha256` and `--frozen-runner-sha256` with `python3 -m scripts.pcbgen.foil_edge_bubble_run`. The old artifacts are neither copied over nor rebound to current native/model hashes.

## Reviewed retained result

The one frozen retained run passed in 13 seconds (10.392 seconds measured in the runner), with peak RSS 566800 KiB. It audited all 94,643 current vertices, ranked 168,632 eligible edges from 236,116 total edges, selected 128 triangle-disjoint patches and accepted all 128 after 4,285 exact overlap comparisons. No patch was rejected or capped. All 167 historical input hashes and 47 executed source/configuration hashes were checked. No solver, factorization, source change or second patch batch ran.

The small [result receipt](./foil-edge-bubble-receipt.json) binds the original ignored result, SHA256 `ab9748a1f7775a5e61f846d9778ef7e9d1eaae01378ae6191e4e38791be6e9b1`, and the executed commit/source hashes. A receipt-only exact arithmetic replay reproduced the patch sums, correction allowance and final upper matrix. The old upper minus the new upper is also exactly PSD for this result; this is checked evidence, not a requirement assumed by the general construction.

Displayed values below are approximate; the linked receipt contains the outward bounds.

| Unit source, each returning to TP990031:1 | Old current-energy upper | New current-energy upper | Certified reduction lower |
| --- | ---: | ---: | ---: |
| J900134:2 |0.887280mΩ|0.859051mΩ|28.229556µΩ|
| C107:2 |1.253563mΩ|1.204631mΩ|48.931788µΩ|

The whole-domain transfer interval narrows from approximately 0.439020–0.644971mΩ to 0.452958–0.621126mΩ. It still straddles the 0.5 mΩ target; this pair neither proves pass nor proves failure. The result demonstrates a concrete reduction of the retained current-trial upper energy while preserving the full prescribed normal traces. It does not attribute all remaining mismatch to the current discretization, prove manufactured copper performance, or establish the instrument's complete common-region/source accounting. The old potential lower, source-lift ansatz and all actual physical qualification gates remain unchanged.
