# JL U8202 exact −12V restoration screen — stopped

Read-only searches against the immutable failed native candidate from run38041226566,artifact11666153064,ZIP4c09d2684114b9ca8bb39694406ccbf1bfc55d03b6570142e4b49892029d3f3f. Native candidate4b85b31bdd8fc059f95ab8df1674e761a140cca8b9ecfdc52eabf3294ee7b391; dumped geometry032346a47796ab47c2e684ab065a84d69aee02d8d1e1847ab589504f55b240ab. Extract merge-rejected-1/dump.json to /tmp/issue189-jl-u8202-rejected-dump.json. This exact candidate retains the original186joint additions and3reviewed cuts, but splits −12V270pads into264+6.

Target six pads: C8122.1,C2322.1,U8106.4,C8124.1,U2304.4,U8105.4. Native groups include copper-object IDs as well as pads:1002/17total members,264/6pads. An initial pad-count assertion mistakenly counted all native members; corrected before any search or copper mutation.

Bounds216.5,139.68,245.705,163.3mm;0.025mm raster,0.25mmclearance,0.3mmrail,0.6mmvias; fill guards and every native input object retained. Outer-only search exhausted270370states below300000. Four-layer300000budget hit expansion_limit; a justified same-input1000000comparison exhausted568598states, still0paths. GuardPASS9s/5s respectively. No larger-budget repeat: two comparable four-layer attempts gave no gain and the final search exhausted its bounded state space.

Native restoration/acceptance NOT RUN, no new copper/proposal adopted. Preserve negative evidence. Next intervention must change a diagnosed cause/method (coordinated local geometry, permitted local placement, or human-guided bounded comparison), not just raise the budget or claim the board physically unroutable. User requested throughput assessment before further long experiments.
