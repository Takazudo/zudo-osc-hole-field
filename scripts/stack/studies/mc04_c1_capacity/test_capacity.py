import importlib.util
from pathlib import Path
import unittest
import numpy as np

spec = importlib.util.spec_from_file_location('capacity', Path(__file__).with_name('capacity.py'))
c = importlib.util.module_from_spec(spec); spec.loader.exec_module(c)


class Tests(unittest.TestCase):
    def test_fits_respects_blocked_cells(self):
        m = np.zeros((20, 20), bool); m[10, :] = True  # first axis is x
        box = [0.0, 0.0, 1.0, 1.0]  # 5 cells wide at 0.25 mm
        pts = c.fits(m, (0.0, 0.0), box)
        self.assertTrue(pts)
        for x, y in pts:
            i0 = int(round(x / c.STEP)); self.assertTrue(i0 + 4 < 10 or i0 > 10)

    def test_fits_none_when_full(self):
        self.assertEqual(c.fits(np.ones((10, 10), bool), (0.0, 0.0), [0, 0, 0.5, 0.5]), [])

    def test_rotation_box(self):
        fp = {'origin': [0, 0], 'courtyard': [-1, -2, 1, 2], 'pads': [{'bbox': [-0.5, -1.5, 0.5, 1.5]}]}
        self.assertEqual(c.footprint_box(fp, 1), [-2, -1, 2, 1])


if __name__ == '__main__':
    unittest.main()
