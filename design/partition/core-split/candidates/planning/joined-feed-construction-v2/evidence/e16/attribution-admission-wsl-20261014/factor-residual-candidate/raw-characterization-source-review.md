# Source-only raw metadata characterization increment

Implemented `attribution_characterization.py` and five synthetic tests. This module has no CLI, request compiler, admission dispatch or original artifact path. No original operator was accessed, no diagnostic/baseline consumed, and no request/grant created. This report is implementation evidence, not independent mathematical approval.

Question: what descriptor-derived raw coordinate bound R and maximum termination support square do the two exact operator artifacts imply? The existing helper extracts sizes/shapes/dtypes and actual support lengths without reading coefficient/node/weight values. R includes original stored class entries, four triples per barrel interval, and all support-length squares. Zero/duplicate/held cancellation cannot reduce this bound. The named array envelope is reported even when R exceeds the existing 16M ceiling. That outcome is `EXCEEDS_RAW_BOUND`, never successful preflight; every board and terminal summary says NOT_QUALIFIED and CHARACTERIZATION_ONLY. Within the bound also does not prove full pipeline fit.

## Execution and lifetimes

The caller supplies exactly KA and KB operator bindings, already independently authenticated inside the guard. Exact binding records are hashed into output. Basic schemas reject extra mesh/config/reduction artifacts, unsupported encodings, malformed digest fields, oversized byte declarations and excessive path text. These checks do not authenticate a trusted pickle. The existing transport verifies compressed bytes before interpretation, enforces decoded byte limits, drains/rehashes, and checks source descriptor stability. The whole operator is decoded: 'metadata-only' describes subsequent access, not partial pickle loading. Pickle memo/object allocation still requires the established enforced worker memory allocation.

Decode and inspect KA, release it, collect garbage, and only then decode KB. No operator reference is retained in the result, and exception traceback frames are discarded before collection. Synthetic weakrefs assert release on success and malformed metadata; a KB identity failure produces an INCOMPLETE receipt after only the KA row. GC cannot promise operating-system heap reclamation; allocator retained pages remain within the live worker allowance. No constructor, solver, mesh iterator, factor or global numerical array is invoked.

The existing Budget is inherited, never restarted. Descriptor visits additionally share an aggregate 16M checkpoint ceiling across both boards. Decoding and source hashing check the same deadline; source hashing streams at most 64KiB and caps each of four source files at 256KiB. Component rows are capped at 8192 bytes each; summary at 4096 bytes. Existing Output additionally accounts all serialized bytes, reserves failure receipt capacity and writes only two bounded component records. Exceeding any limit produces failure rather than an accepted partial characterization. Failures after Output creation receive module INCOMPLETE receipts; pre-output validation/creation failures belong to the authenticated outer host lifecycle.

## Receipt and dispatch review

Inspected attribution_transport.Output and attribution_supervisor terminal validation before implementing. Output preserves the existing components.jsonl digest, terminal status and false electrical/whole-board/adopted flags. Supervisor treats worker COMPLETE only as exhausted output, revokes its worker marker, verifies digest/flags and separately establishes supervisor/host cleanup evidence. CHARACTERIZATION_ONLY must remain explicit in the retained component and summary; COMPLETE must never be presented as successful qualification.

Before live dispatch: introduce an exact separately reviewed request kind; authenticate only the original KA/KB operator bindings and the full transitive executable source set; bind the fixed characterization question, metadata/output limits and method; select this function explicitly without entering run_pipeline or board_parts; retain guard-entry deadline, worker/aggregate memory, zero swap, aggregate output, single-use accounting and complete supervisor/host cleanup. Preserve trusted transport decoding and existing receipt revocation. Do not use this standalone source API to bypass the shared guard. The four emitted source hashes are an audit record of directly relevant code, not a replacement for complete request source binding, dependencies or grants. No new admission compatibility is claimed.

## Synthetic verification

`timeout 30 /home/takazudo/.cache/zudo-e16-numerical-venv/bin/python -B -m unittest test_attribution_characterization test_attribution_preallocation test_attribution_executor -q`: **35 tests PASS, 1.697 s**. The five new tests exercise real temporary serialized transport, descriptor objects that throw on numerical reads, raw excess without numerical allocation, matching existing named-array formula, sequential weakref lifetime, second-board identity failure, malformed metadata cleanup, checkpoint/output caps, cancellation and rejection of unrequested artifact kinds. Tests use inherited 512MiB address-space/20CPU-second fixture bounds and one BLAS thread. No tests read original data.

Source identities:

- attribution_characterization.py: 1b1d2226bd6702a86153cb3e1281d22e663f96a3e0a8d3fedc0dcb9cc4a8aa2d
- test_attribution_characterization.py: 0a6da862bf43c899b56eff073e95b223ce513faad1702012b1fc97dfc079b930
