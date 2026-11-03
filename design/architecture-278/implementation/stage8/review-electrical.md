# Independent electrical source review — Stage8

Reviewed root-authored Stage8 rebudget/assessment and the independently authored critical-locality interface. This reviewer authored the current model and does **not** claim independent review of `stage8_currents.py` or its analytical report.

The rebudget helper preserves source-package and locked-panel conservation through the existing independently reviewed Stage7 pure interfaces/electrical APIs, checks source hashes, and binds the exact serialized interface object to electrical results. Actual interface pad changes therefore cannot silently reuse the former electrical object. OSC225paths/240returns remain the retained Stage6 baseline. Critical copper/barrel lengths are additional source evidence; other allocations remain unrouted.

The assessment now independently reconstructs source-footprint pad obstacles and all reported trace/via reservations. This closes the earlier omission gap identified during review. It checks complete ten-connection inventory, actual source nets/pads/layers, full final different-net copper obstacles, substrate cuts, mounts, headers/courtyards, via positions and geometry, and independently recomputes copper, via and terminal through-hole barrel lengths. Thirteen focused assessment tests and three rebudget binding tests PASS in this review, including omitted pad/reservation, detached endpoint, altered length and stale-interface mutations.

The tenth connection joins C3308:2 to C3309:2 on AGND. Together with both U3305 supply-to-capacitor connections this explicitly represents the local bypass loop topology that was missing from the nine-edge inventory. It does not establish loop inductance/impedance, ESR/ESL or remote supply behavior. C3301 is a drive-to-feedback path; no fictitious AGND leg is introduced. The long jack-tip feedback branch remains physically accounted for, without stability acceptance.

No remaining source-level electrical defect was found in these reviewed helper bytes. Conservative geometric corridors are not native copper, native DRC or full routing, and neither their existence nor the DC current calculations qualify assembled feedback stability, noise, ground gradients, load drive or hot-plug/fault behavior. Actual return-current division through the four AGND conductors and the upstream source remains unknown. No parallel-sharing or cancellation credit is authorized. Native, simulation, physical and hardware acceptance: NOT RUN / OPEN.

## Reviewed source bindings

- `scripts/architecture278/implementation/stage8_rebudget.py`: `745e1c9c02c5851a23db438a8d1571ea7bd0735053599effbee56de7fcd1b989`
- `scripts/architecture278/implementation/test_stage8_rebudget.py`: `24f4d2c7c4451f40751291dc46a7b7330c90d68e1d4f8a91b69c58f6fe03c2d8`
- `scripts/architecture278/implementation/stage8_assessment.py`: `3100b95cb0d459a58ff412259c82a116bda4a48738f389ffbc53b526c628dbe9`
- `scripts/architecture278/implementation/test_stage8_assessment.py`: `c5c3080e7d54b8d9d51df1d278f838927541d0d1a4441ba9f11cd227468f8ddf`
- `scripts/architecture278/implementation/stage8_locality.py`: `e52e3e04759b86a3a4486422864ea6ac7672a9f661bb80ce75a3d990efe70995`
- `scripts/architecture278/implementation/test_stage8_locality.py`: `0d3e052407b5dfddf2354cd7251802692770790473e8ec2124afecb8d01d038e`

## Reviewed report bindings

All source-hash maps were checked against current bytes; the electrical/interface object hash matched. The independent geometry checker reports10of10 compatible conditional corridors, including the24.1mm capAGNDtie.

- `design/architecture-278/implementation/stage8/mechanical-report.json`: `613a29089a103ffb878933dd1a818e6c69bd074d1652d01da62cb70d64d78dab`
- `design/architecture-278/implementation/stage8/locality-report.json`: `2c560c670e7724fba3d1d0042704d793b4e6a1f630f6b81afb1b716ddb5151af`
- `design/architecture-278/implementation/stage8/interfaces-report.json`: `b2c1c6729e85fc58471a0ea9533fba8b1a23e98a87b4dc32303b05a0e83e3224`
- `design/architecture-278/implementation/stage8/electrical-report.json`: `cb689ec02064b59887fa5edb84602b923436df9010fb5c27ecaf27425243c943`
