"""MC04-S13 multi-analysis runner: one deck is one ngspice invocation through the pinned oracle.

The deck is written with `@D@` in place of its data-file stem; the SHA-256 of that text is the deck key, and the
stem is the first 20 hex digits of it, so byte-identical decks share one key. Every run goes through
`bash scripts/kicad/run.sh ngspice -b <deck>` from the repository root with a 600 s timeout, and through the imported
`check_oracle_result`; the deck text must be unchanged afterwards and every data file fresh, non-empty and finite.
On a timeout every container of the pinned image is killed and the list must be empty before the next deck.
"""
from __future__ import annotations

import bisect
import cmath
import gzip
import hashlib
import math
import subprocess
import time
from pathlib import Path

from cells import ROOT
from guard import IMAGE, kill_pinned_containers, pinned_containers
from design.spec.modules.spice_trace import check_oracle_result

WORK = ROOT / ".circuit-cache/sources/mc04-s13"
TIMEOUT_S = 600
INVOCATIONS = {"count": 0}


class OracleError(RuntimeError):
    pass


def deck_key(text_with_placeholder: str) -> str:
    return hashlib.sha256(text_with_placeholder.encode()).hexdigest()


def read_table(path: Path):
    rows = path.read_text().split("\n")
    names = []
    for nm in rows[0].split():  # a complex vector is written as two same-named columns: real, imaginary
        names.append(nm + "#imag" if nm in names else nm)
    table = [[float(x) for x in r.split()] for r in rows[1:] if r.strip()]
    if not table or not all(math.isfinite(x) for r in table for x in r):
        raise OracleError(f"{path.name}: empty or nonfinite data")
    return {nm: [r[i] for r in table] for i, nm in enumerate(names)}


def ensure_spiceinit():
    init = ROOT / ".spiceinit"
    if init.exists():
        if init.read_text() != "set ngbehavior=ps\n":
            raise OracleError("refusing to use a foreign .spiceinit")
        return False
    init.write_text("set ngbehavior=ps\n")
    return True


def remove_spiceinit():
    init = ROOT / ".spiceinit"
    if init.exists() and init.read_text() == "set ngbehavior=ps\n":
        init.unlink()


def run(text: str, files: list[str], *, keep=True):
    """Run one deck. `text` holds `@D@` where data paths go; `files` are the data-file suffixes it writes.

    Returns (key, {suffix: table}, wall seconds)."""
    WORK.mkdir(parents=True, exist_ok=True)
    key = deck_key(text)
    stem = key[:20]
    rel = (WORK / stem).relative_to(ROOT).as_posix()
    body = text.replace("@D@", rel)
    deck = WORK / f"{stem}.cir"
    deck.write_text(body)
    paths = {s: WORK / f"{stem}.{s}.dat" for s in files}
    for p in paths.values():
        p.unlink(missing_ok=True)
    if pinned_containers():
        raise OracleError("a container of the pinned image is running before the deck")
    INVOCATIONS["count"] += 1
    t0 = time.time()
    try:
        proc = subprocess.run(["bash", "scripts/kicad/run.sh", "ngspice", "-b", deck.relative_to(ROOT).as_posix()],
                              cwd=ROOT, capture_output=True, text=True, timeout=TIMEOUT_S)
    except subprocess.TimeoutExpired:
        survivors = kill_pinned_containers()
        if survivors:
            raise SystemExit(f"STOP: container survived docker kill: {survivors}")
        raise OracleError(f"deck {stem} timed out after {TIMEOUT_S} s")
    wall = time.time() - t0
    (WORK / f"{stem}.log").write_text(proc.stdout + "\n" + proc.stderr)
    if deck.read_text() != body:
        raise OracleError(f"deck {stem} changed during execution")
    for p in paths.values():
        check_oracle_result(proc, p)
    tables = {s: read_table(p) for s, p in paths.items()}
    if keep:
        for p in paths.values():
            with open(p, "rb") as f, gzip.open(str(p) + ".gz", "wb") as g:
                g.write(f.read())
            p.unlink()
    return key, tables, wall


# ------------------------------------------------------------------------------------------------ loop deck

LOOP_TOLERANCES = (("reltol=1e-6 vntol=1e-9 abstol=1e-15", ".options reltol=1e-6 vntol=1e-9 abstol=1e-15"),
                   ("reltol=1e-5", ".options reltol=1e-5"), ("ngspice default", None))
LOOP_AC = "ac dec 100 10 1g"


def loop_text(netlist_lines, op_vectors, *, x="xinm", y="inm", tol=None, ac=LOOP_AC):
    """The sequence of the retained loop_oracle(): op, AC voltage injection, AC current injection, op again."""
    probe = [f"Vmy n1 {y} 0", f"Vinj {x} n1 DC 0 AC 1", "Iinj 0 n1 DC 0 AC 0"]
    vv, vi = ["v(n1)", f"v({x})"], ["i(Vmy)", "i(Vinj)"]
    lines = netlist_lines + probe + ([tol] if tol else []) + [
        ".control", "set noinit", "set wr_singlescale", "set wr_vecnames", "option numdgt=8",
        "op", "wrdata @D@.op1.dat " + " ".join(op_vectors),
        ac, "wrdata @D@.v.dat " + " ".join(vv),
        "alter @vinj[acmag]=0", "alter @iinj[acmag]=1",
        ac, "wrdata @D@.i.dat " + " ".join(vi),
        "op", "wrdata @D@.op2.dat " + " ".join(op_vectors),
        "quit", ".endc", ".end", ""]
    return "\n".join(lines), vv, vi


def middlebrook(tv, ti):
    return (tv * ti - 1) / (tv + ti + 2)


def complex_col(cols, name):
    return [complex(a, b) for a, b in zip(cols[name], cols[name + "#imag"])]


def loop_gain(cv, ci, vv, vi):
    if cv["frequency"] != ci["frequency"]:
        raise OracleError("loop runs use different frequency grids")
    vy, vx = complex_col(cv, vv[0]), complex_col(cv, vv[1])
    iy, ix = complex_col(ci, vi[0]), [-z for z in complex_col(ci, vi[1])]  # I(n->x) = -i(Vinj)
    tv = [-a / b for a, b in zip(vy, vx)]
    ti = [a / b for a, b in zip(iy, ix)]
    return cv["frequency"], [middlebrook(a, b) for a, b in zip(tv, ti)], tv


def unwrap_deg(values):
    import cmath
    out, prev = [], None
    for z in values:
        p = math.degrees(cmath.phase(z))
        if prev is not None:
            while p - prev > 180:
                p -= 360
            while p - prev < -180:
                p += 360
        out.append(p)
        prev = p
    return out


def margins(freq, loop):
    """K1/K2 inputs: every unity crossing (log-interpolated) with its phase margin 180 + phase(T); every phase
    crossing (180 + phase = 0 mod 360) above the first unity crossing with |T| < 1, and its gain margin."""
    ph, mag = unwrap_deg(loop), [abs(z) for z in loop]
    unity, phase_x = [], []
    for k in range(1, len(mag)):
        a, b = mag[k - 1], mag[k]
        if (a - 1) * (b - 1) < 0:
            fr = math.log(a) / (math.log(a) - math.log(b))
            f = freq[k - 1] * (freq[k] / freq[k - 1]) ** fr
            pm = 180 + ph[k - 1] + (ph[k] - ph[k - 1]) * fr
            unity.append({"f_Hz": f, "pm_deg": ((pm + 180) % 360) - 180, "falling": b < a})
    for k in range(1, len(ph)):
        a, b = 180 + ph[k - 1], 180 + ph[k]
        na, nb = math.floor(a / 360 + 0.5), math.floor(b / 360 + 0.5)  # nearest multiple of 360 crossed
        for m in range(min(na, nb), max(na, nb) + 1):
            t = 360 * m
            if (a - t) * (b - t) < 0:
                fr = (t - a) / (b - a)
                f = freq[k - 1] * (freq[k] / freq[k - 1]) ** fr
                g = math.exp(math.log(mag[k - 1]) + (math.log(mag[k]) - math.log(mag[k - 1])) * fr)
                phase_x.append({"f_Hz": f, "gain_margin_dB": -20 * math.log10(g)})
    return {"dc_loop_gain_dB": 20 * math.log10(mag[0]), "unity": unity, "phase_crossings": phase_x}


# ------------------------------------------------------------------------------------------------ measurements
# Criterion measurements on one deck's tables (brief Ruling 2 and the stimulus table).

PM_LIMIT, GM_LIMIT, PEAK_LIMIT, OVERSHOOT_LIMIT, OSC_LIMIT = 45.0, 10.0, 3.0, 25.0, 1e-3
SETTLE_LIMIT_S, REL_LIMIT, K7_DB, K7_DEG, K9_DB = 1e-3, 0.01, 0.1, 2.0, 1.0
GM_FMAX = 100e6


def r(x, sig=6):
    if x is None or isinstance(x, bool) or not isinstance(x, float) or x == 0 or not math.isfinite(x):
        return x
    return float(f"{x:.{sig}g}")


# ------------------------------------------------------------------------------------------------ loop

def loop_metrics(cv, ci, vv, vi):
    f, T, tv = loop_gain(cv, ci, vv, vi)
    m = margins(f, T)
    falling = [u for u in m["unity"] if u["falling"]]
    first = falling[0]["f_Hz"] if falling else None
    pm = min((u["pm_deg"] for u in m["unity"]), default=None)
    gms = [p for p in m["phase_crossings"] if first is not None and p["f_Hz"] > first and p["f_Hz"] < GM_FMAX
           and p["gain_margin_dB"] > 0]
    gm = min((p["gain_margin_dB"] for p in gms), default=None)
    return {"phase_margin_deg": r(pm), "crossover_Hz": r(first), "unity_crossings": len(m["unity"]),
            "all_unity": [{k: r(v) if isinstance(v, float) else v for k, v in u.items()} for u in m["unity"][:6]],
            "gain_margin_dB": r(gm), "phase_crossings_below_100MHz": len(gms),
            "dc_loop_gain_dB": r(m["dc_loop_gain_dB"])}


def k1_k2(m):
    pm = m["phase_margin_deg"]
    k1 = pm is not None and pm >= PM_LIMIT
    k2 = m["gain_margin_dB"] is None or m["gain_margin_dB"] >= GM_LIMIT
    return k1, k2


# ------------------------------------------------------------------------------------------------ AC / noise

def complex_col(cols, name):
    return [complex(a, b) for a, b in zip(cols[name], cols[name + "#imag"])]


def unwrap(values):
    out, prev = [], None
    for z in values:
        p = math.degrees(cmath.phase(z))
        if prev is not None:
            while p - prev > 180:
                p -= 360
            while p - prev < -180:
                p += 360
        out.append(p)
        prev = p
    return out


def ac_metrics(cols, node):
    f = cols["frequency"]
    h = complex_col(cols, f"v({node})")
    mag = [abs(z) for z in h]
    lf = mag[0]
    ph = unwrap(h)
    lf_ph = ph[0]
    ph = [p - 360 * round(lf_ph / 360) for p in ph]
    k = bisect.bisect_left(f, 20e3)
    fr = (math.log(20e3) - math.log(f[k - 1])) / (math.log(f[k]) - math.log(f[k - 1]))
    db = lambda x: 20 * math.log10(x) if x > 0 else -400.0  # noqa: E731
    g20 = db(mag[k - 1]) + (db(mag[k]) - db(mag[k - 1])) * fr
    p20 = ph[k - 1] + (ph[k] - ph[k - 1]) * fr
    peak = max(mag)
    return {"lf_gain": r(lf if h[0].real >= 0 else -lf), "peaking_dB": r(db(peak / lf) if lf > 1e-9 else None),
            "f_peak_Hz": r(f[mag.index(peak)]), "gain_20k_dB": r(g20), "phase_20k_deg": r(p20)}


def noise_metrics(cols):
    f = cols["frequency"]
    s = cols["onoise_spectrum"]
    total = sum((f[k] - f[k - 1]) * (s[k] ** 2 + s[k - 1] ** 2) / 2 for k in range(1, len(f)))
    return {"integrated_uVrms": r(math.sqrt(total) * 1e6), "band_Hz": [f[0], f[-1]]}


# ------------------------------------------------------------------------------------------------ transient

class Wave:
    def __init__(self, t, y):
        self.t, self.y = t, y

    def window(self, a, b):
        i, j = bisect.bisect_left(self.t, a), bisect.bisect_right(self.t, b)
        return self.t[i:j], self.y[i:j]

    def mean(self, a, b):
        _, y = self.window(a, b)
        return sum(y) / len(y)


def overshoot(w, edge, end):
    t, y = w.window(edge, end)
    pre = w.mean(edge - 5e-6, edge)
    final = w.mean(end - 0.1 * (end - edge), end)
    span = final - pre
    if abs(span) < 1e-6:
        return {"overshoot_percent": None, "span_V": r(span)}
    sgn = 1 if span > 0 else -1
    over = max(0.0, max((v - final) * sgn for v in y)) / abs(span) * 100
    return {"overshoot_percent": r(over, 5), "span_V": r(span)}


def detrended_pp(t, y, order=2):
    n = len(t)
    if n < order + 2:
        return None
    t0, sc = t[0], (t[-1] - t[0]) or 1.0
    xs = [(x - t0) / sc for x in t]
    return lsq_residual_pp(xs, y, [lambda x, p=p: x ** p for p in range(order + 1)])


def lsq_residual_pp(xs, y, basis):
    m = len(basis)
    a = [[0.0] * m for _ in range(m)]
    b = [0.0] * m
    rows = [[f(x) for f in basis] for x in xs]
    for row, v in zip(rows, y):
        for i in range(m):
            b[i] += row[i] * v
            for j in range(m):
                a[i][j] += row[i] * row[j]
    coef = solve(a, b)
    res = [v - sum(c * q for c, q in zip(coef, row)) for row, v in zip(rows, y)]
    return max(res) - min(res)


def solve(a, b):
    n = len(b)
    m = [row[:] + [b[i]] for i, row in enumerate(a)]
    for c in range(n):
        p = max(range(c, n), key=lambda i: abs(m[i][c]))
        m[c], m[p] = m[p], m[c]
        if abs(m[c][c]) < 1e-300:
            raise ValueError("singular fit")
        for i in range(n):
            if i != c:
                f = m[i][c] / m[c][c]
                for j in range(c, n + 1):
                    m[i][j] -= f * m[c][j]
    return [m[i][n] / m[i][i] for i in range(n)]


def late_residual(w, windows, late=100e-6):
    out = []
    for edge, end, _ in windows:
        a = max(edge + (end - edge) / 2, end - late)
        t, y = w.window(a, end - 1e-6)
        out.append(detrended_pp(t, y))
    return max(x for x in out if x is not None)


def sine_residual(w, t0, t1, f, nh=10):
    a = t0 + (t1 - t0) / 2
    t, y = w.window(a, t1 - 1e-7)
    basis = [lambda x: 1.0, lambda x: x - a]
    for k in range(1, nh + 1):
        basis.append(lambda x, k=k: math.sin(2 * math.pi * k * f * x))
        basis.append(lambda x, k=k: math.cos(2 * math.pi * k * f * x))
    return lsq_residual_pp(t, y, basis), max(y), min(y)


def settle(w, edge, end, band=1e-3):
    """Time after `edge` at which |v - final| last exceeds `band`, linearly interpolated between samples."""
    t, y = w.window(edge, end)
    final = w.mean(end - 0.01 * (end - edge), end)
    e = [abs(v - final) - band for v in y]
    last = max((k for k, x in enumerate(e) if x > 0), default=None)
    if last is None:
        return 0.0
    if last >= len(e) - 1:
        return None
    a, b = e[last], e[last + 1]
    tc = t[last] + (t[last + 1] - t[last]) * a / (a - b)
    return tc - edge


def tau_fit(w, edge, end, tau0):
    final = w.mean(end - 0.01 * (end - edge), end)
    t, y = w.window(edge + tau0, edge + 5 * tau0)
    pts = [(x, math.log(abs(v - final))) for x, v in zip(t, y) if abs(v - final) > 0]
    n = len(pts)
    mx = sum(p[0] for p in pts) / n
    my = sum(p[1] for p in pts) / n
    sxy = sum((p[0] - mx) * (p[1] - my) for p in pts)
    sxx = sum((p[0] - mx) ** 2 for p in pts)
    return -sxx / sxy


def closed_metrics(circuit, corner, P, tables):
    cls, sub = circuit["class"], circuit["subclass"]
    nodes = ["out"] + (["harness"] if cls == "A" else [])
    m = {"op": {k: r(v[0]) for k, v in tables["op"].items() if k.startswith("v(")}}
    paths = ["buf", "rem"] if cls == "B" else [P["main"]]
    m["ac"] = {}
    for k, role in enumerate(paths):
        for node in nodes:
            m["ac"][f"{role}@{node}"] = ac_metrics(tables[f"ac{k}"], node)
    m["noise"] = {node: noise_metrics(tables[f"noise{k}"]) for k, node in enumerate(nodes)}
    t1 = tables["t1"]
    waves = {node: Wave(t1["time"], t1[f"v({node})"]) for node in nodes}
    m["k4"] = {}
    wins = P["windows"]["K4"]
    if isinstance(wins, dict):
        for role, ws in wins.items():
            for node in nodes:
                m["k4"][f"{role}@{node}"] = [overshoot(waves[node], e, end) for e, end, _ in ws]
    else:
        m["k4"]["main@out"] = [overshoot(waves["out"], e, end) for e, end, _ in wins]
    if cls == "C":
        ti = tables["tinj"]
        wi = Wave(ti["time"], ti["v(out)"])
        m["k4"]["inj@out"] = [overshoot(wi, e, end) for e, end, _ in P["windows"]["K4_inj"]]
    m["k5"] = {}
    if "K5_step" in P["windows"]:
        for node in nodes:
            m["k5"][f"step@{node}"] = r(late_residual(waves[node], P["windows"]["K5_step"]))
    if "K5_load" in P["windows"]:
        m["k5"]["load@out"] = r(late_residual(waves["out"], P["windows"]["K5_load"]))
    if P.get("sine"):
        s = P["sine"]
        for node in nodes:
            res, hi, lo = sine_residual(waves[node], s["t0"], s["t1"], s["f"])
            m["k5"][f"sine@{node}"] = r(res)
            m.setdefault("sine_swing", {})[node] = [r(lo), r(hi)]
    if "K6" in P["windows"]:
        if cls == "C":
            w = waves["out"]
            m["k6"] = [r(settle(w, e, end)) for e, end, _ in P["windows"]["K6"]]
            e, end, _ = P["windows"]["K6"][0]
            m["k8_tau_s"] = r(tau_fit(w, e, end, P["tau0_s"]), 9)
            m["resolution_fraction"] = r(P["resolution_fraction"])
        else:
            t2 = tables["t2"]
            w = Wave(t2["time"], t2["v(out)"])
            m["k6"] = [r(settle(w, e, end)) for e, end, _ in P["windows"]["K6"]]
    if "K6_load" in P["windows"]:
        t2 = tables["t2"]
        w = Wave(t2["time"], t2["v(out)"])
        m["k6"] = [r(settle(w, e, end)) for e, end, _ in P["windows"]["K6_load"]]
    return m
