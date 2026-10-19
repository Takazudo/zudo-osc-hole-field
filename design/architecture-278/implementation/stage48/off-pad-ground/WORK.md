# Stage48 work record

Authorized bounded goal: remove Stage47 via-in-SMT-pad dependency using disposable
local retained-signal routing, preserving history and canonical outputs. Reconcile
Stage47 exact-head CI first; done. Executor was available. No competing head/work
was found; PR287 remained draft at ce732b7143f5e68d32bd6d967b83f088009d9edf.

Two native trials were run serially under the shared heavy guard. First result
and all failures are retained; no threshold was weakened. Neither trial accepted.
The next F-tail cleanup scope is described and drawn, not implemented. No further
candidate was run after discovering that boundary. Exploratory unexecuted drafts
were discarded, not presented as tested proposals.

Checks completed:

- `pnpm circuit:check` before edits and `pnpm circuit:check && pnpm check` after:
  PASS. Manual inventory68lines/0declared placements, no schematic/placement binding;
  pin-asset check performed. Generated output/model/previews current; doc tsc passes.
- `python3 design/architecture-278/implementation/stage45/connectivity-inventory/verify_bindings.py`
  and optimized `python3 -O ...`: PASS, seven historical checkpoints and four
  Stage41–44 review manifests. Stage45/46/47 manifests additionally verified by
  SHA256 against all30/37/34 bound files. Historical stages untouched.
- Initial normal/-O Stage48 unit runs: nine portable controls passed, local replay
  failed because a nested UUID tuple differed from its JSON list representation.
  Corrected explicit nested-list serialization; no native evidence changed and
  no acceptance threshold relaxed. Added retained-report/execution/proposal SHA
  controls at independent review request. Final results are retained in evidence/.
- Final focused commands use existing `/workspace/shared/osc-ci-python/bin/python`:
  `-m unittest scripts.checks.test_offpad_ground_trials -v` and
  `-O -m unittest scripts.checks.test_offpad_ground_trials -v`.
  Eleven tests pass in each mode, no local skips. Nine original portable controls,
  one new evidence-hash control and one full local replay. CI explicitly skips
  that local replay if ignored full native artifacts are absent; it does not
  reproduce native builds. Existing Stage47 evidence remains separately tested.
- `visualize.py` generated scope.svg from retained Stage46 geometry; rendered with
  installed Chromium and visually inspected. Diagram shows proposal only.
- Staged whitespace check and review bindings are verified before commit.

No full aggregate/history replay or canonical regeneration was duplicated locally;
exact-head CI supplies those repository-wide checks. CI outcome is reported on the
issue/PR after push, tied to the exact SHA. No native fresh-pair acceptance was
attempted for either rejected design, and the expanded proposal has NOT RUN.
