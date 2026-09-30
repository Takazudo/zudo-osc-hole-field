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
