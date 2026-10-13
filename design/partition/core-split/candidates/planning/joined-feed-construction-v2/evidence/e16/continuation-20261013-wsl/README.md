# WSL runner and fresh request preparation — 2026-10-13

Implementation source remains `e215b9eb3f9695d74cd9dfc9de182e0882bebcd7`. This preparation ran at `f1650bba3f224585e654930fbf4c521c3b9f61ed` after fast-forwarding the clean existing `worktrees/e16-r4` integration worktree from `dd3ef71`. No completed implementation was repeated or changed. The root main checkout and other worktrees remain untouched. PR #260 stays draft and unmerged; KEEP_K1402_INCUMBENT.

## Runner observations

`runner.json` retains exact read-only commands, versions, exit codes, paths and storage measurements. This is Ubuntu 24.04.4 LTS, x86_64, WSL2 kernel 6.18.33.2, systemd 255 and local Docker 29.3.0 with overlayfs and systemd/cgroup v2. The pinned Linux/amd64 image is already present. About 409.7 billion bytes and 46.3 million inodes were free on the checkout, Docker and containerd filesystems; these paths share the same underlying filesystem and are not additive reserves. No image pull, pruning or container start occurred. Image metadata/available storage do not establish measured native peak usage or runtime KiCad/ngspice versions.

The user manager is reachable but reports degraded because of one pre-existing failed allocation scope. It was not reset. A fresh harmless user scope passed: `memory.max=2147483648`, `memory.swap.max=0`, verified from inside the scope (`user-scope.*`). This establishes the numerical scope configuration, not an OOM stress test, production solve, or native whole-worker qualification. System swap exists, but the tested scope forbids its use. Existing Python 3.12.3 / NumPy 2.2.6 / SciPy 1.15.3 / Shapely 2.1.2 (GEOS 3.13.1) matches the numerical requirements. Codex and Claude heavy guards have identical hashes and use the shared queue.

**Failed prerequisite:** `sudo -n systemctl show --property=Version --value` exited 1, `sudo: a password is required`. The native guard also requires privileged transient units and runtime slice limits. No service/security configuration, sudo policy, .wslconfig or WSL lifecycle was changed. The supported next setup step is for the operator to provide an approved execution context for the existing guard where that probe succeeds, then separately admit its qualification procedure. Merely authenticating or running a Docker container does not prove all guard operations or the current native startup handshake.

## Fresh source inputs

The guarded source preparation took 285.42 seconds with cumulative child peak RSS 1,393,168 KiB; guard verdict PASS, minimum available memory 8,636 MiB. Source construction/materialization units use 180 seconds / 2 GiB address-space bounds; each evaluator child independently uses the existing 180-second bound and inherited 2 GiB limit. `source-steps.json` and target receipts record individual commands and outputs. The separate descriptor/repeat step took 24.02 seconds, peak RSS 1,130,920 KiB, shared guard PASS; its descriptor preparation is staging only, not a production solve or native resource qualification.

Fresh candidate05 → normalization → materialization → caps/clip/graph/census completed for all three targets. Complete census fields and unresolved identities match retained evidence, not only the counts (`census-comparison.json`). Repeated materialization yields 15 byte-identical outputs (`repeat.json`), including matching PCB/project/rule sidecars and source manifests. The manifests retain original UUID mappings and exact input/output hashes.

| Variant | Unresolved identities | This round |
| --- | ---: | --- |
| KA-t2 baseline | 196 | Fresh source census matches retained identities |
| KB-t2 baseline | 486 | Fresh source census matches retained identities |
| KB-p1 separate pilot | 480 | Fresh source census matches retained identities |
| KA long-B remedy | 194 | Prior reviewed result retained; not rematerialized or substituted |
| KA parallel-via / combined feed | 196 | Prior distinct result retained; no numerical rerun |
| KA wider-face feed | 196 | Prior baseline-equivalent negative retained |

P1's six-pad credit and long-B's two-pad credit still have zero newly disconnected identities in their retained evidence. No new geometry credit is claimed. All 550 protected files match before/after hashes (`preservation.json`). Completed independent t2 replay and finite-path coverage remain closed work; this is fresh input preparation for admission, not a new routing search.

## Admission packet and reproduction

Source inputs are local at `/home/takazudo/.cache/zudo-e16-runs/20261013-wsl-admission`. The preparation recipe and exact commands are retained in `prepare_source.py.txt`, `finish_packet.py.txt`, and the JSON receipts. Run these source operations from the integration worktree with the existing numerical venv, under the shared heavy guard, using fresh output names; existing directories deliberately refuse reuse. Source files, retained deltas and hashes in the manifests are the durable reproduction inputs. Large disposable boards/sheets remain ignored local artifacts; no Git LFS.

`native-descriptor-source.json.gz` binds this WSL checkout and source-head preparation, with staged inputs at `.circuit-cache/e16-native-wsl-source-f1650bba`. `oracle-request-source.json` separately specifies only the one deferred unittest, phase-python 1,680-second deadline, source/model/hook hashes, resource limits and heavy guard. It expects unittest exit 0 only when the original fixture returns its supported failure. The TI ZIP/library bytes already match their pins; no download was performed. The fresh `.circuit-cache/e16-oracle-wsl-final` evidence parent is prepared and `guard.json` is absent; the existing guard does not create its evidence parent. On reproduction, create a fresh evidence directory before seeking approval and never reuse a previous guard receipt.

These are **preparation records, not approval**. The current admission implementation requires an actual GitHub run ID and attempt, matching checkout/GitHub/parent SHA, reviewed hook, and external approval of the exact E16 request digest. No supported local-run identity mode exists. There is no actual admitted run for this checkout: the oracle request records a null run ID rather than inventing one; attempt 1 is the proposed request attempt, not evidence of a real run. A separate parent/operator must supply the actual run binding, global reservation and approval. The phase-python wrapper enforces run/SHA/hook admission; this retained command request must also receive explicit separate operator approval before execution.

After the evidence commit, regenerate the descriptor with `native_descriptor.py` against the same authenticated local materializations/graphs, a new ignored stage, the final HEAD and the actual proposed attempt. The final PR/issue checkpoint carries those final-head hashes and local paths; this avoids a self-referential evidence commit. Any changed HEAD, path, method, input or attempt requires fresh preparation and review. Do not export `EPIC242_PARENT_REQUEST_SHA256` from preparation, fabricate GITHUB variables, or reuse cloud receipts. A changed run binding requires a newly reviewed approval, even though the E16 descriptor itself does not contain the run ID.

The existing `qualify_resource_guard.py` requires separate admission and approved privilege. Its harmless fixture proof alone does not qualify the newer native startup handshake, as `scripts/kicad/README.md` explicitly states. Native execution remains held until the operator has qualified the actual protocol and approved the exact requests. Fill → full-severity DRC → complete UUID pad/feed/peer reconciliation must use the same preserved filled boards. Long-B and feed variants need their own matched inputs and separate admission.

## Validation and remaining work

- PASS: live user memory/swap scope configuration; fresh three-target source preparation; repeat materialization; exact census comparison; 28 targeted materialization/admission/numerical-fixture tests; circuit contract and documentation checks, guarded documentation build, strict built-site checks. Exact logs and source SHA are retained.
- FAIL: noninteractive privileged system-manager prerequisite. Runtime native runner qualification is incomplete.
- NOT RUN / NOT ADMITTED: deferred oracle unittest, runtime KiCad 10.0.6/ngspice version probes, E16 native fill/DRC/reconciliation, separately admitted production finite reduction/coupled/variant validation and native control/cleanup qualification.
- NOT RUN: aggregate suite (explicitly excluded by owner), full `regen-all.sh` (contains unadmitted native phases and canonical-board generation), retained-artifact native integration and CI for this continuation. Historical 1,681-test PASS remains bound to its original source receipt, not relabeled as a new run.
- OPEN / failed retained copper criteria: physical source/protection geometry, unsupported loads, complete source-to-pad resistance, node-KCL and energy acceptance, GH current allocation and physical/process qualification. Typical reduced-load voltage, isolated-strip resistance and analytic fixtures are not full electrical acceptance. G1/G2/G3/G4/G6 remain open.

One concrete next action: the operator supplies an approved runner context for the existing privileged guard and an actual supported run identity, then independently reviews/admits qualification and the final-head single-test request. Until these dependencies exist, no native command is authorized by this preparation.
