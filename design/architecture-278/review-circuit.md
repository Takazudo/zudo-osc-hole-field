> Historical revision-1 review and exact input hashes are retained below. Current revision-2 review receipts are review-revision-electrical.md and review-revision-mechanical.md; see GATE.md for the current conditional recommendation.

# Independent circuit/source review — #280 / #284

Reviewer: circuit_review subagent, independent of the packet authors. Review is confined to source mapping and retained evidence; it is not electrical or hardware qualification. Baseline is 65cefd41fc39e064d38319115ad96016a1c6b71c. Execution lane: Python 3 on the parent's WSL Linux checkout. No native, SPICE, routing or bench campaign ran.

## Verdict

Accept the captured source mapping as a reviewable design checkpoint. **REVISE before architecture adoption or implementation authorization.** Final connector pin assignments, source/receiver impedance and loading bounds, return allocation, partial-power protection and physically supported rear disconnects remain explicit blockers. No signed-off full interface or production circuit is implied.

## Independent checks

Read the actual oscillator builder and I/O region/package refiner, rather than relying on counts alone. Traced four input fault/protection/receiver chains and four output driver/protection/local-feedback chains to the jack region; five pot wipers remain unbuffered at the controls. Timing, exponential sum, VEE5/feedback and raw waveforms remain rear-core local. The source's compensated reference and FM/PWM remote drivers retain local feedback; a crossing output net is not permission to move the sense point remotely.

The generated O1 plus OCTAVE_REF inventory contains 329 source units/declarations, 250 package/declaration entries, 171 nets, 768 connected endpoints and 38 NC endpoints. Nonphysical PWR_FLAG is explicitly distinguishable. Independent reverse joins confirmed every endpoint net and owner against the part-pin table, every owner summary against its endpoint owners and all rear-terminal source fields against partition.json. All 36 factory terminals are preserved, without claiming finished-enclosure rear accessibility. There are eight jack endpoints (four inputs/four outputs), eight controls, six O1 trims, and the separate shared octave-span assembly. Whole-package units including spare and supply units are retained; no cross-card split was found. O2/O5 mapping uses the shared family and actual designator bindings, not assumed panel strides.

All 13 service classes are present. Eleven harnesses contain 51 conductors: JL-K-15/16 each 8, K-O1-1/2 each 7, K-P-81 through 87 each 3. Both original connector faces and 102 crimps are retained as historical accounting; final candidate connector faces and power/reference returns remain unallocated. These are not savings or a final connector bill.

Whole-instrument ledger retains 33 functions, 438 locked centres, 5,904 physical packages and 8,226 units at the exact baseline. This is retained-report coverage, not live-source or native parity for every non-OSC family. Reuse classifications preserve exact-part applicability, copper/admission invalidation, unresolved requirements and parked campaigns.

## Findings and resolution

1. New shared-reference boundaries initially inherited `source-local` labels because the retained report placed both endpoints on K. Parent corrected classification to shared reference (and shared power/return for rails). Explicit tests now cover OSC_REF5, OSC_REFN5 and OSC_GATE_REF. RESOLVED.
2. Validator originally compared endpoint identities but not assigned nets or owners; net swaps and stale owner summaries could pass its direct coverage test. Reviewer applied a scoped fix comparing endpoint net/owner to parts, deriving owner summaries, checking NC ownership and checking shared-service classification. Added net-swap, owner-summary, endpoint-owner and shared-reference mutations. Existing package-split test initially encountered the earlier owner check; reordered checks so the package-split diagnostic remains tested directly. RESOLVED. These fixes are disclosed reviewer-authored validation changes, not independent review of those changes by their author.
3. Explicit final source/load electrical direction, impedance, dynamic/fault bounds and pin/return assignment for new shared-reference crossings remain OPEN. Endpoint roles allow topology inspection but do not constitute a complete final connector contract. No adoption while these remain missing.
4. Soldered factory rail terminals have no proven removable-card conversion or support/load path. OPEN, matching the packet's blocker; no claim of solder-free service qualification.

Validation after fixes: `python3 -m unittest scripts.architecture278.test_extract scripts.architecture278.test_ledger` — PASS, 19 tests. `python3 scripts/architecture278/extract.py --check` — PASS source extraction parity; NOT RUN electrical/physical qualification. `python3 scripts/architecture278/ledger.py --check` — PASS after semantic-join extension. These are bookkeeping/source checks, not ERC/DRC. Parent owns final circuit:check and final packet integration tests.

The final ledger additionally reuses immutable PR261 trimmer semantics from 7aba720c1246d6ec3f02909af6fb08dc774b3d31, joins 100 rows by Ref/Block/Role/MPN, and retains 28 roles without adopting label geometry or calibration qualification. Reviewed the added join against package/unit source fields; ledger reproduction and all 19 tests passed again.

## Exact reviewed bytes

- `scripts/architecture278/extract.py`: `07e618b971777aef687f7f3bebd6fb1d74620c939c2ba710ae5eec210d0da3e3`
- `scripts/architecture278/ledger.py`: `f47c7f681bae52b5d97cdcae73ebbfec85b2cdd08769b24593390ff9a9891f98`
- `scripts/architecture278/test_extract.py`: `4485aa61a53c99170460c42de5aab6e766dc2b205b920cce5037ee0276905dad`
- `scripts/architecture278/test_ledger.py`: `de964ac130aa102ebe6e03e3a81981d785d381c19a37fd935b5aafd27516c985`
- `design/architecture-278/interface-contract.json`: `1a96d576f5b33536014da093b6d0bf1e34b7ef5816dd1a35fb6d26465d4e656b`
- `design/architecture-278/source-ledger.json`: `708826e21e701dd04cea00e283360d4b7d6d48f78ef235a709b694927a538ce1`
- `design/architecture-278/interfaces.md`: `8e252c6efd2a5b5e48fb7c14c1181a277714954fd299c1e83bd3aad4e29af933`
- `design/architecture-278/reuse.md`: `2da1591565855e531c624057a965a508af180eb2584629004af9a1a810b6ad45`
- `design/spec/modules/oscillator.py`: `c83a10adb792265798ae453af4380300b6fde8d1e26afe6dca240412eb965d3e`
- `design/spec/modules/io_partition.py`: `3372b2b650e34d0323c080ec094715c2ed44864418864db3b95a84eb82f18980`
