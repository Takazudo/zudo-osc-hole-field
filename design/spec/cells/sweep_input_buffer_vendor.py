"""MC04 stage 4: input-buffer stages with the TI OPAx196 and OPAx197 PSpice models.

Compares OPA4196 (current, SOIC-14) and OPA4197 (TSSOP-14 candidate OPA4197IPWR; the model is
die-level and does not see the package) in the six input-buffer ICs U1216, U1416, U1518, U4346,
U8314 and U8417, in the pinned KiCad 10 ngspice oracle. Both TI libraries stay in the ignored
local cache and are pinned by digest; a changed remote file fails closed.

Cases follow circuit/orchestration/campaigns/osc-stack-20261114/
mc04-s4-input-buffer-native-brief-20261121.md (commit 4b0ccee). The 10 % overshoot and 1 mV
settling numbers of sweep_precision.py are DIAGNOSTIC labels only; this report sets no acceptance.
"""
from __future__ import annotations

import bisect
import cmath
import hashlib
import json
import math
import subprocess
import sys
import urllib.request
import zipfile

from design.spec.modules.spice_trace import check_oracle_result
from ._builder import ROOT
from . import sweep_precision_vendor as opa197

OPA196_URL = "https://www.ti.com/lit/zip/sbomaf9"
OPA196_ZIP_SHA256 = "9c264813a36536f743c166b6a101904b76ed08f049f2eeb127a438cc6e8ccdf5"
OPA196_LIB_SHA256 = "31142f5dbd71b758d887ee8a411692fc4c1309c8f47100af4ba5bed7e173c430"
OPA196_CACHE = ROOT / ".circuit-cache/sources/opa196-model"
OPA196_ARCHIVE = OPA196_CACHE / "SBOMAF9E.ZIP"
OPA196_LIBRARY = OPA196_CACHE / "OPAx196.LIB"
OPA196_RETAINED = "Takazudo/circuit-dev-resources texas-instruments/opa4196/opa4196-pspice-model-sbomaf9e.zip"
WORK = ROOT / ".circuit-cache/sources/input-buffer-vendor"
OUT = ROOT / "design/reports/spice/input-buffer-vendor.json"
BRIEF = "circuit/orchestration/campaigns/osc-stack-20261114/mc04-s4-input-buffer-native-brief-20261121.md"

MODELS = {
    "OPA4196": {"subckt": "OPAx196", "lib": ".circuit-cache/sources/opa196-model/OPAx196.LIB"},
    "OPA4197": {"subckt": "OPAx197", "lib": ".circuit-cache/sources/opa197-model/OPAx197.LIB"},
}

# Generic diode models: no vendor SPICE model is retained for these parts. Every one is ASSUMED,
# with a stated nonzero junction capacitance (CJO) and transit time (TT).
DIODES = {
    "DSCH": ("BAT54S,215 clamp / D_BOOT", "IS=2e-7 N=1.04 RS=1.5 CJO=10p VJ=0.35 M=0.33 TT=5n BV=30 IBV=1e-6"),
    "DLL": ("BAV199,215 low-leakage clamp", "IS=8e-14 N=1.5 RS=1 CJO=2p VJ=0.7 M=0.33 TT=3u BV=85 IBV=1e-9"),
    "DBAS": ("BAS16GW-QX bridge diode", "IS=2.52n N=1.752 RS=0.568 CJO=1.5p VJ=0.7 M=0.33 TT=4n BV=100 IBV=1e-6"),
    "DLED": ("APHHS1005QWF/D white LED", "IS=5.9e-20 N=3 RS=10 CJO=20p VJ=2.5 M=0.3 TT=10n BV=5 IBV=1e-5"),
}
R_ON = 15  # TMUX7412F R_ON bound, fact-fault-switch-t-ron-12v-single; fixed resistor ASSUMED

INSTANCES = {
    "U1216": {"board": "JL", "module": "O2 oscillator", "units": "1-3 high_impedance_input (base), 4 general_output"},
    "U1416": {"board": "JL", "module": "O4 oscillator", "units": "1-3 high_impedance_input (base), 4 general_output"},
    "U1518": {"board": "JL", "module": "O5 oscillator 1V/oct", "units": "1 high_impedance_input variant precision (BAV199 clamp + BAT54S D_BOOT); 2-4 idle"},
    "U4346": {"board": "JR", "module": "E3 envelope", "units": "1-3 high_impedance_input (base), 4 general_output"},
    "U8314": {"board": "JR", "module": "M4A mix4_vca", "units": "1-4 high_impedance_input (base)"},
    "U8417": {"board": "JR", "module": "M4B mix4_vca", "units": "1 high_impedance_input (base), 2 general_output, 3-4 magnitude_indicator"},
}
CELL_USERS = {
    "follower_base": ["U1216", "U1416", "U4346", "U8314", "U8417"],
    "follower_precision": ["U1518"],
    "general_output": ["U1216", "U1416", "U4346", "U8417"],
    "magnitude_indicator": ["U8417"],
}

C_RUN = ("10p", "30p", "50p")
OUT_LOADS = {"open": "1e12", "100k": "100k", "10k": "10k"}
OUT_CABLES = {"0": None, "100p": "100p", "1n": "1n"}
IND_CAPS = {"0": None, "7.2p": "7.2p", "15p": "15p", "30p": "30p"}
IND_BIAS = {"1uA": 1e-6, "10uA": 1e-5, "100uA": 1e-4, "1mA": 1e-3}
IND_AMPS = {"10mV": 0.01, "100mV": 0.1, "1V": 1.0, "5V": 5.0}
R_SENSE = 5600
PAPER = {"no_cable_worst_deg": 82, "7.2p_worst_deg": 69, "29p_worst_deg": 40}

STEP = "PULSE(-5 5 0 1u 1u 500u 1m)"
SINE = "SIN(0 10 20k)"
OVER = "PWL(0 0 10u 0 11u 12 211u 12 212u 0 511u 0 512u -12 712u -12 713u 0 1.1m 0)"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def opa196_model(*, offline: bool = False) -> None:
    OPA196_CACHE.mkdir(parents=True, exist_ok=True)
    if not OPA196_ARCHIVE.exists():
        if offline:
            raise RuntimeError(f"TI OPA196 model missing: {OPA196_ARCHIVE}; rerun without --offline to fetch {OPA196_URL}")
        with urllib.request.urlopen(OPA196_URL, timeout=30) as response:
            downloaded = response.read()
        if digest(downloaded) != OPA196_ZIP_SHA256:
            raise RuntimeError("TI OPA196 model ZIP hash changed; inspect the new bytes before updating the pin")
        OPA196_ARCHIVE.write_bytes(downloaded)
    if digest(OPA196_ARCHIVE.read_bytes()) != OPA196_ZIP_SHA256:
        raise RuntimeError("cached TI OPA196 model ZIP hash mismatch")
    with zipfile.ZipFile(OPA196_ARCHIVE) as bundle:
        library = bundle.read("OPAx196.LIB")
    if digest(library) != OPA196_LIB_SHA256:
        raise RuntimeError("TI OPA196 model library hash mismatch")
    if OPA196_LIBRARY.exists() and OPA196_LIBRARY.read_bytes() != library:
        raise RuntimeError("cached TI OPA196 model library differs from pinned archive")
    OPA196_LIBRARY.write_bytes(library)


def models(*, offline: bool = False) -> None:
    opa197.model(offline=offline)
    opa196_model(offline=offline)


# ----------------------------------------------------------------------------------------------
# Netlist fragments


def follower(tag, sub, wave, *, source="1k", variant="base", c_sense=None, c_buffer=None):
    """J -> R_ON (switch) -> PROTECTED (100k R_PD) -> 10k R_LIMIT -> SENSE (clamp, IN+) -> follower."""
    j, p, s, b = f"j{tag}", f"p{tag}", f"s{tag}", f"b{tag}"
    lines = []
    if source is not None:
        lines += [f"Vs{tag} src{tag} 0 {wave}", f"Rsrc{tag} src{tag} {j} {source}"]
    lines += [f"Ron{tag} {j} {p} {R_ON}", f"Rpd{tag} {p} 0 100k", f"Rlim{tag} {p} {s} 10k",
              f"Rjleak{tag} {j} 0 1e12"]
    clamp = "DLL" if variant == "precision" else "DSCH"
    lines += [f"Dcp{tag} {s} vp {clamp}", f"Dcn{tag} vn {s} {clamp}"]
    if variant == "precision":
        lines += [f"Dbt1{tag} {s} {b} DSCH", f"Dbt2{tag} {b} {s} DSCH"]
    lines.append(f"X{tag} {s} {b} vp vn {b} {sub}")
    if c_sense:
        lines.append(f"Csn{tag} {s} 0 {c_sense}")
    if c_buffer:
        lines.append(f"Cbf{tag} {b} 0 {c_buffer}")
    return lines, {"jack": j, "protected": p, "sense": s, "out": b, "src": f"src{tag}" if source else None}


def general_output(tag, sub, wave, load, cable):
    d, m, j = f"d{tag}", f"m{tag}", f"k{tag}"
    lines = [f"Vs{tag} src{tag} 0 {wave}", f"X{tag} src{tag} {d} vp vn {d} {sub}",
             f"Risa{tag} {d} {m} 499", f"Risb{tag} {m} {j} 499", f"Rld{tag} {j} 0 {load}"]
    if cable:
        lines.append(f"Ccb{tag} {j} 0 {cable}")
    return lines, {"src": f"src{tag}", "drive": d, "jack": j}


def indicator(tag, sub, monitor, cap):
    """magnitude_indicator as U8417 unit 3: OUT=DRIVE, D1 DRIVE->LED_A, D2 SENSE->LED_A,
    D3 LED_K->DRIVE, D4 LED_K->SENSE, LED LED_A->LED_K, R_SENSE 5.6k SENSE->AGND, IN-=SENSE."""
    d, s, a, k, km, mon = (f"d{tag}", f"s{tag}", f"a{tag}", f"k{tag}", f"km{tag}", f"mon{tag}")
    lines = [f"Vm{tag} {mon} 0 {monitor}",
             f"D1{tag} {d} {a} DBAS", f"D2{tag} {s} {a} DBAS", f"D3{tag} {k} {d} DBAS", f"D4{tag} {k} {s} DBAS",
             f"DL{tag} {a} {km} DLED", f"Vled{tag} {km} {k} 0", f"Rsn{tag} {s} 0 {R_SENSE}"]
    if cap:
        lines += [f"Cla{tag} {a} 0 {cap}", f"Clk{tag} {k} 0 {cap}"]
    return lines, {"drive": d, "sense": s, "led_i": f"i(Vled{tag})", "mon": mon}


def header(title, model):
    m = MODELS[model]
    out = [title, ".param TEMP=27", f".include {m['lib']}", "Vplus vp 0 12", "Vminus vn 0 -12"]
    out += [f".model {name} D({params})" for name, (_, params) in DIODES.items()]
    return out


def control(analysis, vectors, data):
    rel = data.relative_to(ROOT).as_posix()
    return [".control", "set noinit", "set wr_singlescale", "set wr_vecnames", "option numdgt=8",
            analysis, f"wrdata {rel} " + " ".join(vectors), "quit", ".endc", ".end", ""]


# ----------------------------------------------------------------------------------------------
# Cases: one circuit per ngspice deck (several vendor cores in one deck share a timestep and failed
# to converge together, while each converges on its own).


def follower_cases(model):
    sub = MODELS[model]["subckt"]
    out = []

    def add(case, cell, variant, kind, analysis, frag):
        out.append({"model": model, "case": case, "cell": cell, "variant": variant, "kind": kind,
                    "analysis": analysis, "frag": frag})
    st, si, ov = "tran 20n 2m 0 20n", "tran 10n 200u 0 10n", "tran 20n 1.1m 0 20n"
    for v in ("base", "precision"):
        cell = f"follower_{v}"
        add("case1", cell, "patched_1k_step", "step", st, lambda t, v=v: follower(t, sub, STEP, variant=v))
        add("case1", cell, "unpatched", "quiet", st, lambda t, v=v: follower(t, sub, STEP, source=None, variant=v))
        add("case1", cell, "patched_1k_sine", "sine", si, lambda t, v=v: follower(t, sub, SINE, variant=v))
        for c in C_RUN:
            add("case2", cell, f"SENSE+{c}", "step", st, lambda t, c=c, v=v: follower(t, sub, STEP, variant=v, c_sense=c))
            add("case2", cell, f"BUFFER+{c}", "step", st, lambda t, c=c, v=v: follower(t, sub, STEP, variant=v, c_buffer=c))
        add("case4", cell, "overdrive_12V", "over", ov, lambda t, v=v: follower(t, sub, OVER, variant=v))
    for load, lv in OUT_LOADS.items():
        for cable, cv in OUT_CABLES.items():
            add("case3", "general_output", f"{load}/{cable}", "output", st,
                lambda t, lv=lv, cv=cv: general_output(t, sub, STEP, lv, cv))
    return out


def forward(model, current):
    """Forward voltage of a generic diode model at `current` (used only to seed the DC solve)."""
    scale = {"f": 1e-15, "p": 1e-12, "n": 1e-9, "u": 1e-6, "m": 1e-3}
    p = {k: float(v[:-1]) * scale[v[-1]] if v[-1] in scale else float(v)
         for k, v in (kv.split("=") for kv in DIODES[model][1].split())}
    return p["N"] * 0.025852 * math.log(current / p["IS"] + 1) + current * p["RS"]


def indicator_cases():
    sub = MODELS["OPA4196"]["subckt"]
    out = []
    for cap_key, cap in IND_CAPS.items():
        for bias_key, current in IND_BIAS.items():
            def frag(t, cap=cap, current=current):
                lines, nodes = indicator(t, sub, f"DC {current * R_SENSE:.6g}", cap)
                # Loop broken at IN-: injection between SENSE (low impedance) and IN- (high impedance).
                lines += [f"Vinj{t} inm{t} {nodes['sense']} DC 0 AC 1",
                          f"X{t} {nodes['mon']} inm{t} vp vn {nodes['drive']} {sub}"]
                nodes["inm"] = f"inm{t}"
                # The DC solve fails at 1 mA without a starting point; nodeset only seeds it.
                vs, vb, vl = current * R_SENSE, forward("DBAS", current), forward("DLED", current)
                lines.append(f".nodeset v({nodes['drive']})={vs + 2 * vb + vl:.4f} v(a{t})={vs + vb + vl:.4f} "
                             f"v(k{t})={vs - vb:.4f} v(km{t})={vs - vb:.4f} v(inm{t})={vs:.4f} v({nodes['sense']})={vs:.4f}")
                return lines, nodes
            out.append({"model": "OPA4196", "case": "case5a", "cell": "magnitude_indicator",
                        "variant": f"{cap_key}/{bias_key}", "kind": "loop", "analysis": "ac dec 100 10 1g", "frag": frag})
    for kind in ("sine", "step"):
        for amp_key, a in IND_AMPS.items():
            wave = f"SIN(0 {a:g} 20k)" if kind == "sine" else f"PULSE({-a:g} {a:g} 0 100n 100n 100u 200u)"
            for cap_key, cap in IND_CAPS.items():
                def frag(t, wave=wave, cap=cap):
                    lines, nodes = indicator(t, sub, wave, cap)
                    lines.append(f"X{t} {nodes['mon']} {nodes['sense']} vp vn {nodes['drive']} {sub}")
                    return lines, nodes
                out.append({"model": "OPA4196", "case": "case5b", "cell": "magnitude_indicator",
                            "variant": f"{kind}/{amp_key}/{cap_key}", "kind": f"ind_{kind}", "amp": a,
                            "analysis": f"tran 5n {'200u' if kind == 'sine' else '400u'} 0 5n", "frag": frag})
    return out


def all_cases():
    return [c for m in MODELS for c in follower_cases(m)] + indicator_cases()


# ----------------------------------------------------------------------------------------------
# Oracle and waveform readers


def oracle(name, body_lines, analysis, vectors):
    data = WORK / f"{name}.dat"
    deck = WORK / f"{name}.cir"
    body = "\n".join(body_lines + control(analysis, vectors, data))
    deck.write_text(body)
    data.unlink(missing_ok=True)
    proc = subprocess.run(["bash", "scripts/kicad/run.sh", "ngspice", "-b", deck.relative_to(ROOT).as_posix()],
                          cwd=ROOT, capture_output=True, text=True, timeout=600)
    if deck.read_text() != body:
        raise RuntimeError(f"{name} deck changed during execution")
    check_oracle_result(proc, data)
    rows = data.read_text().split("\n")
    names = []
    for nm in rows[0].split():  # a complex vector is written as two same-named columns: real, imaginary
        names.append(nm + "#imag" if nm in names else nm)
    table = [[float(x) for x in r.split()] for r in rows[1:] if r.strip()]
    if not table or not all(math.isfinite(x) for r in table for x in r):
        raise RuntimeError(f"{name}: empty or nonfinite waveform")
    cols = {nm: [r[i] for r in table] for i, nm in enumerate(names)}
    data.unlink()
    deck.unlink()
    return digest(body.encode()), cols


class Wave:
    def __init__(self, t, y):
        self.t, self.y = t, y

    def window(self, a, b):
        i, j = bisect.bisect_left(self.t, a), bisect.bisect_right(self.t, b)
        return self.t[i:j], self.y[i:j]

    def at(self, x):
        i = min(max(bisect.bisect_left(self.t, x), 1), len(self.t) - 1)
        t0, t1, y0, y1 = self.t[i - 1], self.t[i], self.y[i - 1], self.y[i]
        return y0 if t1 == t0 else y0 + (y1 - y0) * (x - t0) / (t1 - t0)

    def mean(self, a, b):
        _, y = self.window(a, b)
        return sum(y) / len(y)

    def pp(self, a, b):
        _, y = self.window(a, b)
        return max(y) - min(y)


def r(x, sig=5):
    if x is None:
        return None
    if x == 0 or not math.isfinite(x):
        return x
    return float(f"{x:.{sig}g}")


def settle_time(w, edge, end, final, band):
    """Time after `edge` when |v - final| last exceeded `band` within [edge, end]; None if never inside."""
    t, y = w.window(edge, end)
    last = None
    for ti, yi in zip(t, y):
        if abs(yi - final) > band:
            last = ti
    if last is None:
        return 0.0
    if last >= t[-1] - 1e-9:
        return None
    return last - edge


def step_metrics(w, ref=None, *, period=1e-3, half=500e-6, rise=1e-3, tail=100e-6):
    """Second cycle of the +/-5 V pulse: rise at 1 ms, fall at 1.501 ms."""
    fall = rise + half + 1e-6
    hi = w.mean(fall - 11e-6, fall - 1e-6)
    lo = w.mean(rise + period - 11e-6, rise + period - 1e-6)
    span = hi - lo
    _, yr = w.window(rise, fall)
    _, yf = w.window(fall, rise + period)
    over = max(0.0, (max(yr) - hi) / span, (lo - min(yf)) / span) * 100
    s_up = settle_time(w, rise, fall - 1e-6, hi, 1e-3)
    s_dn = settle_time(w, fall, rise + period - 1e-6, lo, 1e-3)
    ripple = max(w.pp(fall - tail, fall - 1e-6), w.pp(rise + period - tail, rise + period - 1e-6))
    m = {"overshoot_percent": r(over, 4),
         "settle_1mV_rise_us": r(s_up * 1e6, 4) if s_up is not None else None,
         "settle_1mV_fall_us": r(s_dn * 1e6, 4) if s_dn is not None else None,
         "settled_high_V": r(hi, 7), "settled_low_V": r(lo, 7),
         "late_ripple_pp_mV": r(ripple * 1e3, 4)}
    if ref is not None:
        rh = ref.mean(fall - 11e-6, fall - 1e-6)
        rl = ref.mean(rise + period - 11e-6, rise + period - 1e-6)
        m["steady_error_vs_protected_mV"] = r(max(abs(hi - rh), abs(lo - rl)) * 1e3, 4)
    m["error_vs_5V_source_mV"] = r(max(abs(hi - 5), abs(lo + 5)) * 1e3, 5)
    s = [x for x in (m["settle_1mV_rise_us"], m["settle_1mV_fall_us"])]
    m["diag_overshoot_le_10pct"] = "PASS" if over <= 10 else "FAIL"
    m["diag_settle_1mV_within_half_period"] = "PASS" if None not in s else "FAIL"
    m["sustained_oscillation"] = ripple > 1e-3
    return m


def quiet_metrics(w):
    t0 = 100e-6
    _, y = w.window(t0, w.t[-1])
    return {"dc_output_mV": r(sum(y) / len(y) * 1e3, 4), "pp_after_100us_mV": r((max(y) - min(y)) * 1e3, 4),
            "sustained_oscillation": (max(y) - min(y)) > 1e-3}


def sine_metrics(w, ref):
    a, b = 150e-6, 200e-6
    _, yo = w.window(a, b)
    _, yr = ref.window(a, b)
    tt, _ = w.window(a, b)
    err = max(abs(w.at(x) - ref.at(x)) for x in tt)
    amp_o, amp_r = (max(yo) - min(yo)) / 2, (max(yr) - min(yr)) / 2
    return {"output_peak_V": r(max(yo), 5), "output_trough_V": r(min(yo), 5),
            "gain_vs_protected": r(amp_o / amp_r, 6), "max_tracking_error_vs_protected_mV": r(err * 1e3, 4),
            "note": "10 V peak exceeds the TMUX7412F usable signal range above +9 V; the fixed 15 ohm R_ON (ASSUMED) does not model that compression"}


def over_metrics(w, sense):
    pos_on, pos_off, neg_on, neg_off = 11e-6, 212e-6, 512e-6, 713e-6
    _, yp = w.window(pos_on + 20e-6, pos_off - 1e-6)
    _, yn = w.window(neg_on + 20e-6, neg_off - 1e-6)
    final_p, final_n = w.mean(500e-6, 510e-6), w.mean(1.09e-3, 1.1e-3)
    out = {"output_min_during_plus12_V": r(min(yp), 5), "output_max_during_minus12_V": r(max(yn), 5),
           "sense_max_V": r(max(sense.y), 5), "sense_min_V": r(min(sense.y), 5),
           "phase_reversal": min(yp) <= 0 or max(yn) >= 0}
    for label, edge, end, final in (("from_plus12", pos_off, neg_on - 1e-6, final_p), ("from_minus12", neg_off, 1.1e-3 - 1e-6, final_n)):
        for band, name in ((1e-3, "1mV"), (10e-3, "10mV")):
            s = settle_time(w, edge, end, final, band)
            out[f"recovery_{name}_{label}_us"] = r(s * 1e6, 4) if s is not None else None
    return out


def extrema_per_period(t, y, period):
    """Count direction changes, ignoring wiggles below 0.1 % of the span, per period."""
    span = (max(y) - min(y)) or 1.0
    thr, count, direction, anchor = span * 1e-3, 0, 0, y[0]
    for v in y[1:]:
        d = v - anchor
        if abs(d) < thr:
            continue
        s = 1 if d > 0 else -1
        if direction and s != direction:
            count += 1
        direction, anchor = s, v
    return count / ((t[-1] - t[0]) / period)


def ind_sine_metrics(drive, sense, led, amp):
    a, b, period = 100e-6, 200e-6, 50e-6
    t, i = led.window(a, b)
    ideal_pk = amp / R_SENSE
    mean_ideal = 2 / math.pi * ideal_pk
    mean_i = sum(abs(x) for x in i) / len(i)
    dead = sum(1 for x in i if abs(x) < 0.05 * ideal_pk) / len(i)
    td, yd = drive.window(a, b)
    samples = [r(led.at(150e-6 + k * period / 40) * 1e6, 4) for k in range(40)]
    # Sustained oscillation would persist through conduction after the handover ring has decayed.
    # Handover ends at the last time, within 21 us of a MONITOR zero crossing, that SENSE is more than
    # 10 % of the amplitude away from MONITOR; the residual is SENSE minus its 2 us centred moving
    # average from 1 us after that until 22 us after the crossing (at least 4 us, else not conducting).
    mon = lambda x: amp * math.sin(2 * math.pi * 20e3 * x)  # noqa: E731
    residual, handovers = None, []
    for z in (100e-6, 125e-6, 150e-6, 175e-6):
        tz = [z + k * 20e-9 for k in range(1101)]
        off = [x for x in tz if abs(sense.at(x) - mon(x)) > 0.1 * amp]
        end = (off[-1] - z) if off else 0.0
        handovers.append(end)
        start = z + end + 1e-6
        n = int(round((z + 22e-6 - start) / 20e-9))
        if n < 200:
            continue
        grid = [sense.at(start + k * 20e-9) for k in range(n + 1)]
        prefix = [0.0]
        for v in grid:
            prefix.append(prefix[-1] + v)
        res = [grid[k] - (prefix[k + 51] - prefix[k - 50]) / 101 for k in range(50, n - 50)]
        residual = max(residual or 0.0, max(res) - min(res))
    return {"led_peak_uA": r(max(i) * 1e6, 4), "ideal_peak_uA": r(ideal_pk * 1e6, 4),
            "led_mean_over_ideal_mean": r(mean_i / mean_ideal, 4),
            "fraction_of_period_below_5pct_of_ideal_peak": r(dead, 4),
            "drive_extrema_per_period": r(extrema_per_period(td, yd, period), 3),
            "drive_extrema_note": "2 = clean; each further pair per period is one damped ring at a bridge handover (turn-on edge)",
            "drive_swing_V": [r(min(yd), 4), r(max(yd), 4)],
            "led_current_uA_one_period_40pts": samples,
            "handover_end_after_zero_crossing_us": [r(x * 1e6, 4) for x in handovers],
            "sense_hf_residual_pp_mV": r(residual * 1e3, 4) if residual is not None else "NOT CONDUCTING (handover lasts the whole window)",
            "sustained_oscillation": residual is not None and residual > max(1e-3, 0.01 * amp)}


def ind_step_metrics(drive, sense, led, amp):
    """Second cycle of PULSE(-A A 0 100n 100n 100u 200u): rise at 200 us, fall at 300.1 us."""
    ideal = amp / R_SENSE
    out = {"ideal_led_uA": r(ideal * 1e6, 4)}
    for label, edge in (("to_plus", 200e-6), ("to_minus", 300.1e-6)):
        end = edge + 99.8e-6
        final = led.mean(end - 10e-6, end)
        t, i = led.window(edge, end)
        peak = max(i)
        s = settle_time(led, edge, end, final, 0.01 * abs(final) if final else 1e-9)
        # The bridge hands over between diode pairs: the LED current dips, then turns back on.
        # Turn-on is the first time after that dip that the current regains 50 % of its final value.
        k_min = min(range(len(i)), key=lambda k: i[k] if t[k] <= edge + 20e-6 else math.inf)
        t_on = next((ti - edge for ti, x in zip(t[k_min:], i[k_min:]) if x >= 0.5 * final), None)
        td, yd = drive.window(edge, end)
        out[label] = {"final_led_uA": r(final * 1e6, 5), "led_dip_min_uA": r(i[k_min] * 1e6, 4),
                      "led_dip_at_us": r((t[k_min] - edge) * 1e6, 4),"led_overshoot_percent": r(max(0.0, (peak - final) / final * 100), 4),
                      "led_turn_on_50pct_us": r(t_on * 1e6, 4) if t_on is not None else None,
                      "led_settle_1pct_us": r(s * 1e6, 4) if s is not None else None,
                      "late_sense_pp_mV": r(sense.pp(end - 10e-6, end) * 1e3, 4),
                      "late_drive_pp_mV": r(drive.pp(end - 10e-6, end) * 1e3, 4),
                      "drive_extrema_after_edge": r(extrema_per_period(td, yd, end - edge), 3)}
    out["sustained_oscillation"] = any(out[k]["late_sense_pp_mV"] > max(1.0, 0.01 * amp * 1e3) for k in ("to_plus", "to_minus"))
    return out


def loop_metrics(cols, nodes):
    f = cols["frequency"]
    s = [complex(a, b) for a, b in zip(cols[f"v({nodes['sense']})"], cols[f"v({nodes['sense']})#imag"])] if f"v({nodes['sense']})#imag" in cols else None
    if s is None:
        raise RuntimeError("complex AC columns missing")
    m = [complex(a, b) for a, b in zip(cols[f"v({nodes['inm']})"], cols[f"v({nodes['inm']})#imag"])]
    loop = [-x / y for x, y in zip(s, m)]
    phase, prev = [], None
    for x in loop:
        p = math.degrees(cmath.phase(x))
        if prev is not None:
            while p - prev > 180:
                p -= 360
            while p - prev < -180:
                p += 360
        phase.append(p)
        prev = p
    mag = [abs(x) for x in loop]
    cross = None
    for k in range(1, len(mag)):
        if mag[k - 1] >= 1 > mag[k]:
            fr = math.log(mag[k - 1]) / (math.log(mag[k - 1]) - math.log(mag[k]))
            cross = (f[k - 1] * (f[k] / f[k - 1]) ** fr, phase[k - 1] + (phase[k] - phase[k - 1]) * fr)
            break
    if cross is None:
        return {"crossover_Hz": None, "phase_margin_deg": None, "dc_loop_gain_dB": r(20 * math.log10(mag[0]), 4)}
    return {"crossover_Hz": r(cross[0], 4), "phase_margin_deg": r(180 + cross[1], 4),
            "dc_loop_gain_dB": r(20 * math.log10(mag[0]), 4)}


# ----------------------------------------------------------------------------------------------


def vectors(nodes, kind):
    if kind == "loop":
        return [f"v({nodes['sense']})", f"v({nodes['inm']})"]
    vecs = [f"v({nodes[k]})" for k in ("out", "protected", "sense", "drive", "jack") if nodes.get(k)]
    if nodes.get("led_i"):
        vecs.append(nodes["led_i"])
    return vecs


def evaluate(c, cols, nodes):
    kind = c["kind"]
    if kind == "loop":
        return loop_metrics(cols, nodes)
    t = cols["time"]

    def w(node):
        return Wave(t, cols[f"v({nodes[node]})"])
    if kind == "step":
        return step_metrics(w("out"), w("protected"))
    if kind == "quiet":
        return quiet_metrics(w("out"))
    if kind == "sine":
        return sine_metrics(w("out"), w("protected"))
    if kind == "over":
        return over_metrics(w("out"), w("sense"))
    if kind == "output":
        return {"jack": step_metrics(w("jack")), "drive": step_metrics(w("drive"))}
    led = Wave(t, cols[nodes["led_i"]])
    fn = ind_sine_metrics if kind == "ind_sine" else ind_step_metrics
    return fn(w("drive"), w("sense"), led, c["amp"])


def run_all():
    WORK.mkdir(parents=True, exist_ok=True)
    init = ROOT / ".spiceinit"
    if init.exists():
        raise RuntimeError("refusing to replace an existing .spiceinit")
    init.write_text("set ngbehavior=ps\n")
    results = []
    try:
        for c in all_cases():
            lines, nodes = c["frag"]("1")
            title = f"MC04-S4 {c['model']} {c['case']} {c['cell']} {c['variant']}"
            name = "-".join((c["model"], c["case"], c["cell"], c["variant"])).replace("/", "_").replace("+", "p")
            deck = header(title, c["model"]) + lines
            method = "trap (ngspice default)"
            try:
                sha, cols = oracle(name, deck, c["analysis"], vectors(nodes, c["kind"]))
            except RuntimeError as error:
                # Fallback for a deck whose trapezoidal run stops with "Timestep too small": rerun once with
                # Gear integration and record it. Gear can damp ringing slightly; the row says so.
                if "Timestep too small" not in str(error):
                    raise
                method = "gear (trap stopped: timestep too small)"
                sha, cols = oracle(name, deck + [".options method=gear"], c["analysis"], vectors(nodes, c["kind"]))
            results.append({"model": c["model"], "case": c["case"], "cell": c["cell"], "variant": c["variant"],
                            "integration": method, "deck_sha256": sha, "metrics": evaluate(c, cols, nodes)})
            print(f"{title}: done", flush=True)
    finally:
        init.unlink()
    return results


def deltas(results):
    index = {(x["case"], x["cell"], x["variant"], x["model"]): x["metrics"] for x in results}
    out = []
    for (case, cell, variant, model), m196 in index.items():
        if model != "OPA4196" or (case, cell, variant, "OPA4197") not in index:
            continue
        m197 = index[(case, cell, variant, "OPA4197")]
        out.append({"case": case, "cell": cell, "variant": variant, "OPA4197_minus_OPA4196": diff(m197, m196)})
    return out


def diff(a, b):
    if isinstance(a, dict):
        d = {k: diff(a[k], b.get(k)) for k in a if k in b}
        return {k: v for k, v in d.items() if v is not None}
    if type(a) in (int, float) and type(b) in (int, float) and not isinstance(a, bool):
        return r(a - b, 4)
    return None


def report(results):
    return {
        "schema_version": 1,
        "status": "MODEL EVIDENCE ONLY - NO ACCEPTANCE SET; NOT HARDWARE QUALIFICATION",
        "brief": BRIEF,
        "task": "osc-stack-20261114 / MC04-S4-INPUT-BUFFER-SPICE / 20261121-1",
        "instances": INSTANCES, "cell_users": CELL_USERS,
        "models": {
            "OPA4196": {"model": "TI OPAx196 Final 1.5 (29AUG2022), generic core for the OPAx196 family",
                        "url": OPA196_URL, "zip_sha256": OPA196_ZIP_SHA256, "lib_sha256": OPA196_LIB_SHA256,
                        "retained": OPA196_RETAINED},
            "OPA4197": {"model": "TI OPAx197 Final 1.3 (23JUN2022), generic core; same die for OPA4197IDR (SOIC-14) and OPA4197IPWR (TSSOP-14)",
                        "url": opa197.URL, "zip_sha256": opa197.ZIP_SHA256, "lib_sha256": opa197.LIB_SHA256},
        },
        "oracle": "pinned KiCad 10 image via scripts/kicad/run.sh, ngspice -b, set ngbehavior=ps",
        "assumed": {
            "switch": f"TMUX7412F modelled as its {R_ON} ohm R_ON bound (fact-fault-switch-t-ron-12v-single), a fixed resistor; no switch capacitance, no R_ON rise within 3 V of VDD, no overvoltage turn-off",
            "diodes": {name: {"stands_for": who, "spice": params} for name, (who, params) in DIODES.items()},
            "board_run_capacitance": "case 2 adds 10/30/50 pF to SENSE or BUFFER (50 pF bounds a long run)",
            "unpatched": "read as no source on the jack (100 kOhm R_PD only); quiescent output and oscillation check",
            "package": "Neither TI model has package parasitics; SOIC-14 vs TSSOP-14 is not distinguished by any case",
        },
        "diagnostic_targets": "overshoot <= 10 % and settle within 1 mV (sweep_precision.py) are diagnostic labels only, not acceptance",
        "conditions": {
            "rails": "+/-12 V ideal", "temperature_C": 27,
            "case1": "PULSE -5..+5 V, 1 ms period, second cycle measured; 10 V-peak 20 kHz sine; source 1 kOhm or unpatched",
            "case2": "case-1 step, patched, with 10/30/50 pF on SENSE or on BUFFER",
            "case3": "follower driven by an ideal +/-5 V step, 499+499 ohm to jack; open/100k/10k loads; 0/100p/1n cable; metrics at jack and DRIVE",
            "case4": "jack PWL 0 -> +12 V (200 us) -> 0 -> -12 V (200 us) -> 0, source 1 kOhm",
            "case5a": "OPA4196 only; loop broken at IN- by AC voltage injection between SENSE and IN- (Middlebrook voltage loop); T = -V(SENSE)/V(IN-); DC bias MONITOR = I x 5.6 kOhm",
            "case5b": "OPA4196 only; 20 kHz sines and +/-A steps (100 us halves), A = 10 mV/100 mV/1 V/5 V; 0/7.2/15/30 pF on each of LED_A and LED_K",
        },
        "paper_screen_case5a": PAPER,
        "results": results,
        "deltas": deltas(results),
        "model_limit": "TI macro-models predict modeled behavior only; package parasitics, layout, tolerance, temperature, the real switch and diodes, and bench stability remain NOT RUN.",
    }


def run(*, check: bool = False, offline: bool = False) -> None:
    models(offline=offline)
    results = run_all()
    body = json.dumps(report(results), indent=2) + "\n"
    if check:
        if not OUT.exists() or OUT.read_text() != body:
            raise RuntimeError("input-buffer vendor report drift")
    else:
        OUT.write_text(body)
    osc = [x for x in results if x["metrics"].get("sustained_oscillation")]
    print(f"Input-buffer TI-model run: {len(results)} rows; {len(osc)} with sustained oscillation flagged")


if __name__ == "__main__":
    run(check="--check" in sys.argv, offline="--offline" in sys.argv)
