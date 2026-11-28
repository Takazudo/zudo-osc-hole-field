"""MC04-S13 deck builders: protected-node cells extracted from the specification.

The netlist is rebuilt from `design.spec.instrument.specification()` (part values and nets) and must match
`design/reports/io-partition.json` `package_units` pin for pin; a mismatch is an error. A cell is extracted from
the amplifier unit that owns a protected node by one rule (brief Ruling 5, "Interpretations made" in the report):

* every part on the unit's OUT, IN- and IN+ nets is included, and the network is followed through passives;
* a designated source net of the class (stimulus table) is an ideal source and is not followed;
* another amplifier's output pin is an ideal source at 0 V (REF5 / REFN5 at +5 V / -5 V): an AC ground;
* another amplifier's inverting input is a virtual ground and is replaced by AGND;
* another amplifier's or a comparator's non-inverting input is open (its input capacitance is covered by the
  fixed 20 pF output stray and its 0 / 100 pF pair);
* an unmodelled semiconductor ends the network: behind >= 10 kOhm on the output it is bracketed (its node to AGND,
  and open; Ruling 6); the TMUX6112PWR on the REF9 output is an output-capacitance pair 0 / 100 pF (Ruling 6); on
  an amplifier input, or behind < 10 kOhm on the output, the node is BLOCKED.

Passives are ideal elements at their specification value. No diode or transistor `.model` line is written.
"""
from __future__ import annotations

import hashlib
import json
import math
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

STUDY = Path(__file__).resolve().parent
LINKS = ("P-K-P-L12.02.01.02", "P-K-P-L03.01", "P-K-P-L13.01.01.01", "P-K-P-L13.01.01.02", "P-K-P-L13.01.02.01",
         "P-K-P-L15.02.01.01")
GRIDS = ("2", "0.5", "0.25")
SUFFIX = re.compile(r"(_FB|_SUM|_SENSE)$")
AMP_MPNS = {"OPA4196IDR": "OPAx196", "OPA4197IDR": "OPAx197", "OPA4197IPWR": "OPAx197"}
OTA_MPN = "LM13700M/NOPB"
AMP_PINS = {1: ("1", "2", "3"), 2: ("7", "6", "5"), 3: ("8", "9", "10"), 4: ("14", "13", "12")}  # OUT, IN-, IN+
RAILS = {"+12V": "vp", "-12V": "vn", "AGND": "0"}
REF_DC = {"REF5": 5.0, "REFN5": -5.0}
MODEL_LIBS = {"OPAx196": ".circuit-cache/sources/opa196-model/OPAx196.LIB",
              "OPAx197": ".circuit-cache/sources/opa197-model/OPAx197.LIB",
              "LM13700/NS": "design/spec/modules/spice/filter-model/LM13700.MOD"}
OUT_STRAY_PF = 20.0
# Retained IABC corners: COMMAND / 12.4 kOhm BIAS_SENSE through the PNP servo (wavefolder.py: TARGET = 5 V - COMMAND,
# EMITTER = TARGET, so I = (REF5 - EMITTER) / 12.4 kOhm = COMMAND / 12.4 kOhm; PNP alpha = 1 ASSUMED). The retained
# wavefolder report gives COMMAND from 0.250018352 V (lowest operating, fold 0.25 V) to 5.17626909 V (control limit).
IABC_A = {"low": 0.250018352 / 12.4e3, "high": 5.17626909 / 12.4e3}


class Blocked(Exception):
    pass


def sha256(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


# ------------------------------------------------------------------------------------------------ netlist

_NETLIST = None


def netlist():
    """Parts by (ref, unit) with values and full net names, checked against io-partition package_units."""
    global _NETLIST
    if _NETLIST is not None:
        return _NETLIST
    from design.spec.instrument import specification
    from scripts.schgen.core import designator
    families, instances = specification()
    by_name = {f.name: f for f in families}
    parts, order = {}, 0
    for inst in instances:
        fam = by_name[inst.family]
        for p in fam.parts:
            ref = designator(p, inst)
            pins = {pin: (None if n is None else n if n in fam.global_nets else f"/{inst.name}/{n}")
                    for pin, n in p.pins.items()}
            parts[(ref, p.unit)] = {"ref": ref, "unit": p.unit, "value": p.value, "mpn": p.attributes.get("MPN", ""),
                                    "role": p.attributes.get("Role", ""), "pins": pins, "key": p.key,
                                    "inst": inst.name, "order": order, "dnp": p.dnp}
            order += 1
    io = json.loads((ROOT / "design/reports/io-partition.json").read_text())
    want = {}
    for u in io["package_units"]:
        want.setdefault(u["ref"], {}).update(u["pins"])
    got = {}
    for p in parts.values():
        got.setdefault(p["ref"], {}).update(p["pins"])
    bad = [(r, pin) for r in want for pin, n in want[r].items() if got.get(r, {}).get(pin) != n]
    if bad:
        raise RuntimeError(f"specification netlist differs from io-partition package_units: {bad[:5]}")
    phys = {p["ref"]: p for p in io["physical_packages"]}
    for p in parts.values():
        pk = phys.get(p["ref"])
        if pk is not None and (pk.get("mpn") or "") != p["mpn"] and p["mpn"]:
            raise RuntimeError(f"MPN differs for {p['ref']}: {pk.get('mpn')} vs {p['mpn']}")
    net_pins = {}
    for k, p in parts.items():
        for pin, n in p["pins"].items():
            if n:
                net_pins.setdefault(n, []).append((k, pin))
    _NETLIST = {"parts": parts, "net_pins": net_pins, "phys": phys, "io": io}
    return _NETLIST


def is_amp(p):
    return p["mpn"] in AMP_MPNS and p["unit"] in AMP_PINS


def amp_pins(p):
    o, m, pl = AMP_PINS[p["unit"]]
    return p["pins"][o], p["pins"][m], p["pins"][pl]


# ------------------------------------------------------------------------------------------------ census (P6)

def census():
    c = json.loads((ROOT / "scripts/stack/studies/mc04_s12_five_ic_joint/census.json").read_text())
    fps, per_link = set(), {}
    for link in LINKS:
        s = set()
        for g in GRIDS:
            s |= set(c["links"][link][g]["t1_by_footprint"])
        per_link[link] = len(s)
        fps |= s
    nl = netlist()
    nets = sorted({n for p in nl["parts"].values() if p["ref"] in fps for n in p["pins"].values()
                   if n and SUFFIX.search(n)})
    rows = {}
    for n in nets:
        rows[n] = classify(n)
    counts = {}
    for r in rows.values():
        counts[r["class"]] = counts.get(r["class"], 0) + 1
    return {"footprints": sorted(fps), "footprint_count": len(fps), "per_link": per_link, "nets": rows,
            "net_count": len(nets), "class_counts": dict(sorted(counts.items()))}


EXPECTED_COUNTS = {"A": 11, "B": 23, "C": 10, "D": 1, "E": 9, "F": 5, "G": 1, "H": 3, "I": 1}
BINDING = {  # brief "The nodes that decide each IC": footprint -> net
    "U8409": [("C8313", "/M4A/C1c45d6_W_SENSE"), ("R7216", "/A02/Cc045d2_W_SENSE"), ("U8411", "/M4B/Ccb7527_FB"),
              ("U8411", "/M4B/C24ce01_SUM"), ("U8411", "/M4B/C24ce01_W_SENSE"), ("U8411", "/M4B/C1c45d6_W_SENSE")],
    "U5210": [("R8356", "/M4A/C24ce01_W_SENSE")],
    "U5110": [("U5205", "/W1/PRE_GAIN_SUM"), ("C5218", "/W1/C01cf3e_FB"), ("R5268", "/W1/C01cf3e_FB"),
              ("R5149", "/W2/FOLDER_SUM"), ("R5162", "/W2/F4_SUM")],
    "U5209": [("R5228", "/W1/CONTROL_SUM"), ("R5250", "/W1/DRIVE_INV_SUM"), ("R5251", "/W1/DRIVE_INV_SUM"),
              ("R5253", "/W1/F1_SUM"), ("C8409", "/M4B/C865f36_FB"), ("R2335", "/F3/C8c344f_W_SENSE"),
              ("U5205", "/W1/PRE_GAIN_SUM"), ("RV5205", "/W1/PRE_GAIN_SUM")],
    "L15.02.01.01 neighbours": [("R8456", "/M4B/C24ce01_W_SENSE"), ("R4238", "/E2/REF9_FB"),
                                ("R8471", "/M4B/TARGET_SUM"), ("C8408", "/M4B/C38051c_SUM")],
}


def check_census(cen):
    errors = []
    if cen["footprint_count"] != 107:
        errors.append(f"footprints {cen['footprint_count']} != 107")
    if cen["net_count"] != 64:
        errors.append(f"nets {cen['net_count']} != 64")
    if cen["class_counts"] != EXPECTED_COUNTS:
        errors.append(f"class counts {cen['class_counts']} != {EXPECTED_COUNTS}")
    nl = netlist()
    for ic, rows in BINDING.items():
        for ref, net in rows:
            if ref not in cen["footprints"]:
                errors.append(f"{ic}: {ref} not in census")
            on = any(p["ref"] == ref and net in p["pins"].values() for p in nl["parts"].values())
            if not on:
                errors.append(f"{ic}: {ref} not on {net}")
            if net not in cen["nets"]:
                errors.append(f"{ic}: {net} not a protected net")
    return errors


# ------------------------------------------------------------------------------------------------ classification

def owner_unit(net):
    """The amplifier unit (or the PRE_GAIN amplifier for the OTA node) whose input is the protected net."""
    nl = netlist()
    for k, pin in nl["net_pins"][net]:
        p = nl["parts"][k]
        if is_amp(p):
            o, m, pl = AMP_PINS[p["unit"]]
            if pin in (m, pl):
                return k, ("IN-" if pin == m else "IN+")
    raise RuntimeError(f"{net}: no amplifier input on the net")


def classify(net):
    nl = netlist()
    k, pin = owner_unit(net)
    amp = nl["parts"][k]
    cell, part = amp["role"].split(":", 1)
    on_net = [nl["parts"][kk] for kk, _ in nl["net_pins"][net]]
    has_ota = any(p["mpn"] == OTA_MPN for p in on_net)
    has_cap = any(p["ref"].startswith("C") for p in on_net)
    local = net.split("/")[-1]
    if cell == "remote_buffer":
        cls = "A"
    elif cell == "bipolar_attenuverter":
        cls = "B"
    elif cell == "dc_control_source":
        cls = "C"
    elif cell == "level_attenuator":
        cls = "D"
    elif re.fullmatch(r"F\d_SUM", local):
        cls = "F"
    elif has_ota:
        cls = "G"
    elif local in ("REF9_FB", "OUTPUT_FB"):
        cls = "H"
    elif local == "RISE_EXPO_SUM":
        cls = "I"
    elif local.endswith("_SUM") and pin == "IN-" and not has_cap:
        cls = "E"
    else:
        raise RuntimeError(f"{net}: unclassified ({amp['role']})")
    sub = None
    if cls == "E":
        sub = "E-audio" if amp["role"] in ("wavefolder:DRIVE_SUM", "wavefolder:DRIVE_INVERT") else "E-control"
    if cls == "H":
        sub = "H-REF9" if local == "REF9_FB" else "H-output"
    return {"class": cls, "subclass": sub or cls, "amp_ref": amp["ref"], "amp_unit": amp["unit"], "pin": pin,
            "amp_mpn": amp["mpn"], "amp_role": amp["role"]}


# ------------------------------------------------------------------------------------------------ values

UNITS = {"": 1, "p": 1e-12, "n": 1e-9, "u": 1e-6, "µ": 1e-6, "m": 1e-3, "k": 1e3, "K": 1e3, "M": 1e6, "G": 1e9}


def parse_value(text):
    m = re.match(r"^\s*([0-9.]+(?:e[+-]?\d+)?)\s*([pnuµmkKMG]?)\s*(Ω|F|ohm)?", text)
    if not m:
        raise ValueError(f"unparsed value {text!r}")
    return float(m[1]) * UNITS[m[2]]


def resistance_code(mpn):
    """PTV09A-4020F-B103 -> 10 kOhm; TC33X-2-103E -> 10 kOhm (three-digit resistance code)."""
    m = re.search(r"(?:-B|-)(\d)(\d)(\d)E?$", mpn)
    if not m:
        raise ValueError(f"no resistance code in {mpn}")
    return float(m[1] + m[2]) * 10 ** int(m[3])


def kind(p):
    ref = p["ref"]
    if ref.startswith("RV"):
        return "pot"
    if ref.startswith(("R", "RB")):
        return "R"
    if ref.startswith("C"):
        return "C"
    if is_amp(p):
        return "amp"
    if p["mpn"] == OTA_MPN:
        return "ota"
    return "semi"


def canon(net, cell_prefix=None):
    """Instance-free net name: '/M4B/Cfaa69a_FB' -> 'fb', '/W1/PRE_GAIN_TRIM' -> 'pre_gain_trim'."""
    if net in RAILS:
        return RAILS[net]
    local = net.split("/")[-1]
    local = re.sub(r"^C[0-9a-f]{6}_", "", local)
    return re.sub(r"[^a-z0-9_]", "_", local.lower())


# ------------------------------------------------------------------------------------------------ extraction

def _namespace(p):
    return re.sub(r"^G\d+_", "", p["key"]).rsplit(".", 1)[0].rsplit("__", 1)[0]


def cell_terminals(amp):
    """Map the standard terminal names of the amplifier's cell to nets, from the parts of its cell namespace."""
    from design.spec.cells._builder import AMP, CELLS, PIN_ALIASES, resolve
    nl = netlist()
    cell = amp["role"].split(":", 1)[0]
    if cell not in CELLS:
        return {}
    amp_nets = set(amp_pins(amp))
    ns = {_namespace(p) for p in nl["parts"].values() if p["inst"] == amp["inst"] and p["role"].startswith(cell + ":")
          and not is_amp(p) and amp_nets & set(p["pins"].values())}
    if len(ns) != 1:
        raise RuntimeError(f"{amp['ref']}: cell namespace not unique: {ns}")
    ns = ns.pop()
    specs = {x["ref"]: x for x in CELLS[cell]["parts"]}
    terms = {}
    for p in nl["parts"].values():
        if p["inst"] != amp["inst"] or not p["role"].startswith(cell + ":") or _namespace(p) != ns:
            continue
        sref = p["role"].split(":", 1)[1]
        if sref not in specs or specs[sref].get("opamp_role"):
            continue
        pid = resolve(specs[sref])[0]
        aliases = PIN_ALIASES.get(pid, {})
        for tname, tval in specs[sref]["terminals"].items():
            pin = aliases.get(tname, tname)
            if p["pins"].get(pin):
                terms.setdefault(tval, p["pins"][pin])
    return terms


def sources_for(net, info, amp):
    """Designated source nets of the class (stimulus table) -> canonical source role."""
    nl = netlist()
    out, inm, inp = amp_pins(amp)
    cls = info["class"]
    t = cell_terminals(amp)
    src = {}
    if cls == "A":
        src[inp] = "sig"
        src[t["REMOTE"]] = "harness"
    elif cls == "B":
        src[t["BUFFERED_INPUT"]] = "buf"
        src[t["REMOTE_INPUT"]] = "rem"
    elif cls == "C":
        src[t["REF_HIGH"]] = "refh"
        if t["REF_LOW"] != "AGND":
            src[t["REF_LOW"]] = "refl"
    elif cls == "D":
        src[t["REMOTE_INPUT"]] = "rem"
    elif cls in ("E", "F"):
        ins = []
        for k, pin in nl["net_pins"][inm]:
            p = nl["parts"][k]
            if kind(p) != "R":
                continue
            other = [n for n in p["pins"].values() if n != inm][0]
            if other != out:
                ins.append((p["order"], parse_value(p["value"]), other, p["ref"]))
        ins.sort()
        local = net.split("/")[-1]
        if info["subclass"] == "E-audio" or cls == "F":
            want = {"FOLDER_SUM": "PRE_GAIN", "DRIVE_INV_SUM": "FOLDER_NEG"}.get(local)
            chosen = [x for x in ins if x[1] == 100e3 and (want is None or x[2].endswith("/" + want))]
        else:
            chosen = [x for x in ins if x[1] == 100e3]
        if not chosen:
            raise RuntimeError(f"{net}: no 100 kOhm signal input")
        src[chosen[0][2]] = "sig"
    elif cls == "G":
        ota = [nl["parts"][k] for k, _ in nl["net_pins"][inm] if nl["parts"][k]["mpn"] == OTA_MPN][0]
        pins = ota_pins(ota)
        sig_net = pins["4"]
        top = [nl["parts"][k] for k, _ in nl["net_pins"][sig_net] if kind(nl["parts"][k]) == "R"
               and parse_value(nl["parts"][k]["value"]) == 100e3][0]
        src[[n for n in top["pins"].values() if n != sig_net][0]] = "sig"
        src[pins["1"]] = "iabc"
        off = [nl["parts"][k] for k, _ in nl["net_pins"][pins["3"]] if kind(nl["parts"][k]) == "R"
               and parse_value(nl["parts"][k]["value"]) == 470e3][0]
        src[[n for n in off["pins"].values() if n != pins["3"]][0]] = "trim"
    elif cls == "H":
        src[inp] = "ref5" if info["subclass"] == "H-REF9" else "sig"
    return src


def ota_pins(ota):
    nl = netlist()
    pins = {}
    for p in nl["parts"].values():
        if p["ref"] == ota["ref"]:
            pins.update({k: v for k, v in p["pins"].items()})
    return pins


def extract(net, info=None, *, diagnostic=False):
    """Return the cell circuit of a protected net (canonical, instance-free) or raise Blocked.

    `diagnostic=True` is the class F diagnostic only: the BAS16GW-QX pair on IN+ is left out of the deck
    (labelled DIAGNOSTIC, NOT A BUDGET); every other rule is unchanged."""
    nl = netlist()
    info = info or classify(net)
    k_amp, _ = owner_unit(net)
    amp = nl["parts"][k_amp]
    out, inm, inp = amp_pins(amp)
    if info["class"] == "F" and not diagnostic:
        raise Blocked("BAS16GW-QX")
    if info["class"] == "I":
        raise Blocked("BCM847BS,115")
    src = sources_for(net, info, amp)
    core = {out: "out", inm: "inm", inp: "inp"} if out != inm else {out: "out", inp: "inp"}
    names = {}

    def name(n):
        if n in RAILS:
            return RAILS[n]
        if n in core:
            return core[n]
        if n in src:
            return src[n]
        return names.setdefault(n, canon(n))

    elements, included, aux, brackets, tmux, parts_used = [], set(), {}, [], [], []
    frontier, seen = [out, inm, inp], set()
    depth = {out: 0, inm: 0, inp: 0}
    while frontier:
        n = frontier.pop(0)
        if n in seen or n in RAILS:
            continue
        seen.add(n)
        if n in src:
            continue  # an ideal source replaces the net (stimulus table), core input nets included
        if depth[n] > 6:
            raise RuntimeError(f"{net}: extraction did not terminate near {n}")
        others = [(k, pin, nl["parts"][k]) for k, pin in nl["net_pins"][n] if k not in included and k != k_amp]
        if n not in core:
            # Classify a boundary net before including anything on it.
            amp_hits = [(pin, p) for k, pin, p in others if kind(p) == "amp"]
            if any(pin == AMP_PINS[p["unit"]][0] for pin, p in amp_hits):
                aux[n] = REF_DC.get(n.split("/")[-1], 0.0)
                continue
            if any(pin == AMP_PINS[p["unit"]][1] for pin, p in amp_hits):
                aux[n] = "vg"  # another amplifier's inverting input: a virtual ground
                continue
            semis = [p for k, pin, p in others if kind(p) == "semi" and not p["dnp"]]
            if semis:
                feed = [nl["parts"][kk] for kk, _ in nl["net_pins"][n]
                        if kind(nl["parts"][kk]) == "R" and out in nl["parts"][kk]["pins"].values()]
                if not feed or min(parse_value(f["value"]) for f in feed) < 10e3:
                    raise Blocked(semis[0]["mpn"])
                brackets.append({"node": n, "semi": sorted({p["ref"] for p in semis}),
                                 "mpn": sorted({p["mpn"] for p in semis}),
                                 "series_ohm": min(parse_value(f["value"]) for f in feed)})
                aux[n] = "bracket"
                continue
        for k, pin, p in others:
            if k in included:
                continue
            kd = kind(p)
            if kd == "amp":
                o, m, pl = AMP_PINS[p["unit"]]
                if pin in (o, m):
                    raise RuntimeError(f"{net}: amplifier {p['ref']} pin {pin} on core node {n}")
                continue  # non-inverting input of another amplifier: open
            if kd == "ota":
                if info["class"] != "G":
                    raise Blocked(f"unexpected OTA {p['ref']}")
                pins = ota_pins(p)
                parts_used.append(p)
                elements.append({"t": "ota", "ref": p["ref"], "pins": pins})
                for kk, pp in nl["parts"].items():
                    if pp["ref"] == p["ref"]:
                        included.add(kk)
                for q in ("1", "3", "4", "5", "6", "7", "11"):
                    if pins.get(q) and pins[q] not in seen:
                        depth.setdefault(pins[q], depth[n] + 1)
                        frontier.append(pins[q])
                continue
            if kd == "semi":
                if p["dnp"]:
                    continue
                if diagnostic and info["class"] == "F" and n == inp and p["mpn"] == "BAS16GW-QX":
                    continue  # DIAGNOSTIC, NOT A BUDGET: no diode in the deck
                if n == out and p["mpn"] == "TMUX6112PWR":
                    tmux.append(p["ref"])
                    included.add(k)
                    continue
                raise Blocked(p["mpn"])
            included.add(k)
            parts_used.append(p)
            if kd in ("R", "C"):
                elements.append({"t": kd, "ref": p["ref"], "a": p["pins"]["1"], "b": p["pins"]["2"],
                                 "v": parse_value(p["value"])})
            elif kd == "pot":
                elements.append({"t": "pot", "ref": p["ref"], "ccw": p["pins"]["1"], "w": p["pins"]["2"],
                                 "cw": p["pins"]["3"], "v": resistance_code(p["mpn"])})
            for q in p["pins"].values():
                if q and q not in seen:
                    depth.setdefault(q, depth[n] + 1)
                    frontier.append(q)
    # A resistor or capacitor ending on a bracketed/virtual-ground/source node keeps that node; record its kind.
    # Brackets apply only to nets behind the output; a bracket elsewhere would be an unmodelled input part.
    circuit = {"net": net, "class": info["class"], "subclass": info["subclass"],
               "model": AMP_MPNS[amp["mpn"]], "amp": {"ref": amp["ref"], "unit": amp["unit"], "mpn": amp["mpn"]},
               "follower": out == inm, "elements": elements, "aux": {}, "sources": {}, "brackets": [],
               "tmux": tmux, "parts": sorted({p["ref"] for p in parts_used} | {amp["ref"]})}
    for n, role in src.items():
        circuit["sources"][role] = {"net": n, "node": name(n), "dc": REF_DC.get(n.split("/")[-1], 0.0)}
    for n, v in aux.items():
        if v == "vg":
            names[n] = "0"
        elif v == "bracket":
            circuit["brackets"].append({**next(b for b in brackets if b["node"] == n), "canon": name(n)})
        else:
            circuit["aux"][name(n)] = {"net": n, "dc": v}
    circuit["node_names"] = {n: name(n) for n in set(names) | set(core) | set(src)}
    circuit["inp_node"] = name(inp)  # "0" when IN+ is AGND in the specification; the deck must not float it
    for e in elements:
        for key in ("a", "b", "ccw", "w", "cw"):
            if key in e:
                e[key + "_n"] = name(e[key])
        if e["t"] == "ota":
            e["pins_n"] = {q: (name(v) if v else None) for q, v in e["pins"].items()}
    if info["class"] == "A":
        circuit["sources"]["harness"]["dc"] = None  # terminal, not a source: envelope load
    return circuit


# ------------------------------------------------------------------------------------------------ deck text

def fmt(v):
    return f"{v:.6g}"


def corners_of(circuit):
    """Corner dictionaries of a cell (brief "Sweep design")."""
    cls, sub = circuit["class"], circuit["subclass"]
    base = [{}]
    if cls == "A":
        base = [{"harness_c": 0.0}, {"harness_c": 1e-9}]
    elif cls in ("B", "C", "D"):
        base = [{"wiper": 0.5}, {"wiper": 1.0}]
    elif cls == "G":
        base = [{"trim": t, "iabc": i} for t in (0.0, 1.0) for i in ("low", "high")]
    elif sub == "H-REF9":
        base = [{"tmux_c": 0.0}, {"tmux_c": 100e-12}]
    if cls == "F":
        base = [{"fdiag": "inp_agnd"}, {"fdiag": "inp_10k"}]
    if circuit["brackets"]:
        base = [{**c, "bracket": b} for c in base for b in ("agnd", "open")]
    return base


def netlist_lines(circuit, corner, c_stray, swept, *, other=None, other_c=0.0, out_c=OUT_STRAY_PF * 1e-12,
                  whatif=False, loop=False, f_diag=None):
    """Element lines of one point. Node names are canonical; element names are assigned after sorting."""
    raw = []
    for e in circuit["elements"]:
        if e["t"] in ("R", "C"):
            a, b = e["a_n"], e["b_n"]
            if (a, b) != tuple(sorted((a, b))):
                a, b = b, a
            raw.append((e["t"], a, b, fmt(e["v"])))
        elif e["t"] == "pot":
            w = corner.get("wiper", corner.get("trim"))
            if w is None:
                raise RuntimeError("pot without wiper position")
            top, bot = (1 - w) * e["v"], w * e["v"]
            # trimmer: END1(ccw)=1, WIPER=2, END2(cw)=3; position p gives R(1-2) = p * R (brief "trimmer at 0 and 1")
            if "trim" in corner:
                r12, r23 = corner["trim"] * e["v"], (1 - corner["trim"]) * e["v"]
                bot, top = r12, r23
            raw.append(("R", *sorted((e["cw_n"], e["w_n"])), fmt(max(top, 1e-3))))
            raw.append(("R", *sorted((e["w_n"], e["ccw_n"])), fmt(max(bot, 1e-3))))
    for b in circuit["brackets"]:
        if corner.get("bracket") == "agnd":
            raw.append(("V", b["canon"], "0", "0"))
    if corner.get("fdiag") == "inp_agnd":
        raw.append(("V", "inp", "0", "0"))
    lines = []
    count = {}
    for t, a, b, v in sorted(raw):
        count[t] = count.get(t, 0) + 1
        lines.append(f"{t}{count[t]} {a} {b} {v}")
    m = circuit["model"]
    inm_pin = "inm" if not circuit["follower"] else "out"
    if loop:
        inm_pin = "xinm"
    lines.append(f"XU {circuit['inp_node']} {inm_pin} vp vn out {m}")
    for e in circuit["elements"]:
        if e["t"] == "ota":
            p = e["pins_n"]
            order = ["1", "2", "3", "4", "5", "6", "7", "8", "11"]
            nodes = [p.get(q) or f"ota_nc{q}" for q in order]
            lines.append("XOTA " + " ".join(nodes) + " LM13700/NS")
    if circuit["class"] == "A":
        lines.append("Rharness harness 0 10k")
        if corner.get("harness_c"):
            lines.append(f"Charness harness 0 {fmt(corner['harness_c'])}")
    if corner.get("tmux_c"):
        lines.append(f"Ctmux out 0 {fmt(corner['tmux_c'])}")
    if out_c:
        lines.append(f"Cout out 0 {fmt(out_c)}")
    if whatif:
        lines.append("Cwhatif out inm 10p")
    lines.append(f"Cstray {swept} 0 {fmt(c_stray)}")
    if other is not None:
        lines.append(f"Cother {other} 0 {fmt(other_c)}")
    for node, a in sorted(circuit["aux"].items()):
        lines.append(f"Vaux_{node} {node} 0 DC {fmt(a['dc'])}")
    return lines


def header(circuit, title):
    libs = [MODEL_LIBS[circuit["model"]]]
    if any(e["t"] == "ota" for e in circuit["elements"]):
        libs.append(MODEL_LIBS["LM13700/NS"])
    return [title, ".param TEMP=27"] + [f".include {lib}" for lib in libs] + ["Vplus vp 0 12", "Vminus vn 0 -12"]


def topology_key(circuit):
    """Hash of the instance-free cell (elements with values and canonical nodes, sources, model)."""
    blob = {"model": circuit["model"], "class": circuit["subclass"], "follower": circuit["follower"],
            "elements": sorted(json.dumps({k: v for k, v in e.items() if k.endswith("_n") or k in ("t", "v")},
                                          sort_keys=True) for e in circuit["elements"]),
            "sources": sorted((r, s["node"], s["dc"]) for r, s in circuit["sources"].items()),
            "aux": sorted((n, a["dc"]) for n, a in circuit["aux"].items()),
            "brackets": sorted(b["canon"] for b in circuit["brackets"]), "tmux": bool(circuit["tmux"]),
            "inp_node": circuit["inp_node"]}
    return sha256(json.dumps(blob, sort_keys=True).encode())[:16]


# ------------------------------------------------------------------------------------------------ stimulus

AUDIO = {"A", "B", "D", "E-audio", "G", "H-output", "F"}
VT = 0.025852  # kT/q at 27 C


def pwl(points):
    """points: [(t, v)] already monotone in t."""
    out, last = [], None
    for t, v in points:
        if last is not None and t <= last:
            t = last + 1e-12
        out.append(f"{t:.9g} {v:.9g}")
        last = t
    return "PWL(" + " ".join(out) + ")"


class Timeline:
    """Step stimuli per source role; values are offsets on top of the source's DC level."""

    def __init__(self):
        self.p = {}

    def step(self, role, t, v, edge):
        pts = self.p.setdefault(role, [(0.0, 0.0)])
        pts.append((t, pts[-1][1]))
        pts.append((t + edge, v))

    def text(self, role):
        pts = self.p.get(role)
        return pwl(pts) if pts and len(pts) > 1 else None


def cell_gain(circuit, corner):
    """Approximate low-frequency gain from the main source to OUT, used only to size steps (recorded)."""
    sub = circuit["subclass"]
    if sub == "G":
        el = {e["ref"]: e for e in circuit["elements"]}
        rf = 49.9e3 + corner["trim"] * 10e3
        gm = IABC_A[corner["iabc"]] / (2 * VT)
        return gm * (200 / (100e3 + 200)) * rf
    if sub == "H-output":
        return 8.0
    if sub == "H-REF9":
        return 1.8
    return 1.0


def c_tau(circuit, corner):
    """Zero-stray RC time constant of a class C node: (w(1-w)R_pot + R_W) * C_W."""
    pot = next(e for e in circuit["elements"] if e["t"] == "pot")
    rw = next(e["v"] for e in circuit["elements"] if e["t"] == "R" and {e["a_n"], e["b_n"]} == {"w", "inp"})
    cw = next(e["v"] for e in circuit["elements"] if e["t"] == "C" and {e["a_n"], e["b_n"]} == {"inp", "0"})
    w = corner["wiper"]
    return (w * (1 - w) * pot["v"] + rw) * cw


def plan(circuit, corner, k5_scale=None):
    """Windows of every transient criterion (brief stimulus table). Times in seconds.
    S14 Ruling S4: `k5_scale` multiplies the two K5 stimuli only (large step, 20 kHz sine) in a second deck."""
    ks = 1.0 if k5_scale is None else k5_scale
    cls, sub = circuit["class"], circuit["subclass"]
    g = abs(cell_gain(circuit, corner))
    tl, P = Timeline(), {"windows": {}, "tran": [], "notes": []}
    main = {"A": "sig", "B": "buf", "C": "refh", "D": "rem", "E": "sig", "F": "sig", "G": "sig",
            "H": "ref5" if sub == "H-REF9" else "sig"}[cls]
    P["main"] = main
    t = 20e-6
    if cls == "C":
        tau = c_tau(circuit, corner)
        tmax = tau / 2000
        hold4 = hold6 = max(40e-6, 14 * tau)
        hold5 = max(100e-6, 14 * tau)
        P["tau0_s"], P["resolution_fraction"] = tau, tmax / tau
        # injection window first: 100 mV through 1 kOhm at W_SENSE (tran B, after alter Rinj = 1 kOhm)
        tau_inj = (1e3 * (w_th(circuit, corner) + 1e3) / (w_th(circuit, corner) + 2e3)) * 10e-9
        hinj = max(40e-6, 14 * tau_inj)
        tl.step("inj", t, 0.1, 100e-9)
        tl.step("inj", t + hinj, 0.0, 100e-9)
        P["windows"]["K4_inj"] = [(t, t + hinj, 0.1), (t + hinj, t + 2 * hinj, -0.1)]
        t_inj_end = t + 2 * hinj
        P["tran_inj"] = {"tstop": t_inj_end, "tmax": min(20e-9, tau_inj / 200)}
        t = t_inj_end + 20e-6
        # K4: 100 mV step at REF_HIGH (5.0 -> 4.9 -> 5.0 V)
        tl.step(main, t, -0.1, 100e-9)
        tl.step(main, t + hold4, 0.0, 100e-9)
        P["windows"]["K4"] = [(t, t + hold4, -0.1), (t + hold4, t + 2 * hold4, 0.1)]
        t += 2 * hold4
        # K6/K8: 1 V step at REF_HIGH (5 -> 4 -> 5 V)
        tl.step(main, t, -1.0, 1e-6)
        tl.step(main, t + hold6, 0.0, 1e-6)
        P["windows"]["K6"] = [(t, t + hold6, -1.0), (t + hold6, t + 2 * hold6, 1.0)]
        t += 2 * hold6
        # K5: +/-5 V step at REF_HIGH (5 -> -5 -> 5 V)
        tl.step(main, t, -10.0 * ks, 1e-6)
        tl.step(main, t + hold5, 0.0, 1e-6)
        P["windows"]["K5_step"] = [(t, t + hold5, -10.0 * ks), (t + hold5, t + 2 * hold5, 10.0 * ks)]
        t += 2 * hold5
        P["tran"].append({"name": "t1", "tstop": t, "tmax": tmax})
        P["timeline"] = tl
        return P
    tmax = 20e-9
    h4, h5 = 40e-6, 200e-6
    paths = ["buf", "rem"] if cls == "B" else [main]
    if sub == "G":
        s = 0.1 / g
    elif sub == "H-output":
        s = 0.1 / 8
    else:
        s = 0.1
    P["windows"]["K4"] = {}
    for role in paths:
        tl.step(role, t, s, 100e-9)
        tl.step(role, t + h4, 0.0, 100e-9)
        P["windows"]["K4"][role] = [(t, t + h4, s), (t + h4, t + 2 * h4, -s)]
        t += 2 * h4 + 10e-6
    P["k4_source_step_V"] = s
    if sub == "H-REF9":
        P["windows"]["K5_load"] = [(t, t + h5, 1e-3), (t + h5, t + 2 * h5, -1e-3)]
        tl.step("iload", t, 1e-3, 1e-6)
        tl.step("iload", t + h5, 0.0, 1e-6)
        t += 2 * h5 + 20e-6
        P["tran"].append({"name": "t1", "tstop": t, "tmax": tmax})
        t1 = t
        tl.step("iload6", t1 + 50e-6, 1e-4, 1e-6)
        tl.step("iload6", t1 + 50e-6 + 1.5e-3, 0.0, 1e-6)
        P["windows"]["K6_load"] = [(t1 + 50e-6, t1 + 1.55e-3, 1e-4), (t1 + 1.55e-3, t1 + 3.05e-3, -1e-4)]
        P["tran"].append({"name": "t2", "tstop": t1 + 3.05e-3, "tmax": 0.5e-6})
        P["timeline"] = tl
        return P
    amp = {"H-output": 0.6, "G": 5.0}.get(sub, 5.0) * ks
    sine = {"H-output": 1.2, "G": 5.0}.get(sub, 10.0) * ks
    if sub == "B":
        pass
    drive = ["buf", "rem"] if cls == "B" else [main]
    # K5 large step: 0 -> -A -> +A -> -A -> 0 (1 us edges), holds of 200 us
    for role in drive:
        for k, v in enumerate((-amp, amp, -amp)):
            tl.step(role, t + k * h5, v, 1e-6)
        tl.step(role, t + 3 * h5, 0.0, 10e-6)
    P["windows"]["K5_step"] = [(t, t + h5, -amp), (t + h5, t + 2 * h5, 2 * amp), (t + 2 * h5, t + 3 * h5, -2 * amp)]
    P["k5_step_V"] = amp
    t += 3 * h5 + 50e-6
    if cls in ("C",) or sub in ("E-control",):
        P["sine"] = None
    else:
        P["sine"] = {"t0": t, "t1": t + 200e-6, "amp": sine, "f": 20e3, "roles": drive}
        t += 200e-6
    P["tran"].append({"name": "t1", "tstop": t, "tmax": tmax})
    if sub == "E-control":
        t1 = t
        for role in drive:
            tl.step(role, t1 + 50e-6, 1.0, 1e-6)
            tl.step(role, t1 + 50e-6 + 1.5e-3, 0.0, 1e-6)
        P["windows"]["K6"] = [(t1 + 50e-6, t1 + 1.55e-3, 1.0), (t1 + 1.55e-3, t1 + 3.05e-3, -1.0)]
        P["tran"].append({"name": "t2", "tstop": t1 + 3.05e-3, "tmax": 0.5e-6})
    P["timeline"] = tl
    return P


def w_th(circuit, corner):
    pot = next(e for e in circuit["elements"] if e["t"] == "pot")
    w = corner["wiper"]
    return w * (1 - w) * pot["v"]


def closed_text(circuit, corner, lines, k5_scale=None):
    """Closed-loop deck: op, AC (once per path for class B), noise, the transients of plan()."""
    cls, sub = circuit["class"], circuit["subclass"]
    P = plan(circuit, corner, k5_scale)
    tl = P["timeline"]
    src_lines = []
    roles = [r for r in circuit["sources"] if r not in ("harness",)]
    for role in roles:
        s = circuit["sources"][role]
        node = s["node"]
        if role == "iabc":
            src_lines.append(f"Iabc 0 {node} DC {fmt(IABC_A[corner['iabc']])}")
            continue
        dc = s["dc"]
        if role == "trim":
            dc = WAVEFOLDER_OFFSET_V
        chain = [f"Vac_{role} {node} {role}_a DC {fmt(dc)} AC 0"]
        w = tl.text(role)
        nxt = f"{role}_a"
        if w:
            chain.append(f"Vpwl_{role} {nxt} {role}_b {w}")
            nxt = f"{role}_b"
        if P.get("sine") and role in P["sine"]["roles"]:
            sn = P["sine"]
            chain.append(f"Bsin_{role} {nxt} 0 V=(time>{sn['t0']:.9g} && time<{sn['t1']:.9g}) ? "
                         f"{sn['amp']:.6g}*sin(6.283185307179586*{sn['f']:.6g}*(time-{sn['t0']:.9g})) : 0")
        else:
            chain.append(f"Vend_{role} {nxt} 0 0")
        src_lines += chain
    if cls == "C":
        src_lines += ["Rinj inp inj_a 1e12", f"Vinj inj_a 0 DC 0 {tl.text('inj')}"]
    if sub == "H-REF9":
        src_lines += [f"Iload out 0 DC 0 {tl.text('iload')}", f"Iload6 out 0 DC 0 {tl.text('iload6')}"]
    meas = ["v(out)"] + (["v(harness)"] if cls == "A" else [])
    main = P["main"]
    ac = "ac dec 50 10 100meg"
    band = (20, 20e3) if sub in AUDIO or cls in AUDIO else (10, 100e3)
    ctl = [".control", "set noinit", "set wr_singlescale", "set wr_vecnames", "option numdgt=8",
           "set numdgt=15", "op", "wrdata @D@.op.dat all", "set numdgt=8"]  # full precision (Addendum B2.5)
    files = ["op"]
    ac_paths = ["buf", "rem"] if cls == "B" else [main]
    for k, role in enumerate(ac_paths):
        for other in ac_paths:
            ctl.append(f"alter @vac_{other}[acmag]={1 if other == role else 0}")
        ctl += [ac, f"wrdata @D@.ac{k}.dat " + " ".join(meas)]
        files.append(f"ac{k}")
    for other in ac_paths:
        ctl.append(f"alter @vac_{other}[acmag]=0")
    for k, node in enumerate(meas):
        # ngspice numbers noise plots after the preceding plots (noise2/noise3 after two ac runs), so the
        # spectrum is addressed as the plot made just before the integrated-noise plot that `noise` leaves current
        ctl += [f"noise {node} vac_{main} dec 20 {band[0]:g} {band[1]:g}", "setplot previous",
                f"wrdata @D@.noise{k}.dat onoise_spectrum"]
        files.append(f"noise{k}")
    for tr in P["tran"]:
        ctl += [f"tran {tr['tmax']:.6g} {tr['tstop']:.9g} 0 {tr['tmax']:.6g}",
                f"wrdata @D@.{tr['name']}.dat " + " ".join(meas)]
        files.append(tr["name"])
    if cls == "C":
        ti = P["tran_inj"]
        ctl += ["alter @rinj[resistance]=1k", f"tran {ti['tmax']:.6g} {ti['tstop']:.9g} 0 {ti['tmax']:.6g}",
                "wrdata @D@.tinj.dat v(out)"]
        files.append("tinj")
    ctl += ["quit", ".endc", ".end", ""]
    text = "\n".join(lines + src_lines + ctl)
    return text, files, P


WAVEFOLDER_OFFSET_V = json.loads((ROOT / "design/reports/spice/wavefolder.json").read_text())["model_offset_calibration_V"]


def loop_lines(circuit, corner, lines):
    """Loop deck elements: all sources at their DC value with no AC; the break is at the IN- pin."""
    src = []
    for role, s in circuit["sources"].items():
        if role == "harness":
            continue
        if role == "iabc":
            src.append(f"Iabc 0 {s['node']} DC {fmt(IABC_A[corner['iabc']])}")
            continue
        dc = WAVEFOLDER_OFFSET_V if role == "trim" else s["dc"]
        src.append(f"Vdc_{role} {s['node']} 0 DC {fmt(dc)}")
    if circuit["class"] == "C":
        src.append("Rinj inp 0 1e12")
    return lines + src
