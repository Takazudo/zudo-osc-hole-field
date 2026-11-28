"""MC04-S13 tests and mutations M1 to M21 (offline; M3 and M12 read recorded runs; the others use in-memory copies or deck text)."""
import copy
import json
import sys
import unittest
from pathlib import Path

STUDY = Path(__file__).resolve().parent
sys.path[:0] = [str(STUDY), str(STUDY.parents[3])]

import budget  # noqa: E402
import p4b  # noqa: E402
import cells  # noqa: E402
import runner  # noqa: E402


def good_closed(cls):
    m = {"ac": {"main@out": {"peaking_dB": 0.5, "gain_20k_dB": 0.0, "phase_20k_deg": -1.0}},
         "k4": {"main@out": [{"overshoot_percent": 5.0}]}, "k5": {"step@out": 1e-5},
         "noise": {"out": {"integrated_uVrms": 10.0}}, "k6": [1e-4, 1e-4], "k8_tau_s": 1e-5}
    return m


def good_loop(pm=60.0):
    return {"phase_margin_deg": pm, "gain_margin_dB": 20.0, "crossover_Hz": 1e6}


def synth(cls, values, fail_at=(), fail_crit="K1"):
    t = {"key": "T", "circuit": {"subclass": cls, "class": cls[0]}, "swept": ["inm"]}
    pts, res = [], {}
    for v in values:
        p = {"topology": "T", "class": cls, "corner": {}, "swept": "inm", "other": None, "c_pF": v,
             "whatif": False, "phase": "sweep", "out_pF": 20.0}
        pts.append(p)
        pid = budget.point_id(p)
        lo, cl = good_loop(), good_closed(cls)
        if v in fail_at:
            if fail_crit == "K1":
                lo["phase_margin_deg"] = 40.0
            elif fail_crit == "K4":
                cl["k4"]["main@out"][0]["overshoot_percent"] = 30.0
        res[(pid, "loop")] = {"status": "OK", "metrics": lo, "point": p}
        res[(pid, "closed")] = {"status": "OK", "metrics": cl, "point": p}
    return t, pts, res


class Census(unittest.TestCase):
    def test_p6(self):
        cen = cells.census()
        self.assertEqual(cells.check_census(cen), [])

    def test_m6_footprint_removed(self):
        cen = cells.census()
        cen = copy.deepcopy(cen)
        cen["footprints"].remove("C8313")
        cen["footprint_count"] -= 1
        self.assertTrue(cells.check_census(cen))


class Decks(unittest.TestCase):
    def setUp(self):
        self.cen, self.topo, self.rows = budget.topologies()

    def test_no_diode_or_transistor_model_line(self):
        for t in self.topo.values():
            p = budget.sweep_points(t)[0]
            for _, text, *_ in budget.loop_texts(t, p) + budget.closed_texts(t, p):
                for line in text.splitlines():
                    self.assertFalse(line.lower().startswith(".model"), line)

    def test_m2_stray_dropped_changes_key(self):
        t = self.topo[self.rows["/M4B/C24ce01_SUM"]["topology"]]
        p = budget.sweep_points(t, values=[10])[0]
        text = budget.loop_texts(t, p)[0][1]
        dropped = "\n".join(x for x in text.splitlines() if not x.startswith("Cstray")) + "\n"
        self.assertNotEqual(runner.deck_key(text), runner.deck_key(dropped))
        self.assertNotIn(runner.deck_key(dropped), [runner.deck_key(x[1]) for x in budget.loop_texts(t, p)])

    def test_blocked_classes(self):
        for net, row in self.rows.items():
            if row["info"]["class"] in ("F", "I"):
                self.assertTrue(row.get("blocked"), net)

    def test_identical_cells_share_a_deck(self):
        a = self.rows["/M4A/C24ce01_W_SENSE"]["topology"]
        b = self.rows["/M4B/C24ce01_W_SENSE"]["topology"]
        self.assertEqual(a, b)


class Limits(unittest.TestCase):
    def test_all_pass_caps_at_50(self):
        t, pts, res = synth("E-audio", budget.VALUES_PF)
        lim = list(budget.corner_limits(pts, res).values())[0]
        self.assertEqual(lim["c_lim_pF"], 50.0)

    def test_m4_forced_fail_lowers_limit(self):
        t, pts, res = synth("E-audio", budget.VALUES_PF, fail_at=(24,), fail_crit="K4")
        lim = list(budget.corner_limits(pts, res).values())[0]
        self.assertEqual(lim["c_lim_pF"], 10.0)  # 2 x 12 = 24 fails, so 12 is not a limit; 10 is

    def test_m7_non_monotonic(self):
        t, pts, res = synth("E-audio", budget.VALUES_PF, fail_at=(8,))
        lim = list(budget.corner_limits(pts, res).values())[0]
        self.assertTrue(lim["non_monotonic"])
        self.assertEqual(lim["lowest_fail_pF"], 8)
        self.assertEqual(lim["c_lim_pF"], 3.0)

    def test_fail_at_zero(self):
        t, pts, res = synth("E-audio", budget.VALUES_PF, fail_at=(0,))
        lim = list(budget.corner_limits(pts, res).values())[0]
        self.assertEqual(lim["status"], "FAILS AT ZERO STRAY")


class Table(unittest.TestCase):
    def row(self, **kw):
        r = {"net": "/X/N", "class": "A", "label": "BUDGET 10 pF (MODEL EVIDENCE ONLY)", "c_lim_pF": 10.0,
             "parts_on_net": [{"ref": "R1", "inventory_line": "line-x"}]}
        r.update(kw)
        return {"rows": [r], "what_if": [], "f_diagnostic": []}

    def test_ok(self):
        budget.validate_budget(self.row())

    def test_m5_blocked_with_number(self):
        with self.assertRaises(ValueError):
            budget.validate_budget(self.row(**{"class": "F"}))
        with self.assertRaises(ValueError):
            budget.validate_budget(self.row(**{"class": "I", "label": "BLOCKED: MISSING VENDOR MODEL BCM847BS,115"}))

    def test_m8_identity_open_plain_budget(self):
        with self.assertRaises(ValueError):
            budget.validate_budget(self.row(parts_on_net=[{"ref": "R1", "inventory_line": "IDENTITY OPEN"}]))
        with self.assertRaises(ValueError):
            budget.validate_budget(self.row(k9_not_run=True))

    def test_whatif_label(self):
        b = self.row()
        b["what_if"] = [{"label": "BUDGET"}]
        with self.assertRaises(ValueError):
            budget.validate_budget(b)


class Models(unittest.TestCase):
    def test_m1_changed_byte_fails_closed(self):
        src = cells.ROOT / ".circuit-cache/sources/opa196-model/OPAx196.LIB"
        if not src.exists():
            self.skipTest("model cache absent")
        work = runner.WORK
        work.mkdir(parents=True, exist_ok=True)
        bad = work / "m1-mutated.lib"
        data = bytearray(src.read_bytes())
        data[100] ^= 1
        bad.write_bytes(bytes(data))
        try:
            with self.assertRaises(SystemExit):
                budget.check_pins({bad.relative_to(cells.ROOT).as_posix(): budget.MODEL_PINS[
                    ".circuit-cache/sources/opa196-model/OPAx196.LIB"]})
        finally:
            bad.unlink()

    def test_m3_recorded(self):
        path = STUDY / "checkpoints/controls.json"
        if not path.exists():
            self.skipTest("controls not run yet")
        c = json.loads(path.read_text())
        self.assertTrue(c["M3"] and all(x["fails_P5"] for x in c["M3"]))


class P4bComparison(unittest.TestCase):
    """Addendum A: M9 to M11 on in-memory copies of the retained receipt; no deck runs."""

    @classmethod
    def setUpClass(cls):
        cls.receipt = json.loads((cells.ROOT / p4b.RECEIPT).read_text())

    def copy(self):
        return copy.deepcopy(self.receipt)

    def test_identity_passes_and_exclusion_is_rows_62_to_77(self):
        self.assertEqual(p4b.carriers(self.receipt), list(range(62, 78)))
        self.assertEqual(p4b.compare(self.copy(), self.receipt), [])

    def test_m9_vendor_metric_changed_fails(self):
        for i, key in ((62, "phase_margin_deg"), (70, "crossover_Hz"), (5, None)):
            c = self.copy()
            if key is None:
                c["results"][i]["deck_sha256"] = "0" * 64
            else:
                c["results"][i]["metrics"][key] = c["results"][i]["metrics"][key] + 1e-4
            self.assertTrue(p4b.compare(c, self.receipt), (i, key))
        c = self.copy()
        c["loop_break_validation"][0]["middlebrook"]["phase_margin_deg"] += 1e-3
        self.assertTrue(p4b.compare(c, self.receipt))

    def test_m10_paper_screen_changed_does_not_fail_but_other_key_does(self):
        c = self.copy()
        c["results"][62]["metrics"]["paper_screen"] = dict(p4b.STUB)
        c["results"][77]["metrics"]["paper_screen"] = {}
        self.assertEqual(p4b.compare(c, self.receipt), [])
        c = self.copy()
        m = c["results"][62]["metrics"]
        other = next(k for k in m if k != "paper_screen")
        m[other] = {"changed": True}
        self.assertTrue(p4b.compare(c, self.receipt))
        c = self.copy()
        del c["results"][62]["metrics"][other]
        self.assertTrue(p4b.compare(c, self.receipt))

    def test_m11_exclusion_set_is_exactly_16_rows(self):
        c = self.copy()
        c["results"][61]["metrics"]["paper_screen"] = dict(p4b.STUB)
        self.assertTrue(p4b.compare(c, self.receipt))
        c = self.copy()
        del c["results"][70]["metrics"]["paper_screen"]
        self.assertTrue(p4b.compare(c, self.receipt))
        self.assertTrue(p4b.compare(self.receipt, c))

    def test_batches_cover_136_cases_with_a_last_batch_of_one(self):
        b = p4b.batches()
        self.assertEqual(len(b), 28)
        self.assertEqual(b[-1], (135, 135))
        flat = [i for first, last in b for i in range(first, last + 1)]
        self.assertEqual(flat, list(range(136)))


class SeedAndP7(unittest.TestCase):
    """Addendum B: M12 reads the recorded deck run; M13 to M16 use in-memory copies."""

    @classmethod
    def setUpClass(cls):
        cls.cen, cls.topo, cls.rows = budget.topologies()
        cls.ref9 = cls.topo[cls.rows["/E2/REF9_FB"]["topology"]]
        cls.good = {"inp": 5.0, "inm": 5.000021, "xinm": 5.000021, "n1": 5.000021, "out": 9.00004,
                    "vp": 12.0, "vn": -12.0, "top_threshold": 0.0}
        path = STUDY / "checkpoints/controls.json"
        cls.controls = json.loads(path.read_text()) if path.exists() else None

    def test_ref9_expected_dc_is_9_and_5(self):
        exp, _ = budget.expected_dc(self.ref9, budget.sweep_points(self.ref9)[0])
        self.assertAlmostEqual(exp["out"], 9.0, places=5)
        self.assertAlmostEqual(exp["inm"], 5.0, places=6)

    def test_grounded_in_plus_is_not_floating(self):
        t = self.topo[self.rows["/W1/DRIVE_INV_SUM"]["topology"]]
        text = budget.loop_texts(t, budget.sweep_points(t)[0])[0][1]
        self.assertIn("XU 0 xinm vp vn out", text)

    def test_seed_deck_differs_only_in_c_stray(self):
        t = self.ref9
        p = budget.sweep_points(t, values=[10])[0]
        seed = budget.seed_netlist(t, p, "loop").splitlines()
        ev = budget.loop_texts(t, p)[2][1].split("\n.control\n")[0].splitlines()
        diff = [(a, b) for a, b in zip(seed, ev) if a != b]
        self.assertEqual(len(seed), len(ev))
        self.assertEqual(len(diff), 1)
        self.assertTrue(diff[0][0].startswith("Cstray") and diff[0][1].startswith("Cstray"))

    def test_nodeset_changes_the_deck_key(self):
        p = budget.sweep_points(self.ref9, values=[10])[0]
        a = budget.loop_texts(self.ref9, p)[0][1]
        b = budget.loop_texts(self.ref9, p, [".nodeset v(out) = 9.00004"])[0][1]
        self.assertNotEqual(runner.deck_key(a), runner.deck_key(b))

    def test_m12_recorded(self):
        path = STUDY / "checkpoints/m12.json"
        if not path.exists():
            self.skipTest("M12 not run yet")
        m = json.loads(path.read_text())
        self.assertEqual(m["status"], "NOT EVALUATED")
        self.assertIsNone(m["metrics"])
        self.assertTrue(all(a["result"] != "accepted" for a in m["attempts"]))

    def test_m13_one_millivolt_fails_50_uV(self):
        ref = dict(self.good)
        if self.controls:
            s = next((x for x in self.controls.get("seeds", []) if x.get("valid")), None)
            if s:
                ref = dict(s["reference"])
        self.assertIsNone(budget.accept_op(ref, ref))
        node = sorted(ref)[0]
        bad = dict(ref)
        bad[node] += 1e-3
        self.assertTrue(budget.accept_op(ref, bad))

    def test_m14_p7_not_evaluated_fails(self):
        rec = {"loop": {"status": "NOT EVALUATED", "pm_deg": None}, "pass": True}
        self.assertFalse(budget.p7_pass(rec, need_k4=False))
        if self.controls and self.controls.get("P7"):
            c = copy.deepcopy(self.controls["P7"]["/E2/REF9_FB"])
            c["loop"]["status"] = "NOT EVALUATED"
            c.pop("K1_fails", None)
            self.assertFalse(budget.p7_pass(c, need_k4=False))

    def test_m15_invalid_seeds(self):
        c = self.ref9["circuit"]
        exp, _ = budget.expected_dc(self.ref9, budget.sweep_points(self.ref9)[0])
        self.assertEqual(budget.seed_validity(c, "loop", self.good, exp), [])
        railed = {**self.good, "out": 11.97}
        self.assertTrue(budget.seed_validity(c, "loop", railed, exp))
        apart = {**self.good, "xinm": 5.002, "inm": 5.002}
        self.assertTrue(budget.seed_validity(c, "loop", apart, exp))

    def test_m16_k4_removed_fails_p7(self):
        rec = {"loop": {"status": "OK"}, "K1_fails": True, "closed": {"status": "OK"}, "K4_fails": True}
        self.assertTrue(budget.p7_pass(rec, need_k4=True))
        drop = copy.deepcopy(rec)
        del drop["K4_fails"]
        self.assertFalse(budget.p7_pass(drop, need_k4=True))
        if self.controls and self.controls.get("P7"):
            c = copy.deepcopy(self.controls["P7"]["/W1/DRIVE_INV_SUM"])
            c.pop("K4_fails", None)
            self.assertFalse(budget.p7_pass(c, need_k4=True))


class AddendumC(unittest.TestCase):
    """Addendum C: M17 to M21."""

    @classmethod
    def setUpClass(cls):
        cls.cen, cls.topo, cls.rows = budget.topologies()
        cls.ref9 = cls.topo[cls.rows["/E2/REF9_FB"]["topology"]]
        cls.good = {"inp": 5.0, "inm": 5.000021, "xinm": 5.000021, "n1": 5.000021, "out": 9.00004,
                    "vp": 12.0, "vn": -12.0, "top_threshold": 0.0}

    def test_m17_fallback_reference_rejected(self):
        c = self.ref9["circuit"]
        exp, _ = budget.expected_dc(self.ref9, budget.sweep_points(self.ref9)[0])
        self.assertEqual(budget.seed_validity(c, "loop", self.good, exp, transient_op=False), [])
        self.assertTrue(budget.seed_validity(c, "loop", self.good, exp, transient_op=True))

    def test_m18_group_disagreement(self):
        a = dict(self.good)
        b = {**a, "out": a["out"] + 124e-6}
        self.assertTrue(budget.group_disagreement([a, b]))
        self.assertIsNone(budget.group_disagreement([a, {**a, "out": a["out"] + 4e-6}]))

    def test_group_key_joins_capacitor_corners_and_both_kinds(self):
        pts = budget.sweep_points(self.ref9, values=[0])
        keys = {json.dumps(p["corner"], sort_keys=True): budget.group_key(self.ref9, p) for p in pts}
        self.assertEqual(keys['{"bracket": "agnd", "tmux_c": 0.0}'], keys['{"bracket": "agnd", "tmux_c": 1e-10}'])
        self.assertNotEqual(keys['{"bracket": "agnd", "tmux_c": 0.0}'], keys['{"bracket": "open", "tmux_c": 0.0}'])

    def all_deck_texts(self):
        for t in self.topo.values():
            p = budget.sweep_points(t)[0]
            for kind in ("loop", "closed"):
                yield "seed " + kind, t, runner.seed_text(budget.seed_netlist(t, p, kind))
            for name, text, *_ in budget.loop_texts(t, p, [".nodeset v(out) = 0"]):
                yield "loop", t, text
            for name, text, *_ in budget.closed_texts(t, p, [".nodeset v(out) = 0"]):
                yield "closed", t, text

    def test_m19_no_lone_input_pin_in_any_complete_deck(self):
        n = 0
        for kind, t, text in self.all_deck_texts():
            self.assertEqual(runner.floating_inputs(text), [], (kind, t["key"]))
            n += 1
        self.assertGreater(n, 80)

    def test_noise_spectrum_plot_selected_relative_to_noise_in_every_closed_deck(self):
        """The spectrum written after each `noise` is the plot made just before the one `noise` leaves current;
        no closed deck names a numbered noise plot (ngspice numbered it noise2 after two ac runs in run 4)."""
        n = 0
        for kind, t, text in self.all_deck_texts():
            if kind != "closed":
                continue
            ctl = text.split("\n.control\n", 1)[1].splitlines()
            self.assertFalse([ln for ln in ctl if ln.startswith("setplot noise")], t["key"])
            for i, ln in enumerate(ctl):
                if ln.startswith("noise "):
                    self.assertEqual(ctl[i + 1], "setplot previous", t["key"])
                    self.assertTrue(ctl[i + 2].startswith("wrdata ") and ctl[i + 2].endswith(" onoise_spectrum"))
                    n += 1
        self.assertGreater(n, 20)

    def test_slice_deadline_refuses_a_deck_whose_timeout_does_not_fit(self):
        import time as _t
        saved = runner.DEADLINE["t"]
        try:
            runner.DEADLINE["t"] = _t.time() + runner.TIMEOUT_S  # less than one timeout plus margin left
            n = runner.INVOCATIONS["count"]
            with self.assertRaises(runner.SliceDeadline):
                runner.run("title\nR1 a 0 1k\nR2 a 0 1k\n.end\n", ["op1"])
            self.assertEqual(runner.INVOCATIONS["count"], n)  # nothing started, nothing counted
            self.assertFalse(issubclass(runner.SliceDeadline, (RuntimeError, runner.OracleError)))
        finally:
            runner.DEADLINE["t"] = saved

    def test_discarded_work_counts_against_the_caps(self):
        d = budget.discarded()
        self.assertGreaterEqual(d["invocations"], 319 + 6)
        self.assertGreaterEqual(d["seed_invocations"], 14 + 4 + 22)

    def test_sweep_order_puts_class_c_full_list_before_g_and_whatifs_last(self):
        tc = next(t for t in self.topo.values() if t["circuit"]["class"] == "C")
        tg = next(t for t in self.topo.values() if t["circuit"]["class"] == "G")
        tb = next(t for t in self.topo.values() if t["circuit"]["class"] == "B")
        got = budget.sweep_order([("sweep", tg, []), ("whatif", tb, []), ("sweep", tc, []), ("sweep", tb, [])])
        self.assertEqual([(ph, t["circuit"]["class"]) for ph, t, _ in got],
                         [("sweep", "B"), ("sweep", "C"), ("sweep", "G"), ("whatif", "B")])

    def drop(self, text, pred):
        return "\n".join(ln for ln in text.splitlines() if not pred(ln)) + "\n"

    def test_m19_mutations_rejected(self):
        p = budget.sweep_points(self.ref9)[0]
        loop = budget.loop_texts(self.ref9, p)[0][1]
        no_inp = self.drop(loop, lambda ln: ln.startswith("Vdc_ref5"))  # IN+ left alone
        self.assertTrue(runner.floating_inputs(no_inp))
        no_inm = self.drop(loop, lambda ln: ln.startswith("Vinj"))  # the inverting pin (xinm) left alone
        self.assertTrue(runner.floating_inputs(no_inm))
        closed = budget.closed_texts(self.ref9, p)[0][1]
        no_inm_c = self.drop(closed, lambda ln: ln.split()[:1] and ln.split()[0][0] in "RC" and " inm " in f" {ln} ")
        self.assertTrue(runner.floating_inputs(no_inm_c))
        with_ns = no_inp.replace("\n.control\n", "\n.nodeset v(inp) = 5\n.control\n", 1)
        self.assertTrue(runner.floating_inputs(with_ns))  # a .nodeset line is not a connection
        g = next(t for t in self.topo.values() if t["circuit"]["class"] == "G")
        gp = budget.sweep_points(g)[0]
        gt = budget.loop_texts(g, gp)[0][1]
        ota = next(ln for ln in gt.splitlines() if ln.startswith("XOTA")).split()
        for pin in (3, 4):
            node = ota[pin]
            mut = self.drop(gt, lambda ln, node=node: not ln.startswith("XOTA") and node in ln.split()[1:3]
                            and not ln.startswith("."))
            self.assertTrue(runner.floating_inputs(mut), pin)
        with self.assertRaises(RuntimeError):
            runner.run(no_inp, ["op1"])

    def test_m20_fallback_evaluation_deck_yields_no_metric(self):
        ref = dict(self.good)
        inside = {k: v + 1e-6 for k, v in ref.items()}
        self.assertIsNone(budget.eval_reason([inside, inside], ref, False))
        self.assertTrue(budget.eval_reason([inside, inside], ref, True))
        self.assertTrue(budget.eval_reason([inside], ref, True))

    def test_m21_seed_invocation_cap_stops(self):
        saved = dict(runner.SEED_INVOCATIONS)
        try:
            runner.SEED_INVOCATIONS["count"] = 540
            with self.assertRaises(SystemExit) as cm:
                runner.run_seed("title\nR1 a 0 1k\n")
            self.assertIn("STOP 3", str(cm.exception))
            self.assertEqual(runner.SEED_INVOCATIONS["count"], 540)
        finally:
            runner.SEED_INVOCATIONS.update(saved)


if __name__ == "__main__":
    unittest.main()
