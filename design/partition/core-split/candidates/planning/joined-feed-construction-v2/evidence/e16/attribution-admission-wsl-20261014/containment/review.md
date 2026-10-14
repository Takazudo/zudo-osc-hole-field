# Independent containment and resource-boundary review

Reviewer: `/root/containment_review`, separate from the author. **PASS for the
containment source change and bounded host-mechanism evidence; no remaining
source findings. NOT RESOURCE_QUALIFIED; neither qualification nor production
admitted.** The reviewer inspected source and retained transcripts; the main
author executed the fixtures. The reviewer made no edits, launched no additional
host resources and accessed no original numerical artifacts.

## Reviewed final source

| File | SHA-256 |
| --- | --- |
| attribution_containment.py | b6a1a4abab94d4014cd348263ddc00463204883cb16b497adacb4a2f0d3fe310 |
| attribution_host.py | ddd6ffc23fa87f602d07ac3c59fb6677d2b122103ab280f58c96d0201d6fd2a4 |
| attribution_admission.py | 75c7396727d17f001931857ed2b807989e85949fc9033a26b620071b5ce7ef35 |

The review traced initial launcher, manager activation, actual cgroup placement,
guard shell/sampler/watchdog/helpers, outer controller, namespace launcher,
supervisor/worker descendants, retention, accounting, receipts and failure cleanup.
Process ancestry was not substituted for cgroup membership. Previous anonymous
mappings are released by exec; previous charges are not claimed to migrate.

## Findings resolved

- Unsupported live RuntimeMaxSec mutation was not accepted as a global host
  blocker. The notify-service alternative was tested and implemented; manager
  activation/runtime/stop must fit the original guard clock before a claim.
- Post-guard cleanup now retains the shared slot through demonstrated pidfd_getfd
  custody of the guard's actual flock, acquired before READY and held until exit.
- Cleanup covers both control and active cgroup subtrees, including migrated and
  detached descendants; process-tree cleanup alone was insufficient.
- Final accounting includes envelope receipt bytes and grant validity through
  the envelope tail. All acceptance flags stay false; exact request, immutable
  journal, durable guard row, root, limits, timing, cleanup and collection agree.
- The systemd-created interpreter removes the installed platform's documented
  loader controls before exec; later environment cleanup alone was insufficient.
- Pre-guard setup failures now retain bounded INCOMPLETE evidence without claiming
  cleanup or overwriting a prior receipt. Already consumed envelopes are refused.
- Historical guard-row parsing remains bounded separately from this operation's
  smaller exact receipt reserve; the initial parsing failure is retained.

## Evidence and qualification boundary

70 key-free focused tests PASS in 1.685 seconds. Final complete host fixture:
47,013,888 bytes root peak; 0.7702516 seconds from the conservative guard timestamp;
kernel swap limit zero and observed swap zero; tmpfs/retention, owned children and
unit collection complete. Exact durable guard-row SHA-256:
`be5dec04c8fb2352c1eac65da765778ac8082e674f4d97162fc262a1cec9b047`.
Wrong-placement and worker-failure fixtures refused and cleaned; the detached
failure child was reaped. Pre-guard root-limit mismatch retained INCOMPLETE
metadata; a separate observation established manager collection.

These use a 192 MiB synthetic envelope with tiny allocations and substituted
metadata/command providers. They do not authenticate a real qualification packet,
exercise original matrices or establish full numerical fit. Production worker
allocation remains 1216 MiB. The 64 MiB external shared-service/pre-exec reserve
remains an allowance requiring complete resource qualification, not a kernel
boundary claimed over shared services.

The signing handoff matches the actual compiler, fixed trust requirements,
message fields, principals, namespaces and detached-signature verification.
Independent trust, grants/reservation, combined qualification and later separate
production approval remain outside this source task.
