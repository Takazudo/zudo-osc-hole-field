# Power interface ERC notes

KiCad 10.0.6 `--severity-all` on the generated instrument reports **zero errors** and 24 `pin_to_pin` warnings: twelve existing H1/H2 LED warnings documented with the pilot, plus twelve on `/POWER/`. Netlist export passes `scripts/schgen/verify_netlist.py`.

All twelve new warnings involve the exact `DW254P-2X8-L0` connector symbol, whose pins are typed `Unspecified` in the pinned zudo-pd CAD source. Eight warn where intentionally paralleled supply pins meet each other (1–2, 3/5/7/8, 4/6/8, 9–10, 11–12). Four warn where a supply pin meets a passive PTC or ground-side bleeder. They are pin-type warnings, not missing or conflicting net connections. Pins 13–16 are explicit no-connects. The generated netlist matches every specified pin.

ERC cannot prove the physical IDC orientation, cable pinout, fuse/TVS fault energy, rail sequence, regulator startup, or safe reversed/offset-cable insertion. Those are open physical gates in the power architecture page.
