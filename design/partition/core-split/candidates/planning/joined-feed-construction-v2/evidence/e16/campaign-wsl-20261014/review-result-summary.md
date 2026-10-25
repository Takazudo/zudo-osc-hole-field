# Independent result-summary review

Reviewer `/root/review_checkpoint`, 2026-10-14. Cache-only source/fixture/retained-snapshot review, no production numerical/native execution or frozen-checkout edits.

Initial source: summarize.py SHA-256 a70a9b7c0149b1c1f78adddff07d6412d15d4bcc6bf3590000e42fe182e88a4a; engineering_report.py SHA-256 23be2649626b9422478ead96509e361bec66f569c17472d3c67685f9bd7995db.

**Initial disposition: corrections required before final completeness/reporting use.** Findings sent directly to coordinator and assigned author; independent recheck pending.

1. Phase totals do not establish exact unit identity coverage. A tiny fixture with two copies of the same KA reduction and two copies of the same KA driving chunk, no KB counterparts, one coupled result and matching phase totals is labeled numerical_full_baseline_complete=true. This reproduces without production inputs. Require unique complete phase/board/net/case/depth identities and exact chunk ranges; duplicate identity replacing a missing expected unit must refuse completeness even when totals match.
2. Step inputs are ignored; coupled data validates only config/service binding, not reduction/driving predecessor identities/hashes. Adding inputs={unbound-input.json:64zeroes} to a fixture receipt leaves integrity_errors empty. Bind each input to exact request or verified predecessor output and bind same-case/board reduction/driving dependencies; do not interpret results with incorrect chain provenance.
3. Engineering renderer states seven finite AGND states are evaluated for each of three cases even in partial snapshots. Change this to the required matrix and report actual completed/missing states. Partial render must not imply all30finite states were evaluated.

Independent existing tiny test run:12PASS in0.045s, log result-summary/independent-review-tests.txt. The tests currently do not cover the first two defects. Retained125-unit snapshot correctly says incomplete,11/12coupled combinations and23/30finite states, no terminal receipt/fullPASS; this positive behavior must remain after correction. AGND table budget is0.0005ohm and rail1mOhm, directly bound from configuration. Loaded-subset and all-pad counts are separate; no summing alternate cases into distinct physical identities. Electricalacceptance remainsfalse, whole-device omissions and source-relative versus fullpath/localground limits are explicit.

No current baseline execution finding is implied: these are reporting-tool robustness/provenance defects. Actual run controls and solver are untouched. Wait for the independent corrected-source recheck below before relying on final completeness flag.

## Independent corrected-source recheck

**PASS for read-only result summarization; initial blocking findings are resolved.** This is not yet a terminal baseline PASS or independent process-cleanup certificate. No production calculation or frozen-checkout edit was performed.

Reviewed corrected hashes:
- summarize.py:32299453dc27ab3e4cd93cce42ed4f80b026afcae850440bf1f13eb06ca7bb18
- provenance.py:332650fabafc4e8a214847856e03d96544d1eeb88014e9a82e858a88afc59ce3
- engineering_report.py:9abd855ee05ae550d20278ad0eaa0bc82b86665c4dc795f3af1f7f979afbae3c
- test_summarize.py:9d81cb6215969db1d079ac7a17dcd9b009a118d6223d6345e25ea8788abb41dd

Pure provenance audit now checks unique phase/board/net/case/depth and driving start/stop identity coverage, duplicate output producers, request-or-successful-predecessor input digests and actual bytes, declared command-file inputs, exact same-case/board reduction and complete DP predecessor sets. Coupled output reduction/operator/method/scope bindings must agree. Missing identities block completeness; unexpected/duplicate identities cause integrity errors and refuse coupled interpretation. Matching phase totals alone no longer suffice. Terminal completeness additionally requires exact command identity and all four explicit true hook integrity fields (request, approval, HEAD, clean checkout), successful processes/guards/checks, complete state matrix and no unreadable/integrity errors. The same148ceiling and required12combinations/30states arise from the unchanged bound baseline scope; no outstanding state is inferred.

Independently ran18tiny tests PASS in0.126s, log result-summary/independent-review-tests-corrected.txt. New tests prove an exact tiny matrix can complete, but duplicateKA replacingKB, wrongchunkrange, unboundinput, changedcoupledpredecessordigest, absentDPcommandpredecessor and incomplete terminalobject all refuse. Existing original12fixture behavior remains covered. No production inputs were loaded by these tests; opaque output files are only hashed, never unpickled.

Re-rendered retained125-unit snapshot in memory: remains INCOMPLETE with11/12combinations,23/30finite states and numerical_full_baseline_complete=false. Renderer now describes sevenAGND states percase as REQUIRED and points to actual matrix coverage rather than claiming all completed. Read corrected132-unit snapshot: zerointegrityerrors,16missing exact identities, fullcompletefalse. It demonstrates chain checks work on this realpartialresult inventory without converting active work into terminalsuccess.

Electricalbudget handling remains correct:1mΩrail and0.5mΩAGND from boundconfig; all-evaluated and included-loaded pad populations separated pernet/case/state. Source-relative potential, conditionalwholedevicesubset, unsupportedpackages/GH/fullpath/physical limits remainexplicit; electricalacceptancefalse. Aggregate class energy doesnot falsely identifya particularvia bottleneck. PreparedU2314followup remainsoutsidecurrentnative/variantauthority. Final report must retain actualexecutionSHA and separate laterpublicationSHA.

Minor nonblocking report-location note senttoauthor: the literal ../next-intervention manifest reference doesnot resolve from currentcache snapshot subdirectory; use an explicit actualcache path or correct finalretention-relative location. Numerical/provenance approval is independent ofthat prose path.

The helper remains a reporting tool, not replacement admission or terminal containment audit. Coordinator/independentreviewer must still verify final request/approval/claim/source/protectedfiles and owned-process cleanup before declaring campaigncomplete.
