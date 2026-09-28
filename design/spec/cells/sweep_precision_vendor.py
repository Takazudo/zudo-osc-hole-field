"""OPA4197-family PSpice sweep in the pinned KiCad/ngspice oracle.

TI's copyrighted library stays in the ignored local cache. Its downloaded ZIP and
extracted library are pinned by digest, so a changed remote file fails closed.
"""
from __future__ import annotations

import hashlib
import json
import re
import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

from ._builder import ROOT, CELLS

URL = "https://www.ti.com/lit/zip/sboma34"
ZIP_SHA256 = "9e55fcaa23d54cee025dda3fa9872b11c41c531f82e0802c2b93d51e943666e5"
LIB_SHA256 = "fc5b020e63346e511bd808bf41c856b0150b000bcf8a41fe00eeececb1f422a5"
CACHE = ROOT / ".circuit-cache/sources/opa197-model"
ARCHIVE = CACHE / "SBOMA34D.ZIP"
LIBRARY = CACHE / "OPAx197.LIB"
DECK = CACHE / "precision-vendor-case.cir"
OUT = ROOT / "design/reports/spice/precision-output-vendor.json"
LOADS = {"open": "1e12", "100k": "100k", "10k": "10k"}
CAPS = {"0": None, "100p": "100p", "1n": "1n", "5n": "5n"}
METRICS = ("pmax", "nmin", "pset", "nset", "platmax", "platmin", "nlatmax", "nlatmin",
           "p2max", "n2min", "p2set", "n2set", "p2latmax", "p2latmin", "n2latmax", "n2latmin")


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def model(*, offline: bool = False) -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    if not ARCHIVE.exists():
        if offline:
            raise RuntimeError(f"TI model missing: {ARCHIVE}; rerun without --offline to fetch pinned {URL}")
        with urllib.request.urlopen(URL, timeout=30) as response:
            downloaded = response.read()
        if digest(downloaded) != ZIP_SHA256:
            raise RuntimeError("TI model ZIP hash changed; inspect the new bytes before updating the pin")
        ARCHIVE.write_bytes(downloaded)
    archive = ARCHIVE.read_bytes()
    if digest(archive) != ZIP_SHA256:
        raise RuntimeError("cached TI model ZIP hash mismatch")
    with zipfile.ZipFile(ARCHIVE) as bundle:
        library = bundle.read("OPAx197.LIB")
    if digest(library) != LIB_SHA256:
        raise RuntimeError("TI model library hash mismatch")
    if LIBRARY.exists() and LIBRARY.read_bytes() != library:
        raise RuntimeError("cached TI model library differs from pinned archive")
    LIBRARY.write_bytes(library)


def values(*, original: bool = False) -> tuple[int, float]:
    cell = CELLS["precision_output"]
    by_ref = {part["ref"]: part for part in cell["parts"]}
    if original:
        return 10000, 1e-10
    assert by_ref["R_ISO_A"]["value"] == by_ref["R_ISO_B"]["value"] == 499
    assert by_ref["R_ISO_A"]["terminals"] == {"1": "DRIVE", "2": "ISO_MID"}
    assert by_ref["R_ISO_B"]["terminals"] == {"1": "ISO_MID", "2": "JACK"}
    assert by_ref["A"]["terminals"]["IN-"] == "FB"
    assert by_ref["R_FB"]["terminals"] == {"1": "JACK", "2": "FB"}
    assert by_ref["C_FAST"]["terminals"] == {"1": "DRIVE", "2": "FB"}
    return by_ref["R_FB"]["value"], by_ref["C_FAST"]["value"]


def deck(load: str, cap: str | None, *, original: bool = False) -> str:
    feedback, compensation = values(original=original)
    lines = [
        "OPA4197 TI OPAx197 PSpice model; fixed OSC-ES-1 output cell",
        ".param TEMP=27",
        ".include .circuit-cache/sources/opa197-model/OPAx197.LIB",
        "Vplus vp 0 12", "Vminus vn 0 -12",
        "Vsig sig 0 PULSE(-5 5 0 1u 1u 500u 1m)",
        "Xamp sig fb vp vn drive OPAx197",
        "Risoa drive mid 499", "Risob mid jack 499",
        f"Rfb jack fb {feedback:g}", f"Cfast drive fb {compensation:g}",
        f"Rload jack 0 {load}",
    ]
    if cap:
        lines.append(f"Cload jack 0 {cap}")
    lines += [
        ".control", "set noinit", "tran 1u 2m",
        "meas tran pmax MAX v(jack) FROM=0 TO=450u",
        "meas tran nmin MIN v(jack) FROM=500u TO=950u",
        "meas tran pset FIND v(jack) AT=400u",
        "meas tran nset FIND v(jack) AT=900u",
        "meas tran platmax MAX v(jack) FROM=300u TO=450u",
        "meas tran platmin MIN v(jack) FROM=300u TO=450u",
        "meas tran nlatmax MAX v(jack) FROM=800u TO=950u",
        "meas tran nlatmin MIN v(jack) FROM=800u TO=950u",
        "meas tran p2max MAX v(jack) FROM=1m TO=1.45m",
        "meas tran n2min MIN v(jack) FROM=1.5m TO=1.95m",
        "meas tran p2set FIND v(jack) AT=1.4m",
        "meas tran n2set FIND v(jack) AT=1.9m",
        "meas tran p2latmax MAX v(jack) FROM=1.3m TO=1.45m",
        "meas tran p2latmin MIN v(jack) FROM=1.3m TO=1.45m",
        "meas tran n2latmax MAX v(jack) FROM=1.8m TO=1.95m",
        "meas tran n2latmin MIN v(jack) FROM=1.8m TO=1.95m",
        "quit", ".endc", ".end", "",
    ]
    return "\n".join(lines)


def measure(output: str) -> dict[str, float]:
    found = {name: float(number) for name, number in re.findall(
        r"(?m)^\s*([a-z0-9]+)\s*=\s*([+-]?\d+(?:\.\d+)?(?:e[+-]?\d+)?)", output, re.I
    ) if name in METRICS}
    missing = set(METRICS) - found.keys()
    if missing:
        raise RuntimeError(f"ngspice measurements missing: {sorted(missing)}")
    return found


def verdict(row: dict) -> list[str]:
    failures = []
    if row["overshoot_percent"] > 10:
        failures.append("overshoot > 10%")
    if row["positive_error_mV"] > 1 or row["negative_error_mV"] > 1:
        failures.append("settling error > 1 mV by 0.4 ms after each step")
    if row["positive_late_ripple_mV"] > 1 or row["negative_late_ripple_mV"] > 1:
        failures.append("late ripple > 1 mV peak-to-peak")
    return failures


def run(*, check: bool = False, offline: bool = False, fixture_original: bool = False) -> None:
    model(offline=offline)
    init = ROOT / ".spiceinit"
    if init.exists():
        raise RuntimeError("refusing to replace an existing .spiceinit")
    init.write_text("set ngbehavior=ps\n")
    rows = []
    try:
        cases = [("open", "5n")] if fixture_original else [
            (load, cap) for load in LOADS for cap in CAPS
        ]
        for load, cap in cases:
            DECK.write_text(deck(LOADS[load], CAPS[cap], original=fixture_original))
            proc = subprocess.run(
                ["bash", "scripts/kicad/run.sh", "ngspice", "-b", DECK.relative_to(ROOT).as_posix()],
                cwd=ROOT, capture_output=True, text=True, timeout=120,
            )
            if proc.returncode:
                raise RuntimeError(f"pinned ngspice failed for {load}/{cap}: {proc.stderr[-1200:]}")
            v = measure(proc.stdout)
            row = {
                "load": load, "cable_capacitance": cap,
                "positive_peak_V": max(v["pmax"], v["p2max"]),
                "negative_peak_V": min(v["nmin"], v["n2min"]),
                "positive_settled_V": v["p2set"], "negative_settled_V": v["n2set"],
                "overshoot_percent": max(0, (max(v["pmax"], v["p2max"]) - 5) / 10,
                                         (-5 - min(v["nmin"], v["n2min"])) / 10) * 100,
                "positive_error_mV": max(abs(v["pset"] - 5), abs(v["p2set"] - 5)) * 1000,
                "negative_error_mV": max(abs(v["nset"] + 5), abs(v["n2set"] + 5)) * 1000,
                "positive_late_ripple_mV": max(v["platmax"] - v["platmin"],
                                                v["p2latmax"] - v["p2latmin"]) * 1000,
                "negative_late_ripple_mV": max(v["nlatmax"] - v["nlatmin"],
                                                v["n2latmax"] - v["n2latmin"]) * 1000,
            }
            row["failures"] = verdict(row)
            row["status"] = "FAIL" if row["failures"] else "PASS - TI MODEL ONLY"
            for key in ("overshoot_percent", "positive_error_mV", "negative_error_mV",
                        "positive_late_ripple_mV", "negative_late_ripple_mV"):
                row[key] = round(row[key], 4)
            rows.append(row)
    finally:
        init.unlink()
        DECK.unlink(missing_ok=True)
    failures = sum(bool(row["failures"]) for row in rows)
    if not fixture_original:
        feedback, compensation = values()
        report = {
            "schema_version": 1,
            "status": "FAIL - TI MODEL TARGET" if failures else "PASS - TI MODEL ONLY; NOT HARDWARE QUALIFICATION",
            "model": "TI OPAx197 Final 1.3 (23JUN2022), generic single core explicitly applicable to OPA4197; PSpice compatibility in KiCad 10.0.6 ngspice-44.2",
            "model_url": URL, "model_zip_sha256": ZIP_SHA256, "model_lib_sha256": LIB_SHA256,
            "network": {"output_isolation_ohm": [499, 499], "jack_feedback_ohm": feedback, "local_feedback_F": compensation},
            "conditions": "+/-12 V rails, +/-5 V steps over two cycles, open/100k/10k loads, 0/100p/1n/5n cable capacitance; one model core per case at 27 C",
            "target": "at most 10% overshoot, within 1 mV by 1 ms, no sustained oscillation",
            "model_limit": "TI macro-model predicts modeled behavior only; package parasitics, tolerance, cable inductance, PCB layout, thermal behavior and bench stability remain NOT RUN.",
            "pass_count": len(rows) - failures, "fail_count": failures, "cases": rows,
        }
        body = json.dumps(report, indent=2) + "\n"
        if check:
            if OUT.read_text() != body:
                raise RuntimeError("precision vendor report drift")
        else:
            OUT.write_text(body)
    print(f"Precision TI-model sweep: {len(rows) - failures}/{len(rows)} pass; {failures} fail")
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    run(check="--check" in sys.argv, offline="--offline" in sys.argv,
        fixture_original="--fixture-original" in sys.argv)
