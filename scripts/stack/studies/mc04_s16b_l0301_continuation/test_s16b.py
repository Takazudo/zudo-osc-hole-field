"""MC04-S16b cases N1 to N14 (brief Revision 2, section "Mutations").

The expected vectors and reasons are copied from the brief and are not taken from s16b.py, so a change to either side
shows. The vector has ten candidate tests (S1 S2 S3 R1 R2 R3 R4 R5 R6 R7), then six acceptance tests (A0 A1 A2 A3 A4
A6). N7 reads S16's cache (read-only). Scratch files go to the system temporary directory and are removed; no file
is written under /mnt/project-files/osc-s16b-cache/stops/ (DS-218).
"""
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import s16b as B  # noqa: E402

R = B.R
BRIEF_VECTORS = {
    'N1': 'PPPPPPPF–– ––––––', 'N3': 'PPPPPPPPPF ––––––', 'N4': 'PPPPPPPPPF ––––––', 'N5': 'PPPPPPPPPP ––––––',
    'N6': 'PPPPPPPPPP ––––––', 'N7': 'PPPPPPPPPF ––––––',
}
N7_STRUCTURE = 'R[K-P-16,K-P-18,P-K-E2]|K-P-20+P-K-E1+P-K-E3'


def blk(w, sites, x, y, d):
    return {'rec': R.block_record(w, sites), 'slot_centre': [x, y], 'direction': d}


class Vectors(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.w = R.s12.World()
        B.W = cls.w
        cls.an = R.Anchors(cls.w)
        cls.placed = R.placed_except(cls.w)

    def vector(self, blocks):
        return B.case_vector16b(self.w, blocks, self.an, self.placed)

    def test_n1_class_s_under_e1_first_survivor(self):
        v, why, det = self.vector([blk(self.w, ['P-K-E1'], 218.0, 181.25, '-x')])
        self.assertEqual(v, BRIEF_VECTORS['N1'])
        self.assertEqual(why['R5'], 'T1: C7205 (S), U8411 (S)')
        self.assertIsNone(det[0]['default_rule'], 'S16 default R5 passes it')
        self.assertEqual(sorted(det[0]['default_extra']['class_s']), ['C7205', 'U8411'])

    def test_n2_record_geometry_strict_r5(self):
        six = R.block_record(self.w, list(R.SITES), 26)
        geo = self.w.byid[R.L03]['geometry']
        bad, cls_s, _ = R.Rules(self.w, six, self.an, 'strict').t1(geo)
        self.assertEqual(sorted(r for r, c in bad if c == 'S'), sorted(R.CLASS_S_PARTS))
        self.assertEqual([r for r, c in bad if c == 'N'], [])
        # Not a vector. Observation recorded for the report: the brief's parenthetical says R4 fails first; measured,
        # R2 fails first without the Ruling P8 exemption (class distance), and with it R4 passes and R5 fails.
        ru = R.Rules(self.w, six, self.an, 'strict')
        self.assertEqual(ru.r2(geo), 'a site beyond its class distance of the connector centres')
        self.assertIsNone(ru.r2_record(geo))
        self.assertIsNone(ru.r4(geo))

    def test_n3_r7_rank1_slot(self):
        v, why, det = self.vector([blk(self.w, ['K-P-20', 'P-K-E1', 'P-K-E3'], 235.25, 182.0833, '-y')])
        self.assertEqual(v, BRIEF_VECTORS['N3'])
        self.assertEqual(det[0]['on_parts'].get('K B (slot)'), ['C8443', 'R7213'])
        self.assertEqual(R.block_record(self.w, ['K-P-20', 'P-K-E1', 'P-K-E3'])['circuits'], 14)

    def test_n4_r7_r7213_alone(self):
        v, why, det = self.vector([blk(self.w, ['P-K-E1'], 227.0, 189.0, '+x')])
        self.assertEqual(v, BRIEF_VECTORS['N4'])
        self.assertEqual(det[0]['on_parts'], {'K B (field)': ['R7213']})

    def test_n5_first_clear_survivor(self):
        v, why, det = self.vector([blk(self.w, ['P-K-E1'], 233.25, 181.25, '-y')])
        self.assertEqual(v, BRIEF_VECTORS['N5'])
        self.assertEqual(det[0]['on_parts'], {})

    def test_n6_non_e1_block_on_parts_sorts_last(self):
        sites = ['K-P-16', 'K-P-18', 'K-P-20', 'P-K-E2']
        v, why, det = self.vector([blk(self.w, sites, 234.75, 182.5, '-y')])
        self.assertEqual(v, BRIEF_VECTORS['N6'])
        self.assertEqual(set(sum(det[0]['on_parts'].values(), [])), {'C8443', 'R7213'})
        self.assertEqual(R.block_record(self.w, sites)['circuits'], 14)
        B.init_ctx()
        _, strict, surv, _ = B.census_one(sites)
        me = [e for e in surv if e['slot_centre'] == [234.75, 182.5] and e['direction'] == '-y']
        self.assertEqual(len(me), 1)
        key = lambda e: (bool(e['on_parts']), e['cost'], e['key'])  # noqa: E731
        clear = [e for e in B.pool_of16b(surv, False) if not e['on_parts']]
        self.assertTrue(clear)
        self.assertTrue(all(key(me[0]) > key(e) for e in clear))
        self.assertTrue(all(key(me[0]) > key(e) for e in surv if not e['on_parts']))

    def test_n7_rank1_scene_whole(self):
        logs = {}
        for f in sorted((B.S16_BULK / 'stage2b').glob('*.json')):
            d = json.loads(f.read_text())
            logs[d['id']] = d
        lg_ = logs[N7_STRUCTURE]
        rp = lg_['replays'][lg_['passed'] - 1]
        bl = B.blocks_of_id(N7_STRUCTURE)
        blocks = [blk(self.w, b, x['slot_centre'][0], x['slot_centre'][1], x['direction']) for b, x in zip(bl, rp['blocks'])]
        v, why, det = self.vector(blocks)
        self.assertEqual(v, BRIEF_VECTORS['N7'])
        plan = B.s16_plans()[N7_STRUCTURE]['plan']
        chosen = [(R.block_record(self.w, b), {'geometry': x['geometry'], 'slot_centre': x['slot_centre'],
                                               'direction': x['direction'], 'ring': x['ring']})
                  for b, x in zip(bl, rp['blocks'])]
        rows = R.scene_rows(self.w, chosen, plan)
        f, _ = R.check_rows16(self.w, rows)
        self.assertEqual(R.acceptance_vector(f), 'PPPPPP')
        self.assertEqual(R.s12.digest(rows), rp['digest'])
        j = B.jclean(R.judge_replan(self.w, {}, rows, chosen, plan, run_overlay_search=False))
        self.assertTrue(any('U8413' in x and 'decoupler row breaks' in x for x in j['fails'].get('A8', [])))
        self.assertTrue(any('R7213' in x for x in j['fails'].get('A9', [])))
        self.assertEqual(B.classify_lite(j['fails']), 'final')


class Order(unittest.TestCase):
    def test_n8_scene_order(self):
        got = B.simulate_scenes(3, 14, [2] * 14, 15)
        self.assertEqual([s for s, _ in got[:14]], [3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 0, 1, 2])
        self.assertTrue(all(c == 0 for _, c in got[:14]))
        self.assertEqual(got[14], (3, 1))

    def rounds(self, finish_in_round1=None):
        order = [{'id': 's%d' % i, 'e1_block': 'E', 'blocks': [], 'plan': []} for i in range(3)]
        state = B.new_state(order)
        self.assertEqual([s['o'] for s in state['structures']], [0, 1, 2])
        out = []
        for rnd in (1, 2):
            spots = []
            for s in B.round_todo(state):
                spot = B.spot_visits(s['cursor'], 2)[0]
                lite = 'pass' if (rnd == 1 and s['index'] == finish_in_round1) else None
                res = {'kind': 'scene', 'cursor': s['cursor'] + 1, 'calls': {},
                       'scene': {'spot': spot, 'lite': {'status': lite} if lite else None}}
                B.apply_result(state, s, res, 1)
                spots.append((s['index'], spot))
            state['position'] = 0
            out.append(spots)
        return out

    def test_n14_cross_structure_order(self):
        r1, r2 = self.rounds()
        self.assertEqual([s for _, s in r1], [0, 1, 0])
        self.assertEqual([s for _, s in r2], [1, 0, 1])
        r1, r2 = self.rounds(finish_in_round1=1)
        self.assertEqual([i for i, _ in r2], [0, 2])


class Lite(unittest.TestCase):
    NOTRUN = "overlay search not run for [('K', 'U4213')]"

    def test_n11_lite_passer(self):
        self.assertEqual(B.classify_lite({'A8': [self.NOTRUN]}), 'pass')
        self.assertEqual(B.classify_lite({'A8': [self.NOTRUN], 'A5': ['S16-B[P-K-E1] loop -1.0 mm < 0']}), 'final')

    def test_n13_lite_undecided(self):
        f = {'A8': [self.NOTRUN], 'A9': ['R_ISO R7213 farther from U7204 than at the base']}
        self.assertEqual(B.classify_lite(f), 'undecided')
        f['A8'].append("('K', 'U8413'): a decoupler row breaks the block rule while the IC row is unchanged "
                       "(stricter reading: no knock-on exemption)")
        self.assertEqual(B.classify_lite(f), 'final')

    def test_final_without_search(self):
        self.assertEqual(B.classify_lite({'A10': ['K C8308: effective pose differs']}), 'final')


class Caps(unittest.TestCase):
    def test_n9_overlay_cap_inside_a_scene(self):
        d = Path(tempfile.mkdtemp(prefix='s16b-n9-'))
        try:
            p = d / 'checkpoints' / 'stage3' / 'overlay-count.json'
            B.write_json(p, {'cap': 10, 'count': 6, 'before_each': [{'count_before': i} for i in range(6)]})
            ran = []
            c = B.OverlayCounter(p)
            search = c.wrap(lambda f, b, ic: ran.append(ic) or ([], None, None))

            def scene():
                for i in range(6):
                    search(None, 'K', 'U%d' % i)
                return {'fails': {}}
            g = B.judge_full_guarded(scene)
            self.assertEqual(g['status'], 'STAGE 3 INCOMPLETE (CAP)')
            self.assertEqual(len(ran), 4)
            self.assertFalse(issubclass(B.OverlayCap, TypeError))
            st = B.read_json(p)
            self.assertEqual(st['count'], 10)
            self.assertEqual([x['count_before'] for x in st['before_each']], list(range(10)))
            r = subprocess.run([sys.executable, '-c', 'import json,sys; print(json.load(open(sys.argv[1]))["count"])',
                                str(p)], capture_output=True, text=True)
            self.assertEqual(r.stdout.strip(), '10')
            self.assertEqual(B.OverlayCounter(p).read()['count'], 10)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def gate(self, d):
        env = {k: v for k, v in os.environ.items() if not k.startswith('S16B_')}
        env.update({'S16B_GATE_CK': str(d / 'checkpoints'), 'S16B_GATE_STOPS': str(d / 'durable' / 'stops') + '/',
                    'S16B_GATE_DECISIONS': str(d / 'decisions.md'), 'PYTHONDONTWRITEBYTECODE': '1'})
        p = subprocess.run([sys.executable, str(HERE / 's16b.py'), '--gate'], capture_output=True, text=True, env=env)
        return p.returncode, p.stdout

    def test_n10_stop_records(self):
        d = Path(tempfile.mkdtemp(prefix='s16b-n10-'))
        try:
            self.assertFalse(str(d).startswith('/mnt/project-files'))
            paths = B.StopPaths(d / 'checkpoints', str(d / 'durable' / 'stops') + '/', d / 'decisions.md')
            (d / 'checkpoints').mkdir()
            self.assertEqual(self.gate(d)[0], 0)
            h, ok = B.record_stop('STOP 1: synthetic', paths=paths)
            self.assertTrue(ok)
            self.assertEqual(B.durable_stops(paths), ['stop-%s.json' % h])
            self.assertNotEqual(self.gate(d)[0], 0)
            (d / 'checkpoints' / 'stop.json').unlink()
            self.assertNotEqual(self.gate(d)[0], 0)  # run.json stop and the durable copy remain
            rec = B.read_json(paths.run_json)
            rec['stop'] = None
            B.write_json(paths.run_json, rec)
            self.assertNotEqual(self.gate(d)[0], 0)  # the durable copy alone
            B.write_json(paths.ruling, {'decision_row': 'DS-999', 'stop_sha256': h})
            (d / 'decisions.md').write_text('| ID | Date |\n| DS-998 | x %s |\n' % h)
            self.assertNotEqual(self.gate(d)[0], 0)  # the row ID is not in decisions.md
            B.write_json(paths.ruling, {'decision_row': 'DS-998', 'stop_sha256': '0' * 64})
            self.assertNotEqual(self.gate(d)[0], 0)  # the hash differs
            B.write_json(paths.ruling, {'decision_row': 'DS-998', 'stop_sha256': h})
            rc, out = self.gate(d)
            self.assertEqual(rc, 0, out)
        finally:
            shutil.rmtree(d, ignore_errors=True)

    def test_n12_changed_pin_and_altered_cache(self):
        d = Path(tempfile.mkdtemp(prefix='s16b-n12-'))
        try:
            for p_ in B.PIN_FILES:
                t = d / p_
                t.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(B.ROOT / p_, t)
            pins = d / 'pins.json'
            B.write_json(pins, {'files': B.compute_pins(d)})
            self.assertEqual(B.verify_pins(d, pins), [])
            f = d / B.PIN_FILES[0]
            b = bytearray(f.read_bytes())
            b[-2] ^= 1
            f.write_bytes(bytes(b))
            self.assertEqual(B.verify_pins(d, pins), ['%s changed' % B.PIN_FILES[0]])
            cache = d / 'cache'
            for i in range(3):
                B.write_json(cache / ('x%d.json' % i), {'i': i})
            man = d / 'bulk-manifest.json'
            B.write_json(man, {'files': {r: {'sha256': B.sha_file(cache / r), 'bytes': (cache / r).stat().st_size}
                                         for r in B.bulk_files(cache)}})
            self.assertEqual(R.bulk_state(cache, man), (True, []))
            B.write_json(cache / 'x1.json', {'i': 'altered'})
            present, bad = R.bulk_state(cache, man)
            self.assertTrue(present and bad)
            shutil.rmtree(cache)
            self.assertEqual(R.bulk_state(cache, man), (False, []))
        finally:
            shutil.rmtree(d, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
