# Pilot current-report regeneration

The original issue #22 pilot capture is retained from merge
`f908ae2e4ad3dc40e21f7249b64fb5cdf9a8f109`. Its standalone current producer was
missing from canonical schematic regeneration. The committed worksheet therefore
still counted three old `0603Whitelight_C2290` symbols per instance after the
captured family changed to `Kingbright_White_0402`. The standalone `--check`
correctly failed, but the previous pilot tests only built the report in memory.

Canonical `scripts/schgen/regen.sh` now refreshes the pilot worksheet immediately
after schematic generation. A committed-report regression enforces equality
with the current family, and a mutation restores the obsolete LED symbol to
prove that the report check rejects it. The package-population label is the only
worksheet data change; all per-instance current values and unqualified/null
maximum fields remain unchanged.

The authored pilot page now identifies the 72.655 mA negative-rail deficit as a
historical preliminary count-model result. Current planning allocation and
external-source requirements are recorded in the power reports. No source,
inlet or current maximum is qualified by this correction.

The ERC text now distinguishes the complete 228-warning master baseline from
the H1/H2 subset of six LED pin-type warnings per instance. The checker and
warning baseline are unchanged. The clean-entry guarded aggregate and fresh
pinned master smoke passed in 261 seconds: zero errors, all expected warning
identities, full exported pin/net parity, separate H1/H2 held nets and rejection
of the deliberate hold-node mutation in both instances. No entry regeneration
drift was found.

The nine focused pilot tests and component evidence check pass after the
correction. Changed-source guarded aggregate regeneration, fresh native checks,
documentation checks, build and strict site checks passed in 457 seconds; the
one existing workbench link exception remains allowlisted. These are software
consistency checks, not hardware qualification. Exact final-head CI remains
required after integration of newer main changes.

Original issue #22 deliverable 6, complete typical/maximum current per rail, remains
unestablished in the pilot and global reports. Acquisition, hold drift, leakage,
noise, real output stability, placement/fit and physical source qualification
remain open. The existing 0.5 µF lag, three-point ideal-model results and explicit
absence of a 25-second slew claim are unchanged. No component, circuit value,
net, panel position or acceptance limit changes in this topic.
