# Comparison verification

Baseline: `94daec5bbdbb007b40f2b5840534b4083ddece0f` (separately published panel audit). Only this new comparison directory changes. All options are proposals; unknown inputs prevent a fit pass.

Author-run:

- Retrieved six exact Würth manufacturer PDFs; all 8/10/16 variants have explicit dimensions. Visually inspected representative header and socket drawing pages. Download hashes and retained dimension extracts in sources.json; downloaded originals remain in ignored `.circuit-cache/sources/standard-idc-comparison/` and can be reacquired via listed URLs.
- Independently retrieved pinned zudo-bus BOM, footprint and maker drawing; visually inspected drawing and checked pad grid/drills. No sibling changes. This does not establish cross-brand mating.
- Read official Würth catalog mating/active status, Doepfer bus conventions and 3M TS0732 flex data. Live stock query remains unknown; “active” is not “in stock”. No exact ribbon assembly selected.
- `python3 design/architecture-278/implementation/stage36/standard-idc-comparison/check.py --cache` and same with `python3 -O`: PASS arithmetic, unresolved-state guards and all ten download hashes. These checks are deliberately narrow; no clearance/physics solver is claimed.
- `COREPACK_HOME=/workspace/shared/corepack corepack pnpm circuit:check` before/after: PASS manual 68-line inventory, schematic/placement binding not performed, pin-asset check performed.

First failures/limitations:

- Independent reviewer caught header tail readback 3.1 mm; corrected to drawing value 3.0±0.15 mm before publication.

- Several web searches returned unrelated results. Used direct official drawing URLs and product catalog links; unrelated results are not evidence.
- Guessed Würth `/WR-BHD` catalog URL returned 404. Correct catalog paths were found and read successfully.
- `bs4` is not installed; used Python stdlib HTMLParser to read catalog text. No package installation.
- PDF rasterization emitted read-only Fontconfig cache warnings but produced readable images. The image-only DEALON PDF had no extractable text; inspected rendered page.
- Doepfer GIF could not be displayed by the web tool; textual bus description supports rail roles only. A numbered drawing-view map is not claimed.
- Installed KiCad remains incompatible (9.0.2 vs 10.0.6), as recorded in panel audit. No native regeneration, ERC/DRC, placement, manufacturing output, CI, physical, energized or procurement work. No historical replay needed: previous stage inputs remain untouched. Documentation site was not rebuilt for this non-published study directory; the preceding panel checkpoint has its separate successful build/site receipt.

Independent final review and repository check completion are recorded below after review.

Final repository check: `COREPACK_HOME=/workspace/shared/corepack corepack pnpm check` PASS generated pages/preflight, 31 models/previews and TypeScript. Source checks normal/-O with all download hashes were rerun after the tail correction and passed. Fresh remote parent remains `b58068fbaeb65886958a67a4f4978613414e31c5`.

Independent reviewer `stage36_review`: **PASS_SOURCE_REVIEW_ONLY**, no remaining blocking finding after the tail correction. Independently checked drawing dimensions, comparison arithmetic, 3M scope, Doepfer conventions and both normal/-O cache checks. Reviewer live catalog request timed out; successful catalog pairing/status read remains author-reported. No stock, fit, physical or architecture acceptance.

Final reviewed SHA256 bindings:

```text
README.md     94104371881b3fbce300a58536c849ec14104849eeb910f19fa65cbd58529c06
sources.json  9979a60d4f731a7e1b4f79922c5d258bc1b42ea891d2aea5b61b187f36a363c9
check.py      8b055a8a25c409ec70796af6051d87c17116fd4045c7a88c49deead2b66ef74c
```

Receipt reviewed before this administrative append: SHA256 `802252504f0c0802efa92623b2541cf53255ebc9892f3d50cf41b30fd1b6bb54`. No substantive source change followed final review.
