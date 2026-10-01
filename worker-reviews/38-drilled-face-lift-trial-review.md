# Issue 38 drilled face lift trial: independent review

Scope: read-only review of `drilled_face_lift_trial.py`, its focused test, and the trial work note. I made no source or board changes. `python3 -m unittest scripts.pcbgen.test_drilled_face_lift_trial -v` passed all three tests using the local historical fixture.

## Result

No blocker to retaining this as a **conditional symbolic trial**. It does not admit a current native board, physical source class, material, or downstream model.

- With local depth pointing from an internal cut toward the exterior face, `J_z=-I b-z(q-Ib)/h` gives cut outward flux `+I b` and exterior outward flux `-q`. The global axial sign reverses for B.Cu while local outward traces remain the same. `div J_xy=(q-Ib)/h` cancels `partial_z J_z`; the `I=0` case retains nonzero signed redistribution.
- The energy expression has units W: `rho` is ohm mm, each term inside the square is A/sqrt(mm), and the full-field triangle bound includes the mean/correction cross term. The `C/h+h/3` factor follows from the planar Poincare estimate and the exact integral of `(z/h)^2` over depth.
- The historical U8304:6 fixture has two complete annuli, convex cover leaves, exact positive overlap squares, and a conservative whole-domain area bound. The test recomputes a conditional constant only. Its `exact_partition_masses=[0,...]` is a balanced formal source, not a proof that any physical source partitions have those masses. Likewise the function accepts externally supplied `C`, source norm, slab, patch, and resistivity; no code path verifies them against current native geometry.

## Minor correction

`sqrt_upper` line 28 says it has a *strict* `10^-12` grid margin, but line 32 returns the exact root when the radicand is a perfect square (for example `sqrt_upper(1)==1`). The returned value is still a valid non-strict outward upper bound. Change the docstring to say "rounded upward to a 10^-12 grid" or always add one grid unit if strictness is required. This does not affect the conditional bound.

Keep the work note's explicit `NOT RUN` physical/current-native/model status. Before any future admission, bind the actual integral `I=int q`, source partition masses, full support of `f=q-Ib`, connected Lipschitz cover and local constants, positive same-face foil slab, patch, and pointwise downstream cut cancellation to a frozen native/source epoch.
