# Independent floor from the retained vertical source lift

This is a mismatch floor for the **fixed retained linear-depth current trial
and depth-constant potential trial**. It is not a floor for arbitrary admissible
3D currents, physical resistance, or a qualified manufactured board. No common
allocation or issue38 target is accepted by this calculation.

For scalar isotropic foil resistivity, the retained current is
`q = (q_xy, q_z)` and the canonical potential has `∂v/∂z = 0`. The exact source
lift `q_z` varies linearly from zero at the opposite face to the prescribed
signed source density at the electrode face. The full foil mismatch splits:

`η² = ∫ρ |q_xy + ∇xy(v)/ρ|² + ∫ρ q_z² ≥ E_lift`.

The retained conservation construction changes only in-plane RT currents and
barrel currents; it does not change this vertical component. Therefore the
global current-correction norm does not need to be subtracted from this
independent floor. Raw-sheet conservation is not assumed. On every whole
source triangle, repaired RT divergence is constant and equals the exact
signed source density, so it cancels the vertical lift divergence pointwise.

A read-only audit of the hash-bound current mesh checks that premise rather
than relying on the lift Gram alone. It records all 168 B.Cu source triangle
identities, exact-grid vertices, areas and signed densities; verifies whole
triangle containment and exact complete patch coverage; and checks that the
stored rounded source operands equal those densities times triangle area.
Partial source triangles or different operands fail. No source triangles
occur on the other three foils. Source overlap and cancellation are retained.

`source_lift_region([profile, profile], ...)` gives an identical-profile
two-sided cross interval, whose lower endpoint is a valid diagonal lower.
The energy upper is never used as a lower. The new floor intersects the prior
regional interval using `max(prior_lower, lift_lower)`, not their sum. Existing
barrel lower bounds concern disjoint regions and may be summed afterwards.

## Retained result

The separate receipt is
`.circuit-cache/issue38-recovery/source-lift-mismatch-v2/receipt.json`, SHA-256
`edb25bfe5063dd085a4984e068848e941d20a28cf709f4b7a87fcf5d614ad274`.
It binds the exact profiles, native/source closure, current mesh/source archive,
canonical capture, historical localization, and all relevant construction and
repair code. The original capture and localization-v1 bytes and producers are
unchanged. Their zero foil lowers remain valid but loose historical results.

Both B.Cu profiles have lift-energy interval
`[8.147044247841373e-6, 8.147044247841375e-6] Ω`. Their revised mismatch
intervals are respectively:

- `[8.147044247841373e-6, 1.4450272599820352e-4] Ω` for J900134:2.
- `[8.147044247841373e-6, 1.9017763214062243e-4] Ω` for C107:2.

Both retain TP990031:1 as return. The complete regional lower sums, including
the existing disjoint barrel lowers, are outward lower bounds
`1.794756078036235e-5 Ω` and `1.7946743995760298e-5 Ω`. These remain well below
the separate complete canonical mismatch uppers. Other foil intervals do not
change. The result does not identify all remaining mismatch or justify a new
solve or geometry change.

The audit took 2.59 s, peak RSS 523576 KiB; heavy guard PASS (3 s). No global or
local solver was constructed. An earlier attempt failed before mesh loading
because layer names belong to the profile document's common mapping rather
than each profile row. Its v1 log is retained. The v2 check requires the exact
four-layer mapping and the frozen B.Cu indices; no geometry premise was waived.

## Why the scope is limited

A unit slab supplies a counterexample to extending this floor to all 3D
currents. Let the top-face density be `g(x)=+1` on the left half and `−1` on
the right half, and let `G(x)=∫₀ˣ g`. With unit resistivity and `v=0`, the field
`q=(-G h′, 0, g h)` is divergence-free and has the prescribed top trace and
insulated bottom/sides when `h(0)=0`, `h(1)=1`. Since `∫G²=1/12`, choosing
`h(z)=z²` gives total energy `1/5 + (1/12)(4/3) = 14/45`, less than the linear
lift's vertical energy `1/3`. Thus the floor is tied to the unchanged linear
lift ansatz. A rational regression preserves this limitation explicitly.
