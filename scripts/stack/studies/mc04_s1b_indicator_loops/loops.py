"""Stage 1b of the accepted remedy (option D): paper loop-stability screen for the magnitude-indicator units.

Stage 1a left the indicator LED bridge nets undetermined because they sit inside the op-amp feedback loop. Each
indicator unit is a follower-type loop: op-amp OUT (*_DRIVE) -> one BAS16GW diode -> *_LED_A -> LED -> *_LED_K -> one
diode -> IN- (*_SENSE, R_SENSE to AGND). The bridge current is V(SENSE)/R_SENSE, so the diode and LED small-signal
resistances, and the poles they make with any cable capacitance added to LED_A, LED_K or SENSE, move with the
signal level.

For every indicator unit on the crossing-net lists pinned by stage 1a, this adds the retained flat-link cable
capacitance (0.5 mm stock FFC, 80 mm, upper permittivity) to each of that unit's nets that crosses, and evaluates
the feedback ladder beta(f) = V(SENSE)/V(OUT) at several bridge currents. With a single-pole amplifier
A = GBW/(j f) (ASSUMED model; retained GBW fact), it reports the loop crossover and the phase margin, against the
same unit with no added capacitance. Diode and LED ideality, the ideal amplifier output, and the 45 degree margin
criterion are ASSUMED. Off-path diode junction capacitance and PCB parasitics are not modelled. Paper only: it
screens for a reason to simulate; it does not establish stability."""
import argparse
import cmath
import collections
import hashlib
import json
import math
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT / 'scripts/stack/link_electrical'))
sys.path.insert(0, str(ROOT / 'scripts/stack/studies/mc04_s1_budgets'))
import link_electrical as le  # noqa: E402
import budgets  # noqa: E402

VT = 0.02585                  # thermal voltage at 300 K
N_DIODE = 2.0                 # ASSUMED ideality; no retained BAS16GW fact
N_LED = 2.0                   # ASSUMED ideality; no retained APHHS1005QWF/D fact
CURRENTS_A = (1e-6, 1e-5, 1e-4, 1e-3)   # reported points
GRID_A = [10 ** (e / 8) for e in range(-56, -23)]  # 1e-7 to 1e-3 A, eighth-decade; pass/fail and worst cases
PM_LIMIT_DEG = 45.0           # ASSUMED draft criterion
FACT_SKILL = {'OPA4196IDR': ('component-ti-opa4196idr', 'fact-op-audio-gbw', 'fact-op-audio-input-impedance'),
              'OPA4197IPWR': ('component-ti-opa4197ipwr', 'fact-op-precision-gbw',
                              'fact-op-precision-input-impedance')}
OUT_PINS = {'1': '2', '7': '6', '8': '9', '14': '13'}


def amp_facts(mpn):
    skill, gbw, zin = FACT_SKILL[mpn]
    f = {x['fact_id']: x for x in json.loads((ROOT / '.claude/skills' / skill / 'facts.json').read_text())['facts']}
    return f[gbw]['value']['typical'] * 1e6, f[zin]['value']['common_mode_pF'] * 1e-12


def beta(f, r1, ca, rl, ck, r2, rs, cs):
    w = 2j * math.pi * f
    z = lambda c: 1 / (w * c) if c else None  # noqa: E731
    par = lambda a, b: a if b is None else a * b / (a + b)  # noqa: E731
    z3 = r2 + par(rs, z(cs))
    z2 = rl + par(z3, z(ck))
    z1 = par(z2, z(ca))
    return (z1 / (r1 + z1), par(z3, z(ck)) / z2, par(rs, z(cs)) / z3)


def margin(gbw, args):
    """Crossover of |GBW/(j f) * beta| and the phase margin; each ladder factor lags between 0 and 90 degrees."""
    lo, hi = 1.0, 1e10
    for _ in range(200):
        mid = math.sqrt(lo * hi)
        if gbw / mid * abs(math.prod(beta(mid, *args))) > 1:
            lo = mid
        else:
            hi = mid
    return lo, 90.0 + sum(math.degrees(cmath.phase(x)) for x in beta(lo, *args))


def led_nets(part, mpn, by_net, drive, sense):
    """LED_A/LED_K from the bridge topology: the BAS16GW diodes (pin 1 K, pin 2 A) on DRIVE and SENSE and the LED."""
    pins = {}
    for u in part['package_units']:
        pins.setdefault(u['ref'], {}).update(u.get('pins') or {})
    diodes = {r for n in (drive, sense) for r, _ in by_net[n] if mpn.get(r) == 'BAS16GW-QX'}
    cath = {pins[r]['1'] for r in diodes if pins[r]['2'] in (drive, sense)}
    anode = {pins[r]['2'] for r in diodes if pins[r]['1'] in (drive, sense)}
    if len(diodes) != 4 or len(cath) != 1 or len(anode) != 1:
        raise ValueError('unexpected bridge on %s/%s: %s' % (drive, sense, sorted(diodes)))
    a, k = cath.pop(), anode.pop()
    leds = [r for r, p in by_net[a] if mpn.get(r) == 'APHHS1005QWF/D' and p == '2' and pins[r].get('1') == k]
    if len(leds) != 1:
        raise ValueError('LED not found between %s and %s' % (a, k))
    return a, k


def r_of(val, ref):
    x = budgets.ohms(val.get(ref))
    if not x:
        raise ValueError('unparsed or zero-ohm resistor value %s %r' % (ref, val.get(ref)))
    return x


def run():
    inp = le.load_inputs()
    pk, length, rule, pair = budgets.CABLE
    c_cable = le.pair_parameters(inp, pk, length, max(inp['cable']['eps_eff']['value']), rule, pair)['Cv_total_F']
    part = json.loads((ROOT / 'design/reports/io-partition.json').read_text())
    mpn = {x['ref']: x['mpn'] for x in part['physical_packages']}
    val = budgets.values()
    units = []
    by_net = collections.defaultdict(list)
    for u in part['package_units']:
        for p, n in (u.get('pins') or {}).items():
            by_net[n].append((u['ref'], p))
    for u in part['package_units']:
        if u['role'] != 'magnitude_indicator:A' or mpn.get(u['ref']) not in FACT_SKILL:
            continue
        out_pin = next((p for p in u['pins'] if p in OUT_PINS), None)
        if out_pin is None:
            continue
        drive, sense = u['pins'][out_pin], u['pins'][OUT_PINS[out_pin]]
        led_a, led_k = led_nets(part, mpn, by_net, drive, sense)
        rs_ref = [r for r, _ in by_net[sense] if r.startswith('R') and 'AGND' in
                  {n for x in part['package_units'] if x['ref'] == r for n in x['pins'].values()}]
        if len(rs_ref) != 1:
            raise ValueError('R_SENSE not unique for %s: %s' % (sense, rs_ref))
        units.append({'ic': u['ref'], 'unit': u['unit'], 'mpn': mpn[u['ref']], 'nets': {
            'DRIVE': drive, 'SENSE': sense, 'LED_A': led_a, 'LED_K': led_k},
            'r_sense_ref': rs_ref[0], 'r_sense_ohm': r_of(val, rs_ref[0])})
    cases = {}
    for case, (p, h) in budgets.NETS.items():
        b = p.read_bytes()
        if hashlib.sha256(b).hexdigest() != h:
            raise ValueError('%s changed' % p)
        crossing = {x['net'] for x in json.loads(b)['nets']}
        rows = []
        for u in units:
            on = sorted(k for k, n in u['nets'].items() if n in crossing)
            if not on:
                continue
            gbw, cin = amp_facts(u['mpn'])
            add = {k: (c_cable if k in on else 0.0) for k in u['nets']}
            levels = []
            fine = []
            for i in GRID_A:
                rd, rl = N_DIODE * VT / i, N_LED * VT / i
                fine.append((margin(gbw, (rd, 0.0, rl, 0.0, rd, u['r_sense_ohm'], cin))[1],
                             margin(gbw, (rd, add['LED_A'], rl, add['LED_K'], rd, u['r_sense_ohm'],
                                          cin + add['SENSE']))[1]))
            for i in CURRENTS_A:
                rd, rl = N_DIODE * VT / i, N_LED * VT / i
                base = (rd, 0.0, rl, 0.0, rd, u['r_sense_ohm'], cin)
                moved = (rd, add['LED_A'], rl, add['LED_K'], rd, u['r_sense_ohm'], cin + add['SENSE'])
                fb, pb = margin(gbw, base)
                fm, pm = margin(gbw, moved)
                levels.append({'bridge_current_A': i, 'sense_V': round(i * u['r_sense_ohm'], 4),
                               'diode_r_ohm': round(rd, 1), 'led_r_ohm': round(rl, 1),
                               'baseline': {'crossover_Hz': round(fb), 'phase_margin_deg': round(pb, 1)},
                               'moved': {'crossover_Hz': round(fm), 'phase_margin_deg': round(pm, 1)},
                               })
            rows.append({'ic': u['ic'], 'unit': u['unit'], 'mpn': u['mpn'], 'crossing': on,
                         'r_sense_ohm': u['r_sense_ohm'], 'gbw_Hz': gbw, 'levels': levels,
                         'worst_moved_pm_deg': round(min(m for _, m in fine), 1),
                         'worst_baseline_pm_deg': round(min(b for b, _ in fine), 1),
                         'pass': min(m for _, m in fine) >= PM_LIMIT_DEG})
        per_ic = collections.defaultdict(list)
        for r in rows:
            per_ic[r['ic']].append(r['pass'])
        cases[case] = {'units': rows, 'per_ic': {k: ('screen passes' if all(v) else 'screen fails: simulate')
                                                 for k, v in sorted(per_ic.items())}}
    gbw, cin = amp_facts('OPA4196IDR')
    sens = []
    for n in (1.0, 2.0, 3.0):  # LED ideality n and 2n
        for k in (1, 2, 4):
            pms = []
            for nl in (n, 2 * n):
                for i in GRID_A:
                    rd = n * VT / i
                    pms.append(margin(gbw, (rd, k * c_cable, nl * VT / i, k * c_cable, rd, 5600.0, cin))[1])
            sens.append({'diode_ideality': n, 'led_ideality': [n, 2 * n], 'cable_C_multiple': k,
                         'worst_pm_deg': round(min(pms), 1)})
    return {'status': 'DRAFT paper screen; not a stability result',
            'sensitivity_R_SENSE_5600_OPA4196': {'currents_A': '1e-7 to 1e-3, eighth-decade steps',
                                                 'crossing': ['LED_A', 'LED_K'], 'rows': sens},
            'cable_C_pF': round(c_cable * 1e12, 2),
            'assumed': {'diode_ideality': N_DIODE, 'led_ideality': N_LED, 'amplifier': 'single pole at GBW, ideal output',
                        'phase_margin_limit_deg': PM_LIMIT_DEG,
                        'not_modelled': ['off-path diode junction capacitance',
                                         'on-path diode and LED junction and diffusion capacitance',
                                         'cable mutual capacitance between LED_A and LED_K and injection from '
                                         'neighbouring nets (Cv_total is applied as a grounded C)',
                                         'PCB parasitics',
                                         'amplifier output resistance and second poles', 'bridge dead band',
                                         'large-signal slewing']},
            'sources': {k: {'path': str(p.relative_to(ROOT)), 'sha256': h} for k, (p, h) in budgets.NETS.items()},
            'cases': cases}


def main():
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument('--out', default=str(Path(__file__).with_name('result.json')))
    a = ap.parse_args()
    text = json.dumps(run(), indent=1) + '\n'
    Path(a.out).write_text(text)
    print(a.out, hashlib.sha256(text.encode()).hexdigest())


if __name__ == '__main__':
    main()
