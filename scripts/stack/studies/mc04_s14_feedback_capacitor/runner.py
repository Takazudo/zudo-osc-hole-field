"""MC04-S14 multi-analysis runner (byte copy of the S13 runner, changed as listed in the S14 report).

One deck is one ngspice invocation through the pinned oracle.

The deck is written with `@D@` in place of its data-file stem; the SHA-256 of that text is the deck key, and the
stem is the first 20 hex digits of it, so byte-identical decks share one key. Every run goes through
`bash scripts/kicad/run.sh ngspice -b <deck>` from the repository root with a 600 s timeout, and through the imported
`check_oracle_result`; the deck text must be unchanged afterwards and every data file fresh, non-empty and finite.
On a timeout every container of the pinned image is killed and the list must be empty before the next deck.

Addendum B: every operating point is written in full precision (`set numdgt=15`, `wrdata ... all`); a seed deck is the
same netlist at zero stray with `op` (or a DC ramp of the bias source) and `wrnodev`, and its `.ic` lines become
`.nodeset` lines of every evaluation deck of that netlist.
"""
from __future__ import annotations

import bisect
import cmath
import gzip
import hashlib
import math
import re
import subprocess
import time
from pathlib import Path

from cells import ROOT
from guard import IMAGE, kill_pinned_containers, pinned_containers
from design.spec.modules.spice_trace import check_oracle_result

WORK = ROOT / ".circuit-cache/sources/mc04-s14"  # S14: own working directory; the S13 cache is read only
TIMEOUT_S = 600
TIMEOUT_G_S = 120  # S14 brief "How the oracle is invoked": 120 s per class G deck
INVOCATIONS = {"count": 0}
LEDGER = {"hook": None, "kind": "eval"}  # S14: every invocation is logged before it starts (N12)
DEADLINE = {"t": None}  # slice deadline (epoch s): no deck starts unless its full timeout fits before it


class SliceDeadline(Exception):
    """No room for one more deck, with its whole timeout, before the slice deadline."""


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


EXTERNAL = re.compile(r"[a-z0-9_]+")  # top-level node names; internal model nodes carry a dot, branches a '#'
OP_ALL = ["set numdgt=15", "op", "wrdata @D@.{name}.dat all", "set numdgt=8"]


def op_lines(name):
    return [x.replace("{name}", name) for x in OP_ALL]


def external_nodes(tab):
    """Full-precision values (last row) of every top-level node in a `wrdata ... all` table from read_table().
    Column 0 is the plot scale; when it is a node it is written again later, and read_table() names that "#imag"."""
    keys = list(tab)
    out = {}
    for k in keys[1:]:
        nm = k[:-5] if k.endswith("#imag") and k[:-5] == keys[0] else k
        if EXTERNAL.fullmatch(nm):
            out[nm] = tab[k][-1]
    if not out:
        raise OracleError("operating-point record has no external node")
    return out


def last_log(key):
    p = WORK / f"{key[:20]}.log"
    return p.read_text() if p.exists() else ""


def seed_control(method="op", src=None, value=None):
    if method == "op":
        an = "op"
    else:
        an = f"dc {src} 0 {value:.9g} {value / 20:.9g}"  # 0 to the nominal value in 20 steps (Addendum B2.2)
    return [".control", "set noinit", "set wr_singlescale", "set wr_vecnames", "set numdgt=15", an,
            "wrdata @D@.ref.dat all", "wrnodev @D@.nodes.txt", "quit", ".endc", ".end", ""]


SEED_INVOCATIONS = {"count": 0, "cap": 180}  # S14 "Deck caps": at most 180 seed invocations; reaching it is STOP 3


class SeedInvocationCap(SystemExit):
    pass


def seed_text(netlist_text, method="op", src=None, value=None, nodeset=()):
    return netlist_text.rstrip("\n") + "\n" + "".join(x + "\n" for x in nodeset) + "\n".join(
        seed_control(method, src, value))


def run_seed(netlist_text, method="op", src=None, value=None, nodeset=(), timeout=None):
    """Run one seed deck. Returns (key, reference {node: V}, nodeset lines, transient_op, wall, text).
    `nodeset` is given only for the confirmation pass of Addendum C2.2."""
    if SEED_INVOCATIONS["count"] >= SEED_INVOCATIONS["cap"]:
        raise SeedInvocationCap(f"STOP 3: seed-deck invocation cap {SEED_INVOCATIONS['cap']} reached")
    SEED_INVOCATIONS["count"] += 1
    text = seed_text(netlist_text, method, src, value, nodeset)
    key = deck_key(text)
    nodes = WORK / f"{key[:20]}.nodes.txt"
    nodes.unlink(missing_ok=True)
    kind, LEDGER["kind"] = LEDGER["kind"], "seed"
    try:
        key, tables, wall = run(text, ["ref"], keep=False, timeout=timeout)
    finally:
        LEDGER["kind"] = kind
    ref = external_nodes(tables["ref"])
    (WORK / f"{key[:20]}.ref.dat").unlink()
    if not nodes.exists():
        raise OracleError(f"seed {key[:20]}: wrnodev wrote nothing")
    ics = [ln for ln in nodes.read_text().splitlines() if ln.startswith(".ic ")]
    nodes.unlink()
    if not ics:
        raise OracleError(f"seed {key[:20]}: no .ic line")
    nodeset = [".nodeset " + ln[len(".ic "):] for ln in ics]
    return key, ref, nodeset, "Transient op" in last_log(key), wall, text


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


AMP_SUBCKTS = {"OPAX196": (1, 2), "OPAX197": (1, 2), "LM13700/NS": (3, 4)}  # input pin positions on the X line


def floating_inputs(deck_text):
    """Addendum C1 / M19: amplifier and OTA input pins that sit on a node with no other element line, in the
    complete deck text (title, .nodeset and the control block are not elements)."""
    body = deck_text.split("\n.control\n")[0].splitlines()[1:]
    elems = [ln.split() for ln in body if ln.strip() and not ln.lstrip().startswith((".", "*", "+"))]
    count = {}
    for f in elems:
        if f[0][0].upper() == "X":
            nodes = f[1:-1]
        elif f[0][0].upper() in "RCLVIDBEFGH":
            nodes = f[1:3] if f[0][0].upper() not in "EG" else f[1:5]
        else:
            nodes = f[1:3]
        for n in nodes:
            count[n] = count.get(n, 0) + 1
    bad = []
    for f in elems:
        if f[0][0].upper() == "X" and f[-1].upper() in AMP_SUBCKTS:
            for pos in AMP_SUBCKTS[f[-1].upper()]:
                n = f[pos]
                if n != "0" and count.get(n, 0) < 2:
                    bad.append(f"{f[0]} pin {pos} on lone node {n}")
    return bad


def run(text: str, files: list[str], *, keep=True, timeout=None):
    """Run one deck. `text` holds `@D@` where data paths go; `files` are the data-file suffixes it writes.

    Returns (key, {suffix: table}, wall seconds)."""
    WORK.mkdir(parents=True, exist_ok=True)
    key = deck_key(text)
    lone = floating_inputs(text)
    if lone:
        raise RuntimeError(f"deck builder: input pin alone on a node ({'; '.join(lone)})")
    stem = key[:20]
    rel = (WORK / stem).relative_to(ROOT).as_posix()
    body = text.replace("@D@", rel)
    deck = WORK / f"{stem}.cir"
    deck.write_text(body)
    paths = {s: WORK / f"{stem}.{s}.dat" for s in files}
    for p in paths.values():
        p.unlink(missing_ok=True)
    if pinned_containers():  # "Stopping the oracle": docker kill before the deck, and the list must be empty
        survivors = kill_pinned_containers()
        if survivors:
            raise SystemExit(f"STOP 3: container survived docker kill: {survivors}")
    timeout = timeout or TIMEOUT_S
    if DEADLINE["t"] is not None and time.time() + timeout + 60 > DEADLINE["t"]:
        raise SliceDeadline("no room for one more deck before the slice deadline")
    if LEDGER["hook"]:
        LEDGER["hook"](LEDGER["kind"], key)  # counted before it runs: an interrupted deck is counted too
    INVOCATIONS["count"] += 1
    t0 = time.time()
    try:
        proc = subprocess.run(["bash", "scripts/kicad/run.sh", "ngspice", "-b", deck.relative_to(ROOT).as_posix()],
                              cwd=ROOT, capture_output=True, text=True, timeout=timeout)
    except subprocess.TimeoutExpired:
        survivors = kill_pinned_containers()
        if survivors:
            raise SystemExit(f"STOP: container survived docker kill: {survivors}")
        raise OracleError(f"deck {stem} timed out after {timeout} s")
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


def probe_lines(x="xinm", y="inm"):
    return [f"Vmy n1 {y} 0", f"Vinj {x} n1 DC 0 AC 1", "Iinj 0 n1 DC 0 AC 0"]


def loop_netlist(netlist_lines, *, x="xinm", y="inm"):
    """The loop deck's netlist (no tolerance, no seed, no control): what its seed deck runs."""
    return "\n".join(netlist_lines + probe_lines(x, y))


def loop_text(netlist_lines, *, x="xinm", y="inm", tol=None, ac=LOOP_AC, nodeset=()):
    """The sequence of the retained loop_oracle(): op, AC voltage injection, AC current injection, op again.
    Both operating points are written in full precision for the seed comparison (Addendum B2.5)."""
    vv, vi = ["v(n1)", f"v({x})"], ["i(Vmy)", "i(Vinj)"]
    lines = netlist_lines + probe_lines(x, y) + ([tol] if tol else []) + list(nodeset) + [
        ".control", "set noinit", "set wr_singlescale", "set wr_vecnames", "option numdgt=8",
        *op_lines("op1"),
        ac, "wrdata @D@.v.dat " + " ".join(vv),
        "alter @vinj[acmag]=0", "alter @iinj[acmag]=1",
        ac, "wrdata @D@.i.dat " + " ".join(vi),
        *op_lines("op2"),
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
            "f_peak_Hz": r(f[mag.index(peak)]), "gain_20k_dB": r(g20), "phase_20k_deg": r(p20),
            "f_3dB_Hz": r(f_3db(f, mag, lf))}


def f_3db(f, mag, lf):
    """S14 cost table: first frequency, log-interpolated, where |H| falls below |H(LF)|/sqrt(2)."""
    lim = lf / math.sqrt(2)
    for k in range(1, len(f)):
        if mag[k] < lim <= mag[k - 1]:
            fr = (math.log(mag[k - 1]) - math.log(lim)) / (math.log(mag[k - 1]) - math.log(mag[k]))
            return f[k - 1] * (f[k] / f[k - 1]) ** fr
    return None


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


SETTLED_FRACTION = 0.05  # S3: the last tenth of a K4 window is settled when its peak-to-peak <= 5 % of the step
UNSETTLED = "NOT EVALUATED: window not settled"


def overshoot(w, edge, end):
    """S3: final value = mean of the last tenth; no percentage unless that tenth is settled."""
    t, y = w.window(edge, end)
    pre = w.mean(edge - 5e-6, edge)
    _, tail = w.window(end - 0.1 * (end - edge), end)
    final = sum(tail) / len(tail)
    span = final - pre
    pp = max(tail) - min(tail)
    out = {"span_V": r(span), "tail_pp_V": r(pp)}
    if abs(span) < 1e-6:
        return {**out, "overshoot_percent": None, "status": "NOT EVALUATED: no step at the output"}
    sgn = 1 if span > 0 else -1
    peak = first_peak(t, y, pre, sgn, span)
    out["first_peak_V"] = r(peak)
    if pp > SETTLED_FRACTION * abs(span):
        return {**out, "overshoot_percent": None, "status": UNSETTLED}
    over = max(0.0, max((v - final) * sgn for v in y)) / abs(span) * 100
    return {**out, "overshoot_percent": r(over, 5), "status": "OK"}


def first_peak(t, y, pre, sgn, span):
    """First local extremum in the step direction after the output has covered half the step (recorded only)."""
    k0 = next((k for k, v in enumerate(y) if (v - pre) * sgn >= abs(span) / 2), None)
    if k0 is None:
        return None
    for k in range(k0 + 1, len(y) - 1):
        if (y[k] - y[k - 1]) * sgn >= 0 and (y[k + 1] - y[k]) * sgn < 0:
            return y[k]
    return None


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


K5_TAU_MULTIPLE = 12  # S4: a class C late window starts 12 zero-stray time constants after its edge


def late_starts(windows, tau0=None):
    """S4: the start of each late window. Class C (tau0 given): edge + 12 tau0; otherwise the second half."""
    return [(edge + K5_TAU_MULTIPLE * tau0 if tau0 is not None else edge + (end - edge) / 2, end - 1e-6)
            for edge, end, _ in windows]


def check_late_windows(windows, starts, tau0):
    """N5: a class C late window that starts earlier than 12 tau0 after its edge, or past its end, is rejected."""
    for (edge, end, _), (a, b) in zip(windows, starts):
        if tau0 is not None and a - edge < K5_TAU_MULTIPLE * tau0 * (1 - 1e-9):
            raise ValueError(f"class C K5 window starts {(a - edge) / tau0:.2f} time constants after its edge")
        if not edge < a < b <= end:
            raise ValueError("K5 late window outside its hold")


def late_residual(w, windows, tau0=None):
    """S4: peak-to-peak with the mean removed only (no polynomial detrend), worst window."""
    starts = late_starts(windows, tau0)
    check_late_windows(windows, starts, tau0)
    out = []
    for a, b in starts:
        _, y = w.window(a, b)
        if len(y) < 2:
            raise ValueError("K5 late window holds fewer than two samples")
        m = sum(y) / len(y)
        out.append(max(v - m for v in y) - min(v - m for v in y))
    return max(out)


def sine_residual(w, t0, t1, f, nh=10):
    """S4: residual after a least-squares fit of the mean, the fundamental and harmonics 2 to 10 (no linear term),
    over the second half of the sine."""
    a = t0 + (t1 - t0) / 2
    t, y = w.window(a, t1 - 1e-7)
    basis = [lambda x: 1.0]
    for k in range(1, nh + 1):
        basis.append(lambda x, k=k: math.sin(2 * math.pi * k * f * x))
        basis.append(lambda x, k=k: math.cos(2 * math.pi * k * f * x))
    return lsq_residual_pp(t, y, basis), max(y), min(y)


CLIP_BAND_V = 11.0  # S4: an output inside 1 V of either +/-12 V rail is clipped


def swing(w):
    return min(w.y), max(w.y)


def clipped(lo, hi):
    return hi >= CLIP_BAND_V or lo <= -CLIP_BAND_V


def k5_scale(vq, lo, hi):
    """S4: 0.9 x (11 V - |Vq|) / (peak excursion from Vq), three significant digits."""
    exc = max(abs(hi - vq), abs(lo - vq))
    return float(f"{0.9 * (CLIP_BAND_V - abs(vq)) / exc:.3g}")


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


def closed_metrics(circuit, corner, P, tables, *, k5_only=False):
    """S13 measurements with S3 (settled K4 window), S4 (K5 windows and residuals, output swing) applied.
    `k5_only`: a rescaled second deck (S4 "Clipping") supplies K5 and the swing only."""
    cls = circuit["class"]
    nodes = ["out"] + (["harness"] if cls == "A" else [])
    m = {}
    t1 = tables["t1"]
    waves = {node: Wave(t1["time"], t1[f"v({node})"]) for node in nodes}
    tau0 = P.get("tau0_s") if cls == "C" else None
    m["k5"] = {}
    if "K5_step" in P["windows"]:
        for node in nodes:
            m["k5"][f"step@{node}"] = r(late_residual(waves[node], P["windows"]["K5_step"], tau0))
    if "K5_load" in P["windows"]:
        m["k5"]["load@out"] = r(late_residual(waves["out"], P["windows"]["K5_load"]))
    if P.get("sine"):
        sn = P["sine"]
        for node in nodes:
            res, hi, lo = sine_residual(waves[node], sn["t0"], sn["t1"], sn["f"])
            m["k5"][f"sine@{node}"] = r(res)
            m.setdefault("sine_swing", {})[node] = [r(lo), r(hi)]
    lo, hi = swing(waves["out"])
    m["swing_out_V"] = [r(lo), r(hi)]
    m["clipped"] = clipped(lo, hi)
    if k5_only:
        return m
    paths = ["buf", "rem"] if cls == "B" else [P["main"]]
    m["ac"] = {}
    for k, role in enumerate(paths):
        for node in nodes:
            m["ac"][f"{role}@{node}"] = ac_metrics(tables[f"ac{k}"], node)
    m["noise"] = {node: noise_metrics(tables[f"noise{k}"]) for k, node in enumerate(nodes)}
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
    if "K6" in P["windows"]:
        if cls == "C":
            w = waves["out"]
            m["k6"] = [r(settle(w, e, end)) for e, end, _ in P["windows"]["K6"]]
            e, end, _ = P["windows"]["K6"][0]
            m["k8_tau_s"] = r(tau_fit(w, e, end, P["tau0_s"]), 9)
            m["resolution_fraction"] = r(P["resolution_fraction"])
            m["k6_resolution_s"] = r(P["tran"][0]["tmax"])
        else:
            t2 = tables["t2"]
            w = Wave(t2["time"], t2["v(out)"])
            m["k6"] = [r(settle(w, e, end)) for e, end, _ in P["windows"]["K6"]]
            m["k6_resolution_s"] = r(P["tran"][-1]["tmax"])
    if "K6_load" in P["windows"]:
        t2 = tables["t2"]
        w = Wave(t2["time"], t2["v(out)"])
        m["k6"] = [r(settle(w, e, end)) for e, end, _ in P["windows"]["K6_load"]]
        m["k6_resolution_s"] = r(P["tran"][-1]["tmax"])
    return m
