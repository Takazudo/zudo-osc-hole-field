# Independent WSL evidence review

Reviewer: separate read-only agent `review_wsl_admission`, 2026-10-13. Scope: current guard/admission code, retained WSL packet, runner observations, materialization/census receipts and result language. The reviewer ran no native command or production solve and supplied no approval.

Verified descriptor/request digests, oracle method/model hashes, fresh versus retained census identities and fields, the 15-file repeat receipt, live user-scope settings, privilege failure and the 28 targeted source-test results. Source packet correctly binds f1650bba and must regenerate at the final evidence HEAD. No implementation or guard changes were needed.

Two review findings were corrected before commit:

1. The oracle request referenced a nonexistent evidence parent, while the existing guard does not create parents. The owner prepared the fresh ignored `.circuit-cache/e16-oracle-wsl-final` directory and retained the exclusive mkdir prerequisite in the request/README; `guard.json` remains absent.
2. README inherited the historical 539 protected-file count. This WSL checkout has 550 protected files; the count now matches `preservation.json`, with no changed hashes.

The evidence index is generated after packaging. Native/production acceptance remains NOT RUN / NOT ADMITTED. Final corrected-file recheck: PASS, both findings corrected, all 67 indexed files hash-match with no omissions, and no remaining publication blocker. The raw descriptor log was subsequently gzip-retained without changing its decompressed bytes to preserve whitespace while satisfying git diff checks; the owner rechecked the final index.
