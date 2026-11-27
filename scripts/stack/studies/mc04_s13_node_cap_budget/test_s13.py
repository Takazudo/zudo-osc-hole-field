"""MC04-S13 tests and mutations M1 to M11 (offline; M3 reads the recorded control run; M9 to M11 use in-memory copies)."""
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
        self.assertTrue(all(x["fails_P5"] for x in c["M3"]))


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


if __name__ == "__main__":
    unittest.main()
