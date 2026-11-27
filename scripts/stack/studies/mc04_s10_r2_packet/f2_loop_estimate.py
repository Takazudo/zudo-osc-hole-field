#!/usr/bin/env python3
"""First-order, TYPICAL-ONLY estimate of the W1 F2 fold-cell loop (U5210 unit B, OPA4196IDR).
NOT evidence of stability. Single-pole op-amp assumption; inputs are the retained typical facts
fact-op-audio-gbw (2.5 MHz typ, no minimum) and fact-op-audio-input-impedance (1.6 pF diff, 6.4 pF CM, typ).
Cell (design/spec/modules/wavefolder.py): IN- = F2_SUM, R5256 100k from F1_OUT, R5257 100k from F2_OUT, no feedback capacitor."""
import math, json
GBW = 2.5e6; RIN = RF = 100e3; CIN = (1.6 + 6.4) * 1e-12
NG = 1 + RF / RIN; RP = RIN * RF / (RIN + RF)
def pm(c_stray_pF):
    c = CIN + c_stray_pF * 1e-12
    fz = 1 / (2 * math.pi * RP * c)
    lo, hi = 1e3, GBW
    for _ in range(200):                      # solve NG*sqrt(1+(f/fz)^2) = GBW/f
        f = math.sqrt(lo * hi)
        if NG * math.sqrt(1 + (f / fz) ** 2) * f > GBW: hi = f
        else: lo = f
    return {'stray_pF': c_stray_pF, 'node_C_pF': round(c * 1e12, 2), 'f_zero_kHz': round(fz / 1e3, 1),
            'f_cross_kHz': round(f / 1e3, 1), 'phase_margin_deg_single_pole_model': round(90 - math.degrees(math.atan(f / fz)), 1)}
rows = [pm(x) for x in (0, 2, 5.07, 5.23, 5.96, 8, 10, 15, 20)]
print(json.dumps({'noise_gain': NG, 'R_parallel_ohm': RP, 'opamp_input_C_pF_typ': CIN * 1e12, 'GBW_MHz_typ': GBW / 1e6, 'rows': rows}, indent=1))
