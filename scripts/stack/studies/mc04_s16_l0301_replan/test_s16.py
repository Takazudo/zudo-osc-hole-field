"""MC04-S16 unit tests: the order builder (Ruling P7) and the mutations M1 to M27 with the brief's full vectors.

The expected vectors are copied from the brief (Revision 4, section "Tests and mutations") and are not taken from
replan.py, so a change to either side shows. The mutation vectors need the slots that arm 0 writes to
checkpoints/mutation-slots.json; without that file those tests are skipped and say so.
"""
import copy
import itertools
import json
import math
import os
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import replan as R  # noqa: E402

BRIEF_VECTORS = {
    'M1': 'PPPPPPPPP FPPPPP', 'M2': '––––––––– PPPPPP', 'M3': 'F–––––––– ––––––', 'M4': 'PF––––––– ––––––',
    'M5': 'PPF–––––– ––––––', 'M6': 'PPF–––––– ––––––', 'M7': 'PPPF––––– ––––––', 'M8': 'PPPPF–––– ––––––',
    'M9': 'PPPPPF––– ––––––', 'M10': 'PPPPPPF–– ––––––', 'M11': 'PPPPPPPF– ––––––', 'M12': 'PPPPPPPPF ––––––',
    'M13': '––––––––– FPFPPP', 'M14': '––––––––– FPPFPP', 'M15': '––––––––– FPPPFP', 'M16': '––––––––– FPPPPF',
    'M22': '––––––––– FFFPPP', 'M23': 'PPF–––––– ––––––', 'M24': 'PF––––––– ––––––', 'M25': 'PF––––––– ––––––',
    'M27a': 'PPF–––––– ––––––', 'M28': 'PF––––––– ––––––',
}
SLOTS = HERE / 'checkpoints' / 'mutation-slots.json'


def sig(n, cls, site='S'):
    return [('/T/%s%d' % (cls[0], i), cls, site) for i in range(n)]


class Builder(unittest.TestCase):
    """capped_order and its checks; no World needed."""

    def test_split_five_logic(self):
        o = R.capped_order(sig(5, 'LOGIC'), 8)
        self.assertIsNotNone(o)
        kinds = [p['kind'][0] for p in o]
        runs = [len(r) for r in ''.join(kinds).replace('u', 'g').split('g') if r]
        self.assertEqual(runs, [3, 2])
        self.assertTrue(R.order_ok('t', o))

    def test_too_long_is_none(self):
        self.assertIsNone(R.capped_order(sig(4, 'LOGIC') + sig(2, 'ANALOGUE', 'T'), 8))

    def test_built_size(self):
        self.assertEqual(R.built_size(sig(3, 'LOGIC'))[0], 8)


class WithWorld(unittest.TestCase):
    """Ruling P9's record block and the builder on the World."""
    @classmethod
    def setUpClass(cls):
        cls.w = R.s12.World()

    def test_c3b_five_records(self):
        ok, out = R.c3b_control(self.w)
        self.assertTrue(ok, out)

    def test_sizes_formula(self):
        """For all 63 site subsets the block size equals circuits_needed plus ceil(n / 3) - 1 for n >= 4 logic lines,
        rounded up to stock."""
        for k in range(1, 7):
            for sub in itertools.combinations(R.SITES, k):
                rec = R.block_record(self.w, list(sub))
                cls = [c for _, c, _ in R.site_signals(self.w.site_by, sorted(sub))]
                n = cls.count('LOGIC')
                need = R.lg.circuits_needed(cls) + (math.ceil(n / 3) - 1 if n >= 4 else 0)
                self.assertEqual(rec['circuits'], min(s for s in R.STOCK if s >= need), sub)

    def test_record_block_l13(self):
        rb = R.record_block(self.w, 'P-K-P-L13.01.01.01')
        self.assertEqual((rb['circuits'], rb['signals'], rb['built'], R.s2_order(rb)), (8, 5, True, None))
        self.assertEqual(sum(1 for p in rb['positions'] if p['kind'] != 'unused'), 7)

    def test_m19_scene_row_digest(self):
        rows = copy.deepcopy(self.w.base_rows_list)
        d0 = R.s12.digest(rows)
        r = next(x for x in rows if x['new'] is not None)
        r['new'] = [r['new'][0] + 0.25, r['new'][1]]
        self.assertNotEqual(R.s12.digest(rows), d0)


@unittest.skipUnless(SLOTS.exists(), 'checkpoints/mutation-slots.json absent: arm 0 has not run')
class Mutations(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.w = R.s12.World()
        cls.res = R.mutation_cases(cls.w, json.loads(SLOTS.read_text()))

    def test_table_matches_brief(self):
        self.assertEqual(R.MUTATIONS, BRIEF_VECTORS)


def _vector_test(k):
    def t(self):
        self.assertEqual(self.res[k]['vector'], BRIEF_VECTORS[k], self.res[k].get('why'))
    return t


for _k in BRIEF_VECTORS:
    setattr(Mutations, 'test_%s' % _k.lower(), _vector_test(_k))


def _extra(self):
    self.assertEqual(R.mutation_problems(self.res), [])


Mutations.test_reasons_and_non_vectors = _extra


class PinsAndCache(unittest.TestCase):
    """M20 and M21 on copies inside the cache's scratch folder, removed afterwards."""

    def setUp(self):
        self.tmp = R.BULK / R.SCRATCH / ('test-%d' % os.getpid())
        if self.tmp.exists():
            shutil.rmtree(self.tmp)
        self.tmp.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)
        try:
            (R.BULK / R.SCRATCH).rmdir()
        except OSError:
            pass

    def test_m20_pins_refuse_a_changed_byte(self):
        pins = self.tmp / 'pins.json'
        R.write_json(pins, {'files': R.compute_pins()})
        src = self.tmp / 'src'
        for p in R.PIN_FILES:
            (src / p).parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(R.ROOT / p, src / p)
        self.assertEqual(R.verify_pins(src, pins), [])
        f = src / R.PIN_FILES[0]
        b = bytearray(f.read_bytes())
        b[10] ^= 1
        f.write_bytes(bytes(b))
        self.assertEqual(R.verify_pins(src, pins), ['%s changed' % R.PIN_FILES[0]])

    def test_m20_driver_refuses_to_start(self):
        out = self.tmp / 'dev'
        out.mkdir()
        pins = R.compute_pins()
        pins[R.PIN_FILES[0]] = '0' * 64
        R.write_json(out / 'pins.json', {'files': pins})
        env = dict(os.environ, S16_DEV_OUT=str(out), PYTHONDONTWRITEBYTECODE='1')
        p = subprocess.run([sys.executable, str(HERE / 'replan.py'), '--run'], capture_output=True, text=True, env=env)
        self.assertNotEqual(p.returncode, 0)
        self.assertIn('the driver does not start', p.stderr)
        self.assertFalse((out / 'checkpoints' / 'run.json').exists())

    def test_m21_altered_then_removed(self):
        bulk = self.tmp / 'cache'
        (bulk / 'a').mkdir(parents=True)
        R.write_json(bulk / 'a' / 'x.json', {'v': 1})
        R.write_json(bulk / 'y.json', {'v': 2})
        man = self.tmp / 'bulk-manifest.json'
        R.write_json(man, {'files': {r: {'sha256': R.sha_file(bulk / r), 'bytes': (bulk / r).stat().st_size}
                                     for r in R.bulk_files(bulk)}})
        self.assertEqual(R.bulk_state(bulk, man), (True, []))
        (bulk / 'y.json').write_text('{"v": 3}\n')
        present, bad = R.bulk_state(bulk, man)
        self.assertTrue(present and bad)
        shutil.rmtree(bulk)
        self.assertEqual(R.bulk_state(bulk, man), (False, []))


if __name__ == '__main__':
    unittest.main()
