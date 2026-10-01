#!/usr/bin/env python3
"""Generate unselected monitor symbols and derive source-bound candidate footprints."""
import argparse
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from scripts.libgen.gen_courtyards import rewrite as normalize_courtyard
from scripts.libgen.gen_ic_package_envelopes import render, footprint_with_model

CATALOG = ROOT / 'design/power/monitor-permit-parts.json'


def property_text(key, value):
    return (f' (property {json.dumps(key)} {json.dumps(value)} (at 0 0 0) '
            '(effects (font (size 1.27 1.27)) (hide yes)))\n')


def ic_symbol(part):
    name = part['symbol']
    # Preserve the shared library's format header; CAD receipts name this
    # actual derivation script. Native validation still uses KiCad 10.0.6.
    text = ('(kicad_symbol_lib\n (version 20231120)\n (generator "kicad_symbol_editor")\n (generator_version "8.0")\n'
            f' (symbol "{name}" (pin_names (offset 0.508)) (in_bom yes) (on_board yes)\n'
            ' (property "Reference" "U" (at 0 8.89 0) (effects (font (size 1.27 1.27))))\n'
            f' (property "Value" "{name}" (at 0 -8.89 0) (effects (font (size 1.27 1.27))))\n')
    for key, value in [('MPN', part['mpn']), ('Manufacturer', part['manufacturer']),
                       ('LCSC', ''), ('Datasheet', part['source']['url']),
                       ('Footprint', 'zudo-osc-hole-field:'+part['footprint'])]:
        text += property_text(key, value)
    text += (f' (symbol "{name}_1_1" (rectangle (start -7.62 7.62) (end 7.62 -7.62) '
             '(stroke (width 0.254) (type default)) (fill (type background)))\n')
    pins = sorted(part['pins'].items(), key=lambda p: int(p[0]))
    split = (len(pins)+1)//2
    for i, (number, label) in enumerate(pins):
        left = i < split
        y = ((split-1)/2-(i % split))*2.54
        kind = 'input'
        if label in ('VDD','GND','V+','V-') or part['mpn']=='REF3433TIDBVR' and label=='IN':
            kind = 'power_in'
        elif label == 'NC':
            kind = 'no_connect'
        elif label == 'VOUT':
            kind = 'power_out'
        elif label.startswith(('RESET','OUT')):
            kind = 'open_collector'
        if 'pin_types' in part:
            if set(part['pin_types']) != set(part['pins']):
                raise ValueError('explicit pin types must cover the complete pin map')
            kind = part['pin_types'][number]
            if kind not in ('input', 'output', 'power_in', 'power_out', 'no_connect', 'open_collector'):
                raise ValueError('unsupported explicit pin type: '+kind)
        text += (f' (pin {kind} line (at {-10.16 if left else 10.16} {y:g} {0 if left else 180}) '
                 f'(length 2.54) (name {json.dumps(label)} (effects (font (size 1.27 1.27)))) '
                 f'(number "{number}" (effects (font (size 1.27 1.27)))))\n')
    return text+'  )\n )\n)\n'


def dct_footprint(envelope):
    """TI DCT0008A example pads; body display and courtyard remain provisional."""
    dx, dy, _ = envelope['body_max_xyz_mm']
    px, py = envelope['pad_size_xy_mm']
    left, right = envelope['pad_row_centres_x_mm']
    pitch = envelope['pad_pitch_mm']
    corner_ratio = envelope['pad_corner_radius_mm']/min(px,py)
    text = ('(footprint "TI_DCT0008A" (version 20260206) (generator "monitor_candidate_assets")\n'
            ' (layer "F.Cu") (attr smd)\n'
            ' (descr "TI DCT0008A 4220784/D example land pattern; unqualified draft")\n'
            ' (property "Reference" "REF**" (at 0 -2.2 0) (layer "F.SilkS") '
            '(effects (font (size 1 1) (thickness 0.15))))\n'
            ' (property "Value" "TI_DCT0008A" (at 0 2.2 0) (layer "F.Fab") '
            '(effects (font (size 1 1) (thickness 0.15))))\n')
    # Chamfer identifies pin 1. Outline uses drawing maxima, not molded shape.
    points = [(-dx/2+.4,-dy/2),(dx/2,-dy/2),(dx/2,dy/2),(-dx/2,dy/2),(-dx/2,-dy/2+.4)]
    for a,b in zip(points,points[1:]+points[:1]):
        text += (f' (fp_line (start {a[0]:g} {a[1]:g}) (end {b[0]:g} {b[1]:g}) '
                 '(stroke (width 0.1) (type solid)) (layer "F.Fab"))\n')
    for number in range(1,9):
        x = left if number <=4 else right
        y = (number-2.5)*pitch if number<=4 else (6.5-number)*pitch
        text += (f' (pad "{number}" smd roundrect (at {x:g} {y:g}) (size {px:g} {py:g}) '
                 f'(layers "F.Cu" "F.Paste" "F.Mask") (roundrect_rratio {corner_ratio:g}))\n')
    text += ')\n'
    return footprint_with_model(normalize_courtyard(text), 'IC_TI_DCT0008A.wrl')


def generate(check=False):
    def emit(path, text):
        if check:
            if not path.exists() or path.read_text() != text:
                raise ValueError('candidate asset drift: '+str(path.relative_to(ROOT)))
        else:
            path.write_text(text)
    parts = json.loads(CATALOG.read_text())['parts']
    template = (ROOT/'symbols/src/RT0603BRD07100KL.kicad_sym').read_text()
    for part in parts:
        if part.get('existing_symbol'):
            if not (ROOT/'symbols/src'/(part['symbol']+'.kicad_sym')).is_file():
                raise ValueError('required existing symbol is missing')
            continue
        if part['kind'] == 'resistor':
            text = template.replace('RT0603BRD07100KL', part['symbol'])
            text = text.replace('"MPN" "'+part['symbol']+'"', '"MPN" '+json.dumps(part['mpn']))
            text = text.replace('zudo-osc-hole-field:R0603', 'zudo-osc-hole-field:'+part['footprint'])
            text = text.replace('(property "Datasheet" ""', '(property "Datasheet" '+json.dumps(part['source']['url']))
        else:
            text = ic_symbol(part)
        emit(ROOT/'symbols/src'/(part['symbol']+'.kicad_sym'), text)
    for name, library, output in (
            ('SOT-23-6', 'Package_TO_SOT_SMD', 'SOT-23-6'),
            ('SOT-23-8', 'Package_TO_SOT_SMD', 'SOT-23-8'),
            ('R_0805_2012Metric', 'Resistor_SMD', 'R_0805_2012Metric_Monitor')):
        text = (ROOT/'circuit/sources/monitor-permit-cad'/(name+'.kicad_mod')).read_text()
        text = text.replace(f'(footprint "{name}"', f'(footprint "{output}"', 1)
        text = text.replace(f'"Value" "{name}"', f'"Value" "{output}"')
        text = text.replace('${KICAD10_3DMODEL_DIR}/'+library+'.3dshapes/'+name+'.step',
                            '${KIPRJMOD}/../../footprints/kicad/zudo-osc-hole-field.3dshapes/'+name+'.wrl')
        if not re.search(r'\(model "\$\{KIPRJMOD\}', text):
            raise ValueError('upstream model reference changed')
        text = normalize_courtyard(text)
        emit(ROOT/'footprints/kicad/zudo-osc-hole-field.pretty'/(output+'.kicad_mod'), text)
    dct = next((p for p in parts if p['footprint'] == 'TI_DCT0008A'), None)
    if dct:
        envelope = dct['package_envelope']
        text = dct_footprint(envelope)
        emit(ROOT/'footprints/kicad/zudo-osc-hole-field.pretty/TI_DCT0008A.kicad_mod', text)
        emit(ROOT/'footprints/kicad/zudo-osc-hole-field.3dshapes/IC_TI_DCT0008A.wrl',
             render('TI_DCT0008A', tuple(envelope['body_max_xyz_mm']), envelope['scope']))
    print(f'Prepared {len(parts)} candidate identities; physical fit unqualified')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true')
    generate(parser.parse_args().check)
