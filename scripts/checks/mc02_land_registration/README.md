# Conditional FH12 recommended-land registration intervals

This is source-only recommended-PCB-land arithmetic in a **reviewer-defined,
counterfactual coordinate frame**. It is not a generated footprint, measured
clearance, actual field registration or physical-body containment proof.

Actual Hirose EDC3-150229-11 SHA-256
`c3257beed2331e5c95e176bc28441b04b804301a44c11b462e486fb5cc649d07`
was visually inspected. Printed sheets1/2 (physical0/1), upper-right recommended
PCB mounting pattern, give signal-pad length1.3±0.1, pad-bottom to tab-near-edge
gap1.5±0.1 and tab length2.2±0.1 mm. Printed sheet5 (physical4) gives G=9.1,
12.1,18.1,25.1 for exact8/14/26/40 SH(55); the pattern marks G±0.1. These are
PCB land dimensions, not the separate stencil drawing or connector A tolerance.

Define the signal-pad-row midpoint as y=0 and positive y toward tabs/body/entry
(down in the depicted pattern). Nominal land Y is[-0.65,4.35]. Independent outer
extrema give[-0.7,4.6]: `[-pad_max/2, pad_max/2+gap_max+tab_max]`. Assuming shared
lateral symmetry only for this comparison, outer tab width is `Gmax`; the signal
pad span conservatively bounded by basicA +2×0.05 +0.33 is smaller. The0.05 per-axis
allowance is an explicitly conservative interpretation of the PCB positional box,
not an exact minimum/manufactured guarantee or borrowed connector tolerance.

A hypothetical field centered at zero has depth6.1 and width`0.5n+5.6`.
For feature[min,max], field dimensionF and additional per-side marginm, permissible
origin translation is `[-F/2+m-min, F/2-m-max]`. Bounds are computed from the
input dimensions, not stored as answers.

| Additional margin | Conditional delta X | Conditional delta Y | Land-only interval |
| --- | --- | --- | --- |
|0|[-0.2,0.2]|[-2.35,-1.55]|Nonempty, counterfactual only|
|0.25|[+0.05,-0.05]|[-2.10,-1.80]|Empty in X|

The positive lower X bound exceeding its upper bound is deliberately retained
as an empty interval. It does not authorize widening the field, changing pads or
reducing the intended margin. Nor does the nonempty zero-margin rectangle provide
a selected placement. Actual and adopted registration remain null; all physical
containment states remain NOT_ESTABLISHED. Dashed connector images, parenthesized
reference0.5 offsets and these PCB land coordinates do not establish the full
physical body/terminal union or its tolerance envelope.

```sh
python3 -B scripts/checks/mc02_land_registration/audit.py
python3 -B scripts/checks/frozen_studies.py discover scripts/checks/mc02_land_registration
pnpm circuit:check
```

Actual source-only execution hashes the authorized ignored PDF and frozen project
inputs, checks61 selected links/four variants, then calculates four interval rows.
No full geometry run, search, native KiCad, CAD edit, adoption, DRC/fill, purchasing
or manufacturing. Missing PDF or changed pins fails closed without acquisition.
