"""MC04-S14 driver: a 10 pF feedback capacitor what-if, the class G specification cell, and a corrected-test
re-score of classes A, C and D of S13 (brief Revision 3, DS-181 and DS-182).

    s14.py --arm0 FETCHED_ZIP     Arm 0, P1 to P10, in order; stops on the first failure
    s14.py --run  [--slice-min 27]   one slice of the sweep (arm R, arm W non-G, pairs, class G last)
    s14.py --evaluate             build whatif.json, rescore.json and result.json from results.jsonl (no simulation)
    s14.py --check                rebuild every deck text and every table from results.jsonl; compare

MODEL EVIDENCE ONLY, STUDY, NOT ADOPTED, UNVALIDATED DRAFT.
"""
from __future__ import annotations

import argparse
import gzip
import hashlib
import json
import math
import subprocess
import sys
import tempfile
import time
from pathlib import Path

STUDY = Path(__file__).resolve().parent
sys.path[:0] = [str(STUDY), str(STUDY.parents[3])]

import budget  # noqa: E402  (the S14 copy)
import cells  # noqa: E402
import runner  # noqa: E402
from cells import ROOT  # noqa: E402
from guard import IMAGE, kill_pinned_containers  # noqa: E402

S13 = ROOT / "scripts/stack/studies/mc04_s13_node_cap_budget"
S13_CACHE = ROOT / ".circuit-cache/sources/mc04-s13"
CK = STUDY / "checkpoints"
RESULTS = STUDY / "results.jsonl"
LEDGER = CK / "invocations.jsonl"
SLICES = CK / "slices.jsonl"
WHATIF = STUDY / "whatif.json"
RESCORE = STUDY / "rescore.json"
RESULT = STUDY / "result.json"
STATUS = "MODEL EVIDENCE ONLY, STUDY, NOT ADOPTED, UNVALIDATED DRAFT"
CAMPAIGN = "circuit/orchestration/campaigns/osc-stack-20261114"
BRIEF = f"{CAMPAIGN}/mc04-s14-feedback-capacitor-brief-20261128.md"
BRIEF_SHA = "c6904428218df07858d0ef3a604fe391be3e7c81c6a7d4615538be5160ae9ec2"
WHATIF_PREFIX = "WHAT-IF 10 pF, NOT ADOPTED: "
WHATIF_LINE = "Cwhatif out inm 10p"

VALUES_W = [0, 4, 6, 8, 12, 16, 24, 32, 50, 64, 100]
CAND_W = [4, 6, 8, 12, 16, 32, 50]
C05_NEW = [32, 40, 64, 80]
CAND_C05 = [20, 25, 32, 40, 50]
CAND_S13 = budget.CANDIDATES_PF
CEILING_PF = 50.0
REL_DB, REL_PP, BASE_DB, BASE_PCT = 1.0, 5.0, 6.0, 50.0  # S2, ASSUMED

CAP_TOTAL, CAP_SEED_INV, CAP_SEEDS, CAP_REPLAYS = 900, 180, 60, 200
NONG_CEILING_S, G_CEILING_S = 105 * 60, 45 * 60
SLICE_HARD_S = 28 * 60
G_LADDER = (("reltol=1e-5", ".options reltol=1e-5"), ("ngspice default", None))  # S6.10

SETS = [  # brief "Arm W": class, topology prefix, corner selector
    ("E-control", "0841e309", {}), ("E-control", "3ef5b8d0", {}), ("E-control", "8fb559a8", {}),
    ("E-control", "ee93250a", {}), ("E-control", "c7bb7f88", {"bracket": "open"}),
    ("E-audio", "a10f67ef", {}), ("E-audio", "932a592b", {"bracket": "open"}),
    ("H-REF9", "e06fd44a", {"tmux_c": 0.0, "bracket": "open"}),
    ("H-REF9", "e06fd44a", {"tmux_c": 100e-12, "bracket": "open"}),
    ("G", "2f451c39", {"trim": 1.0, "iabc": "low"}), ("G", "2f451c39", {"trim": 1.0, "iabc": "high"}),
]
RESCORE_CLASSES = ("A", "C", "D")
ICS = ("U5110", "U8409", "U5209", "U5210")


class Stop(SystemExit):
    pass


class GEnd(Exception):
    """Class G ends as NOT EVALUATED (its ceiling, an invalid seed, P10 on a class G deck)."""


class Ceiling(Exception):
    pass


def sha_file(rel):
    return hashlib.sha256((ROOT / rel).read_bytes()).hexdigest()


def sha_text(x):
    return hashlib.sha256(x.encode()).hexdigest()


# ------------------------------------------------------------------------------------------------ pins (P1, P3)

def s13_result():
    return json.loads((S13 / "result.json").read_text())


def pins14():
    s13 = "scripts/stack/studies/mc04_s13_node_cap_budget"
    pins = dict(s13_result()["pinned_inputs"])
    pins.update({
        BRIEF: BRIEF_SHA,
        f"{CAMPAIGN}/mc04-s13-node-capacitance-budget-brief-20261127.md":
            "360eb262216fdf80004bc4d0d7d4108f64a8c003d1b2e97ab73f255d30225bf4",
        f"{CAMPAIGN}/mc04-s13-disposition-20261127.md":
            "93d75e2bba4e32cce6188638675f25f39d7228e0c3911e0c0cfbb44e65aac0d0",
        f"{CAMPAIGN}/reviews/mc04-s13-result-review-20261127.md":
            "2264925b62386271de73b8f391f9cf44ea92ee19b2730ebbbd58c5f5b3732c65",
        f"{s13}/results.jsonl": "7dbfce7bdc8c5a21a6d221e2b78a5dc0468b93a37429b5c3b3271a5af4c20c45",
        f"{s13}/budget.json": "511c29409661dd236695dc0bcb368f97d5e95b87bf0f29d1378b5dae01bd4136",
        f"{s13}/result.json": "4310cbbc97420817b15ae6b56b480836d8d0d6a067651edebc7c9f59fe93ca1a",
        f"{s13}/census.json": "a28e85b64175e903f9953bc5ffdfc8d9164d64c870ad889bb748caa8bbdfc830",
        f"{s13}/models.json": "5163dc1da7c11ed7164d961d9c977b5ed2dde04e4e9441e5623312fa5531534e",
        f"{s13}/cells.py": "a4105eb400d733480f0831308ec29f6bad2fccea557c7ebbb0ba9447affade6c",
        f"{s13}/runner.py": "225f5283c5967f12b77ad141b49119f7451ea9ebef5da9f88b991332747131c2",
        f"{s13}/budget.py": "e691ef182b165fc7a1b27e1a721a869d66ca568dd536be9b39cbc91a895ec931",
        f"{s13}/guard.py": "5d066228ed1efca4f4f072efa52b5e5c4432f34ca0ec77e90da5d4baa4c51651",
    })
    return pins


def check_pins():
    bad = {k: (sha_file(k) if (ROOT / k).exists() else None) for k, v in pins14().items()
           if not (ROOT / k).exists() or sha_file(k) != v}
    if bad:
        raise Stop(f"STOP 1: input drift {sorted(bad)}")
    budget.check_models()


# ------------------------------------------------------------------------------------------------ pinned S13 helper

def pinned(reqs):
    """Answers from the pinned S13 modules (s13_pinned.py, separate interpreter, no bytecode written)."""
    if not reqs:
        return []
    out = subprocess.run([sys.executable, "-I", str(STUDY / "s13_pinned.py")], input=json.dumps(reqs),
                         capture_output=True, text=True, cwd=ROOT, timeout=900)
    if out.returncode != 0:
        raise RuntimeError("s13_pinned.py failed: " + out.stderr[-800:])
    ans = json.loads(out.stdout)
    bad = [a["error"] for a in ans if not a["ok"]]
    if bad:
        raise RuntimeError("s13_pinned.py: " + "; ".join(bad[:3]))
    return [a["value"] for a in ans]


# ------------------------------------------------------------------------------------------------ records

_S13 = {}


def s13_records():
    if not _S13:
        for line in (S13 / "results.jsonl").read_text().splitlines():
            if line.strip():
                d = json.loads(line)
                _S13[(d["point_id"], d["deck"])] = d
    return _S13


def s13_rows():
    return {r["net"]: r for r in json.loads((S13 / "budget.json").read_text())["rows"]}


def load_results(path=RESULTS):
    out = {}
    if path.exists():
        for line in path.read_text().splitlines():
            if line.strip():
                d = json.loads(line)
                out[(d["point_id"], d["deck"])] = d
    return out


RES = {"r": None}


def append(rec):
    with open(RESULTS, "a") as f:
        f.write(json.dumps(rec, sort_keys=True) + "\n")
    if RES["r"] is not None:
        RES["r"][(rec["point_id"], rec["deck"])] = rec


# ------------------------------------------------------------------------------------------------ ledger and bounds

class Bounds:
    """Every invocation is written to checkpoints/invocations.jsonl before it starts, so discarded and interrupted
    decks count against the caps (N12). Arm time is accumulated per slice in checkpoints/slices.jsonl."""

    def __init__(self, slice_id=None, start=None):
        self.slice, self.start = slice_id, start or time.time()
        self.arm = "arm0"
        self.arm_t0 = self.start
        self.arm_s = {}
        self.sid = None

    def entries(self):
        return [json.loads(x) for x in LEDGER.read_text().splitlines() if x.strip()] if LEDGER.exists() else []

    def counts(self, entries=None):
        e = self.entries() if entries is None else entries
        return {"total": len(e), "seed_invocations": sum(1 for x in e if x["kind"] == "seed"),
                "seeds": len({x["sid"] for x in e if x["kind"] == "seed" and x.get("sid")}),
                "replays": sum(1 for x in e if x["kind"] == "replay")}

    def prior_arm_s(self):
        """Arm time of every earlier slice; a slice without an end record is counted to its last ledger entry."""
        tot = {}
        if not SLICES.exists():
            return tot
        sl = [json.loads(x) for x in SLICES.read_text().splitlines() if x.strip()]
        ends = {x["slice"]: x for x in sl if x["kind"] == "end"}
        led = self.entries()
        for s in (x for x in sl if x["kind"] == "start"):
            if s["slice"] == self.slice:
                continue
            if s["slice"] in ends:
                for k, v in ends[s["slice"]]["arm_s"].items():
                    tot[k] = tot.get(k, 0.0) + v
            else:
                mine = [x for x in led if x.get("slice") == s["slice"]]
                last = max((x["t"] for x in mine), default=s["t"])
                arm = mine[-1]["arm"] if mine else "nonG"
                tot[arm] = tot.get(arm, 0.0) + (last - s["t"]) + runner.TIMEOUT_S  # killed: its last deck in full
        return tot

    def switch(self, arm):
        now = time.time()
        self.arm_s[self.arm] = self.arm_s.get(self.arm, 0.0) + now - self.arm_t0
        self.arm, self.arm_t0 = arm, now

    def used(self, arm):
        prior = self.prior_arm_s().get(arm, 0.0)
        mine = self.arm_s.get(arm, 0.0) + (time.time() - self.arm_t0 if self.arm == arm else 0.0)
        return prior + mine

    def hook(self, kind, key):
        c = self.counts()
        if c["total"] + 1 > CAP_TOTAL:
            raise Stop("STOP 3: total invocation cap 900 reached")
        if kind == "seed" and c["seed_invocations"] + 1 > CAP_SEED_INV:
            raise Stop("STOP 3: seed invocation cap 180 reached")
        if kind == "seed" and self.sid and c["seeds"] + 1 > CAP_SEEDS and self.sid not in {
                x.get("sid") for x in self.entries()}:
            raise Stop("STOP 3: seed cap 60 reached")
        if kind == "replay" and c["replays"] + 1 > CAP_REPLAYS:
            raise Stop("STOP 3: replay cap 200 reached")
        timeout = runner.TIMEOUT_G_S if self.arm == "G" else runner.TIMEOUT_S
        if self.arm == "nonG" and self.used("nonG") + timeout > NONG_CEILING_S:
            raise Ceiling("non-G sweep ceiling 1 h 45 min")
        if self.arm == "G" and self.used("G") + timeout > G_CEILING_S:
            raise GEnd("class G ceiling 45 min reached")
        with open(LEDGER, "a") as f:
            f.write(json.dumps({"t": time.time(), "kind": kind, "key": key, "sid": self.sid if kind == "seed" else None,
                                "slice": self.slice, "arm": self.arm}) + "\n")


BOUNDS = {"b": None}


def install(b):
    BOUNDS["b"] = b
    runner.LEDGER["hook"] = b.hook


# ------------------------------------------------------------------------------------------------ topology, points

_T = {}


def topo():
    if not _T:
        cen, t, rows = budget.topologies()
        _T.update({"cen": cen, "topo": t, "rows": rows})
    return _T


def topology(prefix):
    m = [t for k, t in topo()["topo"].items() if k.startswith(prefix)]
    if len(m) != 1:
        raise Stop(f"STOP 6: topology {prefix} not unique ({len(m)})")
    return m[0]


def point(t, corner, c, *, whatif, phase, out_pF=cells.OUT_STRAY_PF, swept=None):
    return {"topology": t["key"], "class": t["circuit"]["subclass"], "corner": corner,
            "swept": swept or t["swept"][0], "other": None, "c_pF": c, "whatif": whatif, "phase": phase,
            "out_pF": out_pF}


def set_corner(t, sel):
    m = [c for c in cells.corners_of(t["circuit"]) if all(c.get(k) == v for k, v in sel.items())]
    if len(m) != 1:
        raise Stop(f"STOP 6: corner {sel} of {t['key']} not unique")
    return m[0]


def set_id(cls, prefix, corner):
    return f"{cls}:{prefix}:{json.dumps(corner, sort_keys=True)}"


def arm_w_sets():
    out = []
    for cls, prefix, sel in SETS:
        t = topology(prefix)
        if t["circuit"]["subclass"] != cls or len(t["swept"]) != 1:
            raise Stop(f"STOP 6: set {prefix} is not one {cls} swept node")
        out.append({"id": set_id(cls, prefix, set_corner(t, sel)), "class": cls, "t": t,
                    "corner": set_corner(t, sel)})
    return out


def g_trim_check(t):
    """STOP 6 test of the brief: trim 1.0 must be the larger feedback resistance of class G."""
    def rf(trim):
        lines = budget.build_lines(t, point(t, {"trim": trim, "iabc": "low"}, 0, whatif=False, phase="x"), loop=False)
        g = {}
        for ln in lines:
            f = ln.split()
            if f and f[0].startswith("R"):
                g[tuple(f[1:3])] = cells.parse_value(f[3])
        # out -> pre_gain_trim -> inm (trimmer between pre_gain_trim and inm, wiper to inm)
        par = [v for (a, b), v in g.items() if {a, b} == {"inm", "pre_gain_trim"}]
        return g[("out", "pre_gain_trim")] + 1 / sum(1 / v for v in par)
    a, b = rf(0.0), rf(1.0)
    if not b > a:
        raise Stop("STOP 6: trim 1.0 is not the larger feedback resistance")
    return {"trim0_ohm": round(a, 1), "trim1_ohm": round(b, 1)}


def bracket_agnd(corner):
    return {**corner, "bracket": "agnd"}


# ------------------------------------------------------------------------------------------------ no-connect exclusion

OTA_ORDER = ["1", "2", "3", "4", "5", "6", "7", "8", "11"]


def element_pins(text):
    body = text.split("\n.control\n")[0].splitlines()[1:]
    elems = [ln.split() for ln in body if ln.strip() and not ln.lstrip().startswith((".", "*", "+"))]
    out = []
    for f in elems:
        k = f[0][0].upper()
        nodes = f[1:-1] if k == "X" else (f[1:5] if k in "EG" else f[1:3])
        out.append((f, nodes))
    return out


def nc_nodes(circuit, text):
    """S6.8 by rule: a deck node on exactly one element pin, that pin a device pin the specification leaves
    unconnected. Only the OTA has such pins in this study; an op-amp pin is always connected in its cell."""
    count = {}
    for f, nodes in element_pins(text):
        for n in nodes:
            count[n] = count.get(n, 0) + 1
    spec = {}
    for e in circuit["elements"]:
        if e["t"] == "ota":
            spec = {q: e["pins_n"].get(q) for q in OTA_ORDER}
    out = []
    for f, nodes in element_pins(text):
        if f[0].upper() != "XOTA":
            continue
        for q, n in zip(OTA_ORDER, nodes):
            if count.get(n) == 1 and spec.get(q) is None:
                out.append(n)
    return sorted(set(out))


def nc_diagnostics(ext, ref, exclude):
    return {n: {"deviation_V": abs(ext[n] - ref[n]), "label": "diagnostic, not a study result"}
            for n in exclude if n in ext and n in ref}


# ------------------------------------------------------------------------------------------------ P10 and identity

def parse_cap(line):
    f = line.split()
    if len(f) != 4 or not f[0].upper().startswith("C"):
        return None
    try:
        return f[0], {f[1], f[2]}, cells.parse_value(f[3])
    except Exception:
        return None


def p10(s14_text, pinned_text):
    """P10: the what-if deck minus exactly one line equals the pinned build byte for byte; that line is one capacitor
    between OUT and the protected node `inm` (network side of the probe) of 10 pF as a number."""
    a, b = s14_text.split("\n"), pinned_text.split("\n")
    if len(a) != len(b) + 1:
        return "what-if deck is not the pinned build plus one line"
    i = next((k for k in range(len(b)) if a[k] != b[k]), len(b))
    if a[:i] + a[i + 1:] != b:
        return "what-if deck minus its capacitor line differs from the pinned build"
    cap = parse_cap(a[i])
    if cap is None:
        return "the added line is not a capacitor"
    if cap[1] != {"out", "inm"}:
        return "the added capacitor is not between out and inm"
    if abs(cap[2] - 10e-12) > 1e-18:
        return "the added capacitor is not 10 pF"
    return None


def pwl_points(line):
    inner = line[line.index("PWL(") + 4:line.rindex(")")].split()
    return [(float(inner[k]), float(inner[k + 1])) for k in range(0, len(inner), 2)]


def scaled_equal(s14_text, pinned_text, scale, k5_t0):
    """S1/S4: a rescaled second deck equals the pinned build in every line except the two K5 stimuli, which carry
    the pinned value times the recorded scale (from the first K5 edge on); nothing else may differ."""
    a, b = s14_text.split("\n"), pinned_text.split("\n")
    if len(a) != len(b):
        return "line count differs"
    scaled = 0
    for x, y in zip(a, b):
        if x == y:
            continue
        if x.startswith("Vpwl_") and y.startswith("Vpwl_") and x.split()[:3] == y.split()[:3]:
            px, py = pwl_points(x), pwl_points(y)
            if [t for t, _ in px] != [t for t, _ in py]:
                return "PWL times differ"
            for (t, vx), (_, vy) in zip(px, py):
                if vx == vy:
                    continue
                if t < k5_t0 - 1e-12 or abs(vx - vy * scale) > 1e-9 * max(1.0, abs(vy)):
                    return "a stimulus value other than a K5 value differs"
                scaled += 1
        elif x.startswith("Bsin_") and y.startswith("Bsin_"):
            fx, fy = x.split("?")[1].split("*sin")[0].strip(), y.split("?")[1].split("*sin")[0].strip()
            if x.replace(fx + "*sin", "") != y.replace(fy + "*sin", "") or \
                    abs(float(fx) - float(fy) * scale) > 1e-6 * abs(float(fy)):
                return "the sine differs other than by its amplitude"
            scaled += 1
        else:
            return "a line other than the two K5 stimuli differs"
    return None if scaled else "no K5 stimulus value is scaled"


# ------------------------------------------------------------------------------------------------ seeds (S6)

SEEDS = {"s14": {}, "groups": {}}


def s13_seed(sid):
    rec = s13_records().get((sid, "seed"))
    return rec


def seed_ok_s14(t, kind, rec):
    """S6.4 re-checked on a pinned S13 seed record (offline): valid in S13, group OK, and the S14 validity test."""
    if rec is None or not rec.get("valid"):
        return ["no valid pinned S13 seed"]
    g = s13_records().get((rec["group"], "group"))
    if g is None or g["status"] != "OK":
        return ["pinned S13 seed group not within 5 uV"]
    return budget.seed_validity(t["circuit"], kind, rec["reference"], rec["expected_dc"], False)


def spec_seed(t, p, kind):
    """Specification cells other than class G use the pinned S13 seed of the same zero-stray netlist."""
    net = budget.seed_netlist(t, p, kind)
    sid = budget.seed_id(net)
    rec = s13_seed(sid)
    errs = seed_ok_s14(t, kind, rec)
    if errs:
        return {"point_id": sid, "valid": False, "reason": "; ".join(errs), "source": "S13"}
    return {**rec, "source": "S13 pinned seed record", "exclude": []}


def s14_group_members(t, p):
    """The S14-run seeds of one DC group: what-if (and, for class G, specification) seeds of every corner of the
    group in the S14 plan, both deck kinds."""
    g = budget.group_key(t, p)
    corners = [c for c in cells.corners_of(t["circuit"])
               if budget.group_key(t, {**p, "corner": c}) == g]
    flags = [True, False] if t["circuit"]["class"] == "G" else [True]
    out = {}
    for c in corners:
        for wf in flags:
            q = {**p, "corner": c, "whatif": wf, "c_pF": 0, "out_pF": cells.OUT_STRAY_PF}
            for kind in ("loop", "closed"):
                net = budget.seed_netlist(t, q, kind)
                out.setdefault(budget.seed_id(net), (q, kind, net))
    return g, out


def s13_group_refs(g):
    return [r for (pid, d), r in s13_records().items() if d == "seed" and r.get("group") == g and r.get("valid")]


def run_seed_group(t, p):
    """S6.1 to S6.5 for an S14 group: seed every member, compare with the S13-equivalent seeds; one ramp re-seed."""
    g, members = s14_group_members(t, p)
    is_g = t["circuit"]["class"] == "G"
    timeout = runner.TIMEOUT_G_S if is_g else None
    res = RES["r"]
    for sid, (q, kind, net) in members.items():
        if (sid, "seed") in res:
            continue
        BOUNDS["b"].sid = sid
        rec = budget.seed_one(t, q, kind, net, timeout=timeout)
        rec["exclude"] = nc_nodes(t["circuit"], net + "\n.control\n")
        append(rec)
    if (g, "group") in res:
        return res[(g, "group")]
    recs = [res[(sid, "seed")] for sid in members]
    s13r = s13_group_refs(g)
    excl = sorted({n for r in recs for n in r.get("exclude", [])})
    refs = [r["reference"] for r in recs if r["valid"]] + [r["reference"] for r in s13r]
    why = budget.group_disagreement(refs, excl)
    reseeded = False
    if why:
        for sid, (q, kind, net) in members.items():
            BOUNDS["b"].sid = sid
            rec = budget.seed_one(t, q, kind, net, ramp_only=True, timeout=timeout)
            rec["exclude"] = nc_nodes(t["circuit"], net + "\n.control\n")
            rec["attempts"] = res[(sid, "seed")]["attempts"] + rec["attempts"]
            rec["reseeded_by_ramp"] = True
            rec["point_id"] = sid
            append({**rec, "deck": "seed"})
        recs = [res[(sid, "seed")] for sid in members]
        refs = [r["reference"] for r in recs if r["valid"]] + [r["reference"] for r in s13r]
        why = budget.group_disagreement(refs, excl)
        reseeded = True
    worst = 0.0
    for i in range(len(refs)):
        for j in range(i + 1, len(refs)):
            for k in (set(refs[i]) & set(refs[j])) - set(excl):
                worst = max(worst, abs(refs[i][k] - refs[j][k]))
    grec = {"deck": "group", "point_id": g, "members": sorted(members), "s13_members": sorted(r["point_id"] for r in s13r),
            "status": "OK" if not why and all(r["valid"] for r in recs) else "NOT EVALUATED",
            "reason": why or (None if all(r["valid"] for r in recs) else "a member seed is not valid"),
            "max_difference_V": worst, "excluded_no_connect": excl, "reseeded_by_ramp": reseeded,
            "attempts": [], "point": {**p, "c_pF": 0, "phase": "group"}}
    append(grec)
    return grec


def get_seed(t, p, kind):
    """S6.6: the seed of the cell and corner. An output-pair point (Cout 0 or 100 pF, a capacitor-only change, not a
    DC-distinct deck) uses the seed of the same point at the standard 20 pF output stray."""
    p = {**p, "out_pF": cells.OUT_STRAY_PF}
    if not p["whatif"] and t["circuit"]["class"] != "G":
        return spec_seed(t, p, kind)
    g = run_seed_group(t, p)
    net = budget.seed_netlist(t, p, kind)
    sid = budget.seed_id(net)
    rec = RES["r"].get((sid, "seed"))
    if rec is None:
        return {"point_id": sid, "valid": False, "reason": "seed missing from its group"}
    if g["status"] != "OK":
        return {**rec, "valid": False, "reason": "seed group: " + (g["reason"] or "not OK")}
    return rec


# ------------------------------------------------------------------------------------------------ evaluation decks

_PIN_TEXT = {}


def prefetch(items):
    """Pinned S13 texts for (point, deck, nodeset); a what-if point is built pinned with whatif=False."""
    reqs, keys = [], []
    for p, deck, ns in items:
        q = {**p, "whatif": False}
        k = (budget.point_id(q), deck, sha_text("\n".join(ns)))
        if k in _PIN_TEXT or k in keys:
            continue
        keys.append(k)
        reqs.append({"op": "texts", "point": q, "deck": deck, "nodeset": list(ns)})
    for k, v in zip(keys, pinned(reqs)):
        _PIN_TEXT[k] = dict((n, x) for n, x in v)


def pinned_text(p, deck, ns, name):
    k = (budget.point_id({**p, "whatif": False}), deck, sha_text("\n".join(ns)))
    if k not in _PIN_TEXT:
        prefetch([(p, deck, ns)])
    return _PIN_TEXT[k][name]


def identity(p, deck, ns, name, text, scale=None, k5_t0=None):
    """P10 for a what-if deck; for every other S14-built deck the stronger builder identity (byte-equal to the
    pinned build). A rescaled deck is compared with the stimulus rule of S1/S4."""
    ref = pinned_text(p, deck, ns, name)
    if p["whatif"]:
        a = text.split("\n")
        if scale is not None:
            if a.count(WHATIF_LINE) != 1:
                return "rescaled what-if deck without exactly one capacitor line"
            b = [x for x in a if x != WHATIF_LINE]
            why = p10(text, "\n".join(b)) or scaled_equal("\n".join(b), ref, scale, k5_t0)
            return why
        return p10(text, ref)
    if scale is not None:
        return scaled_equal(text, ref, scale, k5_t0)
    return None if text == ref else "S14 build differs from the pinned S13 build"


def ladder(t, deck):
    if deck == "loop":
        return G_LADDER if t["circuit"]["class"] == "G" else runner.LOOP_TOLERANCES
    return None


def timeout_of(t):
    return runner.TIMEOUT_G_S if t["circuit"]["class"] == "G" else runner.TIMEOUT_S


def p10_fail(t, why):
    if t["circuit"]["class"] == "G":
        raise GEnd("P10 failed: " + why)
    raise Stop("STOP 2: P10 failed: " + why)


def eval_deck(t, p, deck, kind="eval"):
    """One loop or closed-loop deck of a point, seeded (S6.6), accepted under S6.7, at the first accepted step."""
    seed = get_seed(t, p, deck)
    if not seed.get("valid"):
        return {"status": "NOT EVALUATED", "reason": "no valid operating point: " + str(seed.get("reason")),
                "key": None, "metrics": None, "attempts": [], "seed_id": seed["point_id"]}
    ns = seed["nodeset"]
    c = t["circuit"]
    texts = budget.loop_texts(t, p, ns, ladder(t, deck)) if deck == "loop" else budget.closed_texts(t, p, ns)
    attempts = []
    runner.LEDGER["kind"] = kind
    for item in texts:
        name, text = item[0], item[1]
        why = identity(p, deck, ns, name, text)
        if why:
            p10_fail(t, why)
        exclude = nc_nodes(c, text)
        files = ["op1", "v", "i", "op2"] if deck == "loop" else item[2]
        try:
            key, tab, wall = runner.run(text, files, timeout=timeout_of(t))
        except (runner.OracleError, RuntimeError) as e:
            why = budget.oracle_failure(str(e))
            if why is None:
                raise
            attempts.append({"step": name, "result": why, "key": runner.deck_key(text)})
            continue
        tranop = "Transient op" in runner.last_log(key)
        ops = [runner.external_nodes(tab["op1"]), runner.external_nodes(tab["op2"])] if deck == "loop" else \
            [runner.external_nodes(tab["op"])]
        why = budget.eval_reason(ops, seed["reference"], tranop, exclude)
        attempts.append({"step": name, "result": why or "accepted", "key": key, "wall_s": round(wall, 2),
                         "transient_op": tranop, "no_connect_diagnostic": nc_diagnostics(ops[0], seed["reference"],
                                                                                         exclude)})
        if why is None:
            if deck == "loop":
                m = runner.loop_metrics(tab["v"], tab["i"], item[2], item[3])
            else:
                m = runner.closed_metrics(c, p["corner"], item[3], tab)
                m["stimulus"] = budget.stimulus_record(c, item[3])
            m["op"] = dict(ops[0])
            return {"status": "OK", "key": key, "metrics": m, "attempts": attempts, "seed_id": seed["point_id"],
                    "seed_sha256": seed["nodeset_sha256"], "accepted_step": name}
    return {"status": "NOT EVALUATED", "reason": "no ladder step gave an accepted operating point", "key": None,
            "metrics": None, "attempts": attempts, "seed_id": seed["point_id"]}


def second_deck(t, p, first, seed_ref_out, ns, kind="rescale"):
    """S4 "Clipping": one rescaled deck, K5 only, at the integration step the first deck was accepted at."""
    sw = first["metrics"]["swing_out_V"]
    scale = runner.k5_scale(seed_ref_out, sw[0], sw[1])
    texts = budget.closed_texts(t, p, ns, k5_scale=scale)
    name = first["accepted_step"]
    item = next(x for x in texts if x[0] == name)
    text, files, P = item[1], item[2], item[3]
    if not (P.get("k5_step_V") or P.get("sine") or t["circuit"]["class"] == "C"):
        return {"scale": None, "reason": "no scalable K5 stimulus in this cell", "status": "NOT EVALUATED"}
    k5_t0 = P["windows"]["K5_step"][0][0]
    why = identity(p, "closed", ns, name, text, scale=scale, k5_t0=k5_t0)
    if why:
        p10_fail(t, "rescaled deck: " + why)
    runner.LEDGER["kind"] = kind
    rec = {"scale": scale, "vq_V": seed_ref_out, "first_swing_V": sw, "step": name,
           "k5_step_V": P.get("k5_step_V") if t["circuit"]["class"] != "C" else P["windows"]["K5_step"][0][2],
           "sine_amp_V": (P.get("sine") or {}).get("amp"), "key": runner.deck_key(text)}
    try:
        key, tab, wall = runner.run(text, files, timeout=timeout_of(t))
    except (runner.OracleError, RuntimeError) as e:
        why = budget.oracle_failure(str(e))
        if why is None:
            raise
        return {**rec, "status": "NOT EVALUATED", "reason": why}
    tranop = "Transient op" in runner.last_log(key)
    e0 = runner.external_nodes(tab["op"])
    seed_ref = first["seed_ref"]
    why = budget.eval_reason([e0], seed_ref, tranop, nc_nodes(t["circuit"], text))
    if why:
        return {**rec, "status": "NOT EVALUATED", "reason": why, "wall_s": round(wall, 2)}
    m = runner.closed_metrics(t["circuit"], p["corner"], P, tab, k5_only=True)
    return {**rec, "status": "OK", "metrics": m, "wall_s": round(wall, 2)}


def prepare(pts):
    """Seeds first, then the pinned reference texts of every point in one helper call."""
    items = []
    for t, p in pts:
        for deck in ("loop", "closed"):
            if (budget.point_id(p), deck) in RES["r"]:
                continue
            sd = get_seed(t, p, deck)
            if sd.get("valid"):
                items.append((p, deck, sd["nodeset"]))
    prefetch(items)


def run_point(t, p, kind="eval"):
    """Loop and closed-loop deck of a point, plus the one rescaled second deck when the first is clipped."""
    res = RES["r"]
    pid = budget.point_id(p)
    for deck in ("loop", "closed"):
        if (pid, deck) in res:
            continue
        t0 = time.time()
        out = eval_deck(t, p, deck, kind)
        append({"point_id": pid, "deck": deck, "point": p, **out, "wall_s": round(time.time() - t0, 2)})
    cl = res[(pid, "closed")]
    if cl["status"] == "OK" and cl["metrics"]["clipped"] and (pid, "k5second") not in res:
        seed = get_seed(t, p, "closed")
        first = {**cl, "seed_ref": seed["reference"]}
        out = second_deck(t, p, first, seed["reference"]["out"], seed["nodeset"], kind)
        append({"point_id": pid, "deck": "k5second", "point": p, "seed_id": seed["point_id"], **out})


# ------------------------------------------------------------------------------------------------ arm R

def rescore_topologies():
    tp = topo()["topo"]
    return sorted((t for t in tp.values() if t["circuit"]["class"] in RESCORE_CLASSES), key=lambda t: t["key"])


def arm_r_records():
    """The 152 closed-loop and 152 loop records of classes A, C and D in the pinned S13 results."""
    keys = {t["key"] for t in rescore_topologies()}
    rec = s13_records()
    closed = [r for (pid, d), r in rec.items() if d == "closed" and r["point"]["topology"] in keys
              and r["point"]["phase"] == "sweep"]
    loop = [r for (pid, d), r in rec.items() if d == "loop" and r["point"]["topology"] in keys
            and r["point"]["phase"] == "sweep"]
    return sorted(closed, key=lambda r: r["point_id"]), sorted(loop, key=lambda r: r["point_id"])


TIME_KEYS = ("k4", "k5", "k6", "k8_tau_s", "sine_swing")


def cache_files(key, files):
    stem = key[:20]
    out = {}
    for s in files:
        gz, dat = S13_CACHE / f"{stem}.{s}.dat.gz", S13_CACHE / f"{stem}.{s}.dat"
        out[s] = gz if gz.exists() else (dat if dat.exists() else None)
    return out


def deck_files(text):
    return [ln.split()[1].split("@D@.")[1].rsplit(".dat", 1)[0] for ln in text.split("\n")
            if ln.startswith("wrdata @D@.")]


def cache_text_key(key):
    cir = S13_CACHE / f"{key[:20]}.cir"
    if not cir.exists():
        return None, None
    body = cir.read_text()
    rel = (S13_CACHE / key[:20]).relative_to(ROOT).as_posix()
    text = body.replace(rel, "@D@")
    return text, runner.deck_key(text)


def read_any(path):
    p = Path(path)
    if p.suffix != ".gz":
        return runner.read_table(p)
    with tempfile.TemporaryDirectory() as d:
        q = Path(d) / p.name[:-3]
        q.write_bytes(gzip.decompress(p.read_bytes()))
        return runner.read_table(q)


def time_metrics(m):
    return {k: m.get(k) for k in TIME_KEYS if k in m}


def same_digits(a, b):
    return json.dumps(a, sort_keys=True) == json.dumps(b, sort_keys=True)


def bind_all(closed):
    """Cache binding of arm R (brief "Where the waveform comes from"): key of the cached text with the placeholder
    put back, then every time-domain metric of the record reproduced digit for digit by the pinned S13 runner."""
    out, reqs, idx = {}, [], []
    for r in closed:
        if r["status"] != "OK":
            out[r["point_id"]] = {"bound": False, "reason": "S13 record NOT EVALUATED"}
            continue
        text, k = cache_text_key(r["key"])
        if k != r["key"]:
            out[r["point_id"]] = {"bound": False, "reason": "cached deck missing or its key differs"}
            continue
        files = cache_files(r["key"], deck_files(text))
        if any(v is None for v in files.values()):
            out[r["point_id"]] = {"bound": False, "reason": "a cached data file is missing"}
            continue
        reqs.append({"op": "closed_metrics", "point": r["point"], "tables": {s: str(v) for s, v in files.items()}})
        idx.append((r, files))
    for (r, files), m in zip(idx, pinned(reqs)):
        ok = same_digits(time_metrics(m), time_metrics(r["metrics"]))
        out[r["point_id"]] = {"bound": ok, "reason": None if ok else "pinned runner does not reproduce the record",
                              "files": {s: str(v.relative_to(ROOT)) for s, v in files.items()},
                              "waveform_sha256": {s: hashlib.sha256(v.read_bytes()).hexdigest()
                                                  for s, v in files.items() if s in ("t1", "t2", "tinj")}}
    return out


def s14_measure(t, p, tables):
    """K4 (S3) and K5 (S4) with the swing, from one closed-loop deck's tables."""
    _, _, P = cells.closed_text(t["circuit"], p["corner"], budget.build_lines(t, p, loop=False))
    m = runner.closed_metrics(t["circuit"], p["corner"], P, tables)
    return {k: m[k] for k in ("k4", "k5", "swing_out_V", "clipped", "sine_swing") if k in m}


REPLAY_TOL = {"pm": 0.01, "db": 0.01, "pp": 0.1, "k5_abs": 1e-6, "k5_rel": 0.01, "rel": 1e-4}


def replay_matches(rec, m):
    """Replay acceptance: 0.01 dB (peaking and gain), 0.1 pp (K4), max(1 uV, 1 %) (K5), 0.01 % (K6, K8)."""
    a = rec
    errs = []
    for k, x in a["ac"].items():
        y = m["ac"].get(k)
        if y is None or abs(x["peaking_dB"] - y["peaking_dB"]) > REPLAY_TOL["db"] or \
                abs(x["gain_20k_dB"] - y["gain_20k_dB"]) > REPLAY_TOL["db"]:
            errs.append(f"ac {k}")
    for k, v in a["k4"].items():
        for o, q in zip(v, m["k4"].get(k, [])):
            if o["overshoot_percent"] is None or q["overshoot_percent"] is None or \
                    abs(o["overshoot_percent"] - q["overshoot_percent"]) > REPLAY_TOL["pp"]:
                errs.append(f"k4 {k}")
    for k, x in a["k5"].items():
        y = m["k5"].get(k)
        if y is None or abs(x - y) > max(REPLAY_TOL["k5_abs"], REPLAY_TOL["k5_rel"] * abs(x)):
            errs.append(f"k5 {k}")
    for x, y in zip(a.get("k6") or [], m.get("k6") or []):
        if x is None or y is None or abs(x - y) > REPLAY_TOL["rel"] * abs(x):
            errs.append("k6")
    if "k8_tau_s" in a and abs(a["k8_tau_s"] - m["k8_tau_s"]) > REPLAY_TOL["rel"] * abs(a["k8_tau_s"]):
        errs.append("k8")
    return errs


def replay(t, r):
    """Rebuilt by the pinned S13 modules with the pinned S13 seed nodeset, to the identical key; run once."""
    p = r["point"]
    seed = s13_seed(r["seed_id"])
    texts = pinned([{"op": "texts", "point": p, "deck": "closed", "nodeset": seed["nodeset"]}])[0]
    m = [x for n, x in texts if runner.deck_key(x) == r["key"]]
    if not m:
        return {"status": "NOT EVALUATED", "reason": "waveform not recoverable: rebuilt key differs"}
    text = m[0]
    runner.LEDGER["kind"] = "replay"
    try:
        key, tab, wall = runner.run(text, deck_files(text))
    except (runner.OracleError, RuntimeError) as e:
        if budget.oracle_failure(str(e)) is None:
            raise
        return {"status": "NOT EVALUATED", "reason": "waveform not recoverable: replay failed", "key": r["key"]}
    stem = runner.WORK / key[:20]
    files = {s: Path(f"{stem}.{s}.dat.gz") for s in deck_files(text)}
    m13 = pinned([{"op": "closed_metrics", "point": p, "tables": {s: str(v) for s, v in files.items()}}])[0]
    errs = replay_matches(r["metrics"], m13)
    out = {"key": key, "wall_s": round(wall, 2), "replay_mismatch": errs,
           "waveform_sha256": {s: hashlib.sha256(v.read_bytes()).hexdigest() for s, v in files.items()
                               if s in ("t1", "t2", "tinj")}}
    if errs:
        return {**out, "status": "NOT EVALUATED", "reason": "waveform not recoverable: replay outside tolerance"}
    return {**out, "status": "OK", "tables": {s: str(v) for s, v in files.items()}}


def arm_r(rebind=False):
    """Binding, replays, re-measurement and rescaled second decks of the 152 closed-loop records."""
    res = RES["r"]
    closed, _ = arm_r_records()
    todo = [r for r in closed if (r["point_id"], "rescore") not in res]
    if not todo:
        return
    tp = topo()["topo"]
    binds = bind_all(todo)
    for r in todo:
        t = tp[r["point"]["topology"]]
        b = binds[r["point_id"]]
        rec = {"point_id": r["point_id"], "deck": "rescore", "point": r["point"], "s13_key": r["key"],
               "binding": {k: v for k, v in b.items()}, "seed_id": r.get("seed_id")}
        if b["bound"]:
            tables = {s: read_any(ROOT / v) for s, v in b["files"].items()}
            rec.update({"source": "cache", "measured": s14_measure(t, r["point"], tables), "status": "OK"})
        elif r["status"] != "OK":
            rec.update({"source": None, "status": "NOT EVALUATED", "reason": "S13 record NOT EVALUATED"})
        else:
            rp = replay(t, r)
            rec["replay"] = {k: v for k, v in rp.items() if k != "tables"}
            if rp["status"] == "OK":
                tables = {s: read_any(v) for s, v in rp["tables"].items()}
                rec.update({"source": "replay", "measured": s14_measure(t, r["point"], tables), "status": "OK"})
            else:
                rec.update({"source": None, "status": "NOT EVALUATED", "reason": rp["reason"]})
        append(rec)


def arm_r_second():
    res = RES["r"]
    tp = topo()["topo"]
    for (pid, d), rec in sorted(res.items()):
        if d != "rescore" or rec["status"] != "OK" or not rec["measured"]["clipped"] or (pid, "k5second") in res:
            continue
        t = tp[rec["point"]["topology"]]
        r13 = s13_records()[(pid, "closed")]
        seed = s13_seed(r13["seed_id"])
        first = {"metrics": rec["measured"], "accepted_step": r13["accepted_step"], "seed_ref": seed["reference"]}
        out = second_deck(t, rec["point"], first, seed["reference"]["out"], seed["nodeset"])
        append({"point_id": pid, "deck": "k5second", "point": rec["point"], "seed_id": seed["point_id"], **out})


def c05_points():
    out = []
    for t in rescore_topologies():
        if t["circuit"]["class"] != "C":
            continue
        corner = next(c for c in cells.corners_of(t["circuit"]) if c["wiper"] == 0.5)
        for v in C05_NEW:
            out.append((t, point(t, corner, v, whatif=False, phase="sweep")))
    return out


# ------------------------------------------------------------------------------------------------ criteria (S2 to S5)

def quantum(x, sig=6):
    if x is None or x == 0 or not math.isfinite(x):
        return 0.0
    return 10 ** (math.floor(math.log10(abs(x))) - (sig - 1))


def passes(margin, resolution):
    """S5: a pass by less than the recorded resolution is a tie, and a tie is a fail."""
    return margin >= 0 and margin >= resolution


def k5_view(closed, second):
    """K5 of a point: the first deck's figures unless it is clipped (S4); then the second deck's, unless that is
    missing, not accepted or clipped too, when K5 is NOT EVALUATED: output clipped (N16)."""
    if not closed.get("clipped"):
        return closed["k5"], None
    if second is None:
        return None, "NOT EVALUATED: output clipped (second deck not run)"
    if second.get("status") != "OK":
        return None, "NOT EVALUATED: output clipped (second deck not accepted)"
    if second["metrics"]["clipped"]:
        return None, "NOT EVALUATED: output clipped"
    return second["metrics"]["k5"], None


def baseline(cls, loop, closed, second):
    """S2/S3/S4 at zero stray: the corner's mode for K3 and K4 and its status."""
    k1, k2 = runner.k1_k2(loop)
    k5, k5_ne = k5_view(closed, second)
    fails, ne = [], []
    if not k1:
        fails.append("K1")
    if not k2:
        fails.append("K2")
    if k5_ne:
        ne.append(k5_ne)
    elif not all(x is not None and x <= runner.OSC_LIMIT for x in k5.values()):
        fails.append("K5")
    peaks = [a["peaking_dB"] for a in closed["ac"].values()]
    edges = [o for v in closed["k4"].values() for o in v]
    if any(o.get("status", "OK") != "OK" for o in edges):
        ne.append(runner.UNSETTLED)
        ov = None
    else:
        ov = max(o["overshoot_percent"] for o in edges)
    pk = None if any(x is None for x in peaks) else max(peaks)
    if pk is None:
        fails.append("K3")
    modes = {"K3": "absolute", "K4": "absolute"}
    exceed = []
    if pk is not None and pk > runner.PEAK_LIMIT:
        exceed.append("K3")
    if ov is not None and ov > runner.OVERSHOOT_LIMIT:
        exceed.append("K4")
    if exceed:
        if (pk is not None and pk > BASE_DB) or (ov is not None and ov > BASE_PCT):
            fails += [k for k in exceed if (k == "K3" and pk > BASE_DB) or (k == "K4" and ov > BASE_PCT)]
            fails += [k for k in exceed if k not in fails]
        elif not ("K1" in fails or "K2" in fails or "K5" in fails or k5_ne):
            for k in exceed:
                modes[k] = "relative"
        else:
            fails += exceed
    if cls in ("E-control", "H-REF9") and closed.get("k6") is not None:
        if not all(x is not None and passes(runner.SETTLE_LIMIT_S - x, closed.get("k6_resolution_s") or 0)
                   for x in closed["k6"]):
            fails.append("K6")
    return {"fails": sorted(set(fails)), "not_evaluated": ne, "modes": modes, "peak0_dB": pk, "overshoot0_pct": ov}


def judge(cls, loop, closed, zero, second, base, only_k1_k5=False):
    """Per-criterion verdict of one value against its corner's zero-stray deck and mode (True, False or a
    NOT EVALUATED reason, which counts as not passed)."""
    res = {}
    k1, k2 = runner.k1_k2(loop)
    res["K1"], res["K2"] = k1, k2
    ok = True
    for k, a in closed["ac"].items():
        pk = a["peaking_dB"]
        if pk is None:
            ok = False
        elif base["modes"]["K3"] == "absolute":
            ok &= pk <= runner.PEAK_LIMIT
        else:
            z = zero["ac"][k]["peaking_dB"]
            ok &= pk <= BASE_DB and passes(z + REL_DB - pk, quantum(pk) + quantum(z))
    res["K3"] = ok
    ok, ne = True, None
    for k, v in closed["k4"].items():
        for i, o in enumerate(v):
            if o.get("status", "OK") != "OK":
                ne = runner.UNSETTLED
                continue
            ov = o["overshoot_percent"]
            if base["modes"]["K4"] == "absolute":
                ok &= ov <= runner.OVERSHOOT_LIMIT
            else:
                z = zero["k4"][k][i]["overshoot_percent"]
                ok &= ov <= BASE_PCT and passes(z + REL_PP - ov, quantum(ov, 5) + quantum(z, 5))
    res["K4"] = ne if ne and ok else ok
    k5, k5_ne = k5_view(closed, second)
    res["K5"] = k5_ne if k5_ne else all(x is not None and x <= runner.OSC_LIMIT for x in k5.values())
    if only_k1_k5:
        return res
    g = budget.gating(cls)
    if "K6" in g:
        if cls == "C":  # relative test; the recorded resolution is the timestep over tau0 (resolution_fraction)
            rs = closed["resolution_fraction"]
            res["K6"] = all(a is not None and b is not None and passes(runner.REL_LIMIT - (a - b) / b, rs)
                            for a, b in zip(closed["k6"], zero["k6"]))
        else:
            rs = closed.get("k6_resolution_s") or closed["stimulus"]["tran"][-1]["tmax"]
            res["K6"] = all(x is not None and passes(runner.SETTLE_LIMIT_S - x, rs) for x in closed["k6"])
    if "K8" in g:
        t, t0 = closed["k8_tau_s"], zero["k8_tau_s"]
        res["K8"] = passes(runner.REL_LIMIT - (t - t0) / t0, closed["resolution_fraction"])
    if "K7" in g:
        ok = True
        for k, a in closed["ac"].items():
            if cls == "A" and not k.endswith("@harness"):
                continue
            b = zero["ac"][k]
            ok &= passes(runner.K7_DB - abs(a["gain_20k_dB"] - b["gain_20k_dB"]),
                         quantum(a["gain_20k_dB"]) + quantum(b["gain_20k_dB"]))
            ok &= passes(runner.K7_DEG - abs(a["phase_20k_deg"] - b["phase_20k_deg"]),
                         quantum(a["phase_20k_deg"]) + quantum(b["phase_20k_deg"]))
        res["K7"] = ok
    ok = True
    for n, x in closed["noise"].items():
        a, b = x["integrated_uVrms"], zero["noise"][n]["integrated_uVrms"]
        d = 20 * math.log10(a / b)
        ok &= passes(runner.K9_DB - d, 20 * math.log10(1 + quantum(a) / a + quantum(b) / b))
    res["K9"] = ok
    return res


def declared_candidates(tested):
    """The candidate list the brief declares for a corner's tested-value list."""
    if tested == VALUES_W:
        return CAND_W
    if tested == sorted(budget.C_REDUCED_PF + C05_NEW):
        return CAND_C05
    if tested == budget.VALUES_PF:
        return CAND_S13
    return []


def check_candidates(tested, candidates):
    """N13: a candidate is accepted at a corner only if its double is a tested value at that same corner, and only
    from the list the brief declares for that corner (class C wiper 0.5: 20, 25, 32, 40 and 50 pF only)."""
    allowed = declared_candidates(tested)
    bad = [g for g in candidates if 2 * g not in tested or g not in allowed]
    if bad:
        raise ValueError(f"candidate limit(s) {bad} rejected: double not tested at this corner")


def corner_limit(cls, values, candidates, only_k1_k5=False):
    """values: {c_pF: {"loop": rec, "closed": metrics or None, "second": rec, "ne": reason}}; every value must be
    present. Returns the corner's status, mode, per-value verdicts and C_lim (Ruling 3, per corner)."""
    tested = sorted(values)
    check_candidates(tested, candidates)
    if 0 not in values:
        return {"status": "INCOMPLETE", "c_lim_pF": None}
    z = values[0]
    if z.get("ne"):
        return {"status": "NOT EVALUATED: " + z["ne"], "c_lim_pF": None, "verdicts": {}}
    base = baseline(cls, z["loop"], z["closed"], z.get("second"))
    if only_k1_k5:  # report only: the same rule restricted to K1 to K5
        base = {**base, "fails": [f for f in base["fails"] if f in ("K1", "K2", "K3", "K4", "K5")]}
    verdicts = {}
    for v in tested:
        x = values[v]
        if x.get("ne"):
            verdicts[v] = {"pass": False, "not_evaluated": True, "failed": ["NOT EVALUATED: " + x["ne"]]}
            continue
        j = judge(cls, x["loop"], x["closed"], z["closed"], x.get("second"), base, only_k1_k5)
        failed = [k for k, r in j.items() if r is not True]
        verdicts[v] = {"pass": not failed, "failed": failed, "criteria": {k: r for k, r in j.items()},
                       "pm_deg": x["loop"]["phase_margin_deg"], "gm_dB": x["loop"]["gain_margin_dB"]}
    out = {"verdicts": verdicts, "modes": base["modes"], "peak0_dB": base["peak0_dB"],
           "overshoot0_pct": base["overshoot0_pct"]}
    op_ne = [v for v in tested if verdicts[v].get("not_evaluated")]
    if base["fails"]:
        return {**out, "status": "FAILS AT ZERO STRAY", "c_lim_pF": None, "deciding": base["fails"]}
    if base["not_evaluated"]:
        return {**out, "status": "NOT EVALUATED: " + base["not_evaluated"][0].replace("NOT EVALUATED: ", ""),
                "c_lim_pF": None, "deciding": base["not_evaluated"]}
    if op_ne:
        return {**out, "status": "NOT EVALUATED: no accepted operating point at " +
                ", ".join(f"{v:g} pF" for v in op_ne), "c_lim_pF": None}
    fails = [v for v in tested if not verdicts[v]["pass"]]
    lim = None
    for g in candidates:
        if all(verdicts[v]["pass"] for v in tested if v <= 2 * g):
            lim = float(g)
    if lim is not None:
        lim = min(lim, CEILING_PF)
    lowest = fails[0] if fails else None
    return {**out, "status": "OK", "c_lim_pF": lim, "lowest_fail_pF": lowest,
            "deciding": verdicts[lowest]["failed"] if lowest is not None else None,
            "non_monotonic": lowest is not None and any(verdicts[v]["pass"] for v in tested if v > lowest)}


# ------------------------------------------------------------------------------------------------ value tables

def value_entry(loop, closed, second=None):
    if loop is None or closed is None:
        return None
    if loop["status"] != "OK" or closed["status"] != "OK":
        why = loop.get("reason") if loop["status"] != "OK" else closed.get("reason")
        return {"ne": why or "no accepted operating point"}
    return {"loop": loop["metrics"], "closed": closed["metrics"], "second": second}


def s14_values(t, corner, values, *, whatif, phase, out_pF=cells.OUT_STRAY_PF):
    res = RES["r"]
    out = {}
    for v in values:
        p = point(t, corner, v, whatif=whatif, phase=phase, out_pF=out_pF)
        pid = budget.point_id(p)
        e = value_entry(res.get((pid, "loop")), res.get((pid, "closed")), res.get((pid, "k5second")))
        if e is not None:
            out[v] = e
    return out


def rescore_values(t, corner):
    """Arm R values of one corner: K1/K2, AC, noise, K6 and K8 from the S13 record; K4 and K5 re-measured."""
    res, rec = RES["r"], s13_records()
    out = {}
    for (pid, d), r in rec.items():
        p = r["point"]
        if d != "closed" or p["topology"] != t["key"] or p["corner"] != corner or p["phase"] != "sweep":
            continue
        lo = rec.get((pid, "loop"))
        rs = res.get((pid, "rescore"))
        if rs is None:
            continue
        if lo["status"] != "OK" or r["status"] != "OK":
            out[p["c_pF"]] = {"ne": "S13 record NOT EVALUATED"}
        elif rs["status"] != "OK":
            out[p["c_pF"]] = {"ne": rs["reason"]}
        else:
            m = {**r["metrics"], **{k: v for k, v in rs["measured"].items()}}
            m.pop("k6_resolution_s", None)
            out[p["c_pF"]] = {"loop": lo["metrics"], "closed": m, "second": res.get((pid, "k5second"))}
    if t["circuit"]["class"] == "C" and corner.get("wiper") == 0.5:
        out.update(s14_values(t, corner, C05_NEW, whatif=False, phase="sweep"))
    return out


def rescore_candidates(t, corner):
    if t["circuit"]["class"] == "C" and corner.get("wiper") == 0.5:
        return CAND_C05
    return CAND_S13


# ------------------------------------------------------------------------------------------------ pairs and brackets

def pair_points(t, corner, c_lim, whatif):
    return [point(t, corner, c_lim, whatif=whatif, phase="outpair", out_pF=o) for o in (0.0, 100.0)]


def pair_verdicts(t, corner, c_lim, whatif, zero_entry, base_cls):
    res = RES["r"]
    out = []
    for p in pair_points(t, corner, c_lim, whatif):
        pid = budget.point_id(p)
        e = value_entry(res.get((pid, "loop")), res.get((pid, "closed")), res.get((pid, "k5second")))
        if e is None:
            out.append({"out_pF": p["out_pF"], "c_pF": c_lim, "pass": False, "failed": ["NOT RUN"]})
            continue
        if e.get("ne"):
            out.append({"out_pF": p["out_pF"], "c_pF": c_lim, "pass": False, "failed": ["NOT EVALUATED"]})
            continue
        base = baseline(base_cls, zero_entry["loop"], zero_entry["closed"], zero_entry.get("second"))
        j = judge(base_cls, e["loop"], e["closed"], zero_entry["closed"], e.get("second"), base)
        failed = [k for k, r in j.items() if r is not True]
        out.append({"out_pF": p["out_pF"], "c_pF": c_lim, "pass": not failed, "failed": failed,
                    "pm_deg": e["loop"]["phase_margin_deg"]})
    return out


def bracket_check(s, lim_open):
    """Arm W bracket check: the AGND bracket at 0, C_lim and 2 C_lim (0 only without a limit)."""
    t, corner = s["t"], bracket_agnd(s["corner"])
    vals = [0] if not lim_open else [0, lim_open, 2 * lim_open]
    ag = s14_values(t, corner, vals, whatif=True, phase="bracket")
    # the check points were run at C_lim as computed (a float); the swept set holds the same values as integers
    op = {v: e for v, e in zip(vals, [s14_values(t, s["corner"], [int(v) if v == int(v) else v], whatif=True,
                                                 phase="whatif").get(int(v) if v == int(v) else v) for v in vals])
          if e is not None}
    if len(ag) < len(vals):
        return {"status": "INCOMPLETE", "values": vals}
    reasons, rows = [], []
    if ag[0].get("ne"):
        return {"status": "NOT EVALUATED", "values": vals, "reason": ag[0]["ne"]}
    base = baseline(s["class"], ag[0]["loop"], ag[0]["closed"], ag[0].get("second"))
    for v in vals:
        a, o = ag[v], op.get(v)
        if a.get("ne") or o is None or o.get("ne"):
            reasons.append(f"check point {v:g} pF not evaluated")
            continue
        d = abs(a["loop"]["phase_margin_deg"] - o["loop"]["phase_margin_deg"])
        if base["fails"] or base["not_evaluated"]:
            ok = False
        else:
            j = judge(s["class"], a["loop"], a["closed"], ag[0]["closed"], a.get("second"), base)
            ok = all(x is True for x in j.values())
        rows.append({"c_pF": v, "pm_agnd_deg": a["loop"]["phase_margin_deg"],
                     "pm_open_deg": o["loop"]["phase_margin_deg"], "dK1_deg": round(d, 3), "agnd_pass": ok})
        if d > 2.0:
            reasons.append(f"brackets differ by {d:.2f} deg in K1 at {v:g} pF")
        if not ok:
            reasons.append(f"AGND bracket check point fails at {v:g} pF")
    return {"status": "OK", "values": vals, "rows": rows, "provisional_reasons": reasons,
            "c_lim_comparison": "NOT RUN: the AGND bracket is not swept"}


# ------------------------------------------------------------------------------------------------ the sweep plan

def arm_w_points(sets, cls_filter):
    out = []
    for s in sets:
        if s["class"] not in cls_filter:
            continue
        for v in VALUES_W:
            out.append((s, point(s["t"], s["corner"], v, whatif=True, phase="whatif")))
    return out


def arm_g_points(sets):
    out = []
    for s in sets:
        if s["class"] == "G":
            for v in VALUES_W:
                out.append((s, point(s["t"], s["corner"], v, whatif=False, phase="armG")))
    return out


def set_limit(s, whatif=True):
    vals = s14_values(s["t"], s["corner"], VALUES_W, whatif=whatif, phase="whatif" if whatif else "armG")
    if len(vals) < len(VALUES_W):
        return {"status": "INCOMPLETE", "c_lim_pF": None}
    return corner_limit(s["class"], vals, CAND_W)


def rescore_corner_limits(t):
    out = {}
    for corner in cells.corners_of(t["circuit"]):
        vals = rescore_values(t, corner)
        expect = budget.VALUES_PF if not (t["circuit"]["class"] == "C" and corner.get("wiper") == 0.5) else \
            sorted(budget.C_REDUCED_PF + C05_NEW)
        if sorted(vals) != sorted(expect):
            out[json.dumps(corner, sort_keys=True)] = {"status": "INCOMPLETE", "c_lim_pF": None}
            continue
        out[json.dumps(corner, sort_keys=True)] = corner_limit(t["circuit"]["subclass"], vals,
                                                               rescore_candidates(t, corner))
    return out


def deciding_corner(lims):
    ok = [(json.loads(k), v) for k, v in lims.items() if v["status"] == "OK" and v["c_lim_pF"]]
    if len(ok) != len(lims) or not ok:
        return None
    return min(ok, key=lambda kv: kv[1]["c_lim_pF"])


def sweep(b, slice_end):
    """One slice of the sweep in the brief's order. Returns the reason it ended."""
    sets = arm_w_sets()
    # arm R
    b.switch("nonG")
    arm_r()
    arm_r_second()
    prepare(c05_points())
    for t, p in c05_points():
        run_point(t, p)
    # arm W, non-G, with bracket checks
    for cls in ("E-control", "E-audio", "H-REF9"):
        prepare([(s["t"], p) for s, p in arm_w_points(sets, {cls})])
        for s, p in arm_w_points(sets, {cls}):
            run_point(s["t"], p)
        for s in sets:
            if s["class"] != cls or "bracket" not in s["corner"]:
                continue
            lim = set_limit(s)
            vals = [0] + ([lim["c_lim_pF"], 2 * lim["c_lim_pF"]] if lim.get("c_lim_pF") else [])
            for v in vals:
                run_point(s["t"], point(s["t"], bracket_agnd(s["corner"]), v, whatif=True, phase="bracket"))
    # Ruling 6 pairs of arm R and the non-G what-if sets
    for t in rescore_topologies():
        d = deciding_corner(rescore_corner_limits(t))
        if d:
            for p in pair_points(t, d[0], d[1]["c_lim_pF"], False):
                run_point(t, p)
    for s in sets:
        if s["class"] == "G":
            continue
        lim = set_limit(s)
        if lim.get("status") == "OK" and lim.get("c_lim_pF"):
            for p in pair_points(s["t"], s["corner"], lim["c_lim_pF"], True):
                run_point(s["t"], p)
    # class G last, inside its own ceiling
    b.switch("G")
    try:
        gsets = [s for s in sets if s["class"] == "G"]
        for s in gsets:
            for wf in (False, True):
                for kind in ("loop", "closed"):
                    seed = get_seed(s["t"], point(s["t"], s["corner"], 0, whatif=wf, phase="x"), kind)
                    if not seed.get("valid"):
                        raise GEnd("a class G seed is not valid under S6")
        zeros = []
        for s in gsets:
            for wf, ph in ((False, "armG"), (True, "whatif")):
                p = point(s["t"], s["corner"], 0, whatif=wf, phase=ph)
                run_point(s["t"], p)
                zeros.append(RES["r"][(budget.point_id(p), "closed")]["status"] == "OK" and
                             RES["r"][(budget.point_id(p), "loop")]["status"] == "OK")
        if not any(zeros):
            raise GEnd("all four class G 0 pF points NOT EVALUATED")
        prepare([(s["t"], p) for s, p in arm_g_points(sets) + arm_w_points(sets, {"G"})])
        for s, p in arm_g_points(sets):
            run_point(s["t"], p)
        for s, p in arm_w_points(sets, {"G"}):
            run_point(s["t"], p)
        for s in gsets:
            for wf in (False, True):
                lim = set_limit(s, whatif=wf)
                if lim.get("status") == "OK" and lim.get("c_lim_pF"):
                    for p in pair_points(s["t"], s["corner"], lim["c_lim_pF"], wf):
                        run_point(s["t"], p)
    except GEnd as e:
        append({"point_id": "class-G-end", "deck": "gend", "reason": str(e), "t": time.time()})
        return "class G ended: " + str(e)
    return "complete"


def drive(slice_min, slice_id):
    check_pins()
    if not (CK / "arm0.json").exists() or not json.loads((CK / "arm0.json").read_text()).get("pass"):
        raise Stop("Arm 0 has not passed")
    survivors = kill_pinned_containers()
    if survivors:
        raise Stop(f"STOP 3: container survived docker kill: {survivors}")
    RES["r"] = load_results()
    if ("class-G-end", "gend") in RES["r"] or ("sweep", "done") in RES["r"]:
        print("sweep already complete")
        return
    t0 = time.time()
    b = Bounds(slice_id, t0)
    install(b)
    with open(SLICES, "a") as f:
        f.write(json.dumps({"kind": "start", "slice": slice_id, "t": t0}) + "\n")
    runner.DEADLINE["t"] = t0 + min(SLICE_HARD_S, slice_min * 60)
    created = ensure_init()
    reason = "complete"
    try:
        reason = sweep(b, runner.DEADLINE["t"])
        if reason == "complete" or reason.startswith("class G ended"):
            append({"point_id": "sweep", "deck": "done", "reason": reason})
    except runner.SliceDeadline:
        reason = "slice end (deadline: no room for one more deck)"
    except Ceiling as e:
        reason = "STOP 3: " + str(e)
    except Stop as e:
        reason = str(e)
    finally:
        runner.remove_spiceinit()
        survivors = kill_pinned_containers()
        b.switch(b.arm)
        runner.DEADLINE["t"] = None
        with open(SLICES, "a") as f:
            f.write(json.dumps({"kind": "end", "slice": slice_id, "t": time.time(), "reason": reason,
                                "arm_s": b.arm_s, "counts": b.counts(), "containers_after": survivors,
                                "spiceinit_created": created}) + "\n")
    print(f"{slice_id}: {reason}; counts {b.counts()}; arm time {b.arm_s}", flush=True)
    if survivors:
        raise Stop("STOP 3: container survived docker kill")
    if reason.startswith("STOP"):
        raise Stop(reason)


def ensure_init():
    """`.spiceinit`: one with the exact content is removed and recreated; one with other content is a stop."""
    init = ROOT / ".spiceinit"
    if init.exists():
        if init.read_text() != "set ngbehavior=ps\n":
            raise Stop("STOP 3: a .spiceinit with foreign content")
        init.unlink()
    return runner.ensure_spiceinit()


# ------------------------------------------------------------------------------------------------ Arm 0

P4_CASES = [("/W1/CONTROL_SUM", {}), ("/E2/REF9_FB", {"tmux_c": 100e-12, "bracket": "open"}),
            ("/F3/Cf75ecf_FB", {"harness_c": 1e-9})]


def p4():
    """Six recorded S13 decks rebuilt by the pinned modules to the identical key, run, and compared."""
    rec, rows = s13_records(), topo()["rows"]
    out = []
    for net, corner in P4_CASES:
        tk = rows[net]["topology"]
        for deck in ("loop", "closed"):
            r = next(x for (pid, d), x in rec.items() if d == deck and x["point"]["topology"] == tk and
                     x["point"]["corner"] == corner and x["point"]["c_pF"] == 0 and x["point"]["phase"] == "sweep")
            seed = s13_seed(r["seed_id"])
            texts = pinned([{"op": "texts", "point": r["point"], "deck": deck, "nodeset": seed["nodeset"]}])[0]
            m = [x for n, x in texts if runner.deck_key(x) == r["key"]]
            row = {"net": net, "corner": corner, "deck": deck, "key": r["key"], "rebuilt_to_key": bool(m)}
            if not m:
                out.append({**row, "pass": False})
                continue
            runner.LEDGER["kind"] = "control"
            files = ["op1", "v", "i", "op2"] if deck == "loop" else deck_files(m[0])
            key, tab, wall = runner.run(m[0], files)
            stem = runner.WORK / key[:20]
            paths = {s: str(Path(f"{stem}.{s}.dat.gz")) for s in files}
            m13 = pinned([{"op": f"{deck}_metrics", "point": r["point"], "tables": paths}])[0]
            if deck == "loop":
                d = abs(m13["phase_margin_deg"] - r["metrics"]["phase_margin_deg"])
                ok = d <= 0.01 and (m13["gain_margin_dB"] is None) == (r["metrics"]["gain_margin_dB"] is None) and \
                    (m13["gain_margin_dB"] is None or abs(m13["gain_margin_dB"] - r["metrics"]["gain_margin_dB"]) <= 0.01)
                row.update({"pm_deg": m13["phase_margin_deg"], "recorded_pm_deg": r["metrics"]["phase_margin_deg"]})
            else:
                errs = []
                for k, a in r["metrics"]["ac"].items():
                    y = m13["ac"][k]
                    if abs(a["peaking_dB"] - y["peaking_dB"]) > 0.01 or abs(a["gain_20k_dB"] - y["gain_20k_dB"]) > 0.01:
                        errs.append(k)
                for k, v in r["metrics"]["k4"].items():
                    for o, q in zip(v, m13["k4"][k]):
                        if abs(o["overshoot_percent"] - q["overshoot_percent"]) > 0.1:
                            errs.append(k)
                ok = not errs
                row["mismatch"] = errs
            out.append({**row, "wall_s": round(wall, 2), "pass": ok})
    return out


def p6():
    sets = arm_w_sets()
    closed, loop = arm_r_records()
    nets = {}
    for t in rescore_topologies():
        for n in t["nets"]:
            nets[n] = t["circuit"]["class"]
    counts = {"what_if_sets": len(sets),
              "class_g_corners": len([s for s in sets if s["class"] == "G"]),
              "arm_w_points": len(sets) * len(VALUES_W) + 4 * 3, "arm_r_closed": len(closed), "arm_r_loop": len(loop),
              "arm_r_rows": len(nets), "rows_by_class": {k: sum(1 for v in nets.values() if v == k) for k in "ACD"}}
    want = {"what_if_sets": 11, "class_g_corners": 2, "arm_w_points": 133, "arm_r_closed": 152, "arm_r_loop": 152,
            "arm_r_rows": 22, "rows_by_class": {"A": 11, "C": 10, "D": 1}}
    return {"counts": counts, "pass": counts == want, "g_trim": g_trim_check(topology("2f451c39"))}


def p6b():
    """Seeds and 0 pF decks of the non-G what-if sets (both brackets) and the H-REF9 specification cell."""
    sets = [s for s in arm_w_sets() if s["class"] != "G"]
    rows = []
    for s in sets:
        corners = [s["corner"]] + ([bracket_agnd(s["corner"])] if "bracket" in s["corner"] else [])
        for corner in corners:
            phase = "whatif" if corner == s["corner"] else "bracket"
            p = point(s["t"], corner, 0, whatif=True, phase=phase)
            row = {"set": s["id"], "corner": corner, "whatif": True, "seeds": {}}
            for kind in ("loop", "closed"):
                sd = get_seed(s["t"], p, kind)
                errs = [] if sd.get("valid") else [str(sd.get("reason"))]
                if s["class"] == "H-REF9" and sd.get("valid"):
                    errs += budget.p6b_check(sd, kind)
                row["seeds"][kind] = {"seed_id": sd["point_id"], "method": sd.get("method"), "errors": errs}
            run_point(s["t"], p)
            pid = budget.point_id(p)
            row["loop"] = RES["r"][(pid, "loop")]["status"]
            row["closed"] = RES["r"][(pid, "closed")]["status"]
            row["pass"] = all(not v["errors"] for v in row["seeds"].values()) and row["loop"] == "OK" and \
                row["closed"] == "OK"
            rows.append(row)
    t = topology("e06fd44a")
    for corner in cells.corners_of(t["circuit"]):
        p = point(t, corner, 0, whatif=False, phase="P6b")
        row = {"set": "H-REF9 specification cell", "corner": corner, "whatif": False, "seeds": {}}
        for kind in ("loop", "closed"):
            sd = get_seed(t, p, kind)
            errs = [] if sd.get("valid") else [str(sd.get("reason"))]
            if sd.get("valid"):
                errs += budget.p6b_check(sd, kind)
            row["seeds"][kind] = {"seed_id": sd["point_id"], "source": sd.get("source"), "errors": errs}
        run_point(t, p, kind="control")
        pid = budget.point_id(p)
        row["loop"] = RES["r"][(pid, "loop")]["status"]
        row["closed"] = RES["r"][(pid, "closed")]["status"]
        row["pass"] = all(not v["errors"] for v in row["seeds"].values()) and row["loop"] == "OK" and \
            row["closed"] == "OK"
        rows.append(row)
    return {"rows": rows, "pass": all(r["pass"] for r in rows)}


def p7():
    out = {}
    rows = topo()["rows"]
    for net, need_k4, want in (("/W1/DRIVE_INV_SUM", True, 2.600), ("/E2/REF9_FB", False, 1.189)):
        t = topo()["topo"][rows[net]["topology"]]
        corner = cells.corners_of(t["circuit"])[0]  # the first corner, as in S13's P7
        p = point(t, corner, 1000, whatif=False, phase="P7")
        lo = eval_deck(t, p, "loop", "control")
        res = {"corner": corner, "loop": {k: lo[k] for k in ("status", "accepted_step", "attempts")}}
        pm = lo["metrics"]["phase_margin_deg"] if lo["metrics"] else None
        res["pm_deg"] = pm
        res["K1_fails"] = pm is not None and not runner.k1_k2(lo["metrics"])[0] and abs(pm - want) <= 0.1
        ok = lo["status"] == "OK" and res["K1_fails"]
        if need_k4:
            cl = eval_deck(t, p, "closed", "control")
            res["closed"] = {k: cl[k] for k in ("status", "accepted_step", "attempts")}
            if cl["metrics"]:
                edges = [o for v in cl["metrics"]["k4"].values() for o in v]
                res["k4_edges"] = edges
                res["K4_fails_or_unsettled"] = any(o["status"] != "OK" or o["overshoot_percent"] > runner.OVERSHOOT_LIMIT
                                                   for o in edges)
            ok &= cl["status"] == "OK" and res.get("K4_fails_or_unsettled") is True
        res["pass"] = ok
        out[net] = res
    return out


def p9(binds_cache):
    """Corrected tests on known cases, from the S13 cache (offline)."""
    out = {}
    tp = topo()["topo"]
    rec = s13_records()
    closed, _ = arm_r_records()
    # class C wiper 1.0 at 0 pF below 0.1 mV under S4 (every class C topology)
    rows = []
    for r in closed:
        p = r["point"]
        if p["class"] != "C" or p["corner"].get("wiper") != 1.0 or p["c_pF"] != 0:
            continue
        b = binds_cache[r["point_id"]]
        tables = {s: read_any(ROOT / v) for s, v in b["files"].items()} if b["bound"] else None
        m = s14_measure(tp[p["topology"]], p, tables) if tables else None
        k5 = max(m["k5"].values()) if m else None
        rows.append({"topology": p["topology"], "bound": b["bound"], "k5_max_V": k5, "pass": k5 is not None and k5 < 1e-4})
    out["class_C_wiper1_k5"] = {"rows": rows, "pass": bool(rows) and all(x["pass"] for x in rows)}
    # class C at 100 pF fails K6 and K8 under S5 (every class C 100 pF record)
    rows = []
    for t in rescore_topologies():
        if t["circuit"]["class"] != "C":
            continue
        for corner in cells.corners_of(t["circuit"]):
            r100 = next(r for r in closed if r["point"]["topology"] == t["key"] and r["point"]["corner"] == corner
                        and r["point"]["c_pF"] == 100)
            r0 = next(r for r in closed if r["point"]["topology"] == t["key"] and r["point"]["corner"] == corner
                      and r["point"]["c_pF"] == 0)
            a, z = r100["metrics"], r0["metrics"]
            rs = a["resolution_fraction"]
            k6 = all(passes(runner.REL_LIMIT - (x - y) / y, rs) for x, y in zip(a["k6"], z["k6"]))
            k8 = passes(runner.REL_LIMIT - (a["k8_tau_s"] - z["k8_tau_s"]) / z["k8_tau_s"], rs)
            k6_s13 = all((x - y) < runner.REL_LIMIT * y for x, y in zip(a["k6"], z["k6"]))
            k8_s13 = (a["k8_tau_s"] - z["k8_tau_s"]) < runner.REL_LIMIT * z["k8_tau_s"]
            rows.append({"topology": t["key"], "corner": corner, "K6_pass_S5": k6, "K8_pass_S5": k8,
                         "K6_pass_S13": k6_s13, "K8_pass_S13": k8_s13,
                         "k6_rel": [round((x - y) / y, 6) for x, y in zip(a["k6"], z["k6"])],
                         "k8_rel": round((a["k8_tau_s"] - z["k8_tau_s"]) / z["k8_tau_s"], 6), "resolution_fraction": rs})
    out["class_C_100pF_K6_K8"] = {"rows": rows, "pass": bool(rows) and all(not x["K6_pass_S5"] and not x["K8_pass_S5"]
                                                                          for x in rows)}
    # the S13 P7 deck acd3968e... is not settled under S3
    c13 = json.loads((S13 / "checkpoints/controls.json").read_text())["P7"]["/W1/DRIVE_INV_SUM"]
    key = c13["closed"]["attempts"][-1]["key"]
    text, k = cache_text_key(key)
    row = {"key": key, "bound_by_key": k == key}
    if k == key:
        t = tp[topo()["rows"]["/W1/DRIVE_INV_SUM"]["topology"]]
        p = point(t, c13["corner"], 1000, whatif=False, phase="P7")
        files = cache_files(key, deck_files(text))
        m13 = pinned([{"op": "closed_metrics", "point": p, "tables": {s: str(v) for s, v in files.items()}}])[0]
        ov13 = max(o["overshoot_percent"] for v in m13["k4"].values() for o in v)
        row["recorded_max_overshoot"], row["pinned_max_overshoot"] = c13["closed"]["max_overshoot_percent"], ov13
        m = s14_measure(t, p, {s: read_any(v) for s, v in files.items()})
        edges = [o for v in m["k4"].values() for o in v]
        row["edges"] = edges
        row["pass"] = ov13 == c13["closed"]["max_overshoot_percent"] and any(o["status"] == runner.UNSETTLED
                                                                             for o in edges)
    else:
        row["pass"] = False
    out["p7_deck_not_settled"] = row
    # one class B record with a +/-11.97 V sine swing is clipped under S4 (from the cache)
    cand = [r for (pid, d), r in rec.items() if d == "closed" and r["point"]["class"] == "B" and r["status"] == "OK"
            and r["metrics"].get("sine_swing") and max(abs(x) for v in r["metrics"]["sine_swing"].values()
                                                      for x in v) >= 11.97]
    cand.sort(key=lambda r: r["point_id"])
    row = {"candidates": len(cand)}
    if cand:
        r = cand[0]
        bb = bind_all([r])[r["point_id"]]
        row.update({"point_id": r["point_id"], "recorded_sine_swing": r["metrics"]["sine_swing"], "bound": bb["bound"]})
        if bb["bound"]:
            m = s14_measure(tp[r["point"]["topology"]], r["point"], {s: read_any(ROOT / v) for s, v in bb["files"].items()})
            row.update({"swing_out_V": m["swing_out_V"], "clipped": m["clipped"], "k5_label":
                        "NOT EVALUATED: output clipped" if m["clipped"] else "evaluated"})
            row["pass"] = m["clipped"]
        else:
            row["pass"] = False
            row["note"] = "not bound; the one allowed replay is not taken automatically"
    else:
        row["pass"] = False
    out["class_B_clipped"] = row
    out["pass"] = all(v["pass"] for v in out.values() if isinstance(v, dict) and "pass" in v)
    return out


def arm0(fetched):
    t_start = time.time()
    CK.mkdir(exist_ok=True)
    out = {"started": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(t_start))}
    b = Bounds("arm0", t_start)
    install(b)
    RES["r"] = load_results()
    stop = None
    try:
        check_pins()
        out["P1"] = {"result": "PASS", "count": len(pins14())}
        rr = lambda *a: subprocess.run(list(a), capture_output=True, text=True, cwd=ROOT, timeout=300)  # noqa: E731
        image_id = rr("docker", "image", "inspect", IMAGE, "--format", "{{.Id}}").stdout.strip()
        ver = rr("bash", "scripts/kicad/run.sh", "kicad-cli", "version").stdout.strip()
        banner = rr("bash", "scripts/kicad/run.sh", "ngspice", "-v").stdout
        ng = next((x.strip() for x in banner.splitlines() if "ngspice-" in x), banner.strip()[:120])
        p2 = image_id == "sha256:" + IMAGE.split("sha256:")[1] and ver == "10.0.6" and "ngspice-44.2" in ng
        out["P2"] = {"result": "PASS" if p2 else "FAIL", "image_id": image_id, "kicad_cli_version": ver,
                     "ngspice_banner": ng}
        if kill_pinned_containers():
            raise Stop("STOP 3: container survived docker kill")
        if not p2:
            raise Stop("STOP 3: oracle identity (P2)")
        f_sha = hashlib.sha256(Path(fetched).read_bytes()).hexdigest()
        cached = ROOT / ".circuit-cache/sources/opa196-model/SBOMAF9E.ZIP"
        p3 = f_sha == budget.MODEL_PINS[".circuit-cache/sources/opa196-model/SBOMAF9E.ZIP"] and \
            cached.read_bytes() == Path(fetched).read_bytes()
        out["P3"] = {"result": "PASS" if p3 else "FAIL", "fetched_sha256": f_sha, "model_pins": budget.MODEL_PINS,
                     "source": "Takazudo/circuit-dev-resources 54c00fc8 texas-instruments/opa4196/"
                               "opa4196-pspice-model-sbomaf9e.zip (gh api, read-only)"}
        if not p3:
            raise Stop("STOP 1: P3 model pin")
        ensure_init()
        b.switch("arm0")
        out["P4"] = p4()
        if not all(x["pass"] for x in out["P4"]):
            raise Stop("STOP 2: P4")
        out["P5"], out["P5_swapped"] = [], []
        runner.LEDGER["kind"] = "control"
        for rl, want in budget.LOOP_VALIDATION:
            base = ["MC04-S13 P5 loop-break validation, linear two-pole loop", "E1 o1 0 0 x 1000", "Rp o1 o2 1k",
                    "Cp o2 0 1.5915n", "E2 o3 0 o2 0 1", "Rq o3 o4 1k", "Cq o4 0 159.15p", "E3 o5 0 o4 0 1",
                    "Ro o5 y 1k", "Rg y 0 2k", f"Rl x 0 {rl:g}"]
            b.sid = f"P5-{rl:g}"
            r = budget.loop_run(base, "x", "y")
            out["P5"].append({"R_load_ohm": rl, "pm_deg": r["pm"], "retained_deg": want,
                              "pass": r["pm"] is not None and abs(r["pm"] - want) <= 0.1})
            b.sid = f"P5s-{rl:g}"
            r2 = budget.loop_run(base, "y", "x")
            out["P5_swapped"].append({"R_load_ohm": rl, "pm_deg": r2["pm"],
                                      "fails": r2["pm"] is None or abs(r2["pm"] - want) > 0.1})
        if not (all(x["pass"] for x in out["P5"]) and all(x["fails"] for x in out["P5_swapped"])):
            raise Stop("STOP 2: P5")
        out["P6"] = p6()
        if not out["P6"]["pass"]:
            raise Stop("STOP 2: P6")
        out["P6b"] = p6b()
        if not out["P6b"]["pass"]:
            raise Stop("STOP 2: P6b")
        out["P7"] = p7()
        if not all(x["pass"] for x in out["P7"].values()):
            raise Stop("STOP 2: P7")
        out["P8"] = []
        runner.LEDGER["kind"] = "control"
        for sub, lib in (("OPAx196", cells.MODEL_LIBS["OPAx196"]), ("OPAx197", cells.MODEL_LIBS["OPAx197"])):
            lines = [f"MC04-S13 P8 plain follower {sub}", ".param TEMP=27", f".include {lib}", "Vplus vp 0 12",
                     "Vminus vn 0 -12", f"XU 0 xinm vp vn out {sub}"]
            b.sid = f"P8-{sub}"
            r = budget.loop_run(lines, "xinm", "out", amp_inputs=("0", "xinm"))
            wp, wf = budget.FOLLOWER[sub]
            out["P8"].append({"model": sub, "pm_deg": r["pm"], "crossover_Hz": r["f"], "retained": [wp, wf],
                              "pass": r["pm"] is not None and abs(r["pm"] - wp) <= 0.1 and abs(r["f"] / wf - 1) <= 0.005})
        if not all(x["pass"] for x in out["P8"]):
            raise Stop("STOP 2: P8")
        closed, _ = arm_r_records()
        binds = bind_all(closed)
        (CK / "arm0-binding.json").write_text(json.dumps(binds, indent=1, sort_keys=True) + "\n")
        out["P9"] = p9(binds)
        if not out["P9"]["pass"]:
            raise Stop("STOP 2: P9")
        out["P10"] = {"result": "PASS", "checked": "every what-if deck built in Arm 0 (the 0 pF decks of the non-G "
                      "sets, both brackets) was compared when built; a failure would have stopped here"}
    except Stop as e:
        stop = str(e)
    finally:
        runner.remove_spiceinit()
        kill_pinned_containers()
        b.switch(b.arm)
    out["stopped"] = stop
    out["pass"] = stop is None
    out["wall_s"] = round(time.time() - t_start, 1)
    out["counts"] = b.counts()
    (CK / "arm0.json").write_text(json.dumps(out, indent=1, sort_keys=True, default=str) + "\n")
    print(json.dumps({"pass": out["pass"], "stopped": stop, "wall_s": out["wall_s"], "counts": out["counts"]}))
    if stop:
        raise Stop(stop)


# ------------------------------------------------------------------------------------------------ tables

PROVISIONAL_G = "LM13700 model overstates AC bandwidth and phase margin by more than twofold (its header)"
G_TRIM0 = "class G trim 0 corners (49.9 kOhm) NOT RUN"
G_LADDER_NOTE = "class G ladder bounded to reltol=1e-5 and default (S6.10)"


def row_label(lims, paper, *, reasons, whatif, arm_w):
    """Exactly one label (brief "Outputs"); a what-if row carries the prefix."""
    pre = WHATIF_PREFIX if whatif else ""
    vals = list(lims.values())
    if not vals or any(v["status"] == "INCOMPLETE" for v in vals):
        return pre + "NOT EVALUATED: sweep incomplete (cap, ceiling, class G end or STOP)", None, None
    ne = [v for v in vals if v["status"].startswith("NOT EVALUATED")]
    if ne:
        return pre + ne[0]["status"], None, ne[0].get("deciding")
    fz = [v for v in vals if v["status"] == "FAILS AT ZERO STRAY"]
    if fz:
        return pre + "FAILS AT ZERO STRAY", None, sorted({k for v in fz for k in v["deciding"]})
    if any(v["c_lim_pF"] is None for v in vals):
        return pre + "NO HEADROOM AT PAPER", None, "no candidate from 4 pF passes" if arm_w else \
            "no candidate passes"
    worst = min(vals, key=lambda v: v["c_lim_pF"])
    lim = worst["c_lim_pF"]
    if lim < paper:
        return pre + "NO HEADROOM AT PAPER", lim, worst.get("deciding")
    rel = sorted({k for v in vals for k, m in v["modes"].items() if m == "relative"})
    if reasons:
        extra = ["BASELINE EXCEEDS " + " AND ".join(rel) + " (RELATIVE FORM)"] if rel else []
        return pre + f"PROVISIONAL {lim:g} pF: " + "; ".join(reasons + extra), lim, worst.get("deciding")
    if rel:
        return pre + f"BUDGET {lim:g} pF, BASELINE EXCEEDS {' AND '.join(rel)} (RELATIVE FORM, MODEL EVIDENCE ONLY)", \
            lim, worst.get("deciding")
    if lim >= CEILING_PF:
        return pre + "BUDGET CAPPED AT 50 pF (MODEL EVIDENCE ONLY)", lim, worst.get("deciding")
    return pre + f"BUDGET {lim:g} pF (MODEL EVIDENCE ONLY)", lim, worst.get("deciding")


LABEL_HEADS = ("BUDGET", "PROVISIONAL", "NO HEADROOM AT PAPER", "FAILS AT ZERO STRAY", "NOT EVALUATED")


def validate_rows(rows, *, whatif_table):
    """N2, N3, N10, N13, N16 and M8 on a finished table."""
    errs = []
    for r in rows:
        lab = r["label"]
        if r.get("class") == "B" or r.get("subclass") == "B":
            errs.append(f"{r.get('id', r.get('net'))}: class B is out of scope in S14")
        if r.get("whatif"):
            if not lab.startswith(WHATIF_PREFIX):
                errs.append(f"{r['id']}: what-if row without its prefix")
            lab = lab[len(WHATIF_PREFIX):]
        elif lab.startswith(WHATIF_PREFIX):
            errs.append(f"{r.get('id', r.get('net'))}: prefix on a row that is not a what-if row")
        if sum(lab.startswith(h) for h in LABEL_HEADS) != 1:
            errs.append(f"{r.get('id', r.get('net'))}: not exactly one label")
        rel = any(m == "relative" for c in r.get("corners", []) for m in (c.get("modes") or {}).values())
        if lab.startswith("BUDGET") and rel and "BASELINE EXCEEDS" not in lab:
            errs.append(f"{r.get('id', r.get('net'))}: relative-form limit labelled as a plain budget")
        if lab.startswith("BUDGET") and r.get("provisional_reasons"):
            errs.append(f"{r.get('id', r.get('net'))}: provisional reason under a budget label")
        lim = r.get("c_lim_pF")
        if lim is not None:
            for c in r.get("corners", []):
                if 2 * lim not in [float(x) for x in c.get("tested", [])]:
                    errs.append(f"{r.get('id', r.get('net'))}: limit {lim} without its double tested at a corner")
        for c in r.get("corners", []):
            for v, x in (c.get("values") or {}).items():
                if x.get("clipped") and x.get("k5_figure_used"):
                    errs.append(f"{r.get('id', r.get('net'))}: clipped record given a K5 figure at {v} pF")
    if errs:
        raise ValueError("table rejected: " + "; ".join(errs[:10]))


def corner_view(lims, tested_map, entries_map):
    out = []
    for cid, v in lims.items():
        vals = {}
        for c, x in sorted((entries_map.get(cid) or {}).items()):
            if x.get("ne"):
                vals[str(c)] = {"pass": False, "not_evaluated": x["ne"]}
                continue
            k5, why = k5_view(x["closed"], x.get("second"))
            ver = (v.get("verdicts") or {}).get(c, {})
            vals[str(c)] = {"pass": ver.get("pass"), "failed": ver.get("failed"), "pm_deg": x["loop"]["phase_margin_deg"],
                            "gm_dB": x["loop"]["gain_margin_dB"], "clipped": x["closed"].get("clipped"),
                            "k5_source": "second deck" if x["closed"].get("clipped") and not why else
                            ("first deck" if not why else None), "k5_figure_used": bool(k5) and
                            bool(x["closed"].get("clipped")) and x.get("second") is None,
                            "k4_status": sorted({o.get("status", "OK") for q in x["closed"]["k4"].values() for o in q})}
        out.append({"corner": json.loads(cid), "status": v["status"], "c_lim_pF": v.get("c_lim_pF"),
                    "modes": v.get("modes"), "peak0_dB": v.get("peak0_dB"), "overshoot0_pct": v.get("overshoot0_pct"),
                    "deciding": v.get("deciding"), "lowest_fail_pF": v.get("lowest_fail_pF"),
                    "non_monotonic": v.get("non_monotonic"), "tested": tested_map.get(cid, []), "values": vals})
    return out


def spec_zero(s):
    """The specification cell at zero stray for a what-if set: S13 record (non-G) or arm G (class G)."""
    t = s["t"]
    if s["class"] == "G":
        v = s14_values(t, s["corner"], [0], whatif=False, phase="armG")
        e = v.get(0)
        return None if not e or e.get("ne") else e["closed"]
    p = point(t, s["corner"], 0, whatif=False, phase="sweep")
    r = s13_records().get((budget.point_id(p), "closed"))
    if r is None or r["status"] != "OK":
        return None
    m = dict(r["metrics"])
    _, k = cache_text_key(r["key"])
    f = cache_files(r["key"], ["ac0"])["ac0"] if k == r["key"] else None
    if f is not None:  # the -3 dB bandwidth was not recorded by S13; read from the key-bound cached AC table
        tab = read_any(f)
        m["ac"] = {key: {**a, "f_3dB_Hz": runner.ac_metrics(tab, key.split("@")[1])["f_3dB_Hz"]}
                   for key, a in m["ac"].items()}
    return m


def cost_row(s, wz, sz):
    if wz is None or sz is None:
        return {"status": "NOT EVALUATED", "reason": "no accepted zero-stray deck for one of the two cells"}
    k = next(iter(sz["ac"]))
    a, b = wz["ac"][k], sz["ac"][k]
    dg, dp = a["gain_20k_dB"] - b["gain_20k_dB"], a["phase_20k_deg"] - b["phase_20k_deg"]
    out = {"path": k, "gain_20k_dB_diff": round(dg, 4), "phase_20k_deg_diff": round(dp, 3),
           "f_3dB_Hz": {"specification": b.get("f_3dB_Hz"), "what_if": a.get("f_3dB_Hz")},
           "noise_uVrms": {"specification": sz["noise"]["out"]["integrated_uVrms"],
                           "what_if": wz["noise"]["out"]["integrated_uVrms"]},
           "k6_s": {"specification": sz.get("k6"), "what_if": wz.get("k6")} if "k6" in sz else None}
    if s["class"] in ("E-audio", "G") and abs(dp) > runner.K7_DEG:
        out["note"] = "exceeds the 2 deg of K7 against the specification cell"
    return out


def paper_of(nets):
    rows = s13_rows()
    return max(rows[n]["c_paper"]["c_paper_pF"] for n in nets), {n: rows[n]["c_paper"] for n in nets}


def parts_of(nets):
    rows = s13_rows()
    return [p for n in nets for p in rows[n]["parts_on_net"]]


def common_reasons(c, nets):
    reasons = []
    parts = parts_of(nets)
    io = sorted({p["ref"] for p in parts if p["inventory_line"] == "IDENTITY OPEN"})
    if io:
        reasons.append("IDENTITY OPEN: " + ", ".join(io))
    if c["subclass"] == "G":
        reasons.append(PROVISIONAL_G)
    if c["tmux"]:
        reasons.append("TMUX6112PWR on-capacitance is not a retained fact (bracketed 0 / 100 pF)")
    return reasons


def whatif_table():
    sets = arm_w_sets()
    rows = []
    for s in sets:
        for wf in ([True] if s["class"] != "G" else [False, True]):
            t, c = s["t"], s["t"]["circuit"]
            phase = "whatif" if wf else "armG"
            ent = s14_values(t, s["corner"], VALUES_W, whatif=wf, phase=phase)
            cid = json.dumps(s["corner"], sort_keys=True)
            lim = corner_limit(s["class"], ent, CAND_W) if len(ent) == len(VALUES_W) else \
                {"status": "INCOMPLETE", "c_lim_pF": None}
            lim15 = corner_limit(s["class"], ent, CAND_W, only_k1_k5=True) if len(ent) == len(VALUES_W) else \
                {"status": "INCOMPLETE", "c_lim_pF": None}
            paper, per_net = paper_of(t["nets"])
            reasons = common_reasons(c, t["nets"])
            br = None
            if "bracket" in s["corner"] and wf:
                br = bracket_check(s, lim.get("c_lim_pF") if lim.get("status") == "OK" else None)
                reasons += br.get("provisional_reasons", []) if br["status"] == "OK" else \
                    [f"bracket check {br['status']}"]
            pairs = None
            if lim.get("status") == "OK" and lim.get("c_lim_pF") and 0 in ent:
                pairs = pair_verdicts(t, s["corner"], lim["c_lim_pF"], wf, ent[0], s["class"])
                bad = [x for x in pairs if not x["pass"]]
                if bad:
                    reasons.append("Ruling 6 output pair fails at C_lim (" + ", ".join(
                        f"{x['out_pF']:g} pF: {'/'.join(x['failed'])}" for x in bad) + ")")
            label, c_lim, deciding = row_label({cid: lim}, paper, reasons=reasons, whatif=wf, arm_w=True)
            l15, c15, _ = row_label({cid: lim15}, paper, reasons=[], whatif=wf, arm_w=True)
            row = {"id": ("what-if " if wf else "arm G ") + s["id"], "whatif": wf, "class": s["class"],
                   "subclass": c["subclass"], "topology": t["key"], "nets": t["nets"], "corner": s["corner"],
                   "c_paper_pF": paper, "c_paper": per_net, "label": label, "c_lim_pF": c_lim, "deciding": deciding,
                   "limit_k1_to_k5_only": {"label": l15, "c_lim_pF": c15}, "provisional_reasons": reasons
                   if label.replace(WHATIF_PREFIX, "").startswith("PROVISIONAL") else [],
                   "corners": corner_view({cid: lim}, {cid: VALUES_W}, {cid: ent}), "bracket_check": br,
                   "outpair": pairs, "parts_on_net": parts_of(t["nets"]),
                   "part": "KEMET C0603C100J5GACTU (line-audio-feedback-c), ideal 10 pF from OUT to the protected node"
                   if wf else None}
            if c["subclass"] == "G":
                row["notes"] = [G_TRIM0, G_LADDER_NOTE, "LM13700 identity limit: every class G row is PROVISIONAL"]
            if wf:
                wz = ent.get(0, {}).get("closed") if ent.get(0) and not ent[0].get("ne") else None
                row["vs_specification_20kHz"] = cost_row(s, wz, spec_zero(s))
            rows.append(row)
    validate_rows(rows, whatif_table=True)
    return rows


def rescore_table():
    rows = []
    s13 = s13_rows()
    for t in rescore_topologies():
        c = t["circuit"]
        lims = rescore_corner_limits(t)
        lims15 = {}
        ents, tested = {}, {}
        for corner in cells.corners_of(c):
            cid = json.dumps(corner, sort_keys=True)
            ents[cid] = rescore_values(t, corner)
            tested[cid] = sorted(ents[cid])
            lims15[cid] = corner_limit(c["subclass"], ents[cid], rescore_candidates(t, corner), only_k1_k5=True) \
                if lims[cid]["status"] != "INCOMPLETE" else lims[cid]
        d = deciding_corner(lims)
        pairs = None
        if d:
            zc = json.dumps(d[0], sort_keys=True)
            pairs = pair_verdicts(t, d[0], d[1]["c_lim_pF"], False, ents[zc][0], c["subclass"])
        for net in sorted(t["nets"]):
            r13 = s13[net]
            paper = r13["c_paper"]["c_paper_pF"]
            reasons = common_reasons(c, [net])
            if pairs:
                bad = [x for x in pairs if not x["pass"]]
                if bad:
                    reasons.append("Ruling 6 output pair fails at C_lim (" + ", ".join(
                        f"{x['out_pF']:g} pF: {'/'.join(x['failed'])}" for x in bad) + ")")
            label, lim, deciding = row_label(lims, paper, reasons=reasons, whatif=False, arm_w=False)
            l15, c15, _ = row_label(lims15, paper, reasons=[], whatif=False, arm_w=False)
            row = {"net": net, "class": c["class"], "subclass": c["subclass"], "topology": t["key"],
                   "amplifier": r13["amplifier"], "parts_on_net": r13["parts_on_net"], "c_paper": r13["c_paper"],
                   "s13_label": r13["label"], "label": label, "c_lim_pF": lim, "deciding": deciding,
                   "limit_k1_to_k5_only": {"label": l15, "c_lim_pF": c15},
                   "provisional_reasons": reasons if label.startswith("PROVISIONAL") else [],
                   "corners": corner_view(lims, tested, ents), "outpair": pairs}
            if lim is not None and label.startswith(("BUDGET", "PROVISIONAL")):
                row["allowance_pF"] = round(lim - paper, 2)
                row["hpwl_max_mm"] = budget.hpwl_max(lim, r13["c_paper"]["n_via"], r13["c_paper"]["n_pad"])
            rows.append(row)
    validate_rows(rows, whatif_table=False)
    return rows


def ic_table(wrows, rrows):
    """S7 (DS-178): an IC is supported only when every row of its blocker route and on its own pins has a plain
    limit above paper. What-if, relative-form and PROVISIONAL rows are conditional on an owner decision."""
    s13 = s13_rows()
    r_by_net = {r["net"]: r for r in rrows}
    w_by_net = {}
    for r in wrows:
        for n in r["nets"]:
            w_by_net.setdefault(n, []).append(r)
    out = {}
    for ic in ICS:
        nets = [n for _, n in cells.BINDING[ic]] + [n for n, r in s13.items() if r["amplifier"]["ref"] == ic]
        if ic == "U5210":
            nets += [n for _, n in cells.BINDING["U8409"]] + [n for n, r in s13.items()
                                                              if r["amplifier"]["ref"] == "U8409"]
        rows = []
        for n in sorted(set(nets)):
            spec = r_by_net.get(n, {}).get("label") or next((r["label"] for r in w_by_net.get(n, []) if not r["whatif"]),
                                                            None) or s13[n]["label"]
            source = "S14 re-score" if n in r_by_net else ("S14 arm G" if any(not r["whatif"] for r in w_by_net.get(n, []))
                                                         else "S13 label (not in S14 scope)")
            wi = [r["label"] for r in w_by_net.get(n, []) if r["whatif"]]
            rows.append({"net": n, "class": s13[n]["class"], "label": spec, "label_source": source, "what_if": wi,
                         "status": row_status(spec, wi)})
        out[ic] = {"rows": rows, "supported": all(r["status"] == "supports" for r in rows),
                   "conditional": any(r["status"] == "conditional on an owner decision" for r in rows)}
    validate_ics(out)
    return out


def plain_budget(label):
    return label.startswith("BUDGET") and "BASELINE EXCEEDS" not in label and not label.startswith(WHATIF_PREFIX)


def row_status(spec, whatif_labels):
    if plain_budget(spec):
        return "supports"
    cond = spec.startswith("PROVISIONAL") or "BASELINE EXCEEDS" in spec or \
        any(x[len(WHATIF_PREFIX):].startswith(("BUDGET", "PROVISIONAL")) for x in whatif_labels)
    return "conditional on an owner decision" if cond else "blocks"


def validate_ics(t):
    """N11: an IC is never supported through a blocked, unevaluated, failing, what-if, relative or PROVISIONAL row."""
    errs = []
    for ic, v in t.items():
        if v["supported"] and any(not plain_budget(r["label"]) or r["status"] != "supports" for r in v["rows"]):
            errs.append(f"{ic}: supported through a row that is not a plain budget")
    if errs:
        raise ValueError("per-IC table rejected: " + "; ".join(errs))


METHOD_LIMITS = budget.METHOD_LIMITS + [
    "the feedback capacitor is an ideal 10 pF element (C0603C100J5GACTU has no retained vendor model)",
    "its +/-5 % tolerance is not swept; the factor of two stands in for it",
    "class G uses a two-step tolerance ladder (reltol=1e-5, then default)",
    "arm R re-uses the S13 records and waveforms; the cache binding is by the recorded metrics, not by a data hash",
]


def evaluate(write=True):
    RES["r"] = load_results()
    w = whatif_table()
    r = rescore_table()
    ics = ic_table(w, r)
    wj = {"status": STATUS, "method_limits": METHOD_LIMITS, "rows": w}
    rj = {"status": STATUS, "method_limits": METHOD_LIMITS, "rows": r, "per_ic": ics}
    if write:
        WHATIF.write_text(json.dumps(wj, indent=1, sort_keys=True) + "\n")
        RESCORE.write_text(json.dumps(rj, indent=1, sort_keys=True) + "\n")
    return wj, rj


def write_result():
    res = load_results()
    b = Bounds()
    led = b.entries()
    sl = [json.loads(x) for x in SLICES.read_text().splitlines() if x.strip()] if SLICES.exists() else []
    guards = {p.name: json.loads(p.read_text()) for p in sorted(CK.glob("guard-*.json"))}
    arm0 = json.loads((CK / "arm0.json").read_text()) if (CK / "arm0.json").exists() else None
    by_kind = {}
    for x in led:
        by_kind[x["kind"]] = by_kind.get(x["kind"], 0) + 1
    recorded = {k for r in res.values() for a in r.get("attempts", []) if a.get("key") for k in [a["key"]]}
    recorded |= {r.get("key") for r in res.values() if r.get("deck") in ("k5second",) and r.get("key")}
    recorded |= {(r.get("replay") or {}).get("key") for r in res.values() if r.get("deck") == "rescore"}
    out = {"status": STATUS, "brief_sha256": sha_file(BRIEF), "pinned_inputs": pins14(), "models": budget.MODEL_PINS,
           "study_files": {f: sha_file(f"scripts/stack/studies/mc04_s14_feedback_capacitor/{f}") for f in
                           ("cells.py", "runner.py", "budget.py", "guard.py", "s13_pinned.py", "s14.py", "test_s14.py")},
           "fingerprint": budget.fingerprint(), "arm0": arm0, "slices": sl, "guards": guards,
           "invocations": {"total": len(led), "by_kind": by_kind, **b.counts(led),
                           "unrecorded_in_results": sum(1 for x in led if x["key"] not in recorded and
                                                        x["kind"] not in ("seed", "control"))},
           "caps": {"total": CAP_TOTAL, "seed_invocations": CAP_SEED_INV, "seeds": CAP_SEEDS, "replays": CAP_REPLAYS},
           "arm_time_s": b.prior_arm_s(), "ceilings_s": {"nonG": NONG_CEILING_S, "G": G_CEILING_S},
           "records": len(res),
           "whatif_sha256": hashlib.sha256(WHATIF.read_bytes()).hexdigest() if WHATIF.exists() else None,
           "rescore_sha256": hashlib.sha256(RESCORE.read_bytes()).hexdigest() if RESCORE.exists() else None}
    RESULT.write_text(json.dumps(out, indent=1, sort_keys=True) + "\n")


# ------------------------------------------------------------------------------------------------ check

def check():
    """Rebuild every deck text from results.jsonl (no simulation), re-apply P10 and the stimulus rule, rebuild the
    second decks from their recorded scale, and rebuild both tables."""
    RES["r"] = res = load_results()
    tp = topo()["topo"]
    bad = []
    for (pid, deck), rec in sorted(res.items()):
        if deck in ("group", "gend", "done", "rescore"):
            continue
        p = rec["point"]
        t = tp.get(p["topology"])
        if t is None:
            bad.append(f"{pid}: unknown topology")
            continue
        if deck == "seed":
            net = budget.seed_netlist(t, p, rec["kind"])
            if budget.seed_id(net) != pid:
                bad.append(f"{pid}: seed netlist differs")
            for a in rec["attempts"]:
                if a.get("key") and runner.deck_key(runner.seed_text(net, a["method"], a.get("source"), a.get("value"),
                                                                     a.get("nodeset", ()))) != a["key"]:
                    bad.append(f"{pid}: seed deck key differs")
            if rec.get("valid") and budget.seed_validity(t["circuit"], rec["kind"], rec["reference"], rec["expected_dc"]):
                bad.append(f"{pid}: seed marked valid but fails S6.4")
            if rec.get("exclude", []) != nc_nodes(t["circuit"], net + "\n.control\n"):
                bad.append(f"{pid}: no-connect set differs from the rule")
            continue
        if budget.point_id(p) != pid:
            bad.append(f"{pid}: point id")
            continue
        seed = (res.get((rec.get("seed_id"), "seed")) or s13_seed(rec.get("seed_id")))
        if seed is None:
            if rec.get("status") == "OK":
                bad.append(f"{pid} {deck}: seed missing")
            continue
        ns = seed.get("nodeset", [])
        if deck == "k5second":
            if rec.get("scale") is None:
                continue
            texts = budget.closed_texts(t, p, ns, k5_scale=rec["scale"])
            item = next(x for x in texts if x[0] == rec["step"])
            if runner.deck_key(item[1]) != rec["key"]:
                bad.append(f"{pid}: second deck does not rebuild from its recorded scale")
            why = identity(p, "closed", ns, rec["step"], item[1], scale=rec["scale"],
                           k5_t0=item[3]["windows"]["K5_step"][0][0])
            if why:
                bad.append(f"{pid}: second deck: {why}")
            continue
        texts = budget.loop_texts(t, p, ns, ladder(t, deck)) if deck == "loop" else budget.closed_texts(t, p, ns)
        keys = {runner.deck_key(x[1]): x for x in texts}
        for a in rec["attempts"]:
            if a.get("key") and a["key"] not in keys:
                bad.append(f"{pid} {deck}: deck key differs from the rebuilt text")
        for k, x in keys.items():
            if any(a.get("key") == k for a in rec["attempts"]):
                why = identity(p, deck, ns, x[0], x[1])
                if why:
                    bad.append(f"{pid} {deck}: {why}")
        if rec["status"] == "OK":
            excl = nc_nodes(t["circuit"], texts[0][1])
            if budget.accept_op(rec["metrics"]["op"], seed["reference"], excl):
                bad.append(f"{pid} {deck}: recorded operating point differs from its seed")
    old_w = json.loads(WHATIF.read_text()) if WHATIF.exists() else None
    old_r = json.loads(RESCORE.read_text()) if RESCORE.exists() else None
    w, r = evaluate(write=False)
    norm = lambda x: json.dumps(json.loads(json.dumps(x, sort_keys=True)), sort_keys=True)  # noqa: E731
    same = old_w is not None and norm(old_w) == norm(w) and old_r is not None and norm(old_r) == norm(r)
    print(f"records rebuilt: {len(res)}; mismatches: {len(bad)}; whatif.json and rescore.json identical: {same}")
    for x in bad[:20]:
        print(" ", x)
    return 0 if not bad and same else 1


def main():
    ap = argparse.ArgumentParser()
    g = ap.add_mutually_exclusive_group(required=True)
    g.add_argument("--arm0", metavar="FETCHED_ZIP")
    g.add_argument("--run", metavar="SLICE_ID")
    for a in ("--evaluate", "--check"):
        g.add_argument(a, action="store_true")
    ap.add_argument("--slice-min", type=float, default=27.0)
    a = ap.parse_args()
    if a.arm0:
        arm0(a.arm0)
    elif a.run:
        drive(a.slice_min, a.run)
    elif a.evaluate:
        evaluate()
        write_result()
    elif a.check:
        sys.exit(check())


if __name__ == "__main__":
    main()
