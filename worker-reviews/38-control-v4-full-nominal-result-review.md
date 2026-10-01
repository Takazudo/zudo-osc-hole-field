# P v4 complete nominal matrix — independent bounded artifact review

## Conclusion and limits

No concrete artifact/source/profile binding defect or unsupported acceptance wording found. This closes the bounded retained-result review only. The receipt correctly says NOT ACCEPTED: nominal finite-profile full-native diagnostic only. Physical contact classes, manufacturing/registration/material envelopes and common/private/K allocation remain unaccepted or NOT RUN. No actual source-current/terminal-flux, full physical 3D/primal, joined J/P/K or electrical-target acceptance follows.

No full solver, native run, mesh or field reconstruction was rerun. Checked actual retained files, source/native hashes, contact/profile identities and a small343×343 dense matrix consistency calculation with one BLAS thread. The latter is a floating diagnostic check, not a new outward numerical certificate. Root's guarded563s execution is separate retained evidence; receipt runtime536.577s excludes guard/process overhead.

## Exact bindings and basis

- Result: `.circuit-cache/issue38-recovery/control-feasibility-v4/ground-full-nineteen-v1.json`, SHA `d3c701ba9688011e31d253c167564967e8e496ece63493ea0801b1b924760a52`.
- Exact sidecar path/name and SHA `84e256396be65e616ed2a66dc94cf68f202f60a3328bc33e793872c2c5e426c2` matched.
- Native export SHA `977997bd280e438940f5b39916233e355f2834cb903845524bb50d33e1d693f9`; PCB SHA `781b2e2c9b6d28c103a644281334f4dbb0b07d2455a11ad9e6bf958f301b00b0` matched actual fresh P v4 artifacts.
- All43 model-source and111 native/source prerequisite hashes independently matched, with a final repeat check. Full P include-loads authority is True; unrelated K/J/peripheral/rail prerequisites are None.
- Sidecar/native/model/prerequisite/reference/layer metadata equals the matrix receipt. Exact ordered sidecar profiles equal matrix ports plus one final reference entry.
- Complete344 unique native/source contacts:214 fitted loads,127 GH,3 mains. All native UUIDs, kinds, physical foil memberships and main-component memberships match the current source inventory. Excluding actual reference TP990031:1/B.Cu gives343 balanced functions. No fitted P load or utility GH is omitted.

Every saved patch is valid, nonempty, finite and positive-area, and is covered by that contact's inward native analytic pad envelope. Three main patches each consist of19 disjoint0.24mm squares(total1.0944mm²); main_strands=True. This independently checks finite profile geometry within the pad, not manufactured support or a replacement for full drill/collar/source-continuity proofs. Minimum saved profile area is approximately0.04mm².

All195 barrel ownership UUIDs are unique and their count matches195 actual AGND holes in the native main component. All344 native ground contacts are retained in the mapping; source-free component omission audit is empty. The potential receipt explicitly labels the three maximum-wetting terminal restrictions as H1 trial restrictions, with no physical equipotential claim.

## Numerical receipt consistency

Both matrices are finite343×343 and exactly symmetric as stored. Independently calculated eigenvalues of sym(U−L) have minimum `3.229086209026091e-5` ohm and maximum `0.013558413096056786` ohm, satisfying the existing−1e−9 ohm diagnostic check. This checks internal bracket consistency, not mesh convergence or actual electrical targets.

| Mode | Maximum equation residual(A) | Maximum residual-work allowance(ohm) | Nodes | Triangles |
|---|---:|---:|---:|---:|
| Current | 5.906901731313595e-10 | 7.690057556796692e-7 | 282497 | 421225 |
| Potential | 2.2203694072404067e-9 | 9.473168966451175e-7 | 282982 | 422232 |

Both residuals are below the unchanged1e−8A gate. Both have43 batches and zero refinement corrections. Reported current physical-gate maxima: operator5.906901731305125e−10A; shared-face continuity5.906901731313595e−10A; sheet source balance5.551115123125783e−17A; barrel balance2.0435042547006788e−15A. These are read from the hash-bound producer receipt, not independently recomputed fields.

Parameters are adaptive coarse2mm/fine0.25mm, refinement1, origin[0,0], four physical/active foils and nominal material assumptions. No refinement/convergence, manufacturing, real terminal-current density or common-path allocation conclusion is implied by process PASS or the PSD-gap check.

## Principal model source hashes

- solve_conductor_volume.py: `3b8c536bfb2b92b3bef8959845b51543cfd3c5b4d3b9fedb73ca3ac1f58ed1de`
- control_model_entry.py: `d262936612c9d5ea5ba8226514800504b1c092c24808dbdf0323b40bd6f393d5`
- ground_volume_geometry.py: `94ff1bc7f7f315566cb401e016ba867cc61624a7891390cb9f09ea3385573b84`
- sheet_volume.py: `b9dd9579d0d79b34beaf867725f0076ab13a9a5b36498077a147272e9f8cc035`
- current_trial_matrix.py: `f5e1d92543b53bdaf181a6463de5ac1a95e2057ea3d0d01c47baf25f7afd3fd5`
- potential_trial_matrix.py: `0fcdaceada6df26f73a2dd60cda1236cec1fdb5bfcadd437d9b144bde06871e2`

No shared code or retained result files were edited. Review notes only; circuit:check PASS49 before writing.
