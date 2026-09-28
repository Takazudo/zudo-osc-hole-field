# Noise ERC notes

The pinned KiCad 10.0.6 `--severity-all` run reports zero errors and zero warnings on `/N1/`. The combined instrument still has 108 previously documented `pin_to_pin` warnings (sample-and-hold LEDs 12, filter LEDs 24, envelope LEDs 60, power connector 12). Noise adds none. Full generated-spec to native netlist pin parity passes. This is an electrical connectivity check, not a physical or performance qualification.
