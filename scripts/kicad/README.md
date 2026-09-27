# KiCad 10 oracle

All headless KiCad commands for `zudo-osc-hole-field` run through `scripts/kicad/run.sh`. The wrapper requires KiCad 10.0.x and selects an available oracle in this order: `KICAD_CLI_BIN`, Docker with the digest in `pin.env`, then the standard macOS application path. If it cannot find a compatible oracle, it exits with an error. Missing KiCad is never treated as a skipped check.

## Use

From the repository root:

```sh
bash scripts/kicad/run.sh kicad-cli version
bash scripts/kicad/run.sh python3 -c 'import pcbnew; print(pcbnew.GetBuildVersion())'
bash scripts/kicad/run.sh ngspice -b path/to/model.cir
bash scripts/kicad/extract-stock.sh Device R
bash scripts/kicad/smoke.sh
```

`run.sh` mounts the repository at `/work`, sets it as the working directory, uses the caller's UID and GID for Docker, and gives KiCad a temporary writable home. Docker runs with `--rm --platform linux/amd64 --network none`. The temporary home is removed after each command, and files written into the repository remain owned by the caller.

`extract-stock.sh Library Name` prints a stock symbol S-expression if that symbol exists, or a stock footprint S-expression otherwise. For example, `bash scripts/kicad/extract-stock.sh Device R` prints the resistor symbol and `bash scripts/kicad/extract-stock.sh Resistor_SMD R_0603_1608Metric` prints that footprint. The command does not copy or modify project files.

## Platform notes

- **WSL/Linux:** install Docker and use the pinned image from `pin.env`.
- **macOS:** Docker Desktop runs the pinned `linux/amd64` image with emulation. A native KiCad 10.0.x CLI can be selected by setting `KICAD_CLI_BIN` to its executable path. Native `python3` and `ngspice` commands also need to be available on `PATH`; for Python board generation, that Python must import `pcbnew`.
- **CI:** install Docker and run the same scripts. Do not silently skip oracle checks when Docker or the image is missing.

The schematic and PCB files produced by these tools are unvalidated drafts. A clean ERC or DRC result reports rule checks only; it does not validate circuit behavior or board fit. Never generate or send fabrication order files from this workflow.

## Known pitfalls

- KiCad 9 cannot open the project's KiCad 10 file formats. The wrapper rejects versions outside `10.0.x`.
- ERC results can change when a fresh user home has no KiCad library tables. Keep project-local symbol and footprint library tables in fixtures and projects that reference stock libraries.
- KiCad CLI has no command to update a PCB from its schematic, and the IPC API needs a running GUI. Build or synchronize boards through `pcbnew` in the oracle.
- The pinned image contains KiCad, `pcbnew`, and `ngspice`, but no Java. Java-dependent tools do not belong in this oracle workflow.
- On macOS, native `KICAD_CLI_BIN` selection checks the CLI version. Commands such as `python3` and `ngspice` still use the corresponding executables on `PATH`.
