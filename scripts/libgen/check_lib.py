#!/usr/bin/env python3
"""Check the project's assembled symbol and footprint assets and receipts."""

from __future__ import annotations

import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LIBRARY = "zudo-osc-hole-field"
FRAGMENT_DIR = ROOT / "symbols" / "src"
SYMBOL_LIBRARY = ROOT / "symbols" / f"{LIBRARY}.kicad_sym"
FOOTPRINT_DIR = ROOT / "footprints" / "kicad" / f"{LIBRARY}.pretty"
MODEL_DIR = ROOT / "footprints" / "kicad" / f"{LIBRARY}.3dshapes"
RECEIPT_DIR = ROOT / "circuit" / "cad-receipts"
MODEL_PREFIX = f"${{KIPRJMOD}}/../../footprints/kicad/{LIBRARY}.3dshapes/"

from gen_courtyards import node_name, parse, rewrite, walk  # noqa: E402


def fail(errors: list[str], message: str) -> None:
    errors.append(message)


def direct_children(node, name: str):
    return [item for item in node[1:] if isinstance(item, list) and node_name(item) == name]


def property_values(symbol, field_name: str) -> list[str]:
    values = []
    for prop in direct_children(symbol, "property"):
        if len(prop) >= 3 and prop[1] == field_name and isinstance(prop[2], str):
            values.append(prop[2])
    return values


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def valid_sha(value) -> bool:
    return isinstance(value, str) and re.fullmatch(r"[0-9a-f]{64}", value) is not None and value != "0" * 64


def symbol_name(symbol) -> str:
    return symbol[1] if len(symbol) > 1 and isinstance(symbol[1], str) else "<unnamed>"


def footprint_root_name(tree) -> str | None:
    if node_name(tree) not in {"module", "footprint"} or len(tree) < 2 or not isinstance(tree[1], str):
        return None
    return tree[1].split(":")[-1]


def check_symbols(errors: list[str]) -> tuple[int, set[str]]:
    if not SYMBOL_LIBRARY.is_file():
        fail(errors, f"assembled symbol library is missing: {SYMBOL_LIBRARY.relative_to(ROOT)}")
        return 0, set()
    library = parse(SYMBOL_LIBRARY.read_text(encoding="utf-8"))
    if node_name(library) != "kicad_symbol_lib":
        fail(errors, "assembled file root is not kicad_symbol_lib")
        return 0, set()
    symbols = direct_children(library, "symbol")
    names: set[str] = set()
    for symbol in symbols:
        name = symbol_name(symbol)
        if name in names:
            fail(errors, f"duplicate assembled symbol name {name!r}")
        names.add(name)
        for field in ("MPN", "Manufacturer", "LCSC", "Footprint"):
            values = property_values(symbol, field)
            if len(values) != 1:
                fail(errors, f"{name}: expected exactly one {field} property, found {len(values)}")
        for field in ("MPN", "Manufacturer", "LCSC"):
            if len(property_values(symbol, field)) != 1:
                continue
            value = property_values(symbol, field)[0]
            if name != "PWR_FLAG" and field != "LCSC" and not value.strip():
                fail(errors, f"{name}: {field} must contain the sourced component identity")
        footprint_values = property_values(symbol, "Footprint")
        if len(footprint_values) != 1 or not footprint_values[0].strip():
            if name != "PWR_FLAG":
                fail(errors, f"{name}: footprint reference must be present")
            continue
        footprint_ref = footprint_values[0]
        if ":" not in footprint_ref:
            fail(errors, f"{name}: footprint reference lacks a library nickname: {footprint_ref!r}")
            continue
        nickname, footprint = footprint_ref.split(":", 1)
        if nickname != LIBRARY:
            fail(errors, f"{name}: footprint must use {LIBRARY}, got {nickname!r}")
        if not (FOOTPRINT_DIR / f"{footprint}.kicad_mod").is_file():
            fail(errors, f"{name}: footprint file does not resolve: {footprint_ref}")
    return len(symbols), names


def check_footprints(errors: list[str]) -> tuple[int, set[str], set[str]]:
    files = sorted(FOOTPRINT_DIR.glob("*.kicad_mod"))
    if not files:
        fail(errors, f"no .kicad_mod files found under {FOOTPRINT_DIR.relative_to(ROOT)}")
    names: set[str] = set()
    outputs = {path.relative_to(ROOT).as_posix() for path in files}
    for path in files:
        name = path.stem
        try:
            text = path.read_text(encoding="utf-8")
            tree = parse(text)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            fail(errors, f"{path.name}: cannot parse footprint: {exc}")
            continue
        internal_name = footprint_root_name(tree)
        if internal_name != name:
            fail(errors, f"{path.name}: internal footprint name is {internal_name!r}")
        names.add(name)
        if rewrite(text) != text:
            fail(errors, f"{path.name}: generated courtyard is stale")
        if name.startswith(("TestPad_", "Fiducial_", "MountingHole")):
            attrs = direct_children(tree, "attr")
            attr_words = {word for attr in attrs for word in attr[1:] if isinstance(word, str)}
            for required in ("exclude_from_pos_files", "exclude_from_bom"):
                if required not in attr_words:
                    fail(errors, f"{path.name}: bare-copper footprint lacks {required}")
        for model in (node for node in walk(tree) if node_name(node) == "model"):
            if len(model) < 2 or not isinstance(model[1], str):
                fail(errors, f"{path.name}: model node has no path")
                continue
            locator = model[1]
            if not locator.startswith(MODEL_PREFIX):
                fail(errors, f"{path.name}: model path is outside the configured project model root: {locator}")
                continue
            model_name = locator[len(MODEL_PREFIX) :]
            if not model_name or "/" in model_name or not (MODEL_DIR / model_name).is_file():
                fail(errors, f"{path.name}: referenced model does not resolve: {locator}")
    model_outputs = {
        path.relative_to(ROOT).as_posix()
        for path in sorted(MODEL_DIR.glob("*"))
        if path.is_file() and path.suffix.lower() in {".step", ".stp", ".wrl"}
    }
    return len(files), names, outputs | model_outputs


def check_receipts(errors: list[str], output_assets: set[str]) -> int:
    receipts = sorted(RECEIPT_DIR.glob("*.receipt.json"))
    if not receipts:
        fail(errors, f"no CAD receipts found under {RECEIPT_DIR.relative_to(ROOT)}")
        return 0
    recorded_outputs: set[str] = set()
    for path in receipts:
        try:
            receipt = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            fail(errors, f"{path.name}: invalid receipt JSON: {exc}")
            continue
        identity = receipt.get("identity", {})
        asset_id = identity.get("asset_id")
        if receipt.get("receipt_version") != 1 or not isinstance(asset_id, str):
            fail(errors, f"{path.name}: invalid receipt version or asset_id")
            continue
        if path.name != f"{asset_id}.receipt.json":
            fail(errors, f"{path.name}: filename does not match asset_id {asset_id!r}")
        acquisition = receipt.get("acquisition", {})
        source_hashes = acquisition.get("sha256", {})
        original_paths = receipt.get("representation", {}).get("original_paths", [])
        if not isinstance(source_hashes, dict) or not source_hashes:
            fail(errors, f"{path.name}: source SHA-256 map is empty")
            source_hashes = {}
        if set(original_paths) != set(source_hashes):
            fail(errors, f"{path.name}: original_paths and source SHA-256 entries differ")
        for source_path, source_hash in source_hashes.items():
            if not valid_sha(source_hash):
                fail(errors, f"{path.name}: invalid or invented source hash for {source_path}")
        derivation = receipt.get("derivation", {})
        if derivation.get("derived") is not True:
            fail(errors, f"{path.name}: imported/normalized CAD output must record its derivation")
        if derivation.get("input_sha256") != source_hashes:
            fail(errors, f"{path.name}: derivation input hashes differ from acquisition hashes")
        output_hashes = derivation.get("output_sha256", {})
        files = receipt.get("representation", {}).get("files", [])
        if not isinstance(output_hashes, dict) or set(files) != set(output_hashes):
            fail(errors, f"{path.name}: represented files and derivation output hashes differ")
            output_hashes = {}
        for output_path, expected in output_hashes.items():
            recorded_outputs.add(output_path)
            target = ROOT / output_path
            if not valid_sha(expected):
                fail(errors, f"{path.name}: invalid output SHA-256 for {output_path}")
            elif not target.is_file() or digest(target) != expected:
                fail(errors, f"{path.name}: output hash is stale for {output_path}")
        fidelity = receipt.get("fidelity", {})
        if fidelity.get("class") not in {"exact-vendor", "family", "derived", "unavailable"}:
            fail(errors, f"{path.name}: invalid fidelity class")
        if not isinstance(fidelity.get("reason"), str) or not fidelity["reason"].strip():
            fail(errors, f"{path.name}: fidelity reason is missing")
    missing = output_assets - recorded_outputs
    if missing:
        fail(errors, "assets without a CAD receipt output hash: " + ", ".join(sorted(missing)))
    return len(receipts)


def main() -> int:
    errors: list[str] = []
    symbol_count, _names = check_symbols(errors)
    footprint_count, _footprint_names, outputs = check_footprints(errors)
    receipt_count = check_receipts(errors, outputs | {path.relative_to(ROOT).as_posix() for path in FRAGMENT_DIR.glob("*.kicad_sym")})
    if errors:
        for error in errors:
            print(f"FAIL: {error}", file=sys.stderr)
        print(f"KiCad library check: FAIL ({len(errors)} issue(s))", file=sys.stderr)
        return 1
    print(f"KiCad library check: PASS ({symbol_count} symbols, {footprint_count} footprints, {receipt_count} receipts)")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except (OSError, ValueError) as exc:
        print(f"check_lib: {exc}", file=sys.stderr)
        raise SystemExit(1)
