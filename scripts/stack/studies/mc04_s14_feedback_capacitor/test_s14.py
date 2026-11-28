"""MC04-S14 tests: the S13 mutations M1 to M8 and M12 (in-memory form) to M21 carried over on the S14 copies, and
the S14 mutations N1 to N16. Offline: no deck runs (N9 reads the S13 cache through the pinned S13 modules)."""
import copy
import gzip
import json
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

STUDY = Path(__file__).resolve().parent
sys.path[:0] = [str(STUDY), str(STUDY.parents[3])]

import budget  # noqa: E402
import cells  # noqa: E402
import runner  # noqa: E402
import s14  # noqa: E402


def loop_m(pm=60.0):
    return {"phase_margin_deg": pm, "gain_margin_dB": 20.0, "crossover_Hz": 1e6}


def closed_m(peak=0.5, ov=5.0, k5=1e-5, noise=10.0, k6=(1e-4, 1e-4), tau=1e-5, swing=(-10.0, 10.0)):
    return {"ac": {"main@out": {"peaking_dB": peak, "gain_20k_dB": 0.0, "phase_20k_deg": -1.0}},
            "k4": {"main@out": [{"overshoot_percent": ov, "status": "OK"}]}, "k5": {"step@out": k5},
            "noise": {"out": {"integrated_uVrms": noise}}, "k6": list(k6), "k8_tau_s": tau,
            "resolution_fraction": 5e-4, "k6_resolution_s": 5e-9, "swing_out_V": list(swing),
            "clipped": runner.clipped(*swing), "stimulus": {"tran": [{"tmax": 5e-9}]}}


def table(values, change=None):
    out = {}
    for v in values:
        lo, cl = loop_m(), closed_m()
        if change:
            change(v, lo, cl)
        out[v] = {"loop": lo, "closed": cl, "second": None}
    return out


class Census(unittest.TestCase):
    def test_p6(self):
        self.assertEqual(cells.check_census(cells.census()), [])

    def test_m6_footprint_removed(self):
        cen = copy.deepcopy(cells.census())
        cen["footprints"].remove("C8313")
        cen["footprint_count"] -= 1
        self.assertTrue(cells.check_census(cen))

    def test_p6_scope_counts(self):
        self.assertTrue(s14.p6()["pass"])


class Decks(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cen, cls.topo, cls.rows = budget.topologies()
        cls.ref9 = cls.topo[cls.rows["/E2/REF9_FB"]["topology"]]
        cls.sets = s14.arm_w_sets()

    def test_m2_stray_dropped_changes_key(self):
        t = self.topo[self.rows["/W1/CONTROL_SUM"]["topology"]]
        p = s14.point(t, {}, 12, whatif=True, phase="whatif")
        text = budget.loop_texts(t, p)[0][1]
        dropped = "\n".join(x for x in text.splitlines() if not x.startswith("Cstray")) + "\n"
        self.assertNotEqual(runner.deck_key(text), runner.deck_key(dropped))

    def test_whatif_deck_is_pinned_build_plus_one_line(self):
        s = self.sets[0]
        p = s14.point(s["t"], s["corner"], 12, whatif=True, phase="whatif")
        for deck in ("loop", "closed"):
            texts = budget.loop_texts(s["t"], p, [".nodeset v(out) = 0"]) if deck == "loop" else \
                budget.closed_texts(s["t"], p, [".nodeset v(out) = 0"])
            for it in texts:
                self.assertIsNone(s14.identity(p, deck, [".nodeset v(out) = 0"], it[0], it[1]), (deck, it[0]))

    def test_n1_capacitor_to_agnd_or_other_value_fails_p10(self):
        s = self.sets[5]
        p = s14.point(s["t"], s["corner"], 0, whatif=True, phase="whatif")
        text = budget.closed_texts(s["t"], p)[0][1]
        for bad in ("Cwhatif inm 0 10p", "Cwhatif out inm 12p", "Cwhatif out 0 10p", "Rwhatif out inm 10p"):
            self.assertTrue(s14.identity(p, "closed", [], "ngspice default (trap)", text.replace(s14.WHATIF_LINE, bad)), bad)
        self.assertIsNone(s14.identity(p, "closed", [], "ngspice default (trap)", text))
        two = text.replace(s14.WHATIF_LINE, s14.WHATIF_LINE + "\nCextra out 0 1p")
        self.assertTrue(s14.identity(p, "closed", [], "ngspice default (trap)", two))

    def test_rescaled_deck_differs_only_in_the_k5_stimuli(self):
        s = self.sets[5]
        p = s14.point(s["t"], s["corner"], 0, whatif=True, phase="whatif")
        name, text, files, P = budget.closed_texts(s["t"], p, k5_scale=0.512)[0]
        t0 = P["windows"]["K5_step"][0][0]
        self.assertIsNone(s14.identity(p, "closed", [], name, text, scale=0.512, k5_t0=t0))
        self.assertTrue(s14.identity(p, "closed", [], name, text, scale=0.6, k5_t0=t0))  # N16: not the recorded scale
        k4 = text.replace("Vpwl_sig sig_a sig_b PWL(0 0 2e-05 0 2.01e-05 0.1", "Vpwl_sig sig_a sig_b PWL(0 0 2e-05 0 2.01e-05 0.0512")
        if k4 != text:
            self.assertTrue(s14.identity(p, "closed", [], name, k4, scale=0.512, k5_t0=t0))

    def test_g_trim_one_is_the_larger_feedback(self):
        r = s14.g_trim_check(s14.topology("2f451c39"))
        self.assertEqual((r["trim0_ohm"], r["trim1_ohm"]), (49900.0, 59900.0))

    def test_m19_no_lone_input_pin_in_any_whatif_deck(self):
        n = 0
        for s in self.sets:
            p = s14.point(s["t"], s["corner"], 0, whatif=True, phase="whatif")
            for _, text, *_ in budget.loop_texts(s["t"], p, [".nodeset v(out) = 0"]) + \
                    budget.closed_texts(s["t"], p, [".nodeset v(out) = 0"]):
                self.assertEqual(runner.floating_inputs(text), [])
                n += 1
        self.assertEqual(n, 55)

    def test_m19_mutations_rejected(self):
        p = budget.sweep_points(self.ref9)[0]
        loop = budget.loop_texts(self.ref9, p)[0][1]
        no_inp = "\n".join(ln for ln in loop.splitlines() if not ln.startswith("Vdc_ref5")) + "\n"
        self.assertTrue(runner.floating_inputs(no_inp))
        with self.assertRaises(RuntimeError):
            runner.run(no_inp, ["op1"])

    def test_noise_spectrum_plot_selected_relative_to_noise(self):
        s = self.sets[5]
        p = s14.point(s["t"], s["corner"], 0, whatif=True, phase="whatif")
        ctl = budget.closed_texts(s["t"], p)[0][1].split("\n.control\n", 1)[1].splitlines()
        i = next(k for k, ln in enumerate(ctl) if ln.startswith("noise "))
        self.assertEqual(ctl[i + 1], "setplot previous")


class Seeds(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cen, cls.topo, cls.rows = budget.topologies()
        cls.ref9 = cls.topo[cls.rows["/E2/REF9_FB"]["topology"]]
        cls.g = s14.topology("2f451c39")
        cls.good = {"inp": 5.0, "inm": 5.000021, "xinm": 5.000021, "n1": 5.000021, "out": 9.00004,
                    "vp": 12.0, "vn": -12.0, "top_threshold": 0.0}

    def test_m12_in_memory_unseeded_operating_point_rejected(self):
        moved = {**self.good, "out": self.good["out"] + 0.3, "inm": self.good["inm"] + 0.1}
        self.assertTrue(budget.eval_reason([moved, moved], self.good, False))

    def test_m13_one_millivolt_fails_50_uV(self):
        self.assertIsNone(budget.accept_op(self.good, self.good))
        self.assertTrue(budget.accept_op({**self.good, "out": self.good["out"] + 1e-3}, self.good))

    def test_m14_m16_p7_not_evaluated_or_k4_missing_fails(self):
        self.assertFalse(budget.p7_pass({"loop": {"status": "NOT EVALUATED"}}, need_k4=False))
        rec = {"loop": {"status": "OK"}, "K1_fails": True, "closed": {"status": "OK"}, "K4_fails": True}
        self.assertTrue(budget.p7_pass(rec, need_k4=True))
        del rec["K4_fails"]
        self.assertFalse(budget.p7_pass(rec, need_k4=True))

    def test_m15_m17_invalid_seeds(self):
        c = self.ref9["circuit"]
        exp, _ = budget.expected_dc(self.ref9, budget.sweep_points(self.ref9)[0])
        self.assertEqual(budget.seed_validity(c, "loop", self.good, exp), [])
        self.assertTrue(budget.seed_validity(c, "loop", {**self.good, "out": 11.97}, exp))
        self.assertTrue(budget.seed_validity(c, "loop", {**self.good, "xinm": 5.002, "inm": 5.002}, exp))
        self.assertTrue(budget.seed_validity(c, "loop", self.good, exp, transient_op=True))

    def test_s6_4_class_g_inputs_are_tested(self):
        c = self.g["circuit"]
        ok = {"xinm": 2e-5, "inm": 2e-5, "out": 0.1, "ota_nc2": 3.0}
        self.assertEqual(budget.seed_validity(c, "loop", ok, {}), [])
        self.assertTrue(budget.seed_validity(c, "loop", {**ok, "xinm": 2e-3}, {}))

    def test_m18_group_disagreement(self):
        a = dict(self.good)
        self.assertTrue(budget.group_disagreement([a, {**a, "out": a["out"] + 124e-6}]))
        self.assertIsNone(budget.group_disagreement([a, {**a, "out": a["out"] + 4e-6}]))

    def test_m20_fallback_evaluation_deck_yields_no_metric(self):
        inside = {k: v + 1e-6 for k, v in self.good.items()}
        self.assertIsNone(budget.eval_reason([inside, inside], self.good, False))
        self.assertTrue(budget.eval_reason([inside], self.good, True))

    def test_m21_seed_invocation_cap_stops_at_180(self):
        saved = dict(runner.SEED_INVOCATIONS)
        try:
            self.assertEqual(runner.SEED_INVOCATIONS["cap"], 180)
            runner.SEED_INVOCATIONS["count"] = 180
            with self.assertRaises(SystemExit) as cm:
                runner.run_seed("title\nR1 a 0 1k\n")
            self.assertIn("STOP 3", str(cm.exception))
        finally:
            runner.SEED_INVOCATIONS.update(saved)

    def test_n8_no_connect_exclusion_by_rule(self):
        p = s14.point(self.g, {"trim": 1.0, "iabc": "low"}, 0, whatif=True, phase="whatif")
        text = budget.loop_texts(self.g, p, (), s14.G_LADDER)[0][1]
        excl = s14.nc_nodes(self.g["circuit"], text)
        self.assertEqual(excl, ["ota_nc2", "ota_nc8"])
        ref = {"xinm": 2e-5, "inm": 2e-5, "n1": 2e-5, "out": 0.1, "ota_nc2": 3.0, "ota_nc8": 1.0}
        self.assertIsNone(budget.eval_reason([{**ref, "ota_nc8": 1.002}] * 2, ref, False, excl))
        self.assertTrue(budget.eval_reason([{**ref, "inm": ref["inm"] + 2e-3}] * 2, ref, False, excl))
        spec = copy.deepcopy(self.g["circuit"])
        for e in spec["elements"]:
            if e["t"] == "ota":
                e["pins_n"]["8"] = "ota_nc8"  # the specification now connects pin 8
        self.assertEqual(s14.nc_nodes(spec, text), ["ota_nc2"])


class Measurements(unittest.TestCase):
    def wave(self, f, t0=0.0, t1=40e-6, n=4001):
        ts = [t0 + (t1 - t0) * k / (n - 1) for k in range(n)]
        return runner.Wave(ts, [f(x) for x in ts])

    def test_n4_unsettled_window_has_no_percentage(self):
        import math
        w = self.wave(lambda x: 0.0 if x < 10e-6 else 0.1 + (0.0395 * math.sin(2 * math.pi * 2e6 * x)))
        o = runner.overshoot(w, 10e-6, 40e-6)
        self.assertEqual(o["status"], runner.UNSETTLED)
        self.assertIsNone(o["overshoot_percent"])
        w2 = self.wave(lambda x: 0.0 if x < 10e-6 else 0.1)
        self.assertEqual(runner.overshoot(w2, 10e-6, 40e-6)["status"], "OK")

    def test_n5_class_c_window_at_7_tau_rejected(self):
        win = [(0.0, 14e-6, -1.0)]
        with self.assertRaises(ValueError):
            runner.check_late_windows(win, [(7e-6, 14e-6 - 1e-6)], 1e-6)
        runner.check_late_windows(win, runner.late_starts(win, 1e-6), 1e-6)
        self.assertAlmostEqual(runner.late_starts(win, 1e-6)[0][0], 12e-6)

    def test_k5_step_residual_is_mean_removed_peak_to_peak(self):
        w = self.wave(lambda x: 1.0 + 1e-3 * x / 40e-6)  # a ramp is not detrended any more
        r = runner.late_residual(w, [(0.0, 40e-6, 1.0)])
        self.assertAlmostEqual(r, 0.5e-3 * (1 - 1e-6 / 20e-6), places=6)

    def test_sine_fit_has_no_linear_term(self):
        import math
        w = self.wave(lambda x: 2.0 + math.sin(2 * math.pi * 20e3 * x), t1=200e-6)
        res, hi, lo = runner.sine_residual(w, 0.0, 200e-6, 20e3)
        self.assertLess(res, 1e-9)
        w2 = self.wave(lambda x: math.sin(2 * math.pi * 20e3 * x) + 1e-3 * x / 200e-6, t1=200e-6)
        self.assertGreater(runner.sine_residual(w2, 0.0, 200e-6, 20e3)[0], 1e-4)

    def test_n7_clipped_record_is_not_evaluated(self):
        self.assertTrue(runner.clipped(-11.5, 11.5))
        self.assertFalse(runner.clipped(-10.9, 10.9))
        cl = closed_m(swing=(-11.5, 11.5))
        k5, why = s14.k5_view(cl, None)
        self.assertIsNone(k5)
        self.assertTrue(why.startswith("NOT EVALUATED: output clipped"))
        k5, why = s14.k5_view(cl, {"status": "OK", "metrics": {"clipped": True, "k5": {"x": 1e-6}}})
        self.assertIsNone(k5)

    def test_k5_scale(self):
        self.assertEqual(runner.k5_scale(5.0, -1.0, 11.97), float(f"{0.9 * 6 / 6.97:.3g}"))


class Limits(unittest.TestCase):
    def test_all_pass_caps_at_50(self):
        lim = s14.corner_limit("E-audio", table(s14.VALUES_W), s14.CAND_W)
        self.assertEqual(lim["c_lim_pF"], 50.0)

    def test_m4_forced_fail_lowers_limit(self):
        def ch(v, lo, cl):
            if v == 24:
                cl["k4"]["main@out"][0]["overshoot_percent"] = 30.0
        lim = s14.corner_limit("E-audio", table(s14.VALUES_W, ch), s14.CAND_W)
        self.assertEqual(lim["c_lim_pF"], 8.0)  # 24 fails: 12 needs 24 and is out; 8 needs 16

    def test_m7_non_monotonic(self):
        def ch(v, lo, cl):
            if v == 8:
                lo["phase_margin_deg"] = 40.0
        lim = s14.corner_limit("E-audio", table(s14.VALUES_W, ch), s14.CAND_W)
        self.assertTrue(lim["non_monotonic"])
        self.assertIsNone(lim["c_lim_pF"])  # 4 needs 8; no candidate from 4 pF passes

    def test_fail_at_zero(self):
        def ch(v, lo, cl):
            if v == 0:
                lo["phase_margin_deg"] = 40.0
        self.assertEqual(s14.corner_limit("E-audio", table(s14.VALUES_W, ch), s14.CAND_W)["status"],
                         "FAILS AT ZERO STRAY")

    def test_n13_candidate_without_its_double_rejected(self):
        with self.assertRaises(ValueError):
            s14.corner_limit("E-audio", table(s14.VALUES_W), s14.CAND_W + [24])
        c05 = sorted(budget.C_REDUCED_PF + s14.C05_NEW)
        with self.assertRaises(ValueError):
            s14.corner_limit("C", table(c05), [16, 20, 25])  # 16 has its double (32) but is not declared
        s14.corner_limit("C", table(c05), s14.CAND_C05)

    def test_n14_only_unevaluated_at_zero_is_not_evaluated(self):
        def ch(v, lo, cl):
            if v == 0:
                cl["k4"]["main@out"][0] = {"overshoot_percent": None, "status": runner.UNSETTLED}
        lim = s14.corner_limit("E-audio", table(s14.VALUES_W, ch), s14.CAND_W)
        self.assertTrue(lim["status"].startswith("NOT EVALUATED"))
        self.assertNotEqual(lim["status"], "FAILS AT ZERO STRAY")

    def test_n15_baseline_above_the_ceiling_fails(self):
        for kw in ({"peak": 6.5}, {"ov": 55.0}):
            def ch(v, lo, cl, kw=kw):
                cl.update(closed_m(**kw))
            self.assertEqual(s14.corner_limit("E-audio", table(s14.VALUES_W, ch), s14.CAND_W)["status"],
                             "FAILS AT ZERO STRAY")

    def test_relative_form_and_its_margin(self):
        def ch(v, lo, cl):
            cl["k4"]["main@out"][0]["overshoot_percent"] = 30.0 + (6.0 if v >= 32 else 0.0)
        lim = s14.corner_limit("E-audio", table(s14.VALUES_W, ch), s14.CAND_W)
        self.assertEqual(lim["modes"]["K4"], "relative")
        self.assertEqual(lim["c_lim_pF"], 12.0)  # 32 exceeds the baseline by 6 points

    def test_n6_tie_is_a_fail(self):
        self.assertFalse(s14.passes(0.00001, 0.0005))
        self.assertTrue(s14.passes(0.001, 0.0005))

        def ch(v, lo, cl):
            if v > 0:
                cl["k8_tau_s"] = 1e-5 * (1 + 0.01 - 0.00001)
        lim = s14.corner_limit("C", table(sorted(budget.C_REDUCED_PF + s14.C05_NEW), ch), s14.CAND_C05)
        self.assertIsNone(lim["c_lim_pF"])
        self.assertIn("K8", lim["deciding"])

    def test_n16_clipped_value_needs_its_second_deck(self):
        def ch(v, lo, cl):
            if v == 16:
                cl.update(closed_m(swing=(-11.5, 11.5)))
        lim = s14.corner_limit("E-audio", table(s14.VALUES_W, ch), s14.CAND_W)
        self.assertEqual(lim["c_lim_pF"], 6.0)
        self.assertTrue(any(str(x).startswith("NOT EVALUATED: output clipped") for x in
                            lim["verdicts"][16]["failed"] + [lim["verdicts"][16]["criteria"]["K5"]]))


class Tables(unittest.TestCase):
    def row(self, **kw):
        r = {"id": "x", "whatif": False, "class": "A", "label": "BUDGET 10 pF (MODEL EVIDENCE ONLY)",
             "c_lim_pF": 10.0, "corners": [{"modes": {"K3": "absolute", "K4": "absolute"}, "tested": [0, 10, 20]}]}
        r.update(kw)
        return r

    def test_ok(self):
        s14.validate_rows([self.row()], whatif_table=False)

    def test_n2_relative_limit_as_plain_budget_rejected(self):
        bad = self.row(corners=[{"modes": {"K3": "absolute", "K4": "relative"}, "tested": [0, 10, 20]}])
        with self.assertRaises(ValueError):
            s14.validate_rows([bad], whatif_table=False)
        s14.validate_rows([{**bad, "label": "BUDGET 10 pF, BASELINE EXCEEDS K4 (RELATIVE FORM, MODEL EVIDENCE ONLY)"}],
                          whatif_table=False)

    def test_n3_whatif_row_without_prefix_rejected(self):
        with self.assertRaises(ValueError):
            s14.validate_rows([self.row(whatif=True)], whatif_table=True)
        s14.validate_rows([self.row(whatif=True, label=s14.WHATIF_PREFIX + "BUDGET 10 pF (MODEL EVIDENCE ONLY)")],
                          whatif_table=True)

    def test_n10_class_b_row_rejected(self):
        with self.assertRaises(ValueError):
            s14.validate_rows([self.row(**{"class": "B"})], whatif_table=False)

    def test_n16_clipped_record_with_k5_figure_rejected(self):
        c = {"modes": {}, "tested": [0, 10, 20], "values": {"10": {"clipped": True, "k5_figure_used": True}}}
        with self.assertRaises(ValueError):
            s14.validate_rows([self.row(corners=[c])], whatif_table=False)

    def test_m8_identity_open_never_plain_budget(self):
        self.assertTrue(s14.common_reasons({"subclass": "E-audio", "tmux": False}, ["/W1/FOLDER_SUM"]))
        lab, _, _ = s14.row_label({"c": {"status": "OK", "c_lim_pF": 50.0, "modes": {"K3": "absolute"}}}, 10.0,
                                  reasons=["IDENTITY OPEN: R5247"], whatif=False, arm_w=True)
        self.assertTrue(lab.startswith("PROVISIONAL"))

    def test_m5_blocked_class_with_number_rejected_by_the_s13_copy(self):
        r = {"net": "/X/N", "class": "F", "label": "BUDGET 10 pF (MODEL EVIDENCE ONLY)", "c_lim_pF": 10.0,
             "parts_on_net": []}
        with self.assertRaises(ValueError):
            budget.validate_budget({"rows": [r], "what_if": [], "f_diagnostic": []})

    def test_n11_ic_supported_through_a_conditional_row_rejected(self):
        for lab in ("NOT EVALUATED: x", "BLOCKED: MISSING VENDOR MODEL BAS16GW-QX",
                    s14.WHATIF_PREFIX + "BUDGET 10 pF (MODEL EVIDENCE ONLY)",
                    "BUDGET 10 pF, BASELINE EXCEEDS K4 (RELATIVE FORM, MODEL EVIDENCE ONLY)", "PROVISIONAL 10 pF: x"):
            t = {"U5110": {"supported": True, "rows": [{"label": lab, "status": "supports"}]}}
            with self.assertRaises(ValueError):
                s14.validate_ics(t)
        self.assertEqual(s14.row_status("FAILS AT ZERO STRAY", [s14.WHATIF_PREFIX + "BUDGET 12 pF (MODEL EVIDENCE ONLY)"]),
                         "conditional on an owner decision")
        self.assertEqual(s14.row_status("FAILS AT ZERO STRAY", []), "blocks")


class Bounds(unittest.TestCase):
    def test_n12_discarded_and_interrupted_decks_count(self):
        with tempfile.TemporaryDirectory() as d:
            saved = s14.LEDGER, s14.SLICES
            s14.LEDGER, s14.SLICES = Path(d) / "inv.jsonl", Path(d) / "slices.jsonl"
            try:
                b = s14.Bounds("t")
                b.hook("eval", "a" * 64)  # its line was later discarded
                b.hook("eval", "b" * 64)  # interrupted: no result line was written
                self.assertEqual(b.counts()["total"], 2)
            finally:
                s14.LEDGER, s14.SLICES = saved

    def test_slice_deadline_refuses_a_deck_whose_timeout_does_not_fit(self):
        import time as _t
        saved = runner.DEADLINE["t"]
        try:
            runner.DEADLINE["t"] = _t.time() + runner.TIMEOUT_S
            n = runner.INVOCATIONS["count"]
            with self.assertRaises(runner.SliceDeadline):
                runner.run("title\nR1 a 0 1k\nR2 a 0 1k\n.end\n", ["op1"])
            self.assertEqual(runner.INVOCATIONS["count"], n)
        finally:
            runner.DEADLINE["t"] = saved

    def test_m1_changed_byte_fails_closed(self):
        src = cells.ROOT / ".circuit-cache/sources/opa196-model/OPAx196.LIB"
        if not src.exists():
            self.skipTest("model cache absent")
        runner.WORK.mkdir(parents=True, exist_ok=True)
        bad = runner.WORK / "m1-mutated.lib"
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
        path = STUDY / "checkpoints/arm0.json"
        if not path.exists():
            self.skipTest("Arm 0 not run yet")
        a = json.loads(path.read_text())
        self.assertTrue(a["P5_swapped"] and all(x["fails"] for x in a["P5_swapped"]))


class CacheBinding(unittest.TestCase):
    def test_n9_changed_sample_fails_the_binding(self):
        closed, _ = s14.arm_r_records()
        r = next(x for x in closed if x["point"]["class"] == "D" and x["status"] == "OK")
        text, k = s14.cache_text_key(r["key"])
        if k != r["key"]:
            self.skipTest("S13 cache absent")
        files = s14.cache_files(r["key"], s14.deck_files(text))
        with tempfile.TemporaryDirectory(dir=runner.WORK.parent) as d:
            paths = {}
            for s, v in files.items():
                q = Path(d) / v.name
                shutil.copy(v, q)
                paths[s] = q
            same = s14.pinned([{"op": "closed_metrics", "point": r["point"], "tables": {s: str(v) for s, v in paths.items()}}])[0]
            self.assertTrue(s14.same_digits(s14.time_metrics(same), s14.time_metrics(r["metrics"])))
            lines = gzip.decompress(paths["t1"].read_bytes()).decode().split("\n")
            e, end, _ = r["metrics"]["stimulus"]["windows"]["K4"]["rem"][0]
            k = next(i for i, ln in enumerate(lines[1:], 1) if ln.strip() and float(ln.split()[0]) > e + (end - e) / 3)
            f = lines[k].split()
            f[1] = repr(float(f[1]) + 0.05)
            lines[k] = " ".join(f)
            paths["t1"].write_bytes(gzip.compress("\n".join(lines).encode()))
            moved = s14.pinned([{"op": "closed_metrics", "point": r["point"], "tables": {s: str(v) for s, v in paths.items()}}])[0]
            self.assertFalse(s14.same_digits(s14.time_metrics(moved), s14.time_metrics(r["metrics"])))


if __name__ == "__main__":
    unittest.main()
