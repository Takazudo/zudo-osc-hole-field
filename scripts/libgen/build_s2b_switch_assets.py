#!/usr/bin/env python3
"""Generate the UNADOPTED S2b switch symbols and the TI RRP0016A WQFN-16 land.

Source bytes: circuit/sources/ic-library/TMUX7412F.pdf (TI SCDS404B) and
circuit/sources/ic-library/TMUX6112.pdf (TI SCDS383F). Pin numbers follow
SCDS404B Table 6-1 (WQFN column) and SCDS383F Table 5-1 (TSSOP column). Land
dimensions follow drawing 4224816/A, physical PDF index 44-46 of SCDS404B.

Phase 24 adds the BAV199,215 precision-input clamp symbol (circuit/sources/ic-library/
BAV199.pdf, Nexperia BAV199 v.3, Table 2 pinning, physical PDF index 0). It reuses the
existing SOT-23 land; the pin geometry matches BAT54S_215 so the cell wiring is unchanged.
"""
import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.libgen.gen_courtyards import rewrite as normalize_courtyard
from scripts.libgen.gen_ic_package_envelopes import render, footprint_with_model

RRP = 'TI_RRP0016A'
RRP_MODEL = 'IC_TI_RRP0016A.wrl'
# 4224816/A outline maxima: 4.1 x 4.1 mm body, 0.8 mm maximum height.
RRP_BODY = (4.1, 4.1, 0.8)
# 4224816/A land example: 16X (0.6) x (0.3) pads, 12X (0.65) pitch, (3.8)
# pad-centre span, (2.6) thermal pad; stencil 4X (1.15) at (0.675) offsets.
PAD_LENGTH, PAD_WIDTH, PITCH, SPAN, THERMAL = 0.6, 0.3, 0.65, 3.8, 2.6
APERTURE, APERTURE_OFFSET = 1.15, 0.675
# 4224816/A solder-mask detail: non-solder-mask-defined, 0.07 mm maximum.
MASK_MARGIN = 0.07

PARTS = {
    'TMUX7412FRRPR': {
        'lcsc': 'C2982617', 'footprint': RRP,
        'url': 'https://www.ti.com/lit/ds/symlink/tmux7412f.pdf',
        'channels': [('S1', '1', 'SEL1', '15', 'D1', '16'), ('S2', '12', 'SEL2', '14', 'D2', '13'),
                     ('S3', '9', 'SEL3', '7', 'D3', '8'), ('S4', '4', 'SEL4', '6', 'D4', '5')],
        'power': [('VDD', '11', 'passive'), ('VSS', '2', 'passive'), ('GND', '3', 'passive'),
                  ('FF', '10', 'open_collector'), ('EP', '17', 'passive')],
    },
    'TMUX6112PWR': {
        'lcsc': 'C2673384', 'footprint': 'TSSOP-16_4.4x5mm_P0.65mm',
        'url': 'https://www.ti.com/lit/ds/symlink/tmux6112.pdf',
        'channels': [('S1', '3', 'SEL1', '1', 'D1', '2'), ('S2', '14', 'SEL2', '16', 'D2', '15'),
                     ('S3', '11', 'SEL3', '9', 'D3', '10'), ('S4', '6', 'SEL4', '8', 'D4', '7')],
        'power': [('VDD', '13', 'passive'), ('VSS', '4', 'passive'), ('GND', '5', 'passive'),
                  ('NC', '12', 'no_connect')],
    },
}


def font():
    return '(effects (font (size 1.27 1.27)))'


def pin(kind, x, y, angle, name, number):
    return (f'    (pin {kind} line (at {x:g} {y:g} {angle}) (length 2.54) (name "{name}" {font()}) '
            f'(number "{number}" {font()}))\n')


def symbol(mpn, part):
    fp = 'zudo-osc-hole-field:' + part['footprint']
    hidden = '(effects (font (size 1.27 1.27)) (hide yes))'
    text = ('(kicad_symbol_lib\n  (version 20231120)\n  (generator "kicad_symbol_editor")\n  (generator_version "8.0")\n'
            f' (symbol "{mpn}"\n  (pin_names (offset 0.508)) (exclude_from_sim no) (in_bom yes) (on_board yes)\n'
            f'  (property "Reference" "U" (at 0 7.62 0) {font()})\n'
            f'  (property "Value" "{mpn}" (at 0 -7.62 0) {font()})\n'
            f'  (property "Footprint" "{fp}" (at 0 0 0) {hidden})\n'
            f'  (property "Datasheet" "{part["url"]}" (at 0 0 0) {hidden})\n'
            f'  (property "MPN" "{mpn}" (at 0 0 0) {hidden})\n'
            f'  (property "Manufacturer" "Texas Instruments" (at 0 0 0) {hidden})\n'
            f'  (property "LCSC" "{part["lcsc"]}" (at 0 0 0) {hidden})\n')
    box = '    (rectangle (start -3.81 5.08) (end 3.81 -5.08) (stroke (width 0.254) (type default)) (fill (type background)))\n'
    for unit, (s, sn, sel, seln, d, dn) in enumerate(part['channels'], 1):
        text += f'  (symbol "{mpn}_{unit}_1"\n' + box
        text += pin('passive', -6.35, 3.81, 0, s, sn) + pin('input', -6.35, 1.27, 0, sel, seln)
        text += pin('passive', 6.35, 3.81, 180, d, dn) + '  )\n'
    text += f'  (symbol "{mpn}_5_1"\n' + box
    slots = [(-6.35, 3.81, 0), (-6.35, 1.27, 0), (6.35, 3.81, 180), (6.35, 1.27, 180), (-6.35, -1.27, 0)]
    for (name, number, kind), (x, y, angle) in zip(part['power'], slots):
        text += pin(kind, x, y, angle, name, number)
    return text + '  )\n )\n)\n'


# Nexperia BAV199 v.3 Table 2: 1 A1 anode (diode 1), 2 K2 cathode (diode 2),
# 3 K1/A2 common. Same pin numbers and positions as BAT54S_215.
CLAMP_LL = {'mpn': 'BAV199,215', 'name': 'BAV199_215', 'lcsc': 'C40919', 'footprint': 'SOT-23',
            'url': 'https://assets.nexperia.com/documents/data-sheet/BAV199.pdf'}


def clamp_symbol():
    name, mpn, lcsc, fp, url = (CLAMP_LL[k] for k in ('name', 'mpn', 'lcsc', 'footprint', 'url'))
    hidden = '(effects (font (size 1.27 1.27)) (hide yes))'
    stroke = '(stroke (width 0) (type default)) (fill (type none))'
    text = ('(kicad_symbol_lib\n  (version 20231120)\n  (generator "kicad_symbol_editor")\n  (generator_version "8.0")\n'
            f' (symbol "{name}"\n  (pin_names (offset 0)) (exclude_from_sim no) (in_bom yes) (on_board yes)\n'
            f'  (property "Reference" "D" (at 2.54 -5.08 0) {font()})\n'
            f'  (property "Value" "{name}" (at -6.35 3.175 0) {font()})\n'
            f'  (property "Footprint" "zudo-osc-hole-field:{fp}" (at 0 0 0) {hidden})\n'
            f'  (property "Datasheet" "{url}" (at 0 0 0) {hidden})\n'
            f'  (property "Description" "Low-leakage series double diode, VR 75 V, SOT-23; UNADOPTED S2b precision-input candidate" (at 0 0 0) {hidden})\n'
            f'  (property "MPN" "{mpn}" (at 0 0 0) {hidden})\n'
            f'  (property "Manufacturer" "Nexperia" (at 0 0 0) {hidden})\n'
            f'  (property "LCSC" "{lcsc}" (at 0 0 0) {hidden})\n'
            f'  (symbol "{name}_0_1"\n')
    # Two series junction diodes, A1 -> K1/A2 -> K2, without Schottky cathode hooks.
    for pts in ('(xy -4.445 1.27) (xy -4.445 -1.27) (xy -2.54 0) (xy -4.445 1.27)', '(xy -2.54 -1.27) (xy -2.54 1.27)',
                '(xy -3.81 0) (xy -1.27 0)', '(xy -1.905 0) (xy 1.905 0)', '(xy 1.27 0) (xy 3.81 0)',
                '(xy 1.905 1.27) (xy 1.905 -1.27) (xy 3.81 0) (xy 1.905 1.27)', '(xy 3.81 -1.27) (xy 3.81 1.27)'):
        text += f'    (polyline (pts {pts}) {stroke})\n'
    text += '    (circle (center 0 0) (radius 0.254) (stroke (width 0) (type default)) (fill (type outline)))\n  )\n'
    text += f'  (symbol "{name}_1_1"\n'
    text += (f'    (pin passive line (at -7.62 0 0) (length 3.81) (name "A" {font()}) (number "1" {font()}))\n'
             f'    (pin passive line (at 7.62 0 180) (length 3.81) (name "K" {font()}) (number "2" {font()}))\n'
             f'    (pin passive line (at 0 -5.08 90) (length 5.08) (name "COM" {font()}) (number "3" {font()}))\n')
    return text + '  )\n )\n)\n'


def rrp_footprint():
    dx, dy, _ = RRP_BODY
    text = (f'(footprint "{RRP}" (version 20260206) (generator "s2b_switch_assets")\n'
            ' (layer "F.Cu") (attr smd)\n'
            ' (descr "TI RRP0016A WQFN-16 4224816/A example land pattern; UNADOPTED S2b candidate; unqualified draft")\n'
            ' (property "Reference" "REF**" (at 0 -3.1 0) (layer "F.SilkS") '
            '(effects (font (size 1 1) (thickness 0.15))))\n'
            f' (property "Value" "{RRP}" (at 0 3.1 0) (layer "F.Fab") '
            '(effects (font (size 1 1) (thickness 0.15))))\n')
    points = [(-dx/2+.5, -dy/2), (dx/2, -dy/2), (dx/2, dy/2), (-dx/2, dy/2), (-dx/2, -dy/2+.5)]
    for a, b in zip(points, points[1:]+points[:1]):
        text += (f' (fp_line (start {a[0]:g} {a[1]:g}) (end {b[0]:g} {b[1]:g}) '
                 '(stroke (width 0.1) (type solid)) (layer "F.Fab"))\n')
    # Pin-1 corner mark on F.SilkS, outside the 4.1 mm body and inside the pad-row extent
    # (edge + 0.3 mm), so the courtyard is unchanged; it clears pad 1 and pad 16 masks.
    for a, b in (((-2.15, -1.5), (-2.15, -2.15)), ((-2.15, -2.15), (-1.5, -2.15))):
        text += (f' (fp_line (start {a[0]:g} {a[1]:g}) (end {b[0]:g} {b[1]:g}) '
                 '(stroke (width 0.1) (type solid)) (layer "F.SilkS"))\n')
    edge = SPAN/2
    offsets = [(n-1.5)*PITCH for n in range(4)]
    pads = []
    for i, o in enumerate(offsets):
        pads.append((str(1+i), -edge, o, PAD_LENGTH, PAD_WIDTH))
        pads.append((str(5+i), o, edge, PAD_WIDTH, PAD_LENGTH))
        pads.append((str(9+i), edge, -o, PAD_LENGTH, PAD_WIDTH))
        pads.append((str(13+i), -o, -edge, PAD_WIDTH, PAD_LENGTH))
    for number, x, y, sx, sy in sorted(pads, key=lambda p: int(p[0])):
        text += (f' (pad "{number}" smd roundrect (at {x:g} {y:g}) (size {sx:g} {sy:g}) '
                 f'(layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio {0.05/min(sx, sy):g}) '
                 f'(solder_mask_margin {MASK_MARGIN:g}))\n')
    text += (f' (pad "17" smd rect (at 0 0) (size {THERMAL:g} {THERMAL:g}) (layers "F.Cu" "F.Mask") '
             f'(solder_mask_margin {MASK_MARGIN:g}))\n')
    for sx in (-1, 1):
        for sy in (-1, 1):
            text += (f' (pad "17" smd rect (at {sx*APERTURE_OFFSET:g} {sy*APERTURE_OFFSET:g}) '
                     f'(size {APERTURE:g} {APERTURE:g}) (layers "F.Paste"))\n')
    return footprint_with_model(normalize_courtyard(text + ')\n'), RRP_MODEL)


def generate(check=False):
    def emit(path, text):
        if check:
            if not path.exists() or path.read_text() != text:
                raise SystemExit('S2b candidate asset drift: ' + str(path.relative_to(ROOT)))
        else:
            path.write_text(text)
    for mpn, part in PARTS.items():
        emit(ROOT/'symbols/src'/(mpn+'.kicad_sym'), symbol(mpn, part))
    emit(ROOT/'symbols/src'/(CLAMP_LL['name']+'.kicad_sym'), clamp_symbol())
    emit(ROOT/'footprints/kicad/zudo-osc-hole-field.pretty'/(RRP+'.kicad_mod'), rrp_footprint())
    emit(ROOT/'footprints/kicad/zudo-osc-hole-field.3dshapes'/RRP_MODEL,
         render(RRP, RRP_BODY, 'Provisional envelope: TI RRP0016A 4224816/A outline maxima 4.1 x 4.1 x 0.8 mm. '
                'UNADOPTED S2b candidate; no land-pattern, solder-joint or physical-fit verdict.'))
    print(f'{"PASS" if check else "Generated"} S2b switch assets: {len(PARTS) + 1} symbols, 1 WQFN land; physical fit unqualified')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    generate(parser.parse_args().check)
