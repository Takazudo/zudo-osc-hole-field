# Jack and indicator evidence bookkeeping

Issue #91 corrects two source declarations identified during the individual #11
acceptance audit. All fixed hardware coordinates, CAD and circuit values stay
unchanged. The original small jack-pitch fixture passed on published410dfa9:
four jacks at17 ×14 mm, zero DRC violations/unconnected items, SVG generated,
unchanged inputs. This is fixture evidence, not installed fit or full-board proof.

The optical-window declaration now distinguishes92 magnitude indicators at
[6.15,0] mm and10 clip indicators at[6.15,2.05] mm relative to parent jack centres.
A checker derives actual Decimal coordinate differences from the locked grid and
compares both lock offset metadata and per-type declarations/counts. It rejects
the previous single-offset form, wrong clip displacement and incorrect counts.
The geometry regeneration entry runs this check; it never moves a coordinate.

The jack owner explicitly retains the unavailable exact manufacturer mechanical
drawing with the required zero-hash sentinel. An unknown-URL text sentinel is
metadata only and is absent from linkable sources/document selections. The
existing Thonk family drawing remains distributor evidence; no manufacturer
identity, terminal dimension or fit is promoted. The new missing-evidence fact
is UNSOURCED and mechanical coverage stays OPEN alongside its physical coupon.

Three focused tests pass in the prepared isolated copy, and independent review
found no blockers. Component publication and aggregate/docs checks must pass
before merge. #61's compact LED supersession and #64's optical/thermal physical
qualification remain separate. #11 closes only after its original scoped
acceptance and these bookkeeping corrections are published.

Guarded baseline and post-change aggregate, documentation checks, build and
strict site checks pass (exit0,401 seconds; one existing template-link exception
remains allowlisted). The merged capacitor evidence was then incorporated. Its
new source and this missing-drawing record are both counted, for132 total owner
sources. The generated preflight conflict was regenerated from source. The jack
inventory source-state summary now agrees with the explicitly unavailable primary
drawing; available distributor evidence is retained. Fresh native monitor ERC
and pin parity pass after that inventory hash change, and its report changes only
the input binding. Geometry tests, component validation and generated-output checks
pass on the combined source. Exact-head CI remains required before merge.
