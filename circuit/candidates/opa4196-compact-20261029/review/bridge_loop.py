"""OPA4196 magnitude-bridge screen for the UNADOPTED U110/U210 candidate.

Runs TI's OPAx196 macro-model (SBOMAF9, Final 1.5) in the pinned KiCad ngspice oracle.
The TI archive stays in the git-ignored cache and is pinned by the digests that
stage6 already recorded; a different archive fails closed. BAS16GW-QX and
APHHS1005QWF/D have no retained SPICE model or forward-voltage facts, so the
diode and LED parameters below are bracketing ASSUMPTIONS, not part data.
"""
from __future__ import annotations

import argparse
import hashlib
import itertools
import json
import re
import math
import subprocess
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
CACHE = ROOT / ".circuit-cache/sources/architecture278-SBOMAF9"
ARCHIVE = CACHE / "SBOMAF9.zip"
LIBRARY = CACHE / "OPAx196.LIB"
WORK = ROOT / ".circuit-cache/opa4196-bridge-loop"
OUT = HERE / "bridge-loop-result.json"
# Digests recorded in design/architecture-278/implementation/stage6/electrical-report.json.
ZIP_SHA256 = "9c264813a36536f743c166b6a101904b76ed08f049f2eeb127a438cc6e8ccdf5"
LIB_SHA256 = "31142f5dbd71b758d887ee8a411692fc4c1309c8f47100af4ba5bed7e173c430"

# Rail corners: OSC load bands from design/architecture-278/integration/power-contract/README.md
# ("Voltage bands"), plus nominal.
RAILS = {
    "low": (11.53, -11.74),
    "nominal": (12.0, -12.0),
    "high": (12.48, -12.37),
}
R_SENSE = {"min1pct": 5544.0, "nom": 5600.0, "max1pct": 5656.0}
# Assumed bracketing device sets (not manufacturer data).
DROP_SETS = {
    "lowdrop": {"led": "Is=1e-18 N=3 Rs=5", "dio": "Is=2.5e-9 N=1.9 Rs=0.6 TT=4n BV=100"},
    "highdrop": {"led": "Is=1e-22 N=3 Rs=20", "dio": "Is=2e-10 N=1.9 Rs=0.6 TT=4n BV=100"},
}
CJ_DIODE = ("1p", "4p")
CJ_LED = ("5p", "50p")
C_DRIVE = ("0.1p", "20p")
C_SENSE = ("3p", "20p")
# Linear-region operating points only; clipped states (|vin| above the DC clip point) have no closed loop.
OPS = (5.0, 1.0, 0.1, 0.01, 0.001, -0.001, -0.01, -0.1, -1.0, -5.0)


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def model() -> None:
    if not ARCHIVE.exists():
        raise SystemExit(f"NOT RUN: TI archive missing at {ARCHIVE}; fetch https://www.ti.com/lit/zip/SBOMAF9")
    if sha(ARCHIVE) != ZIP_SHA256:
        raise SystemExit("FAIL: TI archive digest differs from the recorded pin; inspect before re-pinning")
    with zipfile.ZipFile(ARCHIVE) as z:
        data = z.read("OPAx196.LIB")
    if hashlib.sha256(data).hexdigest() != LIB_SHA256:
        raise SystemExit("FAIL: OPAx196.LIB digest differs from the recorded pin")
    LIBRARY.write_bytes(data)


def instances():
    for drop, cjd, cjl, cdr, cse in itertools.product(DROP_SETS, CJ_DIODE, CJ_LED, C_DRIVE, C_SENSE):
        yield {"drop": drop, "cj_diode": cjd, "cj_led": cjl, "c_drive": cdr, "c_sense": cse}


def bridge(tag: str, inst: dict, rsense: float, vin_node: str, inj: bool) -> str:
    d = DROP_SETS[inst["drop"]]
    inm = f"inm{tag}" if inj else f"s{tag}"
    lines = [
        f"X{tag} {vin_node} {inm} vcc vee d{tag} OPAx196",
        f"Rs{tag} s{tag} 0 {rsense}",
        f"Cs{tag} s{tag} 0 {inst['c_sense']}",
        f"Cd{tag} d{tag} 0 {inst['c_drive']}",
        f"D1{tag} d{tag} la{tag} DS{tag}",
        f"D2{tag} s{tag} la{tag} DS{tag}",
        f"D3{tag} lk{tag} d{tag} DS{tag}",
        f"D4{tag} lk{tag} s{tag} DS{tag}",
        f"VL{tag} la{tag} lx{tag} DC 0",
        f"DL{tag} lx{tag} lk{tag} DL{tag}",
        f".model DS{tag} D({d['dio']} Cjo={inst['cj_diode']})",
        f".model DL{tag} D({d['led']} Cjo={inst['cj_led']})",
    ]
    if inj:
        lines.append(f"Vinj{tag} inm{tag} s{tag} DC 0 AC 1")
    return "\n".join(lines)


def header(vp: float, vn: float) -> str:
    return "\n".join([
        "* OPA4196 magnitude bridge screen (generated; UNADOPTED candidate)",
        f".include {LIBRARY.relative_to(ROOT).as_posix()}",
        f"Vp vcc 0 DC {vp}",
        f"Vn vee 0 DC {vn}",
    ])


def ac_deck(rail: str, inst: dict, n: int) -> str:
    vp, vn = RAILS[rail]
    body = [header(vp, vn), "Vsig vin 0 DC 0", bridge("_0", inst, R_SENSE["nom"], "vin", True)]
    ctl = [".control", "set wr_singlescale", "set wr_vecnames", "option numdgt=7"]
    for k, vin in enumerate(OPS):
        # destroy first, so a failed operating point leaves no stale plot for wrdata
        ctl += ["destroy all", f"alter Vsig dc = {vin}", "ac dec 40 100 30Meg",
                f"wrdata {WORK.relative_to(ROOT).as_posix()}/ac-{rail}-i{n}-{k}.txt v(s_0) v(inm_0)"]
    ctl += ["quit", ".endc", ".end"]
    return "\n".join(body + ctl) + "\n"


DC_COMBOS = [(drop, rk) for drop in DROP_SETS for rk in R_SENSE]


def dc_deck(rail: str, n: int) -> str:
    vp, vn = RAILS[rail]
    drop, rk = DC_COMBOS[n]
    inst = {"drop": drop, "cj_diode": "1p", "cj_led": "5p", "c_drive": "0.1p", "c_sense": "3p"}
    body = [header(vp, vn), "Vsig vin 0 PWL(0 0 60m 12)", bridge("_0", inst, R_SENSE[rk], "vin", False)]
    w = WORK.relative_to(ROOT).as_posix()
    ctl = [".control", "set wr_singlescale", "set wr_vecnames", "option numdgt=7",
           # quasi-static transient ramps: the macro-model's DC sweep does not converge into clipping
           "destroy all", "alter @Vsig[pwl] = [ 0 0 60m 12 ]", "tran 10u 60m 0 10u",
           f"wrdata {w}/dc-{rail}-i{n}-pos.txt v(vin) v(s_0) v(d_0) i(VL_0)",
           "destroy all", "alter @Vsig[pwl] = [ 0 0 60m -12 ]", "tran 10u 60m 0 10u",
           f"wrdata {w}/dc-{rail}-i{n}-neg.txt v(vin) v(s_0) v(d_0) i(VL_0)",
           "quit", ".endc", ".end"]
    return "\n".join(body + ctl) + "\n"


TRAN_CASES = {
    # Requirement-derived: SLEW_BUFFERED fastest lag is R_MIN 2.2 k x 0.5 uF = 1.1 ms (see report).
    "sine5_100Hz": ("SIN(0 5 100)", "25m", "1u"),
    "sine5_1kHz_stress": ("SIN(0 5 1000)", "3m", "0.2u"),
    "ramp_xing_1ms": ("PWL(0 -1 1m 1)", "1m", "0.2u"),
    "step_negclip_to_p3_1us_stress": ("PWL(0 -10 2m -10 2.001m 3)", "4m", "0.2u"),
    "step_posclip_to_n3_1us_stress": ("PWL(0 10 2m 10 2.001m -3)", "4m", "0.2u"),
    "step_negclip_to_p3_rc1p1ms": ("EXP(-10 3 2m 1.1m 50m 1)", "10m", "1u"),
    "step_posclip_to_n3_rc1p1ms": ("EXP(10 -3 2m 1.1m 50m 1)", "10m", "1u"),
}


def tran_deck(rail: str, case: str, inst: dict, n: int) -> str:
    vp, vn = RAILS[rail]
    src, stop, step = TRAN_CASES[case]
    body = [header(vp, vn), f"Vsig vin 0 {src}", bridge("_0", inst, R_SENSE["nom"], "vin", False)]
    ctl = [".control", "set wr_singlescale", "set wr_vecnames", "option numdgt=7", "destroy all",
           f"tran {step} {stop} 0 {step}",
           f"wrdata {WORK.relative_to(ROOT).as_posix()}/tran-{rail}-{case}-i{n}.txt v(vin) v(s_0) v(d_0) i(VL_0)",
           "quit", ".endc", ".end"]
    return "\n".join(body + ctl) + "\n"


def ngspice(deck: Path) -> dict:
    proc = subprocess.run(
        ["bash", "scripts/kicad/run.sh", "ngspice", "-b", deck.relative_to(ROOT).as_posix()],
        cwd=ROOT, capture_output=True, text=True, timeout=900,
    )
    log = deck.with_suffix(".log")
    log.write_text(proc.stdout + "\n--- stderr ---\n" + proc.stderr)
    ver = sorted(set(re.findall(r"ngspice-[0-9][0-9.]*", proc.stdout + proc.stderr)))
    return {"ngspice": ver, "deck": deck.relative_to(ROOT).as_posix(), "deck_sha256": sha(deck), "exit": proc.returncode,
            "log_sha256": sha(log), "errors": [l for l in (proc.stdout + proc.stderr).splitlines()
                                              if "rror" in l][:10]}


def read(path: Path):
    rows = path.read_text().split("\n")
    head = rows[0].split()
    data = [list(map(float, r.split())) for r in rows[1:] if r.strip()]
    return head, data


def loop_metrics(data):
    f = [r[0] for r in data]
    t = [-(complex(r[1], r[2]) / complex(r[3], r[4])) for r in data]
    mag = [20 * math.log10(abs(x)) for x in t]
    ph, prev = [], None
    for x in t:
        a = math.degrees(math.atan2(x.imag, x.real))
        if prev is not None:
            while a - prev > 180:
                a -= 360
            while a - prev < -180:
                a += 360
        ph.append(a)
        prev = a
    fc = pm = None
    for j in range(1, len(f)):
        if mag[j - 1] >= 0 > mag[j]:
            w = mag[j - 1] / (mag[j - 1] - mag[j])
            fc = f[j - 1] * (f[j] / f[j - 1]) ** w
            pm = 180 + ph[j - 1] + w * (ph[j] - ph[j - 1])
            break
    return round(mag[0], 2), (None if fc is None else round(fc, 1)), (None if pm is None else round(pm, 1))


def analyse_ac(rail: str, inst: dict, n: int) -> list[dict]:
    out = []
    for k, vin in enumerate(OPS):
        path = WORK / f"ac-{rail}-i{n}-{k}.txt"
        if not path.exists():
            out.append({"rail": rail, "vin": vin, **inst, "status": "AC OPERATING POINT NOT CONVERGED"})
            continue
        _, data = read(path)
        g, fc, pm = loop_metrics(data)
        out.append({"rail": rail, "vin": vin, **inst, "loop_gain_db_at_100Hz": g, "crossover_hz": fc,
                    "phase_margin_deg": pm})
    return out


def analyse_dc(rail: str, n: int) -> dict:
    drop, rk = DC_COMBOS[n]
    rec = {"rail": rail, "drop": drop, "r_sense": rk}
    for side, sign in (("pos", 1), ("neg", -1)):
        path = WORK / f"dc-{rail}-i{n}-{side}.txt"
        if not path.exists():
            rec[f"{side}_status"] = "DC SWEEP NOT CONVERGED"
            continue
        _, raw = read(path)
        data = [r[1:] for r in raw]
        def at(v):
            return min(data, key=lambda r: abs(r[0] - v))
        clip = None
        for r in data:
            if abs(r[0]) > 0.05 and abs(r[1] - r[0]) > 0.01 * abs(r[0]):
                clip = r[0]
                break
        r5 = at(5.0 * sign)
        r12 = at(12.0 * sign)
        rec[f"{side}_sense_err_mV_at_5V"] = round((r5[1] - r5[0]) * 1e3, 3)
        rec[f"{side}_drive_V_at_5V"] = round(r5[2], 3)
        rec[f"{side}_led_mA_at_5V"] = round(abs(r5[3]) * 1e3, 4)
        rail_v = RAILS[rail][0] if sign > 0 else RAILS[rail][1]
        rec[f"{side}_headroom_to_rail_V_at_5V"] = round(abs(rail_v - r5[2]), 3)
        rec[f"{side}_first_1pct_error_vin_V"] = clip
        rec[f"{side}_led_mA_at_12V"] = round(abs(r12[3]) * 1e3, 4)
        rec[f"{side}_max_led_mA"] = round(max(abs(r[3]) for r in data) * 1e3, 4)
    return rec


def analyse_tran(rail: str, case: str, inst: dict, n: int) -> dict:
    rec = {"rail": rail, "case": case, **inst}
    path = WORK / f"tran-{rail}-{case}-i{n}.txt"
    if not path.exists():
        rec["status"] = "TRANSIENT NOT CONVERGED"
        return rec
    _, data = read(path)
    t = [r[0] for r in data]
    vin = [r[1] for r in data]
    s = [r[2] for r in data]
    il = [r[4] for r in data]
    if case.startswith("step"):
        t0 = 2e-3
        target = 3.0 if "to_p3" in case else -3.0
        # last instant with tracking error above 1 % of 3 V, ignoring the |vin| < 0.1 V zero-crossing window
        last = None
        for j in range(len(t)):
            if t[j] > t0 and abs(vin[j]) > 0.1 and abs(s[j] - vin[j]) > 0.03:
                last = t[j]
        post = [s[j] * (1 if target > 0 else -1) for j in range(len(t)) if t[j] > t0]
        rec["last_error_gt_30mV_after_step_us"] = None if last is None else round((last - t0) * 1e6, 2)
        zc = next((t[j] for j in range(1, len(t)) if t[j] > t0 and (vin[j - 1] < 0) != (vin[j] < 0)), None)
        rec["source_zero_crossing_after_step_us"] = None if zc is None else round((zc - t0) * 1e6, 2)
        rec["overshoot_pct_of_3V"] = round(max(0.0, (max(post) - 3.0) / 3.0 * 100), 3)
        pre = [abs(s[j] - vin[j]) for j in range(len(t)) if 1e-3 < t[j] < t0]
        rec["pre_step_clip_error_V"] = round(max(pre), 3) if pre else None
    else:
        dark, worst, band = 0.0, 0.0, 0.0
        for j in range(1, len(t)):
            ideal = abs(vin[j]) / 5600
            if abs(vin[j]) > 0.02 and abs(il[j]) < 0.5 * ideal:
                dark += t[j] - t[j - 1]
                band = max(band, abs(vin[j]))
            if abs(vin[j]) > 0.5:
                worst = max(worst, abs(abs(s[j]) - abs(vin[j])))
        crossings = sum(1 for j in range(1, len(t)) if (vin[j - 1] < 0) != (vin[j] < 0))
        rec["zero_crossings"] = crossings
        rec["dark_time_per_crossing_us"] = round(dark / max(crossings, 1) * 1e6, 3)
        rec["dark_max_abs_vin_mV"] = round(band * 1e3, 2)
        rec["worst_abs_sense_error_mV_abs_vin_gt_0p5V"] = round(worst * 1e3, 3)
        rec["peak_led_mA"] = round(max(abs(x) for x in il) * 1e3, 4)
    return rec


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.parse_args()
    model()
    WORK.mkdir(parents=True, exist_ok=True)
    init = ROOT / ".spiceinit"
    if init.exists():
        raise SystemExit("refusing to replace an existing .spiceinit")
    init.write_text("set ngbehavior=ps\n")
    insts = list(instances())
    tran_insts = [x for x in insts if x["c_sense"] == "20p" and x["c_drive"] == "20p" and x["cj_diode"] == "4p"]
    runs, ac, dc, tran = [], [], [], []
    try:
        for rail in RAILS:
            for n, inst in enumerate(insts):
                deck = WORK / f"ac-{rail}-i{n}.cir"
                deck.write_text(ac_deck(rail, inst, n))
                runs.append(ngspice(deck))
                ac += analyse_ac(rail, inst, n)
            for n in range(len(DC_COMBOS)):
                deck = WORK / f"dc-{rail}-i{n}.cir"
                deck.write_text(dc_deck(rail, n))
                runs.append(ngspice(deck))
                dc.append(analyse_dc(rail, n))
        for rail in ("low", "high"):
            for case in TRAN_CASES:
                for n, inst in enumerate(tran_insts):
                    deck = WORK / f"tran-{rail}-{case}-i{n}.cir"
                    deck.write_text(tran_deck(rail, case, inst, n))
                    runs.append(ngspice(deck))
                    tran.append(analyse_tran(rail, case, inst, n))
    finally:
        init.unlink()
    valid_pm = [r for r in ac if r.get("phase_margin_deg") is not None]
    worst = min(valid_pm, key=lambda r: r["phase_margin_deg"]) if valid_pm else None
    result = {
        "status": "MODEL SCREEN ONLY; UNADOPTED candidate; not hardware or stability qualification",
        "model": {"archive": "SBOMAF9", "archive_sha256": ZIP_SHA256, "library_sha256": LIB_SHA256,
                  "version": "Final 1.5, 29AUG2022", "temperature": "27 C model default only"},
        "assumptions": {"rails_V": RAILS, "r_sense_ohm": R_SENSE, "drop_sets": DROP_SETS,
                        "cj_diode": CJ_DIODE, "cj_led": CJ_LED, "c_drive": C_DRIVE, "c_sense": C_SENSE,
                        "note": "Diode/LED parameters and parasitic capacitances are assumed brackets; no BAS16GW-QX or APHHS1005QWF/D model or VF fact is retained."},
        "oracle": {"wrapper": "scripts/kicad/run.sh", "image": "kicad/kicad@sha256:18693567392b80da435f9fa952ce3a3e534c66eb5a6033f5b9c80aa3b19dd3ec",
                   "ngspice": sorted({v for r in runs for v in r["ngspice"]}), "compat": "ngbehavior=ps"},
        "runs": runs,
        "summary": {
            "ac_cases": len(ac), "ac_cases_with_crossover": len(valid_pm),
            "worst_phase_margin": worst,
            "min_loop_gain_db_at_100Hz_by_vin": {str(v): min((r["loop_gain_db_at_100Hz"] for r in ac if r["vin"] == v and "loop_gain_db_at_100Hz" in r), default=None) for v in OPS},
            "not_converged": sum(1 for r in ac if "status" in r),
        },
        "ac": ac, "dc": dc, "tran": tran,
    }
    OUT.write_text(json.dumps(result, indent=1) + "\n")
    bad = [r for r in runs if r["exit"] != 0]
    print(f"runs={len(runs)} nonzero_exit={len(bad)} worst_pm={worst and worst['phase_margin_deg']}")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main())
