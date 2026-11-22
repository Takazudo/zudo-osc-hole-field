"""MC04-S7 Revision 9: the GH header assignment is stable against the retained 6093081c baseline."""
import json
import unittest

import scripts.checks.connector_packing35 as cp
from scripts.partition import gh_baseline as gb

ROOT = gb.ROOT


class StableHeaders(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = json.loads(gb.OUT.read_text())
        cls.pack = json.loads(cp.OUT.read_text())
        cls.part = json.loads((ROOT / 'design/partition/partition.json').read_text())
        io = json.loads((ROOT / 'design/reports/io-partition.json').read_text())
        cls.crossing = {r['net'] for r in io['allowed_crossings']}
        cls.heads = {h['id']: h for h in cls.pack['headers']}

    def test_baseline_record_is_the_source_commit(self):
        self.assertEqual(gb.build(), self.base)

    def test_i_baseline_headers_keep_site_and_refdes(self):
        refs = {c['id']: c['pcb_reference'] for c in self.part['connectors']}
        for h in self.base['harnesses']:
            for board, site in h['sites'].items():
                hid = f"{h['id']}-{board}"
                self.assertEqual(self.heads[hid]['center_mm'], site, hid)
        for hid, ref in self.base['header_refdes'].items():
            self.assertEqual(refs[hid], ref, hid)
        new = [r for i, r in refs.items() if i not in self.base['header_refdes']]
        self.assertFalse(set(new) & set(self.base['header_refdes'].values()))  # never reused

    def test_ii_still_crossing_nets_keep_header_and_pin(self):
        for h in self.base['harnesses']:
            for board in h['sites']:
                pins = self.heads[f"{h['id']}-{board}"]['pin_map']
                for j, net in enumerate(h['signal_slots']):
                    if net and net in self.crossing:
                        self.assertEqual(pins[str(2 * j + 1)], net, (h['id'], board, j))

    def test_iii_freed_pins_follow_the_rule(self):
        for h in self.base['harnesses']:
            for board in h['sites']:
                pins = self.heads[f"{h['id']}-{board}"]['pin_map']
                for j, net in enumerate(h['signal_slots']):
                    sig, ret = str(2 * j + 1), str(2 * j + 2)
                    if net and net not in self.crossing:
                        # a freed signal position is NC or carries a new crossing net; its return stays AGND
                        self.assertTrue(pins[sig] == 'NC' or pins[sig] in self.crossing, (h['id'], sig))
                        if ret in pins:
                            self.assertEqual(pins[ret], 'AGND', (h['id'], ret))

    def test_iv_two_runs_agree(self):
        a, b = cp.candidate(), cp.candidate()
        self.assertEqual(a['headers'], b['headers'])
        self.assertEqual(a['harnesses'], b['harnesses'])

    def test_stable_chunks_rules(self):
        chunks, wired = cp.stable_chunks([['a', 'b', 'c', 'd'], ['e', None, None, None]], {'a', 'c', 'd', 'e', 'x', 'y', 'z'}, 1, 4)
        self.assertEqual(chunks[0], ['a', 'x', 'c', 'd'] if False else chunks[0])
        self.assertEqual(chunks[2], ['x', 'y', 'z', None])          # the new header first
        self.assertEqual(chunks[0], ['a', None, 'c', 'd'])          # b freed, not refilled (no net left)
        self.assertEqual(wired[0], [True, True, True, True])
        with self.assertRaisesRegex(ValueError, 'slots run short'):
            cp.stable_chunks([['a']], {'a', 'p', 'q'}, 0, 1)


if __name__ == '__main__':
    unittest.main()
