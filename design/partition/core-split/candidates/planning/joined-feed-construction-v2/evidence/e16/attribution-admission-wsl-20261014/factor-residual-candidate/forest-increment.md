# Verifier-owned one-pass forest certificate

Continued after2dbab46b. The implemented certificate now owns one exhaustive
original-row proof, selects edges only from exact checked negative symmetric
coefficients, and constructs a rooted tree without a second producer row pass or
untrusted cached summary. Inputs must be stably owned; before/after byte/context
hashes detect persistent changes, not adversarial transient concurrent mutation.

Each row begins with a directly checked diagonal copy/decode. Every off-diagonal
contribution, of either sign, performs the explicit exact recurrence
margin <- margin - abs((a_ij+a_ji)/2). Both directed rows are verified. Only one
triangle is considered for tree selection; cycle edges are rejected but all their
row work remains charged. Union by size reroots the smaller component's parent
path and rotates edge conductances with it before connecting. After n-1 unions,
the tree is rerooted at the verified positive-margin node. DSU/size buffers die
before path/state/stack allocation. Memoized parent walks compute each path once.

The path-only inverse proof is unchanged: n*rmax/(1-delta*n*rmax), with the actual
maximum exact row deficit paid quantitatively. The interval-terminal wrapper is
separate and complete. Heterogeneous nonroot unions and final reroots verify the
conductance-rotation invariant; unit grids alone would not expose those bugs.

A new **proposed scalar contribution** ledger accompanies, rather than replaces,
the old floating, exact-kernel, bit-width and index ledgers. Every off-diagonal
recurrence is charged by ceil(max actual aligned operand/result width/64), before
normalization/cancellation. Selected edge conversion, root conversion, path
recurrences, norm corrections and tiny terminal midpoint/interval construction
are charged. Failed scopes finalize their charges. Pure diagonal initialization
and proof comparisons/sign selection retain their exact/index work but are not
numeric destination accumulations, consistent with the source-owned distinction
in the older LDL update counter. This explicit correspondence is reviewed for
bounded local implementation, **not approved for production fit**.

For one-word arithmetic the complete board certificate skeleton is m+n+5,
where m includes the original stored diagonal entries; the interval wrapper and
midpoint add their actual terms. Wide arithmetic increases it. Grid9 reports
455 proposed contributions,328 floating calls and71857 exact kernels, rather
than claiming455 machine operations. Proposed fill semantics would count checked
conductances/root/bounded scalar scratch/small intervals, while all vectors/index
storage still consume full bytes. The old conservative toy slot meter remains.

Packed logical payload peaks at25n bytes, but actual allocated buffers include
headers and are measured separately with sys.getsizeof. Fixed-size arrays replace
capacity-growing range construction. Explicit index event/read/write accounting
includes initialization, DSU compression, reroots, path checks and a single
cached maximum-path scan. Witness hashing streams12n buffer bytes; input hashes
run before and after proof. Candidate tracing and process RSS retain their prior
scope distinctions; these toy measures are not a complete original memory proof.

Validation:4 forest tests and all48 aggregate tests PASS. Separate mathematics
oracle proves103 selected-tree path/energy/inverse cases and51 complete coupled
interval cases, verifies actual single-row-pass coverage, and rejects persistent
matrix/context changes. Separate resource review checks recurrences, scopes,
failed-work snapshots, typed buffer lifetimes and proposed mapping. See
forest-math-review.md, the forest resource review and fixture/forest-results.json.

The full Python interpreted implementation has not established an original
180-second fit. Neither favorable proposed counts nor numerical-entry semantics
prove the1216MiB worker/2GiB aggregate fit. The original raw stamp constructor
still lacks a bound derived before allocation, and solver/Y/B/mesh overlap remains
part of the complete qualification obligation.

Next active source work is a bounded native implementation of the SAME exact
kernels/forest loops with all counters retained, plus a source-owned raw-stamp
preallocation guard. Installed C++13 is available; no new package/host change is
needed or authorized. No native function may be counted as one opaque update.
Keep the established synthetic order/resource limits and compare against the
independent exact oracles before any original-data characterization decision.

No original input, diagnostic, baseline, grant or live claim was consumed here.
Campaign remains15/24 diagnostics and2/3 baselines; no further baseline allowed.
KEEP_K1402_INCUMBENT and all selected experiment/solver/tolerance/resource/hardware
exclusions remain. Attribution is unresolved; the local assignment continues.
