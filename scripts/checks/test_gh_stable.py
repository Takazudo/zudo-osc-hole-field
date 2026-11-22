"""MC04-S7 Revision 9: the GH header assignment is stable against the retained 6093081c baseline. Checks (i)-(iii) run
on the committed packing and on a fresh candidate; (iv) runs the packer in two processes with different hash seeds
(Revision 11 addendum item 4)."""
import hashlib
import json
import os
import subprocess
import sys
import unittest
from unittest import mock

import scripts.checks.connector_packing35 as cp
from scripts.partition import gh_baseline as gb

ROOT = gb.ROOT


def site_errors(base, pack):
    """(i) every baseline header end keeps its site."""
    heads = {h['id']: h for h in pack['headers']}
    return [f"{h['id']}-{b}" for h in base['harnesses'] for b, site in h['sites'].items()
            if heads[f"{h['id']}-{b}"]['center_mm'] != site]


def pin_errors(base, pack, crossing):
    """(ii) a still-crossing net keeps its header and signal pin; (iii) a freed signal pin is NC or a new crossing
    net, and its return stays AGND."""
    heads = {h['id']: h for h in pack['headers']}
    errs = []
    for h in base['harnesses']:
        for board in h['sites']:
            pins = heads[f"{h['id']}-{board}"]['pin_map']
            for j, net in enumerate(h['signal_slots']):
                sig, ret = str(2 * j + 1), str(2 * j + 2)
                if not net:
                    continue
                if net in crossing:
                    if pins[sig] != net:
                        errs.append(('ii', h['id'], board, sig))
                else:
                    if not (pins[sig] == 'NC' or pins[sig] in crossing):
                        errs.append(('iii', h['id'], board, sig))
                    if ret in pins and pins[ret] != 'AGND':
                        errs.append(('iii', h['id'], board, ret))
    return errs


def consecutive(base, current, new_headers, count):
    """The pre-Revision 9 packer: sorted nets in consecutive chunks (used to show the checks catch a revert)."""
    nets = sorted(current)
    chunks = [nets[i:i + count] for i in range(0, len(nets), count)]
    return chunks, [[True] * len(c) for c in chunks]


DIGEST = ('import hashlib, json, scripts.checks.connector_packing35 as cp; c = cp.candidate(); '
          'print(hashlib.sha256(json.dumps([c["headers"], c["harnesses"]], sort_keys=True).encode()).hexdigest())')


class StableHeaders(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base = json.loads(gb.OUT.read_text())
        cls.pack = json.loads(cp.OUT.read_text())
        cls.fresh = cp.candidate()
        cls.part = json.loads((ROOT / 'design/partition/partition.json').read_text())
        io = json.loads((ROOT / 'design/reports/io-partition.json').read_text())
        cls.crossing = {r['net'] for r in io['allowed_crossings']}

    def test_baseline_record_is_the_source_commit(self):
        self.assertEqual(gb.build(), self.base)
        self.assertEqual(len(self.base['source']['commit']), 40)

    def test_fresh_candidate_is_the_committed_packing(self):
        self.assertEqual(self.fresh['headers'], self.pack['headers'])
        self.assertEqual(self.fresh['harnesses'], self.pack['harnesses'])

    def test_i_baseline_headers_keep_site_and_refdes(self):
        for pack in (self.pack, self.fresh):
            self.assertEqual(site_errors(self.base, pack), [])
        refs = {c['id']: c['pcb_reference'] for c in self.part['connectors']}
        for hid, ref in self.base['header_refdes'].items():
            self.assertEqual(refs[hid], ref, hid)
        new = [r for i, r in refs.items() if i not in self.base['header_refdes']]
        self.assertFalse(set(new) & set(self.base['header_refdes'].values()))  # never reused

    def test_ii_iii_pins(self):
        for pack in (self.pack, self.fresh):
            self.assertEqual(pin_errors(self.base, pack, self.crossing), [])

    def test_a_reverted_consecutive_packer_fails_the_checks(self):
        with mock.patch.object(cp, 'stable_chunks', consecutive):
            try:
                reverted = cp.candidate()
            except ValueError:
                return  # refusing to pack also fails
        self.assertTrue(site_errors(self.base, reverted) or pin_errors(self.base, reverted, self.crossing))

    def test_iv_two_processes_with_different_hash_seeds_agree(self):
        out = []
        for seed in ('1', '4242'):
            env = dict(os.environ, PYTHONHASHSEED=seed)
            r = subprocess.run([sys.executable, '-c', DIGEST], cwd=ROOT, env=env, capture_output=True, text=True,
                               check=True)
            out.append(r.stdout.strip().splitlines()[-1])
        self.assertEqual(out[0], out[1])
        self.assertEqual(out[0], hashlib.sha256(json.dumps([self.pack['headers'], self.pack['harnesses']],
                                                           sort_keys=True).encode()).hexdigest())

    def test_stable_chunks_rules(self):
        chunks, wired = cp.stable_chunks([['a', 'b', 'c', 'd'], ['e', None, None, None]],
                                         {'a', 'c', 'd', 'e', 'x', 'y', 'z'}, 1, 4)
        self.assertEqual(chunks[2], ['x', 'y', 'z', None])          # the new header first
        self.assertEqual(chunks[0], ['a', None, 'c', 'd'])          # b freed, not refilled (no net left)
        self.assertEqual(wired[0], [True, True, True, True])
        with self.assertRaisesRegex(ValueError, 'slots run short'):
            cp.stable_chunks([['a']], {'a', 'p', 'q'}, 0, 1)

    def test_freed_slot_is_refilled_before_unwired_slots(self):
        chunks, wired = cp.stable_chunks([['a', 'b', None, None]], {'a', 'n1', 'n2'}, 0, 4)
        self.assertEqual(chunks[0], ['a', 'n1', 'n2', None])        # freed slot 1 first, then unwired slot 2
        self.assertEqual(wired[0], [True, True, False, False])
        self.assertEqual(cp.header_pins(chunks[0], wired[0], 8), ['a', 'AGND', 'n1', 'AGND', 'n2', 'AGND', 'NC', 'NC'])

    def test_freed_unrefilled_slot_is_nc_with_its_agnd_return(self):
        chunks, wired = cp.stable_chunks([['a', 'b', 'c', None]], {'a', 'c'}, 0, 4)
        self.assertEqual(cp.header_pins(chunks[0], wired[0], 8), ['a', 'AGND', 'NC', 'AGND', 'c', 'AGND', 'NC', 'NC'])

    def test_freed_pin_7_of_an_octave_header_is_agnd(self):
        """Revision 11 addendum item 5: a 7-contact header with its pin-7 slot freed and not refilled carries three
        nets; pin 7 takes the fresh-header AGND."""
        chunks, wired = cp.stable_chunks([['s', 'o3', 'o4', 'o5']], {'s', 'o3', 'o4'}, 0, 4)
        self.assertEqual(chunks[0], ['s', 'o3', 'o4', None])
        self.assertEqual(cp.header_pins(chunks[0], wired[0], 7), ['s', 'AGND', 'o3', 'AGND', 'o4', 'AGND', 'AGND'])
        self.assertEqual(cp.header_pins(['s', 'o3', 'o4'], None, 7), ['s', 'AGND', 'o3', 'AGND', 'o4', 'AGND', 'AGND'])
        # a net on the pin-7 slot is never overwritten
        self.assertEqual(cp.header_pins(['s', None, 'o4', 'n'], [True, True, True, False], 7),
                         ['s', 'AGND', 'NC', 'AGND', 'o4', 'AGND', 'n'])


if __name__ == '__main__':
    unittest.main()
