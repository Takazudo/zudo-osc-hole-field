# MC02 conditional 51 mm length sensitivity

One bounded source-only experiment: hold the retained engineering model at
`2c53715d49a4a7639723595590d1fd4eeb3a3c1f`, then change only
`cable_length_mm` from 50 to 51 on exactly the 28 C29534 links. Geometry, cable
labels, conductor order, grounds, unused contacts, material, end-equivalent,
impedance and drive terms remain identical. This does not qualify Molex or any
replacement cable; its actual properties have not entered the model.

`manifest.json` freezes the complete consumed source closure: link record and
retained ratios, electrical inputs, partition/loom used by the harness reference,
power-post joint design used by mixed ground shares, and numerical/helper source
files. Pins are checked before imports and after calculation. All changed records
are private deep copies; no canonical file is written or module function replaced.

Before the variation, the existing adapter-aware `harness_baseline.baseline`
rebuilds the reference using `ds62_table.adapter_rules`. Existing
`link_ratios.link_pairs` evaluates every directed pair for all 61 original links.
The six-significant-digit retained rounding must reproduce every link's pair
maximum, complete witness pair, evaluated count and missing-reference list, plus
all mixed-branch ground-share fields in every post case. All five intentional
STATIC/WIPER null IDs must agree. Any mismatch stops before variation.

The variation calls the same pair kernel for the 28 affected links; 33 unchanged
pair results are reused exactly. Ground shares are recomputed across all 61 links
using `ground_share`/`worst_contact_mixed_at`, because a changed path also changes
the alternative conductance seen by other contacts. This is not global ratio
scaling. `link_row` is deliberately not invoked: it can launch a separate
DS-77 conductor-order remedy when a ratio exceeds one, outside this task's scope.

The JSON result preserves full before/after pair maxima, witness pairs, counts,
all mixed ground-current cases, explicit 28 overrides, null identities and exact
pins. It reports any ratio above one without invoking another search.

## Lightweight fixtures

```sh
python3 -B scripts/checks/frozen_studies.py discover scripts/checks/mc02_length_sensitivity
pnpm circuit:check
```

Fixtures include source-pin rejection, exact override set and record preservation,
baseline mismatch stopping before variation, all-61 mixed input recomputation,
and a two-contact synthetic case using the actual retained mixed-ground functions.
No full numerical study has been run during implementation.

## Actual execution requires coordinator admission

Verify the same machine-wide shared lock, effective 1 CPU / 1 GiB / zero swap /
128 PIDs and total 600 seconds (setup60, analysis480, cleanup60) before execution.
Hold exclusion through process-tree termination and cleanup. One attempt; no
automatic retries. This script itself is not a resource launcher.

```sh
/tmp/osc-numerical-venv-20261117/bin/python -B \
  scripts/checks/mc02_length_sensitivity/study.py \
  --output "$PWD/.circuit-cache/mc02-length-sensitivity/result.json"
```

Output must be a fresh file in this worktree's ignored cache and is exclusively
reserved before analysis. Baseline failure is recorded, not treated as a result.
No native KiCad, routing, placement, DRC, fill, inventory, adoption or manufacturing
work is performed. Pre-edit circuit check passed: 84 manual inventory lines,
445 declared placements unverified; pin-asset check performed. Aggregate/native
regeneration is held and unnecessary for this isolated study.
