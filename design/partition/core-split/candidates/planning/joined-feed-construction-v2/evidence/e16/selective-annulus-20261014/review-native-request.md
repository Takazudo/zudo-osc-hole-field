# Independent exact native request review

Reviewer: independent DRC workstream agent, separate from request preparer. Date: 2026-10-14. Disposition: exact prepared request bindings PASS; execution remains NOT ADMITTED / NOT RUN. This document is review evidence, not an operator approval or global native reservation.

## Exact identity

- Frozen execution checkout: `/home/takazudo/repos/circuits/zudo-osc-hole-field/worktrees/e16-annulus-fixture-ad8f3b1a`.
- HEAD: `b27391dea630ef60a5613608bcbb6b25458a0d8d`. Independently inspected `git status --porcelain --untracked-files=no`: empty; `git rev-parse HEAD` matched.
- Request: `.circuit-cache/annulus-fixture-ad8f3b1a/request.json`.
- SHA-256: `f8da55c709fa59ba3221806f1c10cc4d25462fe8bf9d8c50acf313b0d3fdf4e3`.
- Run: `ad8f3b1a33ef4b5eaf638b183708ef64`, attempt `1`.
- Worker: `local-ad8f3b1a33ef4b5eaf638b183708ef64-1-annulus`.
- Operation: kind `annulus-fixture`, target `annulus`, stage null, 60 seconds, preconfigured-noninteractive authentication.

## Independently checked bindings

Used the frozen checkout's read-only `validate_request` with Python bytecode writing disabled, plus independent request hashing and filesystem checks. All eight required input hashes and the installed heavy-guard hash match. The fixed fixture, fixture worker and local admission module hashes also match the earlier independent source review in `review-native-fixture.md`. The topic's retained `native-request.json` is byte-identical to the frozen request.

The exact command is:

```sh
python3 design/partition/core-split/candidates/planning/joined-feed-construction-v2/fixtures/selective-annulus/native_roundtrip_characterization.py worker --output .circuit-cache/annulus-fixture-ad8f3b1a/guard.json.annulus
```

This is the guarded host-worker payload, not a standalone execution instruction. The outer existing local admission and resource guard must supply approved authority and actual containment; direct invocation cannot establish those prerequisites.

The request binds the existing worker/aggregate caps of 6,442,450,944 / 12,884,901,888 bytes, zero swap, an 8,589,934,592-byte launch-available-memory floor and one global native slot. No limits or global host settings are changed. The heavy guard is `/home/takazudo/.codex/scripts/heavy-guard.sh`, SHA-256 `074a463dd6b3a65b7e2168df95b200c0192c414862375bcfb95f979c34c67ee7`, with an empty override environment.

At review time, the bound request directory contained only `request.json`. No `guard.json*` artifacts, output directory or approval-named files existed there. The exact persistent worker claim/result glob under `/home/takazudo/.local/state/epic242-native-admission` was empty. No local or CI authority variables were present in the review environment. No request, claim, output or run identity was consumed by this review.

## Authority and scope boundary

The existing local contract requires separate operator attestation after independent review, an actual global reservation and applicable native qualification. Preparation supplied none of those. No approval of this fresh exact digest was found, no global slot was reserved by this reviewer, and no native launch was performed. The old baseline campaign authority does not admit this fixture; the absence of an approval artifact is preserved rather than filled with a fabricated operator identity.

If separately admitted, this tiny fixture can characterize the pinned parser/API and round-trip behavior of a still-flashed custom In3 diameter while checking preserved native identities/geometry. It cannot demonstrate exact selective-annulus removal, produce a KA repair, establish complete DRC, rerun finite coverage or numerics, authorize production geometry, adopt copper or qualify hardware. A successful run would remain negative-control characterization; unsupported pinned APIs must fail explicitly. Native runtime behavior is currently NOT RUN.

Only this review note was written. The frozen checkout, request, approvals, claims and outputs were not modified. Native/numerical campaign consumption is unchanged.
