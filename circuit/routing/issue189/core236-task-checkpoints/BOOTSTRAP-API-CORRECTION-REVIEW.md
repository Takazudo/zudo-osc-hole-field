# Bootstrap getter correction; source review before retry

The only bootstrap behavior change is IsRuleArea() → GetIsRuleArea(). Exact zone
UUID/layer/AGND/source-zone bytes, no-arcs native signature, unchanged source/context,
three controls, two independent reloads and zero-DRC-task receipt gates remain.
All323successful tasks,426manifest IDs, native kernel, boards and old approvals
are unchanged. No bootstrap retry or after DRC task dispatched.

The pinned linux/amd64 image config SHA1398ad98... is authenticated under image
18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec. Its compressed
binding layer06396e02790e91afe6eb20d8670e7f7e7f3966ff6fae8d9cecb0e476da2560bb was
fully streamed and SHA256verified; pcbnew.py SHA256decfa18059b9731ae3247fb7990e580c02c501f1b89114f31938512955bb6d17.
The recorded contract captures GetIsRuleArea (not IsRuleArea), inherited GetLayerSet
from BOARD_ITEM, inherited GetNetname from BOARD_CONNECTED_ITEM, filled-poly getter,
LSET.Seq and SHAPE_POLY_SET.ArcCount/Format. Wrapper extraction is API evidence,
not execution of those calls or a geometry receipt.

Strict fake now exposes only GetIsRuleArea and tests rule-area rejection. Old
ba8f6eb geometry source fails on the same strict inputs with AttributeError;
corrected source passes. Local49focused tests pass, compilation/YAML/diff checks
pass. This does not substitute for the real pinned-native contract check.

Ordinary exact-head CI adds one180second API-only smoke in a1GiB/1CPU/pids64
container, no network, readonly root/repository and64MiB writable temporary home;
cleanup trap removes its named container on every exit. It uses real pcbnew,
checks10.0.6 CLI/Python and exact wrapper SHA, then exercises GetIsRuleArea (including
true/false), GetLayerSet().Seq(), GetNetname(), GetFilledPolysList(), ArcCount()
and Format(). Its board/zone/poly are ephemeral in-memory test objects; no immutable
board is loaded or edited, no refill/save/DRC and no after signature/task receipt.
This runs within the existing Python CI job, not a dedicated workflow dispatch.
Require all5exact-head CI jobs green and that smoke step successful before retry.

## Narrow historical authentication

Five exact producer/run/artifact/ZIP-digest/approval-digest tuples are the only
new exceptions in approved_orchestration. It independently rehashes their original
nine git source blobs and requires original orchestration SHA256
2c6bf3e38116aeff707a5b218574ca5e6c9655a90198ac93e827c6fa043b542d. Artifact/source,
actual immutable approval bytes, native kernel/manifest/image/ledgers/receipts and
all native checks still run. Original approvals are not rewritten. Unknown
producers retain strict original/current orchestration equality. The existing53
pilot exception is unchanged. Tests reject altered source/run/artifact/digest,
approval SHA, original source-blob inventory and failed bootstrap approval.

Failed run38095685843 remains in owner-waves-a56f204/geometry-failed-38095685843
as explicitly reviewed FAILURE with empty ledger; it is never a trusted successful
producer or included in the five successful resume approvals. Its cache/config
warnings remain secondary; the established fatal cause was the wrong API getter.

## Proposed ONE bootstrap-only retry, NOT EXECUTED

After independent review of the exact pushed correction commit and successful
all5CI/API smoke, use a clean checkout of that exact commit and a new admission
marker. Populate REVIEWED_FULL_COMMIT from the reviewed correction SHA:

```sh
python3 - REVIEWED_FULL_COMMIT <<'PY'
import json,subprocess,sys
from pathlib import Path
head=sys.argv[1]
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==head
assert not subprocess.check_output(['git','status','--porcelain','--untracked-files=no'],text=True).strip()
resume=Path('circuit/routing/issue189/core236-task-checkpoints/owner-waves-a56f204/all-five-wave-resume-approvals.json').read_text().strip()
inputs=dict(board='osc-core',core_audit_task_pilot=True,core_audit_task_mode='geometry-bootstrap',core_audit_wave='0',core_audit_resume=resume,reviewed_commit=head,reviewed_manifest_sha256='e32424ccb6b44bde66cab3eb1214928eb20c8c6d46678011a06e719d5132a35e',adopt_run='',recover_core=False,replay_jl=False,replay_jr=False,local_repair=False)
with Path('/tmp/issue189-reviewed-bootstrap-retry-admission.json').open('x') as f:json.dump(dict(ref='agent-fix/189-core236-task-checkpoints',inputs=inputs),f)
PY
gh api --method POST repos/Takazudo/zudo-osc-hole-field/actions/workflows/378789207/dispatches \
 --input /tmp/issue189-reviewed-bootstrap-retry-admission.json
```

Before POST verify remote branch still equals the reviewed SHA, no unexpected
admission exists, and exact-head CI is green. Exclusive marker/lost response must
never trigger a second POST automatically. Existing global concurrency group,
max2workers,6GiB/container,12GiBaggregate/2GiBavailable,40mincommand/50minjob,
cleanup and partial upload stay unchanged; bootstrap uses one worker. Controller
reconstructs all323prior authenticated leaves before native read-only work.
Retrieve terminal immutable ZIP (approved connector fallback if needed), verify
fullSHA/fresh producer metadata, then authenticate_geometry must accept exact
native controls/independent reload receipt. Count0DRCtasks and stop for parent
review before103aftertasks. Any failure/partial/guard/cleanup problem stops without
native retry. No before packet replay, routing, adoption, merge or publication.
