# JR130 RB4615 bounded via-branch pilot

This draft depends on PR224/JR130 and cannot be integrated before that exact pending CI approval and acceptance. Main remains JR131. This worker only tests disposable copper and cannot promote a board.

Plan: derive true native cut components after removing one signal via and its two exact attached segments; restore AGND and every victim component; independently verify original connectivity, DRC/parity, warnings, fresh copy, all uncut copper and fixed nonrouting geometry. Full complete-warning audits remain required for any later adoption.

Source board e06b7471ddc8f5c8c498c5eb5bf8655cc6de539e92826a5701cf1de06356e136 and saved native dump9b9af0516701b72623187b1a6539c33cdbe7e53d0ff1a385ba00b47f699dcee8. Input artifact11662823283,ZIP dbbac06e0e996cdeb3ae93695ea94b0964a11b70328680c2f09b41bc5a8bbc27 (JR130 full native run38032373766).

Read-only controls:40 bounded ground-only cases yielded18 paths (guardPASS211s). All18 tested for signal endpoint restoration;3 provisional joint candidates, smallest RB4615.2/27objects including2vias (guardPASS64s). The two retained boundaries are F.Cu(410.3,134.9)mm and In2.Cu(410.65,135.05)mm on X1755C1725708CB94F3AB, inside12.69x13.61mm. These raster positives do not establish native topology or acceptance. No placement/rule/panel changes. Scripts retain exact original paths for this environment; replace input path when replaying elsewhere while preserving hash assertions.

Dispatch existing routing-benchmark.yml on this branch with board=osc-jack-right,local_repair=true,local_mode=cut. Keep issue189 OPEN. Never dispatch a competing JR native worker or use this descendant to bypass PR224 approval. Aggregate native regeneration remains deferred to exact-head CI because the pinned KiCad image cannot unpack locally within the32GB environment; no fallback oracle is permitted.
