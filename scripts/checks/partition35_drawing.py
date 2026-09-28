#!/usr/bin/env python3
"""Source-derived engineering overview; schematic rectangles, not solid CAD."""
import argparse
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'design/partition/board-stack-candidate.svg'


def build():
    s=json.loads((ROOT/'design/partition/partition-input.json').read_text());f=json.loads((ROOT/'design/partition/floorplan-candidate.json').read_text());c=json.loads((ROOT/'design/partition/connector-packing-candidate.json').read_text())
    result=['<svg xmlns="http://www.w3.org/2000/svg" width="1100" height="1190" viewBox="0 0 1100 1190">','<rect width="100%" height="100%" fill="white"/>','<g font-family="sans-serif" fill="#222">','<text x="24" y="27" font-size="20">Nine-board conditional draft — all 438 hardware centres fixed</text>','<text x="24" y="49" font-size="13">Courtyard capacity proposal only. No routed PCB, manufactured assembly or physical fit PASS.</text>']
    for b,ox,oy in [('J',25,90),('P',560,90),('K',25,565),('EL',560,565)]:
        spec=s['boards'][b];scale=1.5
        result.append(f'<text x="{ox}" y="{oy-12}" font-size="16">{spec["id"]}: F.Cu z={spec["face_z_mm"]} mm; {spec["layers"]} layers / {spec["thickness_mm"]} mm</text>')
        result.append(f'<g transform="translate({ox} {oy}) scale({scale})">')
        result.append('<rect x="0" y="0" width="318" height="298" fill="#fafafa" stroke="#ddd"/>')
        result.append('<polygon points="'+' '.join(f'{x},{y}' for x,y in spec['outline'])+'" fill="#e3efec" stroke="#347869" stroke-width="0.5"/>')
        for p in f['placements']:
            if p['board']!=b:continue
            x,y,X,Y=p['courtyard_mm'];color='#a27b4d' if p['fixed'] else '#9ca9c8' if p['side']=='B.Cu' else '#77bca3'
            result.append(f'<rect x="{x}" y="{y}" width="{X-x}" height="{Y-y}" fill="{color}" fill-opacity="0.7" stroke="#555" stroke-width="0.05"/>')
        for h in c['headers']:
            if h['board']!=b:continue
            x,y,X,Y=h['land_courtyard_mm'];result.append(f'<rect x="{x}" y="{y}" width="{X-x}" height="{Y-y}" fill="#8653a9" fill-opacity="0.7"/>')
        power=s['load_distribution']
        for target in ('J','P'):
            for index,x in enumerate(power['x_mm']):
                if b not in (target,'K'):continue
                y=power[target+'_pad_y_mm'] if b==target else power['K_'+target+'_pad_y_mm_by_wire'][index]
                result.append(f'<rect x="{x-2}" y="{y-2}" width="4" height="4" fill="#e58232" stroke="#444" stroke-width="0.1"/>')
        for x,y in spec['supports_mm']:result.append(f'<circle cx="{x}" cy="{y}" r="1.6" fill="#f2b839" stroke="#555" stroke-width="0.15"/>')
        if b=='EL':
            optical=json.loads((ROOT/'design/partition/stage-optical-candidate.json').read_text())
            for h in optical['passages']:result.append(f'<circle cx="{h["center_mm"][0]}" cy="{h["center_mm"][1]}" r="{h["diameter_mm"]/2}" fill="white" stroke="#777" stroke-width="0.2"/>')
            for h in optical['support_posts']:result.append(f'<circle cx="{h["center_mm"][0]}" cy="{h["center_mm"][1]}" r="1.6" fill="#f2b839"/>')
        if b=='K':result.append('<rect x="260" y="248" width="48" height="45" fill="none" stroke="#c94444" stroke-dasharray="2 2" stroke-width="0.6"/>')
        result.append('</g>')
    result +=['<text x="25" y="1040" font-size="14">F/B faces overlaid. Brown: hardware/LEDs. Blue: rear circuits. Green: front circuits. Purple: GH courtyards.</text>','<text x="25" y="1062" font-size="14">Gold: supports. Orange: 24 load-side lands / 12 wires. Red: EXT XY reservation (z = −85..−45 mm); no source or inlet selected.</text>','<text x="25" y="1094" font-size="15">Section datum: panel front 0 → rear −2 → EL −4.2 → J −10 / P −11.8 → O −16 / −29 → K −100</text>','<text x="25" y="1118" font-size="14">K rear face −101.6; component height ceiling 5; proposed enclosure inner rear −120: nominal 13.4 mm gap.</text>','<text x="25" y="1142" font-size="14">Five exact stepped octave adapters omitted from these four area views; retained in the selected #55 drawing.</text>','<text x="25" y="1166" font-size="14">#65 support, seated hardware and loom coupon; #55 selectors; #57 source; #59 protection; #64 optics remain open.</text>','</g></svg>']
    return '\n'.join(result)+'\n'

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--check',action='store_true');a=p.parse_args();text=build()
    if a.check:
        if not OUT.exists() or OUT.read_text()!=text:raise SystemExit('drawing drift')
    else:OUT.write_text(text)
    print('PASS: source engineering overview current; no solid/physical fit claim')
