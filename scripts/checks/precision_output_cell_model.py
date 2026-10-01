"""Powered-on diagnostic of candidate connectivity using the pinned TI core.

The PhotoMOS devices are static lumped contact R/C, not manufacturer models.
This does not model LED permit, switching skew, isolation faults or thermal limits.
Run through heavy-guard because it invokes the pinned native KiCad oracle.
"""
from pathlib import Path
import argparse
import json
import re
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from design.spec.cells.sweep_precision_vendor import model, measure, LOADS, CAPS, LIBRARY, LIB_SHA256, ZIP_SHA256
from scripts.checks.precision_output_cell import SPEC, SOURCES, validate, digest

OUT = ROOT / "design/power/precision-output-cell-model.json"


def deck(spec: dict, load: str, cable: str | None, contact: float, compensation: float) -> str:
    p = {x["ref"]: x for x in spec["parts"]}
    lines = ["Candidate PhotoMOS precision cell: powered-on static R/C diagnostic",
             ".param TEMP=27", ".include OPAx197.LIB",
             "Vplus VP 0 12", "Vminus VN 0 -12", "Vsig SIGNAL 0 PULSE(-5 5 0 1u 1u 1.5m 3m)"]
    # Every analog component edge is emitted from the candidate's pin map.
    for ref, part in p.items():
        pin = part["pins"]
        net = lambda k: "0" if pin[k] == "GND" else pin[k]
        if ref == "U1":
            lines.append(f"Xamp {net('3')} {net('2')} {net('4')} {net('11')} {net('1')} OPAx197")
        elif ref.startswith("K_"):
            lines += [f"R{ref} {net('3')} {net('4')} {contact}",
                      f"C{ref} {net('3')} {net('4')} {spec['conditions']['relay_contact_cap_sensitivity_F']}"]
        else:
            value = compensation if ref == "C_LOCAL" else part["value"]
            lines.append(f"{ref} {net('1')} {net('2')} {value}")
    lines.append(f"Rload JACK 0 {load}")
    if cable:
        lines.append(f"Cload JACK 0 {cable}")
    lines += [".control", "set noinit", "tran 1u 6m"]
    for prefix, start in [("p", 0), ("n", 1.5e-3), ("p2", 3e-3), ("n2", 4.5e-3)]:
        positive = prefix.startswith("p")
        lines += [f"meas tran {prefix}{'max' if positive else 'min'} {'MAX' if positive else 'MIN'} v(JACK) FROM={start} TO={start + 1.45e-3}",
                  f"meas tran {prefix}set FIND v(JACK) AT={start + 400e-6}",
                  f"meas tran {prefix}latmax MAX v(JACK) FROM={start + 300e-6} TO={start + 450e-6}",
                  f"meas tran {prefix}latmin MIN v(JACK) FROM={start + 300e-6} TO={start + 450e-6}",
                  f"meas tran {prefix}deadline FIND v(JACK) AT={start + spec['limits_preserved']['settling_deadline_s']}",
                  f"meas tran {prefix}deadlinehi MAX v(JACK) FROM={start + 1e-3} TO={start + 1.45e-3}",
                  f"meas tran {prefix}deadlinelo MIN v(JACK) FROM={start + 1e-3} TO={start + 1.45e-3}"]
    return "\n".join(lines + ["quit", ".endc", ".end", ""])


def run(check: bool = False) -> None:
    spec = json.loads(SPEC.read_text())
    validate(spec, json.loads(SOURCES.read_text()))
    model(offline=True)
    cache = ROOT / ".circuit-cache/sources/precision-output-cell"
    cache.mkdir(parents=True, exist_ok=True)
    rows = []
    with TemporaryDirectory(prefix="diagnostic-", dir=cache) as directory:
        workdir = Path(directory)
        (workdir / ".spiceinit").write_text("set ngbehavior=ps\n")
        shutil.copyfile(LIBRARY, workdir / "OPAx197.LIB")
        for label, contact, cap in [("25C_table_Ron_Cminus5pct", spec["conditions"]["relay_on_ohm_at_25C"], 9.5e-9),
                                    ("sensitivity_Ron_0p5_Cplus5pct", 0.5, 10.5e-9)]:
            for load in LOADS:
                for cable in CAPS:
                    path = workdir / "candidate-model.cir"
                    path.write_text(deck(spec, LOADS[load], CAPS[cable], contact, cap))
                    proc = subprocess.run(["bash", "scripts/kicad/run.sh", "python3", "-c", "import os,sys; os.chdir(sys.argv[1]); os.execvp('ngspice', ['ngspice', '-b', 'candidate-model.cir'])", str(workdir.relative_to(ROOT))], cwd=ROOT, capture_output=True, text=True, timeout=120)
                    if proc.returncode:
                        raise RuntimeError(proc.stdout + proc.stderr)
                    v = measure(proc.stdout)
                    late = {name: float(value) for name, value in re.findall(r"(?m)^\s*([a-z0-9]+deadline(?:hi|lo)?)\s*=\s*([+-]?[\d.]+(?:e[+-]?\d+)?)", proc.stdout, re.I)}
                    expected = {prefix + suffix for prefix in ("p", "n", "p2", "n2") for suffix in ("deadline", "deadlinehi", "deadlinelo")}
                    if set(late) != expected:
                        raise RuntimeError("Missing original-deadline measurements")
                    overshoot = max(0, max(v["pmax"], v["p2max"]) - 5, -5 - min(v["nmin"], v["n2min"])) / 10 * 100
                    error = max(abs(v[k] - (5 if k.startswith("p") else -5)) for k in ("pset", "p2set", "nset", "n2set")) * 1000
                    ripple = max(v[a] - v[b] for a, b in [("platmax", "platmin"), ("p2latmax", "p2latmin"), ("nlatmax", "nlatmin"), ("n2latmax", "n2latmin")]) * 1000
                    deadline_error = max(abs(late[p + "deadline"] - (5 if p.startswith("p") else -5)) for p in ("p", "n", "p2", "n2")) * 1000
                    deadline_ripple = max(late[p + "deadlinehi"] - late[p + "deadlinelo"] for p in ("p", "n", "p2", "n2")) * 1000
                    rows.append({"corner": label, "load": load, "cable_capacitance": cable, "overshoot_percent": round(overshoot, 6), "settling_error_mV_at_400us": round(error, 6), "ripple_mVpp_at_300_to_450us": round(ripple, 6), "stricter_400us_diagnostic_met": overshoot <= 10 and error <= 1 and ripple <= 1, "settling_error_mV_at_original_1ms_deadline": round(deadline_error, 6), "ripple_mVpp_after_original_deadline": round(deadline_ripple, 6), "diagnostic_targets_met": overshoot <= spec["limits_preserved"]["overshoot_percent"] and deadline_error <= spec["limits_preserved"]["settling_error_mV"] and deadline_ripple <= 1})
    report = {"status": "DIAGNOSTIC ONLY; hardware protection OPEN", "input_sha256": {str(p.relative_to(ROOT)): digest(p) for p in (SPEC, SOURCES, Path(__file__).resolve())}, "oracle": "KiCad 10.0.6 / pinned ngspice via scripts/kicad/run.sh", "TI_model_zip_sha256": ZIP_SHA256, "TI_model_lib_sha256": LIB_SHA256, "conditions": "+/-12 V, +/-5 V pulse (1.5 ms plateaus, 3 ms period, two cycles), one active core at 27 C; 0.12 ohm/9.5 nF and 0.5 ohm/10.5 nF sensitivity pairs, 200 pF ACROSS each closed contact. Not a complete tolerance/temperature sweep.", "deadline_note": "Original 1 ms deadline measured directly. Earlier 400 us error/ripple retained as stricter diagnostics; their failures are not erased or relabeled as passes.", "excluded": "Real relay switching and capacitance, LED driver, charge injection, off leakage, rail/GND faults, spare-core package heat and PCB parasitics; no hardware qualification", "cases": rows}
    body = json.dumps(report, indent=2) + "\n"
    if check:
        if OUT.read_text() != body:
            raise RuntimeError("Candidate model report drift")
    else:
        OUT.write_text(body)
    failed = sum(not r["diagnostic_targets_met"] for r in rows)
    print(f"DIAGNOSTIC: {len(rows)-failed}/{len(rows)} targets met; protection gate remains OPEN")
    if failed:
        raise SystemExit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    run(parser.parse_args().check)
