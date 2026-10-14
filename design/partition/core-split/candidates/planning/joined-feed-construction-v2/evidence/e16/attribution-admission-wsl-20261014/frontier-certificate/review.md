# Certificate storage lifetime correction

Attempt5's actual initial reference count crossed4M before allocation. Eager
materialization cannot serve that input under the fixed cap. The reviewed change
loads an original reference row only when its pivot is reached. Pending entries
contain updates already applied by earlier pivots; untouched entries are read from
the exact original reference on first use. Loading never overwrites updates.
Therefore pivot order, update order, interval enclosures, retained factor bounds
and final Schur are the same as the eager algorithm, with different lifetimes.

Every materialized interval entry and retained factor is charged BEFORE insertion,
including the popped pivot row, future updates and surviving terminal rows. All
factors required by the existing inverse bound remain live and counted. The4M
live-entry cap and shared20Mupdate/16Minput limits are unchanged. Original input
CSR is not a second uncounted interval cache; it remains read-only input, under
input and kernel memory caps. Bounded scalar arithmetic temporaries use the same
convention as the eager checker. Row dictionary/list metadata, adjacent-index
lists, empty factor lists, forward/backward vectors, original CSC/CSR, basis and
all runtime allocations still consume the1216MiBworker/2GiBaggregate limits.
The retained original CSR lifetime is LONGER, and original-data fit is unproven.

The source-only prototype is ignored at this worktree's
`__inbox/e16-frontier/repro.py`; it imports actual interval arithmetic and uses only
tiny synthetic data. Declared bounds512MiBaddressspace,20CPU/30wallseconds,oneprocess,
oneBLASthread,<64KiBoutput.88random bordered cases agree bit-for-bit with eager
pivot minima, Schur intervals, inverse bounds and updatecounts. A40nodechain has
82eager entries versus42frontier peak, crossing a48entry fixture cap only in the
eager case. Densefill still rejects41>40. Actual run0.190s, no campaign charge.
The prototype is not committed; permanent meaningful regression tests are.

Independent `/root/certificate_feasibility` review caught a lingering `target`
row reference during disconnected/isolated pivots. Explicit deletion before pivot
release fixes that real live-entry undercount. Independent line tracing at98points
then found actualuniqueentries+factors peak5, matchingreported5, undercap5.
The experiment also exposed an unsortedCSC transpose assumption: converting to
CSR can produce canonical a while the CSC transpose view remains unsorted. Both
orientations now require canonical format before any merge/lookup; no input is
sorted or mutated by the checker. Original board_parts constructs canonicalCSC
from coordinate data, so this fixture discovery does not erase attempt5's result.

Permanent tests cover32random bordered nonsymmetricoriginals, unchanged inputhash,
eager/frontier arithmetic equivalence, exact42entry chain success/41cap refusal,
disconnected/isolated actual-object lifetime tracing, densefill rejection before
insertion, aggregateWork exhaustion across calls, both canonical gates and old
packet refusal.147focusedtestsPASS in4.168s, circuit/diff checksPASS. Initial new
regression assertions were corrected to reflect raised pipeline refusal and
line-level rather than before-insertion-only lifetime observation; source behavior
was not weakened to satisfy those assertions.

New explicit request `certificate_storage=lazy-frontier-interval-LDL-v1` binds the
selected lifetime contract. Old packets cannot silently select it. Mathematical
coercivity method, original solve/refinement, tolerances/RHS/physicalscope remain.
Small coupled/reference checks continue to use the existing eager method. Final
source/math/lifetime review by `/root/certificate_feasibility`:PASS, no blocking
findings, on identities in source-hashes.json. These are real technical reviews,
not external signing authorities or qualification evidence.

A subsequent FULL qualification may still fail on accumulated factors/fill,
arithmetic budget, interval resolution, memory or deadline. It requires a fresh
clean source/request, exact packet review and genuinely signed delegated grants,
then live admission; any claim consumes one diagnostic. No fit claim, automatic
retry, capincrease, solverchange or reduced mesh coverage is authorized by this
source result.

Separate final resource/admission review by `/root/coordination_review`:PASS on
the same U/P/E hashes; no new accounting or cleanup failure path. One fresh FULL
qualification is technically eligible after cleancommit and exactpacketreview,
with potential bounded chargedfailure and no prospective resource-fit assertion.
