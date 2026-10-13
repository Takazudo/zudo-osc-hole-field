# Diagnostic6 independent terminal evidence review

Reviewer `/root/review_admission`, separate agent from the executing coordinator. This reviewer authored the profiling wrapper; another agent reviewed its source/exact packet before admission. This report independently checks actual execution evidence and cleanup, not an independent approval of the reviewer's own source. No production/native workload was executed by reviewer; only hashes, JSON/rawpstats and OS queries were read.

**Numerical/profile completion and terminal integrity/cleanup PASS.** Exact request `b814dc00c6655cf09c57e0d8689dedeece5689f9e180fc41df1397ff71d0bc69`, run `bd4c89d22aa04b5fa1a7cb74d9358b77`, attempt1, unchanged clean HEAD `9a68f1a87db7afbc20ae16a95ef523a5f8d093ca`. Exactly one profiled actualproduction KBAGND nominal-average/uniform-dielectric dpoint0:16 unit. Numerical assessment1.6095160533084053e-13 PASS versus unchanged1e-9; electricalacceptancefalse. This is16pads only, not a successful96-pad unit or fullbaseline.

All342 sealedinput/method/hook/helper bindings and539 protectedcandidatefiles match. Request/approval/log/observations/stepstreams/result/numericalverdict/rawprofile hashes verify; persistentclaimresult equals packetreceipt. All hook terminalintegrity assertions true. Actual production solver hash `dfd3578cd6c7ca822e15766ea019aeecf43967c4d6393bf5ad145e32633506f6`, output hash `f4778cd99cf61ce0c7767f69cf02d03f1819c11e079de2f8c94a08a93379e1ed`. No arithmetic/source change occurred during profiling.

Hook exit0 elapsed41.06650995207019s; Ledger40.281s, profilewrapper40.04075627203565s; guardPASS exit0 secs42 minimum available7857MiB. Reported childRSS1589068KiB. Independent exactwrapper observer40actualprocess samples confirmed2147483648-byte memory.max andzero memory.swap.max withzero sampled memoryevents. Observed/selfreportedcgrouppeak1597878272bytes. Scope run-rcd92de51a8ba4af49d849eeff3760eb9.scope inactive/cgrouppathabsent. No profiledwrapper/driver/hook/observer or guardowner/heldlock survives. Finalobserverterminalsampleempty andloggerstopped. Observerhash `ad20e864e134ab73b6050af33e5e1ed60cab49919342a242e9ea294eac7750cb`. Hook finite_solve-only observations are correctly empty; wrapper-specific observations supply independentscopeevidence.

## Actual timing finding

Rawpstats SHA-256 `99a3ba0ae9e43ce4ce4f67c651e2937bac907eebf1ead81bb54164c0ad9d9d6a` was read with stdlibpstats. It corroborates the retained JSON function timings:

| Function | Calls | Inclusive seconds | Self seconds |
| --- | ---: | ---: | ---: |
| refined_projection |1|34.396364|0.710685|
| _refined_accumulator |2|33.449541|1.293174|
| _extended_residual |8|26.569040|4.913152|
| ndarray.searchsorted |9792|16.965766|16.965766|
| factor_board |1|5.328198|0.000197|
| SuperLU.solve |8|4.760410|4.760410|
| SuperLU factorization |1|4.053073|4.053073|
| ufunc.at |9792|2.890817|2.890817|

Rawprofile totalself time is40.025319s. Searchsorted alone accounts for about42.4% of that measured unit; extendedresidual inclusive time about66.4%. Inclusive rows overlap and are NOT summed. The repeated sparseentry-to-major-index search in extendedresidual is therefore an observed optimization target, not merely a guess that LU/factorization dominates. Profiling adds overhead, and16-pad measurements do not guarantee96-pad speed or eliminate resource validation.

Sourcefreeze may end after this verified terminalcleanup. A bounded source optimization preserving sparsecontributions/accumulation order, numericalcriteria, resourcecaps and148-unit baselineceiling is justified; new source requires tests, separateindependentreview and fresh exactrequest before any actualproductionverification. The consumed96-pad AGND timeout remains originalnegativeevidence. Campaign used1/3fullbaseline and6/24diagnosticunits; no implicit budget increase or unchangedfullbaseline retry is authorized by this report.
