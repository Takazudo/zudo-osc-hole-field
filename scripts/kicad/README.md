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

## Opt-in Epic 242 resource guard

`native_resource_guard.py` is an opt-in launcher for a separately admitted Linux worker. It requires a clean checkout at an explicitly admitted SHA, a reviewed SHA-256 of the installed `run.sh`, PID 1 systemd, a local systemd-cgroup-v2 Docker daemon, an available memory controller, and at least 8 GiB MemAvailable before launch. A unique worker identity can be used only once. A systemd worker slice caps the whole checks service plus labeled KiCad containers at 6 GiB with no swap; its shared parent caps admitted workers at 12 GiB with no swap. Admission counts populated slices, including stale runs, under a startup mutex; the external watchdog stops producers, removes only containers with that worker label, checks for survivors, then stops itself last. The whole-command deadline, free-memory floor, OOM events, container membership and caps are checked during execution. A parent admission must reserve at most two native slots globally across hosts and exclude all other native work; the local lock alone cannot establish global admission.

The wrapper enters bounded mode only when the launcher sets `EPIC242_NATIVE_SLICE`, `EPIC242_NATIVE_WORKER`, and `EPIC242_NATIVE_DEADLINE`. It refuses native CLI fallback and remote Docker in that mode. Its version probe and requested command both receive the memory and cgroup options and an inner absolute deadline. CI routes its existing native Python checks and all three board DRC checks through `ci_native_admission.py`. This entry refuses execution unless repository variables `EPIC242_PARENT_ADMISSION_RUN_ID`, `EPIC242_PARENT_ADMISSION_SHA`, and `EPIC242_REVIEWED_HOOK_SHA256` match the current run, checkout, and reviewed hook. The parent must reserve both global native slots for this workflow before setting those values. CI runs Python before board DRC and limits board DRC to two workers. A standard runner with under 8 GiB MemAvailable fails closed; the workflow does not select a larger runner automatically. Before a native check, an authorized operator must separately prove actual cgroup membership, Docker/daemon child containment, watchdog death and cleanup behavior on the selected runner using a bounded harmless pilot. Source tests and mocked Docker arguments do not provide that proof.

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

The explicit harmless proof helper `prove_resource_limits.py --run-harmless-proof --evidence FRESH.json` compiles a small static C process tree and imports it locally into Docker, without pulling any image or running KiCad. Two children each allocate 40 MiB beneath a shared 64 MiB cap; a separate sleeping process tree must be terminated after one second. The helper checks actual OOM/exit state and removes its owned containers and image. This proves Docker kernel controls only; it cannot qualify systemd whole-worker membership, independent supervisor or the 6 GiB/12 GiB native setup.
