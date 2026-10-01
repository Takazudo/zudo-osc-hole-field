# Issue 38: independent PTH current-epoch bridge review

## Verdict

**PASS for the stated local nominal geometry transfer.** I found no blocking defect in `verify_pth_current_epoch.py` or its v2 receipt. This does not admit finished plating, contact, source flux, three-dimensional/primal continuity, current, material, or joined electrical performance.

## Checks performed

- Recomputed all 288 dependency SHA-256 values in `pth-current-epoch-bridge-v2.json`; all match. The receipt SHA-256 is `9e2da4e763bb84341860e18d680fee0720eef165daa1132970f983edb367b2b4`.
- Ran the full read-only `verify()` again. Its returned object exactly equals the retained v2 receipt. The verifier rechecks its own source, the pinned historical certificate and mapping, the delegated J bridge, the current P/K native gates, board bytes, and every captured dependency at exit.
- Ran `python3 -m unittest scripts.pcbgen.test_verify_pth_current_epoch -v`: four tests pass, including altered drill, altered foil primitive, duplicate witness, and non-fitted witness rejection.
- Independently compared certificate triples `(ref, pad, uuid)` against the historical fitted PTH inventory: J left 100/100, J right 80/80, P 120/120, K 5/5. Each set is unique and equal. Every corresponding historical native hole is marked plated; every certificate still says physical finished wall and plating are unqualified.
- Read the P/K native gates: they bind the pinned KiCad 10.0.6 export, passing same-board DRC/parity, source manifest, companions and source inventory. The bridge compares complete old/current AGND ref-pad objects, all holes, outline and stack; it checks the specific certificate pad UUID, native drill and all foil primitives against the current export. Its final dependency pass catches input changes during verification.

## Limits and nonblocking observation

The four unit tests exercise P geometry only; K and J are exercised by the full verifier and delegated J bridge. Adding explicit K/J mutation tests would improve regression coverage, but the current v2 result was reproduced and the complete source closure matched. The result is a source-geometry equivalence statement; it does not renew historical numerical model receipts or qualify a fabricated PTH wall.
