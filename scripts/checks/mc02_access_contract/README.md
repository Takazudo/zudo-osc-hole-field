# MC02 manual-access evidence contract

This source-only checker keeps the retained **31 NOT SHOWN latch cases** bound
to their exact neighbour lists, K connector coordinates, front boards, lowering
stages and supporting-hand requirements. Six of these 31 require the supporting
hand; the full retained threading sequence has 12 such operations. It performs
no new footprint extraction, 122-endpoint contact mapping, body-height audit or
placement search. Those existing tools keep their own scope.

The transferred Hirose EDC3-150229-11 document is now byte-verified:1,059,562
bytes, SHA-256 c3257beed2331e5c95e176bc28441b04b804301a44c11b462e486fb5cc649d07.
All10 pages were visually reviewed. `evidence.json` retains the original handoff
URL, actual verified hash, document locators and review date. The offline audit
checks that reviewed transcription; it does not reopen raw PDFs unless
`--source-pdf PATH` is supplied. A new byte verification is then performed before
the audit. This distinguishes a durable reviewed-source receipt from a new raw
file check in each execution.

Closed height2.0 +/-0.2mm is a drawing dimension relative to its mounting
reference. Opening4.8mm is parenthesized/reference, without a guaranteed maximum.
Sheets6/8 require central manual actuator operation by hand only. These are now
verified source statements; assembled access remains entirely separate.

The checker rejects promotion of reference4.8mm to a guaranteed maximum, transfer
of closed-height tolerance to open geometry, manufactured finger/tool corridors,
and substitution of tool-only operation for the reported central manual action.
The existing UNSOURCED/ASSUMED5mm opening entry remains visible, not validated
by subtracting4.8 from5. Neither numerical comparison establishes a swept-envelope
bound, tolerance allowance or mounted clearance.

A per-case tool-reach or contact1-mapping flag is only a separate declared result;
even both flags true leave manual access NOT SHOWN. This checker does not verify
those flags or compute those other results. No case can be promoted to PASS by
this version, because it has no mounted/manual evidence admission path. That is
a deliberate limitation, not a physical rejection of the hardware. A future
assessment needs reviewed actuator swept geometry/tolerances, mounted neighbour
heights, actual central actuation in the stated assembly sequence, clearance for
any concurrent supporting hand, and cable threading/fold retention evidence.
No hand size, approach corridor or force limit is invented here.

```sh
python3 -B scripts/checks/mc02_access_contract/audit.py
python3 -B scripts/checks/frozen_studies.py discover scripts/checks/mc02_access_contract
pnpm circuit:check
```

Lightweight offline validation only. No canonical geometry/source edit, native
KiCad, DRC, fill, physical trial, adoption, supplier contact or manufacturing.
Pre-edit component check passed:84 manual records,445 declared placements
unverified; pin-asset check performed. Exact source drift, missing cases and
invalid evidence promotions are negative fixtures. An implementation/test PASS
means the evidence contract works, not that assembled access passes.

## Reviewed procedure amendment

The original2c53715 procedure allowed a plastic-tool alternative in steps7/12.
Source-first amendment `5620eea27dd2e3232f4ba81a4592660c3f439a26` requires central
hand-only actuation and prohibits inserting tools or fingernails. The checker now
expects zero source-method conflicts and verifies that wording on both61-operation
steps. Reintroducing the plastic-tool alternative fails even if its file hash is
rebound. This correction does not demonstrate any physical access: all31 NOT SHOWN
cases,12 supporting-hand operations and the17-end lowering burden remain unchanged.
The engineering baseline stays2c53715; current input/procedure source is5620eea2.
