"""MC04 stage 4: input-buffer stages with the TI OPAx196 and OPAx197 PSpice models.

Compares OPA4196 (current, SOIC-14) and OPA4197 (TSSOP-14 candidate OPA4197IPWR; the model is
die-level and does not see the package) in the six input-buffer ICs U1216, U1416, U1518, U4346,
U8314 and U8417, in the pinned KiCad 10 ngspice oracle. Both TI libraries stay in the ignored
local cache and are pinned by digest; a changed remote file fails closed.

Cases follow circuit/orchestration/campaigns/osc-stack-20261114/
mc04-s4-input-buffer-native-brief-20261121.md, with Revision 1 after the
independent review (commit c86e6fe), and the MC04-S5 OPA4197 indicator rows
(mc04-s5-opa4197-swap-native-brief-20261121.md, 8394f84). The 10 % overshoot and 1 mV
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
# Stage 1b paper screen, read per point (U8417 units 3-4, default boundary). The paper evaluates
# 7.22 pF per LED net and 2x / 4x that (14.4 / 28.9 pF) for worst values only; this run uses
# 7.2 / 15 / 30 pF, so the 15 pF and 30 pF comparisons are against 14.4 pF and 28.9 pF.
PAPER_RESULT = ROOT / "scripts/stack/studies/mc04_s1b_indicator_loops/result.json"
PAPER_SHA256 = "5cdac8e9d4e482bd390b6dd6549c2cfe244e1f154cddb46c11ff102b412857fa"
OSC_LIMIT = 1e-3  # absolute 1 mV threshold for every sustained-oscillation test
NOT_EVALUATED = "NOT EVALUATED"

STEP = "PULSE(-5 5 0 1u 1u 500u 1m)"
SINE = "SIN(0 10 20k)"
OVERDRIVES = {"12V": 12, "15V": 15}


def over_wave(v):
    return f"PWL(0 0 10u 0 11u {v} 211u {v} 212u 0 511u 0 512u {-v} 712u {-v} 713u 0 1.1m 0)"


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


def control(analysis, vectors, data, op_data=None, op_vectors=None):
    rel = data.relative_to(ROOT).as_posix()
    pre = []
    if op_vectors:
        # Record the DC operating point the AC analysis linearises about.
        pre = ["op", f"wrdata {op_data.relative_to(ROOT).as_posix()} " + " ".join(op_vectors)]
    return ([".control", "set noinit", "set wr_singlescale", "set wr_vecnames", "option numdgt=8"] + pre +
            [analysis, f"wrdata {rel} " + " ".join(vectors), "quit", ".endc", ".end", ""])


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
        for name, volts in OVERDRIVES.items():
            add("case4", cell, f"overdrive_{name}", "over", ov,
                lambda t, v=v, volts=volts: follower(t, sub, over_wave(volts), variant=v))
            out[-1]["volts"] = volts
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


def loop_probe(t, x, y):
    """Break the loop between return node y (source side) and IN- node x (load side) with one fixed
    topology for both Middlebrook runs: y -[Vmy 0 V]- n -[Vinj]- x, and Iinj into n.

    Run 1 (Vinj AC 1, Iinj AC 0): V(x) - V(n) = 1 and V(y) = V(n), so Tv = -V(n)/V(x).
    Run 2 (Vinj AC 0, Iinj AC 1): I(n->y) = i(Vmy) and I(n->x) = -i(Vinj), so Ti = I(n->y)/I(n->x).
    Both runs are AC analyses of the same deck, after one recorded operating point."""
    return ([f"Vmy{t} n{t} {y} 0", f"Vinj{t} {x} n{t} DC 0 AC 1", f"Iinj{t} 0 n{t} DC 0 AC 0"],
            [f"v(n{t})", f"v({x})"], [f"i(Vmy{t})", f"i(Vinj{t})"])


# Indicator models and added LED-net capacitances. OPA4196 is the S4 sweep; OPA4197 at 0 pF (as built,
# U8417 stays on its front board) and 7.2 pF is the MC04-S5 gate before U8417 units 3-4 swap.
IND_MODEL_CAPS = {"OPA4196": tuple(IND_CAPS), "OPA4197": ("0", "7.2p")}


def indicator_cases():
    out = []
    for model, caps in IND_MODEL_CAPS.items():
        sub = MODELS[model]["subckt"]
        for cap_key in caps:
            cap = IND_CAPS[cap_key]
            for bias_key, current in IND_BIAS.items():
                def frag(t, seed, cap=cap, current=current, sub=sub):
                    lines, nodes = indicator(t, sub, f"DC {current * R_SENSE:.6g}", cap)
                    inj, vv, vi = loop_probe(t, f"inm{t}", nodes["sense"])
                    lines += inj + [f"X{t} {nodes['mon']} inm{t} vp vn {nodes['drive']} {sub}"]
                    # Optional DC seed from the forward-voltage estimate; run_all() picks the seed and
                    # asserts both injection runs share one correct operating point.
                    vs, vb, vl = current * R_SENSE, forward("DBAS", current), forward("DLED", current)
                    d, s = nodes["drive"], nodes["sense"]
                    if seed:
                        lines.append(f".nodeset v({d})={vs + 2 * vb + vl:.4f} v(a{t})={vs + vb + vl:.4f} "
                                     f"v(k{t})={vs - vb:.4f} v(km{t})={vs - vb:.4f} v(inm{t})={vs:.4f} v({s})={vs:.4f} v(n{t})={vs:.4f}")
                    op = [f"v({d})", f"v({s})", f"v(a{t})", f"v(k{t})", f"v(km{t})", nodes["led_i"]]
                    return lines, vv, vi, op
                out.append({"model": model, "case": "case5a", "cell": "magnitude_indicator",
                            "variant": f"{cap_key}/{bias_key}", "kind": "loop", "analysis": "ac dec 100 10 1g",
                            "frag": frag, "cap": cap_key, "bias": bias_key, "target_A": current})
    for model, m in MODELS.items():
        def frag(t, seed, sub=m["subckt"]):
            # Control: a plain unity follower (IN+ at 0 V, no load) broken the same way, to show the
            # vendor core's own phase lag apart from the bridge. It needs no DC seed.
            inj, vv, vi = loop_probe(t, f"inm{t}", f"o{t}")
            return [f"X{t} 0 inm{t} vp vn o{t} {sub}"] + inj, vv, vi, [f"v(o{t})"]
        out.append({"model": model, "case": "case5a_control", "cell": "plain_follower", "variant": "no_load",
                    "kind": "loop", "analysis": "ac dec 100 10 1g", "frag": frag})
    for model, caps in IND_MODEL_CAPS.items():
        sub = MODELS[model]["subckt"]
        for kind in ("sine", "step"):
            for amp_key, a in IND_AMPS.items():
                wave = f"SIN(0 {a:g} 20k)" if kind == "sine" else f"PULSE({-a:g} {a:g} 0 100n 100n 100u 200u)"
                for cap_key in caps:
                    def frag(t, wave=wave, cap=IND_CAPS[cap_key], sub=sub):
                        lines, nodes = indicator(t, sub, wave, cap)
                        lines.append(f"X{t} {nodes['mon']} {nodes['sense']} vp vn {nodes['drive']} {sub}")
                        return lines, nodes
                    out.append({"model": model, "case": "case5b", "cell": "magnitude_indicator",
                                "variant": f"{kind}/{amp_key}/{cap_key}", "kind": f"ind_{kind}", "amp": a,
                                "analysis": f"tran 5n {'200u' if kind == 'sine' else '400u'} 0 5n", "frag": frag})
    return out


def all_cases():
    return [c for m in MODELS for c in follower_cases(m)] + indicator_cases()


# ----------------------------------------------------------------------------------------------
# Oracle and waveform readers


def oracle(name, body_lines, analysis, vectors, op_vectors=None):
    data = WORK / f"{name}.dat"
    deck = WORK / f"{name}.cir"
    op_data = WORK / f"{name}.op.dat"
    body = "\n".join(body_lines + control(analysis, vectors, data, op_data, op_vectors))
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
    if op_vectors:
        rows = op_data.read_text().split("\n")
        values = [float(x) for x in rows[1].split()]
        op = dict(zip(rows[0].split(), values))
        op_data.unlink()
        if not all(math.isfinite(v) for v in op.values()):
            raise RuntimeError(f"{name}: nonfinite operating point")
        return digest(body.encode()), cols, op
    return digest(body.encode()), cols


def read_table(path):
    rows = path.read_text().split("\n")
    names = []
    for nm in rows[0].split():  # a complex vector is written as two same-named columns: real, imaginary
        names.append(nm + "#imag" if nm in names else nm)
    table = [[float(x) for x in r.split()] for r in rows[1:] if r.strip()]
    if not table or not all(math.isfinite(x) for r in table for x in r):
        raise RuntimeError(f"{path.name}: empty or nonfinite data")
    return {nm: [r[i] for r in table] for i, nm in enumerate(names)}


def loop_oracle(name, body_lines, analysis, t, vv, vi, op_vectors):
    """One deck: operating point, AC with voltage injection, AC with current injection, operating point.

    Returns the deck digest, both AC tables and the operating point recorded before and after."""
    files = {k: WORK / f"{name}.{k}.dat" for k in ("op1", "v", "i", "op2")}
    rel = {k: p.relative_to(ROOT).as_posix() for k, p in files.items()}
    deck = WORK / f"{name}.cir"
    body = "\n".join(body_lines + [
        ".control", "set noinit", "set wr_singlescale", "set wr_vecnames", "option numdgt=8",
        "op", f"wrdata {rel['op1']} " + " ".join(op_vectors),
        analysis, f"wrdata {rel['v']} " + " ".join(vv),
        f"alter @vinj{t}[acmag]=0", f"alter @iinj{t}[acmag]=1",
        analysis, f"wrdata {rel['i']} " + " ".join(vi),
        "op", f"wrdata {rel['op2']} " + " ".join(op_vectors),
        "quit", ".endc", ".end", ""])
    deck.write_text(body)
    for p in files.values():
        p.unlink(missing_ok=True)
    proc = subprocess.run(["bash", "scripts/kicad/run.sh", "ngspice", "-b", deck.relative_to(ROOT).as_posix()],
                          cwd=ROOT, capture_output=True, text=True, timeout=600)
    if deck.read_text() != body:
        raise RuntimeError(f"{name} deck changed during execution")
    check_oracle_result(proc, files["i"])
    out = {k: read_table(p) for k, p in files.items()}
    for p in files.values():
        p.unlink()
    deck.unlink()
    ops = {k: {n: v[0] for n, v in out[k].items() if n in op_vectors} for k in ("op1", "op2")}  # drop the scale column
    return digest(body.encode()), out["v"], out["i"], ops


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


def hf_residual(f, start, end, *, dt=20e-9, half=25):
    """Peak-to-peak of f minus its centred moving average (2*half+1 points at dt, 1 us by default).

    A smooth error signal leaves almost nothing; a sustained oscillation above about 1 MHz stays."""
    n = int(round((end - start) / dt))
    grid = [f(start + k * dt) for k in range(n + 1)]
    prefix = [0.0]
    for v in grid:
        prefix.append(prefix[-1] + v)
    res = [grid[k] - (prefix[k + half + 1] - prefix[k - half]) / (2 * half + 1) for k in range(half, n - half)]
    return max(res) - min(res)


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
    m["sustained_oscillation"] = ripple > OSC_LIMIT
    return m


def quiet_metrics(w):
    t0 = 100e-6
    _, y = w.window(t0, w.t[-1])
    return {"dc_output_mV": r(sum(y) / len(y) * 1e3, 4), "pp_after_100us_mV": r((max(y) - min(y)) * 1e3, 4),
            "sustained_oscillation": (max(y) - min(y)) > OSC_LIMIT}


def sine_metrics(w, ref, sense):
    a, b = 150e-6, 200e-6
    resid = hf_residual(lambda x: w.at(x) - sense.at(x), a, b)
    _, yo = w.window(a, b)
    _, yr = ref.window(a, b)
    tt, _ = w.window(a, b)
    err = max(abs(w.at(x) - ref.at(x)) for x in tt)
    amp_o, amp_r = (max(yo) - min(yo)) / 2, (max(yr) - min(yr)) / 2
    return {"output_peak_V": r(max(yo), 5), "output_trough_V": r(min(yo), 5),
            "gain_vs_protected": r(amp_o / amp_r, 6), "max_tracking_error_vs_protected_mV": r(err * 1e3, 4),
            "follower_error_hf_residual_pp_mV": r(resid * 1e3, 4),
            "sustained_oscillation": resid > OSC_LIMIT,
            "note": "10 V peak exceeds the TMUX7412F usable signal range above +9 V; the fixed 15 ohm R_ON (ASSUMED) does not model that compression"}


def over_metrics(w, sense, volts):
    """PWL 0 -> +V (11-211 us) -> 0 -> -V (512-712 us) -> 0. Phase reversal: in the positive hold the
    output falls more than 0.5 V below SENSE (in the negative hold, rises above it), per the revised brief."""
    pos_on, pos_off, neg_on, neg_off = 11e-6, 212e-6, 512e-6, 713e-6
    tp, yp = w.window(pos_on + 20e-6, pos_off - 1e-6)
    tn, yn = w.window(neg_on + 20e-6, neg_off - 1e-6)
    gap_p = min(y - sense.at(x) for x, y in zip(tp, yp))
    gap_n = max(y - sense.at(x) for x, y in zip(tn, yn))
    final_p, final_n = w.mean(500e-6, 510e-6), w.mean(1.09e-3, 1.1e-3)
    holds = ((pos_off - 51e-6, pos_off - 1e-6), (neg_on - 51e-6, neg_on - 1e-6),
             (neg_off - 51e-6, neg_off - 1e-6), (1.1e-3 - 51e-6, 1.1e-3 - 1e-6))
    ripple = max(w.pp(a, b) for a, b in holds)
    out = {"jack_overdrive_V": volts,
           "output_min_during_plus_hold_V": r(min(yp), 5), "output_max_during_minus_hold_V": r(max(yn), 5),
           "sense_max_V": r(max(sense.y), 5), "sense_min_V": r(min(sense.y), 5),
           "clamp_conducts": max(sense.y) > 12.0 or min(sense.y) < -12.0,
           "min_output_minus_sense_plus_hold_V": r(gap_p, 4), "max_output_minus_sense_minus_hold_V": r(gap_n, 4),
           "phase_reversal": gap_p < -0.5 or gap_n > 0.5,
           "hold_ripple_pp_mV": r(ripple * 1e3, 4), "sustained_oscillation": ripple > OSC_LIMIT}
    for label, edge, end, final in (("from_plus", pos_off, neg_on - 1e-6, final_p),
                                    ("from_minus", neg_off, 1.1e-3 - 1e-6, final_n)):
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
    # Handover ends at the last time, within 22 us of a MONITOR zero crossing, that SENSE is more than
    # 10 % of the amplitude away from MONITOR. From 1 us after that to 22 us after the crossing (at
    # least 4 us, else the bridge is not conducting and the row is NOT EVALUATED), the follower error
    # SENSE - MONITOR minus its 1 us moving average is tested against the absolute 1 mV limit.
    mon = lambda x: amp * math.sin(2 * math.pi * 20e3 * x)  # noqa: E731
    residual, handovers = None, []
    for z in (100e-6, 125e-6, 150e-6, 175e-6):
        tz = [z + k * 20e-9 for k in range(1101)]
        off = [x for x in tz if abs(sense.at(x) - mon(x)) > 0.1 * amp]
        end = (off[-1] - z) if off else 0.0
        handovers.append(end)
        start = z + end + 1e-6
        if z + 22e-6 - start < 4e-6:
            continue
        res = hf_residual(lambda x: sense.at(x) - mon(x), start, z + 22e-6)
        residual = max(residual or 0.0, res)
    return {"led_peak_uA": r(max(i) * 1e6, 4), "ideal_peak_uA": r(ideal_pk * 1e6, 4),
            "led_mean_over_ideal_mean": r(mean_i / mean_ideal, 4),
            "fraction_of_period_below_5pct_of_ideal_peak": r(dead, 4),
            "drive_extrema_per_period": r(extrema_per_period(td, yd, period), 3),
            "drive_extrema_note": "2 = clean; each further pair per period is one damped ring at a bridge handover (turn-on edge)",
            "drive_swing_V": [r(min(yd), 4), r(max(yd), 4)],
            "led_current_uA_one_period_40pts": samples,
            "handover_end_after_zero_crossing_us": [r(x * 1e6, 4) for x in handovers],
            "sense_error_hf_residual_pp_mV": r(residual * 1e3, 4) if residual is not None else "NOT CONDUCTING (handover lasts the whole window)",
            "sustained_oscillation": NOT_EVALUATED if residual is None else residual > OSC_LIMIT}


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
    out["sustained_oscillation"] = any(out[k]["late_sense_pp_mV"] > OSC_LIMIT * 1e3 for k in ("to_plus", "to_minus"))
    return out


def middlebrook(tv, ti):
    """Middlebrook double injection: T = (Tv*Ti - 1) / (Tv + Ti + 2), with Tv from the voltage run and
    Ti from the current run at the same break; Zs/Zl = (Tv - T) / (1 + T)."""
    t = (tv * ti - 1) / (tv + ti + 2)
    return t, (tv - t) / (1 + t)


def unwrap_deg(values):
    phase, prev = [], None
    for x in values:
        p = math.degrees(cmath.phase(x))
        if prev is not None:
            while p - prev > 180:
                p -= 360
            while p - prev < -180:
                p += 360
        phase.append(p)
        prev = p
    return phase


def loop_metrics(freq, loop):
    """Unity crossover (log-interpolated) and phase margin 180 + phase(T) of a complex loop gain T."""
    phase, mag = unwrap_deg(loop), [abs(x) for x in loop]
    for k in range(1, len(mag)):
        if mag[k - 1] >= 1 > mag[k]:
            fr = math.log(mag[k - 1]) / (math.log(mag[k - 1]) - math.log(mag[k]))
            return {"crossover_Hz": freq[k - 1] * (freq[k] / freq[k - 1]) ** fr,
                    "phase_margin_deg": 180 + phase[k - 1] + (phase[k] - phase[k - 1]) * fr,
                    "dc_loop_gain_dB": 20 * math.log10(mag[0]), "index": k}
    return {"crossover_Hz": None, "phase_margin_deg": None, "dc_loop_gain_dB": 20 * math.log10(mag[0]), "index": None}


def complex_col(cols, name):
    return [complex(a, b) for a, b in zip(cols[name], cols[name + "#imag"])]


def loop_rows(cv, vv, ci, vi):
    """Combine the voltage-injection run (vectors [v(y), v(x)]) and the current-injection run
    (vectors [i(n->y), i(n->x)]) into voltage-only and Middlebrook double-injection results."""
    if cv["frequency"] != ci["frequency"]:
        raise RuntimeError("loop runs use different frequency grids")
    f = cv["frequency"]
    vy, vx = complex_col(cv, vv[0]), complex_col(cv, vv[1])
    iy, ix = complex_col(ci, vi[0]), [-x for x in complex_col(ci, vi[1])]  # I(n->x) = -i(Vinj)
    tv = [-a / b for a, b in zip(vy, vx)]
    ti = [a / b for a, b in zip(iy, ix)]  # Ti = I(n->y) / I(n->x): source-side over load-side current
    pairs = [middlebrook(a, b) for a, b in zip(tv, ti)]
    full = loop_metrics(f, [p[0] for p in pairs])
    volt = loop_metrics(f, tv)
    zr = abs(pairs[full["index"]][1]) if full["index"] is not None else None
    clean = lambda m: {k: r(v, 4) for k, v in m.items() if k != "index"}  # noqa: E731
    return {**clean(full), "zs_over_zl_at_crossover": r(zr, 4), "voltage_injection_only": clean(volt),
            "sustained_oscillation": NOT_EVALUATED}


# Loop decks: solver tolerances tried tightest first. ngspice's default reltol=1e-3 leaves the bridge
# operating point at 1 mA loose by 0.5-0.8 % (it moves between the two AC runs); the tight settings put
# it at the intended current.
LOOP_TOLERANCES = (("reltol=1e-6 vntol=1e-9 abstol=1e-15", ".options reltol=1e-6 vntol=1e-9 abstol=1e-15"),
                   ("reltol=1e-5", ".options reltol=1e-5"), ("ngspice default", None))


def dc_check(ops, target):
    """The operating point recorded before and after the two AC runs must agree (0.1 mV, 0.01 %), and an
    indicator row must carry its intended bridge current through the LED (1 %). None when usable."""
    v, i = ops["op1"], ops["op2"]
    if set(v) != set(i):
        return "operating-point vectors differ"
    for k in v:
        if abs(v[k] - i[k]) > (1e-12 + 1e-4 * abs(v[k]) if k.startswith("i(") else 1e-4):
            return f"operating point moved between the AC runs on {k}: {v[k]:.6g} vs {i[k]:.6g}"
    if target is not None:
        led = next(val for k, val in v.items() if k.startswith("i("))
        if abs(led - target) > 0.01 * target:
            return f"LED current {led:.6g} A is not the intended {target:.6g} A"
    return None


def vectors(nodes, kind):
    vecs = [f"v({nodes[k]})" for k in ("out", "protected", "sense", "drive", "jack") if nodes.get(k)]
    if nodes.get("led_i"):
        vecs.append(nodes["led_i"])
    return vecs


def evaluate(c, cols, nodes):
    kind = c["kind"]
    t = cols["time"]

    def w(node):
        return Wave(t, cols[f"v({nodes[node]})"])
    if kind == "step":
        return step_metrics(w("out"), w("protected"))
    if kind == "quiet":
        return quiet_metrics(w("out"))
    if kind == "sine":
        return sine_metrics(w("out"), w("protected"), w("sense"))
    if kind == "over":
        return over_metrics(w("out"), w("sense"), c["volts"])
    if kind == "output":
        jack, drive = step_metrics(w("jack")), step_metrics(w("drive"))
        return {"jack": jack, "drive": drive,
                "sustained_oscillation": jack["sustained_oscillation"] or drive["sustained_oscillation"]}
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
            title = f"MC04-S4 {c['model']} {c['case']} {c['cell']} {c['variant']}"
            name = "-".join((c["model"], c["case"], c["cell"], c["variant"])).replace("/", "_").replace("+", "p")
            if c["kind"] == "loop":
                # One deck holds both injections around one recorded operating point. Solver tolerance
                # (tightest first) and DC seed (none, then nodeset) are tried in a fixed order; the first
                # attempt that converges, keeps its operating point across both AC runs and carries the
                # intended LED current is used, and every attempt is recorded.
                attempts, chosen = [], None
                for tol_name, tol in LOOP_TOLERANCES:
                    for seed in (False, True):
                        lines, vv, vi, opv = c["frag"]("1", seed)
                        deck = header(f"{title} double injection", c["model"]) + lines + ([tol] if tol else [])
                        try:
                            sha, cv, ci, ops = loop_oracle(name, deck, c["analysis"], "1", vv, vi, opv)
                            why = dc_check(ops, c.get("target_A"))
                        except RuntimeError as error:
                            if "Timestep too small" not in str(error):
                                raise
                            sha, cv, ci, ops, why = None, None, None, None, "DC solve failed"
                        attempts.append({"tolerance": tol_name, "seed": "nodeset" if seed else "none",
                                         "result": why or "usable"})
                        if why is None:
                            chosen = {"sha": sha, "cv": cv, "ci": ci, "vv": vv, "vi": vi, "ops": ops,
                                      "tolerance": tol_name, "seed": "nodeset" if seed else "none"}
                            break
                    if chosen:
                        break
                if chosen is None:
                    raise RuntimeError(f"{title}: no usable DC operating point: {attempts}")
                shas = chosen["sha"]
                metrics = loop_rows(chosen["cv"], chosen["vv"], chosen["ci"], chosen["vi"])
                metrics["dc_operating_point"] = {
                    "tolerance": chosen["tolerance"], "seed": chosen["seed"],
                    "values": {k: r(v, 7) for k, v in chosen["ops"]["op1"].items()}, "attempts": attempts}
                if c["case"] == "case5a" and c["model"] == "OPA4196":  # the paper screen models OPA4196 only
                    metrics["paper_screen"] = paper_point(c["cap"], c["bias"], metrics["phase_margin_deg"])
                results.append({"model": c["model"], "case": c["case"], "cell": c["cell"], "variant": c["variant"],
                                "integration": "ac (small signal)", "deck_sha256": shas, "metrics": metrics})
                print(f"{title}: done", flush=True)
                continue
            lines, nodes = c["frag"]("1")
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


def validate_loop_break():
    """Run the same break on a linear two-pole loop whose true T is known in closed form, for three
    load impedances (Zs/Zl = 0.67, 67 and ~0), and report Middlebrook vs voltage-only vs analytic."""
    rows = []
    for rl in (1e3, 10.0, 1e9):
        base = ["MC04-S4 loop-break validation, linear two-pole loop", "E1 o1 0 0 x 1000", "Rp o1 o2 1k",
                "Cp o2 0 1.5915n", "E2 o3 0 o2 0 1", "Rq o3 o4 1k", "Cq o4 0 159.15p", "E3 o5 0 o4 0 1",
                "Ro o5 y 1k", "Rg y 0 2k", f"Rl x 0 {rl:g}"]
        inj, vv, vi = loop_probe("1", "x", "y")
        _, cv, ci, _ = loop_oracle("loop-validation", base + inj, "ac dec 100 10 100meg", "1", vv, vi, ["v(x)"])
        got = loop_rows(cv, vv, ci, vi)
        f = cv["frequency"]
        z = 2e3 * rl / (2e3 + rl)
        true = loop_metrics(f, [1000 * z / (1e3 + z) / ((1 + 1j * x / 1e5) * (1 + 1j * x / 1e6)) for x in f])
        rows.append({"R_load_ohm": rl, "expected_zs_over_zl": r(z and (1e3 * 2e3 / 3e3) / rl, 4),
                     "middlebrook": {k: got[k] for k in ("crossover_Hz", "phase_margin_deg", "zs_over_zl_at_crossover")},
                     "voltage_injection_only": got["voltage_injection_only"],
                     "analytic": {"crossover_Hz": r(true["crossover_Hz"], 4), "phase_margin_deg": r(true["phase_margin_deg"], 4)}})
    return rows


def paper_points():
    """Per-point phase margins of the stage 1b paper screen for U8417 unit 3 (sha256-pinned)."""
    data = PAPER_RESULT.read_bytes()
    if digest(data) != PAPER_SHA256:
        raise RuntimeError("stage 1b paper-screen result changed; review before updating the pin")
    paper = json.loads(data)
    unit = next(u for u in paper["cases"]["default_one_hop"]["units"] if u["ic"] == "U8417" and u["unit"] == 3)
    levels = {lv["bridge_current_A"]: lv for lv in unit["levels"]}
    worst = {row["cable_C_multiple"]: row["worst_pm_deg"] for row in paper["sensitivity_R_SENSE_5600_OPA4196"]["rows"]
             if row["diode_ideality"] == 2.0}
    return paper["cable_C_pF"], levels, worst


def paper_point(cap_key, bias_key, pm):
    cable, levels, worst = paper_points()
    lv = levels[IND_BIAS[bias_key]]
    if cap_key == "0":
        ref, basis = lv["baseline"]["phase_margin_deg"], "paper no-cable point at this current"
    elif cap_key == "7.2p":
        ref, basis = lv["moved"]["phase_margin_deg"], f"paper {cable} pF point at this current"
    else:
        mult = {"15p": 2, "30p": 4}[cap_key]
        ref, basis = worst[mult], f"paper worst over currents at {round(mult * cable, 1)} pF (no per-point value published)"
    return {"paper_pm_deg": ref, "basis": basis, "run_minus_paper_deg": r(pm - ref, 4) if pm is not None else None}


def oscillation_summary(results):
    flags = [x["metrics"].get("sustained_oscillation") for x in results]
    evaluated = [f for f in flags if isinstance(f, bool)]
    n = len(evaluated)
    return {"evaluated_rows": n, "flagged": sum(evaluated),
            "not_evaluated_rows": sum(1 for f in flags if f == NOT_EVALUATED),
            "statement": (f"no sustained oscillation in the {n} evaluated rows" if not any(evaluated)
                          else f"sustained oscillation flagged in {sum(evaluated)} of {n} evaluated rows"),
            "limit": "absolute 1 mV: late-window peak-to-peak for steps and holds, residual after a 1 us moving average for sines",
            "not_evaluated": "AC loop rows (small-signal, no transient) and 10 mV indicator sines where the bridge never leaves its dead band"}


def settle_comparison(results):
    """Where OPA4197 settles slower than OPA4196, by how much (1 mV settle, rise and fall)."""
    idx = {(x["case"], x["cell"], x["variant"], x["model"]): x["metrics"] for x in results}
    slower, worst = [], 0.0
    for (case, cell, variant, model), m6 in idx.items():
        if model != "OPA4196" or (case, cell, variant, "OPA4197") not in idx:
            continue
        m7 = idx[(case, cell, variant, "OPA4197")]
        for where in ("jack", "drive", None):
            a, b = (m6.get(where), m7.get(where)) if where else (m6, m7)
            if not isinstance(a, dict):
                continue
            for k in ("settle_1mV_rise_us", "settle_1mV_fall_us"):
                if isinstance(a.get(k), (int, float)) and isinstance(b.get(k), (int, float)) and b[k] > a[k]:
                    d = b[k] - a[k]
                    worst = max(worst, d)
                    slower.append({"case": case, "cell": cell, "variant": variant, "node": where or "out",
                                   "metric": k, "OPA4196_us": a[k], "OPA4197_us": b[k], "slower_by_us": r(d, 4)})
    return {"OPA4197_slower_rows": slower, "max_slower_by_us": r(worst, 4)}


def report(results, validation):
    return {
        "schema_version": 2,
        "status": "MODEL EVIDENCE ONLY - NO ACCEPTANCE SET; NOT HARDWARE QUALIFICATION",
        "brief": BRIEF, "brief_revision": "Revision 1 after independent review (2026-11-21)",
        "task": "osc-stack-20261114 / MC04-S4-INPUT-BUFFER-SPICE / 20261121-2, extended by MC04-S5-OPA4197-SWAP / 20261121-1",
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
            "switch": f"TMUX7412F modelled as its {R_ON} ohm R_ON bound (fact-fault-switch-t-ron-12v-single), a fixed resistor; no switch capacitance, no R_ON rise within 3 V of VDD, no overvoltage turn-off (the real switch would open at +/-15 V, so case 4 at 15 V bounds clamp stress, it is not the real fault path)",
            "diodes": {name: {"stands_for": who, "spice": params} for name, (who, params) in DIODES.items()},
            "step_edges": "case 1-3 steps have 1 us rise and fall (PULSE tr = tf = 1 us); overshoot and settling hold for that edge, not a faster one. Case 5b steps use 100 ns edges",
            "board_run_capacitance": "case 2 adds 10/30/50 pF to SENSE or BUFFER (50 pF bounds a long run)",
            "harness_load": "the off-board GH harness load on *_BUFFER (cable capacitance and the far-board input) is NOT bounded by case 2 and is not modelled",
            "unpatched": "read as no source on the jack (100 kOhm R_PD only); quiescent output and oscillation check",
            "package": "Neither TI model has package parasitics; SOIC-14 vs TSSOP-14 is not distinguished by any case",
        },
        "diagnostic_targets": "overshoot <= 10 % and settle within 1 mV (sweep_precision.py) are diagnostic labels only, not acceptance; the 45 degree phase-margin criterion is ASSUMED (stage 1b)",
        "conditions": {
            "rails": "+/-12 V ideal", "temperature_C": 27,
            "case1": "PULSE -5..+5 V, 1 us edges, 1 ms period, second cycle measured; 10 V-peak 20 kHz sine; source 1 kOhm or unpatched",
            "case2": "case-1 step, patched, with 10/30/50 pF on SENSE or on BUFFER",
            "case3": "follower driven by an ideal +/-5 V step (1 us edges), 499+499 ohm to jack; open/100k/10k loads; 0/100p/1n cable; metrics at jack and DRIVE",
            "case4": "jack PWL 0 -> +V (200 us) -> 0 -> -V (200 us) -> 0 for V = 12 and 15, source 1 kOhm; phase reversal = output more than 0.5 V beyond SENSE against the drive direction",
            "case5a": "OPA4196 at 0/7.2/15/30 pF and, for MC04-S5, OPA4197 at 0/7.2 pF; loop broken between SENSE (source side) and IN- (load side); Middlebrook double injection (voltage run and current run, T = (Tv Ti - 1)/(Tv + Ti + 2)) with Zs/Zl at crossover, plus the voltage-only result; DC bias MONITOR = I x 5.6 kOhm; margins are per bias point, and the worst is the worst of four bias points",
            "case5a_control": "plain unity follower (IN+ 0 V, no load) of each model, broken the same way",
            "case5b": "OPA4196 at 0/7.2/15/30 pF and, for MC04-S5, OPA4197 at 0/7.2 pF; 20 kHz sines and +/-A steps (100 ns edges, 100 us halves), A = 10 mV/100 mV/1 V/5 V; 0/7.2/15/30 pF on each of LED_A and LED_K",
        },
        "paper_screen": {"path": PAPER_RESULT.relative_to(ROOT).as_posix(), "sha256": PAPER_SHA256,
                         "note": "the paper evaluated 7.22 pF and 2x/4x (14.4 / 28.9 pF); this run uses 7.2 / 15 / 30 pF, so the 30 pF rows compare against 28.9 pF"},
        "loop_break_validation": validation,
        "oscillation": oscillation_summary(results),
        "settling_OPA4197_vs_OPA4196": settle_comparison(results),
        "results": results,
        "deltas": deltas(results),
        "model_limit": "TI macro-models predict modeled behavior only; package parasitics, layout, tolerance, temperature, the real switch and diodes, the off-board harness, and bench stability remain NOT RUN.",
    }


def run(*, check: bool = False, offline: bool = False) -> None:
    models(offline=offline)
    results = run_all()
    validation = validate_loop_break()
    body = json.dumps(report(results, validation), indent=2) + "\n"
    if check:
        if not OUT.exists() or OUT.read_text() != body:
            raise RuntimeError("input-buffer vendor report drift")
    else:
        OUT.write_text(body)
    print(f"Input-buffer TI-model run: {len(results)} rows; {oscillation_summary(results)['statement']}")


if __name__ == "__main__":
    run(check="--check" in sys.argv, offline="--offline" in sys.argv)
