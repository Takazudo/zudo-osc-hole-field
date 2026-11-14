"""Tests for the ST-06 SUB toggle specification. No network, no KiCad."""
from pathlib import Path
import itertools
import json
import re
import unittest

import sub_toggle as st

ROOT = Path(__file__).resolve().parents[3]
SKILLS = ROOT / '.claude/skills'
PERIOD = 10000
SETTLE = 4


def level_at(sim, net, t):
    return sim.level(net, t)


def samples(sim, net='SUB_OUT'):
    return [level_at(sim, net, t - 100) for t in sim.resets[SETTLE:]]


def assert_mode(test, sim, mode, msg):
    window = (sim.resets[SETTLE], sim.resets[-1])
    edges = [t for t, _ in sim.trace.get('SUB_OUT', []) if window[0] <= t < window[1]]
    if mode == 'PUL':
        changes = [t for t, _ in sim.trace.get('PULSE_LOGIC', [])]
        mids = [(a + b) // 2 for a, b in zip(changes, changes[1:]) if a >= window[0]]
        test.assertTrue(mids, msg)
        for t in mids:
            test.assertEqual(level_at(sim, 'SUB_OUT', t), level_at(sim, 'PULSE_LOGIC', t), msg)
        for t in edges:
            test.assertTrue(any(0 < t - c < 500 for c in changes), f'{msg}: stray edge at {t}')
        return
    out = samples(sim)
    step = 1 if mode == 'DIV2' else 2
    for k in range(len(out) - step):
        test.assertEqual(out[k + step], 1 - out[k], f'{msg}: {out}')
    n = len(sim.resets) - 1 - SETTLE
    test.assertIn(len(edges), {n // step, -(-n // step)}, f'{msg}: {len(edges)} edges for {n} resets')
    for t in edges:
        test.assertTrue(any(0 < t - r < 500 for r in sim.resets), f'{msg}: edge at {t} not after a reset')


class TestSpecFile(unittest.TestCase):
    def test_spec_matches_generator(self):
        self.assertEqual(st.SPEC.read_text(), st.render(), 'regenerate spec.json')

    def test_no_needs_design_and_proposal_status(self):
        spec = json.loads(st.SPEC.read_text())
        self.assertEqual(spec['decision_state']['needs_design'], [])
        self.assertIn('PROPOSAL', spec['status'])
        self.assertNotIn('validated', json.dumps(spec).lower().replace('unvalidated', ''))


class TestStateTable(unittest.TestCase):
    """Every position, both travel states and the faults have one defined mode."""

    def test_table_covers_every_select_combination(self):
        combos = {(r['sel_a'], r['sel_b']) for r in st.STATE_TABLE}
        self.assertEqual(combos, set(itertools.product((0, 1), repeat=2)))
        kinds = [r['kind'] for r in st.STATE_TABLE]
        self.assertEqual(kinds.count('position'), 3)
        self.assertEqual(kinds.count('travel'), 2)

    def test_same_levels_give_same_mode(self):
        seen = {}
        for r in st.STATE_TABLE:
            key = (r['sel_a'], r['sel_b'])
            self.assertEqual(seen.setdefault(key, r['mode']), r['mode'], r['state'])

    def test_positions_are_monotonic(self):
        modes = [r['mode'] for r in st.STATE_TABLE if r['kind'] == 'position']
        self.assertEqual(modes, ['PUL', 'DIV2', 'DIV4'])
        for r in st.STATE_TABLE:
            if r['kind'] == 'travel':
                self.assertEqual(r['mode'], 'DIV2', 'travel passes the centre state only')

    def test_every_state_every_initial_state_every_delay_corner(self):
        for row in st.STATE_TABLE:
            for init in itertools.product((0, 1), repeat=2):
                for delays in st.delay_sets():
                    sim = st.run_mode('saw', row['sel_a'], row['sel_b'], list(init), delays)
                    msg = f"{row['state']} init={init} delays={delays}"
                    self.assertEqual(sim.violations, [], msg)
                    assert_mode(self, sim, row['mode'], msg)


class TestSubIgnoresPulseWidth(unittest.TestCase):
    def test_pw_extremes_do_not_stop_the_sub(self):
        d = st.delay_sets()[-1]
        for row in st.STATE_TABLE:
            if row['mode'] == 'PUL':
                continue
            for duty in (0, 0.01, 0.5, 0.99, 1):
                sim = st.run_mode('saw', row['sel_a'], row['sel_b'], [1, 0], d, pulse_duty=duty)
                assert_mode(self, sim, row['mode'], f"{row['state']} duty={duty}")

    def test_alternative_pulse_clock_stalls_at_extremes(self):
        d = st.delay_sets()[0]
        for sel_b, mode in ((1, 'DIV2'), (0, 'DIV4')):
            for duty in (0, 1):
                sim = st.run_mode('pulse', 1, sel_b, [1, 0], d, pulse_duty=duty)
                late = [t for t, _ in sim.trace.get('SUB_OUT', []) if t > sim.resets[SETTLE]]
                self.assertEqual(late, [], f'pulse clock keeps running at duty {duty}')
            sim = st.run_mode('pulse', 1, sel_b, [1, 0], d, pulse_duty=0.5)
            edges = [t for t, _ in sim.trace.get('SUB_OUT', []) if t > sim.resets[SETTLE]]
            self.assertGreater(len(edges), 3, mode)


class TestHardSync(unittest.TestCase):
    def test_each_counted_reset_advances_the_divider(self):
        resets, t = [], 1000
        for k in range(30):
            resets.append(t)
            t += (PERIOD if k % 3 else 4100)  # every third cycle truncated by sync
        d = st.delay_sets()[5]
        for sel_b, step in ((1, 1), (0, 2)):
            sim = st.run_mode('saw', 1, sel_b, [0, 1], d, resets=resets, saw_high=3000)
            out = samples(sim)
            for k in range(len(out) - step):
                self.assertEqual(out[k + step], 1 - out[k], out)


class TestTransitions(unittest.TestCase):
    def test_lever_sequences_with_bounce_never_leave_the_table(self):
        d = st.delay_sets()[-2]
        positions = {'PUL': (0, 1), 'C': (1, 1), 'M2': (1, 0)}
        for path in (('PUL', 'C', 'M2', 'C', 'PUL'), ('M2', 'C', 'PUL', 'C', 'M2'), ('C', 'M2', 'PUL')):
            a, b = positions[path[0]]
            sim = st.Sim(st.logic_netlist('saw'), d, [0, 0], {'SUB_A_DB': a, 'SUB_B_DB': b,
                                                                'SAW_LOGIC': 0, 'PULSE_LOGIC': 0})
            resets = [1000 + k * PERIOD for k in range(12 * len(path))]
            for r in resets:
                sim.drive(r, 'SAW_LOGIC', 1)
                sim.drive(r + 3000, 'SAW_LOGIC', 0)
                sim.drive(r + 1700, 'PULSE_LOGIC', 1)
                sim.drive(r + 6700, 'PULSE_LOGIC', 0)
            for i, name in enumerate(path[1:], 1):
                t0 = resets[12 * i] - 5000
                na, nb = positions[name]
                for k in range(3):  # bounce on the changing line(s)
                    if na != a:
                        sim.drive(t0 + 300 * k, 'SUB_A_DB', na if k % 2 == 0 else a)
                    if nb != b:
                        sim.drive(t0 + 300 * k, 'SUB_B_DB', nb if k % 2 == 0 else b)
                sim.drive(t0 + 1000, 'SUB_A_DB', na)
                sim.drive(t0 + 1000, 'SUB_B_DB', nb)
                a, b = na, nb
            sim.run_until(resets[-1] + PERIOD)
            self.assertEqual(sim.violations, [])
            for i, name in enumerate(path):
                block = resets[12 * i + 6: 12 * i + 12]
                out = [level_at(sim, 'SUB_OUT', r - 100) for r in block]
                if name == 'C':
                    self.assertTrue(all(out[k + 1] == 1 - out[k] for k in range(len(out) - 1)), (path, name, out))
                elif name == 'M2':
                    self.assertTrue(all(out[k + 2] == 1 - out[k] for k in range(len(out) - 2)), (path, name, out))
                else:
                    self.assertEqual(level_at(sim, 'SUB_OUT', block[0] + 4000), 1, (path, name))
                    self.assertEqual(level_at(sim, 'SUB_OUT', block[0] + 8000), 0, (path, name))


class TestEvidenceBinding(unittest.TestCase):
    def test_inventory_lines_and_identities(self):
        inv = json.loads((SKILLS / 'component-spec-audit/references/inventory.json').read_text())
        lines = {l['line_id']: l for l in inv['lines']}
        for line_id, maker, mpn, _ in st.LINES.values():
            self.assertIn(line_id, lines)
            self.assertEqual(lines[line_id]['manufacturer'], maker)
            if mpn and line_id != 'line-r-precision':
                self.assertEqual(lines[line_id]['mpn'], mpn)

    def pinout(self, bundle):
        facts = json.loads((SKILLS / bundle / 'facts.json').read_text())['facts']
        text = next(f['value'] for f in facts if f['fact_id'].endswith('-pinout'))
        return dict(re.findall(r'pin (\d+) ([^;]+?) ->', text))

    def test_flipflop_pins_follow_bundle(self):
        p = self.pinout('component-ti-sn74hc74dr')
        for unit, n in zip(st.FF_UNITS, (1, 2)):
            for role, pin in unit.items():
                name = {'CLR': f'{n}CLR', 'D': f'{n}D', 'CLK': f'{n}CLK', 'PRE': f'{n}PRE', 'Q': f'{n}Q', 'QN': f'{n}Q inverted'}[role]
                self.assertTrue(p[pin].startswith(name), (pin, p[pin], name))
        self.assertEqual((p['7'], p['14']), ('GND', 'VCC'))
        self.assertEqual((st.FLIPFLOP['7'], st.FLIPFLOP['14']), ('AGND', '+5V'))

    def test_nand_pins_follow_bundle(self):
        p = self.pinout('component-ti-sn74hc00dr')
        for n, (a, b, y) in enumerate(st.NAND_UNITS, 1):
            self.assertEqual((p[a], p[b], p[y]), (f'{n}A input', f'{n}B input', f'{n}Y NAND output'))
        self.assertEqual((st.NAND['7'], st.NAND['14']), ('AGND', '+5V'))

    def test_comparator_half_b_pins(self):
        p = self.pinout('component-ti-lm393bidr')
        self.assertEqual((p['5'], p['6'], p['7']), ('2IN+', '2IN-', '2OUT open collector'))
        changed = {c['pin']: c['to'] for c in st.CHANGED if c['part'].startswith('PULSE_CMP')}
        self.assertEqual(changed, {'5': 'SUB_THRESH', '6': 'SAW_RAW', '7': 'SAW_LOGIC'})

    def test_toggle_footprint_and_pair_order(self):
        text = (st.FOOTPRINTS / 'Toggle_Dailywell_2MS_T1B1M2.kicad_mod').read_text()
        pads = {n: float(x) for n, x in re.findall(r'\(pad "(\d)" thru_hole circle \(at ([-\d.]+) 0\)', text)}
        self.assertEqual(pads, {'3': -2.54, '2': 0.0, '1': 2.54})
        self.assertEqual(st.TOGGLE_PINS['2'], 'AGND')
        self.assertEqual([st.PAIR_PINS[k] for k in '123'], ['SUB_SEL_A', 'AGND', 'SUB_SEL_B'])
        self.assertEqual(st.PAIR_PINS['1'], st.TOGGLE_PINS['3'])
        self.assertEqual(st.PAIR_PINS['3'], st.TOGGLE_PINS['1'])

    def test_fixed_centres(self):
        lock = json.loads((ROOT / 'design/grid/placements.lock.json').read_text())['placements']
        by = {p['uid']: p for p in lock}
        for inst, x in (('O2', 31.5), ('O4', 65.5)):
            row = by.get(f'C:{inst}.SUB') or by[f'C:{inst}.OCT']
            self.assertEqual((row['x_mm'], row['y_mm']), (x, 185.0))


class TestBoundaries(unittest.TestCase):
    def test_no_sensitive_or_reference_net_is_touched(self):
        nets = {n for _, _, _, pins in st.PASSIVES for n in pins.values()}
        nets |= set(st.FLIPFLOP.values()) | set(st.NAND.values()) | {n for row in st.SCHMITT for n in row[:2]}
        nets |= {c['to'] for c in st.CHANGED}
        self.assertFalse(nets & set(st.UNTOUCHED_SENSITIVE))

    def test_joint_carries_only_static_lines(self):
        self.assertEqual(set(st.PAIR_PINS.values()), {'SUB_SEL_A', 'SUB_SEL_B', 'AGND'})
        audio = {'PULSE_LOGIC', 'SAW_RAW', 'SAW_LOGIC', 'SUB_OUT', 'SUB_SELECTED', 'PULSE_CLEAN'}
        self.assertFalse(set(st.PAIR_PINS.values()) & audio)

    def test_threshold_and_level_arithmetic(self):
        th = st.threshold_calc()
        self.assertAlmostEqual(th['saw_rising_threshold_V'], 2.5 + 2.5 * 50 / 1054.7, places=5)
        self.assertAlmostEqual(th['saw_falling_threshold_V'], 2.5 - 2.5 * 50 / 1050, places=5)
        lv = st.level_calc()['bound']
        self.assertEqual(lv['nominal_PUL_SCALED_V'], [-5.0, 5.0])

    def test_rail_and_area_deltas(self):
        rd = st.rail_delta('saw')['per_SUB_oscillator']
        self.assertEqual(rd['typical_mA']['+12V'], 0)
        self.assertEqual(rd['planning_mA']['-12V'], 0)
        self.assertAlmostEqual(rd['planning_mA']['+5V'], 3 * 0.5 + 2 * 0.5 + 5 / 4.7 + 0.03, places=5)
        a = st.area('saw')
        self.assertEqual(a['by_footprint'], {'SOIC-14_3.9x8.7mm_P1.27mm': 3, 'R0603': 9, 'C0603': 5})
        self.assertAlmostEqual(a['courtyard_mm2'], 3 * 7.4 * 9.63 + 9 * 3.28 * 1.82 + 5 * 3.28 * 1.92, places=3)
        b = st.area('pulse')
        self.assertEqual(b['by_footprint'], {'SOIC-14_3.9x8.7mm_P1.27mm': 2, 'R0603': 5, 'C0603': 4})


if __name__ == '__main__':
    unittest.main()
