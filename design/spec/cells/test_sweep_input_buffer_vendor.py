"""Offline checks of the input-buffer harness arithmetic (no ngspice, no vendor model)."""
import cmath
import math
import unittest

from design.spec.cells.sweep_input_buffer_vendor import Wave, loop_metrics, middlebrook, settle_time


def freqs(n=601, lo=1.0, hi=1e9):
    return [lo * (hi / lo) ** (k / (n - 1)) for k in range(n)]


class LoopMetrics(unittest.TestCase):
    def test_single_pole_crossover_and_90_degree_margin(self):
        f = freqs()
        a0, fp = 1e5, 10.0  # crossover near a0 * fp = 1 MHz
        loop = [a0 / (1 + 1j * x / fp) for x in f]
        m = loop_metrics(f, loop)
        self.assertAlmostEqual(m["crossover_Hz"] / 1e6, 1.0, delta=0.01)
        self.assertAlmostEqual(m["phase_margin_deg"], 90.0, delta=0.5)
        self.assertAlmostEqual(m["dc_loop_gain_dB"], 20 * math.log10(a0 / abs(1 + 1j / fp)), delta=1e-9)

    def test_two_pole_margin_matches_closed_form(self):
        f = freqs()
        a0, p1, p2 = 1e5, 10.0, 786e3
        gain = lambda x: a0 / abs((1 + 1j * x / p1) * (1 + 1j * x / p2))  # noqa: E731
        lo, hi = 1.0, 1e9
        for _ in range(200):
            mid = math.sqrt(lo * hi)
            lo, hi = (mid, hi) if gain(mid) > 1 else (lo, mid)
        expected = 180 - math.degrees(math.atan(lo / p1) + math.atan(lo / p2))
        m = loop_metrics(f, [a0 / ((1 + 1j * x / p1) * (1 + 1j * x / p2)) for x in f])
        self.assertAlmostEqual(m["crossover_Hz"] / lo, 1.0, delta=0.01)
        self.assertAlmostEqual(m["phase_margin_deg"], expected, delta=0.3)

    def test_phase_is_unwrapped_past_180(self):
        f = freqs()
        loop = [1e6 / ((1 + 1j * x / 10.0) * (1 + 1j * x / 1e5) * (1 + 1j * x / 2e5)) for x in f]
        m = loop_metrics(f, loop)
        self.assertLess(m["phase_margin_deg"], 0.0)  # unstable loop reads as a negative margin

    def test_no_crossover(self):
        f = freqs(51)
        m = loop_metrics(f, [complex(0.5, 0)] * len(f))
        self.assertIsNone(m["crossover_Hz"])
        self.assertIsNone(m["phase_margin_deg"])


class Middlebrook(unittest.TestCase):
    """Tv and Ti from an ideal break: Tv = T(1 + k) + k, Ti = T(1 + 1/k) + 1/k with k = Zs/Zl."""

    def check(self, t, k):
        tv = t * (1 + k) + k
        ti = t * (1 + 1 / k) + 1 / k
        got, ratio = middlebrook(tv, ti)
        self.assertLess(abs(got - t), 1e-9 * max(1, abs(t)))
        self.assertLess(abs(ratio - k), 1e-9 * max(1, abs(k)))

    def test_recovers_true_loop_gain_and_impedance_ratio(self):
        for t in (100.0, 1.0 * cmath.exp(-2.3j), 0.3j - 0.1):
            for k in (1e-6, 0.2, 1.0, 5.0, 1e4):
                self.check(t, k)

    def test_high_impedance_load_reduces_to_voltage_injection(self):
        t, k = 2.0 * cmath.exp(-2j), 1e-9
        tv = t * (1 + k) + k
        got, _ = middlebrook(tv, t * (1 + 1 / k) + 1 / k)
        self.assertLess(abs(got - tv), 1e-6)


class SettleTime(unittest.TestCase):
    def wave(self, tau=1e-6, amp=1.0, n=20001, stop=100e-6):
        t = [k * stop / (n - 1) for k in range(n)]
        return Wave(t, [amp * (1 - math.exp(-x / tau)) for x in t])

    def test_exponential_settles_at_tau_ln(self):
        w = self.wave()
        s = settle_time(w, 0.0, 100e-6, 1.0, 1e-3)
        self.assertAlmostEqual(s / 1e-6, math.log(1000), delta=0.01)

    def test_already_inside_band_is_zero(self):
        w = Wave([0, 1e-6, 2e-6], [1.0, 1.0002, 0.9999])
        self.assertEqual(settle_time(w, 0.0, 2e-6, 1.0, 1e-3), 0.0)

    def test_never_settles_is_none(self):
        w = self.wave(tau=1e-3)
        self.assertIsNone(settle_time(w, 0.0, 100e-6, 1.0, 1e-3))


if __name__ == "__main__":
    unittest.main()
