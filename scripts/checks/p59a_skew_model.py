"""Diagnostic start-skew screen for the UNADOPTED P59-A VEE5 clamp.

Uses the pinned TI OPAx197 model through the KiCad oracle. TI does not claim model
validity below the 4.5 V minimum supply, REF5050 has no retained model, and no
official BAT54S model is retained. The clamp is a conservative envelope built from
the promoted 25 C VF maxima: at every voltage it conducts no more than a diode that
meets those maxima, so it can only overstate VEE5. Results are diagnostic only.
"""
from pathlib import Path
import itertools
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from design.spec.cells.sweep_precision_vendor import model

# (VF_max_k, I_{k-1}) from fact-clamp-diode-forward-voltage: 0.1/1/10/30/100 mA at
# 0.24/0.32/0.40/0.50/0.80 V. Pairing each VF maximum with the previous test current
# makes the envelope conduct less than any conforming diode at every voltage.
CLAMP_ENVELOPE = [(-20, 0), (0.24, 0), (0.32, 1e-4), (0.40, 1e-3), (0.50, 1e-2), (0.80, 3e-2), (1.20, 1e-1), (20, 1e-1)]
SLOPE_P, SLOPE_N = 1.23, 1.22  # V/ms, pd-interface-20v.md section 5 fastest slopes
SKEWS_MS = [-1.0, -0.69, -0.41, 0.0, 0.55, 1.0, 2.26, 4.65]  # +ve: +12 V leads
LOADS = {'0mA': 0.0, '6mA': 6e-3}
REFS = {
    'track': 'limit(V(vp)-0.2,0,5)',
    'late': '5*limit((V(vp)-5.2)/0.2,0,1)',
}
VARIANTS = {'current_100ohm_no_clamp': (100, False, False), 'p59a_1210ohm_clamp': (1210, True, False),
            'p59a_rev2_sink_diode_100ohm_clamp_bleed10k': (100, True, True)}
VARIANT_LOADS = {'p59a_rev2_sink_diode_100ohm_clamp_bleed10k': {'0mA': 0.0, '6.5mA': 6.5e-3, '10mA': 10e-3}}
OUT = ROOT / 'design/power/proposals-59/p59a-skew-model.json'
CACHE = ROOT / '.circuit-cache/sources/p59a-skew'


def deck(skew_ms, ref, iload, riso, clamp, sink=False):
    tp = max(0.0, -skew_ms) * 1e-3
    tn = max(0.0, skew_ms) * 1e-3
    vp, vn = SLOPE_P * 10, -SLOPE_N * 10
    env = ', '.join(f'{v:g},{i:g}' for v, i in CLAMP_ENVELOPE)
    lines = [
        'P59-A diagnostic start-skew screen (TI OPAx197 model; surrogates noted)',
        '.param TEMP=27',
        '.include .circuit-cache/sources/opa197-model/OPAx197.LIB',
        f'Vp vp 0 PWL(0 0 {tp:g} 0 {tp + 10e-3:g} {vp:g} 40m {vp:g})',
        f'Vn vn 0 PWL(0 0 {tn:g} 0 {tn + 10e-3:g} {vn:g} 40m {vn:g})',
        f'Braw rawi 0 V = {REFS[ref]}',
        'Rraw rawi raw 10', 'Craw raw 0 1u',
        'XA1 raw ref5 vp vn ref5 OPAx197',
        'Rinv ref5 inv 10k', 'Rfb refn5 inv 10k',
        'XA2 0 inv vp vn refn5 OPAx197',
        'XDRV refn5 vfb vp vn vdrive OPAx197',
        (f'Riso vdrive vsink {riso}' if sink else f'Riso vdrive vee5 {riso}'), 'Rvfb vee5 vfb 10k', 'Cfast vdrive vfb 100p',
        'Cvee vee5 0 100n',
        f'Bload vp vee5 I = {iload:g}*limit(V(vp)-V(vee5),0,1)',
    ]
    if sink:
        # Sink-only series diode (anode VEE5, cathode toward the driver), same conservative envelope, plus a 10 k bleed.
        lines += [f'Bsink vee5 vsink I = pwl(V(vee5)-V(vsink), {env})', 'Rbleed vee5 0 10k']
    if clamp:
        lines += [f'Bclamp vee5 0 I = pwl(V(vee5), {env})', f'Bic ic 0 V = pwl(V(vee5), {env})']
    else:
        lines += ['Bic ic 0 V = 0']
    lines += [
        '.control', 'set noinit', 'tran 2u 25m',
        'meas tran vmax MAX v(vee5) FROM=0 TO=25m',
        'meas tran vmin MIN v(vee5) FROM=0 TO=25m',
        'meas tran imax MAX v(ic) FROM=0 TO=25m',
        'meas tran vend FIND v(vee5) AT=24m',
        '.endc', '.end',
    ]
    return '\n'.join(lines) + '\n'


def measure(text):
    out = {}
    for key in ('vmax', 'vmin', 'imax', 'vend'):
        m = re.search(rf'^{key}\s*=\s*([-+0-9.eE]+)(?:\s+at=\s*([-+0-9.eE]+))?', text, re.M)
        out[key] = float(m.group(1)) if m else None
        out[key + '_at'] = float(m.group(2)) if m and m.group(2) else None
    return out


def run(selected):
    model()
    CACHE.mkdir(parents=True, exist_ok=True)
    init = ROOT / '.spiceinit'
    if init.exists():
        raise RuntimeError('Refusing to replace .spiceinit')
    init.write_text('set ngbehavior=ps\n')
    rows = []
    try:
        for (variant, (riso, clamp, sink)), ref, skew in itertools.product([(k, v) for k, v in VARIANTS.items() if k in selected], REFS, SKEWS_MS):
          for lname, iload in VARIANT_LOADS.get(variant, LOADS).items():
            path = CACHE / 'case.cir'
            path.write_text(deck(skew, ref, iload, riso, clamp, sink))
            try:
                r = subprocess.run(['bash', 'scripts/kicad/run.sh', 'ngspice', '-b', str(path.relative_to(ROOT))], cwd=ROOT, capture_output=True, text=True, timeout=180)
            except subprocess.TimeoutExpired:
                rows.append({'variant': variant, 'ref_surrogate': ref, 'vee_load': lname, 'skew_ms_plus12_leads': skew, 'status': 'NOT RUN', 'reason': 'ngspice exceeded 180 s'})
                continue
            m = measure(r.stdout)
            if r.returncode or None in (m['vmax'], m['vmin']):
                rows.append({'variant': variant, 'ref_surrogate': ref, 'vee_load': lname, 'skew_ms_plus12_leads': skew, 'status': 'NOT RUN', 'reason': (r.stdout + r.stderr)[-400:]})
                continue
            inside = m['vmax'] <= 0.5 and m['vmin'] >= -6.0
            rows.append({'variant': variant, 'ref_surrogate': ref, 'vee_load': lname, 'skew_ms_plus12_leads': skew,
                         'vee5_max_V': round(m['vmax'], 4), 'vee5_max_at_ms': round(m['vmax_at'] * 1e3, 3) if m['vmax_at'] is not None else None, 'vee5_min_V': round(m['vmin'], 4), 'vee5_at_24ms_V': round(m['vend'], 4) if m['vend'] is not None else None,
                         'clamp_envelope_current_max_mA': round(m['imax'] * 1e3, 3) if m['imax'] is not None else None,
                         'inside_as3340_vee_limits_diagnostic': inside})
    finally:
        init.unlink()
    if OUT.exists():
        rows = [r for r in json.loads(OUT.read_text())['cases'] if r['variant'] not in selected] + rows
    report = {
        'status': 'DIAGNOSTIC ONLY; P59-A UNADOPTED; not a qualification',
        'oracle': 'KiCad 10.0.6 pinned ngspice via scripts/kicad/run.sh',
        'amplifier': 'Pinned TI OPAx197 Final 1.3 (library SHA-256 fc5b020e...); TI claims no validity below 4.5 V span',
        'clamp': 'Conservative envelope from fact-clamp-diode-forward-voltage (25 C maxima); official BAT54S SPICE model NOT RETAINED (Nexperia download refused, HTTP 403)',
        'reference': 'REF5050 has no retained model; two surrogates bracket it: track = limit(VIN-0.2,0,5), late = 0 until VIN = 5.2 V, then 0 to 5 V over the next 0.2 V of VIN',
        'vee_load': 'AS3340 VEE pin current is not guaranteed (fact-vco-positive-supply-current is a typical-table 6.5 mA maximum at +15 V); swept 0 and 6 mA (0, 6.5 and 10 mA for rev2) as a current from +12 V into VEE5',
        'remote_buffer': 'The audio-role LOCAL_REFN5 buffer is not modelled; the A2 inverter output drives the VEE driver directly',
        'ramps': f'linear, {SLOPE_P}/{SLOPE_N} V/ms (fastest contract slopes), 10 ms; positive skew = +12 V starts first',
        'limits_V': {'vee5_max': 0.5, 'vee5_min': -6.0},
        'cases': rows,
    }
    OUT.write_text(json.dumps(report, indent=2) + '\n')
    ok = [r for r in rows if r.get('inside_as3340_vee_limits_diagnostic')]
    print(f'DIAGNOSTIC: {len(ok)}/{len(rows)} cases inside VEE limits; NOT RUN {sum(r.get("status") == "NOT RUN" for r in rows)}')


if __name__ == '__main__':
    run(sys.argv[1:] or list(VARIANTS))
