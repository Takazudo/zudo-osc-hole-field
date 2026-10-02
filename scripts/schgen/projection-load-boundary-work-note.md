# Load-terminal and raw-tip projection boundary

The post-PR116 issue36 acceptance audit reproduced a sensitive local node escaping through a matched custom-terminal pair and wire while the independent verifier still reported PASS. The existing filter covered GH headers only. A separate matched GH pair carrying `/A01/IN_TIP` also passed because the old name filter recognized RAW_TIP but not the actual captured `_TIP` convention. These are synthetic export mutations, not reports of corrupted current board data.

The current source contract is explicit: `design/partition/partition-input.json`, `load_distribution.status`, says “PROPOSAL load side only; does not bridge AbstractBoundary CN301/XB301”. Its `net_order` contains +12V, -12V, +5V and three AGND returns. `scripts/checks/partition35.py` constructs the 36 terminals and 18 wires from this order and labels them existing regulated load-side nets only. Separately, `scripts/checks/io_partition60.py::crossing_kind` classifies every captured net ending `_TIP` as raw/exposed and forbids crossing.

The verifier now applies one Sensitive/raw/storage/summing screen to GH pins and custom load terminals. Load-terminal nets must also belong to the independent source input's load-distribution order; changing the generated partition's echoed power metadata cannot authorize a signal or raw inlet rail. Wire endpoint equality and one-wire-per-terminal checks remain required. The shared screen incorporates the existing `_TIP` classification.

Regressions exercise a local HOLD_CAP net on load wires, actual IN_TIP on an added GH harness, ordinary SIGNAL and raw +12V_IN/-12V_IN/+5V_IN on load terminals, and every declared load rail/return as a positive case. No board, pin mapping, source rail requirement, copper or component population is changed. Abstract inlet separation, physical DNP coverage and all existing interface identity checks remain intact.

The baseline passed in 289 seconds with no tracked regeneration drift. Final native export/ERC, aggregate/docs and CI receipts are recorded in the PR. Electrical/physical/thermal/manufacturing qualification remains NOT RUN; this is a logical projection guard for unvalidated drafts.
