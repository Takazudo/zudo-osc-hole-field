#!/usr/bin/env python3
"""Narrow arithmetic and retained-source checks; never hardware qualification."""
from pathlib import Path
import hashlib
import json
import unittest

ROOT = Path(__file__).resolve().parents[5]
HERE = Path(__file__).resolve().parent


def penetration(spacing, pin=6.0, separation_tolerance=0.10):
    return (2.54-.15 + pin-.20 + 8.5-.20-spacing-separation_tolerance,
            2.54+.15 + pin+.20 + 8.5+.20-spacing+separation_tolerance)


class Evidence(unittest.TestCase):
    def test_axial_screen(self):
        lo, hi = penetration(12)
        self.assertAlmostEqual(lo, 4.39)
        self.assertAlmostEqual(hi, 5.69)
        self.assertGreater(lo, 2.40)
        self.assertLess(hi, 5.96)
        self.assertAlmostEqual(17.59+.10-5.96, 11.73)
        self.assertAlmostEqual(16.49-.10-2.40, 13.99)
        self.assertLessEqual(penetration(11.73)[1]-5.96, 1e-12)
        self.assertAlmostEqual(12-.1-(2.54+.15+8.5+.2), .51)

    def test_existing_gap_fails(self):
        self.assertLess(penetration(19.2)[1], 0)
        self.assertAlmostEqual(penetration(19.2, 11.21)[0], 2.4)
        self.assertAlmostEqual(penetration(19.2, 13.47)[1], 5.96)

    def test_retained_pdf_bytes(self):
        for source in json.loads((HERE/'sources.json').read_text())['sources']:
            data = (ROOT/source['local_cache']).read_bytes()
            self.assertTrue(data.startswith(b'%PDF'))
            self.assertEqual(hashlib.sha256(data).hexdigest(), source['sha256'])


if __name__ == '__main__':
    unittest.main()
