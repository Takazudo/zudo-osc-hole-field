import hashlib
import importlib.util
import json
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



class CurrentScene(unittest.TestCase):
    """The current-scene mode (MC04-S7 Revision 1) reads the committed gate, not the pinned R1 spec."""

    @classmethod
    def setUpClass(cls):
        cls.gate = json.loads((c.ROOT / c.GATE).read_text())
        cls.scene, cls.unresolved, cls.accepted, cls.hashes = c.current_scene()

    def test_unresolved_is_the_gate_record(self):
        rows = self.gate['replacement']['footprints']
        self.assertEqual(self.unresolved, [r for r in rows if r['new'] is None])
        self.assertEqual(self.accepted, sum(1 for r in rows if r['new'] is not None))

    def test_records_every_input(self):
        for name in list(self.gate['provenance']['input_sha256']) + [c.GATE, c.PARTITION_REPORT, *c.STUDY_PROGRAM]:
            self.assertIn(name, self.hashes)
        for name in (c.GATE, c.PARTITION_REPORT):
            self.assertEqual(self.hashes[name], hashlib.sha256((c.ROOT / name).read_bytes()).hexdigest())

    def test_moved_bodies_are_at_their_new_place(self):
        for r in self.gate['replacement']['footprints']:
            if r['new'] is not None:
                self.assertEqual(self.scene.bodies[(r['board'], r['ref'])]['origin'], r['new'])
                break

    def test_stale_input_is_refused(self):
        real = c.r1.lg.input_hashes

        def changed(inp):
            out = real(inp)
            out['design/stack/geometry/parameters.json'] = '0' * 64
            return out
        c.r1.lg.input_hashes = changed
        try:
            with self.assertRaisesRegex(c.r1.AdmissionError, 'stale input.*parameters.json'):
                c.current_scene()
        finally:
            c.r1.lg.input_hashes = real

    def test_stale_names(self):
        self.assertEqual(c.stale_inputs({'a': '1', 'b': '2'}, {'a': '1', 'b': '3', 'c': '4'}), ['b', 'c'])
        self.assertEqual(c.stale_inputs({'a': '1'}, {'a': '1'}), [])


if __name__ == '__main__':
    unittest.main()
