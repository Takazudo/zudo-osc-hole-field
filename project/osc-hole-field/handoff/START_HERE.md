# zudo-osc-hole-field R21 — local handoff

The two final control cells now contain **S&H 1 SLEW** and **S&H 2 SLEW**. Same grid, same hardware scale, no moved existing jacks/controls. The package is documentation/engineering input for local KiCad work, not a fabrication release.

## Look first

Open `payload/project/osc-hole-field/workbench/index.html` locally. The full flat/3D workbench is self-contained. A duplicate public copy is at `payload/doc/public/assets/osc-hole-field/workbench.html`. Both are generated publications; edit the source under the workbench directory.

`LOCAL_AGENT_PROMPT.md` is the ready-to-use starting instruction. Complete current decisions are in `payload/project/osc-hole-field/`; circuit candidate evidence is in `payload/research/osc-hole-field/`.

## Initialize locally

The reviewed official source is `5d0e2b630776489d394be341586b889dfe0d1cb8` (initializer version 0.1.0). The generated host requires Node >=22.18.0 and its pinned pnpm version. Use the upstream package family together; do not replace dependencies piecemeal.

```sh
# From this extracted handoff. Prints the proposed command without running by default:
python3 bootstrap_project.py /absolute/path/to/zudo-osc-hole-field
# Run the official initializer only after reviewing it:
python3 bootstrap_project.py /absolute/path/to/zudo-osc-hole-field --run

# Inspect and apply the content overlay:
python3 install_resources.py /absolute/path/to/zudo-osc-hole-field
python3 install_resources.py /absolute/path/to/zudo-osc-hole-field --apply

cd /absolute/path/to/zudo-osc-hole-field
corepack pnpm install
pnpm circuit:doctor
pnpm circuit:check
pnpm circuit:generate
pnpm check
pnpm build
pnpm check:site
pnpm dev
```

The initializer is create-only. Never run it against a non-empty existing project. For an already initialized circuit project, skip initialization and inspect the importer dry run; collisions are rejected instead of overwritten. Read the generated `circuit/WORKFLOW.md`.

The registry command is a local execution path, **not a claim that the package was downloaded here**. If it cannot obtain the pinned release, use your local checkout of the official repo, build/pack it under its own instructions, and pass the initializer entry script plus an **absolute** runtime tarball path using the bootstrap script's local options. See `UPSTREAM-INTEGRATION.md`.

## What is deliberately absent

No handwritten files in the generator-owned component tree. No counterfeit evidence inventory, retained PDF hash, fabricated source receipt, native KiCad release, order BOM/CPL or Gerber set. The installer preserves the official evidence workflow, version pins and dependencies.

## Validate these resources

```sh
python3 verify_handoff.py
python3 -m unittest discover -s tests -v
cd payload/project/osc-hole-field/workbench
python3 scripts/validate.py
node scripts/test_logic.cjs
node scripts/test_slew.cjs
```

Native documentation setup/build and native KiCad checks were not run in this environment. New direct downloads failed; web/connector sources were reviewed. See `VALIDATION.md` for the actual executed checks, not inferred passes.
