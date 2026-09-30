#!/usr/bin/env python3
"""Import the generic KiCad seed assets from the pinned zudo-pd revision.

This is an explicit, one-time import command. Normal regeneration uses only the
committed fragments, footprints, models and receipts, so it does not need the
sibling checkout or network access.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIBRARY = "zudo-osc-hole-field"
SOURCE_REPO_NAME = "Takazudo/zudo-pd"
SOURCE_COMMIT = "f25194fa73ded724e82d4561307c106480fbd9ce"
SOURCE_SYMBOLS = "symbols/zudo-pd.kicad_sym"
SOURCE_FOOTPRINT_DIR = "footprints/kicad/zudo-power.pretty"
SOURCE_MODEL_DIR = "footprints/kicad/zudo-pd.3dshapes"
SEED_DATE = "2026-09-28"

# Identities are taken from the #8 issue and the pinned zudo-pd owner manifests.
# The dictionaries intentionally contain only identity fields; this importer
# does not copy component specifications into symbol fields.
PARTS = [
    {"symbol": "0603Whitelight_C2290", "manufacturer": "KENTO", "mpn": "KT-0603W", "lcsc": "C2290", "package": "LED0603-R-RD_WHITE"},
    {"symbol": "KT-0603R", "manufacturer": "Hubei KENTO Elec", "mpn": "KT-0603R", "lcsc": "C2286", "package": "LED0603-RD"},
    {"symbol": "CC0603KRX7R9BB104", "manufacturer": "Yageo", "mpn": "CC0603KRX7R9BB104", "lcsc": "C14663", "package": "C0603"},
    {"symbol": "CL10A105KB8NNNC", "manufacturer": "Samsung Electro-Mechanics", "mpn": "CL10A105KB8NNNC", "lcsc": "C15849", "package": "C0603"},
    {"symbol": "CL31A106KBHNNNE", "manufacturer": "Samsung Electro-Mechanics", "mpn": "CL31A106KBHNNNE", "lcsc": "C13585", "package": "C1206"},
    {"symbol": "DW254P-2X8-L0", "manufacturer": "DEALON", "mpn": "DW254P-2X8-L0", "lcsc": "C4749189", "package": "IDC-TH_16P-P2.54_321016RG0ABK00A01"},
    {"symbol": "mSMD110-33V", "manufacturer": "TECHFUSE", "mpn": "mSMD110-33V", "lcsc": "C70119", "package": "F1812"},
    {"symbol": "SMAJ15A_C571368", "manufacturer": "High Diode", "mpn": "SMAJ15A", "lcsc": "C571368", "package": "D-FLAT_L4.3-W2.6-LS5.3-RD"},
    {"symbol": "SMAJ6.5A_C87267", "manufacturer": "Brightking", "mpn": "SMAJ6.5A", "lcsc": "C87267", "package": "D-FLAT_L4.3-W2.6-LS5.3-RD"},
]

for mpn, lcsc in [
    ("0603WAF1003T5E", "C25803"),
    ("0603WAF5602T5E", "C23206"),
    ("0603WAF4700T5E", "C23179"),
    ("0603WAF4701T5E", "C23162"),
    ("0603WAF1002T5E", "C25804"),
    ("0603WAF1001T5E", "C21190"),
    ("0603WAF5101T5E", "C23186"),
    ("0603WAF0000T5E", "C21189"),
    ("0603WAF1503T5E", "C22807"),
    ("0603WAF4301T5E", "C23159"),
]:
    PARTS.append({"symbol": mpn, "manufacturer": "UNI-ROYAL", "mpn": mpn, "lcsc": lcsc, "package": "R0603"})

for mpn, lcsc in [
    ("RT0603BRD071KL", "C110776"),
    ("RT0603BRD078K2L", "C861589"),
    ("RT0603BRD07680RL", "C861519"),
    ("RT0603BRD073K09L", "C861371"),
    ("RT0603BRD0733RL", "C861332"),
    ("RT0603BRD0710K5L", "C861077"),
]:
    PARTS.append({"symbol": mpn, "manufacturer": "YAGEO", "mpn": mpn, "lcsc": lcsc, "package": "R0603"})

UTILITY_SYMBOLS = [{"symbol": "PWR_FLAG", "manufacturer": "", "mpn": "", "lcsc": "", "package": ""}]

FOOTPRINTS = [
    "C0603",
    "C0805",
    "C1206",
    "R0603",
    "LED0603-RD",
    "LED0603-R-RD_WHITE",
    "IDC-TH_16P-P2.54_321016RG0ABK00A01",
    "F1812",
    "D-FLAT_L4.3-W2.6-LS5.3-RD",
    "TestPad_D1.5mm",
    "MountingHole_M3",
    "Fiducial_1mm_Mask2mm",
]

MODEL_BASES = [
    "C0603_L1.6-W0.8-H0.8",
    "C0805_L2.0-W1.3-H1.3",
    "C1206_L3.2-W1.6-H1.3",
    "R0603",
    "LED0603-RD",
    "IDC-TH_16P-P2.54_321016RG0ABK00A01",
    "F1812_L4.5-W3.2-H1.0",
    "SMA_L4.2-W2.6-LS5.3-RD",
]

FOOTPRINTS_WITH_MODELS = {
    "C0603": "C0603_L1.6-W0.8-H0.8",
    "C0805": "C0805_L2.0-W1.3-H1.3",
    "C1206": "C1206_L3.2-W1.6-H1.3",
    "R0603": "R0603",
    "LED0603-RD": "LED0603-RD",
    "IDC-TH_16P-P2.54_321016RG0ABK00A01": "IDC-TH_16P-P2.54_321016RG0ABK00A01",
    "F1812": "F1812_L4.5-W3.2-H1.0",
    "D-FLAT_L4.3-W2.6-LS5.3-RD": "SMA_L4.2-W2.6-LS5.3-RD",
}


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def git_show(repo: Path, path: str) -> bytes:
    try:
        return subprocess.check_output(
            ["git", "-C", str(repo), "show", f"{SOURCE_COMMIT}:{path}"],
            stderr=subprocess.PIPE,
        )
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.decode("utf-8", errors="replace").strip()
        raise RuntimeError(f"Unable to read pinned source {path}: {detail}") from exc


def sexpr_ranges(text: str, form_name: str, parent_depth: int) -> list[tuple[int, int]]:
    """Return spans for forms at one S-expression depth, ignoring quoted text."""
    spans: list[tuple[int, int]] = []
    depth = 0
    quoted = False
    escaped = False
    start: int | None = None
    token = f"({form_name}"
    for index, char in enumerate(text):
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
            continue
        if char == '"':
            quoted = True
            continue
        if char == "(":
            if depth == parent_depth and text.startswith(token, index):
                after = index + len(token)
                if after == len(text) or text[after].isspace() or text[after] == ")":
                    start = index
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == parent_depth and start is not None:
                spans.append((start, index + 1))
                start = None
            if depth < 0:
                raise ValueError("unbalanced closing parenthesis")
    if quoted or depth != 0:
        raise ValueError("unbalanced symbol library")
    return spans


def sexpr_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def symbol_name(block: str) -> str:
    match = re.match(r'\(symbol\s+("(?:\\.|[^"\\])*")', block)
    if not match:
        raise ValueError("symbol form has no quoted name")
    return json.loads(match.group(1))


def property_matches(block: str, names: tuple[str, ...]) -> list[re.Match[str]]:
    choices = "|".join(re.escape(name) for name in names)
    pattern = re.compile(
        rf'(?ms)^([ \t]*)\(property\s+"(?:{choices})"\s+"(?:\\.|[^"\\])*"'
    )
    return list(pattern.finditer(block))


def set_property(block: str, name: str, value: str, aliases: tuple[str, ...] = ()) -> str:
    allowed = (name, *aliases)
    matches = property_matches(block, allowed)
    if len(matches) > 1:
        raise ValueError(f"symbol contains multiple {name} properties")
    encoded_name = sexpr_string(name)
    encoded_value = sexpr_string(value)
    if matches:
        match = matches[0]
        replacement = f'{match.group(1)}(property {encoded_name} {encoded_value}'
        return block[: match.start()] + replacement + block[match.end() :]

    reference = re.search(r'(?m)^([ \t]*)\(property\s+"Reference"', block)
    indent = reference.group(1) if reference else "\t\t"
    child_indent = indent + "  "
    nested = re.search(r'(?m)^[ \t]*\(symbol\s+"[^"]+_0_\d+"', block)
    if not nested:
        raise ValueError(f"symbol {symbol_name(block)} has no graphics unit")
    line_start = block.rfind("\n", 0, nested.start()) + 1
    property_text = (
        f'{indent}(property {encoded_name} {encoded_value}\n'
        f'{child_indent}(at 0 0 0)\n'
        f'{child_indent}(effects (font (size 1.27 1.27)) (hide yes))\n'
        f'{indent})\n'
    )
    return block[:line_start] + property_text + block[line_start:]


def normalize_symbol(block: str, part: dict[str, str]) -> str:
    footprint = f"{LIBRARY}:{part['package']}" if part["package"] else ""
    block = set_property(block, "Footprint", footprint)
    block = set_property(block, "MPN", part["mpn"])
    block = set_property(block, "Manufacturer", part["manufacturer"])
    block = set_property(block, "LCSC", part["lcsc"], aliases=("LCSC Part",))
    return block.strip()


def quoted_property_value(block: str, field: str) -> str | None:
    pattern = re.compile(
        rf'(?ms)^\s*\(property\s+"{re.escape(field)}"\s+((?:\\.|[^"\\])*)'
    )
    match = pattern.search(block)
    if not match:
        return None
    return match.group(1).replace('\\"', '"').replace('\\\\', '\\')


def remove_unavailable_model(text: str) -> str:
    """Drop only the white LED's unresolved EasyEDA model node."""
    match = re.search(r'(?m)^[ \t]*\(model\s+"\$\{EASYEDA2KICAD\}[^\n]*', text)
    if not match:
        return text
    depth = 0
    quoted = False
    escaped = False
    end = None
    for index in range(match.start(), len(text)):
        char = text[index]
        if quoted:
            if escaped:
                escaped = False
            elif char == "\\":
                escaped = True
            elif char == '"':
                quoted = False
            continue
        if char == '"':
            quoted = True
        elif char == "(":
            depth += 1
        elif char == ")":
            depth -= 1
            if depth == 0:
                end = index + 1
                break
    if end is None:
        raise ValueError("unclosed unavailable model reference")
    start = match.start()
    while start > 0 and text[start - 1] in " \t":
        start -= 1
    if start > 0 and text[start - 1] == "\n":
        start -= 1
    while end < len(text) and text[end] in " \t":
        end += 1
    if end < len(text) and text[end] == "\n":
        end += 1
    return text[:start] + text[end:]


def normalize_footprint(text: str, name: str) -> str:
    text = remove_unavailable_model(text)
    root = re.compile(r'(?m)^(\(module\s+)([^\s)]+)')
    if root.search(text):
        text = root.sub(lambda m: f"{m.group(1)}{name}", text, count=1)
    else:
        quoted_root = re.compile(r'(?m)^(\(footprint\s+)("(?:\\.|[^"\\])*" )?')
        match = quoted_root.search(text)
        if not match:
            raise ValueError(f"unrecognized footprint root for {name}")
        text = text[: match.start()] + f'(footprint {sexpr_string(name)} ' + text[match.end() :]
    text = text.replace(
        "${KIPRJMOD}/../../footprints/kicad/zudo-pd.3dshapes/",
        "${KIPRJMOD}/../../footprints/kicad/zudo-osc-hole-field.3dshapes/",
    )
    return text


def parse_xyz(text: str, key: str) -> list[float] | None:
    match = re.search(rf'\({key}\s+\(xyz\s+([^)]*)\)\)', text)
    if not match:
        return None
    try:
        values = [float(value) for value in match.group(1).split()]
    except ValueError:
        return None
    return values if len(values) == 3 else None


def source_url(path: str) -> str:
    return f"https://github.com/{SOURCE_REPO_NAME}/blob/{SOURCE_COMMIT}/{path}"


def output_hashes(paths: list[str]) -> dict[str, str]:
    values = {}
    for relative in paths:
        path = ROOT / relative
        if not path.is_file():
            raise RuntimeError(f"Missing generated asset while writing receipt: {relative}")
        values[relative] = sha256(path.read_bytes())
    return values


def asset_slug(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")


def seeded_output_paths() -> list[Path]:
    paths = [ROOT / "symbols" / f"{LIBRARY}.kicad_sym"]
    paths.extend(ROOT / "symbols" / "src" / f"{part['symbol']}.kicad_sym" for part in [*PARTS, *UTILITY_SYMBOLS])
    paths.extend(ROOT / "footprints" / "kicad" / f"{LIBRARY}.pretty" / f"{name}.kicad_mod" for name in FOOTPRINTS)
    paths.extend(
        ROOT / "footprints" / "kicad" / f"{LIBRARY}.3dshapes" / f"{base}.{extension}"
        for base in MODEL_BASES
        for extension in ("step", "wrl")
    )
    asset_ids = {
        f"cad-{part['lcsc'].lower()}-{asset_slug(part['symbol'])}"
        for part in PARTS
    }
    asset_ids.add("symbol-pwr-flag")
    component_packages = {part["package"] for part in PARTS}
    asset_ids.update(f"footprint-{asset_slug(name)}" for name in FOOTPRINTS if name not in component_packages)
    paths.extend(ROOT / "circuit" / "cad-receipts" / f"{asset_id}.receipt.json" for asset_id in asset_ids)
    return paths


def make_receipt(
    *,
    asset_id: str,
    manufacturer: str | None,
    mpn: str | None,
    package: str | None,
    variant_notes: str | None,
    source_paths: list[str],
    output_paths: list[str],
    symbol: str | None,
    footprint: str | None,
    model_path: str | None,
    transform: dict[str, list[float] | None],
    fidelity_reason: str,
    source_hashes: dict[str, str],
) -> dict:
    primary_path = source_paths[0]
    return {
        "receipt_version": 1,
        "identity": {
            "asset_id": asset_id,
            "record_id": None,
            "manufacturer": manufacturer,
            "mpn": mpn,
            "package": package,
            "variant_notes": variant_notes,
        },
        "acquisition": {
            "provider": f"GitHub repository {SOURCE_REPO_NAME}",
            "library_release_tag": None,
            "source_url": source_url(primary_path),
            "acquired_on": SEED_DATE,
            "original_filenames": [Path(path).name for path in source_paths],
            "sha256": source_hashes,
        },
        "representation": {
            "files": output_paths,
            "formats": sorted({Path(path).suffix.lstrip(".") for path in output_paths}),
            "units": "KiCad schematic units; footprint and model dimensions in mm",
            "original_paths": source_paths,
        },
        "fidelity": {
            "class": "family",
            "reason": fidelity_reason,
            "evidence": [
                f"Source bytes are pinned to zudo-pd commit {SOURCE_COMMIT}.",
                "The footprint is an imported package representation; exact manufacturer dimensional correspondence has not been independently established here.",
            ],
        },
        "derivation": {
            "derived": True,
            "input_sha256": source_hashes,
            "tool": "scripts/libgen/seed_assets.py and scripts/libgen/gen_courtyards.py",
            "tool_version": "1",
            "parameters": {
                "source_commit": SOURCE_COMMIT,
                "library_nickname": LIBRARY,
                "operations": [
                    "extract one symbol",
                    "set local footprint nickname",
                    "normalize identity fields",
                    "generate courtyard",
                    "normalize STEP text line endings and trailing spaces",
                ],
            },
            "output_sha256": output_hashes(output_paths),
        },
        "cad_use": {
            "symbol": f"{LIBRARY}:{symbol}" if symbol else None,
            "footprint": f"{LIBRARY}:{footprint}" if footprint else None,
            "model_path": model_path,
            "transform": {
                "offset": transform.get("offset"),
                "rotation": transform.get("rotation"),
                "scale": transform.get("scale"),
            },
            "seating_plane": None,
        },
        "checks": {
            "performed": [
                f"Source file SHA-256 values were calculated from {SOURCE_COMMIT} Git objects.",
                "Generated output SHA-256 values are checked by scripts/libgen/check_lib.py.",
            ],
            "remaining_physical_checks": [
                "Compare package dimensions, pin/pad numbering, orientation and seating against the exact manufacturer's drawing before using a board for fabrication."
            ],
        },
        "publication": {
            "preview_selected": False,
            "download_published": False,
            "permitted_scope": None,
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source-repo", required=True, type=Path, help="read-only zudo-pd checkout containing the pinned commit")
    parser.add_argument("--replace", action="store_true", help="overwrite existing seed outputs after reviewing local edits")
    args = parser.parse_args()
    source_repo = args.source_repo.resolve()
    if not source_repo.is_dir():
        parser.error(f"source repository does not exist: {source_repo}")
    available = subprocess.run(
        ["git", "-C", str(source_repo), "cat-file", "-e", f"{SOURCE_COMMIT}^{{commit}}"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    if available.returncode != 0:
        parser.error(f"pinned source commit is unavailable in {source_repo}; fetch it in that checkout first")
    existing_outputs = [path for path in seeded_output_paths() if path.exists()]
    if existing_outputs and not args.replace:
        parser.error(
            "seed outputs already exist; review local edits and pass --replace to overwrite them: "
            + ", ".join(path.relative_to(ROOT).as_posix() for path in existing_outputs[:5])
            + (" …" if len(existing_outputs) > 5 else "")
        )

    symbol_source = git_show(source_repo, SOURCE_SYMBOLS)
    symbol_text = symbol_source.decode("utf-8")
    symbol_ranges = sexpr_ranges(symbol_text, "symbol", parent_depth=1)
    source_symbols: dict[str, list[str]] = {}
    for start, end in symbol_ranges:
        block = symbol_text[start:end]
        source_symbols.setdefault(symbol_name(block), []).append(block)

    source_file_hashes: dict[str, str] = {SOURCE_SYMBOLS: sha256(symbol_source)}
    fragment_paths: dict[str, str] = {}
    library_header = {
        "version": re.search(r"\(version\s+(\d+)\)", symbol_text).group(1),
        "generator": re.search(r'\(generator\s+"([^"]+)"\)', symbol_text).group(1),
        "generator_version": re.search(r'\(generator_version\s+"([^"]+)"\)', symbol_text).group(1),
    }

    for part in [*PARTS, *UTILITY_SYMBOLS]:
        name = part["symbol"]
        blocks = source_symbols.get(name)
        if not blocks:
            raise RuntimeError(f"Pinned symbol library has no symbol named {name}")
        # On duplicate names, use the last definition in the pinned library.
        # The duplicated KT-0603R definitions were inspected and have the same
        # 1=K, 2=A pin mapping; choosing one keeps the new library unambiguous.
        symbol_block = normalize_symbol(blocks[-1], part)
        fragment = (
            "(kicad_symbol_lib\n"
            f"\t(version {library_header['version']})\n"
            f"\t(generator {sexpr_string(library_header['generator'])})\n"
            f"\t(generator_version {sexpr_string(library_header['generator_version'])})\n"
            f"\t{symbol_block.replace(chr(10), chr(10) + chr(9))}\n"
            ")\n"
        )
        relative = f"symbols/src/{name}.kicad_sym"
        (ROOT / relative).parent.mkdir(parents=True, exist_ok=True)
        (ROOT / relative).write_text(fragment, encoding="utf-8", newline="\n")
        fragment_paths[name] = relative

    source_footprints: dict[str, bytes] = {}
    output_footprints: dict[str, str] = {}
    for name in FOOTPRINTS:
        source_path = f"{SOURCE_FOOTPRINT_DIR}/{name}.kicad_mod"
        source_bytes = git_show(source_repo, source_path)
        source_file_hashes[source_path] = sha256(source_bytes)
        normalized = normalize_footprint(source_bytes.decode("utf-8"), name).encode("utf-8")
        source_footprints[name] = source_bytes
        relative = f"footprints/kicad/{LIBRARY}.pretty/{name}.kicad_mod"
        (ROOT / relative).parent.mkdir(parents=True, exist_ok=True)
        (ROOT / relative).write_bytes(normalized)
        output_footprints[name] = relative

    model_sources: dict[str, list[str]] = {}
    model_outputs: dict[str, list[str]] = {}
    for base in MODEL_BASES:
        model_sources[base] = []
        model_outputs[base] = []
        for extension in ("step", "wrl"):
            source_path = f"{SOURCE_MODEL_DIR}/{base}.{extension}"
            source_bytes = git_show(source_repo, source_path)
            source_file_hashes[source_path] = sha256(source_bytes)
            relative = f"footprints/kicad/{LIBRARY}.3dshapes/{base}.{extension}"
            (ROOT / relative).parent.mkdir(parents=True, exist_ok=True)
            output_bytes = source_bytes
            if extension == "step":
                output_bytes = b"\n".join(
                    line.rstrip(b" \t") for line in source_bytes.splitlines()
                ) + b"\n"
            (ROOT / relative).write_bytes(output_bytes)
            model_sources[base].append(source_path)
            model_outputs[base].append(relative)

    # Assemble symbols and create the generated courtyards before locking output hashes.
    for script in ("build_symbol_lib.py", "gen_courtyards.py"):
        result = subprocess.run([sys.executable, str(ROOT / "scripts/libgen" / script)], cwd=ROOT)
        if result.returncode != 0:
            return result.returncode

    def outputs_for(package: str, symbol_path: str | None = None) -> list[str]:
        outputs = [output_footprints[package]] if package else []
        if symbol_path:
            outputs.insert(0, symbol_path)
        model_base = FOOTPRINTS_WITH_MODELS.get(package)
        if model_base:
            outputs.extend(model_outputs[model_base])
        return outputs

    def source_paths_for(package: str, symbol: str | None = None) -> list[str]:
        paths = [SOURCE_SYMBOLS] if symbol else []
        if package:
            paths.append(f"{SOURCE_FOOTPRINT_DIR}/{package}.kicad_mod")
            model_base = FOOTPRINTS_WITH_MODELS.get(package)
            if model_base:
                paths.extend(model_sources[model_base])
        return paths

    def model_details(package: str) -> tuple[str | None, dict[str, list[float] | None]]:
        base = FOOTPRINTS_WITH_MODELS.get(package)
        if not base:
            return None, {"offset": None, "rotation": None, "scale": None}
        footprint = source_footprints[package].decode("utf-8")
        return (
            f"${{KIPRJMOD}}/../../footprints/kicad/{LIBRARY}.3dshapes/{base}.wrl",
            {"offset": parse_xyz(footprint, "offset"), "rotation": parse_xyz(footprint, "rotate"), "scale": parse_xyz(footprint, "scale")},
        )

    receipt_dir = ROOT / "circuit/cad-receipts"
    receipt_dir.mkdir(parents=True, exist_ok=True)
    receipts: list[tuple[str, dict]] = []
    for part in PARTS:
        name = part["symbol"]
        package = part["package"]
        symbol_path = fragment_paths[name]
        output_paths = outputs_for(package, symbol_path)
        source_paths = source_paths_for(package, symbol=name)
        hashes = {path: source_file_hashes[path] for path in source_paths}
        model_path, transform = model_details(package)
        asset_id = f"cad-{part['lcsc'].lower()}-{asset_slug(name)}"
        if name.startswith("0603WAF"):
            variant_notes = "0603 1% resistor; exact orderable identity comes from the pinned zudo-pd owner bundle."
            fidelity_reason = "The part identity is exact, but R0603 is a shared package-family footprint and has not been verified against each manufacturer's drawing."
        elif name.startswith("RT0603BRD07"):
            variant_notes = "0603 0.1% thin-film resistor; exact orderable identity comes from the pinned zudo-pd owner bundle."
            fidelity_reason = "The part identity is exact, but R0603 is a shared package-family footprint and has not been verified against each manufacturer's drawing."
        elif name == "0603Whitelight_C2290":
            variant_notes = "KENTO KT-0603W, white 0603 LED; the imported footprint referenced an unavailable EASYEDA2KICAD model, so no 3D model is claimed."
            fidelity_reason = "The symbol identifies the requested KENTO variant; the copied footprint is a generic 0603 LED package and the source commit contains no matching retained white LED model."
        else:
            variant_notes = "Exact symbol identity copied from the pinned zudo-pd library; footprint geometry is classified as package-family fidelity."
            fidelity_reason = "The symbol represents the exact named orderable part, while the copied footprint/model is a generic package representation from zudo-pd and has not been matched to a manufacturer dimensional drawing in this task."
        receipt = make_receipt(
            asset_id=asset_id,
            manufacturer=part["manufacturer"],
            mpn=part["mpn"],
            package=package,
            variant_notes=variant_notes,
            source_paths=source_paths,
            output_paths=output_paths,
            symbol=name,
            footprint=package,
            model_path=model_path,
            transform=transform,
            fidelity_reason=fidelity_reason,
            source_hashes=hashes,
        )
        receipts.append((asset_id, receipt))

    for part in UTILITY_SYMBOLS:
        name = part["symbol"]
        symbol_path = fragment_paths[name]
        source_paths = [SOURCE_SYMBOLS]
        asset_id = "symbol-pwr-flag"
        receipt = make_receipt(
            asset_id=asset_id,
            manufacturer=None,
            mpn=None,
            package=None,
            variant_notes="Abstract KiCad power-flag symbol; it declares ERC power intent and has no manufactured package.",
            source_paths=source_paths,
            output_paths=[symbol_path],
            symbol=name,
            footprint=None,
            model_path=None,
            transform={"offset": None, "rotation": None, "scale": None},
            fidelity_reason="This is a schematic utility symbol, not a physical component. No package geometry is claimed.",
            source_hashes={SOURCE_SYMBOLS: source_file_hashes[SOURCE_SYMBOLS]},
        )
        receipt["fidelity"]["class"] = "family"
        receipts.append((asset_id, receipt))

    for name in FOOTPRINTS:
        if name in {part["package"] for part in PARTS}:
            continue
        source_path = f"{SOURCE_FOOTPRINT_DIR}/{name}.kicad_mod"
        output_paths = [output_footprints[name]]
        source_paths = [source_path]
        model_path, transform = model_details(name)
        model_base = FOOTPRINTS_WITH_MODELS.get(name)
        if model_base:
            output_paths.extend(model_outputs[model_base])
            source_paths.extend(model_sources[model_base])
        hashes = {path: source_file_hashes[path] for path in source_paths}
        asset_id = f"footprint-{asset_slug(name)}"
        receipt = make_receipt(
            asset_id=asset_id,
            manufacturer=None,
            mpn=None,
            package=name,
            variant_notes="Generic footprint asset; no specific manufacturer or orderable MPN is assigned.",
            source_paths=source_paths,
            output_paths=output_paths,
            symbol=None,
            footprint=name,
            model_path=model_path,
            transform=transform,
            fidelity_reason="Generic mechanical or test footprint copied from the sibling library; no vendor-specific part identity is claimed.",
            source_hashes=hashes,
        )
        receipts.append((asset_id, receipt))

    # Receipts for repeated packages share the same current footprint/model
    # hashes; include the output model bytes in their derivation record.
    for asset_id, receipt in receipts:
        receipt_path = receipt_dir / f"{asset_id}.receipt.json"
        receipt_path.write_text(json.dumps(receipt, indent=2, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")

    # Capture generic footprint/model files under the CAD receipts too. The
    # models are recorded in every component receipt that uses their package.
    print(f"Seeded {len(PARTS) + len(UTILITY_SYMBOLS)} symbol fragments, {len(FOOTPRINTS)} footprints, {sum(len(x) for x in model_outputs.values())} models and {len(receipts)} receipts from {SOURCE_COMMIT}.")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError, RuntimeError, AttributeError) as exc:
        print(f"seed_assets: {exc}", file=sys.stderr)
        raise SystemExit(1)
