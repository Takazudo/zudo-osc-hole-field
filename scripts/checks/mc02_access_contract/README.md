# MC02 manual-access evidence contract

This source-only checker keeps the retained **31 NOT SHOWN latch cases** bound
to their exact neighbour lists, K connector coordinates, front boards, lowering
stages and supporting-hand requirements. Six of these 31 require the supporting
hand; the full retained threading sequence has 12 such operations. It performs
no new footprint extraction, 122-endpoint contact mapping, body-height audit or
placement search. Those existing tools keep their own scope.

The separate handoff at issue362 comment6948020518 reports Hirose
EDC3-150229-11, closed height2.0 +/-0.2mm, **reference** opening4.8mm and central
manual actuator operation on pages6/8. The exact document bytes have not been
verified by this task. `evidence.json` retains expected hash and source URLs,
with `UNVERIFIED_HANDOFF` and verified hash null. Source verification and subsequent
applicability review must update the contract explicitly; a claimed hash is not
proof that PDF bytes were inspected.

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
