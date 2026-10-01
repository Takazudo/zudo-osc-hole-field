# Independent review: conditional PTH wall mean to internal B cut

Date: 2026-09-30. Read-only review of the standalone field, focused fixture and implementation note. No native run, full solver, shared-source edit or physical admission.

## Snapshot

- `scripts/pcbgen/pth_wall_to_b_cut.py`: `df1579322cbdfd5706a1c53709bc315994f585bf3bb18024d88716c4f901544a`
- `scripts/pcbgen/test_pth_wall_to_b_cut.py`: `308128a2263390f4c0e60b693c4108c06b6ea70c7716173c44ddd9e4f73fd261`
- `worker-reviews/38-pth-wall-b-cut-implementation.md`: `2aa93894e85ab34e8aa06ca275cd1b5e3451d09532a6f45e6cb631a404ebb669`

## Conclusion

No blocking mathematical error found in this conditional construction. The source and work note make no physical or joined-model acceptance claim. Closure is limited to the exact analytic field and outward resistance coefficient for the represented geometry and a pointwise resistivity ceiling.

## Independent trace and conservation check

Let D=ro²−ri² and D2=R²−ro². Lines 49–69 implement the stated stream function. Its mixed derivatives cancel in cylindrical divergence in each open region. Across z=L−d, Jz has the common value I(L−d)/(pi L D), independent of r. The tangential Jr jump contributes no distributional divergence. No discontinuity of normal current is hidden at that seam.

For any signed I, the shell inner-wall outward normal is −er, giving outward density −I/(2 pi ri L) and total −I. Its outer radial trace is zero below the sleeve, and +I/(2 pi ro d) in the sleeve band. The sleeve has precisely the same vector Jr at ro; its outward normal there is −er, so the interface flux cancels pointwise. Shell end-face Jz is zero at both z=0 and z=L. Sleeve Jr vanishes at R and Jz vanishes at L. At the internal sleeve cut z=L−d, Jz=−I/(pi D2); outward normal −ez gives +I/(pi D2), total +I. All signs reverse when I reverses; I=0 gives zero field. At the radial/horizontal corner, one-sided tangential values need not agree on the zero-area edge.

## Energy, units and arithmetic

The shell pointwise bounds are |Jr|≤|I|max(1,L/d)/(2 pi L ri) and |Jz|≤|I|/(pi D). Multiplication of their squared sum by shell volume pi D L and rho gives lines 93/106–108. The sleeve bounds are |Jr|≤|I|/(2 pi d ro) and |Jz|≤|I|/(pi D2), with volume pi D2 d, giving lines 94/109–110. The two metal volumes are disjoint up to their matching interface. Their energy sum is valid without an omitted cross term between these two pieces.

J has units A/mm²; rho times volume times J² gives ohm A². Replacing pi by 3 increases each positive bound. Fractions are constructed from the checked binary64 values before squared differences/products/division; `_up` returns an enclosing coefficient. The total is rounded from the exact rational sum, rather than from the separately rounded displayed components. No geometric tolerance interval is automatically covered: future interval admission must bound the coefficient over that interval, not presume monotonicity in every dimension. The field sampling routines use ordinary floating point and are diagnostic evaluations of the exact field, not interval-certified pointwise samples for arbitrary extreme exponents.

## Focused verification

Pinned solver Python ran `python -m unittest scripts.pcbgen.test_pth_wall_to_b_cut -v`: 3 tests PASS (reported test time 0.007 s). Independent small checks used three geometries and I=−2,0,+3; checked cut flux and the shell seam normal trace; exact Fraction comparisons confirmed each returned coefficient encloses the separately reconstructed rational bound.

An independent reduced one-dimensional energy integration used the analytic axial integrals and radial quadrature, avoiding the fixture's unsplit shell quadrature across the narrow top band. For the test geometry (.61,.635,.915,1.6,.035,.0175) mm at rho=2.3e−5 ohm mm, energy/I²=0.00015592890196362906 ohm, below upper 0.0013499085584935883 ohm. Two additional positive geometries likewise passed (upper/exact ratios about 4.0593 and 9.3061). These integrations are diagnostics; the pointwise-volume argument above supplies the bound.

## Required limits on later use

The actual domain must contain the complete finished circular wall/shell over L and the full same-net annular B sleeve over d, without another hole, cut or missing sector. The coordinate B foil must genuinely occupy [L−t_B,L], with 0<d<t_B<L. The supplied rho ceiling must cover all metal used. Neither the helper nor these tests establishes those facts for any of the 305 contacts.

The exported profile is on the internal annular cut ro<r<R, not an exterior B-face or an entire pad source. The full shell continues below that cut and carries nonzero axial current there; a downstream assembly must preserve this ownership and match the cut trace pointwise. Superposed downstream, zero-mean-wall or face-source fields on shared metal need their cross energy charged; merely adding their independent energies is insufficient. Exterior F/B annular injections, nonuniform wall redistribution, actual leads/solder/process and a continuous primal extension remain separate obligations exactly as the implementation note states. No matrix, common-path, source-current class or physical qualification follows from this closure.

`pnpm circuit:check` passed before and after recording this note. Reviewed source hashes were rechecked unchanged at completion.
