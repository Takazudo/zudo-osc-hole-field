# Raw-stamp guard implementation review

Reviewer: primary coordinator, independently inspecting the resource-review
agent's implementation; this is separate from its author review. No original
input or metadata opened. Scope is source-only internal guard, not admission.

- `attribution_preallocation.py` SHA256 `55d331ef8b535f849f8aab84f5221a570df0d68351553a450b700b8253fcc268`
- `attribution_executor.py` SHA256 `be61e82a8be2962f659c6dc59ffea3af019767885ed2e08804cf0f147f2a10af`
- `test_attribution_preallocation.py` SHA256 `3659808e23c8346ff2b20b862a8d3e08bf51366055fafc01638cd577bafd07df`

Read pinned finite_solve.board_parts/terminal_stamps and executor call sites.
The helper bounds retained stored arrays by descriptor size rather than CSR.nnz
(which may index indptr), adds four raw entries per barrel interval, and uses
sum of each actual terminal support length squared. Held pruning, duplicate
nodes and zero weights cannot reduce this conservative raw bound. The named
conversion-array bound and outer buffers remain explicitly partial. Full
workspace, other constructors, live baseline and allocator/tail declarations
are required before the internal constructor hook, with unchanged 1216 MiB cap.
A nonempty evidence reference is a caller assertion, not authenticated review.

The opt-in _board_selected preflight runs before held/free/Y allocations.
_guarded_board_parts is available for a future separately bound residual call.
Current run_pipeline does not select this policy, and SOURCE_NAMES does not
bind the new helper: this is intentionally NOT an admitted characterization
or qualification path. Both original pipeline call sites still need explicit
future lane integration after complete resource/admission review. The lazy
import avoids introducing an unbound helper into existing request execution.
No original numerical solver, assembly arithmetic or refinement was modified.

Independent execution: six focused tests PASS, 0.018 seconds under existing
512 MiB/20 CPU-second fixture and outer 30-second timeout. Descriptor stubs
throw on indexing/conversion/iteration; cap and missing-envelope tests prove
refusal before held_nodes and board_parts. Synthetic constructor output is
byte-identical to pinned original construction, including CSR/CSC arrays and
returned dense/free/position arrays. Deadline callback is reused, not reset.

Decision: ACCEPT source-only guard scaffold. NOT_QUALIFIED persists even when
caller-declared envelope comparison passes. No original execution eligibility,
no authenticated grant, no complete heap/time proof. This review does not
qualify the declaration values used only in tiny tests.
