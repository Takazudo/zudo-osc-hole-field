"""ST-06 SUB toggle specification for OSC2 and OSC4 (unvalidated draft proposal).

This module is the source of `design/stack/sub-toggle/spec.json`. It holds the
proposed netlist delta, the select-logic state table, the comparison netlist for
the rejected clock node, the rail and area deltas, and a gate-level model used by
the unit tests. Standard library only; no network, no KiCad.

  python3 scripts/stack/sub_toggle/sub_toggle.py          write spec.json
  python3 scripts/stack/sub_toggle/sub_toggle.py --check  fail on drift
"""
from pathlib import Path
import hashlib
import heapq
import itertools
import json
import re
import sys

ROOT = Path(__file__).resolve().parents[3]
SPEC = ROOT / 'design/stack/sub-toggle/spec.json'
FOOTPRINTS = ROOT / 'footprints/kicad/zudo-osc-hole-field.pretty'
INSTANCES = ('O2', 'O4')
LAUNCH_COMMIT = '78246cf004f179250e773ed8c67434199cec471a'

# Inputs read for this proposal. Hashes are recorded as data at the launch
# commit; later edits by the implementing task are expected and not asserted.
INPUTS = (
    'design/spec/modules/oscillator.py',
    'design/spec/modules/oscillator-work-note.md',
    'design/spec/modules/io_partition.py',
    'design/standard/electrical-standard.json',
    'design/grid/placements.lock.json',
    'project/osc-hole-field/workbench/layout/grid.json',
    'design/reports/current/oscillator.json',
    '.claude/skills/component-spec-audit/references/inventory.json',
    '.claude/skills/component-ti-sn74hc74dr/facts.json',
    '.claude/skills/component-ti-sn74hc00dr/facts.json',
    '.claude/skills/component-ti-sn74hc14dr/facts.json',
    '.claude/skills/component-ti-lm393bidr/facts.json',
    '.claude/skills/component-dailywell-2ms3t1b1m2qes/facts.json',
    '.claude/skills/component-dailywell-2ms3t1b1m2qes/pin-map.json',
    '.claude/skills/component-ti-opa4196idr/facts.json',
    '.claude/skills/component-alfa-rpar-as3340d/facts.json',
    'footprints/kicad/zudo-osc-hole-field.pretty/SOIC-14_3.9x8.7mm_P1.27mm.kicad_mod',
    'footprints/kicad/zudo-osc-hole-field.pretty/R0603.kicad_mod',
    'footprints/kicad/zudo-osc-hole-field.pretty/C0603.kicad_mod',
    'footprints/kicad/zudo-osc-hole-field.pretty/Toggle_Dailywell_2MS_T1B1M2.kicad_mod',
)
# ST-02 output read from the wave-1 worktree (not on this branch).
EXTERNAL_INPUTS = {
    'wave-1:design/stack/geometry/stack-candidate.json':
        'pair P-K-SUB-O2/O4 planning pin map [SUB_SEL_A, AGND, SUB_SEL_B]; P-to-K order signal-AGND-signal',
}

# ---------------------------------------------------------------- inventory
LINES = {
    'flipflop': ('line-flipflop', 'Texas Instruments', 'SN74HC74DR', 'SOIC-14_3.9x8.7mm_P1.27mm'),
    'nand': ('line-nand', 'Texas Instruments', 'SN74HC00DR', 'SOIC-14_3.9x8.7mm_P1.27mm'),
    'schmitt': ('line-schmitt', 'Texas Instruments', 'SN74HC14DR', 'SOIC-14_3.9x8.7mm_P1.27mm'),
    'comparator': ('line-comparator', 'Texas Instruments', 'LM393BIDR', 'SOIC-8_3.9x4.9mm_P1.27mm'),
    'toggle': ('line-2ms3', 'Dailywell', '2MS3T1B1M2QES', 'Toggle_Dailywell_2MS_T1B1M2'),
    'r_contact_pullup': ('line-contact-pullup-r', 'Yageo', 'RC0603FR-0710KL', 'R0603'),
    'r_contact_debounce': ('line-contact-debounce-r', 'Yageo', 'RC0603FR-071KL', 'R0603'),
    'c_bypass': ('line-c-bypass', 'Murata', 'GRM188R71H104KA93D', 'C0603'),
    'r_precision_100k': ('line-r-precision', 'Yageo', 'RT0603BRD07100KL', 'R0603'),
    # Same series representative, other value: exact MPN unresolved, as for the
    # existing PUL_PULL 4.7 kohm and the oscillator's other non-100k resistors.
    'r_precision_family': ('line-r-precision', 'Yageo', '', 'R0603'),
}

# ------------------------------------------------------------ added parts (K)
# (key, line, value, {pin: net}). Pin numbers are the evidence-bundle pinouts.
FLIPFLOP = {'1': '+5V', '2': 'SUB_D1', '3': 'SUB_CLK', '4': '+5V', '5': 'SUB_Q1', '6': None, '7': 'AGND',
            '8': 'SUB_Q2_N', '9': 'SUB_Q2', '10': 'SUB_PUL_OFF', '11': 'SUB_CLK2', '12': 'SUB_Q2_N',
            '13': '+5V', '14': '+5V'}
NAND = {'1': 'PULSE_CLEAN', '2': 'SUB_PUL_ON', '3': 'SUB_PUL_TERM',
        '4': 'SUB_PUL_TERM', '5': 'SUB_Q2', '6': 'SUB_OUT', '7': 'AGND',
        '9': 'SUB_CLK_GATE', '10': 'SUB_Q1', '8': 'SUB_CLK2',
        '12': 'SUB_Q1', '13': 'SUB_DIV4_ON', '11': 'SUB_D1', '14': '+5V'}
NAND_UNITS = (('1', '2', '3'), ('4', '5', '6'), ('9', '10', '8'), ('12', '13', '11'))
FF_UNITS = ({'CLR': '1', 'D': '2', 'CLK': '3', 'PRE': '4', 'Q': '5', 'QN': '6'},
            {'CLR': '13', 'D': '12', 'CLK': '11', 'PRE': '10', 'Q': '9', 'QN': '8'})
# Logical Schmitt sections (input, output). io_partition.refine packs them with
# the oscillator's existing SYNC Schmitt (1 of 6 used) into whole SN74HC14DR
# packages; the physical unit number is the packer's, not part of this spec.
SCHMITT = (
    ('SUB_A_DB', 'SUB_PUL_ON', 'select A (PUL throw) debounced contact -> high when PUL'),
    ('SUB_B_DB', 'SUB_DIV4_ON', 'select B (-2 throw) debounced contact -> high when -2'),
    ('SUB_PUL_ON', 'SUB_PUL_OFF', 'complement: low when PUL; drives 2PRE'),
    ('SAW_LOGIC', 'SUB_CLK_GATE', 'clock chain stage 1: falls at the core reset'),
    ('SUB_CLK_GATE', 'SUB_CLK', 'clock chain stage 2: rises at the core reset; clocks FF1'),
    ('PULSE_LOGIC', 'PULSE_LOGIC_N', 'pulse squaring stage 1'),
    ('PULSE_LOGIC_N', 'PULSE_CLEAN', 'pulse squaring stage 2: same polarity as PULSE_LOGIC'),
)
PASSIVES = (
    ('R_SUB_A_PULL', 'r_contact_pullup', '10 kΩ', {'1': '+5V', '2': 'SUB_SEL_A'}),
    ('R_SUB_A_SER', 'r_contact_debounce', '1 kΩ', {'1': 'SUB_SEL_A', '2': 'SUB_A_DB'}),
    ('C_SUB_A_DB', 'c_bypass', '100 nF', {'1': 'SUB_A_DB', '2': 'AGND'}),
    ('R_SUB_B_PULL', 'r_contact_pullup', '10 kΩ', {'1': '+5V', '2': 'SUB_SEL_B'}),
    ('R_SUB_B_SER', 'r_contact_debounce', '1 kΩ', {'1': 'SUB_SEL_B', '2': 'SUB_B_DB'}),
    ('C_SUB_B_DB', 'c_bypass', '100 nF', {'1': 'SUB_B_DB', '2': 'AGND'}),
    ('R_SAW_PULL', 'r_precision_family', '4.7 kΩ', {'1': '+5V', '2': 'SAW_LOGIC'}),
    ('R_SUB_TH_TOP', 'r_precision_100k', '100 kΩ', {'1': '+5V', '2': 'SUB_THRESH'}),
    ('R_SUB_TH_BOT', 'r_precision_100k', '100 kΩ', {'1': 'SUB_THRESH', '2': 'AGND'}),
    ('R_SUB_TH_HYS', 'r_precision_family', '1 MΩ', {'1': 'SAW_LOGIC', '2': 'SUB_THRESH'}),
    ('R_SUB_ISO', 'r_precision_family', '4.7 kΩ', {'1': 'SUB_OUT', '2': 'SUB_SELECTED'}),
    ('C_DEC_SUB_FF', 'c_bypass', '100 nF', {'1': '+5V', '2': 'AGND'}),
    ('C_DEC_SUB_NAND', 'c_bypass', '100 nF', {'1': '+5V', '2': 'AGND'}),
    ('C_DEC_SUB_SCHMITT', 'c_bypass', '100 nF', {'1': '+5V', '2': 'AGND'}),
)
# Existing parts whose connections change in the SUB variant only.
CHANGED = (
    {'part': 'PULSE_CMP (LM393BIDR, existing)', 'pin': '5', 'name': '2IN+', 'from': 'AGND', 'to': 'SUB_THRESH'},
    {'part': 'PULSE_CMP (LM393BIDR, existing)', 'pin': '6', 'name': '2IN-', 'from': '+5V', 'to': 'SAW_RAW'},
    {'part': 'PULSE_CMP (LM393BIDR, existing)', 'pin': '7', 'name': '2OUT', 'from': None, 'to': 'SAW_LOGIC'},
    {'part': 'PUL_SCALE (OPA4196IDR section, existing)', 'pin': 'IN+', 'name': 'non-inverting input',
     'from': 'PULSE_LOGIC', 'to': 'SUB_SELECTED'},
    {'part': 'R_OCT_SER (existing)', 'pin': '1', 'name': 'selector side', 'from': 'OCT_SELECTED', 'to': 'AGND'},
)
REMOVED = (
    {'part': 'OCT_SELECTOR', 'mpn': 'SRBV160803', 'region': 'selector (O2/O4 adapter)',
     'reason': 'owner decision DS-02; the adapter board and its GH7 harnesses are retired by the stack plan'},
)
KEPT_UNCHANGED = ('R_OCT_SER (1 kΩ, pin 2 OCT_FILTER)', 'R_OCT_PD (10 MΩ)', 'C_OCT_FILTER (100 nF)',
                  'OCT_RECEIVER (precision follower)', 'PITCH_OCT (100 kΩ OCT_CV -> EXPO_SUM)',
                  'PUL_DIV_TOP/BOT, PULSE_CMP half A, REF25 divider, PUL_PULL 4.7 kΩ',
                  'PUL_RF/PUL_RREF 100 kΩ and the PUL output cell')
UNTOUCHED_SENSITIVE = ('TIMING_CAP', 'EXPO_SUM', 'SCALE_PIN', 'SCALE1', 'SCALE2', 'LINEAR_REF', 'HF_PIN',
                       'LOCAL_REF5', 'LOCAL_REFN5', 'REF25', 'REF4', 'OSC_REF5', 'OSC_REFN5',
                       'OSC_GATE_REF', 'OSC_OCT0', 'OSC_OCT1', 'OSC_OCT2', 'OSC_OCT3', 'OSC_OCT4', 'OSC_OCT5')

# --------------------------------------------------------------- P-side parts
TOGGLE_PINS = {'3': 'SUB_SEL_A', '2': 'AGND', '1': 'SUB_SEL_B'}
PAIR_PINS = {'1': 'SUB_SEL_A', '2': 'AGND', '3': 'SUB_SEL_B'}
POSITIONS = ('PUL', '-1', '-2')  # grid order: pin-3 throw, centre, pin-1 throw (as SYNC: SOFT, OFF, HARD)

# ------------------------------------------------------------- state table
# Contact level at the select line: 0 = shorted to AGND by the toggle, 1 = open
# (10 kohm pull-up on K). u/w are the Schmitt outputs; ubar drives 2PRE.
MODES = {'PUL': 'PULSE_LOGIC', 'DIV2': 'square at f/2', 'DIV4': 'square at f/4'}
STATE_TABLE = (
    {'state': 'PUL position (pin-3 throw closed)', 'kind': 'position', 'sel_a': 0, 'sel_b': 1, 'mode': 'PUL'},
    {'state': '-1 position (centre, both open)', 'kind': 'position', 'sel_a': 1, 'sel_b': 1, 'mode': 'DIV2'},
    {'state': '-2 position (pin-1 throw closed)', 'kind': 'position', 'sel_a': 1, 'sel_b': 0, 'mode': 'DIV4'},
    {'state': 'travel between PUL and -1 (break before make)', 'kind': 'travel', 'sel_a': 1, 'sel_b': 1, 'mode': 'DIV2'},
    {'state': 'travel between -1 and -2 (break before make)', 'kind': 'travel', 'sel_a': 1, 'sel_b': 1, 'mode': 'DIV2'},
    {'state': 'both lines low: shorted harness, or the first ~0.4-1.1 ms after +5 V rises while both debounce capacitors charge',
     'kind': 'fault/power-up', 'sel_a': 0, 'sel_b': 0, 'mode': 'PUL'},
    {'state': 'joint unmated or toggle missing (pull-ups only)', 'kind': 'fault', 'sel_a': 1, 'sel_b': 1, 'mode': 'DIV2'},
)


def select_signals(sel_a, sel_b):
    """Static Schmitt-output levels for given select-line levels (after debounce)."""
    u = 1 - sel_a
    w = 1 - sel_b
    return {'SUB_PUL_ON': u, 'SUB_DIV4_ON': w, 'SUB_PUL_OFF': 1 - u}


# ----------------------------------------------------- comparison netlist
# Alternative clock node: PULSE_LOGIC. PULSE_CMP half B stays tied off, the saw
# threshold network is absent and the clock chain shares the pulse squaring
# stages. Five Schmitt sections, so it fits the existing package.
ALT_PULSE = {
    'schmitt': (('SUB_A_DB', 'SUB_PUL_ON'), ('SUB_B_DB', 'SUB_DIV4_ON'), ('SUB_PUL_ON', 'SUB_PUL_OFF'),
                ('PULSE_LOGIC', 'PULSE_LOGIC_N'), ('PULSE_LOGIC_N', 'PULSE_CLEAN')),
    'nand_inputs': {'SUB_CLK2': ('PULSE_LOGIC_N', 'SUB_Q1')},
    'ff1_clk': 'PULSE_CLEAN',
    'removed_parts': ('R_SAW_PULL', 'R_SUB_TH_TOP', 'R_SUB_TH_BOT', 'R_SUB_TH_HYS', 'C_DEC_SUB_SCHMITT'),
    'pulse_cmp_half_b': 'unchanged tie-off: pin 5 AGND, pin 6 +5V, pin 7 NC',
}


# ===================================================================== model
def logic_netlist(variant='saw'):
    """Gate list derived from the pin tables above (single source of truth)."""
    gates = []
    schmitt = SCHMITT if variant == 'saw' else ALT_PULSE['schmitt']
    for row in schmitt:
        gates.append({'type': 'INV', 'in': (row[0],), 'out': row[1]})
    for a, b, y in NAND_UNITS:
        ins = (NAND[a], NAND[b])
        if variant == 'pulse' and NAND[y] in ALT_PULSE['nand_inputs']:
            ins = ALT_PULSE['nand_inputs'][NAND[y]]
        gates.append({'type': 'NAND', 'in': ins, 'out': NAND[y]})
    ffs = []
    for unit in FF_UNITS:
        row = {k: FLIPFLOP[p] for k, p in unit.items()}
        if variant == 'pulse' and row['CLK'] == 'SUB_CLK':
            row['CLK'] = ALT_PULSE['ff1_clk']
        ffs.append(row)
    return {'gates': gates, 'flipflops': ffs}


class Sim:
    """Event-driven gate model with transport delays, so any glitch propagates.

    Flip-flop: rising CLK samples D as it was strictly before the edge; PRE low
    forces Q=1; CLR low forces Q=0. A D change within SETUP ns before an edge is
    recorded as a violation.
    """
    SETUP = 10

    def __init__(self, netlist, delays, init, levels):
        self.gates, self.ffs = netlist['gates'], netlist['flipflops']
        for n, g in enumerate(self.gates):
            g['idx'] = n
        self.delays = delays
        self.v = dict(levels)
        self.v.update({'+5V': 1, 'AGND': 0, None: 0})
        for n, ff in enumerate(self.ffs):
            q = init[n]
            if ff['Q']:
                self.v[ff['Q']] = q
            if ff['QN']:
                self.v[ff['QN']] = 1 - q
        self.state = list(init)
        self.fan = {}
        for g in self.gates:
            for i in g['in']:
                self.fan.setdefault(i, []).append(('g', g))
        for n, ff in enumerate(self.ffs):
            for pin in ('CLK', 'D', 'PRE', 'CLR'):
                self.fan.setdefault(ff[pin], []).append(('f', n))
        self.q = []
        self.seq = itertools.count()
        self.t = 0
        self.trace = {}
        self.last_change = {}
        self.violations = []
        # settle combinational logic from the initial levels
        for _ in range(len(self.gates) + 2):
            for g in self.gates:
                self.v[g['out']] = self.eval(g)
        for n, ff in enumerate(self.ffs):
            self.async_force(n, 0, immediate=True)
        for _ in range(len(self.gates) + 2):
            for g in self.gates:
                self.v[g['out']] = self.eval(g)
        self.initial = dict(self.v)

    def level(self, net, t):
        value = self.initial.get(net, 0)
        for when, val in self.trace.get(net, []):
            if when > t:
                break
            value = val
        return value

    def eval(self, g):
        x = [self.v.get(i, 0) for i in g['in']]
        return 1 - x[0] if g['type'] == 'INV' else 1 - (x[0] & x[1])

    def schedule(self, t, net, value):
        heapq.heappush(self.q, (t, next(self.seq), net, value))

    def async_force(self, n, t, immediate=False):
        ff = self.ffs[n]
        pre, clr = self.v.get(ff['PRE'], 1), self.v.get(ff['CLR'], 1)
        if pre and clr:
            return
        q = 1 if not pre else 0
        if not pre and not clr:
            q = 1  # not used by this design
        self.state[n] = q
        if immediate:
            self.v[ff['Q']] = q
            if ff['QN']:
                self.v[ff['QN']] = 1 - q
        else:
            d = self.delays['pre']
            self.schedule(t + d, ff['Q'], q)
            if ff['QN']:
                self.schedule(t + d, ff['QN'], 1 - q)

    def drive(self, t, net, value):
        self.schedule(t, net, value)

    def run_until(self, t_end):
        while self.q and self.q[0][0] <= t_end:
            t = self.q[0][0]
            batch = []
            while self.q and self.q[0][0] == t:
                batch.append(heapq.heappop(self.q))
            old = dict(self.v)
            changed = []
            for _, _, net, value in batch:
                if self.v.get(net) != value:
                    self.v[net] = value
                    changed.append(net)
            for net in changed:
                self.trace.setdefault(net, []).append((t, self.v[net]))
                self.last_change[net] = t
            touched_g, touched_f = [], set()
            for net in changed:
                for kind, obj in self.fan.get(net, ()):
                    if kind == 'g':
                        touched_g.append(obj)
                    else:
                        touched_f.add(obj)
            for g in {g['idx']: g for g in touched_g}.values():
                spread = self.delays[g['type']]
                self.schedule(t + spread[g['idx'] % len(spread)], g['out'], self.eval(g))
            for n in sorted(touched_f):
                ff = self.ffs[n]
                pre, clr = self.v.get(ff['PRE'], 1), self.v.get(ff['CLR'], 1)
                if not (pre and clr):
                    self.async_force(n, t)
                    continue
                if ff['CLK'] in changed and old.get(ff['CLK']) == 0 and self.v[ff['CLK']] == 1:
                    d_old = old.get(ff['D'], 0)
                    last = self.last_change.get(ff['D'], -10**9)
                    if ff['D'] in changed or t - last < self.SETUP:
                        self.violations.append((t, n))
                    self.state[n] = d_old
                    self.schedule(t + self.delays['ff'], ff['Q'], d_old)
                    if ff['QN']:
                        self.schedule(t + self.delays['ff'], ff['QN'], 1 - d_old)
        self.t = t_end

    def edges(self, net, rising=True, after=0):
        return [t for t, val in self.trace.get(net, []) if val == (1 if rising else 0) and t >= after]


def delay_sets():
    """Corner sets plus per-instance spreads. Max values: HC14 31 ns, HC74 CLK 44 ns
    and PRE 58 ns (retained rows at VCC 4.5 V); HC00 has no retained delay, so a
    wide 1..60 ns bracket is used."""
    out = []
    for inv, nand, ff, pre in itertools.product((1, 31), (1, 60), (1, 44), (1, 58)):
        out.append({'INV': (inv,), 'NAND': (nand,), 'ff': ff, 'pre': pre})
    out.append({'INV': (1, 31, 7, 19, 3, 29, 11), 'NAND': (60, 1, 33, 5), 'ff': 44, 'pre': 1})
    out.append({'INV': (31, 1, 23, 2, 30, 5, 17), 'NAND': (1, 60, 4, 41), 'ff': 1, 'pre': 58})
    return out


def run_mode(variant, sel_a, sel_b, init, delays, period=10000, saw_high=3000, pulse_duty=0.5,
             cycles=24, resets=None, pulse_phase=1700):
    """Drive saw-logic resets and an independent PULSE_LOGIC; return the simulator."""
    levels = {'SUB_A_DB': sel_a, 'SUB_B_DB': sel_b, 'SAW_LOGIC': 0, 'PULSE_LOGIC': 0}
    sim = Sim(logic_netlist(variant), delays, init, levels)
    resets = resets if resets is not None else [1000 + k * period for k in range(cycles)]
    for k, t in enumerate(resets):
        nxt = resets[k + 1] if k + 1 < len(resets) else t + period
        sim.drive(t, 'SAW_LOGIC', 1)
        if t + saw_high < nxt:
            sim.drive(t + saw_high, 'SAW_LOGIC', 0)
    end = resets[-1] + 2 * period
    if 0 < pulse_duty < 1:
        t = pulse_phase
        while t < end:
            sim.drive(t, 'PULSE_LOGIC', 1)
            sim.drive(t + int(period * pulse_duty), 'PULSE_LOGIC', 0)
            t += period
    elif pulse_duty >= 1:
        sim.drive(pulse_phase, 'PULSE_LOGIC', 1)
    sim.run_until(end)
    sim.resets = resets
    sim.end = end
    return sim


# =============================================================== analog calc
V5 = 5.0


def threshold_calc():
    top, bot, hys, pull = 100e3, 100e3, 1e6, 4.7e3
    thev_v, thev_r = V5 * bot / (top + bot), top * bot / (top + bot)
    rising = thev_v + (V5 - thev_v) * thev_r / (thev_r + hys + pull)  # SAW_LOGIC high (saw below)
    falling = thev_v * (1 - thev_r / (thev_r + hys))                   # SAW_LOGIC low (ideal 0 V)
    return {'thevenin_V': round(thev_v, 6), 'thevenin_ohm': round(thev_r, 3),
            'saw_rising_threshold_V': round(rising, 6), 'saw_falling_threshold_V': round(falling, 6),
            'hysteresis_V': round(rising - falling, 6),
            'conditions': 'Ideal: +5V = 5.000 V, comparator VOL = 0 V, output leakage 0, resistors at nominal. '
                          'Thresholds scale with the +5 V rail; LM393B offset (<=4.0 mV full temperature, '
                          'fact-comparator-input-offset-voltage) and VOL (not retained) shift them.'}


def debounce_calc():
    import math
    r_pull, r_ser, c = 10e3, 1e3, 100e-9
    tau_open, tau_close = (r_pull + r_ser) * c, r_ser * c
    vtp, vtn = (1.55, 3.13), (0.9, 2.45)  # HC14 VT+ / VT- rows at VCC 4.5 V (retained)
    t_open = [round(-tau_open * math.log(1 - v / V5) * 1e3, 4) for v in vtp]
    t_close = [round(-tau_close * math.log(v / V5) * 1e3, 4) for v in vtn]
    return {'tau_open_ms': round(tau_open * 1e3, 4), 'tau_close_ms': round(tau_close * 1e3, 4),
            'open_to_switch_ms_range': t_open, 'close_to_switch_ms_range': t_close,
            'contact_current_mA': round(V5 / r_pull * 1e3, 4),
            'conditions': 'Single-pole RC into the Schmitt input; HC14 threshold rows are retained at VCC 4.5 V '
                          '(fact-schmitt-schmitt-high/low) and applied to a 5.0 V swing as an indicative bound. '
                          'Contact bounce duration of the toggle is not retained.'}


def level_calc():
    """PUL_SCALED = 2*V(in) - V(LOCAL_REF5): PUL_SCALE is non-inverting with
    PUL_RF 100k (output->sum) and PUL_RREF 100k (LOCAL_REF5->sum)."""
    ref = 5.0
    return {'transfer': 'PUL_SCALED = 2*V(PUL_SCALE IN+) - V(LOCAL_REF5)',
            'present_input': {'node': 'PULSE_LOGIC', 'high': 'V(+5V) via PUL_PULL 4.7 kΩ (source 4.7 kΩ)',
                              'low': 'LM393B VOL at ~1.06 mA sink (value not retained)'},
            'proposed_input': {'node': 'SUB_SELECTED', 'high': 'SN74HC00 VOH at ~0 load via R_SUB_ISO 4.7 kΩ',
                               'low': 'SN74HC00 VOL at ~0 load via R_SUB_ISO 4.7 kΩ',
                               'source_ohm': '4.7 kΩ + SN74HC00 output resistance in both states'},
            'bound': {'input_V': [0.0, 'V(+5V)'], 'PUL_SCALED_V': [-ref, 2 * V5 - ref],
                      'nominal_PUL_SCALED_V': [2 * 0.0 - ref, 2 * V5 - ref]},
            'argument': 'A CMOS output with no DC load stays between its own GND and VCC pins, here AGND and '
                        '+5V, as the present open-collector-plus-pull-up node does. Both input sets therefore '
                        'lie in [0, V(+5V)] and PUL_SCALED in [-V(LOCAL_REF5), 2 V(+5V) - V(LOCAL_REF5)], '
                        'nominally -5 to +5 V, the audio_nominal_V range of the electrical standard. The low '
                        'level moves towards -5 V by 2*(VOL_LM393 - VOL_HC00); exact VOL/VOH rows are an '
                        'evidence need.',
            'partial_power': 'With ±12 V absent and +5 V present, current into the unpowered PUL_SCALE input '
                             'is limited by 4.7 kΩ to <= V(+5V)/4.7 kΩ = 1.064 mA, the same path the present '
                             'PUL_PULL forms, against the retained 10 mA input-current absolute maximum '
                             '(fact-op-audio-input-absolute).'}


# ============================================================ loads / area
def courtyard_area(name):
    text = (FOOTPRINTS / f'{name}.kicad_mod').read_text()
    pts = re.findall(r'\(start ([-\d.]+) ([-\d.]+)\) \(end ([-\d.]+) ([-\d.]+)\) \(layer "?F\.CrtYd"?\)', text)
    xs = [float(v) for p in pts for v in (p[0], p[2])]
    ys = [float(v) for p in pts for v in (p[1], p[3])]
    return round((max(xs) - min(xs)) * (max(ys) - min(ys)), 4), [round(max(xs) - min(xs), 3), round(max(ys) - min(ys), 3)]


def added_parts(variant='saw'):
    rows = [('U_SUB_FF', 'flipflop'), ('U_SUB_NAND', 'nand')]
    schmitt = SCHMITT if variant == 'saw' else ALT_PULSE['schmitt']
    existing_spare = 5
    extra_schmitt_packages = -(-max(0, len(schmitt) - existing_spare) // 6)
    rows += [(f'U_SUB_SCHMITT{n + 1}', 'schmitt') for n in range(extra_schmitt_packages)]
    for key, line, _, _ in PASSIVES:
        if variant == 'pulse' and key in ALT_PULSE['removed_parts']:
            continue
        rows.append((key, line))
    return rows, len(schmitt), extra_schmitt_packages


def area(variant='saw'):
    rows, _, _ = added_parts(variant)
    total, counts = 0.0, {}
    for _, line in rows:
        fp = LINES[line][3]
        a, _ = courtyard_area(fp)
        total += a
        counts[fp] = counts.get(fp, 0) + 1
    return {'parts': len(rows), 'by_footprint': counts, 'courtyard_mm2': round(total, 4)}


def rail_delta(variant='saw'):
    rows, n_schmitt, extra = added_parts(variant)
    keys = {k for k, _ in rows}
    items = []

    def add(load, count, typ, plan, basis):
        items.append({'load': load, 'count': count, 'typical_unit_mA': typ, 'planning_unit_mA': plan, 'basis': basis})
    hc = 2 + extra
    add('SN74HC74DR, SN74HC00DR' + (', added SN74HC14DR' if extra else '') + ' packages', hc,
        {'+12V': 0, '-12V': 0, '+5V': 0.2}, {'+12V': 0, '-12V': 0, '+5V': 0.5},
        'Per-package planning reserve used for HC logic in the envelope worksheet (0.2 typical / 0.5 planning); '
        'fact-flipflop-quiescent-table-max 40 µA and fact-schmitt-quiescent-table-max 20 µA at VCC 6 V are static '
        'only. Not a guaranteed maximum.')
    add('Contact pull-ups 10 kΩ (one closed at an end position, both in the fault/power-up row)', 2,
        {'+12V': 0, '-12V': 0, '+5V': 0.25}, {'+12V': 0, '-12V': 0, '+5V': 0.5},
        'V(+5V)/10 kΩ = 0.5 mA per closed contact; envelope control-contact convention.')
    if 'R_SAW_PULL' in keys:
        add('Saw comparator pull-up 4.7 kΩ', 1, {'+12V': 0, '-12V': 0, '+5V': 0.5},
            {'+12V': 0, '-12V': 0, '+5V': round(5 / 4.7, 6)},
            'Envelope comparator pull-up convention: 0.5 typical, 5 V/4.7 kΩ planning (output low).')
        add('Saw threshold divider 2 × 100 kΩ and 1 MΩ hysteresis', 1, {'+12V': 0, '-12V': 0, '+5V': 0.025},
            {'+12V': 0, '-12V': 0, '+5V': 0.03}, '5 V / 200 kΩ = 0.025 mA plus <= 5 µA through 1 MΩ.')
    add('LM393BIDR half B activated', 0, {'+12V': 0, '-12V': 0, '+5V': 0}, {'+12V': 0, '-12V': 0, '+5V': 0},
        'Whole-package allowance (0.6 typical / 1 planning on +12 V) already counts both halves; no delta.')
    typ = {r: round(sum(i['count'] * i['typical_unit_mA'][r] for i in items), 6) for r in ('+12V', '-12V', '+5V')}
    plan = {r: round(sum(i['count'] * i['planning_unit_mA'][r] for i in items), 6) for r in ('+12V', '-12V', '+5V')}
    return {'per_SUB_oscillator': {'typical_mA': typ, 'planning_mA': plan},
            'ledger_total_two_oscillators': {'typical_mA': {r: round(2 * v, 6) for r, v in typ.items()},
                                             'planning_mA': {r: round(2 * v, 6) for r, v in plan.items()}},
            'items': items, 'schmitt_sections': n_schmitt, 'added_schmitt_packages': extra,
            'guaranteed_maximum': None,
            'status': 'Planning deltas only; dynamic switching at audio rates (C·V·f below 0.01 mA for 50 pF '
                      'nodes at 20 kHz) is inside the package reserve. Measured current NOT RUN.'}


# ================================================================= the spec
def sha(path):
    return hashlib.sha256((ROOT / path).read_bytes()).hexdigest()


def pinmap(pins):
    return {k: pins[k] for k in sorted(pins, key=lambda p: (len(p), p))}


def build():
    th = threshold_calc()
    spec = {
        'schema_version': 1,
        'task': 'osc-stack-20261114/ST-06@' + LAUNCH_COMMIT,
        'status': 'PROPOSAL - unvalidated draft specification; no schematic, board or lock is changed',
        'provenance': {'launch_commit': LAUNCH_COMMIT,
                       'inputs_sha256_at_launch': {p: sha(p) for p in INPUTS},
                       'external_inputs': EXTERNAL_INPUTS,
                       'generator': 'scripts/stack/sub_toggle/sub_toggle.py'},
        'scope': {'instances': list(INSTANCES), 'board_core': 'K, OSC2 and OSC4 cores',
                  'board_control': 'P, control tabs at C:O2 and C:O4 centres',
                  'unchanged_instances': ['O1', 'O3', 'O5']},
        'decision_state': {
            'item_1_clock_node': 'PROPOSED: SAW_LOGIC from LM393 half B; the design authority decides',
            'items_2_to_8': 'PROPOSED inside DS-02; no pitch, timing or reference node changes',
            'needs_design': [],
        },
        'clock_node': {
            'proposed': 'saw',
            'saw': {'node': 'SAW_LOGIC', 'source': 'PULSE_CMP half B (LM393BIDR pins 5/6/7), today tied off',
                    'inputs': {'2IN+ (pin 5)': 'SUB_THRESH', '2IN- (pin 6)': 'SAW_RAW'},
                    'edge': 'SAW_LOGIC rises when SAW_RAW falls below the lower threshold, i.e. at the core '
                            'reset; FF1 counts that edge',
                    'threshold': th},
            'pulse': {'node': 'PULSE_LOGIC', 'netlist': ALT_PULSE},
        },
        'divider': {
            'part': 'SN74HC74DR (line-flipflop), one per SUB oscillator',
            'ff1': 'D1 = NAND(Q1, SUB_DIV4_ON): toggles in -2, settles to Q1=1 otherwise; CLK1 = SUB_CLK; '
                   '1PRE and 1CLR tied to +5V',
            'ff2': 'D2 = 2Q-bar; CLK2 = NAND(SUB_CLK_GATE, Q1); 2PRE = SUB_PUL_OFF (holds Q2=1 in PUL); 2CLR tied to +5V',
            'power_up': 'No reset network. All four (Q1, Q2) states lie on the count cycle; Q1 reaches 1 within '
                        'one reset in PUL and -1, Q2 is preset asynchronously in PUL. During the first '
                        '~0.4-1.1 ms both debounce nodes are low, which the table maps to PUL.',
            'sync': 'The divider is not reset by SYNC. It counts core resets, including hard-sync resets once '
                    'the saw has passed the upper threshold; its phase relative to the sync master is one of 2 '
                    'or 4 and stays fixed while sync persists.',
            'race_freedom': 'SUB_CLK_GATE is upstream of SUB_CLK in the Schmitt chain, so it is low before FF1 '
                            'can change Q1; CLK2 = NAND(SUB_CLK_GATE, Q1) therefore has one rising edge per '
                            'counted reset for any gate delays. Proven by the unit test over delay corners.',
            'unused': {'1Q-bar (pin 6)': 'no connect (output)', 'inputs': 'none unused',
                       'rule': 'No unused-input rule is retained in the bundles; the project convention '
                               '(envelope.finish_envelope, io_partition.spare) is used for the added Schmitt '
                               'package: input AGND, output no-connect.'},
            'bypass': '100 nF GRM188R71H104KA93D from pin 14 (+5V) to AGND per package, as for every IC rail',
            'pins': pinmap(FLIPFLOP),
        },
        'gating': {
            'nand_part': 'SN74HC00DR (line-nand)', 'nand_pins': pinmap(NAND),
            'nand_units': [{'A': NAND[a], 'B': NAND[b], 'Y': NAND[y], 'pins': [a, b, y]} for a, b, y in NAND_UNITS],
            'schmitt_part': 'SN74HC14DR (line-schmitt)',
            'schmitt_sections': [{'in': a, 'out': z, 'role': r} for a, z, r in SCHMITT],
            'schmitt_packing': 'Seven sections: io_partition.refine fills the five spare sections of the existing '
                               'SYNC SN74HC14DR and adds one package with 2 used and 4 grounded spare sections.',
            'output': 'SUB_OUT = NAND(NAND(PULSE_CLEAN, SUB_PUL_ON), Q2) -> R_SUB_ISO 4.7 kΩ -> SUB_SELECTED -> PUL_SCALE IN+',
            'select_conditioning': 'Each select line uses the switch_button_input topology (10 kΩ pull-up, 1 kΩ, '
                                   '100 nF, Schmitt) but placed in the oscillator core on K; the contact lines '
                                   'cross the joint, the logic does not.',
        },
        'state_table': [dict(r, **select_signals(r['sel_a'], r['sel_b']), output=MODES[r['mode']])
                        for r in STATE_TABLE],
        'level': level_calc(),
        'debounce': debounce_calc(),
        'octave_input': {
            'proposal': 'R_OCT_SER pin 1 to AGND; OCT_SELECTOR removed; R_OCT_SER, R_OCT_PD, C_OCT_FILTER, '
                        'OCT_RECEIVER and PITCH_OCT stay. OCT_CV = receiver(0 V) = zero octaves.',
            'reference_effect': 'OSC_OCT0..5 lose the O2/O4 selector branches (owner decision DS-02) and gain '
                                'nothing; no reference value, buffer or ladder element changes.',
            'alternatives': [
                {'option': 'R_OCT_SER pin 1 to OSC_OCT2 (0 V tap)', 'state': 'NEEDS_DESIGN if chosen',
                 'reason': 'adds a fixed 1 kΩ/100 nF/10 MΩ branch per SUB oscillator to a reference node; keeps the '
                           'same calibrated zero as O1/O3/O5'},
                {'option': 'delete OCT chain and PITCH_OCT', 'state': 'NEEDS_DESIGN if chosen',
                 'reason': 'removes an input from the pitch sum EXPO_SUM'},
                {'option': 'leave OCT_SELECTED open on the 10 MΩ pull-down', 'state': 'not proposed',
                 'reason': 'high-impedance 10 MΩ node; an unconnected 1 kΩ pin needs an ERC no-connect'}],
        },
        'parts': {
            'added_K': [{'key': 'U_SUB_FF', 'line': LINES['flipflop'][0], 'mpn': LINES['flipflop'][2], 'footprint': LINES['flipflop'][3]},
                        {'key': 'U_SUB_NAND', 'line': LINES['nand'][0], 'mpn': LINES['nand'][2], 'footprint': LINES['nand'][3]},
                        {'key': 'U_SUB_SCHMITT1 (packing overflow)', 'line': LINES['schmitt'][0], 'mpn': LINES['schmitt'][2], 'footprint': LINES['schmitt'][3]}]
                       + [{'key': k, 'line': LINES[l][0], 'mpn': LINES[l][2] or 'UNRESOLVED (series representative, value not exact)',
                           'value': v, 'footprint': LINES[l][3], 'pins': p} for k, l, v, p in PASSIVES],
            'added_P': [{'key': 'SUB_TOGGLE', 'line': LINES['toggle'][0], 'mpn': LINES['toggle'][2],
                         'footprint': LINES['toggle'][3], 'pins': pinmap(TOGGLE_PINS)}],
            'changed': list(CHANGED), 'removed': list(REMOVED), 'kept_unchanged': list(KEPT_UNCHANGED),
            'untouched_sensitive_and_reference_nets': list(UNTOUCHED_SENSITIVE),
        },
        'joint': {
            'pair': '1×3, one per SUB oscillator, P B.Cu to K F.Cu; connector not selected (ST-01)',
            'pin_map': pinmap(PAIR_PINS),
            'order_rule': 'signal-AGND-signal, as every P-to-K 1×3 pair; pin n of the P half mates pin n of the K half',
            'routing_note': 'Toggle pad 3 is at x-2.54, pad 2 at the centre, pad 1 at x+2.54 (rot 0); a pair with '
                            'pin 1 at -x reaches each throw without a crossing. A mirrored mate would swap PUL '
                            'and -2 only; netlist parity catches it.',
            'audio_across_joint': False,
            'near_site_parts': 'None added on P besides the toggle and the pair half. All K-side conditioning '
                               'may sit anywhere in the OSC2/OSC4 core; nothing is required within the 0.7 mm window.',
        },
        'toggle': {'mpn': '2MS3T1B1M2QES', 'pins': pinmap(TOGGLE_PINS),
                   'evidence': {'pin_labels': 'unverified (pin-map.json: LEFT=3, COMMON=2, RIGHT=1)',
                                'contact_map': 'UNSOURCED (fact-2ms3-contact)',
                                'suffix_equivalence': 'UNSOURCED (fact-2ms3-suffix-equivalence)',
                                'assumption_shared_with': 'SYNC_SELECT on all five oscillators (pin 2 common)'},
                   'positions_grid_order': list(POSITIONS)},
        'panel_binding': [{'instance': i, 'ref': f'SW{i[1]}01', 'uid_now': f'C:{i}.OCT', 'uid_proposed': f'C:{i}.SUB',
                           'x_mm': x, 'y_mm': 185.0} for i, x in (('O2', 31.5), ('O4', 65.5))],
        'grid_revision_proposal': {
            'state': 'PROPOSAL for ST-10; not applied',
            'row_changes': {'uid': 'C:Ox.OCT -> C:Ox.SUB', 'id': 'Ox.OCT -> Ox.SUB', 'key': 'OCT -> SUB',
                            'label': 'OCT -> SUB', 'kind': 'octave -> switch',
                            'component': 'alps-srbv160803 -> dailywell-2ms3', 'diameter_mm': '8 -> 6',
                            'positions': '[-2,-1,0,1,2,3] -> ["PUL","-1","-2"]', 'accent': 'owner artwork decision'},
            'lock_consequence': {'domain': 'O -> P', 'hole_d_mm': '7.0 -> 5.2 (fitted toggle class)',
                                 'rot_deg': '180 -> 0 (as the other P toggles)',
                                 'assembly_pcb_z_mm/assembly_group': 'removed (selector-only fields)',
                                 'x_mm/y_mm': 'unchanged'},
            'reason_for_uid_rename': 'io_partition.region() classifies any C:*.OCT uid as region "selector"; the '
                                     'toggle must be region "control" (P). Keeping the uid needs a special case.',
            'alternative': 'keep uid C:Ox.OCT and special-case region(); fewer renamed references, one exception',
        },
        'rail_delta': {'proposed': rail_delta('saw'), 'alternative_pulse': rail_delta('pulse')},
        'area_K': {'proposed': area('saw'), 'alternative_pulse': area('pulse'),
                   'courtyards': {fp: courtyard_area(fp) for fp in ('SOIC-14_3.9x8.7mm_P1.27mm', 'R0603', 'C0603')},
                   'note': 'Courtyard rectangles from the project footprints; counts per SUB oscillator; no placement.'},
        'implementation_notes_for_ST11': [
            'Split the shared oscillator family into a SUB variant for O2 and O4; O4 is also split by '
            'precision-tssop-retention.json, so the SUB variant must compose with that split.',
            'Builder.finish() maps SN74HC74DR and SN74HC00DR to the ±12 V bypass branch; add them to the +5 V '
            'branch, or io_partition.refine() raises "orphaned bypass capacitors".',
            'Create the select conditioning with oscillator roles, not b.cell("switch_button_input"): that role '
            'is a CONTROL_CELL and would move the parts to P.',
            'Use the exact contact lines (RC0603FR-0710KL, RC0603FR-071KL) via CATALOG, as the cells do; b.r() '
            'would assign the RT0603BRD series with no MPN.',
            'Append new parts after existing ones so the designator lock only grows.',
            'Panel template: C:{}.SUB for the SUB variant (C:{}.OCT stays for O1/O3/O5).',
        ],
        'evidence_needs': [
            {'part': 'ALFA RPAR AS3340D', 'need': 'sawtooth output low and high level, shape and drive at +12 V / -5 V',
             'used_for': 'saw threshold window (needs low < 2.38 V and high > 2.62 V nominal) and LM393 input >= -0.3 V'},
            {'part': 'ALFA RPAR AS3340D', 'need': 'pulse output polarity relative to the saw reset; PW input span for 0 % and 100 %',
             'used_for': 'comparison claims for the PULSE_LOGIC clock'},
            {'part': 'ALFA RPAR AS3340D', 'need': 'hard and soft sync reset behaviour', 'used_for': 'player-facing sync description'},
            {'part': 'Texas Instruments LM393BIDR', 'need': 'VOL at about 1.1 mA sink; input common-mode range at VCC 12 V; large-signal response time',
             'used_for': 'HC14 VT- margin, SAW_RAW range, edge latency'},
            {'part': 'Texas Instruments SN74HC00DR', 'need': 'VOH/VOL rows, input transition-time limit, propagation delay',
             'used_for': 'exact PUL level and timing model bracket (1..60 ns assumed)'},
            {'part': 'Texas Instruments SN74HC74DR / SN74HC14DR', 'need': 'VOH/VOL rows and 5 V threshold rows; unused-input rule',
             'used_for': 'levels; the project convention replaces the missing rule'},
            {'part': 'Dailywell 2MS3T1B1M2QES', 'need': 'contact map (common pin, lever-to-throw), break-before-make, bounce time, suffix equivalence',
             'used_for': 'pin map, legend order, debounce adequacy'},
            {'part': 'Texas Instruments OPA4196IDR', 'need': 'input bias current', 'used_for': 'IN+ error term across 4.7 kΩ (same as today)'},
            {'part': '1×3 board-to-board pair', 'need': 'no connector selected (ST-01)', 'used_for': 'land pattern width against the 0.7 mm window'},
        ],
        'verification_plan': {
            'unit_tests_this_task': 'python3 scripts/checks/frozen_studies.py discover scripts/stack/sub_toggle',
            'ideal_simulation': [
                {'deck': 'saw comparator', 'stimulus': 'ideal saw PWL 0..8 V with 1 µs reset at 0.1 Hz, 100 Hz, 2 kHz, 20 kHz; '
                 '10 mV rms noise; swing variants 0.5..6 V and 0..10 V', 'model': 'behavioural comparator, open collector, 4.7 kΩ pull-up, divider and 1 MΩ',
                 'pass': 'thresholds within 1 mV of 2.6185 / 2.3810 V; exactly one SAW_LOGIC rising edge per reset'},
                {'deck': 'logic', 'stimulus': 'SAW_LOGIC and PULSE_LOGIC with PW 0, 1, 50, 99, 100 %; truncated hard-sync cycles; all toggle states and transitions',
                 'model': 'XSPICE d_dff, d_nand, d_inverter with 1..60 ns delays',
                 'pass': 'PUL: output equals PULSE_LOGIC; -1: one output edge per reset, 50 % duty; -2: one per two resets; no output pulse < 1 µs in the sub positions'},
                {'deck': 'level', 'stimulus': 'SUB_SELECTED 0/5 V through 4.7 kΩ', 'model': 'ideal op-amp PUL_SCALE',
                 'pass': 'PUL_SCALED -5.000/+5.000 V ±1 mV at nominal rails; identical to the present deck with PULSE_LOGIC'},
                {'deck': 'debounce', 'stimulus': 'contact make with 5 bounces 50 µs..1 ms; power-up ramp of +5 V',
                 'model': 'RC plus ideal Schmitt at both retained threshold corners',
                 'pass': 'only states of the table occur; no state outside it; power-up passes through PUL only'},
            ],
            'ST11_checks': [
                {'check': 'ERC through scripts/kicad/run.sh (KiCad 10.0.6)', 'pass': 'no new ERC error or warning class against the pre-change baseline'},
                {'check': 'netlist parity', 'pass': 'exported netlist of O2/O4 contains every net and pin of this spec; O1/O3/O5 unchanged; '
                 'sensitive and reference nets identical across variants except the removed selector pins'},
                {'check': 'model contract tests (test_oscillator and this task\'s test against the netlist)',
                 'pass': 'no SRBV160803 in O2/O4; R_OCT_SER pin 1 = AGND; PUL_SCALE IN+ = SUB_SELECTED; HC packages on +5V/AGND with 100 nF; '
                 'gate-level replay of the exported logic reproduces the state table'},
                {'check': 'check_oscillator.sh and pnpm circuit:check', 'pass': 'pass'},
                {'check': 'rail ledger refresh (build_oscillator_current)', 'pass': 'SUB variant +5 V row equals this delta'},
            ],
        },
    }
    return spec


def render():
    return json.dumps(build(), indent=2, ensure_ascii=False) + '\n'


def main(argv):
    text = render()
    if '--check' in argv:
        if SPEC.read_text() != text:
            raise SystemExit('spec.json drift: regenerate with scripts/stack/sub_toggle/sub_toggle.py')
        print('spec.json matches its generator')
        return 0
    SPEC.parent.mkdir(parents=True, exist_ok=True)
    SPEC.write_text(text)
    print('wrote', SPEC.relative_to(ROOT))
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
