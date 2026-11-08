# Scaffold provenance

This repository was initialized on 2026-09-28 with `create-zudo-circuit-doc@0.1.0`.

## Initializer command

```sh
STAGE=$(mktemp -d)
pnpm create zudo-circuit-doc@0.1.0 "$STAGE/zudo-osc-hole-field" \
  --name zudo-osc-hole-field --title "zudo-osc-hole-field" \
  --library zudo-osc-hole-field --agent both --yes --no-git --no-install
```

The scaffold was copied from the temporary directory into the repository root.

## Version family

- Initializer: `create-zudo-circuit-doc@0.1.0`
- Framework: `@takazudo/zudo-circuit-doc@0.1.0`
- Documentation packages: zudo-doc `5.27.0` and zfb `2.21.0`
- Package manager: pnpm `11.5.2`
- Node.js: `>=22.18.0`
- Python: `>=3.10`

## Upstream template

- Repository: [Takazudo/zudo-circuit-doc](https://github.com/Takazudo/zudo-circuit-doc)
- Template commit: `5d0e2b630776489d394be341586b889dfe0d1cb8`

## Migration to the 0.3 runtime family (2026-11-08)

The host was migrated by hand on 2026-11-08 following the upstream
[ownership and upgrades guide](https://github.com/Takazudo/zudo-circuit-doc/blob/create-zudo-circuit-doc-v0.2.1/doc/src/content/docs/concepts/ownership-and-upgrades.mdx);
no initializer was run over this repository. Reference scaffolds were generated in a scratch
directory with `create-zudo-circuit-doc@0.2.1` and `create-zudo-doc@9.1.4` and their `doc/` host
files were diffed against this project's copies (see `ZUDO_DEPS_PINS.md`).

- Framework: `@takazudo/zudo-circuit-doc@0.3.0` (range `^0.3.0`)
- Documentation packages: zudo-doc `9.1.4`, zudo-doc-history-server `9.1.4`, zfb family `5.2.2`
- Reference initializers (provenance only, not dependencies): `create-zudo-circuit-doc@0.2.1`,
  `create-zudo-doc@9.1.4`
- Node.js: `>=24 <25` (Node 24 LTS)
- Appearance: Classic (`themePack: "default"`), kept deliberately although 0.2.1 scaffolds Graphite
