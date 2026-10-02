# Historical power interface ERC notes

This records the original issue #24 pilot-plus-power capture, merged at `03c764840fb051708a2cb6939b47db1450751057`. Issue #52 superseded that inlet with the abstract EXT raw/load boundary. The current whole-master acceptance inventory is in [erc-notes.md](erc-notes.md); the figures and connector below are historical, not current hardware or protection acceptance. Source realization remains open in #57 and exact protection in #59.

At that checkpoint, KiCad 10.0.6 `--severity-all` on the generated instrument reported **zero errors** and 24 `pin_to_pin` warnings: twelve existing H1/H2 LED warnings documented with the pilot, plus twelve on `/POWER/`. Netlist export passed `scripts/schgen/verify_netlist.py`.

All twelve power warnings involved the exact `DW254P-2X8-L0` connector symbol, whose pins are typed `Unspecified` in the pinned zudo-pd CAD source. Eight warn where intentionally paralleled supply pins meet each other (1–2, 3/5/7/8, 4/6/8, 9–10, 11–12). Four warn where a supply pin meets a passive PTC or ground-side bleeder. They are pin-type warnings, not missing or conflicting net connections. Pins 13–16 are explicit no-connects. The generated netlist matches every specified pin.

ERC cannot prove the physical IDC orientation, cable pinout, fuse/TVS fault energy, rail sequence, regulator startup, or safe reversed/offset-cable insertion. Those are open physical gates in the power architecture page.
