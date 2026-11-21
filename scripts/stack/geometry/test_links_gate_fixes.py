"""MC04-S6 link-gate fixes: place() honours the caller's accept filter, and the a7 comparisons are hashed.

No network and no KiCad.
"""
import hashlib
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

sys.path.insert(0, str(Path(__file__).resolve().parent))

import links  # noqa: E402
import links_gate as lg  # noqa: E402

ROOT = Path(__file__).resolve().parents[3]


class Stop(Exception):
    pass


class PlaceAccept(unittest.TestCase):
    def setUp(self):
        self.saved = lg.search
        self.calls = []

    def tearDown(self):
        lg.search = self.saved

    def ctx(self):
        return SimpleNamespace(model=SimpleNamespace(memo_for=lambda _: None, drop_memo=lambda _: None))

    def test_search_inside_place_receives_accept(self):
        def fake(*args, **kw):
            self.calls.append(kw)
            return None, {}
        lg.search = fake
        accept = lambda geo: None  # noqa: E731
        ok, _ = lg.place(self.ctx(), {}, {'id': 'L1', 'front_board': 'JL'}, {}, (0, 0), set(), accept=accept)
        self.assertFalse(ok)
        self.assertIs(self.calls[0].get('accept'), accept)

    def test_lengthened_tail_check_receives_accept(self):
        def fake(*args, **kw):
            self.calls.append(kw)
            raise Stop()
        lg.search = fake
        accept = lambda geo: 'rejected'  # noqa: E731
        geo = {'front_extension_mm': 1.0, 'K_extension_mm': 0.0}
        best = (1.0, (), geo, [], 0, (0.0, 0.0), 0.0)
        with self.assertRaises(Stop):
            lg.place(self.ctx(), {}, {'id': 'L1', 'front_board': 'JL'}, {}, (0, 0), set(), best=best, accept=accept)
        self.assertEqual(self.calls[0].get('lengthen'), False)
        self.assertIs(self.calls[0].get('accept'), accept)


class ProvenanceHashesA7(unittest.TestCase):
    def test_a7_comparisons_are_an_input(self):
        a7 = links.LINK_DIR / 'link-gate-a7-comparisons.json'
        self.assertTrue(a7.exists())
        inp = {'root': ROOT, 'class_rules': {}, 'fixing_list': {'fixings': [], 'access_holes': []},
               'compliance': {'inputs_sha256': '', 'nodes': []}}
        hashes = lg.input_hashes(inp)
        key = a7.resolve().relative_to(ROOT.resolve()).as_posix()
        self.assertEqual(hashes.get(key), hashlib.sha256(a7.read_bytes()).hexdigest())


if __name__ == '__main__':
    unittest.main()
